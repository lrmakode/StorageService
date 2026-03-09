# StorageService - Media Backup & Organization Tool

A Python-based storage service that backs up media files (photos, videos, audio, documents) and organizes them into an ideal directory structure with automatic deduplication and integrity checking.

## Features

✨ **Smart Media Organization**
- Automatically categorizes files by type (Photos, Videos, Audio, Documents)
- Organizes by date (Year > Month) based on file modification time
- Suggested directory structure for optimal organization

🔄 **Deduplication**
- SHA256 hash-based duplicate detection
- Prevents storing identical files multiple times
- Deduplication index tracking

✅ **Integrity & Tracking**
- Backup registry to track all backed-up files
- Metadata tracking for backup history
- File integrity verification

📊 **Statistics & Monitoring**
- Backup statistics and reports
- Deduplication metrics
- Backup directory structure visualization

## Project Structure

```
StorageService/
├── storage_service/           # Main package
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── media_detector.py      # Media type detection
│   ├── deduplicator.py        # Deduplication logic
│   ├── core.py                # Core storage service
│   └── cli.py                 # Command-line interface
├── tests/                     # Unit tests
├── docs/                      # Documentation
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
└── README.md                  # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip

### Setup

1. **Clone or navigate to the workspace:**
   ```bash
   cd /home/avyagrah/workspace/StorageService
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the package in development mode:**
   ```bash
   pip install -e .
   ```

## Usage

### Command Line Interface

#### 1. **Interactive Mode** (Recommended for beginners)
```bash
storage-service interactive
```
This will guide you through the backup process step-by-step.

#### 2. **Direct Backup**
```bash
storage-service backup --backup-root /path/to/backup --source /path/to/media
```

**Options:**
- `--backup-root, -b`: Root directory for backups (required)
- `--source, -s`: Source directory containing media files (required)
- `--skip-duplicates/--no-skip-duplicates`: Skip duplicate files (default: True)

**Example:**
```bash
storage-service backup -b ~/backup_storage -s ~/Pictures
```

#### 3. **View Backup Structure**
```bash
storage-service show-structure --backup-root /path/to/backup
```

#### 4. **View Statistics**
```bash
storage-service stats --backup-root /path/to/backup
```

#### 5. **Show Suggested Directory Structure**
```bash
storage-service show-config
```

### Python API

```python
from storage_service import StorageService, Config

# Initialize service
service = StorageService(backup_root="/path/to/backup")

# Backup a directory
stats = service.backup_directory(
    source_dir="/path/to/media",
    skip_duplicates=True,
    show_progress=True
)

print(f"Backed up {stats['successful']} files")

# View backup structure
service.print_structure()

# Get statistics
stats = service.get_statistics()
print(stats)
```

## Ideal Directory Structure

The service organizes backups as follows:

```
backup_root/
├── Photos/
│   ├── 2025/
│   │   ├── 01_January/
│   │   │   ├── photo1.jpg
│   │   │   ├── photo2.png
│   │   │   └── ...
│   │   ├── 02_February/
│   │   └── ...
│   ├── 2024/
│   └── ...
├── Videos/
│   ├── 2025/
│   │   ├── 01_January/
│   │   │   └── video.mp4
│   │   └── ...
│   └── ...
├── Audio/
│   ├── 2025/
│   │   ├── 01_January/
│   │   │   └── song.mp3
│   │   └── ...
│   └── ...
├── Documents/
│   ├── 2025/
│   │   ├── 01_January/
│   │   │   └── document.pdf
│   │   └── ...
│   └── ...
└── .storage_service/
    ├── backup_registry.json    # Tracks all backed up files
    ├── hash_index.json         # Deduplication index
    └── backup_metadata.json    # Metadata about backups
```

## Supported Media Types

### Photos
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tiff`, `.svg`

### Videos
- `.mp4`, `.mkv`, `.avi`, `.mov`, `.flv`, `.wmv`, `.webm`, `.m4v`

### Audio
- `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, `.m4a`, `.opus`

### Documents
- `.pdf`, `.docx`, `.doc`, `.xlsx`, `.xls`, `.pptx`, `.ppt`, `.txt`, `.rtf`

## Key Concepts

### Deduplication
The service uses SHA256 hashing to identify duplicate files. When a duplicate is detected:
- The file is not copied again
- The original location is recorded in the backup registry
- Deduplication metrics are tracked

### Backup Registry
A JSON file (`backup_registry.json`) that tracks:
- Source file paths
- Target backup locations
- Backup timestamps
- Backup status (success, skipped, error)

### Integrity Index
A JSON file (`hash_index.json`) that maintains:
- SHA256 hashes of all backed-up files
- List of files with identical content
- Helps identify duplicates on future backups

## Examples

### Example 1: Backup your Pictures folder
```bash
storage-service backup \
  --backup-root ~/MyBackup \
  --source ~/Pictures
```

### Example 2: View structure of existing backups
```bash
storage-service show-structure --backup-root ~/MyBackup
```

### Example 3: Get detailed statistics
```bash
storage-service stats --backup-root ~/MyBackup
```

### Example 4: Using Python API for custom logic
```python
from storage_service import StorageService

service = StorageService(backup_root="/mnt/backup")

# Get files organized by media type
structure = service.get_backup_structure()

for media_type, content in structure.items():
    print(f"\n{media_type}:")
    print(content)
```

## Configuration

The service uses sensible defaults, but you can customize behavior through the `Config` class:

```python
from storage_service import Config, StorageService

# Create custom config
config = Config()

# Access media type configurations
media_types = config.get("media_types")

# Create service with custom config
service = StorageService(backup_root="/path/to/backup", config=config)
```

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

Or using unittest:

```bash
python -m unittest discover tests/
```

## Troubleshooting

### Files not being backed up
1. Check if the file extension is supported
2. Verify source directory path is correct
3. Ensure you have read permissions on source files
4. Check write permissions on backup destination

### Disk space issues
1. Review deduplication statistics
2. Check for large video files using: `du -sh /path/to/backup`
3. Consider external storage for backup destination

### Permission errors
```bash
# Run with appropriate permissions
sudo storage-service backup -b /backup_path -s /source_path

# Or fix permissions
chmod -R 755 /backup_path
```

## Performance Tips

1. **Use deduplication** - Especially helpful for folders with similar files
2. **First run** - Initial backup may take longer as hashes are calculated
3. **Batch backups** - Group media files by type before backup
4. **External drives** - Use fast USB 3.0/3.1 or SSD for backup destination

## Future Enhancements

- [ ] Cloud backup support (AWS S3, Google Drive, Azure)
- [ ] Incremental backup (only backup changed files)
- [ ] Compression support
- [ ] Encryption for sensitive data
- [ ] Web UI for managing backups
- [ ] Automatic backup scheduling
- [ ] Backup restoration utilities
- [ ] Advanced filtering and search

## Contributing

Contributions are welcome! Areas for improvement:
- Additional cloud providers
- Performance optimizations
- Extended media type support
- GUI development

## License

MIT License

## Support

For issues or questions:
1. Check existing documentation
2. Review error messages carefully
3. Check file permissions and paths
4. Verify Python version compatibility

---

**Version:** 0.1.0

**Last Updated:** March 2026
