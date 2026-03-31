#!/usr/bin/env python3
"""
Public-ready FTP sync script.

- Keeps local files as source of truth.
- Uploads files and optionally removes remote orphans.
- Supports ignore rules via .ftpignore.
- Uses environment variables or a local .env file for configuration.

Usage:
  python3 syncftp.py upload
  python3 syncftp.py download
  python3 syncftp.py sync
"""

from __future__ import annotations

import ftplib
import fnmatch
import os
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


SCRIPT_DIR = Path(__file__).resolve().parent
ENV_FILE = SCRIPT_DIR / ".env"


@dataclass
class Config:
    ftp_host: str
    ftp_port: int
    ftp_user: str
    ftp_pass: str
    ftp_path: str
    workspace_dir: Path
    site_subdir: str
    workspace_prefix: str
    local_dir: Path
    ftp_ignore_file: Path
    passive_mode: bool
    timeout_seconds: int
    ignore_files: set[str]
    ignore_dirs: set[str]
    unwanted_remote_entries: list[str]
    download_files: list[str]


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _get_bool(var_name: str, default: bool) -> bool:
    raw_value = os.getenv(var_name)
    if raw_value is None:
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(var_name: str, default: int) -> int:
    raw_value = os.getenv(var_name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def _get_csv(var_name: str, default: str) -> list[str]:
    raw_value = os.getenv(var_name, default)
    return [part.strip() for part in raw_value.split(",") if part.strip()]


def load_config() -> Config:
    _load_env_file(ENV_FILE)

    workspace_dir = Path(os.getenv("WORKSPACE_DIR", str(SCRIPT_DIR.parent))).expanduser().resolve()
    site_subdir = os.getenv("SITE_SUBDIR", "al-page-gd").strip("/\\")
    workspace_prefix = os.getenv("WORKSPACE_PREFIX", site_subdir).strip("/\\")
    local_dir = workspace_dir / site_subdir

    ignore_file_env = os.getenv("FTP_IGNORE_FILE", "").strip()
    if ignore_file_env:
        ftp_ignore_file = Path(ignore_file_env).expanduser().resolve()
    else:
        candidate_workspace_ignore = workspace_dir / ".ftpignore"
        ftp_ignore_file = candidate_workspace_ignore if candidate_workspace_ignore.exists() else SCRIPT_DIR / ".ftpignore"

    return Config(
        ftp_host=os.getenv("FTP_HOST", "ftpupload.net"),
        ftp_port=_get_int("FTP_PORT", 21),
        ftp_user=os.getenv("FTP_USER", ""),
        ftp_pass=os.getenv("FTP_PASS", ""),
        ftp_path=os.getenv("FTP_PATH", "/htdocs"),
        workspace_dir=workspace_dir,
        site_subdir=site_subdir,
        workspace_prefix=workspace_prefix,
        local_dir=local_dir,
        ftp_ignore_file=ftp_ignore_file,
        passive_mode=_get_bool("PASSIVE_MODE", True),
        timeout_seconds=_get_int("CONNECTION_TIMEOUT", 10),
        ignore_files=set(
            _get_csv(
                "IGNORE_FILES",
                ".vscode,.git,.DS_Store,node_modules,.gitignore,sync.py,.ftpkr.json,vscode,.gitkeep,.prettierrc,.override,DO NOT UPLOAD FILES HERE",
            )
        ),
        ignore_dirs=set(_get_csv("IGNORE_DIRS", ".vscode,.git,__pycache__,node_modules,vscode,.github")),
        unwanted_remote_entries=_get_csv("UNWANTED_REMOTE_ENTRIES", ""),
        download_files=_get_csv("DOWNLOAD_FILES", "index.html,index2.html"),
    )


def validate_config(config: Config) -> None:
    if not config.ftp_user:
        print("✗ Missing FTP_USER. Set it in .env or environment variables.", file=sys.stderr)
        sys.exit(1)
    if not config.ftp_pass:
        print("✗ Missing FTP_PASS. Set it in .env or environment variables.", file=sys.stderr)
        sys.exit(1)
    if not config.local_dir.exists() or not config.local_dir.is_dir():
        print(f"✗ Local site folder not found: {config.local_dir}", file=sys.stderr)
        sys.exit(1)


def load_ftp_ignore_patterns(config: Config) -> list[str]:
    patterns: list[str] = []
    if not config.ftp_ignore_file.exists():
        return patterns

    try:
        with config.ftp_ignore_file.open("r", encoding="utf-8") as ignore_file:
            for raw_line in ignore_file:
                line = raw_line.strip().replace("\\", "/")
                if not line or line.startswith("#"):
                    continue
                while line.startswith("/"):
                    line = line[1:]
                if line:
                    patterns.append(line)
    except Exception as exc:
        print(f"- Warning: could not read {config.ftp_ignore_file.name}: {exc}")

    return patterns


def matches_ignore_pattern(rel_path: str, name: str, patterns: list[str], prefix: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    prefixed = f"{prefix}/{normalized}" if prefix else normalized
    candidates = [normalized, prefixed, name]

    for pattern in patterns:
        for candidate in candidates:
            if fnmatch.fnmatch(candidate, pattern):
                return True
            if PurePosixPath(candidate).match(pattern):
                return True

    return False


def get_local_files(config: Config) -> list[tuple[Path, str]]:
    ignore_patterns = load_ftp_ignore_patterns(config)
    files: list[tuple[Path, str]] = []

    for root, dirs, filenames in os.walk(config.local_dir):
        root_path = Path(root)

        kept_dirs: list[str] = []
        for dirname in dirs:
            if dirname in config.ignore_dirs:
                continue

            dir_rel_path = (root_path / dirname).relative_to(config.local_dir)
            dir_rel = str(dir_rel_path).replace("\\", "/")
            if matches_ignore_pattern(dir_rel, dirname, ignore_patterns, config.workspace_prefix):
                continue

            kept_dirs.append(dirname)

        dirs[:] = kept_dirs

        for filename in filenames:
            if filename in config.ignore_files:
                continue

            full_path = root_path / filename
            rel_path = full_path.relative_to(config.local_dir)
            rel_path_str = str(rel_path).replace("\\", "/")
            if matches_ignore_pattern(rel_path_str, filename, ignore_patterns, config.workspace_prefix):
                continue

            files.append((full_path, rel_path_str))

    return files


def get_remote_files(ftp: ftplib.FTP) -> set[str]:
    remote_files: set[str] = set()
    try:
        for item in ftp.nlst("."):
            if item not in (".", "..", "./.", "./.."):
                clean_item = item.replace("./", "")
                if clean_item and clean_item not in (".", ".."):
                    remote_files.add(clean_item)

        try:
            ftp.cwd("imgs")
            for img in ftp.nlst("."):
                if img not in (".", "..", "./.", "./.."):
                    clean_img = img.replace("./", "")
                    if clean_img and clean_img not in (".", ".."):
                        remote_files.add(f"imgs/{clean_img}")
            ftp.cwd("..")
        except ftplib.error_perm:
            pass
    except ftplib.all_errors:
        pass

    return remote_files


def connect_ftp(config: Config) -> ftplib.FTP:
    ftp = ftplib.FTP()
    print(f"Connecting to {config.ftp_host}:{config.ftp_port}...")
    ftp.connect(config.ftp_host, config.ftp_port, timeout=config.timeout_seconds)
    ftp.set_pasv(config.passive_mode)
    ftp.login(config.ftp_user, config.ftp_pass)
    print("✓ Connected and logged in")
    ftp.cwd(config.ftp_path)
    print(f"✓ Changed to {config.ftp_path}")
    return ftp


def remove_unwanted_remote_entries(ftp: ftplib.FTP, entries: list[str]) -> None:
    if not entries:
        return

    for name in entries:
        try:
            ftp.delete(name)
            print(f"  ✓ Removed server file: {name}")
        except ftplib.error_perm:
            try:
                ftp.rmd(name)
                print(f"  ✓ Removed server directory: {name}")
            except ftplib.error_perm:
                print(f"  - Keep {name}: permission denied or not empty")
            except Exception:
                print(f"  - Keep {name}: could not remove")
        except Exception:
            print(f"  - Keep {name}: error during delete")


def upload(config: Config) -> None:
    try:
        validate_config(config)
        ftp = connect_ftp(config)

        remove_unwanted_remote_entries(ftp, config.unwanted_remote_entries)

        local_files = get_local_files(config)
        local_paths = {rel_path for _, rel_path in local_files}

        print(f"\n📤 Uploading {len(local_files)} file(s):")

        for local_path, rel_path in local_files:
            remote_dir = "/".join(rel_path.split("/")[:-1])
            if remote_dir:
                dirs_to_create = remote_dir.split("/")
                for i, _ in enumerate(dirs_to_create):
                    cumulative_path = "/".join(dirs_to_create[: i + 1])
                    full_remote_path = f"{config.ftp_path}/{cumulative_path}"
                    try:
                        ftp.mkd(full_remote_path)
                        print(f"  📁 Created directory: {cumulative_path}")
                    except ftplib.error_perm:
                        pass

            try:
                full_remote_path = f"{config.ftp_path}/{rel_path}"
                with open(local_path, "rb") as local_file:
                    ftp.storbinary(f"STOR {full_remote_path}", local_file)
                print(f"  ✓ {rel_path}")
            except Exception as exc:
                print(f"  ✗ {rel_path}: {exc}")

        print("\n🗑️  Checking for removed files...")
        remote_files = get_remote_files(ftp)
        files_to_delete = remote_files - local_paths

        if files_to_delete:
            print(f"Removing {len(files_to_delete)} orphaned file(s) from server:")
            for remote_file in sorted(files_to_delete):
                try:
                    ftp.delete(remote_file)
                    print(f"  ✓ Deleted {remote_file}")
                except ftplib.error_perm:
                    print(f"  - Skip {remote_file}: Permission denied")
                except Exception as exc:
                    print(f"  - Skip {remote_file}: {exc}")
        else:
            print("✓ No orphaned files to remove")

        ftp.quit()
        print("\n✅ Sync complete! (Local is source of truth)")
    except Exception as exc:
        print(f"✗ Error: {exc}", file=sys.stderr)
        sys.exit(1)


def download(config: Config) -> None:
    try:
        validate_config(config)
        ftp = connect_ftp(config)

        print("\n📥 Downloading files:")
        for filename in config.download_files:
            try:
                local_file = config.local_dir / filename
                with open(local_file, "wb") as local_handle:
                    ftp.retrbinary(f"RETR {filename}", local_handle.write)
                print(f"  ✓ {filename}")
            except ftplib.error_perm:
                print(f"  - {filename} (not found on server)")
            except Exception as exc:
                print(f"  - {filename}: {exc}")

        ftp.quit()
        print("\n✅ Download complete!")
    except Exception as exc:
        print(f"✗ Error: {exc}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    config = load_config()

    if len(sys.argv) < 2:
        print("Usage: python3 syncftp.py [upload|download|sync]")
        print("  upload   - Upload local files and delete remote files not in local")
        print("  download - Download selected files from server")
        print("  sync     - Alias to upload")
        sys.exit(1)

    command = sys.argv[1].lower().strip()

    if command in {"upload", "sync"}:
        if command == "sync":
            print("🔄 Running SMART SYNC (local is source of truth)...")
        upload(config)
    elif command == "download":
        download(config)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
