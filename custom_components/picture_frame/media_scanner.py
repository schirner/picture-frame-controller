"""
Media scanner for discovering images in Home Assistant media folders.
This module scans directories and catalogs images by album.
"""

import os
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .db_manager import DatabaseManager

_LOGGER = logging.getLogger(__name__)

class MediaScanner:
    """Class for scanning media directories and tracking displayed images."""
    
    def __init__(self, media_paths: List[str], allowed_extensions: List[str], db_manager: DatabaseManager):
        """
        Initialize the media scanner.
        
        Args:
            media_paths: List of paths to the media root directories
            allowed_extensions: List of allowed file extensions
            db_manager: Database manager instance
        """
        self.media_paths = [Path(path) for path in media_paths]
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
        
        # Scan each configured media path
        for media_root in self.media_paths:
            if not media_root.exists():
                _LOGGER.error(f"Media path does not exist: {media_root}")
                continue
                
            # Scan for image files at any depth
            for img_path in media_root.glob("**/*"):
                if img_path.is_file() and img_path.suffix.lower() in self.allowed_extensions:
                    # Use the lowest directory as the album name
                    album_name = img_path.parent.name
                    
                    # Handle case where the image is directly in the media_root
                    if img_path.parent == media_root:
                        album_name = "Root"
                    
                    # Get directory path relative to media root
                    dir_path = str(img_path.parent.relative_to(media_root))
                    if dir_path == ".":
                        dir_path = ""
                        
                    # Get just the filename
                    filename = img_path.name
                    
                    # Source path for this media root
                    source_path = str(media_root)
                    
                    # Add album to local tracking if needed
                    if album_name not in albums:
                        albums[album_name] = []
                    
                    # Add to local tracking
                    rel_path = os.path.join(dir_path, filename) if dir_path else filename
                    albums[album_name].append({
                        "path": rel_path,
                        "source_path": source_path
                    })
                    
                    # Add album and image to database with directory path
                    album_id = self.db_manager.add_album(album_name, dir_path, source_path)
                    if album_id >= 0:
                        self.db_manager.add_image(filename, album_id)
                
        total_images = sum(len(images) for images in albums.values())
        _LOGGER.info(f"Found {total_images} images in {len(albums)} albums")
        return albums
    
    def get_next_image(self, album: Optional[str] = None) -> Dict[str, str]:
        """
        Get the next image to display that hasn't been shown yet.
        If all images have been shown, reset the tracking.
        Uses database-level queries for efficiency with large collections.
        
        Args:
            album: Optional album name to filter by
        
        Returns:
            Dict with image path and album info
        """
        # Override album parameter if we have a currently set album
        if self._current_album is not None and not album:
            album = self._current_album
            
        # Check how many undisplayed images exist
        undisplayed_count = self.db_manager.count_undisplayed_images(album)
        
        # If all images have been displayed, reset tracking
        if undisplayed_count == 0:
            _LOGGER.info("All images have been displayed, resetting tracking")
            self.db_manager.clear_displayed_images()
            undisplayed_count = self.db_manager.count_all_images(album)
            
        # Return empty result if no images found
        if undisplayed_count == 0:
            _LOGGER.warning(f"No images found for album: {album or 'All albums'}")
            self._current_image = {"path": "", "relative_path": "", "album": "", "source_path": ""}
            return self._current_image

        # Get a random undisplayed image directly from the database
        selected = None
        if self.db_manager.count_undisplayed_images(album) > 0:
            selected = self.db_manager.get_random_undisplayed_image(album)
        else:
            selected = self.db_manager.get_random_image(album)
            
        if selected:
            # Mark the image as displayed
            self.db_manager.mark_image_displayed(selected["id"])
            
            # Build full path from source path and relative path
            full_path = str(Path(selected["source_path"]) / selected["path"])
            
            # Set as current image
            self._current_image = {
                "path": full_path,
                "relative_path": selected["path"],
                "source_path": selected["source_path"], 
                "album": selected["album"]
            }
            
            return self._current_image
        
        # Return empty result if somehow no image was selected
        self._current_image = {"path": "", "relative_path": "", "album": "", "source_path": ""}
        return self._current_image
    
    def set_album(self, album_name: Optional[str] = None) -> bool:
        """
        Set the current album filter.
        
        Args:
            album_name: Album name to filter by, or None to show all albums
            
        Returns:
            True if successful, False otherwise
        """
        if album_name is None or album_name == "":
            # Reset to show all albums
            self._current_album = None
            _LOGGER.info("Set current album to: All albums")
            return True
            
        # For path-style albums, we need to use the last segment as the album name
        if "/" in album_name:
            base_name = album_name.split("/")[-1]
        else:
            base_name = album_name
            
        # Verify the album exists
        albums = self.db_manager.get_all_albums()
        if base_name not in albums:
            _LOGGER.warning(f"Album not found: {album_name}")
            return False
                
        # Set the current album
        self._current_album = base_name
        _LOGGER.info(f"Set current album to: {album_name}")
        return True
    
    def get_current_album(self) -> Optional[str]:
        """
        Get the current album filter.
        
        Returns:
            Current album name or None if no album filter is set
        """
        return self._current_album
    
    def get_current_image(self) -> Dict[str, str]:
        """
        Get the current image info.
        
        Returns:
            Current image info or empty dict if no image is set
        """
        return self._current_image or {"path": "", "relative_path": "", "album": "", "source_path": ""}
    
    def get_available_albums(self) -> List[str]:
        """
        Get a list of all available albums.
        
        Returns:
            List of album names
        """
        return self.db_manager.get_all_albums()