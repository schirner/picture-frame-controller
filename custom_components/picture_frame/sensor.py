"""
Sensor platform for Picture Frame component.
Provides sensors for image display, current album, and available albums.
"""

import logging
import os
from typing import Optional, Any, Dict, List

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.util.dt as dt_util
from datetime import timedelta

from .const import (
    DOMAIN,
    CONF_MEDIA_PATHS,
    CONF_ALLOWED_EXTENSIONS,
    CONF_DB_PATH,
    ATTR_ALBUM,
    ATTR_CURRENT_ALBUM,
    ATTR_AVAILABLE_ALBUMS,
    ATTR_PATH,
    ATTR_RELATIVE_PATH,
    ATTR_SOURCE_PATH,
    SCAN_INTERVAL,
    SENSOR_NEXT_IMAGE,
    SENSOR_CURRENT_ALBUM,
    SENSOR_AVAILABLE_ALBUMS
)
from .db_manager import DatabaseManager
from .media_scanner import MediaScanner

_LOGGER = logging.getLogger(__name__)

async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities,
    discovery_info: Optional[DiscoveryInfoType] = None,
):
    """Set up the Picture Frame sensor platform."""
    if discovery_info is None:
        return

    domain_config = hass.data[DOMAIN]
    media_paths = domain_config[CONF_MEDIA_PATHS]
    allowed_extensions = domain_config[CONF_ALLOWED_EXTENSIONS]
    db_path = domain_config[CONF_DB_PATH]

    # Create database manager
    db_manager = DatabaseManager(db_path)
    
    # Create media scanner
    media_scanner = MediaScanner(media_paths, allowed_extensions, db_manager)
    
    # Store media scanner in hass data for services to use
    hass.data[DOMAIN]["media_scanner"] = media_scanner
    
    # Initial media scan
    await hass.async_add_executor_job(media_scanner.scan_media)
    
    # Create and add entities
    next_image_sensor = PictureFrameNextImageSensor(hass, media_scanner)
    current_album_sensor = PictureFrameCurrentAlbumSensor(hass, media_scanner)
    available_albums_sensor = PictureFrameAvailableAlbumsSensor(hass, media_scanner)
    async_add_entities(
        [next_image_sensor, current_album_sensor, available_albums_sensor], 
        True
    )


class PictureFrameNextImageSensor(Entity):
    """Representation of a Picture Frame Next Image sensor."""

    def __init__(self, hass: HomeAssistant, media_scanner: MediaScanner):
        """Initialize the sensor."""
        self.hass = hass
        self._media_scanner = media_scanner
        self._state = None
        self._attributes = {}
        self._available = False
        
        # Schedule periodic updates
        async_track_time_interval(
            hass, self._async_update, timedelta(seconds=SCAN_INTERVAL)
        )
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return "Picture Frame Next Image"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available
        
    @property
    def unique_id(self):
        """Return a unique ID."""
        return SENSOR_NEXT_IMAGE
        
    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:image"
        
    async def _async_update(self, *_):
        """Update the sensor state."""
        await self.async_update()
    
    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            # Get the next image from the media scanner
            image_info = await self.hass.async_add_executor_job(
                self._media_scanner.get_next_image
            )
            
            if image_info["path"]:
                self._state = image_info["path"]
                self._attributes = {
                    ATTR_ALBUM: image_info["album"],
                    ATTR_PATH: image_info["path"],
                    ATTR_RELATIVE_PATH: image_info["relative_path"],
                    ATTR_SOURCE_PATH: image_info["source_path"],
                    ATTR_CURRENT_ALBUM: self._media_scanner.get_current_album()
                }
                self._available = True
            else:
                self._state = None
                self._available = False
                
        except Exception as e:
            _LOGGER.error(f"Error updating Picture Frame Next Image sensor: {e}")
            self._available = False


class PictureFrameCurrentAlbumSensor(Entity):
    """Representation of a Picture Frame Current Album sensor."""

    def __init__(self, hass: HomeAssistant, media_scanner: MediaScanner):
        """Initialize the sensor."""
        self.hass = hass
        self._media_scanner = media_scanner
        self._state = None
        self._attributes = {}
        self._available = False
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return "Picture Frame Current Album"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available
        
    @property
    def unique_id(self):
        """Return a unique ID."""
        return SENSOR_CURRENT_ALBUM
        
    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:folder-multiple-image"
        
    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            # Get the current image info
            image_info = self._media_scanner.get_current_image()
            
            if image_info["album"]:
                self._state = image_info["album"]
                self._attributes = {
                    ATTR_PATH: image_info["path"],
                    ATTR_CURRENT_ALBUM: self._media_scanner.get_current_album()
                }
                self._available = True
            else:
                self._state = None
                self._available = False
                
        except Exception as e:
            _LOGGER.error(f"Error updating Picture Frame Current Album sensor: {e}")
            self._available = False


class PictureFrameAvailableAlbumsSensor(Entity):
    """Representation of a Picture Frame Available Albums sensor."""

    def __init__(self, hass: HomeAssistant, media_scanner: MediaScanner):
        """Initialize the sensor."""
        self.hass = hass
        self._media_scanner = media_scanner
        self._state = 0  # Will store the count of available albums
        self._attributes = {}
        self._available = False
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return "Picture Frame Available Albums"

    @property
    def state(self):
        """Return the state of the sensor (count of albums)."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available
        
    @property
    def unique_id(self):
        """Return a unique ID."""
        return SENSOR_AVAILABLE_ALBUMS
        
    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:folder-multiple"
        
    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return "albums"
        
    async def async_update(self):
        """Fetch new state data for the sensor."""
        try:
            # Get the available albums
            albums = self._media_scanner.get_available_albums()
            
            if albums:
                self._state = len(albums)
                self._attributes = {
                    ATTR_AVAILABLE_ALBUMS: albums
                }
                self._available = True
            else:
                self._state = 0
                self._attributes = {ATTR_AVAILABLE_ALBUMS: []}
                self._available = True
                
        except Exception as e:
            _LOGGER.error(f"Error updating Picture Frame Available Albums sensor: {e}")
            self._available = False