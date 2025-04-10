"""
Picture Frame Controller for Home Assistant.
Provides a service to manage image rotation for WallPanel integration.
"""

import os
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify
import json

from src.routes.api import api_bp
from src.utils.media_scanner import MediaScanner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("picture_frame_controller.log")
    ]
)

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Register blueprints
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Create a simple frontend for testing
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy"})
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Create a MediaScanner for initial scan
    scanner = MediaScanner()
    scanner.scan_media()
    
    # Start the Flask application
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)