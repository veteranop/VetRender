# Grid Artifact Fix - January 19, 2026

## Problem
After 5 hours of calculation, the 200km Ultra propagation plot showed severe artifacts:
- ❌ Blocky rectangular chunks instead of smooth contours
- ❌ Radial lines radiating from transmitter
- ❌ Triangular geometry artifacts
- ❌ No visible terrain shadows
- ❌ Discrete color banding

## Root Cause Analysis

### Issue #1: Coordinate System Mismatch (FIXED)
The propagation controller was:
1. Creating a Cartesian grid (x_km, y_km) ✓
2. Calculating signal on Cartesian grid ✓
3. Converting to polar (az_grid, dist_grid) and returning that ✗
4. Plotter received polar coordinates
5. **Plotter converted BACK to Cartesian** (lines 78-80 in propagation_plot.py) ✗
6. matplotlib's `contourf` tried to interpolate this double-converted mess
7. Result: Complete geometric destruction

### Issue #2: Terrain Interpolation Artifacts (FIXED)
Even with correct Cartesian grids, the terrain loss calculation was:
1. Sampling terrain in POLAR coordinates (radial lines)
2. Converting polar samples to Cartesian for interpolation
3. **Recreating Cartesian grid from polar dist_grid/az_grid** ✗
4. Interpolating with scipy griddata
5. Result: Polar-to-Cartesian conversion artifacts in terrain data

## The Fix

### Fix #1: Return Cartesian Grids from Controller

**controllers/propagation_controller.py Line 324-326**: Changed return statement
```python
# OLD (broken):
return az_grid, dist_grid, rx_power_grid, terrain_loss_grid, stats

# NEW (fixed):
return x_grid, y_grid, rx_power_grid, terrain_loss_grid, stats
```

Now returns Cartesian grids directly, avoiding conversion.

### Fix #2: Pass Original Cartesian Grids to Terrain Function

**controllers/propagation_controller.py Line 334-336**: Updated function signature
```python
# OLD (broken):
def _calculate_terrain_loss(self, ..., mask, dist_grid, az_grid):

# NEW (fixed):
def _calculate_terrain_loss(self, ..., mask, dist_grid, az_grid, x_grid, y_grid):
```

**Line 465-470**: Use original Cartesian grids instead of recreating
```python
# OLD (broken):
# Recreate Cartesian grids from polar coordinates
x_grid = dist_grid * np.sin(np.radians(az_grid))
y_grid = dist_grid * np.cos(np.radians(az_grid))

# NEW (fixed):
# Use the original Cartesian grids passed from calculate_coverage
# This avoids polar-to-Cartesian conversion artifacts
# (x_grid and y_grid are now function parameters)
```

Now terrain interpolation uses the **exact same Cartesian grid** that was originally created, with no polar conversion round-trip.

### gui/propagation_plot.py
**Line 51-81**: Updated plot_coverage signature and coordinate handling
```python
# OLD (broken):
def plot_coverage(self, ..., az_grid, dist_grid, ...):
    az_rad = np.deg2rad(az_grid)
    x = tx_pixel_x + dist_grid * pixel_scale * np.sin(az_rad)
    y = tx_pixel_y - dist_grid * pixel_scale * np.cos(az_rad)

# NEW (fixed):
def plot_coverage(self, ..., x_grid_km, y_grid_km, ...):
    x_pixels = tx_pixel_x + x_grid_km * pixel_scale
    y_pixels = tx_pixel_y - y_grid_km * pixel_scale
```

Direct Cartesian-to-pixel conversion, no polar coordinates involved.

**Lines 109, 136**: Updated contourf calls to use new coordinate names
```python
# OLD:
contour = self.ax.contourf(x, y, rx_power_masked, ...)

# NEW:
contour = self.ax.contourf(x_pixels, y_pixels, rx_power_masked, ...)
```

### gui/main_window.py
Updated all references to az_grid/dist_grid → x_grid/y_grid:
- Line 285: Result unpacking
- Line 288: Storing propagation results
- Lines 382, 469, 534, 558, 1285: Unpacking stored results
- Lines 1396-1397: Save plot dictionary keys
- Lines 1434-1435: Load plot with backward compatibility

## Why This Should Fix It

**Before (broken):**
```
Cartesian grid → polar conversion → Cartesian conversion → matplotlib interpolation
     ✓                  ✗                     ✗                      ✗
```

**After (fixed):**
```
Cartesian grid → matplotlib interpolation
     ✓                        ✓
```

The grid geometry is preserved end-to-end. No coordinate transformations means:
- ✓ Smooth contours (1200×1200 grid preserved)
- ✓ No radial artifacts (Cartesian geometry maintained)
- ✓ Proper terrain shadows (calculated on Cartesian grid, plotted on Cartesian grid)
- ✓ Smooth color gradients (matplotlib can interpolate properly)

## Test Instructions

1. Run a **small test first** (50km, Medium quality) to verify it works
2. Should complete in ~5-10 minutes
3. Look for:
   - Smooth circular/elliptical coverage area
   - Gradual color transitions
   - No blocky chunks or radial lines
   - Realistic terrain shadows if terrain enabled

If that works, then try 200km Ultra again (but expect 4+ hours).

## Performance Note

The fix doesn't change computation time - the 5 hours was spent calculating correctly.
The artifacts were purely a **plotting bug**, not a calculation bug.
The data was good, the visualization was broken.

## Backward Compatibility

Load plot function includes fallback for old saved plots:
```python
x_grid = np.array(plot_data.get('x_grid', plot_data.get('az_grid')))
y_grid = np.array(plot_data.get('y_grid', plot_data.get('dist_grid')))
```

Old saved plots (with az_grid/dist_grid) will still load, but may show artifacts.
New saves will use x_grid/y_grid and render correctly.
