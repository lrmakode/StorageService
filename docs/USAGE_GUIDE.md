# Usage Guide - StorageService

## Quick Start

### 1. Installation
```bash
cd /home/avyagrah/workspace/StorageService
pip install -r requirements.txt
pip install -e .
```

### 2. First Backup (Interactive Mode)
```bash
storage-service interactive
```

Follow the prompts to back up your media files.

## Common Use Cases

### Scenario 1: Backup Your Photo Collection

```bash
storage-service backup \
  --backup-root ~/BackupDrive/MediaBackup \
  --source ~/Pictures
```

**Result:**
```
~/BackupDrive/MediaBackup/
├── Photos/
│   └── 2025/
│       └── 01_January/
│           ├── vacation_photo1.jpg
│           └── vacation_photo2.png
```

### Scenario 2: Backup Multiple Media Types

```bash
storage-service backup \
  -b ~/External_SSD/Backup \
  -s ~/MediaFolder
```

For a directory containing:
```
~/MediaFolder/
├── vacation.mp4
├── family_photo.jpg
├── my_song.mp3
└── document.pdf
```

Creates:
```
~/External_SSD/Backup/
├── Photos/
│   └── 2025/01_January/family_photo.jpg
├── Videos/
│   └── 2025/01_January/vacation.mp4
├── Audio/
│   └── 2025/01_January/my_song.mp3
└── Documents/
    └── 2025/01_January/document.pdf
```

### Scenario 3: Check Backup Status

```bash
# View the structure
storage-service show-structure -b ~/BackupDrive/MediaBackup

# Get detailed statistics
storage-service stats -b ~/BackupDrive/MediaBackup
```

### Scenario 4: Avoid Duplicates on Second Backup

```bash
# First backup
storage-service backup \
  -b ~/Backup \
  -s ~/Pictures

# Add new photos to source
# ...

# Second backup (skips duplicates by default)
storage-service backup \
  -b ~/Backup \
  -s ~/Pictures
```

The service will:
- Skip files with identical content (based on SHA256)
- Only copy new files
- Report statistics showing how many were skipped

## Advanced Usage

### Python API for Custom Applications

#### Basic Backup
```python
from storage_service import StorageService

service = StorageService(backup_root="/mnt/backup")
stats = service.backup_directory("/home/user/Pictures")

print(f"Backed up: {stats['successful']} files")
print(f"Skipped: {stats['skipped']} duplicates")
print(f"Failed: {stats['failed']} files")
```

#### Check for Duplicates Before Backup
```python
from storage_service import StorageService

service = StorageService(backup_root="/mnt/backup")

# Check if specific file is duplicate
if service.deduplicator.is_duplicate("/home/user/Pictures/photo.jpg"):
    print("This file is already backed up!")
else:
    service.backup_file("/home/user/Pictures/photo.jpg")
```

#### View Duplicate Groups
```python
from storage_service import StorageService

service = StorageService(backup_root="/mnt/backup")
duplicates = service.deduplicator.get_duplicate_groups()

for hash_value, files in duplicates.items():
    print(f"\nDuplicate group (hash: {hash_value[:8]}...):")
    for file_path in files:
        print(f"  - {file_path}")
```

#### Custom Organization Logic
```python
from storage_service import StorageService

service = StorageService(backup_root="/mnt/backup")

# Get organized structure
structure = service.get_backup_structure()

# Count files by media type
for media_type, content in structure.items():
    file_count = count_files(content)
    print(f"{media_type}: {file_count} files")

def count_files(obj):
    """Recursively count files in structure"""
    count = len(obj.get('files', []))
    for key, value in obj.items():
        if key != 'files' and isinstance(value, dict):
            count += count_files(value)
    return count
```

### Batch Processing

```bash
#!/bin/bash
# backup_all.sh - Backup multiple source directories

BACKUP_ROOT="/mnt/backup"

for source_dir in ~/Pictures ~/Videos ~/Documents; do
    echo "Backing up: $source_dir"
    storage-service backup \
        -b "$BACKUP_ROOT" \
        -s "$source_dir"
    echo "---"
done
```

### Incremental Backups

```bash
# Day 1: Initial backup
storage-service backup -b ~/Backup -s ~/Pictures

# Day 2: Backup only new/changed files
# (Duplicates from Day 1 are skipped automatically)
storage-service backup -b ~/Backup -s ~/Pictures

# View what was added
storage-service stats -b ~/Backup
```

## Command Reference

### Main Commands

#### `storage-service backup`
Backup media files from a source directory

**Usage:**
```bash
storage-service backup --backup-root PATH --source PATH [OPTIONS]
```

**Options:**
- `-b, --backup-root TEXT` - Root directory for backups (required)
- `-s, --source TEXT` - Source directory to backup (required)
- `--skip-duplicates / --no-skip-duplicates` - Skip duplicate files (default: True)

**Examples:**
```bash
storage-service backup -b ~/Backup -s ~/Pictures
storage-service backup --backup-root /mnt/ssd/backup --source ~/Downloads
storage-service backup -b ~/Backup -s ~/Pictures --no-skip-duplicates
```

#### `storage-service show-structure`
Display the current backup directory structure

**Usage:**
```bash
storage-service show-structure --backup-root PATH
```

