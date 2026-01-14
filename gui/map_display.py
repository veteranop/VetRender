"""
Map Display Module
==================
Handles all map rendering, zooming, marker placement, and coordinate conversions.

This module encapsulates all the complex map display logic that was previously
scattered throughout main_window.py, making it much easier to maintain and test.
"""

import numpy as np
from models.map_handler import MapHandler


class MapDisplay:
    """Manages map display, zoom, and coordinate transformations"""
    
    def __init__(self, ax, canvas):
        """Initialize map display
        
        Args:
            ax: Matplotlib axis for rendering
            canvas: Matplotlib canvas for drawing
        """
        self.ax = ax
        self.canvas = canvas
        
        # Map state
        self.map_image = None
        self.map_zoom = 13
        self.map_xtile = 0
        self.map_ytile = 0
        self.map_center_lat = None
        self.map_center_lon = None
        
        # Zoom state for preserving overlays
        self.plot_xlim = None
        self.plot_ylim = None
        
    def load_map(self, lat, lon, zoom, basemap, cache):
        """Load and cache map tiles
        
        Args:
            lat: Center latitude
            lon: Center longitude
            zoom: Zoom level (10-16)
            basemap: Basemap style name
            cache: MapCache instance
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use 5x5 tile grid for bigger maps (prevents white edges when zooming out)
            self.map_image, self.map_zoom, self.map_xtile, self.map_ytile = MapHandler.get_map_tile(
                lat, lon, zoom, tile_size=5, basemap=basemap, cache=cache
            )
            
            if self.map_image:
                # Store actual center coordinates (center of middle tile)
                self.map_center_lat, self.map_center_lon = MapHandler.num2deg(
                    self.map_xtile + 0.5, self.map_ytile + 0.5, self.map_zoom
                )
                
                print(f"Map loaded: {self.map_image.size[0]}x{self.map_image.size[1]} pixels at zoom {zoom}")
                return True
            else:
                print("ERROR: Failed to load map image")
                return False
                
        except Exception as e:
            print(f"ERROR loading map: {e}")
            return False
    
    def display_map_only(self, tx_lat, tx_lon, show_marker=True):
        """Display map with optional transmitter marker
        
        Args:
            tx_lat: Transmitter latitude
            tx_lon: Transmitter longitude
            show_marker: Whether to show transmitter marker
        """
        self.ax.clear()
        
        if self.map_image:
            self.ax.imshow(self.map_image)
            self.ax.axis('off')
            
            if show_marker:
                tx_pixel_x, tx_pixel_y = self.get_tx_pixel_position(tx_lat, tx_lon)
                
                if tx_pixel_x is not None:
                    self.ax.plot(tx_pixel_x, tx_pixel_y, 'r^', markersize=20, 
                                label='Transmitter',
                                markeredgecolor='white', markeredgewidth=2)
                    self.ax.legend(loc='upper right', fontsize=12)
            
        self.canvas.draw()
    
    def get_tx_pixel_position(self, tx_lat, tx_lon):
        """Calculate exact pixel position of transmitter on map
        
        Args:
            tx_lat: Transmitter latitude
            tx_lon: Transmitter longitude
            
        Returns:
            Tuple of (tx_pixel_x, tx_pixel_y) or (None, None) if map not loaded
        """
        if not self.map_image or self.map_center_lat is None:
            return None, None
        
        # Get exact fractional tile positions
        lat_rad_tx = np.radians(tx_lat)
        lat_rad_center = np.radians(self.map_center_lat)
        n = 2.0 ** self.map_zoom
        
        tx_xtile_exact = (tx_lon + 180.0) / 360.0 * n
        tx_ytile_exact = (1.0 - np.log(np.tan(lat_rad_tx) + (1 / np.cos(lat_rad_tx))) / np.pi) / 2.0 * n
        
        center_xtile_exact = (self.map_center_lon + 180.0) / 360.0 * n
        center_ytile_exact = (1.0 - np.log(np.tan(lat_rad_center) + (1 / np.cos(lat_rad_center))) / np.pi) / 2.0 * n
        
        # Calculate pixel offset
        tile_size = 256
        img_size = self.map_image.size[0]
        
        tile_offset_x = tx_xtile_exact - center_xtile_exact
        tile_offset_y = tx_ytile_exact - center_ytile_exact
        
        pixel_offset_x = tile_offset_x * tile_size
        pixel_offset_y = tile_offset_y * tile_size
        
        # Transmitter pixel position
        img_center = img_size // 2
        tx_pixel_x = img_center + pixel_offset_x
        tx_pixel_y = img_center + pixel_offset_y
        
        return tx_pixel_x, tx_pixel_y
    
    def pixel_to_latlon(self, pixel_x, pixel_y):
        """Convert pixel coordinates to lat/lon
        
        Args:
            pixel_x: X pixel coordinate
            pixel_y: Y pixel coordinate
            
        Returns:
            Tuple of (lat, lon) or (None, None) if map not loaded
        """
        if not self.map_image or self.map_center_lat is None:
            return None, None
        
        img_size = self.map_image.size[0]
        
        lat, lon = MapHandler.pixel_to_latlon(
            pixel_x, pixel_y,
            self.map_center_lat, self.map_center_lon,
            self.map_zoom, img_size
        )
        
        return lat, lon
    
    def handle_scroll_zoom(self, event):
        """Handle scroll wheel zoom events
        
        Args:
            event: Matplotlib scroll event
            
        Returns:
            bool: True if zoom was applied, False otherwise
        """
        if event.inaxes != self.ax or not self.map_image:
            return False
        
        # Get current limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        # Zoom factor
        zoom_factor = 0.8 if event.button == 'up' else 1.25
        
        # Get mouse position for zoom center
        xdata, ydata = event.xdata, event.ydata
        
        # Calculate new size
        new_width = (xlim[1] - xlim[0]) * zoom_factor
        new_height = (ylim[1] - ylim[0]) * zoom_factor
        
        # Keep mouse position fixed (relative position stays the same)
        rel_x = (xdata - xlim[0]) / (xlim[1] - xlim[0])
        rel_y = (ydata - ylim[0]) / (ylim[1] - ylim[0])
        
        new_xlim = [xdata - new_width * rel_x, xdata + new_width * (1 - rel_x)]
        new_ylim = [ydata - new_height * rel_y, ydata + new_height * (1 - rel_y)]
        
        # Clamp to image bounds
        img_w, img_h = self.map_image.size
        new_xlim = [max(0, new_xlim[0]), min(img_w, new_xlim[1])]
        new_ylim = [max(0, new_ylim[0]), min(img_h, new_ylim[1])]
        
        # Ensure valid range
        if new_xlim[1] <= new_xlim[0]:
            new_xlim = (0, img_w)
        if new_ylim[1] <= new_ylim[0]:
            new_ylim = (img_h, 0)
        
        # Apply zoom
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)
        
        # Store for overlay preservation
        self.plot_xlim = new_xlim
        self.plot_ylim = new_ylim
        
        self.canvas.draw()
        
        print(f"View zoom: factor {zoom_factor:.2f}, limits x={new_xlim}, y={new_ylim}")
        return True
    
    def reset_zoom(self):
        """Reset zoom to full map view"""
        if self.map_image:
            self.ax.set_xlim(0, self.map_image.size[0])
            self.ax.set_ylim(self.map_image.size[1], 0)
            self.plot_xlim = None
            self.plot_ylim = None
            self.canvas.draw()
    
    def restore_zoom_state(self):
        """Restore previously saved zoom state"""
        if self.plot_xlim and self.plot_ylim:
            self.ax.set_xlim(self.plot_xlim)
            self.ax.set_ylim(self.plot_ylim)
        else:
            self.reset_zoom()
    
    def get_pixel_scale(self):
        """Get pixels per km at current zoom level
        
        Returns:
            float: Pixels per kilometer
        """
        return 30 * (2 ** (self.map_zoom - 13))
