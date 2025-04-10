#!/usr/bin/env python3
"""
Test script for Picture Frame Controller component.
Uses Home Assistant REST API to interact with the component.
"""

import argparse
import json
import requests
import time
import os
from pprint import pprint

# Default settings
DEFAULT_HA_URL = "http://localhost:8123"

class PictureFrameTester:
    """Helper class for testing Picture Frame component in Home Assistant."""
    
    def __init__(self, ha_url, token):
        """Initialize with Home Assistant connection details."""
        self.ha_url = ha_url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
    
    def _call_service(self, domain, service, service_data=None):
        """Call a service in Home Assistant."""
        url = f"{self.ha_url}/api/services/{domain}/{service}"
        response = requests.post(
            url, 
            headers=self.headers, 
            json=service_data or {}
        )
        return response
    
    def _get_state(self, entity_id):
        """Get the state of an entity from Home Assistant."""
        url = f"{self.ha_url}/api/states/{entity_id}"
        response = requests.get(url, headers=self.headers)
        return response.json()
    
    def test_next_image(self, album=None):
        """Test getting the next image."""
        print("Testing 'next_image' service...")
        service_data = {}
        if album:
            service_data["album"] = album
        
        response = self._call_service("picture_frame", "next_image", service_data)
        if response.status_code == 200:
            print("✓ Service call successful")
        else:
            print(f"✗ Service call failed ({response.status_code}): {response.text}")
            return
            
        # Give time for state to update
        time.sleep(2)
        
        # Check the state - use next_image instead of current_image
        state = self._get_state("sensor.picture_frame_next_image")
        print("Current image state:")
        pprint(state)
        return state
        
    def test_set_album(self, album):
        """Test setting an album."""
        print(f"Testing 'set_album' service with album '{album}'...")
        # Always include the album key in the service data, with None or empty string if no album specified
        service_data = {"album": album if album else None}
        
        response = self._call_service("picture_frame", "set_album", service_data)
        if response.status_code == 200:
            print("✓ Service call successful")
        else:
            print(f"✗ Service call failed ({response.status_code}): {response.text}")
            return
            
        # Check the current album
        time.sleep(2)
        state = self._get_state("sensor.picture_frame_current_album")
        print("Current album state:")
        pprint(state)
        return state
    
    def test_clear_history(self):
        """Test clearing display history."""
        print("Testing 'reset_history' service...")
        response = self._call_service("picture_frame", "reset_history")
        
        if response.status_code == 200:
            print("✓ Service call successful")
        else:
            print(f"✗ Service call failed ({response.status_code}): {response.text}")
            
    def get_album_list(self):
        """Get the list of available albums."""
        print("Getting available albums...")
        state = self._get_state("sensor.picture_frame_available_albums")
        print("Available albums:")
        pprint(state)
        return state
    
    def run_memory_test(self, cycles=10, delay=1):
        """Run a memory usage test by cycling through images."""
        print(f"Running memory test with {cycles} cycles...")
        
        for i in range(cycles):
            print(f"Cycle {i+1}/{cycles}...")
            self.test_next_image()
            time.sleep(delay)
            
        print("Memory test complete")

def get_token():
    """Get or create long-lived access token from .ha_token file."""
    token_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.ha_token')
    
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            return f.read().strip()
    
    print("No Home Assistant token found at .ha_token")
    print("You need to create a Long-Lived Access Token in Home Assistant:")
    print("1. Go to your Home Assistant profile")
    print("2. Scroll down to Long-Lived Access Tokens")
    print("3. Create a token named 'picture_frame_tester'")
    print("4. Copy the token and paste it below")
    
    token = input("Enter your Long-Lived Access Token: ")
    
    with open(token_file, 'w') as f:
        f.write(token)
    
    print(f"Token saved to {token_file}")
    return token

def main():
    parser = argparse.ArgumentParser(description='Test Picture Frame Controller component')
    parser.add_argument('--ha-url', default=DEFAULT_HA_URL, help='Home Assistant URL')
    parser.add_argument('--action', choices=['next', 'album', 'clear', 'list', 'memory-test'], 
                        default='next', help='Action to perform')
    parser.add_argument('--album', help='Album name for album-specific actions')
    parser.add_argument('--cycles', type=int, default=10, help='Number of cycles for memory test')
    args = parser.parse_args()
    
    token = get_token()
    tester = PictureFrameTester(args.ha_url, token)
    
    if args.action == 'next':
        tester.test_next_image(args.album)
    elif args.action == 'album':
        tester.test_set_album(args.album)
    elif args.action == 'clear':
        tester.test_clear_history()
    elif args.action == 'list':
        tester.get_album_list()
    elif args.action == 'memory-test':
        tester.run_memory_test(args.cycles)

if __name__ == "__main__":
    main()