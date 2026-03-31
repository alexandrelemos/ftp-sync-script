#!/usr/bin/env python3
"""
FTP Sync Script for InfinityFree by Al (http://al.page.gd)
Syncs local files to InfinityFree hosting
LOCAL IS SOURCE OF TRUTH - deleting local files removes from server
Usage: python3 sync.py [upload|download|sync]
"""

import ftplib
import fnmatch
import os
import sys
from pathlib import Path, PurePosixPath

# Configuration
FTP_HOST = "ftpupload.net"
FTP_PORT = 21
FTP_USER = "USERNAME_HERE"
FTP_PASS = "PASSWORD_HERE"
FTP_PATH = "/htdocs"

LOCAL_DIR = Path(__file__).parent.parent
FTP_IGNORE_FILE = Path(__file__).parent / ".FtpIgnore"
IGNORE_FILES = {'.vscode', '.git', '.DS_Store', 'node_modules', '.gitignore', 'sync.py', '.ftpkr.json', 'vscode', '.gitkeep', '.prettierrc'}
IGNORE_DIRS = {'.vscode', '.git', '__pycache__', 'node_modules', 'vscode'}

def load_ftp_ignore_patterns():
    """Load ignore patterns from .FtpIgnore file next to this script."""
    patterns = []
    if not FTP_IGNORE_FILE.exists():
        return patterns

    try:
        with FTP_IGNORE_FILE.open('r', encoding='utf-8') as ignore_file:
            for raw_line in ignore_file:
                line = raw_line.strip().replace('\\', '/')
                if not line or line.startswith('#'):
                    continue

                while line.startswith('/'):
                    line = line[1:]

                if line:
                    patterns.append(line)
    except Exception as exc:
        print(f"- Warning: could not read {FTP_IGNORE_FILE.name}: {exc}")

    return patterns

def matches_ignore_pattern(rel_path, name, patterns):
    """Check if path/name matches any ignore pattern."""
    normalized = rel_path.replace('\\', '/')
    workspace_relative = f"al-page-gd/{normalized}"
    candidates = [normalized, workspace_relative, name]

    for pattern in patterns:
        for candidate in candidates:
            if fnmatch.fnmatch(candidate, pattern):
                return True
            if PurePosixPath(candidate).match(pattern):
                return True

    return False

def get_local_files():
    """Get all files in local directory to sync"""
    ignore_patterns = load_ftp_ignore_patterns()
    files = []
    for root, dirs, filenames in os.walk(LOCAL_DIR):
        # Filter ignored directories
        root_path = Path(root)
        kept_dirs = []
        for dirname in dirs:
            if dirname in IGNORE_DIRS:
                continue

            dir_rel_path = (root_path / dirname).relative_to(LOCAL_DIR)
            dir_rel = str(dir_rel_path).replace('\\', '/')
            if matches_ignore_pattern(dir_rel, dirname, ignore_patterns):
                continue

            kept_dirs.append(dirname)

        dirs[:] = kept_dirs

        for filename in filenames:
            if filename in IGNORE_FILES:
                continue

            full_path = root_path / filename
            rel_path = full_path.relative_to(LOCAL_DIR)
            rel_path_str = str(rel_path).replace('\\', '/')
            if matches_ignore_pattern(rel_path_str, filename, ignore_patterns):
                continue

            files.append((full_path, rel_path_str))

    return files

def get_remote_files(ftp):
    """Get list of remote files to sync (fast, non-recursive)"""
    remote_files = set()
    try:
        # Only list root level
        for item in ftp.nlst('.'):
            if item not in ('.', '..', './.', './..'):
                # Clean up FTP path artifacts
                clean_item = item.replace('./', '')
                if clean_item and clean_item not in ('.', '..'):
                    remote_files.add(clean_item)

        # Check for imgs folder
        try:
            ftp.cwd('imgs')
            for img in ftp.nlst('.'):
                if img not in ('.', '..', './.', './..'):
                    clean_img = img.replace('./', '')
                    if clean_img and clean_img not in ('.', '..'):
                        remote_files.add(f'imgs/{clean_img}')
            ftp.cwd('..')
        except ftplib.error_perm:
            pass
    except ftplib.all_errors:
        pass

    return remote_files

