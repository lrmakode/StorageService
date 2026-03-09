"""Media type detection module"""

import os
from pathlib import Path
from typing import Optional, Dict
from .config import Config


class MediaDetector:
    """Detects and categorizes media files"""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize media detector

        Args:
            config: Config object with media type definitions
        """
        self.config = config or Config()

    def detect_media_type(self, filepath: str) -> Optional[str]:
        """
        Detect media type of a file

        Args:
            filepath: Path to the file

        Returns:
            Media type name or None if unknown
        """
        file_ext = Path(filepath).suffix.lower()
        return self.config.get_media_type(file_ext)

    def is_supported_media(self, filepath: str) -> bool:
        """
        Check if file is supported media

        Args:
            filepath: Path to the file

        Returns:
            True if file is supported media, False otherwise
        """
        return self.detect_media_type(filepath) is not None

    def get_media_directory_name(self, media_type: str) -> str:
        """
        Get the directory name for a media type

        Args:
            media_type: Media type name

        Returns:
            Directory name from config
        """
        media_config = self.config.get("media_types", {}).get(media_type, {})
        return media_config.get("directory", media_type.capitalize())

    def categorize_files(self, file_paths: list) -> Dict[str, list]:
        """
        Categorize files by media type

        Args:
            file_paths: List of file paths

        Returns:
            Dictionary with media types as keys and file lists as values
        """
        categorized = {}

        for filepath in file_paths:
            if not os.path.exists(filepath):
                continue

            media_type = self.detect_media_type(filepath)
            if media_type:
                if media_type not in categorized:
                    categorized[media_type] = []
                categorized[media_type].append(filepath)

        return categorized
