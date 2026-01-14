"""
TRANSPARENCY SLIDER INTEGRATION PATCH
======================================

This script shows exactly what needs to be added to main_window.py
to wire up the transparency slider.

CHANGES NEEDED:
===============

1. ADD to get_toolbar_callbacks() method (around line 219):

   'on_transparency_change': self.on_transparency_change,

2. ADD new method after on_quality_change() (around line 478):

   def on_transparency_change(self):
       \"\"\"Handle transparency slider change - redraw overlay with new alpha\"\"\"
       if self.last_propagation is not None and self.show_coverage.get():
           az_grid, dist_grid, rx_power_grid = self.last_propagation
           tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
               self.tx_lat, self.tx_lon
           )
           alpha = self.toolbar.get_transparency()
           self.propagation_plot.plot_coverage(
               self.map_display.map_image, tx_pixel_x, tx_pixel_y,
               az_grid, dist_grid, rx_power_grid, self.signal_threshold,
               self.map_display.get_pixel_scale(),
               self.last_terrain_loss, self.show_shadow.get(),
               (self.map_display.plot_xlim, self.map_display.plot_ylim),
               alpha=alpha
           )

3. UPDATE ALL plot_coverage() calls to include alpha parameter:

   Find these locations and add ", alpha=self.toolbar.get_transparency()" at end:
   
   - Line ~276 (calculate_propagation)
   - Line ~540 (toggle_coverage_overlay)  
   - Line ~558 (update_shadow_display)
   - Line ~730 (reload_map)

   Example:
   BEFORE:
   self.propagation_plot.plot_coverage(
       self.map_display.map_image, tx_pixel_x, tx_pixel_y,
       az_grid, dist_grid, rx_power_grid, self.signal_threshold,
       self.map_display.get_pixel_scale(),
       self.last_terrain_loss, self.show_shadow.get(),
       (self.map_display.plot_xlim, self.map_display.plot_ylim)
   )
   
   AFTER:
   self.propagation_plot.plot_coverage(
       self.map_display.map_image, tx_pixel_x, tx_pixel_y,
       az_grid, dist_grid, rx_power_grid, self.signal_threshold,
       self.map_display.get_pixel_scale(),
       self.last_terrain_loss, self.show_shadow.get(),
       (self.map_display.plot_xlim, self.map_display.plot_ylim),
       alpha=self.toolbar.get_transparency()
   )

DEPLOYMENT:
===========

1. Backup current toolbar.py:
   cp gui/toolbar.py gui/toolbar.py.BACKUP_PRE_TRANSPARENCY

2. Replace with enhanced version:
   cp gui/toolbar_ENHANCED.py gui/toolbar.py

3. Apply changes to main_window.py (listed above)

4. Launch and test!

TESTING:
========

1. Launch VetRender
2. Calculate coverage  
3. Move the "Overlay" slider left (more transparent) and right (less transparent)
4. Coverage overlay should fade in/out smoothly!
5. Try changing basemaps - overlay should stay with new transparency!

"""

print(__doc__)
