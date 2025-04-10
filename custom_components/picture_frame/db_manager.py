"""
Database manager for the Picture Frame Controller.
Handles SQLite database operations for tracking displayed images.
"""

import os
import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import random

_LOGGER = logging.getLogger(__name__)

# Schema version to track database migrations
SCHEMA_VERSION = 1

class DatabaseManager:
    """Class for managing SQLite database operations."""
    
    def __init__(self, db_path: str):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with necessary tables if they don't exist."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Create schema version table first
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS schema_version (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                version INTEGER NOT NULL
            )
            ''')
            
            # Check current schema version
            cursor.execute("SELECT version FROM schema_version WHERE id = 1")
            result = cursor.fetchone()
            
            if not result:
                # First time initialization - set to current schema version
                cursor.execute(
                    "INSERT INTO schema_version (id, version) VALUES (1, ?)", 
                    (SCHEMA_VERSION,)
                )
                current_version = SCHEMA_VERSION
            else:
                current_version = result[0]
            
            # Create tables for current schema
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                directory_path TEXT,
                source_path TEXT,
                UNIQUE(name, source_path)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY,
                filename TEXT NOT NULL,
                album_id INTEGER,
                FOREIGN KEY (album_id) REFERENCES albums (id),
                UNIQUE(filename, album_id)
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS displayed_images (
                id INTEGER PRIMARY KEY,
                image_id INTEGER UNIQUE NOT NULL,
                displayed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images (id)
            )
            ''')
            
            conn.commit()
            _LOGGER.info(f"Database initialized with schema version {current_version}")
        except sqlite3.Error as e:
            _LOGGER.error(f"Database initialization error: {e}")
        finally:
            if conn:
                conn.close()
    
    def _get_connection(self):
        """Get a SQLite connection."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        return sqlite3.connect(self.db_path)
    
    def clear_displayed_images(self):
        """Clear the list of displayed images."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM displayed_images")
            conn.commit()
            _LOGGER.info("Cleared displayed images history")
        except sqlite3.Error as e:
            _LOGGER.error(f"Error clearing displayed images: {e}")
        finally:
            if conn:
                conn.close()
    
    def add_album(self, album_name: str, directory_path: str, source_path: str) -> int:
        """
        Add an album to the database if it doesn't exist.
        
        Args:
            album_name: Name of the album
            directory_path: Directory path for this album
            source_path: Source media path this album belongs to
            
        Returns:
            Album ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if album already exists
            cursor.execute(
                "SELECT id FROM albums WHERE name = ? AND source_path = ?", 
                (album_name, source_path)
            )
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Insert new album
            cursor.execute(
                "INSERT INTO albums (name, directory_path, source_path) VALUES (?, ?, ?)", 
                (album_name, directory_path, source_path)
            )
            conn.commit()
            
            # Get the new album ID
            album_id = cursor.lastrowid
            _LOGGER.debug(f"Added album: {album_name} (ID: {album_id})")
            return album_id
        except sqlite3.Error as e:
            _LOGGER.error(f"Error adding album {album_name}: {e}")
            return -1
        finally:
            if conn:
                conn.close()
    
    def add_image(self, filename: str, album_id: int) -> int:
        """
        Add an image to the database if it doesn't exist.
        
        Args:
            filename: Filename of the image (without directory path)
            album_id: ID of the album this image belongs to
            
        Returns:
            Image ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if image already exists
            cursor.execute(
                "SELECT id FROM images WHERE filename = ? AND album_id = ?", 
                (filename, album_id)
            )
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Insert new image
            cursor.execute(
                "INSERT INTO images (filename, album_id) VALUES (?, ?)", 
                (filename, album_id)
            )
            conn.commit()
            
            # Get the new image ID
            image_id = cursor.lastrowid
            _LOGGER.debug(f"Added image: {filename} (ID: {image_id})")
            return image_id
        except sqlite3.Error as e:
            _LOGGER.error(f"Error adding image {filename}: {e}")
            return -1
        finally:
            if conn:
                conn.close()
    
    def mark_image_displayed(self, image_id: int) -> bool:
        """
        Mark an image as having been displayed.
        
        Args:
            image_id: ID of the image that was displayed
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT OR REPLACE INTO displayed_images (image_id) VALUES (?)",
                (image_id,)
            )
            conn.commit()
            _LOGGER.debug(f"Marked image displayed: ID {image_id}")
            return True
        except sqlite3.Error as e:
            _LOGGER.error(f"Error marking image {image_id} as displayed: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_all_images(self, album_name: Optional[str] = None) -> List[Dict]:
        """
        Get all images, optionally filtered by album.
        
        Args:
            album_name: Optional album name to filter by
            
        Returns:
            List of image dictionaries with path and album
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if album_name:
                cursor.execute("""
                    SELECT i.id, i.filename, a.name, a.directory_path, a.source_path
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    WHERE a.name = ?
                """, (album_name,))
            else:
                cursor.execute("""
                    SELECT i.id, i.filename, a.name, a.directory_path, a.source_path
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                """)
            
            rows = cursor.fetchall()
            images = []
            
            for row in rows:
                # Construct the full relative path using directory_path and filename
                directory_path = row[3]
                filename = row[1]
                relative_path = os.path.join(directory_path, filename)
                
                images.append({
                    "id": row[0],
                    "path": relative_path,
                    "album": row[2],
                    "source_path": row[4]
                })
            
            return images
        except sqlite3.Error as e:
            _LOGGER.error(f"Error getting images: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_undisplayed_images(self, album_name: Optional[str] = None) -> List[Dict]:
        """
        Get images that haven't been displayed yet, optionally filtered by album.
        
        Args:
            album_name: Optional album name to filter by
            
        Returns:
            List of image dictionaries with path and album
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if album_name:
                cursor.execute("""
                    SELECT i.id, i.filename, a.name, a.directory_path, a.source_path
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    LEFT JOIN displayed_images d ON i.id = d.image_id
                    WHERE d.id IS NULL AND a.name = ?
                """, (album_name,))
            else:
                cursor.execute("""
                    SELECT i.id, i.filename, a.name, a.directory_path, a.source_path
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    LEFT JOIN displayed_images d ON i.id = d.image_id
                    WHERE d.id IS NULL
                """)
            
            rows = cursor.fetchall()
            images = []
            
            for row in rows:
                # Construct the full relative path using directory_path and filename
                directory_path = row[3]
                filename = row[1]
                relative_path = os.path.join(directory_path, filename)
                
                images.append({
                    "id": row[0],
                    "path": relative_path,
                    "album": row[2],
                    "source_path": row[4]
                })
            
            return images
        except sqlite3.Error as e:
            _LOGGER.error(f"Error getting undisplayed images: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_all_albums(self) -> List[str]:
        """
        Get a list of all album names.
        
        Returns:
            List of album names
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT name FROM albums")
            rows = cursor.fetchall()
            
            return [row[0] for row in rows]
        except sqlite3.Error as e:
            _LOGGER.error(f"Error getting albums: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_schema_version(self) -> int:
        """
        Get the current schema version.
        
        Returns:
            Current schema version number
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT version FROM schema_version WHERE id = 1")
            result = cursor.fetchone()
            
            if result:
                return result[0]
            return 0
        except sqlite3.Error as e:
            _LOGGER.error(f"Error getting schema version: {e}")
            return 0
        finally:
            if conn:
                conn.close()
                
    def update_schema_version(self, version: int) -> bool:
        """
        Update the schema version.
        
        Args:
            version: New schema version number
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE schema_version SET version = ? WHERE id = 1",
                (version,)
            )
            conn.commit()
            _LOGGER.info(f"Updated schema version to {version}")
            return True
        except sqlite3.Error as e:
            _LOGGER.error(f"Error updating schema version: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def count_undisplayed_images(self, album_name: Optional[str] = None) -> int:
        """
        Count how many images haven't been displayed yet, optionally filtered by album.
        
        Args:
            album_name: Optional album name to filter by
            
        Returns:
            Count of undisplayed images
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if album_name:
                cursor.execute("""
                    SELECT COUNT(i.id)
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    LEFT JOIN displayed_images d ON i.id = d.image_id
                    WHERE d.id IS NULL AND a.name = ?
                """, (album_name,))
            else:
                cursor.execute("""
                    SELECT COUNT(i.id)
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    LEFT JOIN displayed_images d ON i.id = d.image_id
                    WHERE d.id IS NULL
                """)
            
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            _LOGGER.error(f"Error counting undisplayed images: {e}")
            return 0
        finally:
            if conn:
                conn.close()
    
    def count_all_images(self, album_name: Optional[str] = None) -> int:
        """
        Count all images, optionally filtered by album.
        
        Args:
            album_name: Optional album name to filter by
            
        Returns:
            Count of all images
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if album_name:
                cursor.execute("""
                    SELECT COUNT(i.id)
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    WHERE a.name = ?
                """, (album_name,))
            else:
                cursor.execute("SELECT COUNT(id) FROM images")
            
            result = cursor.fetchone()
            return result[0] if result else 0
        except sqlite3.Error as e:
            _LOGGER.error(f"Error counting images: {e}")
            return 0
        finally:
            if conn:
                conn.close()
    
    def get_random_undisplayed_image(self, album_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get a single random undisplayed image directly from the database.
        
        Args:
            album_name: Optional album name to filter by
            
        Returns:
            Dictionary with image information or None if no undisplayed images
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # SQLite doesn't have a built-in RAND() function, so we use ORDER BY RANDOM() LIMIT 1
            if album_name:
                cursor.execute("""
                    SELECT i.id, i.filename, a.name, a.directory_path, a.source_path
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    LEFT JOIN displayed_images d ON i.id = d.image_id
                    WHERE d.id IS NULL AND a.name = ?
                    ORDER BY RANDOM()
                    LIMIT 1
                """, (album_name,))
            else:
                cursor.execute("""
                    SELECT i.id, i.filename, a.name, a.directory_path, a.source_path
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    LEFT JOIN displayed_images d ON i.id = d.image_id
                    WHERE d.id IS NULL
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
            
            row = cursor.fetchone()
            
            if row:
                # Construct the full relative path using directory_path and filename
                directory_path = row[3]
                filename = row[1]
                relative_path = os.path.join(directory_path, filename)
                
                return {
                    "id": row[0],
                    "path": relative_path,
                    "album": row[2],
                    "source_path": row[4]
                }
            return None
        except sqlite3.Error as e:
            _LOGGER.error(f"Error getting random undisplayed image: {e}")
            return None
        finally:
            if conn:
                conn.close()
    
    def get_random_image(self, album_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get a single random image directly from the database.
        
        Args:
            album_name: Optional album name to filter by
            
        Returns:
            Dictionary with image information or None if no images
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if album_name:
                cursor.execute("""
                    SELECT i.id, i.filename, a.name, a.directory_path, a.source_path
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    WHERE a.name = ?
                    ORDER BY RANDOM()
                    LIMIT 1
                """, (album_name,))
            else:
                cursor.execute("""
                    SELECT i.id, i.filename, a.name, a.directory_path, a.source_path
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    ORDER BY RANDOM()
                    LIMIT 1
                """)
            
            row = cursor.fetchone()
            
            if row:
                # Construct the full relative path using directory_path and filename
                directory_path = row[3]
                filename = row[1]
                relative_path = os.path.join(directory_path, filename)
                
                return {
                    "id": row[0],
                    "path": relative_path,
                    "album": row[2],
                    "source_path": row[4]
                }
            return None
        except sqlite3.Error as e:
            _LOGGER.error(f"Error getting random image: {e}")
            return None
        finally:
            if conn:
                conn.close()