"""
Database manager for the Picture Frame Controller.
Handles SQLite database operations for tracking displayed images.
"""

import os
import sqlite3
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

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
            
            # Check if we need to perform migration
            need_migration = False
            try:
                cursor.execute("SELECT directory_path FROM albums LIMIT 1")
            except sqlite3.OperationalError:
                need_migration = True
            
            # Create tables if they don't exist or need update
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
            
            # If migration is needed, perform it
            if need_migration:
                self._migrate_db(cursor)
            
            conn.commit()
            _LOGGER.info("Database initialized successfully")
        except sqlite3.Error as e:
            _LOGGER.error(f"Database initialization error: {e}")
        finally:
            if conn:
                conn.close()
    
    def _migrate_db(self, cursor):
        """Migrate from old schema to new schema."""
        try:
            # Check if old tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='images'")
            if cursor.fetchone():
                _LOGGER.info("Migrating database structure...")
                
                # Create temporary tables with new schema
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS new_albums (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    directory_path TEXT,
                    source_path TEXT,
                    UNIQUE(name, source_path)
                )
                ''')
                
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS new_images (
                    id INTEGER PRIMARY KEY,
                    filename TEXT NOT NULL,
                    album_id INTEGER,
                    FOREIGN KEY (album_id) REFERENCES new_albums (id),
                    UNIQUE(filename, album_id)
                )
                ''')
                
                # Copy data from old tables to new tables
                try:
                    # Get all albums with their images
                    cursor.execute('''
                    SELECT a.id, a.name, i.path, i.source_path 
                    FROM albums a 
                    JOIN images i ON i.album_id = a.id
                    ''')
                    
                    albums_data = {}
                    for row in cursor.fetchall():
                        old_album_id, album_name, image_path, source_path = row
                        # Extract directory path from image path
                        path_obj = Path(image_path)
                        # Use the parent directory of the image as the album directory
                        directory_path = str(path_obj.parent)
                        # Get just the filename
                        filename = path_obj.name
                        
                        album_key = (album_name, source_path)
                        if album_key not in albums_data:
                            albums_data[album_key] = {
                                'album_name': album_name, 
                                'directory_path': directory_path,
                                'source_path': source_path,
                                'images': []
                            }
                        albums_data[album_key]['images'].append(filename)
                    
                    # Insert albums into new table
                    for album_data in albums_data.values():
                        cursor.execute(
                            "INSERT INTO new_albums (name, directory_path, source_path) VALUES (?, ?, ?)",
                            (album_data['album_name'], album_data['directory_path'], album_data['source_path'])
                        )
                        new_album_id = cursor.lastrowid
                        
                        # Insert images into new table
                        for filename in album_data['images']:
                            cursor.execute(
                                "INSERT INTO new_images (filename, album_id) VALUES (?, ?)",
                                (filename, new_album_id)
                            )
                    
                    # Copy displayed_images data
                    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS new_displayed_images (
                        id INTEGER PRIMARY KEY,
                        image_id INTEGER UNIQUE NOT NULL,
                        displayed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (image_id) REFERENCES new_images (id)
                    )
                    ''')
                    
                    cursor.execute('''
                    INSERT INTO new_displayed_images (image_id, displayed_at)
                    SELECT ni.id, di.displayed_at
                    FROM displayed_images di
                    JOIN images oi ON di.image_id = oi.id
                    JOIN new_albums na ON oi.album_id = na.id
                    JOIN new_images ni ON ni.album_id = na.id AND ni.filename = (SELECT substr(oi.path, instr(oi.path, '/')+1))
                    ''')
                    
                    # Replace old tables with new ones
                    cursor.execute("DROP TABLE displayed_images")
                    cursor.execute("DROP TABLE images")
                    cursor.execute("DROP TABLE albums")
                    
                    cursor.execute("ALTER TABLE new_albums RENAME TO albums")
                    cursor.execute("ALTER TABLE new_images RENAME TO images")
                    cursor.execute("ALTER TABLE new_displayed_images RENAME TO displayed_images")
                    
                    _LOGGER.info("Database migration completed successfully")
                    
                except sqlite3.Error as e:
                    _LOGGER.error(f"Error during migration: {e}")
                
        except sqlite3.Error as e:
            _LOGGER.error(f"Migration check error: {e}")
    
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