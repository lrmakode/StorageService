import os
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Optional
from storage_service.config import MediaType
from storage_service.media_detector import MediaDetector
try:
    from PIL import Image
    from PIL.ExifTags import TAGS
except ImportError:
    Image = None
    TAGS = None

# Media file extensions
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".heic"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi"}


class MediaCreationDateExtractor:
    """Extracts creation date information from file paths and file metadata."""
    def __init__(self, detector: Optional[MediaDetector] = None):
        """
        Initialize media detector

        Args:
            detector: MediaDetector object
        """
        self.detector = detector or MediaDetector()

    def extract_image_datetime(self, file_path: str) -> Optional[datetime]:
        """
        Extract creation date from image EXIF metadata.
        
        Args:
            file_path: Path to the image file
            
        Returns:
            datetime object if EXIF data found, None otherwise
        """
        if Image is None:
            return None
        
        try:
            img = Image.open(file_path)
            exif_data = img.getexif()

            if not exif_data:
                return None

            readable_exif = {}

            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                readable_exif[tag] = value

            date_original = readable_exif.get("DateTimeOriginal")
            create_date = readable_exif.get("DateTime")
            digitized_date = readable_exif.get("DateTimeDigitized")

            date_value = date_original or digitized_date or create_date

            if date_value:
                return datetime.strptime(date_value, "%Y:%m:%d %H:%M:%S")

        except Exception as e:
            print(f"Image EXIF error: {e}")

        return None

    @staticmethod
    def extract_video_datetime(file_path: str) -> Optional[datetime]:
        """
        Extract creation date from video metadata using ffprobe.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            datetime object if metadata found, None otherwise
        """
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_entries",
                    "format_tags",
                    "-of",
                    "json",
                    file_path,
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                return None

            data = json.loads(result.stdout)
            tags = data.get("format", {}).get("tags", {})

            for tag in [
                "creation_time",
                "com.apple.quicktime.creationdate",
                "date",
            ]:
                if tag in tags:
                    date_str = tags[tag]

                    if "T" in date_str:
                        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))

                    try:
                        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass

        except Exception as e:
            print(f"Video metadata error: {e}")

        return None

    def extract_creation_date(self, file_path: str) -> Optional[datetime]:
        """
        Extract creation date from media file using appropriate method based on media type.
        Falls back to filesystem modification time if metadata unavailable.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            datetime object if creation date can be extracted, None otherwise
        """
        if not os.path.exists(file_path):
            return None
        
        # Detect media type
        media_type_str = self.detector.detect_media_type(file_path)
        
        # Convert string to enum if possible
        try:
            media_type = MediaType(media_type_str) if media_type_str else None
        except ValueError:
            media_type = None

        # Extract from image EXIF
        if media_type == MediaType.PHOTOS:
            date = self.extract_image_datetime(file_path)
            if date:
                return date
        
        # Extract from video metadata
        elif media_type == MediaType.VIDEOS:
            date = self.extract_video_datetime(file_path)
            if date:
                return date
        
        
        # Fallback to filesystem modification time
        try:
            modification_time = os.path.getmtime(file_path)
            return datetime.fromtimestamp(modification_time)
        except (OSError, ValueError):
            return None

    @staticmethod
    def extract_creation_date_from_filename(file_path: str) -> Optional[datetime]:
        """
        Extract creation date from the filename if it contains date information.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            datetime object if date is found in filename, None otherwise
        """
        # Get filename without extension
        filename = os.path.splitext(os.path.basename(file_path))[0]
        
        # Try common date formats in filenames
        formats = [
            "%Y%m%d",           # YYYYMMDD
            "%Y-%m-%d",         # YYYY-MM-DD
            "%Y_%m_%d",         # YYYY_MM_DD
            "%d-%m-%Y",         # DD-MM-YYYY
        ]
        
        for date_format in formats:
            try:
                return datetime.strptime(filename, date_format)
            except ValueError:
                continue
        
        return None
