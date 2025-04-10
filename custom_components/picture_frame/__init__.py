"""
Picture Frame Controller for Home Assistant.
Provides image rotation ensuring no repeats until all images are shown.
"""
import logging
import os
import voluptuous as vol

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import discovery
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_PATH
import homeassistant.helpers.entity_component as entity_component

from .const import (
    DOMAIN,
    CONF_MEDIA_PATH,
    CONF_ALLOWED_EXTENSIONS,
    CONF_DB_PATH,
    DEFAULT_MEDIA_PATH,
    DEFAULT_ALLOWED_EXTENSIONS,
    DEFAULT_DB_PATH,
    SCAN_INTERVAL
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_MEDIA_PATH, default=DEFAULT_MEDIA_PATH): cv.string,
                vol.Optional(CONF_ALLOWED_EXTENSIONS, default=DEFAULT_ALLOWED_EXTENSIONS): 
                    vol.All(cv.ensure_list, [cv.string]),
                vol.Optional(CONF_DB_PATH, default=DEFAULT_DB_PATH): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Picture Frame component."""
    conf = config.get(DOMAIN, {})
    
    media_path = conf.get(CONF_MEDIA_PATH, DEFAULT_MEDIA_PATH)
    allowed_extensions = conf.get(CONF_ALLOWED_EXTENSIONS, DEFAULT_ALLOWED_EXTENSIONS)
    db_path = conf.get(CONF_DB_PATH, DEFAULT_DB_PATH)
    
    # Ensure media path exists
    if not os.path.exists(media_path):
        _LOGGER.error("Media path does not exist: %s", media_path)
        return False
    
    # Store config in hass data
    hass.data[DOMAIN] = {
        CONF_MEDIA_PATH: media_path,
        CONF_ALLOWED_EXTENSIONS: allowed_extensions,
        CONF_DB_PATH: db_path,
    }
    
    # Load platforms
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )
    
    # Register services
    hass.async_create_task(
        hass.helpers.discovery.async_load_platform("services", DOMAIN, {}, config)
    )
    
    # Load services
    await _register_services(hass)
    
    return True

async def _register_services(hass):
    """Register services for the Picture Frame component."""
    from .services import picture_frame_services
    await picture_frame_services.async_register(hass)