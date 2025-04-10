# Picture Frame Controller for Home Assistant

A service that manages image rotation for Home Assistant with WallPanel, ensuring that no image is shown twice until all images have been displayed.

## Features

- **Anti-Repetition Algorithm**: Ensures that all images are shown before any repeats
- **Album Information**: Keeps track of which album each image belongs to
- **Album Filtering**: Optional feature to show images from specific albums only
- **Simple Web Interface**: Manage your images and albums through a web browser
- **RESTful API**: Integrate with Home Assistant automations or other services
- **SQLite Database**: Scalable storage solution for tracking images and display history

## How It Works

This service scans your Home Assistant media directory and catalogs all images by album using a SQLite database. It keeps track of which images have been displayed, ensuring that no image is shown twice until all images have been displayed.

Albums are determined by the top-level directory structure in your media folder.

## Installation

1. Clone this repository to your Home Assistant server or a machine that can access your Home Assistant media.

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Configure the service by editing the settings in `config/settings.py`:

```python
# Path to your Home Assistant media folder
MEDIA_ROOT = "/config/media"

# File extensions to include
ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

# Database file path for SQLite storage
DB_FILE = "/config/picture_frame_controller.db"
```

4. Run the service:

```bash
python app.py
```

## Integration with Home Assistant and WallPanel

### Option 1: Using the REST API

1. Configure WallPanel to use the `/api/next_image` endpoint to fetch images.

2. Create an automation in Home Assistant to refresh the image periodically, for example:

```yaml
automation:
  - alias: "Update WallPanel Image"
    trigger:
      platform: time_pattern
      minutes: '/5'  # Every 5 minutes
    action:
      - service: rest_command.get_next_image
        data:
          album: "Vacation"  # Optional parameter
```

3. Define the rest_command in your Home Assistant configuration:

```yaml
rest_command:
  get_next_image:
    url: "http://your-server:5000/api/next_image{% if album is defined %}?album={{ album }}{% endif %}"
    method: GET
    verify_ssl: false
    timeout: 30
```

### Option 2: Proxy Through Home Assistant

1. Create a sensor that fetches the next image path:

```yaml
sensor:
  - platform: rest
    name: next_display_image
    resource: http://your-server:5000/api/next_image
    value_template: "{{ value_json.image.path }}"
    json_attributes:
      - album
```

2. Update your WallPanel configuration to use the sensor value.

## API Endpoints

- `GET /api/next_image`: Get the next image to display
  - Optional query parameter: `album` to filter by album
  
- `GET /api/albums`: Get a list of all available albums

- `POST /api/scan`: Trigger a manual scan of the media directory

## Web Interface

Access the web interface at `http://your-server:5000/` to:

- View the current image
- Select albums to filter by
- Trigger a manual media scan

## License

MIT