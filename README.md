# syncftp

A lightweight FTP sync script for static/web project deployment.

This repository was built as a learning-oriented tool to support my web development study workflow while still being reusable by other developers.

## Highlights

- Upload local files to an FTP server
- Keep local files as source of truth
- Delete remote orphan files (within current script behavior)
- **Upload individual files for quick fixes** (new in this version)
- **VS Code integration with tasks.json** (new in this version)
- Ignore paths via `.ftpignore`
- Externalized configuration via `.env`
- Configurable workspace paths via environment variables

## Technologies

- Python 3
- Standard library modules only (`ftplib`, `pathlib`, `fnmatch`, `os`, `sys`)

## Repository Structure

- `syncftp.py` — canonical script entrypoint
- `.env.example` — safe configuration template
- `.ftpignore` — ignore pattern file example
- `LICENSE` — BSD-3-Clause license (requires keeping copyright notice)

## Quick Start

1. Copy the environment template:

```bash
cp .env.example .env
```

2. Edit `.env` with your FTP credentials and paths.

3. Run one of the commands:

```bash
python3 syncftp.py upload
python3 syncftp.py download
python3 syncftp.py sync
```

## Commands

### `upload` / `sync`
Uploads all local files and removes remote files not present locally (full synchronization).

```bash
python3 syncftp.py upload
# or (alias):
python3 syncftp.py sync
```

**Use case:** Complete deployment or full site synchronization.

**Note:** Deletes remote orphans—use with caution.

### `download`
Downloads specific files from the server (configured in `.env` via `DOWNLOAD_FILES`).

```bash
python3 syncftp.py download
```

### `upload-file` (NEW)
Uploads a single file without removing remote orphans.

```bash
python3 syncftp.py upload-file <relative_path>
```

**Examples:**

```bash
# Upload a file in the root
python3 syncftp.py upload-file index.html

# Upload a file in a subdirectory
python3 syncftp.py upload-file restaurante/gestao/painel.php
```

**Use case:** Quick bug fixes during development.

**⚠️ Important:** Single-file upload does **not** remove remote orphans. After uploading fixes, run `sync` to ensure full consistency.

### `setup-vscode` (NEW)
Generates VS Code `tasks.json` configuration for syncftp integration.

```bash
python3 syncftp.py setup-vscode
```

**What it does:**
- Creates/updates `.vscode/tasks.json` in your workspace
- Adds four new tasks for fast FTP operations:
  - **FTP Upload (syncftp)** — full sync with orphan cleanup
  - **FTP Download (syncftp)** — download specified files
  - **FTP: Upload Current File (syncftp)** — upload the file you're currently editing
  - **FTP: Upload File (with prompt)** — upload any file (path pre-filled from current file)

**How to use:**
1. Run `python3 syncftp.py setup-vscode` once
2. In VS Code, press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Linux/Windows)
3. Type "Tasks: Run Task"
4. Select your desired FTP task

**Quick workflows:**

*Scenario 1: Upload the file you're editing*
- Open `restaurante/gestao/painel.php`
- Run task "FTP: Upload Current File (syncftp)"
- ✅ Instant upload, no prompts

*Scenario 2: Upload a different file*
- Run task "FTP: Upload File (with prompt)"
- Prompt appears with current file path pre-filled
- Edit or confirm the path
- ✅ Upload starts

**Benefits:**
- No need to open terminal for common operations
- Auto-detection of current file for instant uploads
- Pre-filled prompts reduce typing
- Integration directly in VS Code workflow

## Configuration

The script reads configuration from environment variables and from a local `.env` file.

Required:

- `FTP_USER`
- `FTP_PASS`

Common optional values:

- `FTP_HOST` (default: `ftpupload.net`)
- `FTP_PORT` (default: `21`)
- `FTP_PATH` (default: `/htdocs`)
- `WORKSPACE_DIR` (default: parent folder of script)
- `SITE_SUBDIR` (default: `al-page-gd`)
- `WORKSPACE_PREFIX` (default: same as `SITE_SUBDIR`)
- `PASSIVE_MODE` (default: `true`)
- `CONNECTION_TIMEOUT` (default: `10`)
- `UNWANTED_REMOTE_ENTRIES` (comma-separated)
- `DOWNLOAD_FILES` (comma-separated)

## Security Notes

- Never commit `.env` with real credentials.
- Rotate FTP credentials immediately if they were ever exposed.
- Keep the repository private while cleaning sensitive history, if needed.

## .ftpignore Patterns

The script supports glob-like matching to exclude files and directories from synchronization.

Examples:

```txt
# Ignore documentation files
*.md
*.txt

# Ignore a specific file in a subdirectory
path/to/temporary_file.html
```

## Educational & Professional Context

This project is designed as a lightweight, reusable tool for developers who need reliable FTP synchronization without complex dependencies. It prioritizes simplicity, transparency, and educational value.

## Development Notes

This project was developed with an emphasis on clarity, maintainability, and pragmatic design decisions. The code prioritizes readability and ease of customization for different deployment scenarios.

## License

This project is licensed under the **BSD 3-Clause License**.

For legal terms, see `LICENSE`.
