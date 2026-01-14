# Auto-Save Configuration Feature

## Overview
VetRender now automatically saves and restores your last session configuration, so you don't need to re-enter settings every time you start the app.

## What Gets Auto-Saved

The following settings are automatically saved:
- **Station Information**: Callsign, TX type, transmission mode
- **Location**: Transmitter latitude and longitude
- **Power Settings**: ERP, frequency, antenna height
- **Coverage Settings**: Max distance, signal threshold, terrain quality
- **Map Settings**: Zoom level, basemap style
- **Terrain Settings**: Use terrain checkbox state
- **Antenna Pattern**: Current antenna pattern name

## How It Works

### On Startup
1. The app looks for `.vetrender_config.json` in the application directory
2. If found, it loads all your previous settings automatically
3. If not found (first run), you'll see the project setup dialog as usual

### During Operation
Configuration is automatically saved when you:
- Change transmitter location (click or precise coordinates)
- Edit transmitter configuration (ERP, frequency, height, threshold)
- Change antenna pattern
- Edit station information
- Change basemap style
- Reset location
- Complete project setup

### On Exit
When you close the application, the current configuration is saved automatically.

## Configuration File

- **File**: `.vetrender_config.json`
- **Location**: Same directory as the application
- **Format**: JSON (human-readable)
- **Hidden**: Yes (starts with `.` on Unix-like systems)

## Benefits

1. **No More Re-Entry**: Your settings persist between sessions
2. **Quick Startup**: Skip the setup dialog on subsequent launches
3. **Seamless Workflow**: Changes are saved automatically as you work
4. **Multiple Projects**: You can still use "Save Project" and "Load Project" for different configurations

## Note

The auto-save feature is independent from the "Save Project" feature:
- **Auto-save**: Automatically saves your current working configuration
- **Save Project**: Lets you save named project files (.vtr) for different sites/scenarios
