"""
Dialog windows for VetRender GUI
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np

class TransmitterConfigDialog:
    """Dialog for editing transmitter configuration"""
    def __init__(self, parent, erp, freq, height):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Transmitter Configuration")
        self.dialog.geometry("350x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        ttk.Label(self.dialog, text="ERP (dBm):").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.erp_var = tk.StringVar(value=str(erp))
        ttk.Entry(self.dialog, textvariable=self.erp_var, width=20).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(self.dialog, text="Frequency (MHz):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.freq_var = tk.StringVar(value=str(freq))
        ttk.Entry(self.dialog, textvariable=self.freq_var, width=20).grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Label(self.dialog, text="Antenna Height (m):").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.height_var = tk.StringVar(value=str(height))
        ttk.Entry(self.dialog, textvariable=self.height_var, width=20).grid(row=2, column=1, padx=10, pady=10)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def ok(self):
        try:
            erp = float(self.erp_var.get())
            freq = float(self.freq_var.get())
            height = float(self.height_var.get())
            self.result = (erp, freq, height)
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")
    
    def cancel(self):
        self.dialog.destroy()


class AntennaInfoDialog:
    """Dialog for editing antenna information"""
    def __init__(self, parent, pattern_name):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Antenna Information")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        ttk.Label(self.dialog, text="Current Antenna Pattern:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        ttk.Label(self.dialog, text=pattern_name, font=('Arial', 10, 'bold')).grid(row=0, column=1, padx=10, pady=10, sticky=tk.W)
        
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=1, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Load New Pattern (XML)", command=self.load_pattern).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Reset to Omni", command=self.reset_omni).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.close).pack(side=tk.LEFT, padx=5)
        
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
    def load_pattern(self):
        filepath = filedialog.askopenfilename(
            title="Select Antenna Pattern XML",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filepath:
            self.result = ('load', filepath)
            self.dialog.destroy()
    
    def reset_omni(self):
        self.result = ('reset', None)
        self.dialog.destroy()
    
    def close(self):
        self.dialog.destroy()


class CacheManagerDialog:
    """Dialog for managing map and terrain cache"""
    def __init__(self, parent, cache):
        self.cache = cache
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Cache Manager")
        self.dialog.geometry("500x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Stats frame
        stats_frame = ttk.LabelFrame(self.dialog, text="Cache Statistics", padding="10")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.stats_text = tk.Text(stats_frame, height=8, width=50, state='disabled')
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        self.update_stats()
        
        # Buttons frame
        btn_frame = ttk.Frame(self.dialog, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Refresh Stats", command=self.update_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Tile Cache", command=self.clear_tiles).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear Terrain Cache", command=self.clear_terrain).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear All", command=self.clear_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def update_stats(self):
        """Update cache statistics display"""
        stats = self.cache.get_cache_stats()
        
        self.stats_text.config(state='normal')
        self.stats_text.delete('1.0', tk.END)
        self.stats_text.insert('1.0', 
            f"Cache Location: {self.cache.cache_dir}\n\n"
            f"Map Tiles Cached: {stats['tiles']:,}\n"
            f"Terrain Files Cached: {stats['terrain']:,}\n"
            f"Total Cache Size: {stats['size_mb']} MB\n\n"
            f"Benefits:\n"
            f"  • Map tiles load instantly from cache\n"
            f"  • Terrain data loads in <1 second vs 3-5 minutes\n"
            f"  • Works offline after initial download\n"
        )
        self.stats_text.config(state='disabled')
    
    def clear_tiles(self):
        """Clear tile cache"""
        if messagebox.askyesno("Confirm", "Clear all cached map tiles?"):
            self.cache.clear_cache(clear_tiles=True, clear_terrain=False)
            self.update_stats()
            messagebox.showinfo("Success", "Tile cache cleared")
    
    def clear_terrain(self):
        """Clear terrain cache"""
        if messagebox.askyesno("Confirm", "Clear all cached terrain data?"):
            self.cache.clear_cache(clear_tiles=False, clear_terrain=True)
            self.update_stats()
            messagebox.showinfo("Success", "Terrain cache cleared")
    
    def clear_all(self):
        """Clear all cache"""
        if messagebox.askyesno("Confirm", "Clear ALL cached data (maps and terrain)?"):
            self.cache.clear_cache(clear_tiles=True, clear_terrain=True)
            self.update_stats()
            messagebox.showinfo("Success", "All cache cleared")


class ProjectSetupDialog:
    """Initial dialog to set up project location and download map area"""
    def __init__(self, parent):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("VetRender - Project Setup")
        self.dialog.geometry("900x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make it modal
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Import here to avoid circular imports
        from models.map_handler import MapHandler
        from models.map_cache import MapCache
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        from PIL import Image
        
        self.MapHandler = MapHandler
        self.cache = MapCache()
        self.current_map = None
        self.current_zoom = 13
        self.current_lat = 43.4665
        self.current_lon = -112.0340
        self.current_basemap = 'Esri WorldImagery'
        
        # Title
        title_frame = ttk.Frame(self.dialog, padding="10")
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text="VetRender - Select Coverage Area", font=('Arial', 16, 'bold')).pack()
        ttk.Label(title_frame, text="Navigate the map and download your area for offline propagation modeling", font=('Arial', 10)).pack()
        
        # Main content with map on left, controls on right
        content_frame = ttk.Frame(self.dialog)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: Map viewer
        map_frame = ttk.LabelFrame(content_frame, text="Map Viewer - Click and drag to explore", padding="5")
        map_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(7, 7), dpi=80)
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Bind mouse events for panning
        self.drag_start = None
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_drag)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)
        
        # Right: Controls
        control_frame = ttk.Frame(content_frame, padding="5")
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Location input
        location_frame = ttk.LabelFrame(control_frame, text="Location", padding="10")
        location_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(location_frame, text="Latitude:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.lat_var = tk.StringVar(value="43.4665")
        ttk.Entry(location_frame, textvariable=self.lat_var, width=15).grid(row=0, column=1, pady=2)
        
        ttk.Label(location_frame, text="Longitude:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.lon_var = tk.StringVar(value="-112.0340")
        ttk.Entry(location_frame, textvariable=self.lon_var, width=15).grid(row=1, column=1, pady=2)
        
        ttk.Button(location_frame, text="Go To Location", command=self.go_to_location).grid(row=2, column=0, columnspan=2, pady=5)
        
        # Zoom controls
        zoom_frame = ttk.LabelFrame(control_frame, text="Zoom Level", padding="10")
        zoom_frame.pack(fill=tk.X, pady=5)
        
        self.zoom_var = tk.StringVar(value="13")
        for i, (zoom, desc) in enumerate([
            ('10', '~300 km'),
            ('11', '~150 km'),
            ('12', '~75 km'),
            ('13', '~40 km'),
            ('14', '~20 km'),
            ('15', '~10 km'),
            ('16', '~5 km')
        ]):
            ttk.Radiobutton(zoom_frame, text=f"Zoom {zoom} ({desc})", 
                          variable=self.zoom_var, value=zoom,
                          command=self.update_map).grid(row=i, column=0, sticky=tk.W)
        
        # Basemap
        basemap_frame = ttk.LabelFrame(control_frame, text="Basemap Style", padding="10")
        basemap_frame.pack(fill=tk.X, pady=5)
        
        self.basemap_var = tk.StringVar(value="Esri WorldImagery")
        basemap_combo = ttk.Combobox(basemap_frame, textvariable=self.basemap_var, width=18,
                                     values=list(MapHandler.BASEMAPS.keys()), state='readonly')
        basemap_combo.pack(fill=tk.X)
        basemap_combo.bind('<<ComboboxSelected>>', lambda e: self.update_map())
        
        # Coverage radius
        radius_frame = ttk.LabelFrame(control_frame, text="Max Coverage Distance", padding="10")
        radius_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(radius_frame, text="Radius (km):").pack()
        self.radius_var = tk.StringVar(value="50")
        ttk.Entry(radius_frame, textvariable=self.radius_var, width=15).pack()
        
        # Instructions
        inst_frame = ttk.LabelFrame(control_frame, text="Instructions", padding="10")
        inst_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        instructions = tk.Text(inst_frame, height=8, width=30, wrap=tk.WORD, font=('Arial', 9))
        instructions.pack(fill=tk.BOTH, expand=True)
        instructions.insert('1.0',
            "• Enter coordinates or drag map\n"
            "• Scroll wheel to zoom in/out\n"
            "• Choose zoom level for detail\n"
            "• Select basemap style\n"
            "• Set coverage radius\n"
            "• Click 'Set This Area' when ready\n"
            "• Then click 'Download & Continue'\n\n"
            "The map area will be cached for fast offline use!"
        )
        instructions.config(state='disabled')
        
        # Bottom buttons
        btn_frame = ttk.Frame(self.dialog, padding="10")
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        ttk.Button(btn_frame, text="← Set This Area", 
                  command=self.set_area).pack(side=tk.LEFT, padx=5)
        
        self.download_btn = ttk.Button(btn_frame, text="✓ Download & Continue", 
                                       command=self.download_and_create, 
                                       state='disabled')
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=5)
        
        self.status_label = ttk.Label(btn_frame, text="Explore map, then click 'Set This Area'")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Track if area has been set
        self.area_set = False
        
        # Load initial map
        self.update_map()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def on_mouse_press(self, event):
        """Start dragging"""
        if event.inaxes and event.button == 1:
            self.drag_start = (event.xdata, event.ydata)
    
    def on_mouse_drag(self, event):
        """Pan the map"""
        if self.drag_start and event.inaxes and self.current_map:
            dx = event.xdata - self.drag_start[0]
            dy = event.ydata - self.drag_start[1]
            
            # Update view limits
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            self.ax.set_xlim(xlim[0] - dx, xlim[1] - dx)
            self.ax.set_ylim(ylim[0] - dy, ylim[1] - dy)
            self.canvas.draw()
    
    def on_mouse_release(self, event):
        """Stop dragging and update map center"""
        if self.drag_start and self.current_map:
            # Calculate how much we've panned in pixels
            img_size = self.current_map.size[0]
            
            # Get current axis limits to see how much we panned
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()
            
            # Calculate the new center (middle of visible area)
            center_x = (xlim[0] + xlim[1]) / 2
            center_y = (ylim[0] + ylim[1]) / 2
            
            # Convert pixel offset to lat/lon offset
            pixel_offset_x = center_x - (img_size / 2)
            pixel_offset_y = center_y - (img_size / 2)
            
            # Approximate conversion: at zoom level, each pixel is roughly this many degrees
            # This is a rough approximation that works reasonably well
            degrees_per_pixel = 360 / (256 * (2 ** self.current_zoom))
            
            lat_offset = -pixel_offset_y * degrees_per_pixel / np.cos(np.radians(self.current_lat))
            lon_offset = pixel_offset_x * degrees_per_pixel
            
            # Update center location
            self.current_lat += lat_offset
            self.current_lon += lon_offset
            
            # Update UI
            self.lat_var.set(f"{self.current_lat:.4f}")
            self.lon_var.set(f"{self.current_lon:.4f}")
            
            # Reload map at new center
            self.update_map()
            
        self.drag_start = None
    
    def on_scroll(self, event):
        """Zoom with scroll wheel"""
        current_zoom = int(self.zoom_var.get())
        if event.button == 'up' and current_zoom < 16:
            self.zoom_var.set(str(current_zoom + 1))
            self.update_map()
        elif event.button == 'down' and current_zoom > 10:
            self.zoom_var.set(str(current_zoom - 1))
            self.update_map()
    
    def go_to_location(self):
        """Navigate to entered coordinates"""
        try:
            self.current_lat = float(self.lat_var.get())
            self.current_lon = float(self.lon_var.get())
            self.update_map()
        except ValueError:
            messagebox.showerror("Error", "Invalid coordinates")
    
    def update_map(self):
        """Reload map with current settings (preview only, no caching)"""
        try:
            self.current_zoom = int(self.zoom_var.get())
            self.current_basemap = self.basemap_var.get()
            
            self.status_label.config(text="Loading preview...")
            self.dialog.update()
            
            # Load map WITHOUT caching (cache=None)
            map_img, _, _, _ = self.MapHandler.get_map_tile(
                self.current_lat, self.current_lon, 
                self.current_zoom, tile_size=3, 
                basemap=self.current_basemap, 
                cache=None  # No caching during preview
            )
            
            if map_img:
                self.current_map = map_img
                self.ax.clear()
                self.ax.imshow(map_img)
                
                # Mark center
                center = map_img.size[0] // 2
                self.ax.plot(center, center, 'r+', markersize=20, markeredgewidth=3)
                self.ax.axis('off')
                self.canvas.draw()
                
                self.status_label.config(text="Explore map, then click 'Set This Area'")
            else:
                self.status_label.config(text="Failed to load map")
                
        except Exception as e:
            print(f"Error updating map: {e}")
            self.status_label.config(text="Error loading map")
    
    def set_area(self):
        """User has selected this area - enable download"""
        self.area_set = True
        self.download_btn.config(state='normal')
        
        # Update lat/lon to current view center
        self.current_lat = float(self.lat_var.get())
        self.current_lon = float(self.lon_var.get())
        
        self.status_label.config(text=f"Area set! Click 'Download & Continue' to cache this region")
        print(f"Area set: Lat={self.current_lat:.4f}, Lon={self.current_lon:.4f}, Zoom={self.current_zoom}")
    
    def download_and_create(self):
        """Download map area and create project"""
        try:
            if not self.area_set:
                messagebox.showwarning("Area Not Set", "Please click 'Set This Area' first!")
                return
            
            lat = float(self.lat_var.get())
            lon = float(self.lon_var.get())
            zoom = int(self.zoom_var.get())
            basemap = self.basemap_var.get()
            radius = float(self.radius_var.get())
            
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                messagebox.showerror("Error", "Invalid coordinates")
                return
            
            self.download_btn.config(state='disabled')
            self.status_label.config(text="Downloading and caching map tiles...")
            self.dialog.update()
            
            # Now download WITH caching
            print(f"Downloading map area for caching...")
            map_img, _, _, _ = self.MapHandler.get_map_tile(
                lat, lon, zoom, tile_size=3, 
                basemap=basemap, 
                cache=self.cache  # Enable caching for download
            )
            
            self.result = {
                'lat': lat,
                'lon': lon,
                'zoom': zoom,
                'basemap': basemap,
                'radius': radius
            }
            
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid values")
            self.download_btn.config(state='normal')
    
    def cancel(self):
        """User cancelled - exit application"""
        if messagebox.askyesno("Exit", "Exit VetRender?"):
            self.result = None
            self.dialog.destroy()