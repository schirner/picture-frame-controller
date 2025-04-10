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
import sys
import re
from pprint import pprint

# Default settings
DEFAULT_HA_URL = "http://localhost:8123"

class ValidationError(Exception):
    """Exception raised for test validation failures."""
    pass

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
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        self.known_albums = None
        self.last_image = None
    
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

    def assert_true(self, condition, message):
        """Assert that a condition is true."""
        if not condition:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(message)
            print(f"✗ VALIDATION FAILED: {message}")
            return False
        print(f"✓ Validated: {message}")
        self.test_results["passed"] += 1
        return True
        
    def assert_equal(self, actual, expected, message):
        """Assert that two values are equal."""
        if actual == expected:
            print(f"✓ Validated: {message}")
            self.test_results["passed"] += 1
            return True
        else:
            error_msg = f"{message} - Expected: {expected}, Got: {actual}"
            self.test_results["failed"] += 1
            self.test_results["errors"].append(error_msg)
            print(f"✗ VALIDATION FAILED: {error_msg}")
            return False
    
    def assert_in(self, item, collection, message):
        """Assert that an item is in a collection."""
        if item in collection:
            print(f"✓ Validated: {message}")
            self.test_results["passed"] += 1
            return True
        else:
            error_msg = f"{message} - {item} not found in {collection}"
            self.test_results["failed"] += 1
            self.test_results["errors"].append(error_msg)
            print(f"✗ VALIDATION FAILED: {error_msg}")
            return False
                               
    def assert_matches(self, value, pattern, message):
        """Assert that a value matches a regular expression pattern."""
        if bool(re.match(pattern, value)):
            print(f"✓ Validated: {message}")
            self.test_results["passed"] += 1
            return True
        else:
            error_msg = f"{message} - {value} does not match pattern {pattern}"
            self.test_results["failed"] += 1
            self.test_results["errors"].append(error_msg)
            print(f"✗ VALIDATION FAILED: {error_msg}")
            return False
    
    def test_next_image(self, album=None):
        """Test getting the next image with validation."""
        print("\nTesting 'next_image' service...")
        service_data = {}
        if album:
            service_data["album"] = album
        
        response = self._call_service("picture_frame", "next_image", service_data)
        if response.status_code == 200:
            print("✓ Service call successful")
        else:
            print(f"✗ Service call failed ({response.status_code}): {response.text}")
            return None
            
        # Give time for state to update
        time.sleep(2)
        
        # Check the state - use next_image sensor
        state = self._get_state("sensor.picture_frame_next_image")
        print("Current image state:")
        pprint(state)
        
        # Store the image path to check for duplicates
        current_image = state["state"]
        
        # Run validation checks
        if "state" in state:
            # Check that the path exists and has expected format
            self.assert_matches(state["state"], r'^/media/.+\.(jpg|jpeg|png|gif|webp)$', 
                              "Image path has the correct format")
            
            # Check for duplicates if we have a last image
            if self.last_image:
                self.assert_true(current_image != self.last_image, 
                                "New image is different from previous image")
            
            # Check that attributes are present
            if "attributes" in state:
                attrs = state["attributes"]
                self.assert_in("album", attrs, "Image has album attribute")
                self.assert_in("path", attrs, "Image has path attribute")
                self.assert_equal(attrs["path"], state["state"], "Path matches state")
                self.assert_in("relative_path", attrs, "Image has relative_path attribute")
                
                # If a specific album was requested, verify it matches
                if album and "album" in attrs:
                    # For path-style albums, get the last segment
                    expected_album = album.split("/")[-1] if "/" in album else album
                    self.assert_equal(attrs["album"], expected_album, 
                                     f"Image is from the requested album {expected_album}")
        
        # Update last image for future comparisons
        self.last_image = current_image
        return state
        
    def test_set_album(self, album):
        """Test setting an album with validation."""
        print(f"\nTesting 'set_album' service with album '{album}'...")
        # Always include the album key in the service data, with None if no album specified
        service_data = {"album": album if album else None}
        
        response = self._call_service("picture_frame", "set_album", service_data)
        if response.status_code == 200:
            print("✓ Service call successful")
        else:
            print(f"✗ Service call failed ({response.status_code}): {response.text}")
            return None
            
        # Check the current album
        time.sleep(2)
        state = self._get_state("sensor.picture_frame_current_album")
        print("Current album state:")
        pprint(state)
        
        # Run validation checks
        if album and album != "":
            # For path-style albums, get the last segment
            expected_album = album.split("/")[-1] if "/" in album else album
            
            # Should match the album name
            if self.known_albums and expected_album in self.known_albums:
                self.assert_in(state["state"], self.known_albums, 
                              f"Album {state['state']} is in known albums list")
                
                if "attributes" in state and "current_album" in state["attributes"]:
                    self.assert_equal(state["attributes"]["current_album"], expected_album, 
                                     "current_album attribute matches requested album")
        
        return state
    
    def test_clear_history(self):
        """Test clearing display history with validation."""
        print("\nTesting 'reset_history' service...")
        
        # First, get a reference image
        before_image = self._get_state("sensor.picture_frame_next_image")["state"]
        
        response = self._call_service("picture_frame", "reset_history")
        if response.status_code == 200:
            print("✓ Service call successful")
        else:
            print(f"✗ Service call failed ({response.status_code}): {response.text}")
            return False
            
        # Get the next image after clearing history
        time.sleep(2)
        self._call_service("picture_frame", "next_image", {})
        time.sleep(2)
        after_state = self._get_state("sensor.picture_frame_next_image")
        after_image = after_state["state"]
        
        print(f"Before reset: {before_image}")
        print(f"After reset:  {after_image}")
        
        # We can't guarantee images will be different after clearing history
        # But we can check that a valid image is returned
        self.assert_matches(after_image, r'^/media/.+\.(jpg|jpeg|png|gif|webp)$',
                          "Image path has the correct format after reset")
        
        return True
            
    def get_album_list(self):
        """Get the list of available albums with validation."""
        print("\nGetting available albums...")
        state = self._get_state("sensor.picture_frame_available_albums")
        print("Available albums:")
        pprint(state)
        
        # Store albums for future tests
        if "attributes" in state and "available_albums" in state["attributes"]:
            self.known_albums = state["attributes"]["available_albums"]
        
        # Run validation checks
        if "state" in state:
            # State should be the number of albums
            self.assert_matches(state["state"], r'^\d+$', "Album count is a number")
            
            if "attributes" in state and "available_albums" in state["attributes"]:
                albums = state["attributes"]["available_albums"]
                count = int(state["state"])
                self.assert_equal(len(albums), count, "Album count matches number of albums in list")
                
                # Should contain at least some standard albums we expect
                self.assert_true(len(albums) >= 1, "At least one album is available")
                self.assert_in("Root", albums, "Root album is present")
                
        return state
    
    def run_memory_test(self, cycles=10, delay=1):
        """Run a memory usage test by cycling through images."""
        print(f"\nRunning memory test with {cycles} cycles...")
        
        seen_images = set()
        duplicate_count = 0
        
        for i in range(cycles):
            print(f"Cycle {i+1}/{cycles}...")
            state = self.test_next_image()
            if state and "state" in state:
                path = state["state"]
                if path in seen_images:
                    duplicate_count += 1
                    print(f"  Duplicate image detected: {path}")
                seen_images.add(path)
            time.sleep(delay)
            
        # After a full cycle through images, verify how many duplicates
        total_images = len(seen_images)
        print(f"\nMemory test summary:")
        print(f"- Total unique images: {total_images}")
        print(f"- Duplicate images: {duplicate_count}")
        
        # If cycles > total images, we expect some duplicates after all images have been shown once
        if cycles > total_images:
            expected_dupes = cycles - total_images
            self.assert_true(duplicate_count <= expected_dupes + 1,  # Allow for 1 extra due to timing
                           f"Duplicate count ({duplicate_count}) is close to expected ({expected_dupes})")
        else:
            self.assert_equal(duplicate_count, 0, "No duplicates when cycle count <= total images")
            
        print("Memory test complete")
        return total_images, duplicate_count
        
    def print_test_summary(self):
        """Print a summary of all test results."""
        total = self.test_results["passed"] + self.test_results["failed"]
        print("\n" + "="*60)
        print(f"TEST SUMMARY: {self.test_results['passed']}/{total} checks passed")
        print("="*60)
        
        if self.test_results["failed"] > 0:
            print("\nFAILED CHECKS:")
            for i, error in enumerate(self.test_results["errors"], 1):
                print(f"{i}. {error}")
            return False
        else:
            print("\nAll validation checks passed!")
            return True

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
    parser.add_argument('--action', choices=['next', 'album', 'clear', 'list', 'memory-test', 'validate-all'], 
                        default='next', help='Action to perform')
    parser.add_argument('--album', help='Album name for album-specific actions')
    parser.add_argument('--cycles', type=int, default=10, help='Number of cycles for memory test')
    parser.add_argument('--validate', action='store_true', help='Validate the test results')
    args = parser.parse_args()
    
    token = get_token()
    tester = PictureFrameTester(args.ha_url, token)
    
    if args.action == 'validate-all':
        # Run complete validation suite
        tester.get_album_list()
        tester.test_set_album("album1")
        tester.test_next_image()
        tester.test_set_album("album2/subalbum1")
        tester.test_next_image()
        tester.test_clear_history()
        tester.test_set_album("")
        tester.test_next_image()
        # Print final summary
        success = tester.print_test_summary()
        sys.exit(0 if success else 1)
    elif args.action == 'next':
        tester.test_next_image(args.album)
    elif args.action == 'album':
        tester.test_set_album(args.album)
    elif args.action == 'clear':
        tester.test_clear_history()
    elif args.action == 'list':
        tester.get_album_list()
    elif args.action == 'memory-test':
        tester.run_memory_test(args.cycles)
    
    # Print summary if validation is enabled
    if args.validate:
        success = tester.print_test_summary()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()