"""
Services for the Picture Frame component.
"""

import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from ..const import (
    DOMAIN,
    SERVICE_SCAN_MEDIA,
    SERVICE_NEXT_IMAGE,
    SERVICE_SET_ALBUM,
    SERVICE_RESET_HISTORY,
    CONF_ALBUM,
    SENSOR_NEXT_IMAGE,
    SENSOR_CURRENT_ALBUM,
    SENSOR_AVAILABLE_ALBUMS
)

_LOGGER = logging.getLogger(__name__)

# Schema for scan_media service
SCAN_MEDIA_SCHEMA = vol.Schema({})

# Schema for next_image service
NEXT_IMAGE_SCHEMA = vol.Schema({
    vol.Optional(CONF_ALBUM): cv.string,
})

# Schema for set_album service
SET_ALBUM_SCHEMA = vol.Schema({
    vol.Optional(CONF_ALBUM): vol.Any(cv.string, None),
})

# Schema for reset_history service
RESET_HISTORY_SCHEMA = vol.Schema({})

async def async_register(hass: HomeAssistant):
    """Register the Picture Frame services."""
    
    async def handle_scan_media(call: ServiceCall):
        """Handle the scan_media service call."""
        media_scanner = hass.data[DOMAIN]["media_scanner"]
        await hass.async_add_executor_job(media_scanner.scan_media)
        
        # Force update of all sensors including the available albums sensor
        for entity_id in [
            f"sensor.{SENSOR_NEXT_IMAGE}", 
            f"sensor.{SENSOR_CURRENT_ALBUM}",
            f"sensor.{SENSOR_AVAILABLE_ALBUMS}"
        ]:
            await hass.services.async_call(
                "homeassistant", "update_entity", {"entity_id": entity_id}
            )
        
    async def handle_next_image(call: ServiceCall):
        """Handle the next_image service call."""
        media_scanner = hass.data[DOMAIN]["media_scanner"]
        album = call.data.get(CONF_ALBUM)
        image_info = await hass.async_add_executor_job(
            media_scanner.get_next_image, album
        )
        
        # Force sensor updates
        for entity_id in [f"sensor.{SENSOR_NEXT_IMAGE}", f"sensor.{SENSOR_CURRENT_ALBUM}"]:
            await hass.services.async_call(
                "homeassistant", "update_entity", {"entity_id": entity_id}
            )
            
        return image_info
        
    async def handle_set_album(call: ServiceCall):
        """Handle the set_album service call."""
        media_scanner = hass.data[DOMAIN]["media_scanner"]
        album = call.data.get(CONF_ALBUM)
        
        # Treat empty strings as None to reset album selection
        if album == "":
            album = None
            
        success = await hass.async_add_executor_job(media_scanner.set_album, album)
        
        # Force update of the current album sensor
        await hass.services.async_call(
            "homeassistant", "update_entity", 
            {"entity_id": f"sensor.{SENSOR_CURRENT_ALBUM}"}
        )
        
        return {"success": success, "album": album if success else None}
        
    async def handle_reset_history(call: ServiceCall):
        """Handle the reset_history service call."""
        db_manager = hass.data[DOMAIN]["media_scanner"].db_manager
        await hass.async_add_executor_job(db_manager.clear_displayed_images)
        
        # Update all sensors after resetting history
        for entity_id in [
            f"sensor.{SENSOR_NEXT_IMAGE}", 
            f"sensor.{SENSOR_CURRENT_ALBUM}"
        ]:
            await hass.services.async_call(
                "homeassistant", "update_entity", {"entity_id": entity_id}
            )
    
    # Register the services
    hass.services.async_register(
        DOMAIN, SERVICE_SCAN_MEDIA, handle_scan_media, schema=SCAN_MEDIA_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_NEXT_IMAGE, handle_next_image, schema=NEXT_IMAGE_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_SET_ALBUM, handle_set_album, schema=SET_ALBUM_SCHEMA
    )
    
    hass.services.async_register(
        DOMAIN, SERVICE_RESET_HISTORY, handle_reset_history, schema=RESET_HISTORY_SCHEMA
    )