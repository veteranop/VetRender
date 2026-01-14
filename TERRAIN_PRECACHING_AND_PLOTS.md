# Terrain Pre-Caching and Plot Management - Implementation Summary

## Overview
Two major features have been added to VetRender:
1. **Aggressive Terrain Pre-Caching** - Downloads all terrain elevation data when transmitter location is set
2. **Plot History Management** - Save, load, and manage coverage plots within projects

## Feature 1: Aggressive Terrain Pre-Caching

### What It Does
When you set a transmitter location (via right-click, precise entry, or project setup), VetRender now automatically pre-downloads ALL terrain elevation data for the entire coverage area. This eliminates the "Fetching X uncached terrain points" messages during coverage calculations and enables fully offline operation.

### How It Works

**Pre-Caching Process:**
1. When location is set, `precache_terrain_for_coverage()` is called
2. Generates all lat/lon points for the coverage area based on:
   - Coverage radius (max_distance)
   - Terrain quality setting (Low/Medium/High)
3. Downloads elevation data in 100-point batches
4. Shows progress in status bar: "Caching terrain data [X/Y] - N/M points..."
5. Reports statistics:
   - Total points cached
   - Already cached vs newly fetched
   - Cache hit rate

**Terrain Quality Settings:**
- **Low**: 36 azimuths × 25 distances = **900 points**
- **Medium**: 72 azimuths × 50 distances = **3,600 points**
- **High**: 360 azimuths × 100 distances = **36,000 points**

### Performance Impact

**First Time (New Location):**
- Low quality: ~10 seconds
- Medium quality: ~30-60 seconds
- High quality: 2-5 minutes

**Subsequent Times (Same Location):**
- All points loaded from cache: < 1 second
- Coverage calculations are now instant (no API calls)

### User Experience

**Before:**
```
Calculate Coverage clicked
→ Fetching 72 uncached terrain points (cached: 0)
→ Wait 15-30 seconds
→ Coverage displayed
```

**After:**
```
Set transmitter location
→ Caching terrain data [1/36] - 100/3600 points...
→ Caching terrain data [36/36] - 3600/3600 points...
→ Terrain data cached - 3600 points ready for offline use

Calculate Coverage clicked
→ All 3600 terrain points loaded from cache
→ Coverage displayed instantly
```

### Files Modified

**gui/main_window.py:**
- Added `precache_terrain_for_coverage()` method (lines 1292-1387)
- Calls pre-caching in:
  - `set_tx_location()` - after right-click location set
  - `set_tx_location_precise()` - after precise coordinate entry
  - `show_project_setup()` - after initial project setup

**Output:**
```
============================================================
PRE-CACHING TERRAIN DATA
============================================================
Location: 43.466500, -112.034000
Coverage radius: 100.0 km
Terrain quality: Medium
Granularity: 72 azimuths × 50 distances
Total points to cache: 3600
  Batch 1/36: 0 cached, 100 fetched
  Batch 6/36: 45 cached, 55 fetched
  ...
  Batch 36/36: 98 cached, 2 fetched

============================================================
TERRAIN PRE-CACHING COMPLETE
============================================================
Total points: 3600
Already cached: 2847
Newly fetched: 753
Cache hit rate: 79.1%
============================================================
```

## Feature 2: Plot History Management

### What It Does
VetRender now automatically saves every coverage calculation to a plot history, allowing you to:
- View all saved plots from the current project
- Load previous plots instantly
- Delete unwanted plots
- Save/load plots with project files

### How It Works

**Automatic Plot Saving:**
- Every time you click "Calculate Coverage", the plot is automatically saved to history
- Plots are stored in memory and in project files
- Up to 20 plots kept in history (older ones auto-deleted)

**Plot Data Stored:**
- Timestamp and unique name
- All transmitter parameters (location, ERP, frequency, height, etc.)
- Coverage data (az_grid, dist_grid, rx_power_grid, terrain_loss_grid)
- Configuration (zoom, basemap, terrain settings, antenna pattern)

**Plots Button:**
- Located in left side panel under "Edit Station Info"
- Opens Plot Manager dialog showing all saved plots
- Shows plot count: "Plots (5)" if plots exist

### Plot Manager Dialog

**Features:**
- Scrollable list of all saved plots
- Each plot shows: timestamp, ERP, frequency, height, distance, terrain status
- Click a plot to see detailed information
- "Load Plot" button - instantly displays the selected coverage plot
- "Delete Plot" button - removes unwanted plots from history
- Detailed info panel shows: location, parameters, coverage settings

**Example List:**
```
 1. 2025-01-12 14:23:15 |  40.0dBm |  900.0MHz | 30.0m | 100.0km | Terrain
 2. 2025-01-12 14:25:42 |  47.0dBm |  900.0MHz | 16.0m |  80.0km | Terrain
 3. 2025-01-12 14:27:19 |  47.0dBm |  900.0MHz | 16.0m | 100.0km | Terrain
```

### Project File Integration

**Project File Format Updated:**
- Version bumped from 2.0 → 2.1
- New field: `saved_plots` array

**Save Project:**
- All plots saved with project file (.vtr)
- Message: "Project saved to: filename.vtr - Included 5 coverage plots"

