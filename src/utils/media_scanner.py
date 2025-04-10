"""
Media scanner for discovering images in Home Assistant media folders.
This module scans directories and catalogs images by album.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional

from config import settings

logger = logging.getLogger(__name__)

class MediaScanner:
    """Class for scanning media directories and tracking displayed images."""
    
    def __init__(self):
        """Initialize the media scanner."""
        self.media_root = Path(settings.MEDIA_ROOT)
        self.db_file = Path(settings.DB_FILE)
        self.displayed_images = set()
        self._albums_cache = {}
        self._all_images = []
        self.load_state()
    
    def scan_media(self) -> Dict[str, List[str]]:
        """
        Scan all media directories and return a dictionary of albums and their images.
        
        Returns:
            Dict mapping album names to lists of image paths
        """
        albums = {}
        
        # Reset cache
        self._all_images = []
        self._albums_cache = {}
        
        if not self.media_root.exists():
            logger.error(f"Media root does not exist: {self.media_root}")
            return albums
            
        # Each top-level directory is considered an album
        for item in self.media_root.iterdir():
            if item.is_dir():
                album_name = item.name
                images = []
                
                # Collect all valid images in this album
                for img_path in item.glob("**/*"):
                    if img_path.is_file() and img_path.suffix.lower() in settings.ALLOWED_EXTENSIONS:
                        # Store relative path for portability
                        rel_path = str(img_path.relative_to(self.media_root))
                        images.append(rel_path)
                        self._all_images.append({
                            "path": rel_path,
                            "album": album_name
                        })
                
                albums[album_name] = images
                
        self._albums_cache = albums
        logger.info(f"Found {len(self._all_images)} images in {len(albums)} albums")
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
        # Scan media if we haven't done so yet
        if not self._all_images:
            self.scan_media()
            
        filtered_images = self._all_images
        
        # Filter by album if requested
        if album and settings.ENABLE_ALBUM_FILTERING:
            filtered_images = [img for img in self._all_images if img["album"] == album]
            if not filtered_images:
                logger.warning(f"No images found in album: {album}")
                # Fall back to all images
                filtered_images = self._all_images
        
        # Find images that haven't been displayed yet
        unseen_images = [img for img in filtered_images 
                        if img["path"] not in self.displayed_images]
        
        # If all images have been seen, reset tracking
        if not unseen_images:
            logger.info("All images have been displayed, resetting tracking")
            self.displayed_images.clear()
            unseen_images = filtered_images
        
        # Return the first unseen image
        if unseen_images:
            selected = unseen_images[0]
            self.displayed_images.add(selected["path"])
            self.save_state()
            
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
        if not self._albums_cache:
            self.scan_media()
        
        return list(self._albums_cache.keys())
    
    def load_state(self):
        """Load the state of displayed images from the database file."""
        if self.db_file.exists():
            try:
                with open(self.db_file, 'r') as f:
                    data = json.load(f)
                    self.displayed_images = set(data.get('displayed_images', []))
                    logger.info(f"Loaded {len(self.displayed_images)} displayed images from state")
            except Exception as e:
                logger.error(f"Error loading state: {e}")
                self.displayed_images = set()
    
    def save_state(self):
        """Save the current state of displayed images to the database file."""
        try:
            # Ensure directory exists
            self.db_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.db_file, 'w') as f:
                json.dump({
                    'displayed_images': list(self.displayed_images)
                }, f)
                
            logger.info(f"Saved {len(self.displayed_images)} displayed images to state")
        except Exception as e:
            logger.error(f"Error saving state: {e}")