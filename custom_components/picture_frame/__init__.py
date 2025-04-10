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
    CONF_MEDIA_PATHS,
    CONF_ALLOWED_EXTENSIONS,
    CONF_DB_PATH,
    DEFAULT_MEDIA_PATHS,
    DEFAULT_ALLOWED_EXTENSIONS,
    DEFAULT_DB_PATH,
    SCAN_INTERVAL
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_MEDIA_PATHS, default=DEFAULT_MEDIA_PATHS): 
                    vol.All(cv.ensure_list, [cv.string]),
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
    
    media_paths = conf.get(CONF_MEDIA_PATHS, DEFAULT_MEDIA_PATHS)
    allowed_extensions = conf.get(CONF_ALLOWED_EXTENSIONS, DEFAULT_ALLOWED_EXTENSIONS)
    db_path = conf.get(CONF_DB_PATH, DEFAULT_DB_PATH)
    
    # Ensure at least one media path exists
    valid_paths = []
    for path in media_paths:
        if os.path.exists(path):
            valid_paths.append(path)
        else:
            _LOGGER.warning("Media path does not exist: %s", path)
    
    if not valid_paths:
        _LOGGER.error("None of the configured media paths exist")
        return False
    
    # Store config in hass data
    hass.data[DOMAIN] = {
        CONF_MEDIA_PATHS: valid_paths,
        CONF_ALLOWED_EXTENSIONS: allowed_extensions,
        CONF_DB_PATH: db_path,
    }
    
    # Load platforms
    component = entity_component.EntityComponent(
        _LOGGER, DOMAIN, hass, scan_interval=SCAN_INTERVAL
    )
    
    # Load sensor platform
    hass.async_create_task(
        discovery.async_load_platform(hass, "sensor", DOMAIN, {}, config)
    )
    
    # Register services directly instead of using discovery
    from .services import picture_frame_services
    await picture_frame_services.async_register(hass)
    
    return True