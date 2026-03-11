"""Tests for Storage Service"""

import unittest
import tempfile
import os
from pathlib import Path
from storage_service import StorageService, Config
from storage_service.media_detector import MediaDetector
from storage_service.deduplicator import Deduplicator


class TestConfig(unittest.TestCase):
    """Test configuration module"""

    def test_media_type_detection(self):
        """Test correct media type detection"""
        self.assertEqual(Config.get_media_type(".jpg"), "photos")
        self.assertEqual(Config.get_media_type(".mp4"), "videos")
        self.assertEqual(Config.get_media_type(".mp3"), "audio")
        self.assertEqual(Config.get_media_type(".pdf"), "documents")
        self.assertIsNone(Config.get_media_type(".unknown"))


class TestMediaDetector(unittest.TestCase):
    """Test media detector module"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = Config()
        self.detector = MediaDetector(self.config)

    def test_detect_media_type(self):
        """Test media type detection"""
        self.assertEqual(self.detector.detect_media_type("photo.jpg"), "photos")
        self.assertEqual(self.detector.detect_media_type("video.mp4"), "videos")
        self.assertEqual(self.detector.detect_media_type("song.mp3"), "audio")
        self.assertEqual(self.detector.detect_media_type("doc.pdf"), "documents")

    def test_is_supported_media(self):
        """Test supported media check"""
        self.assertTrue(self.detector.is_supported_media("photo.jpg"))
        self.assertFalse(self.detector.is_supported_media("file.txt"))

    def test_categorize_files(self):
        """Test file categorization"""
        files = ["photo.jpg", "video.mp4", "song.mp3", "doc.pdf"]
        categorized = self.detector.categorize_files(files)

        self.assertIn("photos", categorized)
        self.assertIn("videos", categorized)
        self.assertIn("audio", categorized)
        self.assertIn("documents", categorized)


class TestDeduplicator(unittest.TestCase):
    """Test deduplication module"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.deduplicator = Deduplicator(
            os.path.join(self.temp_dir, "hash_index.json")
        )

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_file_hash_calculation(self):
        """Test file hash calculation"""
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        hash1 = self.deduplicator.calculate_file_hash(test_file)
        hash2 = self.deduplicator.calculate_file_hash(test_file)

        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA256 hex digest length

    def test_register_and_check_file(self):
        """Test file registration and duplicate check"""
        test_file1 = os.path.join(self.temp_dir, "test1.txt")
        test_file2 = os.path.join(self.temp_dir, "test2.txt")

        # Create identical files
        with open(test_file1, "w") as f:
            f.write("same content")
        with open(test_file2, "w") as f:
            f.write("same content")

        # Register first file
        hash1 = self.deduplicator.register_file(test_file1)
        self.assertFalse(self.deduplicator.is_duplicate(test_file1))

        # Register second file (should be flagged as duplicate)
        hash2 = self.deduplicator.register_file(test_file2)
        self.assertEqual(hash1, hash2)
        self.assertTrue(self.deduplicator.is_duplicate(test_file2))


