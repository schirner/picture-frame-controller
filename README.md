# Picture Frame Controller for Home Assistant

A Home Assistant custom component that manages image rotation for WallPanel, ensuring that no image is shown twice until all images have been displayed.

## Features

- **Anti-Repetition Algorithm**: Ensures that all images are shown before any repeats
- **Album Information**: Keeps track of which album each image belongs to
- **Album Filtering**: Optional feature to show images from specific albums only
- **Fully Integrated**: Runs directly as a Home Assistant custom component
- **SQLite Database**: Scalable storage solution for tracking images and display history

## How It Works

This component scans your Home Assistant media directories and catalogs all images by album using a SQLite database. It keeps track of which images have been displayed, ensuring that no image is shown twice until all images have been displayed.

Albums are determined by the top-level directory structure in your media folder.

## Installation

1. Copy the `custom_components/picture_frame` directory to your Home Assistant configuration directory under `custom_components/`.

2. Add the following configuration to your Home Assistant `configuration.yaml`:

```yaml
# Picture Frame Controller configuration
picture_frame:
  media_path: /config/media
  allowed_extensions:
    - .jpg
    - .jpeg
    - .png
    - .gif
    - .webp
  db_path: /config/picture_frame.db
```

3. Restart Home Assistant to load the custom component.

## Integration with WallPanel

The component provides a sensor `sensor.picture_frame_next_image` that will contain the path to the next image to display. WallPanel can use this sensor value directly.

### Example WallPanel Configuration

In your WallPanel config:

```yaml
wallpanel:
  dashboard_url: "https://your-home-assistant-url/dashboard"
  media_url: "{{ states('sensor.picture_frame_next_image') }}"
  # Other WallPanel configuration options...
```

### Using in Automations

You can create an automation to update the image periodically:

```yaml
automation:
  - alias: "Update WallPanel Image Every 5 Minutes"
    trigger:
      platform: time_pattern
      minutes: '/5'
    action:
      - service: picture_frame.next_image
```

### Use with Album Selection

You can select a specific album:

```yaml
automation:
  - alias: "Display Vacation Photos in the Evening"
    trigger:
      platform: time
      at: '19:00:00'
    action:
      - service: picture_frame.set_album
        data:
          album: "Vacation"
```

## Available Services

- **picture_frame.scan_media**: Scan the media directory for new images
- **picture_frame.next_image**: Get the next image to display
  - Optional parameter: `album` to filter by album
- **picture_frame.set_album**: Set the current album filter
  - Optional parameter: `album` to set which album to use
- **picture_frame.reset_history**: Clear the display history (all images will be considered new again)

## Sensor Attributes

The `sensor.picture_frame_next_image` sensor provides the following attributes:

- **path**: Full path to the image
- **album**: Album name the image belongs to
- **relative_path**: Relative path within the media directory
- **current_album**: Currently selected album (if any)
- **available_albums**: List of all available albums

## Example Dashboard Cards

You can create a nice dashboard to manage your picture frame:

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: sensor.picture_frame_next_image
    name: Current Display Image
    show_state: false
  - type: entities
    title: Picture Frame Controls
    show_header_toggle: false
    entities:
      - entity: sensor.picture_frame_next_image
        name: Current Image
        secondary_info: attribute
        attribute: album
      - type: button
        name: Next Image
        tap_action:
          action: call-service
          service: picture_frame.next_image
      - type: select
        name: Select Album
        options: >
          {{ state_attr('sensor.picture_frame_next_image', 'available_albums') }}
        tap_action:
          action: call-service
          service: picture_frame.set_album
          data:
            album: "{{ option }}"
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `media_path` | Path to your media directory | `/config/media` |
| `allowed_extensions` | File extensions to include | `.jpg, .jpeg, .png, .gif, .webp` |
| `db_path` | Path to SQLite database file | `/config/picture_frame.db` |

## License

MIT