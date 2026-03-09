"""Deduplication module for identifying duplicate files"""

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from .database import Database


class Deduplicator:
    """Handles file deduplication using content hashing with SQLite backend"""

    def __init__(self, db_path: str):
        """
        Initialize deduplicator with SQLite database

        Args:
            db_path: Path to SQLite database file
        """
        self.db = Database(db_path)

    @staticmethod
    def calculate_file_hash(filepath: str, algorithm: str = "sha256") -> str:
        """
        Calculate file hash using specified algorithm

        Args:
            filepath: Path to the file
            algorithm: Hash algorithm to use (default: sha256)

        Returns:
            Hex digest of the file hash
        """
        hasher = hashlib.new(algorithm)
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def is_duplicate(self, filepath: str) -> bool:
        """
        Check if file is a duplicate of an already backed up file

        Args:
            filepath: Path to the file to check

        Returns:
            True if file is a duplicate, False otherwise
        """
        if not os.path.exists(filepath):
            return False

        file_hash = self.calculate_file_hash(filepath)
        return self.db.hash_exists(file_hash)

    def get_duplicate_files(self, filepath: str) -> List[str]:
        """
        Get list of files that are duplicates of the given file

        Args:
            filepath: Path to the file

        Returns:
            List of paths to files with same hash
        """
        if not os.path.exists(filepath):
            return []

        file_hash = self.calculate_file_hash(filepath)
        return self.db.get_files_by_hash(file_hash)

    def register_file(self, filepath: str) -> str:
        """
        Register a file in the deduplication index

        Args:
            filepath: Path to the file

        Returns:
            The file hash
        """
        file_hash = self.calculate_file_hash(filepath)
        hash_id = self.db.add_hash(file_hash)
        self.db.add_file_to_hash(hash_id, filepath)
        return file_hash

    def get_duplicate_groups(self) -> Dict[str, List[str]]:
        """
        Get all groups of duplicate files

        Returns:
            Dictionary mapping hash to list of file paths
        """
        all_hashes = self.db.get_all_hashes()
        # Filter out single files (not duplicates)
        return {
            file_hash: files
            for file_hash, files in all_hashes.items()
            if len(files) > 1
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get deduplication statistics"""
        all_hashes = self.db.get_all_hashes()
        total_files = sum(len(files) for files in all_hashes.values())
        duplicate_groups = sum(1 for files in all_hashes.values() if len(files) > 1)
        total_duplicates = sum(max(0, len(files) - 1) for files in all_hashes.values())

        return {
            "total_unique_hashes": len(all_hashes),
            "total_files_tracked": total_files,
            "duplicate_groups": duplicate_groups,
            "total_duplicate_files": total_duplicates,
        }