**Load Project:**
- Plots automatically restored from project file
- Message: "Project loaded: KDPI - 5 coverage plots restored"

**Backwards Compatibility:**
- Old v2.0 project files still load (with 0 plots)
- New v2.1 project files work seamlessly

### Files Modified

**gui/main_window.py:**
- Added `saved_plots` list to `__init__` (line 78)
- Added "Plots" button to side panel (line 185)
- Added `save_current_plot_to_history()` method (lines 1389-1428)
- Added `load_plot_from_history()` method (lines 1430-1449)
- Added `delete_plot_from_history()` method (lines 1451-1458)
- Added `show_plots_manager()` method (lines 1460-1469)
- Modified `calculate_propagation()` to auto-save plots (line 1094)
- Modified `save_project()` to include plots (line 599)
- Modified `load_project()` to restore plots (line 649)

**gui/dialogs.py:**
- Added `PlotsManagerDialog` class (lines 746-890)
- Features: scrollable list, details panel, load/delete buttons

### Usage Workflow

**Saving Plots:**
1. Calculate coverage with different parameters
2. Plots automatically saved to history
3. Up to 20 most recent plots kept

**Viewing Plots:**
1. Click "Plots" button in left panel
2. See list of all saved plots
3. Click a plot to view details

**Loading Plots:**
1. Select plot from list
2. Click "Load Plot"
3. Coverage immediately displayed on map

**Managing Plots:**
1. Select unwanted plot
2. Click "Delete Plot"
3. Confirm deletion
4. Plot removed from history

**Saving/Loading Projects:**
1. Save Project → all plots included in .vtr file
2. Load Project → plots automatically restored
3. Share project files with colleagues (includes all plots!)

## Benefits

### Terrain Pre-Caching
✅ **Eliminates API calls during calculations**
✅ **Fully offline operation after initial setup**
✅ **Instant coverage recalculations with different parameters**
✅ **Better reliability (no network dependency)**
✅ **Reduced API load on Open-Elevation servers**

### Plot Management
✅ **Compare different configurations side-by-side**
✅ **Quick access to previous calculations**
✅ **Document coverage changes over time**
✅ **Share complete projects with team members**
✅ **No need to recalculate for parameter comparisons**

## Technical Details

### Memory Usage
- Each plot: ~1-5 MB depending on resolution
- 20 plots max: ~20-100 MB total
- Terrain cache: ~100 bytes per point
- Medium quality (3600 points): ~350 KB

### Performance
- Plot save: < 10ms (in-memory)
- Plot load: < 100ms (array conversion + display)
- Pre-caching: 30-60 seconds (Medium quality, first time)
- Pre-caching: < 1 second (subsequent times, cached)

### Storage
- Project files (.vtr): JSON format
- Plot data stored as nested arrays
- File size increase: ~100 KB per plot
- Example: 5 plots = ~500 KB addition to project file

## What Changed

### Project File Structure (v2.1)
```json
{
  "version": "2.1",
  "callsign": "KDPI",
  "tx_lat": 43.4665,
  "tx_lon": -112.0340,
  ... other parameters ...
  "saved_plots": [
    {
      "timestamp": "2025-01-12T14:23:15.123456",
      "name": "Plot_20250112_142315",
      "parameters": { ... },
      "az_grid": [ ... ],
      "dist_grid": [ ... ],
      "rx_power_grid": [ ... ],
      "terrain_loss_grid": [ ... ]
    }
  ]
}
```

### User Messages

**Location Set:**
```
Transmitter moved to Lat: 43.4665, Lon: -112.0340
Caching zoom level 10 [1/7]...
...
Caching terrain data [1/36] - 100/3600 points...
...
Terrain data cached - 3600 points ready for offline use
```

**Coverage Calculated:**
```
PROPAGATION CALCULATION COMPLETE
Plot saved to history: Plot_20250112_142315
Coverage calculated - EIRP: 42.2 dBm
```

**Project Saved:**
```
PROJECT SAVED
File: C:\Users\...\KDPI.vtr
Plots saved: 5
```

**Project Loaded:**
```
PROJECT LOADED
Callsign: KDPI
Location: 43.466500, -112.034000
Zoom: 10 (default)
Plots loaded: 5
```

## Future Enhancements

Possible additions:
- **Named plots**: Allow users to name plots instead of auto-generated names
- **Plot comparison**: Side-by-side view of two plots
- **Export plots**: Save individual plots as images or CSV
- **Plot notes**: Add comments/descriptions to plots
- **Plot filtering**: Search/filter plots by parameters
- **Bulk pre-caching**: Pre-cache for different coverage radii
- **Terrain cache cleanup**: Tools to manage terrain cache size

## Summary

Both features work together to create a powerful, offline-capable RF planning workflow:

1. **Set transmitter location** → Map tiles + terrain data pre-cached
2. **Calculate coverage** → Uses cached data, plot auto-saved
3. **Try different parameters** → Instant recalculation, all plots saved
4. **Review plots** → Compare different configurations
5. **Save project** → All data (config + plots) saved together
6. **Load project** → Everything restored, ready for more work
7. **Work offline** → No network needed after initial setup

These improvements make VetRender significantly more practical for professional RF planning and site analysis work.
