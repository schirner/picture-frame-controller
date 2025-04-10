#!/usr/bin/env python3
"""
Script to generate test images for the Picture Frame Controller.
This creates sample images in different albums to test component functionality.
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import argparse

def create_test_image(path, width=800, height=600, text=None):
    """Create a test image with random colors and optional text."""
    # Create a new image with random background color
    r, g, b = (random.randint(0, 200) for _ in range(3))
    image = Image.new('RGB', (width, height), color=(r, g, b))
    draw = ImageDraw.Draw(image)
    
    # Draw random shapes
    for _ in range(5):
        shape_type = random.choice(['rectangle', 'ellipse'])
        x1 = random.randint(0, width-100)
        y1 = random.randint(0, height-100)
        x2 = x1 + random.randint(50, 200)
        y2 = y1 + random.randint(50, 200)
        
        fill_r, fill_g, fill_b = (random.randint(0, 255) for _ in range(3))
        if shape_type == 'rectangle':
            draw.rectangle([x1, y1, x2, y2], fill=(fill_r, fill_g, fill_b))
        else:
            draw.ellipse([x1, y1, x2, y2], fill=(fill_r, fill_g, fill_b))

    # Add text if provided
    if text:
        try:
            # Try to find a font, fall back if not available
            try:
                font = ImageFont.truetype("DejaVuSans.ttf", 24)
            except IOError:
                font = ImageFont.load_default()
                
            draw.text((width//2-100, height//2), text, fill=(255, 255, 255), font=font)
        except Exception as e:
            print(f"Could not add text to image: {e}")
    
    # Save the image
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)
    print(f"Created test image: {path}")

def main():
    parser = argparse.ArgumentParser(description='Generate test images for Picture Frame Controller')
    parser.add_argument('--count', type=int, default=5, help='Number of images per album')
    args = parser.parse_args()
    
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_media')
    albums = [
        'album1',
        'album2/subalbum1',
        'album2/subalbum2',
    ]
    
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    # Create images in each album
    for album in albums:
        for i in range(args.count):
            filename = f"test_image_{i+1}_{timestamp}.jpg"
            path = os.path.join(base_dir, album, filename)
            create_test_image(path, text=f"{album} - Image {i+1}")
            
    print(f"Generated {args.count} test images in each album")

if __name__ == "__main__":
    main()