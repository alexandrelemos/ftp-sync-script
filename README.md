# syncftp

A lightweight FTP sync script for static/web project deployment.

This repository was built as a learning-oriented tool to support my web development study workflow while still being reusable by other developers.

## Highlights

- Upload local files to an FTP server
- Keep local files as source of truth
- Delete remote orphan files (within current script behavior)
- Ignore paths via `.ftpignore`
- Externalized configuration via `.env`
- Defaults to syncing only `al-page-gd` under your workspace

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

The script supports glob-like matching with plain and prefixed candidates.

Examples:

```txt
# Ignore a specific file
al-page-gd/restaurante/gestao/tmp_html_gestor.html

# Ignore Markdown files under al-page-gd
al-page-gd/*.md
al-page-gd/**/*.md
```

## Educational Context

I (Al) am a student and this project is primarily educational. It is shared publicly because it may still be useful for others and because open feedback helps improve implementation quality.

## AI Usage Disclosure

Parts of this project were developed with AI assistance for drafting, refactoring, and documentation support. Final review, validation, and responsibility remain with the repository owner.

## License

This project is licensed under the **BSD 3-Clause License**.

For legal terms, see `LICENSE`. Attribution to the original author (`Alexandre Lemos (Al)`) must be preserved in redistributions.
