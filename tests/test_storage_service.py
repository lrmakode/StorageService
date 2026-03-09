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


if __name__ == "__main__":
    unittest.main()
