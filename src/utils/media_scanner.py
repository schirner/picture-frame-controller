"""
Media scanner for discovering images in Home Assistant media folders.
This module scans directories and catalogs images by album.
"""

import os
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional

from config import settings
from src.utils.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class MediaScanner:
    """Class for scanning media directories and tracking displayed images."""
    
    def __init__(self):
        """Initialize the media scanner."""
        self.media_root = Path(settings.MEDIA_ROOT)
        # Replace JSON file with SQLite
        self.db_manager = DatabaseManager(settings.DB_FILE)
        self._albums_cache = {}
    
    def scan_media(self) -> Dict[str, List[str]]:
        """
        Scan all media directories and return a dictionary of albums and their images.
        
        Returns:
            Dict mapping album names to lists of image paths
        """
        albums = {}
        
        # Reset cache
        self._albums_cache = {}
        
        if not self.media_root.exists():
            logger.error(f"Media root does not exist: {self.media_root}")
            return albums
            
        # Each top-level directory is considered an album
        for item in self.media_root.iterdir():
            if item.is_dir():
                album_name = item.name
                images = []
                
                # Add album to database
                album_id = self.db_manager.add_album(album_name)
                
                if album_id < 0:
                    logger.error(f"Failed to add album to database: {album_name}")
                    continue
                
                # Collect all valid images in this album
                for img_path in item.glob("**/*"):
                    if img_path.is_file() and img_path.suffix.lower() in settings.ALLOWED_EXTENSIONS:
                        # Store relative path for portability
                        rel_path = str(img_path.relative_to(self.media_root))
                        images.append(rel_path)
                        
                        # Add image to database
                        self.db_manager.add_image(rel_path, album_id)
                
                albums[album_name] = images
                
        self._albums_cache = albums
        total_images = sum(len(images) for images in albums.values())
        logger.info(f"Found {total_images} images in {len(albums)} albums")
        return albums
    
    def get_next_image(self, album: Optional[str] = None) -> Dict[str, str]:
        """
        Get the next image to display that hasn't been shown yet.
        If all images have been shown, reset the tracking.
        
        Args:
            album: Optional album name to filter by
        
        Returns:
            Dict with image path and album info
        """
        # Get undisplayed images from database
        undisplayed_images = self.db_manager.get_undisplayed_images(album)
        
        # If all images have been displayed, reset tracking
        if not undisplayed_images:
            logger.info("All images have been displayed, resetting tracking")
            self.db_manager.clear_displayed_images()
            undisplayed_images = self.db_manager.get_all_images(album)
        
        # Return a random image from the undisplayed images
        if undisplayed_images:
            selected = random.choice(undisplayed_images)
            self.db_manager.mark_image_displayed(selected["id"])
            
            # Return full path and metadata
            full_path = str(self.media_root / selected["path"])
            return {
                "path": full_path,
                "relative_path": selected["path"],
                "album": selected["album"]
            }
        
        return {"path": "", "relative_path": "", "album": ""}
    
    def get_albums(self) -> List[str]:
        """
        Get a list of all available albums.
        
        Returns:
            List of album names
        """
        return self.db_manager.get_all_albums()