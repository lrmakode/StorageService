#!/usr/bin/env python3
"""
Debug script for Storage Service
Run this to test and debug the application easily
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, '/home/avyagrah/workspace/StorageService')

def test_basic_functionality():
    """Test basic Storage Service functionality"""
    print("=" * 70)
    print("STORAGE SERVICE DEBUG TEST")
    print("=" * 70)
    
    from storage_service.core import StorageService
    from storage_service.config import Config
    from storage_service.media_detector import MediaDetector
    
    # Create temp directories
    with tempfile.TemporaryDirectory() as temp_dir:
        backup_root = os.path.join(temp_dir, "backup")
        source_dir = os.path.join(temp_dir, "source")
        os.makedirs(source_dir)
        
        print(f"\n✓ Created temp directories:")
        print(f"  - Backup root: {backup_root}")
        print(f"  - Source dir: {source_dir}")
        
        # Initialize service
        service = StorageService(backup_root)
        print(f"\n✓ ServiceInitialized")
        print(f"  - DB path: {service.db_path}")
        print(f"  - Backup root: {service.backup_root}")
        
        # Create test files
        print(f"\n▶ Creating test files...")
        test_files = {
            "photo.jpg": "fake jpeg data",
            "video.mp4": "fake video data",
            "document.pdf": "fake pdf data",
            "unknown.xyz": "unsupported format",
        }
        
        created_files = {}
        for filename, content in test_files.items():
            filepath = os.path.join(source_dir, filename)
            with open(filepath, 'w') as f:
                f.write(content)
            created_files[filename] = filepath
            print(f"  ✓ {filename}")
        
        # Test media detection
        print(f"\n▶ Testing media detection...")
        detector = MediaDetector(Config())
        for filename, filepath in created_files.items():
            media_type = detector.detect_media_type(filepath)
            is_supported = detector.is_supported_media(filepath)
            print(f"  {filename:20} → Type: {str(media_type):12} Supported: {is_supported}")
        
        # Test preview functionality
        print(f"\n▶ Testing preview_target_path()...")
        for filename, filepath in created_files.items():
            target = service.preview_target_path(filepath)
            if target:
                print(f"  {filename:20} → {target}")
            else:
                print(f"  {filename:20} → ❌ Not supported")
        
        # Test file datetime extraction
        print(f"\n▶ Testing _extract_file_datetime()...")
        for filename, filepath in created_files.items():
            if detector.is_supported_media(filepath):
                dt = service._extract_file_datetime(filepath)
                print(f"  {filename:20} → {dt}")
        
        # Test actual backup
        print(f"\n▶ Testing backup_file()...")
        for filename, filepath in created_files.items():
            if detector.is_supported_media(filepath):
                status = service.backup_file(filepath)
                print(f"  {filename:20} → {status}")
        
        # Check backup structure
        print(f"\n▶ Checking backup structure...")
        backup_files = list(Path(backup_root).rglob("*"))
        media_files = [f for f in backup_files if f.is_file() and ".storage_service" not in str(f)]
        print(f"  Total files in backup: {len(media_files)}")
        for f in media_files:
            rel_path = f.relative_to(backup_root)
            print(f"    - {rel_path}")
        
        # Test collision handling
        print(f"\n▶ Testing collision handling...")
        test_collision_path = Path(backup_root) / "Photos" / "2026" / "03_March"
        test_collision_path.mkdir(parents=True, exist_ok=True)
        
        collision_file = test_collision_path / "photo.jpg"
        collision_file.write_text("original")
        
        resolved = service._resolve_collision(collision_file)
        print(f"  Original name exists: photo.jpg")
        print(f"  Resolved to: {resolved.name}")
        print(f"  Path matches expected pattern: {resolved.name == 'photo_1.jpg'}")
        
        print(f"\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 70)


def test_with_real_file():
    """Test with a real file"""
    print("\n" + "=" * 70)
    print("TESTING WITH REAL FILE")
    print("=" * 70)
    
    from storage_service.core import StorageService
    
    filepath = input("\nEnter path to test file (or press Enter to skip): ").strip()
    
    if not filepath:
        print("Skipped.")
        return
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    backup_root = "/tmp/storage_service_debug"
    service = StorageService(backup_root)
    
    print(f"\nFile: {filepath}")
    print(f"Exists: {os.path.exists(filepath)}")
    print(f"Size: {os.path.getsize(filepath)} bytes")
    
    # Test extraction
    dt = service._extract_file_datetime(filepath)
    print(f"Extracted datetime: {dt}")
    
    # Test target path
    target = service.preview_target_path(filepath)
    print(f"Target path: {target}")
    
    # Test backup
    choice = input("\nBackup this file? (y/n): ").strip().lower()
    if choice == 'y':
        status = service.backup_file(filepath)
        print(f"Backup status: {status}")
        print(f"Backup root: {backup_root}")


if __name__ == "__main__":
    try:
        test_basic_functionality()
        
        choice = input("\n\nTest with real file? (y/n): ").strip().lower()
        if choice == 'y':
            test_with_real_file()
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
