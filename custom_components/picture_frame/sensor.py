"""
Sensor platform for Picture Frame component.
Provides a sensor that returns the next image to display.
"""

import logging
import os
from typing import Optional, Any, Dict

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.event import async_track_time_interval
import homeassistant.util.dt as dt_util
from datetime import timedelta

from .const import (
    DOMAIN,
    CONF_MEDIA_PATH,
    CONF_ALLOWED_EXTENSIONS,
    CONF_DB_PATH,
    ATTR_ALBUM,
    ATTR_CURRENT_ALBUM,
    ATTR_AVAILABLE_ALBUMS,
    ATTR_PATH,
    ATTR_RELATIVE_PATH,
    SCAN_INTERVAL
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
    media_path = domain_config[CONF_MEDIA_PATH]
    allowed_extensions = domain_config[CONF_ALLOWED_EXTENSIONS]
    db_path = domain_config[CONF_DB_PATH]

    # Create database manager
    db_manager = DatabaseManager(db_path)
    
    # Create media scanner
    media_scanner = MediaScanner(media_path, allowed_extensions, db_manager)
    
    # Store media scanner in hass data for services to use
    hass.data[DOMAIN]["media_scanner"] = media_scanner
    
    # Initial media scan
    await hass.async_add_executor_job(media_scanner.scan_media)
    
    # Create and add entities
    sensor = PictureFrameSensor(hass, media_scanner)
    async_add_entities([sensor], True)


class PictureFrameSensor(Entity):
    """Representation of a Picture Frame sensor."""

    def __init__(self, hass: HomeAssistant, media_scanner: MediaScanner):
        """Initialize the sensor."""
        self.hass = hass
        self._media_scanner = media_scanner
        self._state = None
        self._attributes = {}
        self._available = False
        self._last_update = None
        
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
        return "picture_frame_next_image"
        
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
                    ATTR_CURRENT_ALBUM: self._media_scanner.get_current_album(),
                    ATTR_AVAILABLE_ALBUMS: self._media_scanner.get_available_albums()
                }
                self._available = True
            else:
                self._state = None
                self._available = False
                
            self._last_update = dt_util.utcnow()
            
        except Exception as e:
            _LOGGER.error(f"Error updating Picture Frame sensor: {e}")
            self._available = False