# VetRender Debug Logs

This directory contains coordinate tracking debug logs to help diagnose GPS positioning issues.

## Log Files

Each time you run VetRender, a new log file is created with a timestamp:
- Format: `coordinate_debug_YYYYMMDD_HHMMSS.log`
- Example: `coordinate_debug_20260112_143052.log`

## What's Logged

The debug logger tracks all coordinate-related operations:

### 1. Map Loading
- Requested center coordinates (tx_lat, tx_lon)
- Integer tile position returned by map system
- Actual lat/lon that the tile center represents
- Offset between requested and actual center

### 2. Transmitter Marker Positioning
- TX coordinates
- Calculated pixel position on map
- Image center position
- Offset from center in pixels

### 3. Location Changes
- Old and new coordinates when you set transmitter location
- Change in degrees

### 4. Signal Probing
- Click position in pixels
- Calculated probe coordinates
- TX coordinates for reference
- Distance and azimuth from TX
- Coordinate difference

## How to Use

1. **Run VetRender** - A new log file is automatically created
2. **Perform actions** - Set transmitter location, probe signals, etc.
3. **Check the latest log** - Open the most recent `.log` file
4. **Look for discrepancies** - Compare requested vs actual coordinates

## Troubleshooting with Logs

If coordinates don't match up:

1. Check the **MAP LOADED** section:
   - Is "Map tile center represents" close to the requested coordinates?
   - If offset is large (>0.5°), there may be a tile calculation bug

2. Check the **TRANSMITTER MARKER POSITION** section:
   - Is the marker pixel position far from image center?
   - Offset should match the fractional tile position

3. Check the **SIGNAL PROBE** section:
   - When probing at TX marker, probe coordinates should equal TX coordinates
   - If they differ significantly, coordinate conversion has a bug

## Example Log Excerpt

```
[14:30:52.123] ================================================================================
[14:30:52.123] MAP LOADED
[14:30:52.123] ================================================================================
[14:30:52.123] Requested center: Lat=43.713501, Lon=-113.010241
[14:30:52.123] Zoom level: 10
[14:30:52.123] Map tile (integer): X=175, Y=367
[14:30:52.124] Map tile center represents: Lat=43.580410, Lon=-113.027344
[14:30:52.124] Offset from requested: (0.133091°, 0.017103°)
[14:30:52.124] Distance offset: 14.77 km N/S, 1.90 km E/W
[14:30:52.124] ================================================================================
```

This shows a 14.77 km offset - the transmitter marker should be drawn 14.77 km north of the image center!
