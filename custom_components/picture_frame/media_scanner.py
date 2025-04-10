"""
Media scanner for discovering images in Home Assistant media folders.
This module scans directories and catalogs images by album.
"""

import os
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional

from .db_manager import DatabaseManager

_LOGGER = logging.getLogger(__name__)

class MediaScanner:
    """Class for scanning media directories and tracking displayed images."""
    
    def __init__(self, media_root: str, allowed_extensions: List[str], db_manager: DatabaseManager):
        """
        Initialize the media scanner.
        
        Args:
            media_root: Path to the media root directory
            allowed_extensions: List of allowed file extensions
            db_manager: Database manager instance
        """
        self.media_root = Path(media_root)
        self.allowed_extensions = allowed_extensions
        self.db_manager = db_manager
        self._current_album = None
        self._current_image = None
    
    def scan_media(self) -> Dict[str, List[str]]:
        """
        Scan all media directories and return a dictionary of albums and their images.
        
        Returns:
            Dict mapping album names to lists of image paths
        """
        albums = {}
        
        if not self.media_root.exists():
            _LOGGER.error(f"Media root does not exist: {self.media_root}")
            return albums
            
        # Each top-level directory is considered an album
        for item in self.media_root.iterdir():
            if item.is_dir():
                album_name = item.name
                images = []
                
                # Add album to database
                album_id = self.db_manager.add_album(album_name)
                
                if album_id < 0:
                    _LOGGER.error(f"Failed to add album to database: {album_name}")
                    continue
                
                # Collect all valid images in this album
                for img_path in item.glob("**/*"):
                    if img_path.is_file() and img_path.suffix.lower() in self.allowed_extensions:
                        # Store relative path for portability
                        rel_path = str(img_path.relative_to(self.media_root))
                        images.append(rel_path)
                        
                        # Add image to database
                        self.db_manager.add_image(rel_path, album_id)
                
                albums[album_name] = images
                
        total_images = sum(len(images) for images in albums.values())
        _LOGGER.info(f"Found {total_images} images in {len(albums)} albums")
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
        # Override album parameter if we have a currently set album
        if self._current_album is not None and not album:
            album = self._current_album
            
        # Get undisplayed images from database
        undisplayed_images = self.db_manager.get_undisplayed_images(album)
        
        # If all images have been displayed, reset tracking
        if not undisplayed_images:
            _LOGGER.info("All images have been displayed, resetting tracking")
            self.db_manager.clear_displayed_images()
            undisplayed_images = self.db_manager.get_all_images(album)
        
        # Return a random image from the undisplayed images
        if undisplayed_images:
            selected = random.choice(undisplayed_images)
            self.db_manager.mark_image_displayed(selected["id"])
            
            # Set as current image
            self._current_image = {
                "path": str(self.media_root / selected["path"]),
                "relative_path": selected["path"],
                "album": selected["album"]
            }
            
            return self._current_image
        
        # Return empty result if no images found
        self._current_image = {"path": "", "relative_path": "", "album": ""}
        return self._current_image
    
    def set_album(self, album_name: Optional[str] = None) -> bool:
        """
        Set the current album filter.
        
        Args:
            album_name: Album name to filter by, or None to show all albums
            
        Returns:
            True if successful, False otherwise
        """
        if album_name:
            # Verify the album exists
            albums = self.db_manager.get_all_albums()
            if album_name not in albums:
                _LOGGER.warning(f"Album not found: {album_name}")
                return False
                
        # Set the current album
        self._current_album = album_name
        _LOGGER.info(f"Set current album to: {album_name or 'All albums'}")
        return True
    
    def get_current_album(self) -> Optional[str]:
        """
        Get the current album filter.
        
        Returns:
            Current album name or None if no album filter is set
        """
        return self._current_album
    
    def get_available_albums(self) -> List[str]:
        """
        Get a list of all available albums.
        
        Returns:
            List of album names
        """
        return self.db_manager.get_all_albums()