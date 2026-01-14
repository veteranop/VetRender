# VetRender Updates

## Changes Made

### 1. Interactive Zoom on Map (Without Losing Plot)
- Added scroll wheel zoom capability to the main map view
- Zoom state is preserved when recalculating coverage
- Coverage overlay remains visible and correctly positioned during zoom
- Zoom is centered on mouse cursor position
- Implementation: `on_scroll_zoom()` method in `main_window.py`

### 2. Improved Interpolation (Removed Radial Artifacts)
- Replaced Gaussian-weighted radial spreading with proper 2D spline interpolation
- Uses `scipy.interpolate.RectBivariateSpline` for smooth terrain loss interpolation
- Fallback to numpy-based bilinear interpolation if scipy not available
- Handles azimuth wraparound (0° = 360°) correctly for seamless coverage
- Removed old kernel-based smoothing that was creating artifacts
- Result: Much smoother coverage plots without visible radial lines

### 3. Configurable Minimum Signal Level
- Added "Min Signal Level (dBm)" field to transmitter config dialog
- Default: -110 dBm
- Areas below this threshold are shown as "no coverage" (masked in plot)
- User can adjust to see where coverage meets their specific requirements
- Configuration saved and applied to all coverage calculations

### 4. Reset Location Button
- Added "Reset Location..." button to main toolbar
- Opens the project setup dialog to select a new area
- Clears previous coverage data and zoom state
- Downloads and caches new map tiles for the selected area
- Useful for quickly moving to a completely different location

### 5. Fixed Transmitter Location Accuracy
- **CRITICAL FIX**: Corrected coordinate conversion in `pixel_to_latlon()`
- Previous bug: Used integer tile numbers causing systematic offset errors
- New implementation: Uses exact fractional tile positions for accurate conversion
- Transmitter now appears at the EXACT coordinates entered
- Example: 43.661474, -114.403802 now places correctly without shifting

## Technical Details

### Dependencies
- **New optional dependency**: `scipy` (for best interpolation quality)
- If scipy not installed, code automatically falls back to numpy-based interpolation
- To install scipy: `pip install scipy`

### Files Modified
1. `gui/main_window.py` - Main application logic
   - Added zoom event handling
   - Improved terrain interpolation algorithm
   - Added reset location functionality
   - Updated config dialog to include min signal level

2. `gui/dialogs.py` - Dialog windows
   - Extended TransmitterConfigDialog with min_signal parameter
   - Now returns 4 values: (erp, freq, height, min_signal)

3. `models/map_handler.py` - Coordinate conversions
   - Fixed `pixel_to_latlon()` to use exact fractional tile positions
   - Added detailed comments explaining the fix

## Usage Notes

### Zoom Controls
- **Scroll up**: Zoom in (centered on mouse)
- **Scroll down**: Zoom out (centered on mouse)
- Zoom state persists when recalculating coverage
- To reset zoom: Click "Refresh Map" or "Reset Location"

### Minimum Signal Level
- Right-click → "Edit Transmitter Configuration"
- Adjust "Min Signal Level (dBm)" to your threshold
- Lower values (e.g., -120 dBm) show more coverage area
- Higher values (e.g., -90 dBm) show only strong signal areas
- Useful for regulatory compliance or service quality requirements

### Interpolation Quality
- With scipy installed: Smooth cubic spline interpolation (best quality)
- Without scipy: Bilinear interpolation (good quality, slight performance boost)
- Both methods eliminate radial artifacts from previous version

### Location Accuracy
- Transmitter marker now shows EXACT input coordinates
- No more mysterious shifting when zooming or reloading
- Critical for regulatory compliance and field work

## Testing Recommendations

1. **Test coordinate accuracy**:
   - Enter your known coordinates (e.g., 43.661474, -114.403802)
   - Verify transmitter marker is at correct location on map
   - Compare with external mapping tool (Google Maps, etc.)

2. **Test zoom functionality**:
   - Calculate coverage
   - Zoom in/out with scroll wheel
   - Verify coverage overlay stays aligned with map

3. **Test interpolation quality**:
   - Calculate with terrain enabled (Medium or High quality)
   - Look for smooth gradients in coverage plot
   - Should see NO visible radial lines

4. **Test min signal threshold**:
   - Try different values (-90, -100, -110, -120 dBm)
   - Verify coverage area changes appropriately
   - Lower threshold = larger coverage area

## Known Limitations

- Interpolation quality depends on terrain sample density
- Very low terrain quality settings may still show some artifacts
- Recommend Medium or High quality for best visual results
- Ultra quality provides minimal visual improvement vs. High
