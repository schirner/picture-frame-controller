"""Constants for the Picture Frame component."""

DOMAIN = "picture_frame"

# Configuration constants
CONF_MEDIA_PATH = "media_path"
CONF_ALLOWED_EXTENSIONS = "allowed_extensions"
CONF_DB_PATH = "db_path"
CONF_ALBUM = "album"

# Default values
DEFAULT_MEDIA_PATH = "/config/media"
DEFAULT_ALLOWED_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp"]
DEFAULT_DB_PATH = "/config/picture_frame.db"

# Update interval for sensor (in seconds)
SCAN_INTERVAL = 300  # 5 minutes

# Service names
SERVICE_SCAN_MEDIA = "scan_media"
SERVICE_NEXT_IMAGE = "next_image"
SERVICE_SET_ALBUM = "set_album"
SERVICE_RESET_HISTORY = "reset_history"

# Attributes
ATTR_ALBUM = "album"
ATTR_CURRENT_ALBUM = "current_album"
ATTR_AVAILABLE_ALBUMS = "available_albums"
ATTR_PATH = "path"
ATTR_RELATIVE_PATH = "relative_path"