def upload():
    """Upload local files to server and delete server files not in local"""
    try:
        ftp = ftplib.FTP()
        print(f"Connecting to {FTP_HOST}:{FTP_PORT}...")
        ftp.connect(FTP_HOST, FTP_PORT, timeout=10)
        ftp.set_pasv(True)
        ftp.login(FTP_USER, FTP_PASS)
        print(f"✓ Connected and logged in")

        ftp.cwd(FTP_PATH)
        print(f"✓ Changed to {FTP_PATH}")

        # Get local files
        local_files = get_local_files()
        local_paths = {rel_path for _, rel_path in local_files}

        print(f"\n📤 Uploading {len(local_files)} file(s):")

        # Upload all local files
        for local_path, rel_path in local_files:
            # Create remote directories if needed
            remote_dir = '/'.join(rel_path.split('/')[:-1])
            if remote_dir:
                # Build directory path incrementally from /htdocs
                dirs_to_create = remote_dir.split('/')
                current_path = FTP_PATH
                for dir_part in dirs_to_create:
                    current_path = current_path + '/' + dir_part
                    try:
                        ftp.mkd(current_path)
                        print(f"  📁 Created directory: {dir_part}")
                    except ftplib.error_perm:
                        pass  # Directory already exists

            # Upload file
            try:
                # Use absolute path from FTP_PATH
                full_remote_path = f"{FTP_PATH}/{rel_path}"
                with open(local_path, 'rb') as f:
                    ftp.storbinary(f'STOR {full_remote_path}', f)
                print(f"  ✓ {rel_path}")
            except Exception as e:
                print(f"  ✗ {rel_path}: {e}")

        # Get remote files and delete those not in local
        print(f"\n🗑️  Checking for removed files...")
        remote_files = get_remote_files(ftp)
        remote_files_set = set(remote_files)
        files_to_delete = remote_files_set - local_paths

        if files_to_delete:
            print(f"Removing {len(files_to_delete)} orphaned file(s) from server:")
            for remote_file in sorted(files_to_delete):
                try:
                    ftp.delete(remote_file)
                    print(f"  ✓ Deleted {remote_file}")
                except ftplib.error_perm as e:
                    print(f"  - Skip {remote_file}: Permission denied")
                except Exception as e:
                    print(f"  - Skip {remote_file}: {e}")
        else:
            print(f"✓ No orphaned files to remove")

        ftp.quit()
        print(f"\n✅ Sync complete! (Local is source of truth)")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

def download():
    """Download files from server (server overwrites local)"""
    try:
        ftp = ftplib.FTP()
        print(f"Connecting to {FTP_HOST}:{FTP_PORT}...")
        ftp.connect(FTP_HOST, FTP_PORT, timeout=10)
        ftp.set_pasv(True)
        ftp.login(FTP_USER, FTP_PASS)
        print(f"✓ Connected and logged in")

        ftp.cwd(FTP_PATH)
        print(f"✓ Changed to {FTP_PATH}")

        # Simple download of main HTML files
        files_to_download = ['index.html', 'index2.html']
        print(f"\n📥 Downloading files:")

        for filename in files_to_download:
            try:
                local_file = LOCAL_DIR / filename
                with open(local_file, 'wb') as f:
                    ftp.retrbinary(f'RETR {filename}', f.write)
                print(f"  ✓ {filename}")
            except ftplib.error_perm:
                print(f"  - {filename} (not found on server)")
            except Exception as e:
                print(f"  - {filename}: {e}")

        ftp.quit()
        print(f"\n✅ Download complete!")

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)

def sync():
    """Smart sync: upload + delete (local is source of truth)"""
    print("🔄 Running SMART SYNC (local is source of truth)...")
    upload()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 sync.py [upload|download|sync]")
        print("  upload  - Upload local files, delete remote files not in local")
        print("  download - Download from server")
        print("  sync    - Smart sync (same as upload)")
        sys.exit(1)

    command = sys.argv[1].lower()
    if command == 'upload' or command == 'sync':
        upload()
    elif command == 'download':
        download()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

