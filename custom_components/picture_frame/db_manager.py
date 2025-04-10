"""
Database manager for the Picture Frame Controller.
Handles SQLite database operations for tracking displayed images.
"""

import os
import sqlite3
import logging
from typing import List, Dict, Optional

_LOGGER = logging.getLogger(__name__)

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
            
            # Create tables if they don't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS albums (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL
            )
            ''')
            
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                album_id INTEGER,
                FOREIGN KEY (album_id) REFERENCES albums (id)
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
            _LOGGER.info("Database initialized successfully")
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
    
    def add_album(self, album_name: str) -> int:
        """
        Add an album to the database if it doesn't exist.
        
        Args:
            album_name: Name of the album
            
        Returns:
            Album ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if album already exists
            cursor.execute("SELECT id FROM albums WHERE name = ?", (album_name,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Insert new album
            cursor.execute("INSERT INTO albums (name) VALUES (?)", (album_name,))
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
    
    def add_image(self, image_path: str, album_id: int) -> int:
        """
        Add an image to the database if it doesn't exist.
        
        Args:
            image_path: Path to the image (relative to media root)
            album_id: ID of the album this image belongs to
            
        Returns:
            Image ID
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if image already exists
            cursor.execute("SELECT id FROM images WHERE path = ?", (image_path,))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            
            # Insert new image
            cursor.execute("INSERT INTO images (path, album_id) VALUES (?, ?)", 
                          (image_path, album_id))
            conn.commit()
            
            # Get the new image ID
            image_id = cursor.lastrowid
            _LOGGER.debug(f"Added image: {image_path} (ID: {image_id})")
            return image_id
        except sqlite3.Error as e:
            _LOGGER.error(f"Error adding image {image_path}: {e}")
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
                    SELECT i.id, i.path, a.name
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    WHERE a.name = ?
                """, (album_name,))
            else:
                cursor.execute("""
                    SELECT i.id, i.path, a.name
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                """)
            
            rows = cursor.fetchall()
            images = []
            
            for row in rows:
                images.append({
                    "id": row[0],
                    "path": row[1],
                    "album": row[2]
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
                    SELECT i.id, i.path, a.name
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    LEFT JOIN displayed_images d ON i.id = d.image_id
                    WHERE d.id IS NULL AND a.name = ?
                """, (album_name,))
            else:
                cursor.execute("""
                    SELECT i.id, i.path, a.name
                    FROM images i
                    JOIN albums a ON i.album_id = a.id
                    LEFT JOIN displayed_images d ON i.id = d.image_id
                    WHERE d.id IS NULL
                """)
            
            rows = cursor.fetchall()
            images = []
            
            for row in rows:
                images.append({
                    "id": row[0],
                    "path": row[1],
                    "album": row[2]
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
            
            cursor.execute("SELECT name FROM albums")
            rows = cursor.fetchall()
            
            return [row[0] for row in rows]
        except sqlite3.Error as e:
            _LOGGER.error(f"Error getting albums: {e}")
            return []
        finally:
            if conn:
                conn.close()