# Debugging Guide for Storage Service

## Quick Start

### 1. Using VS Code Debugger (Easiest)

1. **Set Breakpoints**: Click on the line number in the editor to add red dots
2. **Run Debug Configuration**: 
   - Press `Ctrl+Shift+D` → Select configuration → Click ▶ (green play button)
   - Or use `F5` shortcut

3. **Debug Controls**:
   - `F10` - Step over (execute next line)
   - `F11` - Step into (enter function)
   - `Shift+F11` - Step out (exit function)
   - `F5` - Continue execution
   - `Ctrl+Shift+B` - Stop debugging

4. **Inspect Variables**: Hover over variables to see values

---

## 2. Using Python Debugger (pdb)

Add breakpoint in code:
```python
def preview_target_path(self, filepath: str) -> Optional[str]:
    if not os.path.exists(filepath):
        return None
    
    breakpoint()  # Execution pauses here, opens interactive debugger
    target_path = self._get_target_path(filepath)
    return str(target_path) if target_path else None
```

Run with terminal:
```bash
python3 -m storage_service.cli preview -b /tmp/backup /path/to/file.jpg
```

Commands in pdb:
- `l` or `list` - Show code around current line
- `n` or `next` - Execute next line
- `s` or `step` - Step into function
- `c` or `continue` - Continue execution
- `p variable` - Print variable value
- `pp variable` - Pretty print variable
- `w` or `where` - Show stack trace
- `h` or `help` - Show help

---

## 3. Using Logging

Add to your code:
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Use in functions
def _extract_file_datetime(self, filepath: str) -> Optional[datetime]:
    logger.debug(f"Extracting datetime from: {filepath}")
    
    try:
        result = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
        logger.info(f"Successfully extracted: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to extract datetime: {e}", exc_info=True)
        return None
```

Enable debug logging:
```bash
# Run with debug level
LOGLEVEL=DEBUG python3 -m storage_service.cli preview -b /tmp/backup /path/to/file.jpg
```

---

## 4. Debugging Specific Commands

### Debug Preview Command
```bash
# With verbose output
python3 -c "
import sys
sys.path.insert(0, '/home/avyagrah/workspace/StorageService')
from storage_service.core import StorageService

service = StorageService('/tmp/test_backup')
filepath = '/path/to/file.jpg'
print(f'File exists: {service._get_target_path(filepath) is not None}')
print(f'Target path: {service._get_target_path(filepath)}')
"
```

### Debug Backups
```bash
# Test single file backup
python3 << 'EOF'
from storage_service.core import StorageService
import os

service = StorageService('/tmp/test_backup')
test_file = '/tmp/test_photo.jpg'

# Create test file
open(test_file, 'w').write('test')

# Check what happens
result = service.preview_target_path(test_file)
print(f"Preview result: {result}")

# Now actual backup
status = service.backup_file(test_file)
print(f"Backup status: {status}")
EOF
```

---

## 5. Debugging Unit Tests

Run specific test with verbose output:
```bash
python3 -m unittest tests.test_storage_service.TestStorageService.test_get_target_path_with_supported_media -v
```

Run with debugging:
```bash
python3 -m pdb -m unittest tests.test_storage_service.TestStorageService -v
```

---

## 6. Common Debugging Scenarios

### "File not found" errors
```python
filepath = '/path/to/file.jpg'
print(f"File exists: {os.path.exists(filepath)}")
print(f"Absolute path: {os.path.abspath(filepath)}")
print(f"Is file: {os.path.isfile(filepath)}")
```

### "Unsupported media type" issues
```python
from storage_service.config import Config
from storage_service.media_detector import MediaDetector

config = Config()
detector = MediaDetector(config)

filepath = '/path/to/file.jpg'
media_type = detector.detect_media_type(filepath)
print(f"Detected type: {media_type}")
print(f"Is supported: {detector.is_supported_media(filepath)}")

# Check what extensions are supported
print(f"Photo extensions: {config.MEDIA_TYPES['photos']['extensions']}")
```

### "EXIF extraction failing"
```python
from storage_service.core import StorageService

service = StorageService('/tmp/backup')
filepath = '/path/to/photo.jpg'

# Debug extraction
dt = service._extract_file_datetime(filepath)
print(f"Extracted datetime: {dt}")

# Check if PIL/Pillow is installed
try:
    from PIL import Image
    img = Image.open(filepath)
    exif = img._getexif() if hasattr(img, '_getexif') else None
    print(f"EXIF data: {exif}")
except Exception as e:
    print(f"EXIF error: {e}")
```

### "Database errors"
```python
from storage_service.database import Database

db = Database('/tmp/backup/.storage_service/storage.db')
conn = db.get_connection()
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print(f"Tables: {tables}")

# Check backup entries
cursor.execute("SELECT COUNT(*) FROM backup_registry;")
count = cursor.fetchone()
print(f"Backup entries: {count}")

conn.close()
```

---

## 7. Using VSCode Watch Expressions

In Debug mode, add watch expressions:
- `len(self.backup_root)` - Check if path is valid
- `self.deduplicator` - Check deduplicator state
- `target_path.exists()` - Check if collision target exists
- `file_datetime` - Check extracted datetime

---

## 8. Debug Mode Checklist

- ✓ Check virtual environment is activated
- ✓ Verify test files exist at expected paths
- ✓ Check file permissions (readable files)
- ✓ Verify PIL/Pillow installed: `pip list | grep Pillow`
- ✓ Verify click installed: `pip list | grep click`
- ✓ Check database not locked by running process

---

## Pro Tips

1. **Add print debugging**:
   ```python
   print(f"DEBUG: filepath={filepath}, exists={os.path.exists(filepath)}")
   ```

2. **Use f-string for quick inspection**:
   ```python
   print(f"{filepath=}")  # Shows: filepath=/path/to/file.jpg
   ```

3. **Dump objects as JSON**:
   ```python
   import json
   from pathlib import Path
   print(json.dumps(stats, indent=2, default=str))
   ```

4. **Use repr() for clarity**:
   ```python
   print(f"Path object: {repr(target_path)}")
   print(f"Type: {type(target_path)}")
   ```
