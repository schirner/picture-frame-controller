#!/bin/bash
# Helper script for setting up and running tests for Picture Frame Controller

set -e

# Directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Function to display help
show_help() {
    echo "Picture Frame Controller Test Harness"
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  setup       Generate test images and start Home Assistant container"
    echo "  start       Start the Home Assistant container"
    echo "  stop        Stop the Home Assistant container"
    echo "  restart     Restart the Home Assistant container"
    echo "  logs        Show Home Assistant container logs"
    echo "  test        Run all tests"
    echo "  test-mem    Run memory usage test"
    echo "  test-next   Test next_image service"
    echo "  test-albums Test album functionality"
    echo "  test-clear  Test clearing history"
    echo "  test-validate Run all tests with validation"
    echo "  clean       Remove all test images"
    echo "  help        Show this help message"
    echo ""
}

# Function for setting up test environment
setup_environment() {
    echo "Setting up test environment..."
    
    # Check if Python PIL is installed
    if ! python3 -c "import PIL" &> /dev/null; then
        echo "Installing required Python packages..."
        pip install Pillow requests
    fi
    
    # Generate test images
    echo "Generating test images..."
    python3 generate_test_images.py --count 20
    
    # Make test scripts executable
    chmod +x test_component.py
    
    # Start Home Assistant container
    start_container
    
    echo "Setup complete. Home Assistant will be available at http://localhost:8123/"
    echo "Wait for Home Assistant to fully start (check with 'docker logs ha_test_picture_frame')"
    echo "Then create a long-lived access token and use it with test_component.py"
}

# Function to start the container
start_container() {
    echo "Starting Home Assistant container..."
    docker-compose up -d
    echo "Home Assistant is starting at http://localhost:8123/"
    echo "It may take a few minutes to fully initialize."
}

# Function to stop the container
stop_container() {
    echo "Stopping Home Assistant container..."
    docker-compose down
}

# Function to restart the container
restart_container() {
    echo "Restarting Home Assistant container..."
    docker-compose restart
    echo "Home Assistant is restarting..."
}

# Function to show logs
show_logs() {
    echo "Showing Home Assistant logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

# Function to clean up test environment
clean_environment() {
    echo "Cleaning up test environment..."
    
    # Stop container if running
    docker-compose down
    
    # Remove test images
    find test_media -type f -name "*.jpg" -delete
    find test_media -type f -name "*.png" -delete
    
    echo "Cleanup complete."
}

# Function to run all tests
run_all_tests() {
    echo "Running all tests..."
    
    # Test getting available albums
    python3 test_component.py --action list
    
    # Test setting album to album1
    python3 test_component.py --action album --album album1
    
    # Test getting next image in album1
    python3 test_component.py --action next
    
    # Test setting album to album2/subalbum1
    python3 test_component.py --action album --album album2/subalbum1
    
    # Test getting next image in album2/subalbum1
    python3 test_component.py --action next
    
    # Test clearing history
    python3 test_component.py --action clear
    
    # Test setting back to all albums
    python3 test_component.py --action album --album ""
    
    # Test getting next image from all albums
    python3 test_component.py --action next
    
    echo "All tests completed."
}

# Function to run all tests with validation
run_validated_tests() {
    echo "Running all tests with validation..."
    python3 test_component.py --action validate-all
}

# Function to run memory test
run_memory_test() {
    echo "Running memory usage test..."
    python3 test_component.py --action memory-test --cycles 50
}

# Function to test next image
test_next_image() {
    echo "Testing next_image service..."
    python3 test_component.py --action next
}

# Function to test albums
test_albums() {
    echo "Testing album functionality..."
    python3 test_component.py --action list
    python3 test_component.py --action album --album album1
    python3 test_component.py --action next
    python3 test_component.py --action album --album album2/subalbum1
    python3 test_component.py --action next
    python3 test_component.py --action album --album ""
    python3 test_component.py --action next
}

# Function to test clearing history
test_clear_history() {
    echo "Testing clearing display history..."
    python3 test_component.py --action clear
    python3 test_component.py --action next
}

# Main script logic
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    setup)
        setup_environment
        ;;
    start)
        start_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        restart_container
        ;;
    logs)
        show_logs
        ;;
    test)
        run_all_tests
        ;;
    test-mem)
        run_memory_test
        ;;
    test-next)
        test_next_image
        ;;
    test-albums)
        test_albums
        ;;
    test-clear)
        test_clear_history
        ;;
    test-validate)
        run_validated_tests
        ;;
    clean)
        clean_environment
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown option: $1"
        show_help
        exit 1
        ;;
esac

exit 0