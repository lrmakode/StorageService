# Storage Service Architecture Guide

## Overview

StorageService is a modular Python-based media backup system designed to help users organize and back up their media files efficiently. The architecture follows a layered design pattern with clear separation of concerns.

## High-Level Architecture

```
┌─────────────────────────────────────────┐
│         CLI Interface (cli.py)          │
│    Interactive & Command-Line Access    │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│      Core Storage Service (core.py)     │
│   Main Backup & Organization Logic      │
└────────────┬────────────────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
┌───▼──┐  ┌─▼──┐  ┌──▼────┐
│Media │  │Dedu│  │Config │
│Detec│  │plic│  │Manager │
│tor  │  │ator│  │        │
└─────┘  └────┘  └────────┘
```

## Module Descriptions

### 1. Config Module (`config.py`)
**Responsibility:** Configuration management and media type definitions

**Key Classes:**
- `Config`: Manages service configuration
  - Provides media type mappings
  - Handles directory structure templates
  - Loads/saves configuration files
  - Determines media type from file extension

**Features:**
- Built-in media type definitions (photos, videos, audio, documents)
- Extensible configuration system
- YAML/JSON configuration file support

### 2. Media Detector Module (`media_detector.py`)
**Responsibility:** File type detection and categorization

**Key Classes:**
- `MediaDetector`: Detects and categorizes media files
  - Identifies file type from extension
  - Validates supported media
  - Categorizes multiple files
  - Gets directory names for media types

**Dependencies:**
- Config module

**Key Methods:**
- `detect_media_type(filepath)` → Returns media type
- `is_supported_media(filepath)` → Boolean check
- `categorize_files(file_paths)` → Dict of categorized files

### 3. Deduplicator Module (`deduplicator.py`)
**Responsibility:** Duplicate detection and index management

**Key Classes:**
- `Deduplicator`: Manages file hashing and duplicate detection
  - Calculates SHA256 hashes
  - Maintains hash index
  - Detects duplicates
  - Tracks file groups with identical content

**Key Methods:**
- `calculate_file_hash(filepath)` → SHA256 hex digest
- `register_file(filepath)` → Registers file in index
- `is_duplicate(filepath)` → Boolean check
- `get_duplicate_files(filepath)` → List of duplicate paths
- `get_duplicate_groups()` → Dict of all duplicate groups
- `get_stats()` → Statistics dictionary

**Index Format (JSON):**
```json
{
  "hash1": ["file1_path", "file2_path"],
  "hash2": ["file3_path"]
}
```

### 4. Core Module (`core.py`)
**Responsibility:** Main storage service orchestration

**Key Classes:**
- `StorageService`: Main service class
  - Orchestrates backup operations
  - Manages directory structure
  - Maintains backup registry
  - Provides statistics and reporting

**Dependencies:**
- Config, MediaDetector, Deduplicator

**Key Methods:**
- `backup_file(filepath, skip_duplicates)` → Boolean
- `backup_directory(source_dir, skip_duplicates, show_progress)` → Stats dict
- `get_backup_structure()` → Directory structure dict
- `get_statistics()` → Statistics dict
- `print_structure()` → Pretty-print directory tree

**Registry Format (JSON):**
```json
{
  "/source/file.jpg": [
    {
      "target": "/backup/Photos/2025/01_January/file.jpg",
      "timestamp": "2025-01-15T10:30:00",
      "status": "success"
    }
  ]
}
```

### 5. CLI Module (`cli.py`)
**Responsibility:** Command-line interface and user interaction

**Key Functions:**
- `backup()` - Direct backup command
- `show_structure()` - Display backup structure
- `stats()` - Show statistics
- `show_config()` - Display suggested structure
- `interactive()` - Interactive backup mode

**Dependencies:**
- Click (CLI framework)
- StorageService, Config

## Data Flow

### Backup Process Flow

