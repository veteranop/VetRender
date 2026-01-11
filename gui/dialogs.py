"""
Dialog windows for VetRender GUI
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

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
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Make it modal
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel)
        
        # Title
        title_frame = ttk.Frame(self.dialog, padding="10")
        title_frame.pack(fill=tk.X)
        ttk.Label(title_frame, text="Welcome to VetRender", font=('Arial', 16, 'bold')).pack()
        ttk.Label(title_frame, text="Set up your propagation study area", font=('Arial', 10)).pack()
        
        # Instructions
        inst_frame = ttk.LabelFrame(self.dialog, text="Instructions", padding="10")
        inst_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        instructions = tk.Text(inst_frame, height=6, width=70, wrap=tk.WORD)
        instructions.pack(fill=tk.BOTH, expand=True)
        instructions.insert('1.0', 
            "1. Enter the coordinates where you want to plan RF coverage\n"
            "2. Choose zoom level (higher = more detail, larger download)\n"
            "3. Select basemap type\n"
            "4. Click 'Download & Create Project' to cache the map area\n"
            "5. This enables fast offline calculations and terrain analysis\n\n"
            "Tip: Start with zoom 13 for city-scale, zoom 15 for detailed neighborhood work"
        )
        instructions.config(state='disabled')
        
        # Location input
        input_frame = ttk.LabelFrame(self.dialog, text="Project Location", padding="10")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Latitude
        lat_frame = ttk.Frame(input_frame)
        lat_frame.pack(fill=tk.X, pady=5)
        ttk.Label(lat_frame, text="Latitude:", width=15).pack(side=tk.LEFT)
        self.lat_var = tk.StringVar(value="43.4665")
        ttk.Entry(lat_frame, textvariable=self.lat_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(lat_frame, text="(e.g., 43.4665 for Idaho Falls)").pack(side=tk.LEFT)
        
        # Longitude
        lon_frame = ttk.Frame(input_frame)
        lon_frame.pack(fill=tk.X, pady=5)
        ttk.Label(lon_frame, text="Longitude:", width=15).pack(side=tk.LEFT)
        self.lon_var = tk.StringVar(value="-112.0340")
        ttk.Entry(lon_frame, textvariable=self.lon_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(lon_frame, text="(negative for West)").pack(side=tk.LEFT)
        
        # Zoom level
        zoom_frame = ttk.Frame(input_frame)
        zoom_frame.pack(fill=tk.X, pady=5)
        ttk.Label(zoom_frame, text="Zoom Level:", width=15).pack(side=tk.LEFT)
        self.zoom_var = tk.StringVar(value="13")
        zoom_combo = ttk.Combobox(zoom_frame, textvariable=self.zoom_var, width=18,
                                  values=['10', '11', '12', '13', '14', '15', '16'], state='readonly')
        zoom_combo.pack(side=tk.LEFT, padx=5)
        
        zoom_info = {
            '10': '~300 km coverage',
            '11': '~150 km coverage',
            '12': '~75 km coverage',
            '13': '~40 km coverage (default)',
            '14': '~20 km coverage',
            '15': '~10 km coverage',
            '16': '~5 km coverage (detailed)'
        }
        self.zoom_info_label = ttk.Label(zoom_frame, text=zoom_info['13'])
        self.zoom_info_label.pack(side=tk.LEFT)
        zoom_combo.bind('<<ComboboxSelected>>', lambda e: self.zoom_info_label.config(
            text=zoom_info.get(self.zoom_var.get(), '')))
        
        # Basemap
        basemap_frame = ttk.Frame(input_frame)
        basemap_frame.pack(fill=tk.X, pady=5)
        ttk.Label(basemap_frame, text="Basemap:", width=15).pack(side=tk.LEFT)
        self.basemap_var = tk.StringVar(value="OpenStreetMap")
        
        # Import MapHandler to get basemap list
        from models.map_handler import MapHandler
        basemap_combo = ttk.Combobox(basemap_frame, textvariable=self.basemap_var, width=18,
                                     values=list(MapHandler.BASEMAPS.keys()), state='readonly')
        basemap_combo.pack(side=tk.LEFT, padx=5)
        ttk.Label(basemap_frame, text="(recommend OpenTopoMap for terrain)").pack(side=tk.LEFT)
        
        # Coverage radius
        radius_frame = ttk.Frame(input_frame)
        radius_frame.pack(fill=tk.X, pady=5)
        ttk.Label(radius_frame, text="Coverage Radius:", width=15).pack(side=tk.LEFT)
        self.radius_var = tk.StringVar(value="50")
        ttk.Entry(radius_frame, textvariable=self.radius_var, width=20).pack(side=tk.LEFT, padx=5)
        ttk.Label(radius_frame, text="km (for terrain pre-download)").pack(side=tk.LEFT)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog, padding="10")
        btn_frame.pack(fill=tk.X)
        
        self.download_btn = ttk.Button(btn_frame, text="Download & Create Project", command=self.download_and_create)
        self.download_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="Skip (Quick Start)", command=self.quick_start).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Load Existing Project...", command=self.load_project).pack(side=tk.LEFT, padx=5)
        
        self.status_label = ttk.Label(btn_frame, text="")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def download_and_create(self):
        """Download map area and create project"""
        try:
            lat = float(self.lat_var.get())
            lon = float(self.lon_var.get())
            zoom = int(self.zoom_var.get())
            basemap = self.basemap_var.get()
            radius = float(self.radius_var.get())
            
            if not (-90 <= lat <= 90):
                messagebox.showerror("Error", "Latitude must be between -90 and 90")
                return
            
            if not (-180 <= lon <= 180):
                messagebox.showerror("Error", "Longitude must be between -180 and 180")
                return
            
            self.download_btn.config(state='disabled')
            self.status_label.config(text="Downloading map tiles...")
            self.dialog.update()
            
            # This will trigger map download with caching
            self.result = {
                'lat': lat,
                'lon': lon,
                'zoom': zoom,
                'basemap': basemap,
                'radius': radius,
                'mode': 'download'
            }
            
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")
            self.download_btn.config(state='normal')
    
    def quick_start(self):
        """Quick start without downloading"""
        try:
            lat = float(self.lat_var.get())
            lon = float(self.lon_var.get())
            zoom = int(self.zoom_var.get())
            basemap = self.basemap_var.get()
            
            self.result = {
                'lat': lat,
                'lon': lon,
                'zoom': zoom,
                'basemap': basemap,
                'radius': 50,
                'mode': 'quick'
            }
            
            self.dialog.destroy()
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")
    
    def load_project(self):
        """Load existing project file"""
        filepath = filedialog.askopenfilename(
            title="Load VetRender Project",
            filetypes=[("VetRender Project", "*.vrp"), ("All files", "*.*")]
        )
        if filepath:
            self.result = {
                'mode': 'load',
                'filepath': filepath
            }
            self.dialog.destroy()
    
    def cancel(self):
        """User cancelled - exit application"""
        if messagebox.askyesno("Exit", "Exit VetRender?"):
            self.result = None
            self.dialog.destroy()