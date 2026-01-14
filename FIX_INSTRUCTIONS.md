# VetRender Propagation Fix - Eliminates Radial Artifacts

## Problem Diagnosis

Looking at your latest plot (Plot_20260112_164638.jpg), the issues were:

1. **Blocky, pixelated coverage** with obvious radial lines extending from transmitter
2. **Sparse coverage** - mostly green blocks scattered around
3. **Clear radial artifacts** - blue lines extending outward
4. **Coverage looks unrealistic** - not smooth or continuous

## Root Causes

### 1. **Polar vs. Cartesian Coordinate Mismatch**
   - Original code calculated propagation in POLAR coordinates (azimuth/distance)
   - But displayed results in CARTESIAN coordinates (x/y pixels)
   - Matplotlib's contourf() function interpolates between data points
   - When you give it polar data and ask it to draw Cartesian contours, it creates radial artifacts!

### 2. **Resolution Mismatch**
   - Grid resolution: 500x500 points
   - Terrain sampling: only 72 azimuths × 50 distances = 3,600 points
   - Sparse terrain data being interpolated across 250,000 grid points
   - Creates blocky, discontinuous coverage patterns

### 3. **contourf() with Polar Data**
   - contourf() tries to create smooth contours by connecting points
   - With polar data, it connects points radially, creating spoke patterns
   - This is the direct cause of those blue radial lines you're seeing

## The Fix

### Key Changes:

1. **Cartesian Grid Creation** (calculate_propagation_FIXED.py):
   ```python
   # OLD (polar):
   azimuths = np.linspace(0, 360, self.resolution)
   distances = np.linspace(0.1, self.max_distance, self.resolution)
   az_grid, dist_grid = np.meshgrid(azimuths, distances)
   
   # NEW (Cartesian):
   x_km = np.linspace(-self.max_distance, self.max_distance, self.resolution)
   y_km = np.linspace(-self.max_distance, self.max_distance, self.resolution)
   x_grid, y_grid = np.meshgrid(x_km, y_km)
   
   # Then calculate polar FROM Cartesian:
   dist_grid = np.sqrt(x_grid**2 + y_grid**2)
   az_grid = np.degrees(np.arctan2(x_grid, y_grid)) % 360
   ```

2. **Circular Masking**:
   ```python
   # Mask points outside max distance (creates circular coverage)
   mask = dist_grid > self.max_distance
   ```

3. **Use pcolormesh Instead of contourf** (plot_propagation_FIXED.py):
   ```python
   # OLD:
   contour = self.ax.contourf(x, y, rx_power_masked, levels=levels, ...)
   
   # NEW:
   contour = self.ax.pcolormesh(x_pixels, y_pixels, rx_power_masked,
                                shading='gouraud',  # Smooth interpolation
                                cmap=cmap, alpha=0.65)
   ```
   
   **Why this matters:**
   - `contourf()` creates contour lines and tries to interpolate smoothly between them
   - With polar data, this creates radial artifacts
   - `pcolormesh()` with `shading='gouraud'` renders each grid cell directly
   - Creates smooth gradients WITHOUT radial artifacts

## Installation Instructions

1. **Backup your current file**:
   ```
   copy gui\main_window.py gui\main_window_backup.py
   ```

2. **Replace calculate_propagation function**:
   - Open `gui\main_window.py`
   - Find the `def calculate_propagation(self):` function (around line 943)
   - Replace the ENTIRE function with the code from `calculate_propagation_FIXED.py`

3. **Replace plot function**:
   - Find the `def plot_propagation_on_map(self, az_grid, dist_grid, rx_power_grid, terrain_loss_grid=None):` function
   - RENAME it to `plot_propagation_on_map_OLD` (keep as backup)
   - Add the NEW function from `plot_propagation_FIXED.py`
   - Name it `plot_propagation_on_map_cartesian`

4. **Update function signature in other places**:
   - The new function is called `plot_propagation_on_map_cartesian` with different parameters
   - It's already called correctly in the fixed calculate_propagation function
   
5. **Update probe_signal function** (if you use it):
   - The `last_propagation` tuple now has 4 elements instead of 3:
     ```python
     # OLD:
     self.last_propagation = (az_grid, dist_grid, rx_power_grid)
     
     # NEW:
     self.last_propagation = (x_grid, y_grid, rx_power_grid, mask)
     ```
   - Update probe_signal accordingly (or just disable it temporarily)

## Expected Results

After applying these fixes, you should see:

✅ **Smooth, continuous coverage patterns**
✅ **No radial lines or artifacts**
✅ **Proper circular coverage area**
✅ **Realistic signal gradations**
✅ **Clean color transitions**

## Testing

1. Run the application
2. Click "Calculate Coverage"
3. You should now see a smooth, circular coverage pattern without any radial lines
4. The coverage should look like smooth color gradients, not blocky patches

## If You Still See Issues

If you still see radial artifacts after this fix:
- Make sure BOTH functions were replaced
- Check that you're using pcolormesh, not contourf
- Verify the grid is created in Cartesian (x_km, y_km), not polar
- Check the log output to confirm "CARTESIAN grid" is being used

## Technical Notes

The fundamental issue was trying to visualize polar data (azimuth/distance) in a Cartesian display space (x/y pixels). By:
1. Creating the grid in Cartesian space FIRST
2. Then calculating polar values (distance/azimuth) for propagation calculations
3. Then displaying the results using pcolormesh which respects the Cartesian grid

We eliminate the coordinate system mismatch that was causing the artifacts.
