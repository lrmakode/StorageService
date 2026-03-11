"""
StorageService - A media backup and organization service.

A Python-based storage service that backs up media files and suggests
an ideal directory structure based on media type and date.
"""

__version__ = "0.1.0"
__author__ = "Storage Service Team"

from .core import StorageService
from .config import Config

__all__ = ["StorageService", "Config"]