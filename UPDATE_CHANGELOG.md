# syncftp Update Summary

**Date:** April 7, 2026  
**Commit:** `5531e39`  
**Branch:** `main`  
**Repository:** https://github.com/alexandrelemos/ftp-sync-script

## Changes Made

### 1. New Feature: `upload-file` Command
Added a new command to upload individual files for quick fixes during development.

**Syntax:**
```bash
python3 syncftp.py upload-file <relative_path>
```

**Examples:**
```bash
python3 syncftp.py upload-file painel.php
python3 syncftp.py upload-file restaurante/gestao/painel.php
```

**Key Characteristics:**
- ✅ Validates file existence before upload
- ✅ Creates remote directories automatically
- ✅ Provides clear feedback
- ⚠️ Does NOT remove remote orphans (intentional for speed)
- ⚠️ Users should run `sync` afterward to ensure full consistency

### 2. Documentation Updates

Updated `README.md` with:
- New "Commands" section with detailed descriptions of each command
- Clear use cases for each operation
- Warnings about orphan file management
- Example usage patterns

### 3. Code Changes

**Modified Files:**
- `syncftp.py`: Added `upload_file()` function and updated `main()` to handle new command
- `README.md`: Added command documentation and examples

**Commit Message:**
```
feat: add upload-file command for selective file uploads

- New command: 'upload-file <path>' for uploading individual files
- Useful for quick bug fixes during development
- Does not remove remote orphans (for speed)
- Includes validation for file existence and readability
- Updated README with new command documentation and examples
- Added clear warnings about orphan file management
```

## Security & Privacy

✅ Verified that confidential files remain protected:
- `.env` is in `.gitignore` (not committed)
- FTP credentials never exposed in repository
- Only safe configuration templates committed (`.env.example`)

## Workflow for Future Use

### For Quick Bug Fixes:
```bash
# 1. Edit file locally
vi restaurante/gestao/painel.php

# 2. Upload quickly
python3 syncftp.py upload-file restaurante/gestao/painel.php

# 3. Later, sync fully to ensure consistency
python3 syncftp.py sync
```

### For Complete Deployment:
```bash
python3 syncftp.py sync
```

## Version History
- **Previous:** Single-file uploads not supported
- **Now:** Supports both full sync and selective file uploads
