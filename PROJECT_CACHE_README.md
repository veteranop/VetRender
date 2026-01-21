# Project-Based Caching System

## Overview

VetRender now saves **all terrain elevation data and land cover polygons** directly in project files (`.vtr`). This makes projects:

✅ **Fully portable** - Share projects with colleagues without losing terrain data
✅ **Offline-capable** - Re-run calculations without internet (no API calls)
✅ **Faster** - Instant terrain lookup from cached data
✅ **Self-contained** - Everything needed for the calculation is in one file

## How It Works

### When You Save a Project

`File → Save Project` now includes:

1. **All project parameters** (frequency, location, ERP, etc.)
2. **Terrain elevation cache** for the coverage area
3. **Land cover polygons** (water, urban, forest) if enabled
4. **Coverage plots** (as before)

### File Format

Project files (`.vtr`) are JSON with embedded cache data:

```json
{
  "version": "3.1",
  "callsign": "KDPI",
  "tx_lat": 43.661225,
  "tx_lon": -114.402965,
  ...
  "terrain_cache": {
    "43.6612,−114.4030": 1823,
    "43.6622,−114.4030": 1829,
    ...thousands of elevation points...
  },
  "land_cover_cache": {
    "water": [[[lon,lat], [lon,lat]...]],
    "urban": [...],
    "forest": [...]
  }
}
```

### When You Load a Project

`File → Load Project` will:

1. Load all project parameters
2. **Import terrain cache** into memory and disk cache
3. **Import land cover polygons** if available
4. Ready to calculate instantly (no API fetches needed!)

## Cache Coverage

### Terrain Cache

Exports all terrain elevations within the coverage area bounding box:

- **Coverage**: `max_distance` × 2 (full coverage square)
- **Resolution**: 0.01° grid (~1km)
- **Size**: ~1-5 MB for 200km coverage area

Example for 200km coverage:
- Bounding box: 400km × 400km
- Grid points: ~160,000 elevation samples
- JSON size: ~2-3 MB

### Land Cover Cache

Exports all OSM polygons within coverage area:

- Water bodies, rivers, lakes
- Urban areas (buildings, residential, commercial)
- Forests and vegetation

Typical sizes:
- Rural area: 100-500 KB
- Urban area: 1-5 MB
- Mixed terrain: 500 KB - 2 MB

## Benefits

### 1. Portability

Share your `.vtr` project file with anyone:
- They don't need to fetch terrain data
- Calculations are exactly reproducible
- Works offline

### 2. Speed

**Without cache:**
- 18 million API calls for Ultra quality
- 2-4 hours calculation time
- Depends on internet speed

**With cache (after first save):**
- Zero API calls
- Instant terrain lookup from project file
- 5-10 minutes calculation time (just RF math)

### 3. Consistency

- Same terrain data every time
- No API changes affect results
- Perfect for before/after comparisons

## Practical Usage

### Workflow A: Online (Normal)

1. Create new project, set parameters
2. **Calculate coverage** (fetches terrain from API)
3. **Save project** (terrain cache embedded)
4. Share `.vtr` file
5. Recipient loads project - instant calculations!

### Workflow B: Offline

1. Load a `.vtr` project with embedded cache
2. Adjust parameters (ERP, frequency, antenna)
3. **Calculate instantly** - no internet needed
4. Compare multiple scenarios

### Workflow C: Iterative Design

1. Calculate coverage with terrain (slow first time)
2. Save project
3. Try different antennas/parameters
4. Each subsequent calculation is **fast** (uses cache)
5. Save each variation as new project

## Technical Details

### Terrain Cache Export

Location: `models/terrain.py`

```python
TerrainHandler.export_cache_for_area(center_lat, center_lon, radius_km)
```

- Searches memory cache + disk cache
- Filters to coverage area bounding box
- Returns JSON-serializable dictionary

### Terrain Cache Import

```python
TerrainHandler.import_cache(cache_data)
```

- Loads into memory cache (fast lookups)
- Also saves to disk cache (persistent)
- Automatically used by `get_elevations_batch()`

### Land Cover Cache Export

Location: `models/land_cover.py`

```python
land_cover_handler.export_cache()
```

- Converts Shapely polygons to coordinate lists
- JSON-serializable format
- Includes bounding box metadata

### Land Cover Cache Import

```python
land_cover_handler.import_cache(cache_data)
```

- Reconstructs Shapely polygons
- Prepares geometries for fast point-in-polygon checks
- Ready for RF loss calculations

## File Size Expectations

| Coverage Area | Terrain Cache | Land Cover | Total Project |
|---------------|---------------|------------|---------------|
| 50 km         | 400 KB        | 200 KB     | ~1 MB         |
| 100 km        | 1 MB          | 500 KB     | ~2 MB         |
| 200 km        | 3 MB          | 1-2 MB     | ~5 MB         |
| 300 km        | 5 MB          | 2-4 MB     | ~10 MB        |

Projects remain small enough to:
- Email to colleagues
- Store in Git repos
- Share on cloud storage

## Backward Compatibility

### Old Projects (v3.0)

Projects saved before cache feature:
- Still load perfectly
- Don't include terrain/land cover cache
- Will fetch terrain on first calculation
- Save again to add cache

### Version Detection

```json
{
  "version": "3.1",  // ← Has cache support
  ...
}
```

Old projects without cache:
```json
{
  "version": "3.0",
  ...
  // No terrain_cache or land_cover_cache fields
}
```

## Cache Invalidation

Cache is **permanent** in project files. To refresh:

1. **Delete cache fields** from `.vtr` JSON file
2. **Recalculate** - will fetch fresh API data
3. **Save again** - new cache embedded

Or simply:
1. **New project** from scratch
2. Fresh terrain fetch
3. Save with new cache

## Future Enhancements

- [ ] Cache compression (gzip) for smaller files
- [ ] Selective cache (only calculated points, not full area)
- [ ] Cache versioning (terrain data updates)
- [ ] Cache merging (combine multiple projects)
- [ ] Cache visualization (show what's cached on map)

## Troubleshooting

### Project File Too Large

If > 50 MB:
- Reduce `max_distance` before saving
- Disable land cover cache
- Cache only calculated terrain points (future feature)

### Cache Not Loading

Check console output:
```
Imported 45,234 terrain elevation points from project cache
Imported land cover cache: 234 water, 1523 urban, 89 forest polygons
```

If not shown:
- Check project version (should be 3.1+)
- Verify `terrain_cache` and `land_cover_cache` fields exist in JSON

### Cache Corruption

If project won't load:
1. Open `.vtr` in text editor
2. Remove `"terrain_cache": {...},` line
3. Remove `"land_cover_cache": {...},` line
4. Save and try loading again

## Summary

**Projects are now self-contained!**

- Save once → embed all terrain data
- Load anywhere → instant calculations
- Share easily → fully reproducible results
- Work offline → no API dependency

This makes VetRender projects truly portable and professional-grade.
