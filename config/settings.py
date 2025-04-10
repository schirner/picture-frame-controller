"""
Configuration settings for the Picture Frame Controller.
"""

# Path to Home Assistant media folder (adjust to your actual path)
MEDIA_ROOT = "/config/media"

# File extensions to include
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# Database file to track displayed images
DB_FILE = "/config/picture_frame_data.json"

# Default display time for each image (in seconds)
DEFAULT_DISPLAY_TIME = 60

# Enable/disable album filtering
ENABLE_ALBUM_FILTERING = True

# WebSocket configuration for communicating with Home Assistant
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8123