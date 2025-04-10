# Picture Frame Controller Testbench Harness

This document describes the testbench harness for testing and validating the Picture Frame Controller component prior to deploying it in a production Home Assistant environment.

## Overview

The testbench harness provides a controlled environment for developing and testing the Picture Frame Controller component. It consists of:

1. A Docker-based Home Assistant development environment
2. Test image generation utilities
3. Automated test scripts for component validation
4. Helper scripts for managing the test environment

## Directory Structure

```
dev-env/
├── config/                  # Home Assistant configuration
│   └── configuration.yaml   # Main configuration file
├── test_media/              # Test media directory structure
│   ├── album1/              # Test album 1
│   └── album2/              # Test album 2
│       ├── subalbum1/       # Nested album example
│       └── subalbum2/       # Nested album example
├── docker-compose.yaml      # Docker configuration
├── generate_test_images.py  # Script to create test images
├── run_tests.sh             # Test orchestration script
└── test_component.py        # Component interaction script
```

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- Python 3 with pip installed
- Required Python packages: Pillow, requests

### Setup

1. Navigate to the dev-env directory:
   ```bash
   cd dev-env/
   ```

2. Set up the test environment:
   ```bash
   ./run_tests.sh setup
   ```

   This command will:
   - Install required Python packages (if missing)
   - Generate test images in the test_media folders
   - Start the Home Assistant container
   - Set appropriate permissions for the test scripts

3. Wait for Home Assistant to fully initialize (usually takes a few minutes)
   - You can check progress with `./run_tests.sh logs`

4. Access the Home Assistant instance:
   - Open your browser and go to http://localhost:8123
   - Complete the onboarding process if necessary

5. Create a long-lived access token for the test scripts:
   - Click on your profile (bottom left)
   - Scroll down to "Long-Lived Access Tokens"
   - Create a token named "picture_frame_tester"
   - When you run your first test, you'll be prompted for this token

## Managing the Test Environment

The `run_tests.sh` script provides several commands for managing the test environment:

| Command | Description |
|---------|-------------|
| `setup` | Initialize the test environment |
| `start` | Start the Home Assistant container |
| `stop` | Stop the Home Assistant container |
| `restart` | Restart the Home Assistant container |
| `logs` | Show the Home Assistant logs |
| `clean` | Remove all test data and containers |
| `help` | Show available commands |

Example:
```bash
./run_tests.sh start   # Start the Home Assistant container
./run_tests.sh logs    # View the logs
./run_tests.sh stop    # Stop the container
```

## Running Tests

The testbench includes automated tests for various component features:

| Test Command | Description |
|--------------|-------------|
| `test` | Run all tests |
| `test-next` | Test the next_image service |
| `test-albums` | Test album selection functionality |
| `test-clear` | Test clearing display history |
| `test-mem` | Run a memory usage test |

Example:
```bash
./run_tests.sh test        # Run all tests
./run_tests.sh test-albums # Test album functionality
```

## Generating Test Images

The `generate_test_images.py` script creates random test images in the test_media folders. You can run it directly with:

```bash
python3 generate_test_images.py --count 10
```

Parameters:
- `--count`: Number of test images to generate in each album (default: 5)

## Manual Testing with the API Client

The `test_component.py` script provides a command-line interface for interacting with the Picture Frame component:

```bash
python3 test_component.py --action next
```

Available actions:
- `next`: Test the next_image service
- `album`: Set the current album (use with --album parameter)
- `clear`: Clear the display history
- `list`: List available albums
- `memory-test`: Run a memory usage test

Options:
- `--action`: The action to perform
- `--album`: The album name for album-specific actions
- `--ha-url`: Home Assistant URL (default: http://localhost:8123)
- `--cycles`: Number of cycles for memory test (default: 10)

Example:
```bash
# Set the current album
python3 test_component.py --action album --album album1

# Get the next image
python3 test_component.py --action next

# List available albums
python3 test_component.py --action list
```

## Monitoring Memory and Performance

To check for memory leaks or performance issues, you can use the memory test:

```bash
./run_tests.sh test-mem
```

This will cycle through images multiple times and check for resource usage patterns.

You can also monitor the Home Assistant logs:

```bash
./run_tests.sh logs
```

## Customizing the Testbench

### Modifying Home Assistant Configuration

To change Home Assistant configuration settings, edit the `config/configuration.yaml` file.

### Adding Custom Test Media

You can add your own test images to the test_media folders. The component will detect and use them automatically.

### Creating Custom Test Scenarios

Edit the `run_tests.sh` file to add custom test scenarios by combining existing test commands or adding new functions.

## Troubleshooting

### Home Assistant Fails to Start

Check the logs for errors:
```bash
./run_tests.sh logs
```

Common issues:
- Port conflicts: Modify the docker-compose.yaml file to use a different port
- Permission issues: Ensure directories are accessible by Docker

### Tests Fail to Connect

- Verify Home Assistant is running: `docker ps`
- Check if you need to create a new token: Delete the `.ha_token` file
- Verify network connectivity: Try accessing http://localhost:8123 in your browser

### Component Not Loading

- Check Home Assistant logs for component errors
- Verify the component is correctly mounted in docker-compose.yaml
- Ensure configuration.yaml contains the correct component configuration