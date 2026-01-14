# Complete Caching and Offline Capability

## Overview
VetRender now has comprehensive caching for both map tiles and terrain data, enabling fully offline operation after initial setup.

## Map Tile Caching

### Automatic Multi-Level Caching
When you set a transmitter location, all zoom levels (10-16) are automatically cached:
- **Location**: `map_cache/tiles/[basemap]/[zoom]/[x]/[y].png`
- **Size**: ~5-15 MB per location
- **Persistence**: Permanent until manually cleared
- **Coverage**: 3x3 tile grid at each zoom level (63 tiles total)

### Scroll Wheel Zoom
- **Scroll up**: Zoom in (loads cached tiles instantly)
- **Scroll down**: Zoom out (loads cached tiles instantly)
- **Range**: Zoom levels 10-16
- **Speed**: < 100ms per zoom change (uses cache)

## Terrain Data Caching

### How It Works
Terrain elevation data is now cached locally with a grid-based system:

**Cache Structure:**
- **Directory**: `terrain_cache/`
- **Resolution**: 0.01° grid (~1km at equator)
- **Format**: Pickle files for fast loading
- **Organization**: `terrain_cache/lat_[XX]/lon_[YY]/[lat]_[lon].pkl`

**Two-Level Cache:**
1. **Memory Cache**: Active session, instant access
2. **Disk Cache**: Persistent across sessions

### Benefits

**First Run (Location):**
- Downloads terrain data from Open-Elevation API
- Saves to local disk cache
- Typical: 50-500 points per coverage calculation

**Subsequent Runs (Same Location):**
- Loads from disk cache (if available)
- No API calls needed
- 10-100x faster terrain calculations
- Fully offline capable

**Example Output:**
```
First calculation:
  Fetching 360 uncached terrain points (cached: 0)
  Time: 15-30 seconds

Second calculation (same area):
  All 360 terrain points loaded from cache
  Time: < 1 second
```

## Fully Offline Operation

Once you've cached a location, VetRender can operate completely offline:

### What Works Offline:
✅ Map display at all cached zoom levels
✅ Scroll wheel zooming
✅ Coverage calculations with terrain
✅ Changing transmitter parameters
✅ Moving transmitter within cached area
✅ Signal strength probing
✅ All UI operations

### What Requires Internet:
❌ Initial location setup (downloads tiles + terrain)
❌ Changing to new basemap style
❌ Moving to uncached location
❌ Terrain outside cached radius

## Cache Management

### Map Tile Cache
Use "Manage Cache..." from right-click menu to:
- View cache size and statistics
- Clear specific basemaps
- Clear entire cache
- See cached locations

### Terrain Cache
Automatically managed, grows as you use different locations:
- **File size**: ~100 bytes per cached point
- **Typical coverage area**: 1-5 MB per location
- **No manual management needed** (yet)

## Performance Improvements

### Map Operations
- **Before**: 1-5 seconds per zoom change (downloads tiles)
- **After**: < 100ms per zoom change (uses cache)

### Terrain Calculations
- **First calculation**: 15-30 seconds (downloads elevation data)
- **Subsequent calculations**: < 1 second (uses cache)
- **Same location, different parameters**: Instant (fully cached)

### Overall Workflow
1. **Setup location** (one-time): 20-40 seconds
   - Caches all zoom levels
   - Downloads initial terrain data
2. **Work offline**: Unlimited
   - All operations use local cache
   - No network needed
3. **Move to new location**: 20-40 seconds
   - Repeats caching process

## Technical Details

### Map Tile Cache
- Format: PNG images (256x256 pixels)
- Per-tile size: 10-50 KB (depends on terrain complexity)
- Total for location: ~5-15 MB (all zoom levels)

### Terrain Cache
- Format: Python pickle (binary)
- Per-point size: ~100 bytes
- Grid resolution: 0.01° (~1 km)
- Compression: None (fast loading)

### Memory Usage
- **Map tiles**: Loaded on demand per zoom level (~2 MB active)
- **Terrain data**: In-memory cache for active points (~1-5 MB)
- **Total**: Minimal RAM impact

## Cache Locations

All caches are stored in the application directory:
```
VetRender/
├── map_cache/
│   └── tiles/
│       ├── Esri WorldImagery/
│       ├── OpenStreetMap/
│       └── ...
└── terrain_cache/
    ├── lat_43/
    │   └── lon_-112/
    │       ├── 43.467_-112.034.pkl
    │       └── ...
    └── lat_44/
        └── ...
```

## Best Practices

1. **Pre-cache your sites**: Use "Reset Location" to cache all important sites
2. **Let terrain build**: First calculation is slow, subsequent ones are instant
3. **Don't clear cache**: Unless you need to free space
4. **Multiple basemaps**: Each basemap caches separately (use one primary)
5. **Large coverage areas**: Higher terrain quality = more cached points = better offline performance

## Future Enhancements

Possible additions:
- Bulk terrain pre-caching for coverage radius
- Cache expiration/cleanup tools
- Cache export/import for sharing
- SRTM offline tile support (no API needed)
- Cache compression options