**Example Output:**
```
Backup Structure:
==================================================

PHOTOS/
  ├── 2025/
  │   ├── 01_January/
  │   │   ├── (50 files)
  │   └── 02_February/
  │       ├── (30 files)
  └── 2024/
      └── ...

VIDEOS/
  └── 2025/
      └── 01_January/
          ├── (15 files)
```

#### `storage-service stats`
Show detailed backup statistics

**Usage:**
```bash
storage-service stats --backup-root PATH
```

**Example Output:**
```
📊 Backup Statistics
==================================================
Backup Root: /home/user/Backup
Total Files Backed Up: 500

🔄 Deduplication Stats:
   Total Unique Hashes: 450
   Total Files Tracked: 500
   Duplicate Groups: 5
   Total Duplicate Files: 50
```

#### `storage-service show-config`
Display the suggested directory structure

**Usage:**
```bash
storage-service show-config
```

#### `storage-service interactive`
Interactive backup mode (guided wizard)

**Usage:**
```bash
storage-service interactive [OPTIONS]
```

**Options:**
- `-b, --backup-root TEXT` - Pre-set backup root (optional)
- `-s, --source TEXT` - Pre-set source directory (optional)

**Example:**
```bash
storage-service interactive
storage-service interactive -b ~/Backup
```

## Troubleshooting Guide

### Problem: Files not being backed up

**Symptoms:**
- Command runs but shows 0 successful backups
- Files exist but aren't copied

**Solutions:**

1. **Check file extension is supported:**
   ```bash
   storage-service show-config
   ```
   Look for your file extension in the supported list.

2. **Verify file permissions:**
   ```bash
   ls -la ~/Pictures/your_file.jpg
   ```
   You need read permissions.

3. **Check path is correct:**
   ```bash
   ls -la ~/Pictures/  # Verify directory exists
   ```

### Problem: Permission denied error

**Error Message:**
```
❌ Error: Permission denied: '/path/to/backup'
```

**Solutions:**

1. **Check backup directory permissions:**
   ```bash
   ls -la ~/Backup
   chmod 755 ~/Backup
   ```

2. **Run with sudo (if necessary):**
   ```bash
   sudo storage-service backup -b /mnt/backup -s ~/Pictures
   ```

3. **Create backup directory with proper permissions:**
   ```bash
   mkdir -p ~/Backup
   chmod 755 ~/Backup
   ```

### Problem: Slow backup

**Solutions:**

1. **Check disk speed:**
   ```bash
   hdparm -Tt /dev/sdX  # Replace X with your disk
   ```

2. **For external drives:**
   - Use USB 3.0 or faster
   - Consider SSD for faster backup
   - Avoid network drives for initial backup

3. **Large files:**
   - Video files take longer to hash
   - This is normal and expected
   - Enable progress bar to monitor

### Problem: Disk space issues

**Solutions:**

1. **Check backup size:**
   ```bash
   du -sh ~/Backup
   du -sh ~/Backup/*  # By media type
   ```

2. **Find largest files:**
   ```bash
   find ~/Backup -type f -exec du -h {} \; | sort -hr | head -20
   ```

3. **Check deduplication effectiveness:**
   ```bash
   storage-service stats -b ~/Backup
   ```
   Look at "Total Duplicate Files" to see how much space duplicates save.

## Best Practices

### 1. Regular Backups
```bash
# Weekly backup script
#!/bin/bash
DATE=$(date +%A)
echo "Weekly backup on $DATE"
storage-service backup -b ~/Backup -s ~/Pictures
storage-service stats -b ~/Backup
```

### 2. Multiple Backup Locations
```bash
# Backup to external drive
storage-service backup -b /media/external/Backup -s ~/Pictures

# Also backup to cloud (future feature)
# storage-service backup -b s3://my-bucket/backup -s ~/Pictures
```

### 3. Monitor Backup Health
```bash
# Monthly check
storage-service stats -b ~/Backup
storage-service show-structure -b ~/Backup
```

### 4. Organize Source Before Backup
```bash
# Better: Already organized by type
~/MediaFolder/
├── Photos/
├── Videos/
└── Documents/

# Backup as a group
storage-service backup -b ~/Backup -s ~/MediaFolder
```

### 5. Use Descriptive Backup Root Names
```bash
# Good
~/ExternalDrive/2025_MediaBackup
~/NAS/FamilyPhotos_Backup

# Less clear
~/backup1
~/bkp
```

## Tips & Tricks

### Verify Backup Integrity
```python
from storage_service import StorageService

service = StorageService(backup_root="~/Backup")

# Check all files have hashes
stats = service.get_statistics()
print(f"Total files: {stats['total_backed_up_files']}")
print(f"Tracked files: {stats['deduplication']['total_files_tracked']}")

# Should be equal
```

### Find Similar Photos (Duplicates)
```python
from storage_service import StorageService

service = StorageService(backup_root="~/Backup")
duplicates = service.deduplicator.get_duplicate_groups()

if duplicates:
    print("Found duplicates!")
    for hash_val, files in duplicates.items():
        print(f"\nIdentical files:")
        for f in files:
            print(f"  {f}")
```

### Export Backup Manifest
```bash
# Get list of all backed-up files
find ~/Backup -type f ! -path "*/.storage_service/*" > manifest.txt
```

---

**Guide Version:** 1.0  
**Last Updated:** March 2026
