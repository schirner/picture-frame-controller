"""
API routes for the Picture Frame Controller.
Provides endpoints for Home Assistant to get images and album information.
"""

import logging
from flask import Blueprint, jsonify, request, current_app

from src.utils.media_scanner import MediaScanner

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)

# Initialize the media scanner
media_scanner = MediaScanner()

@api_bp.route('/next_image', methods=['GET'])
def get_next_image():
    """
    Get the next image to display.
    Optional query parameter 'album' to filter by album.
    
    Returns:
        JSON with image path and album information
    """
    album = request.args.get('album', None)
    image_info = media_scanner.get_next_image(album)
    
    if not image_info["path"]:
        return jsonify({
            "success": False,
            "message": "No images found"
        }), 404
    
    return jsonify({
        "success": True,
        "image": {
            "path": image_info["path"],
            "album": image_info["album"]
        }
    })

@api_bp.route('/albums', methods=['GET'])
def get_albums():
    """
    Get a list of all available albums.
    
    Returns:
        JSON with album list
    """
    albums = media_scanner.get_albums()
    return jsonify({
        "success": True,
        "albums": albums
    })

@api_bp.route('/scan', methods=['POST'])
def scan_media():
    """
    Manually trigger a media scan.
    
    Returns:
        JSON with scan results
    """
    albums = media_scanner.scan_media()
    # Calculate total images from the albums dictionary
    total_images = sum(len(images) for images in albums.values())
    
    return jsonify({
        "success": True,
        "albums_count": len(albums),
        "total_images": total_images
    })