class TestStorageService(unittest.TestCase):
    """Test storage service module"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.backup_root = os.path.join(self.temp_dir, "backup")
        self.service = StorageService(self.backup_root)

    def tearDown(self):
        """Clean up test fixtures"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_get_target_path_with_unsupported_media(self):
        """Test _get_target_path returns None for unsupported media"""
        unsupported_file = os.path.join(self.temp_dir, "file.unknown")
        with open(unsupported_file, "w") as f:
            f.write("content")

        target_path = self.service._get_target_path(unsupported_file)
        self.assertIsNone(target_path)

    def test_get_target_path_with_supported_media(self):
        """Test _get_target_path returns correct path for supported media"""
        photo_file = os.path.join(self.temp_dir, "photo.jpg")
        with open(photo_file, "w") as f:
            f.write("fake image data")

        target_path = self.service._get_target_path(photo_file)

        # Should return a Path object
        self.assertIsInstance(target_path, Path)
        # Should contain 'Photos' directory (photos category, capitalized)
        self.assertIn("Photos", str(target_path))
        # Should contain year and month directories
        self.assertIn("2026", str(target_path))  # Current year
        # Should preserve the filename
        self.assertTrue(str(target_path).endswith("photo.jpg"))

    def test_get_target_path_directory_structure(self):
        """Test _get_target_path creates correct directory structure"""
        video_file = os.path.join(self.temp_dir, "video.mp4")
        with open(video_file, "w") as f:
            f.write("fake video data")

        target_path = self.service._get_target_path(video_file)

        # Parent directory should exist
        self.assertTrue(target_path.parent.exists())
        # Full path structure should match pattern: backup_root/media_type/year/month/filename
        path_parts = str(target_path).split(os.sep)
        self.assertIn("Videos", path_parts)
        self.assertTrue(any(year.isdigit() and len(year) == 4 for year in path_parts))

    def test_resolve_collision_no_collision(self):
        """Test _resolve_collision returns original path when no collision exists"""
        test_path = Path(self.temp_dir) / "subdir" / "photo.jpg"
        test_path.parent.mkdir(parents=True, exist_ok=True)

        # File doesn't exist yet
        resolved = self.service._resolve_collision(test_path)

        # Should return the same path
        self.assertEqual(resolved, test_path)

    def test_resolve_collision_with_collision(self):
        """Test _resolve_collision appends numeric suffix on collision"""
        test_dir = Path(self.temp_dir) / "subdir"
        test_dir.mkdir(parents=True, exist_ok=True)
        original_path = test_dir / "photo.jpg"

        # Create first file
        original_path.write_text("content1")

        # Try to resolve collision
        resolved = self.service._resolve_collision(original_path)

        # Should return path with _1 suffix
        self.assertEqual(resolved.name, "photo_1.jpg")
        self.assertEqual(resolved.parent, original_path.parent)

    def test_resolve_collision_multiple_collisions(self):
        """Test _resolve_collision handles multiple collisions with incrementing suffixes"""
        test_dir = Path(self.temp_dir) / "subdir"
        test_dir.mkdir(parents=True, exist_ok=True)
        original_path = test_dir / "photo.jpg"

        # Create multiple collision scenarios
        original_path.write_text("content1")
        (test_dir / "photo_1.jpg").write_text("content2")

        # Should return _2 suffix
        resolved = self.service._resolve_collision(original_path)
        self.assertEqual(resolved.name, "photo_2.jpg")

    def test_backup_file_different_content_same_dir(self):
        """Test backup_file with different files to same backup directory"""
        # Create two different image files that may map to same backup dir
        source_dir = Path(self.temp_dir) / "source"
        source_dir.mkdir()

        file1 = source_dir / "photo1.jpg"
        file2 = source_dir / "photo2.jpg"

        file1.write_text("content1")
        file2.write_text("content2")

        # Backup both files
        status1 = self.service.backup_file(str(file1))
        status2 = self.service.backup_file(str(file2))

        # Both should succeed
        self.assertEqual(status1, "success")
        self.assertEqual(status2, "success")

        # Check backup directory contains both files
        backup_files = list(Path(self.backup_root).rglob("*.jpg"))
        self.assertGreaterEqual(len(backup_files), 2)

    def test_preview_target_path_supported(self):
        """Test preview_target_path returns target path for supported media"""
        photo_file = os.path.join(self.temp_dir, "photo.jpg")
        with open(photo_file, "w") as f:
            f.write("fake image data")

        target_path = self.service.preview_target_path(photo_file)

        # Should return a string path
        self.assertIsNotNone(target_path)
        self.assertIsInstance(target_path, str)
        # Should contain expected components
        self.assertIn("Photos", target_path)
        self.assertIn("2026", target_path)
        self.assertIn("photo.jpg", target_path)
        # Should NOT create the file
        self.assertFalse(Path(target_path).exists())

    def test_preview_target_path_unsupported(self):
        """Test preview_target_path returns None for unsupported media"""
        unsupported_file = os.path.join(self.temp_dir, "file.unknown")
        with open(unsupported_file, "w") as f:
            f.write("content")

        target_path = self.service.preview_target_path(unsupported_file)

        # Should return None for unsupported types
        self.assertIsNone(target_path)

    def test_preview_target_path_nonexistent(self):
        """Test preview_target_path returns None for nonexistent files"""
        nonexistent_file = os.path.join(self.temp_dir, "nonexistent.jpg")

        target_path = self.service.preview_target_path(nonexistent_file)

        # Should return None for nonexistent files
        self.assertIsNone(target_path)

    def test_preview_target_path_no_actual_backup(self):
        """Test preview_target_path does not actually backup the file"""
        photo_file = os.path.join(self.temp_dir, "photo.jpg")
        with open(photo_file, "w") as f:
            f.write("test content")

        # Preview the path
        target_path = self.service.preview_target_path(photo_file)
        self.assertIsNotNone(target_path)

        # Verify the target file does not exist (no actual backup occurred)
        self.assertFalse(Path(target_path).exists())

    def test_extract_file_datetime_fallback(self):
        """Test _extract_file_datetime falls back to filesystem time"""
        photo_file = os.path.join(self.temp_dir, "photo.jpg")
        with open(photo_file, "w") as f:
            f.write("fake image data")

        # Should fallback to filesystem mtime since no EXIF data
        extracted_dt = self.service._extract_file_datetime(photo_file)

        self.assertIsNotNone(extracted_dt)
        # Should be roughly current time (within a few seconds)
        from datetime import datetime, timedelta
        now = datetime.now()
        self.assertLess(abs((now - extracted_dt).total_seconds()), 10)

    def test_extract_file_datetime_invalid_file(self):
        """Test _extract_file_datetime returns None for invalid files"""
        nonexistent = os.path.join(self.temp_dir, "nonexistent.jpg")

        extracted_dt = self.service._extract_file_datetime(nonexistent)

        # Should return None for nonexistent files
        self.assertIsNone(extracted_dt)


if __name__ == "__main__":
    unittest.main()
