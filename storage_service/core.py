"""Core storage service module"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from click import echo

from .src.MediaCreationDateExtractor import MediaCreationDateExtractor

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
        self.date_extractor = MediaCreationDateExtractor(self.detector)
        
        # Initialize SQLite database
        self.db_path = str(self.backup_root / ".storage_service" / "storage.db")
        self.db = Database(self.db_path)
        self.deduplicator = Deduplicator(self.db_path)

    def _extract_file_datetime(self, filepath: str) -> Optional[datetime]:
        """
        Extract datetime from file metadata with fallback to filesystem modification time.
        
        Args:
            filepath: Path to the file
            
        Returns:
            datetime object or None if file doesn't exist
        """
        if not os.path.exists(filepath):
            return None
        
        # Try to extract from metadata
        file_datetime = self.date_extractor.extract_creation_date(filepath)
        
        if file_datetime:
            return file_datetime
        
        # Fallback to filesystem modification time
        try:
            mtime = os.path.getmtime(filepath)
            return datetime.fromtimestamp(mtime)
        except (OSError, ValueError):
            return None

    def _get_target_path(self, filepath: str, file_hash: Optional[str] = None) -> Optional[Path]:
        """
        Determine target backup path for a file

        Args:
            filepath: Source file path
            file_hash: Pre-calculated file hash (optional, will calculate if not provided)

        Returns:
            Target backup path or None if media type not supported
        """
        media_type = self.detector.detect_media_type(filepath)
        if not media_type:
            return None

        # Extract datetime from file metadata (EXIF, video metadata, etc.)
        # Falls back to filesystem time if metadata unavailable
        file_datetime = self._extract_file_datetime(filepath)
        if not file_datetime:
            return None

        # Use provided hash or calculate it
        if file_hash is None:
            file_hash = self.deduplicator.calculate_file_hash(filepath)
        hash_bucket = file_hash[:2].lower()  # Use first 2 chars of hash as bucket

        # Get directory names from config
        media_dir = self.detector.get_media_directory_name(media_type)
        year = file_datetime.strftime("%Y")
        month = file_datetime.strftime("%m")  # e.g., "09"

        # Build target path: media_dir/YYYY/MM/hash_bucket/filename
        target_dir = self.backup_root / media_dir / year / month / hash_bucket
        target_dir.mkdir(parents=True, exist_ok=True)

        filename = Path(filepath).name
        target_path = target_dir / filename

        # Handle collision by appending numeric suffix
        target_path = self._resolve_collision(target_path)

        return target_path

    def _resolve_collision(self, target_path: Path) -> Path:
        """
        Resolve filename collisions by appending numeric suffix (_1, _2, etc.)

        Args:
            target_path: Proposed target path

        Returns:
            Unique target path with numeric suffix if collision exists
        """
        if not target_path.exists():
            return target_path

        # File exists, append numeric suffix
        counter = 1
        file_stem = target_path.stem
        file_ext = target_path.suffix
        
        while True:
            unique_filename = f"{file_stem}_{counter}{file_ext}"
            unique_target_path = target_path.parent / unique_filename
            
            if not unique_target_path.exists():
                return unique_target_path
            
            counter += 1

    def preview_target_path(self, filepath: str) -> Optional[str]:
        """
        Preview where a file would be backed up without actually backing it up

        Args:
            filepath: Path to the file to preview

        Returns:
            Target backup path as string, or None if file type not supported
        """
        if not os.path.exists(filepath):
            return None

        # Use provided hash or calculate it
        file_hash = self.deduplicator.calculate_file_hash(filepath)
        print(f"Previewing target path for: {filepath} (hash: {file_hash})")
        target_path = self._get_target_path(filepath, file_hash)
        return str(target_path) if target_path else None

    def backup_file(self, filepath: str, skip_duplicates: bool = True) -> str:
        """
        Backup a single file

        Args:
            filepath: Path to file to backup
            skip_duplicates: Skip if file already backed up

        Returns:
            Status: "success", "skipped_duplicate", or "failed"
        """
        if not os.path.exists(filepath):
            return "failed"

        # Calculate file hash once and reuse throughout
        file_hash = self.deduplicator.calculate_file_hash(filepath)
        
        target_path = self._get_target_path(filepath, file_hash)
        if not target_path:
            return "failed"

        # Check for duplicates
        if skip_duplicates and self.deduplicator.is_duplicate(filepath, file_hash):
            # File already exists, just register it
            self.deduplicator.register_file(filepath, file_hash)
            self._register_backup(filepath, str(target_path), "skipped_duplicate", file_hash)
            return "skipped_duplicate"

        # Copy file
        try:
            shutil.copy2(filepath, target_path)
            self.deduplicator.register_file(filepath, file_hash)
            self._register_backup(filepath, str(target_path), "success", file_hash)
            return "success"
        except Exception as e:
            self._register_backup(filepath, str(target_path), f"error: {str(e)}", file_hash)
            return "failed"

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

        # Count files in backup storage before backup
        backup_files_before = sum(
            1
            for _ in self.backup_root.rglob("*")
            if _.is_file() and not str(_).startswith(str(self.backup_root / ".storage_service"))
        )

        # Collect all files
        files = [
            f
            for f in source_path.rglob("*")
            if f.is_file() and self.detector.is_supported_media(str(f))
        ]

        stats: Dict = {
            "total_source_files": len(files),
            "successful": 0,
            "skipped": 0,
            "failed": 0,
            "total_size": 0,
            "by_media_type": {},
            "backup_files_before": backup_files_before,
        }

        iterator = tqdm(files, disable=not show_progress) if show_progress else files
        for file_path in iterator:
            status = self.backup_file(str(file_path), skip_duplicates)
            if status == "success":
                stats["successful"] += 1
                media_type = self.detector.detect_media_type(str(file_path)) or "unknown"
                file_size = file_path.stat().st_size
                stats["total_size"] += file_size
                entry = stats["by_media_type"].setdefault(media_type, {"count": 0, "size": 0})
                entry["count"] += 1
                entry["size"] += file_size
            elif status == "skipped_duplicate":
                stats["skipped"] += 1
            else:  # "failed"
                stats["failed"] += 1

        # Count files in backup storage after backup
        backup_files_after = sum(
            1
            for _ in self.backup_root.rglob("*")
            if _.is_file() and not str(_).startswith(str(self.backup_root / ".storage_service"))
        )
        stats["backup_files_after"] = backup_files_after

        return stats

    def _register_backup(self, source: str, target: str, status: str, file_hash: Optional[str] = None) -> None:
        """Register a backup in the registry"""
        # Get file info
        file_size = None
        media_type = self.detector.detect_media_type(source)
        
        if os.path.exists(source):
            file_size = os.path.getsize(source)
        
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
            "successful": registry_stats["successful"],
            "skipped": registry_stats["skipped"],
            "failed": registry_stats["failed"],
            "total_size": registry_stats["total_size"],
            "by_media_type": registry_stats["by_media_type"],
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

    def delete_file(self, target_path: str) -> str:
        """
        Delete a backed-up file by its backup (target) path.

        Removes the physical file and all matching entries from the registry.
        If no other source files reference the same hash, the hash record is
        also cleaned up.

        Args:
            target_path: Absolute path to the backed-up file to delete.

        Returns:
            Status: "success", "not_found", or "failed"
        """
        target = Path(target_path)

        # Verify the file is inside backup_root for safety
        try:
            target.resolve().relative_to(self.backup_root.resolve())
        except ValueError:
            return "failed"

        if not target.exists():
            # Still remove stale DB entries if any
            self.db.delete_backup_entry_by_target(target_path)
            return "not_found"

        try:
            target.unlink()
        except OSError:
            return "failed"

        # Remove registry entries
        self.db.delete_backup_entry_by_target(target_path)

        # Clean up the hash index
        self.db.cleanup_orphan_hashes()

        # Remove empty parent directories up to backup_root
        try:
            parent = target.parent
            while parent != self.backup_root and parent != parent.parent:
                if not any(parent.iterdir()):
                    parent.rmdir()
                    parent = parent.parent
                else:
                    break
        except OSError:
            pass

        return "success"

    def delete_by_source(self, source_path: str) -> Dict:
        """
        Delete all backed-up files that were sourced from the given path.

        Args:
            source_path: Original source file path used during backup.

        Returns:
            Dictionary with counts: {"deleted": int, "not_found": int, "failed": int}
        """
        entries = self.db.search_backups(source_path=source_path)

        # Filter to exact source path matches
        entries = [e for e in entries if e["source_path"] == source_path]

        stats: Dict[str, int] = {"deleted": 0, "not_found": 0, "failed": 0}

        if not entries:
            return stats

        seen_targets = set()
        for entry in entries:
            target = entry["target_path"]
            if target in seen_targets:
                continue
            seen_targets.add(target)

            status = self.delete_file(target)
            if status == "success":
                stats["deleted"] += 1
            elif status == "not_found":
                # Remove stale DB record and still count as handled
                self.db.delete_backup_entry_by_source(source_path)
                stats["not_found"] += 1
            else:
                stats["failed"] += 1

        # Remove any remaining source-path entries from the registry
        self.db.delete_backup_entry_by_source(source_path)
        self.db.remove_file_from_hash(source_path)
        self.db.cleanup_orphan_hashes()

        return stats