```
User Input
    │
    ▼
┌─────────────────┐
│  CLI Interface  │ → Parse arguments
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│   StorageService.backup_directory│
└────────┬────────────────────────┘
         │
         ├─→ Collect Files ─→ os.walk / rglob
         │
         ├─→ For Each File:
         │   ├─→ MediaDetector.detect_media_type()
         │   │   └─→ Determine target directory
         │   │
         │   ├─→ Deduplicator.is_duplicate()
         │   │   ├─→ Calculate SHA256 hash
         │   │   └─→ Check hash index
         │   │
         │   ├─→ Copy File (if not duplicate)
         │   │   └─→ shutil.copy2()
         │   │
         │   └─→ Register in Registry & Index
         │       ├─→ Update hash_index.json
         │       └─→ Update backup_registry.json
         │
         ▼
    Return Statistics
```

## Directory Organization Strategy

### Organizational Hierarchy
1. **Level 1:** Media Type (Photos, Videos, Audio, Documents)
2. **Level 2:** Year (2025, 2024, etc.)
3. **Level 3:** Month (01_January, 02_February, etc.)
4. **Level 4:** Files

### Why This Structure?
- **Intuitive:** Matches natural media organization
- **Scalable:** Handles large collections efficiently
- **Chronological:** Date-based access patterns
- **Type-based:** Easy to find specific media types

## Internal Metadata

### Backup Registry (`backup_registry.json`)
**Purpose:** Track backup history and status

**Structure:**
```json
{
  "/path/to/source/file.jpg": [
    {
      "target": "/backup/Photos/2025/01_January/file.jpg",
      "timestamp": "2025-01-15T10:30:45.123456",
      "status": "success|skipped_duplicate|error"
    }
  ]
}
```

### Hash Index (`hash_index.json`)
**Purpose:** Enable rapid duplicate detection

**Structure:**
```json
{
  "abc123...def456": [
    "/backup/Photos/2025/01_January/photo1.jpg",
    "/backup/Photos/2025/02_February/photo2.jpg"
  ]
}
```

### Backup Metadata (`backup_metadata.json`)
**Purpose:** Store additional backup metadata (future use)

## Extension Points

### Adding New Media Types
```python
# In config.py, update MEDIA_TYPES:
"ebooks": {
    "name": "ebooks",
    "extensions": {".epub", ".mobi", ".azw"},
    "directory": "eBooks",
}
```

### Custom Directory Structure
```python
# Override in Config:
config.set("directory_structure", "{media_type}/{custom_folder}/{year}")
```

### Adding New Features
- Extend `StorageService` class
- Add new detection modules
- Create new CLI commands

## Error Handling

### Per-File Failures
- Individual file errors are caught and logged
- Backup continues with remaining files
- Failures tracked in backup_registry.json with `"error: <message>"` status

### Directory Failures
- Invalid source directory → Error message
- Invalid backup root → Auto-created if possible
- Permission errors → Caught and reported

## Performance Considerations

### Hash Calculation
- Reads file in 8KB chunks to handle large files
- Only calculated once per file
- Results cached in hash_index.json

### Duplicate Detection
- O(1) lookup in hash index
- No file comparison after first backup
- Efficient for large backups

### File Operations
- Uses `shutil.copy2()` to preserve metadata
- Progress bar for user feedback (optional)
- Batch registry saves to reduce I/O

## Security Considerations

### Current Implementation
- File ownership preserved via shutil.copy2()
- Permissions preserved
- Metadata maintained

### Future Enhancements
- Optional encryption
- Access control lists
- Backup integrity verification

## Testing Strategy

### Unit Tests Organization
- `TestConfig`: Configuration loading and media type detection
- `TestMediaDetector`: File categorization and detection
- `TestDeduplicator`: Hash calculation and duplicate detection
- `TestStorageService`: Integration tests (could be added)

### Running Tests
```bash
python -m unittest discover tests/
python -m pytest tests/  # If pytest installed
```

---

**Architecture Version:** 1.0
**Last Updated:** March 2026
