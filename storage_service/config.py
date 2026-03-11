"""Configuration management for Storage Service"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class Config:
    """Manages storage service configuration"""

    # Default media type configurations
    MEDIA_TYPES = {
        "photos": {
            "name": "photos",
            "extensions": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".svg", ".heic", ".heif"},
            "directory": "Photos",
        },
        "videos": {
            "name": "videos",
            "extensions": {".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm", ".m4v"},
            "directory": "Videos",
        },
        "audio": {
            "name": "audio",
            "extensions": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".opus"},
            "directory": "Audio",
        },
        "documents": {
            "name": "documents",
            "extensions": {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".ppt", ".txt", ".rtf"},
            "directory": "Documents",
        },
    }

    # Default directory structure template
    DEFAULT_STRUCTURE = "{media_type}/{year}/{month}"

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration

        Args:
            config_file: Path to config file (YAML/JSON). If not provided, uses defaults.
        """
        self.config_file = config_file
        self.data: Dict[str, Any] = self._load_or_create_config()

    def _load_or_create_config(self) -> Dict[str, Any]:
        """Load config from file or create defaults"""
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                if self.config_file.endswith(".json"):
                    return json.load(f)
                else:
                    return yaml.safe_load(f) or {}

        return {
            "media_types": self.MEDIA_TYPES,
            "directory_structure": self.DEFAULT_STRUCTURE,
            "enable_deduplication": True,
            "enable_integrity_check": True,
            "backup_metadata": True,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set configuration value"""
        self.data[key] = value

    def save(self, filepath: str) -> None:
        """Save configuration to file"""
        with open(filepath, "w") as f:
            if filepath.endswith(".json"):
                json.dump(self.data, f, indent=2)
            else:
                yaml.dump(self.data, f, default_flow_style=False)

    @staticmethod
    def get_media_type(file_extension: str) -> Optional[str]:
        """
        Determine media type from file extension

        Args:
            file_extension: File extension (e.g., '.jpg')

        Returns:
            Media type name or None if not recognized
        """
        ext = file_extension.lower()
        for media_type, config in Config.MEDIA_TYPES.items():
            if ext in config["extensions"]:
                return media_type
        return None

    @staticmethod
    def get_suggested_structure() -> str:
        """Get the suggested directory structure"""
        return """
SUGGESTED DIRECTORY STRUCTURE:
==============================

BackupRoot/
├── Photos/
│   ├── 2025/
│   │   ├── 01_January/
│   │   │   └── [photo files]
│   │   ├── 02_February/
│   │   │   └── [photo files]
│   │   └── ...
│   ├── 2024/
│   │   └── ...
│   └── ...
├── Videos/
│   ├── 2025/
│   │   ├── 01_January/
│   │   └── ...
│   └── ...
├── Audio/
│   ├── 2025/
│   │   ├── 01_January/
│   │   └── ...
│   └── ...
├── Documents/
│   ├── 2025/
│   │   ├── 01_January/
│   │   └── ...
│   └── ...
└── .storage_service/
    └── storage.db             # SQLite database containing:
                               #   - Backup registry (all backed up files)
                               #   - Hash index (deduplication tracking)
                               #   - File metadata

KEY FEATURES:
=============
✓ Organized by Media Type (Photos, Videos, Audio, Documents)
✓ Organized by Date (Year > Month)
✓ Deduplication (Prevents storing duplicate files)
✓ Integrity Checking (SHA256 hash verification)
✓ Backup Metadata (Tracks file history and sources)
"""
