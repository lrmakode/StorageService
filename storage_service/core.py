"""Core storage service module"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    from tqdm import tqdm
except ImportError:
    # Fallback if tqdm is not installed
    def tqdm(iterable, **kwargs):
        return iterable

from .config import Config
from .media_detector import MediaDetector
from .deduplicator import Deduplicator
from .database import Database


class StorageService:
    """Main storage service for managing media backups"""

    def __init__(self, backup_root: str, config: Optional[Config] = None):
        """
        Initialize storage service

        Args:
            backup_root: Root directory for backups
            config: Configuration object
        """
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)

        self.config = config or Config()
        self.detector = MediaDetector(self.config)
        
        # Initialize SQLite database
        self.db_path = str(self.backup_root / ".storage_service" / "storage.db")
        self.db = Database(self.db_path)
        self.deduplicator = Deduplicator(self.db_path)

    def _get_target_path(self, filepath: str) -> Optional[Path]:
        """
        Determine target backup path for a file

        Args:
            filepath: Source file path

        Returns:
            Target backup path or None if media type not supported
        """
        media_type = self.detector.detect_media_type(filepath)
        if not media_type:
            return None

        file_stat = os.stat(filepath)
        file_mtime = datetime.fromtimestamp(file_stat.st_mtime)

        # Get directory names from config
        media_dir = self.detector.get_media_directory_name(media_type)
        year = file_mtime.strftime("%Y")
        month = file_mtime.strftime("%m_%B")  # e.g., "01_January"

        # Build target path
        target_dir = self.backup_root / media_dir / year / month
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = Path(filepath).name
        target_path = target_dir / filename

        return target_path

    def backup_file(self, filepath: str, skip_duplicates: bool = True) -> bool:
        """
        Backup a single file

        Args:
            filepath: Path to file to backup
            skip_duplicates: Skip if file already backed up

        Returns:
            True if backed up successfully, False otherwise
        """
        if not os.path.exists(filepath):
            return False

        target_path = self._get_target_path(filepath)
        if not target_path:
            return False

        # Check for duplicates
        if skip_duplicates and self.deduplicator.is_duplicate(filepath):
            # File already exists, just register it
            self.deduplicator.register_file(filepath)
            self._register_backup(filepath, str(target_path), "skipped_duplicate")
            return True

        # Copy file
        try:
            shutil.copy2(filepath, target_path)
            self.deduplicator.register_file(filepath)
            self._register_backup(filepath, str(target_path), "success")
            return True
        except Exception as e:
            self._register_backup(filepath, str(target_path), f"error: {str(e)}")
            return False

    def backup_directory(
        self, source_dir: str, skip_duplicates: bool = True, show_progress: bool = True
    ) -> Dict[str, int]:
        """
        Backup all supported media files from a directory

        Args:
            source_dir: Source directory path
            skip_duplicates: Skip duplicate files
            show_progress: Show progress bar

        Returns:
            Dictionary with backup statistics
        """
        source_path = Path(source_dir)
        if not source_path.exists() or not source_path.is_dir():
            return {"error": "Invalid source directory"}

        # Collect all files
        files = [
            f
            for f in source_path.rglob("*")
            if f.is_file() and self.detector.is_supported_media(str(f))
        ]

        stats = {"total": len(files), "successful": 0, "skipped": 0, "failed": 0}

        iterator = tqdm(files, disable=not show_progress) if show_progress else files
        for file_path in iterator:
            result = self.backup_file(str(file_path), skip_duplicates)
            if result:
                stats["successful"] += 1
            else:
                stats["failed"] += 1

        return stats

    def _register_backup(self, source: str, target: str, status: str) -> None:
        """Register a backup in the registry"""
        # Get file info
        file_size = None
        file_hash = None
        media_type = self.detector.detect_media_type(source)
        
        if os.path.exists(source):
            file_size = os.path.getsize(source)
            if status != "skipped_duplicate":
                file_hash = self.deduplicator.calculate_file_hash(source)
        
        # Store in database
        self.db.add_backup_entry(
            source_path=source,
            target_path=target,
            status=status,
            media_type=media_type,
            file_size=file_size,
            file_hash=file_hash,
        )

    def get_backup_structure(self) -> Dict:
        """
        Get the current backup structure

        Returns:
            Dictionary representing the backup directory structure
        """
        structure = {}

        for media_type in self.config.get("media_types", {}).keys():
            media_dir = self.backup_root / self.detector.get_media_directory_name(
                media_type
            )
            if media_dir.exists():
                structure[media_type] = self._scan_structure(media_dir)

        return structure

    def _scan_structure(self, path: Path) -> Dict:
        """Recursively scan directory structure"""
        structure = {}

        if not path.is_dir():
            return structure

        for item in sorted(path.iterdir()):
            if item.is_dir():
                structure[item.name] = self._scan_structure(item)
            else:
                if "files" not in structure:
                    structure["files"] = []
                structure["files"].append(item.name)

        return structure

    def get_statistics(self) -> Dict:
        """Get backup service statistics"""
        dedup_stats = self.deduplicator.get_stats()
        registry_stats = self.db.get_registry_stats()

        # Count files in backup
        total_files = sum(
            1
            for _ in self.backup_root.rglob("*")
            if _.is_file() and not str(_).startswith(str(self.backup_root / ".storage_service"))
        )

        return {
            "backup_root": str(self.backup_root),
            "total_backed_up_files": total_files,
            "deduplication": dedup_stats,
            "registry_entries": registry_stats["total"],
            "registry_stats": registry_stats,
        }

    def print_structure(self) -> None:
        """Print directory structure in a readable format"""
        structure = self.get_backup_structure()
        print("\nBackup Structure:")
        print("=" * 50)

        if not structure:
            print("No backups found.")
            return

        for media_type, content in structure.items():
            print(f"\n{media_type.upper()}/")
            self._print_tree(content, prefix="  ")

    def _print_tree(self, obj: Dict, prefix: str = "") -> None:
        """Print directory tree structure"""
        keys = [k for k in obj.keys() if k != "files"]
        file_count = len(obj.get("files", []))

        for i, key in enumerate(keys):
            is_last_dir = (i == len(keys) - 1) and file_count == 0
            current_prefix = "└── " if is_last_dir else "├── "
            print(f"{prefix}{current_prefix}{key}/")

            next_prefix = prefix + ("    " if is_last_dir else "│   ")
            self._print_tree(obj[key], next_prefix)

        if file_count > 0:
            print(f"{prefix}├── ({file_count} files)")
