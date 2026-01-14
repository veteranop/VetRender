# Multi-Zoom Level Caching

## Overview
VetRender now automatically caches map tiles at **all zoom levels (10-16)** whenever you set a transmitter location. This provides instant, smooth zooming with no loading delays.

## What Gets Cached

When you set a transmitter location (by any method), the app automatically downloads and caches:
- Zoom level 10 (widest view, ~100+ km coverage)
- Zoom level 11
- Zoom level 12
- Zoom level 13 (default view)
- Zoom level 14
- Zoom level 15
- Zoom level 16 (closest view, street-level detail)

Each zoom level caches a 3x3 grid of 256x256 pixel tiles around your location.

## When Caching Happens

The app caches all zoom levels automatically when you:

1. **Initial Project Setup**: When you first set up a project location
2. **Right-Click Set Location**: When you right-click and "Set Transmitter Location (Click)"
3. **Precise Coordinates**: When you use "Set Transmitter Location (Coordinates)..."
4. **Reset Location**: When you use "Reset Location..." to move to a new area

## User Experience

**Before caching:**
- Changing zoom levels required downloading tiles
- Each zoom change took 1-5 seconds
- User had to wait between zoom operations

**After caching:**
- All zoom levels are pre-downloaded
- Zooming is instant (< 100ms)
- Smooth, responsive experience like Google Maps
- Progress indicator shows caching status

## Progress Indicator

While caching, you'll see in the status bar:
```
Caching zoom level 10 [1/7]...
Caching zoom level 11 [2/7]...
Caching zoom level 12 [3/7]...
...
All zoom levels cached - Ready
```

## Cache Storage

- **Location**: `map_cache/tiles/` directory
- **Organization**: Organized by basemap, zoom level, and tile coordinates
- **Size**: Approximately 5-15 MB per location (depends on terrain variety)
- **Persistence**: Cache survives app restarts - tiles are only downloaded once

## Benefits

1. **Instant Zoom Response**: No waiting when exploring different zoom levels
2. **Better User Experience**: Smooth, professional feel
3. **Reduced Bandwidth**: Tiles downloaded once, used forever
4. **Offline Capability**: Once cached, works without internet for that location
5. **Efficient Coverage Planning**: Quickly switch between overview and detail views

## Technical Details

The caching process:
1. Downloads 3x3 grid (9 tiles) at each zoom level
2. Each tile is 256x256 pixels
3. Total tiles cached: 7 levels × 9 tiles = 63 tiles per location
4. Tiles are saved to disk as PNG files
5. Organized by: `basemap/zoom/x_tile/y_tile.png`

## Managing Cache

Use "Manage Cache..." from the right-click menu to:
- View cache size and statistics
- Clear cache for specific basemaps
- Clear entire cache
- See which locations are cached
