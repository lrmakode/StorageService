# Quick Debugging Reference

## Run Debug Script (Easiest)
```bash
cd /home/avyagrah/workspace/StorageService
python3 debug_test.py
```
Interactive testing with all functionality tested automatically.

---

## VS Code Debugging Steps

1. **Set Breakpoint**: Click line number in editor (red dot appears)
2. **Select Debug Config**: `Ctrl+Shift+D` → Choose config from dropdown
3. **Start Debug**: Press `F5` or click green ▶ button
4. **Use Debug Controls**:
   - `F10` = Step over
   - `F11` = Step into
   - `Shift+F11` = Step out
   - `F5` = Continue
   - `Ctrl+Shift+F5` = Restart
   - `Shift+F5` = Stop

5. **Inspect Values**: 
   - Hover over variables
   - Use Watch panel (right side)
   - Use Debug Console at bottom

---

## Command-Line Debugging

### Test Preview Command
```bash
# Quick test
python3 -m storage_service.cli preview -b /tmp/backup_test /tmp/test_photo.jpg

# With Python debugger
python3 -m pdb -m storage_service.cli preview -b /tmp/backup_test /tmp/test_photo.jpg
```

### Run Unit Tests with Debug
```bash
# Run all tests
python3 -m unittest tests.test_storage_service -v

# Run specific test
python3 -m unittest tests.test_storage_service.TestStorageService.test_get_target_path_with_supported_media -v

# With pdb debugger
python3 -m pdb -m unittest tests.test_storage_service.TestStorageService.test_preview_target_path_supported -v
```

---

## Check Dependencies

```bash
# Verify all required packages installed
pip list | grep -E "Pillow|click|tqdm|PyYAML"

# Check if PIL/Pillow is working
python3 -c "from PIL import Image; print('✓ PIL working')"

# Check if click is working
python3 -c "import click; print('✓ Click working')"

# Check database
python3 -c "import sqlite3; print('✓ SQLite3 working')"
```

---

## Specific Issue Debugging

### "File not found" or "Unsupported media type"
```python
# Quick check
python3 -c "
from storage_service.media_detector import MediaDetector
from storage_service.config import Config

detector = MediaDetector(Config())
filepath = '/path/to/file.jpg'

print(f'File: {filepath}')
print(f'Extension: {filepath.split(\".\")[-1]}')
print(f'Type detected: {detector.detect_media_type(filepath)}')
print(f'Supported exts (photos): {Config.MEDIA_TYPES[\"photos\"][\"extensions\"]}')
"
```

### "EXIF not extracting"
```python
python3 -c "
from PIL import Image
filepath = '/path/to/photo.jpg'

try:
    img = Image.open(filepath)
    exif = img._getexif() if hasattr(img, '_getexif') else None
    print(f'EXIF data found: {exif is not None}')
    if exif:
        # Tag 36867 = DateTimeOriginal
        date = exif.get(36867, 'Not found')
        print(f'DateTimeOriginal: {date}')
except Exception as e:
    print(f'Error: {e}')
"
```

### "Collision handling not working"
```python
from pathlib import Path
from storage_service.core import StorageService
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    service = StorageService(tmpdir)
    
    test_dir = Path(tmpdir) / "test"
    test_dir.mkdir()
    
    # Create first file
    file1 = test_dir / "photo.jpg"
    file1.write_text("content1")
    
    # Test resolution
    resolved = service._resolve_collision(file1)
    print(f'Original: {file1.name}')
    print(f'Resolved: {resolved.name}')
    print(f'Correct: {resolved.name == \"photo_1.jpg\"}')
"
```

---

## Debug Logging

Add to any Python script:
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Then use
logger.debug(f"File path: {filepath}")
logger.info(f"Processing complete")
logger.warning(f"Potential issue: {issue}")
logger.error(f"Error occurred: {error}")
```

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'click'` | click not installed | `pip install click` |
| `ModuleNotFoundError: No module named 'PIL'` | Pillow not installed | `pip install Pillow` |
| `EXIF not reading` | PIL can't access image | Check file is valid JPEG |
| `Database locked` | Process holding lock | Kill the process or restart |
| `Permission denied` | Can't read source file | Check file permissions: `ls -l filepath` |
| `Invalid backup root` | Path doesn't exist | Parent directories created automatically |

---

## One-Liner Debugging

```bash
# Check if file is valid image
python3 -c "from PIL import Image; Image.open('/path/to/file.jpg'); print('✓ Valid')"

# Extract EXIF date
python3 -c "from PIL.ExifTags import TAGS; from PIL import Image; img=Image.open('/path'); exif=img._getexif(); print([(TAGS.get(k), v) for k,v in exif.items() if 'DateTime' in TAGS.get(k, '')])"

# List backup structure
python3 -c "from pathlib import Path; [print(f) for f in Path('/tmp/backup').rglob('*') if f.is_file()]"

# Check database tables
python3 -c "import sqlite3; conn=sqlite3.connect('/tmp/backup/.storage_service/storage.db'); cursor=conn.cursor(); cursor.execute(\"SELECT name FROM sqlite_master WHERE type='table'\"); print([row[0] for row in cursor.fetchall()])"
```

---

## Getting Help

1. **Run debug_test.py** to see what's working
2. **Check DEBUG_GUIDE.md** for detailed instructions
3. **Use breakpoints** in VS Code for step-by-step debugging
4. **Check log output** for error messages
5. **Add print statements** for quick debugging
