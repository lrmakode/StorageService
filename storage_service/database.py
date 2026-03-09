"""Database management module using SQLite"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class Database:
    """Manages SQLite database for storage service"""

    def __init__(self, db_path: str):
        """
        Initialize database

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_db()

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self) -> None:
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Hash index table for deduplication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_hashes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_hash TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # File paths associated with hash
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hash_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                FOREIGN KEY(hash_id) REFERENCES file_hashes(id),
                UNIQUE(hash_id, file_path)
            )
        """)

        # Backup registry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backup_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_path TEXT NOT NULL,
                target_path TEXT NOT NULL,
                status TEXT NOT NULL,
                media_type TEXT,
                file_size INTEGER,
                file_hash TEXT,
                backed_up_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Backup metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS backup_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for faster searches
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_hash ON file_hashes(file_hash)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_source_path ON backup_registry(source_path)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_media_type ON backup_registry(media_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_status ON backup_registry(status)
        """)

        conn.commit()
        conn.close()

    # Hash Index Operations
    def hash_exists(self, file_hash: str) -> bool:
        """Check if hash exists in database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM file_hashes WHERE file_hash = ?", (file_hash,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def add_hash(self, file_hash: str) -> int:
        """Add a new hash and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO file_hashes (file_hash) VALUES (?)", (file_hash,))
            conn.commit()
            hash_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute("SELECT id FROM file_hashes WHERE file_hash = ?", (file_hash,))
            hash_id = cursor.fetchone()[0]
        conn.close()
        return hash_id

    def add_file_to_hash(self, hash_id: int, file_path: str) -> None:
        """Add a file path to a hash"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO hash_files (hash_id, file_path) VALUES (?, ?)",
                (hash_id, file_path),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # File already associated with this hash
        conn.close()

    def get_files_by_hash(self, file_hash: str) -> List[str]:
        """Get all file paths with a specific hash"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT file_path FROM hash_files 
               WHERE hash_id = (SELECT id FROM file_hashes WHERE file_hash = ?)""",
            (file_hash,),
        )
        results = cursor.fetchall()
        conn.close()
        return [row[0] for row in results]

    def get_all_hashes(self) -> Dict[str, List[str]]:
        """Get all hashes and their associated files"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT fh.file_hash, hf.file_path FROM file_hashes fh
               LEFT JOIN hash_files hf ON fh.id = hf.hash_id"""
        )
        results = cursor.fetchall()
        conn.close()

        hash_dict: Dict[str, List[str]] = {}
        for row in results:
            file_hash, file_path = row
            if file_hash not in hash_dict:
                hash_dict[file_hash] = []
            if file_path:
                hash_dict[file_hash].append(file_path)
        return hash_dict

    # Backup Registry Operations
    def add_backup_entry(
        self,
        source_path: str,
        target_path: str,
        status: str,
        media_type: Optional[str] = None,
        file_size: Optional[int] = None,
        file_hash: Optional[str] = None,
    ) -> None:
        """Add entry to backup registry"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO backup_registry 
               (source_path, target_path, status, media_type, file_size, file_hash)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (source_path, target_path, status, media_type, file_size, file_hash),
        )
        conn.commit()
        conn.close()

    def get_backup_entries(self, status: Optional[str] = None) -> List[Dict]:
        """Get backup registry entries"""
        conn = self.get_connection()
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM backup_registry WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT * FROM backup_registry")
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]

    def search_backups(self, **kwargs) -> List[Dict]:
        """Search backups with multiple criteria"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM backup_registry WHERE 1=1"
        params = []

        if "source_path" in kwargs:
            query += " AND source_path LIKE ?"
            params.append(f"%{kwargs['source_path']}%")
        if "media_type" in kwargs:
            query += " AND media_type = ?"
            params.append(kwargs["media_type"])
        if "status" in kwargs:
            query += " AND status = ?"
            params.append(kwargs["status"])
        if "file_hash" in kwargs:
            query += " AND file_hash = ?"
            params.append(kwargs["file_hash"])

        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        return [dict(row) for row in results]

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics from backup registry"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM backup_registry")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) as count FROM backup_registry WHERE status = ?", ("success",))
        successful = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) as count FROM backup_registry WHERE status = ?",
            ("skipped_duplicate",),
        )
        skipped = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) as count FROM backup_registry WHERE status LIKE ?", ("error%",))
        failed = cursor.fetchone()[0]

        cursor.execute(
            """SELECT media_type, COUNT(*) as count FROM backup_registry 
               WHERE status = ? GROUP BY media_type""",
            ("success",),
        )
        by_type = {row[0]: row[1] for row in cursor.fetchall()}

        conn.close()

        return {
            "total": total,
            "successful": successful,
            "skipped": skipped,
            "failed": failed,
            "by_media_type": by_type,
        }

    # Metadata Operations
    def set_metadata(self, key: str, value: Any) -> None:
        """Set metadata value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        value_str = json.dumps(value) if not isinstance(value, str) else value
        cursor.execute(
            """INSERT OR REPLACE INTO backup_metadata (key, value) VALUES (?, ?)""",
            (key, value_str),
        )
        conn.commit()
        conn.close()

    def get_metadata(self, key: str) -> Optional[Any]:
        """Get metadata value"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM backup_metadata WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()

        if result:
            try:
                return json.loads(result[0])
            except json.JSONDecodeError:
                return result[0]
        return None

    def get_all_metadata(self) -> Dict[str, Any]:
        """Get all metadata"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM backup_metadata")
        results = cursor.fetchall()
        conn.close()

        metadata = {}
        for key, value in results:
            try:
                metadata[key] = json.loads(value)
            except json.JSONDecodeError:
                metadata[key] = value
        return metadata

    # Duplicate Detection Operations
    def find_duplicate_hashes(self) -> Dict[str, List[str]]:
        """Find all hashes that have multiple files (duplicates)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT fh.file_hash, GROUP_CONCAT(hf.file_path, '|') as file_paths
            FROM file_hashes fh
            JOIN hash_files hf ON fh.id = hf.hash_id
            GROUP BY fh.file_hash
            HAVING COUNT(*) > 1
        """)
        results = cursor.fetchall()
        conn.close()

        duplicates = {}
        for row in results:
            file_hash, file_paths = row
            duplicates[file_hash] = file_paths.split('|') if file_paths else []
        return duplicates

    def find_duplicate_files_in_registry(self) -> Dict[str, List[Dict]]:
        """Find all files in registry that appear multiple times"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT file_hash, GROUP_CONCAT(id) as ids, COUNT(*) as count
            FROM backup_registry
            WHERE file_hash IS NOT NULL
            GROUP BY file_hash
            HAVING COUNT(*) > 1
        """)
        results = cursor.fetchall()
        conn.close()

        duplicates = {}
        for row in results:
            file_hash, ids, count = row
            id_list = [int(x) for x in ids.split(',')]
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, source_path, target_path, media_type, backed_up_at
                FROM backup_registry
                WHERE id IN ({})
            """.format(','.join('?' * len(id_list))), id_list)
            files = [dict(r) for r in cursor.fetchall()]
            conn.close()
            duplicates[file_hash] = files

        return duplicates

    def get_duplicate_stats(self) -> Dict[str, Any]:
        """Get statistics about duplicates"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Total unique hashes
        cursor.execute("SELECT COUNT(*) FROM file_hashes")
        total_hashes = cursor.fetchone()[0]

        # Hashes with duplicates
        cursor.execute("""
            SELECT COUNT(*) FROM file_hashes
            WHERE id IN (
                SELECT hash_id FROM hash_files
                GROUP BY hash_id HAVING COUNT(*) > 1
            )
        """)
        duplicate_hashes = cursor.fetchone()[0]

        # Total duplicate files
        cursor.execute("""
            SELECT COUNT(*) - COUNT(DISTINCT hash_id) FROM hash_files
        """)
        total_duplicate_files = cursor.fetchone()[0]

        # Duplicate groups
        cursor.execute("""
            SELECT COUNT(*) FROM (
                SELECT hash_id FROM hash_files
                GROUP BY hash_id HAVING COUNT(*) > 1
            )
        """)
        duplicate_groups = cursor.fetchone()[0]

        conn.close()

        return {
            "total_hashes": total_hashes,
            "duplicate_hashes": duplicate_hashes,
            "total_duplicate_files": total_duplicate_files,
            "duplicate_groups": duplicate_groups,
        }
