"""
Main VetRender GUI window
"""
import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.colors import LinearSegmentedColormap

from models.antenna import AntennaPattern
from models.propagation import PropagationModel
from models.terrain import TerrainHandler
from models.map_handler import MapHandler
from models.map_cache import MapCache
from gui.dialogs import TransmitterConfigDialog, AntennaInfoDialog, CacheManagerDialog, ProjectSetupDialog


class VetRender:
    def __init__(self, root):
        self.root = root
        self.root.title("VetRender - RF Propagation Tool")
        self.root.geometry("1400x900")
        
        self.antenna_pattern = AntennaPattern()
        self.pattern_name = "Default Omni (0 dBi)"
        
        # Initialize cache
        self.cache = MapCache()
        print(f"Cache initialized at: {self.cache.cache_dir}")
        
        # Transmitter parameters
        self.tx_lat = 43.4665
        self.tx_lon = -112.0340
        self.erp = 40
        self.frequency = 900
        self.height = 30
        self.max_distance = 100
        self.resolution = 500
        
        # Terrain calculation granularity
        self.terrain_azimuths = 72  # Every 5 degrees
        self.terrain_distances = 50  # Points per radial
        
        # Signal threshold (dBm) - below this, no signal is shown
        self.signal_threshold = -110
        
        # Map parameters
        self.zoom = 13
        self.basemap = 'OpenStreetMap'
        self.map_image = None
        self.map_zoom = 13
        self.map_xtile = 0
        self.map_ytile = 0
        
        # Terrain settings
        self.use_terrain = tk.BooleanVar(value=False)
        
        self.setup_ui()
        self.load_map()
        
    def setup_ui(self):
        """Setup the user interface"""
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Label(toolbar, text="Transmitter:").pack(side=tk.LEFT, padx=5)
        self.tx_label = ttk.Label(toolbar, text=f"Lat: {self.tx_lat:.4f}, Lon: {self.tx_lon:.4f}")
        self.tx_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(toolbar, text="Basemap:").pack(side=tk.LEFT, padx=5)
        self.basemap_var = tk.StringVar(value=self.basemap)
        basemap_combo = ttk.Combobox(toolbar, textvariable=self.basemap_var, width=18,
                                     values=list(MapHandler.BASEMAPS.keys()), state='readonly')
        basemap_combo.pack(side=tk.LEFT, padx=5)
        basemap_combo.bind('<<ComboboxSelected>>', lambda e: self.change_basemap())
        
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Label(toolbar, text="Zoom:").pack(side=tk.LEFT, padx=5)
        self.zoom_var = tk.StringVar(value=str(self.zoom))
        zoom_combo = ttk.Combobox(toolbar, textvariable=self.zoom_var, width=5, 
                                  values=['10', '11', '12', '13', '14', '15', '16'])
        zoom_combo.pack(side=tk.LEFT, padx=5)
        zoom_combo.bind('<<ComboboxSelected>>', lambda e: self.load_map())
        
        ttk.Button(toolbar, text="Refresh Map", command=self.load_map).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Checkbutton(toolbar, text="Use Terrain Data", variable=self.use_terrain).pack(side=tk.LEFT, padx=5)
        
        # Terrain granularity controls
        ttk.Label(toolbar, text="Azimuths:").pack(side=tk.LEFT, padx=(10, 2))
        self.azimuth_var = tk.StringVar(value=str(self.terrain_azimuths))
        azimuth_entry = ttk.Entry(toolbar, textvariable=self.azimuth_var, width=5)
        azimuth_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(toolbar, text="Dist Points:").pack(side=tk.LEFT, padx=(5, 2))
        self.dist_points_var = tk.StringVar(value=str(self.terrain_distances))
        dist_entry = ttk.Entry(toolbar, textvariable=self.dist_points_var, width=5)
        dist_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(toolbar, text="Calculate Coverage", command=self.calculate_propagation).pack(side=tk.LEFT, padx=20)
        
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.status_var = tk.StringVar(value="Ready - Right-click on map for options")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        # Main map area
        map_frame = ttk.Frame(self.root, padding="0")
        map_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fig = Figure(dpi=100)
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.canvas.mpl_connect('button_press_event', self.on_map_click)
        
        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Set Transmitter Location", command=self.set_tx_location)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit Transmitter Configuration", command=self.edit_tx_config)
        self.context_menu.add_command(label="Edit Antenna Information", command=self.edit_antenna_info)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Manage Cache...", command=self.manage_cache)
        
        self.click_x = 0
        self.click_y = 0
        
    def change_basemap(self):
        """Change the basemap style"""
        self.basemap = self.basemap_var.get()
        print(f"\n{'='*60}")
        print(f"BASEMAP CHANGED")
        print(f"{'='*60}")
        print(f"New basemap: {self.basemap}")
        self.load_map()
        
    def load_map(self):
        """Load and display map"""
        try:
            self.zoom = int(self.zoom_var.get())
            
            print(f"\n{'='*60}")
            print(f"LOADING MAP")
            print(f"{'='*60}")
            print(f"Basemap: {self.basemap}")
            print(f"Center: Lat={self.tx_lat:.6f}, Lon={self.tx_lon:.6f}")
            print(f"Zoom Level: {self.zoom}")
            
            self.status_var.set("Loading map...")
            self.root.update()
            
            self.map_image, self.map_zoom, self.map_xtile, self.map_ytile = MapHandler.get_map_tile(
                self.tx_lat, self.tx_lon, self.zoom, tile_size=3, basemap=self.basemap, cache=self.cache
            )
            
            if self.map_image:
                print(f"Map loaded successfully - Image size: {self.map_image.size}")
                print(f"Tile position: X={self.map_xtile}, Y={self.map_ytile}")
                self.display_map()
                self.status_var.set(f"Map loaded - Right-click for options")
            else:
                print("ERROR: Failed to load map image")
                self.status_var.set("Failed to load map - check internet connection")
                
        except Exception as e:
            print(f"ERROR loading map: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Map error: {e}")
            self.status_var.set("Error loading map")
    
    def display_map(self):
        """Display map with transmitter marker"""
        self.ax.clear()
        
        if self.map_image:
            self.ax.imshow(self.map_image)
            self.ax.axis('off')
            
            img_center = self.map_image.size[0] // 2
            self.ax.plot(img_center, img_center, 'r^', markersize=20, label='Transmitter', 
                        markeredgecolor='white', markeredgewidth=2)
            self.ax.legend(loc='upper right', fontsize=12)
            
        self.canvas.draw()
    
    def on_map_click(self, event):
        """Handle mouse clicks on map"""
        if event.inaxes == self.ax and self.map_image:
            if event.button == 3:  # Right click
                self.click_x = event.xdata
                self.click_y = event.ydata
                try:
                    self.context_menu.tk_popup(int(event.guiEvent.x_root), int(event.guiEvent.y_root))
                finally:
                    self.context_menu.grab_release()
    
    def set_tx_location(self):
        """Set transmitter location from click position"""
        if self.map_image:
            img_size = self.map_image.size[0]
            lat, lon = MapHandler.pixel_to_latlon(
                self.click_x, self.click_y, 
                self.tx_lat, self.tx_lon, 
                self.map_zoom, img_size
            )
            
            print(f"\n{'='*60}")
            print(f"TRANSMITTER LOCATION CHANGED")
            print(f"{'='*60}")
            print(f"Click position: Pixel X={self.click_x:.1f}, Y={self.click_y:.1f}")
            print(f"Old location: Lat={self.tx_lat:.6f}, Lon={self.tx_lon:.6f}")
            print(f"New location: Lat={lat:.6f}, Lon={lon:.6f}")
            
            self.tx_lat = lat
            self.tx_lon = lon
            self.tx_label.config(text=f"Lat: {lat:.4f}, Lon: {lon:.4f}")
            
            self.status_var.set(f"Transmitter moved to Lat: {lat:.4f}, Lon: {lon:.4f}")
            
            self.load_map()
    
    def edit_tx_config(self):
        """Open dialog to edit transmitter configuration"""
        dialog = TransmitterConfigDialog(self.root, self.erp, self.frequency, self.height)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            old_erp, old_freq, old_height = self.erp, self.frequency, self.height
            self.erp, self.frequency, self.height = dialog.result
            
            print(f"\n{'='*60}")
            print(f"TRANSMITTER CONFIGURATION UPDATED")
            print(f"{'='*60}")
            print(f"ERP:       {old_erp} dBm -> {self.erp} dBm")
            print(f"Frequency: {old_freq} MHz -> {self.frequency} MHz")
            print(f"Height:    {old_height} m -> {self.height} m")
            
            self.status_var.set(f"Configuration updated - ERP: {self.erp} dBm, Freq: {self.frequency} MHz")
    
    def edit_antenna_info(self):
        """Open dialog to edit antenna information"""
        dialog = AntennaInfoDialog(self.root, self.pattern_name)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            action, data = dialog.result
            print(f"\n{'='*60}")
            print(f"ANTENNA PATTERN CHANGED")
            print(f"{'='*60}")
            if action == 'load':
                if self.antenna_pattern.load_from_xml(data):
                    self.pattern_name = data.split('/')[-1].split('\\')[-1]
                    print(f"Loaded pattern: {self.pattern_name}")
                    print(f"File path: {data}")
                    print(f"Max gain: {self.antenna_pattern.max_gain:.2f} dBi")
                    print(f"Azimuth points: {len(self.antenna_pattern.azimuth_pattern)}")
                    print(f"Elevation points: {len(self.antenna_pattern.elevation_pattern)}")
                    self.status_var.set(f"Antenna pattern loaded: {self.pattern_name}")
                else:
                    print(f"ERROR: Failed to load pattern from {data}")
                    messagebox.showerror("Error", "Failed to load antenna pattern")
            elif action == 'reset':
                self.antenna_pattern.load_default_omni()
                self.pattern_name = "Default Omni (0 dBi)"
                print(f"Reset to: {self.pattern_name}")
                self.status_var.set("Reset to default omnidirectional antenna")
    
    def manage_cache(self):
        """Open cache management dialog"""
        CacheManagerDialog(self.root, self.cache)
    
    def show_project_setup(self):
        """Show project setup dialog on startup"""
        dialog = ProjectSetupDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result is None:
            # User cancelled - exit app
            self.root.quit()
            return
        
        mode = dialog.result['mode']
        
        if mode == 'download':
            # Set parameters from dialog
            self.tx_lat = dialog.result['lat']
            self.tx_lon = dialog.result['lon']
            self.zoom = dialog.result['zoom']
            self.basemap = dialog.result['basemap']
            self.max_distance = dialog.result['radius']
            
            # Update UI
            self.tx_label.config(text=f"Lat: {self.tx_lat:.4f}, Lon: {self.tx_lon:.4f}")
            self.zoom_var.set(str(self.zoom))
            self.basemap_var.set(self.basemap)
            
            print(f"\n{'='*60}")
            print(f"PROJECT SETUP - DOWNLOAD MODE")
            print(f"{'='*60}")
            print(f"Location: {self.tx_lat:.4f}, {self.tx_lon:.4f}")
            print(f"Zoom: {self.zoom}, Basemap: {self.basemap}")
            print(f"Coverage radius: {self.max_distance} km")
            
            # Load map (will cache tiles)
            self.load_map()
            
            messagebox.showinfo("Project Ready", 
                              "Map area downloaded and cached!\n\n"
                              "• Right-click to place transmitter\n"
                              "• Edit transmitter config\n"
                              "• Click 'Calculate Coverage'\n\n"
                              "Calculations will now be much faster!")
            
        elif mode == 'quick':
            # Quick start - just load map without pre-caching terrain
            self.tx_lat = dialog.result['lat']
            self.tx_lon = dialog.result['lon']
            self.zoom = dialog.result['zoom']
            self.basemap = dialog.result['basemap']
            
            self.tx_label.config(text=f"Lat: {self.tx_lat:.4f}, Lon: {self.tx_lon:.4f}")
            self.zoom_var.set(str(self.zoom))
            self.basemap_var.set(self.basemap)
            
            print(f"\n{'='*60}")
            print(f"PROJECT SETUP - QUICK START")
            print(f"{'='*60}")
            print(f"Location: {self.tx_lat:.4f}, {self.tx_lon:.4f}")
            
            self.load_map()
            
        elif mode == 'load':
            # Load existing project
            filepath = dialog.result['filepath']
            center, radius = self.cache.import_project(filepath)
            
            if center:
                self.tx_lat = center['lat']
                self.tx_lon = center['lon']
                self.max_distance = radius
                
                self.tx_label.config(text=f"Lat: {self.tx_lat:.4f}, Lon: {self.tx_lon:.4f}")
                
                print(f"\n{'='*60}")
                print(f"PROJECT LOADED")
                print(f"{'='*60}")
                print(f"Location: {self.tx_lat:.4f}, {self.tx_lon:.4f}")
                
                self.load_map()
                
                messagebox.showinfo("Project Loaded", 
                                  f"Loaded project from:\n{filepath}\n\n"
                                  "Cached data is ready for fast calculations!")
            else:
                messagebox.showerror("Error", "Failed to load project file")
                self.show_project_setup()  # Try again
    
    def calculate_propagation(self):
        """Calculate and overlay propagation on map"""
        try:
            print(f"\n{'='*60}")
            print(f"CALCULATING PROPAGATION")
            print(f"{'='*60}")
            print(f"Transmitter Location: Lat={self.tx_lat:.6f}, Lon={self.tx_lon:.6f}")
            print(f"ERP: {self.erp} dBm")
            print(f"Frequency: {self.frequency} MHz")
            print(f"Antenna Height: {self.height} m")
            print(f"Max Distance: {self.max_distance} km")
            print(f"Resolution: {self.resolution} points")
            print(f"Antenna Pattern: {self.pattern_name}")
            print(f"Use Terrain: {self.use_terrain.get()}")
            
            self.status_var.set("Calculating propagation...")
            self.root.update()
            
            eirp_dbm = PropagationModel.erp_to_eirp(self.erp)
            print(f"EIRP: {eirp_dbm:.2f} dBm")
            
            print(f"\nCreating calculation grid...")
            azimuths = np.linspace(0, 360, self.resolution)
            distances = np.linspace(0.1, self.max_distance, self.resolution)
            
            az_grid, dist_grid = np.meshgrid(azimuths, distances)
            print(f"Grid shape: {az_grid.shape}")
            
            print(f"Calculating antenna gains...")
            gain_grid = np.zeros_like(az_grid)
            for i, az in enumerate(azimuths):
                gain_grid[:, i] = self.antenna_pattern.get_gain(az, elevation=0)
            
            print(f"Gain range: {gain_grid.min():.2f} to {gain_grid.max():.2f} dBi")
            
            print(f"Calculating path loss...")
            fspl_grid = PropagationModel.free_space_loss(dist_grid, self.frequency)
            
            terrain_loss_grid = np.zeros_like(dist_grid)
            if self.use_terrain.get():
                print(f"Fetching terrain data and calculating terrain losses...")
                self.status_var.set("Fetching terrain data...")
                self.root.update()
                
                # Get user-defined granularity
                try:
                    sample_azimuths_count = int(self.azimuth_var.get())
                    sample_distances_count = int(self.dist_points_var.get())
                except ValueError:
                    sample_azimuths_count = 72
                    sample_distances_count = 50
                    print(f"Invalid granularity values, using defaults: {sample_azimuths_count} azimuths, {sample_distances_count} distances")
                
                print(f"Terrain granularity: {sample_azimuths_count} azimuths, {sample_distances_count} distance points")
                print(f"Total terrain queries: {sample_azimuths_count * sample_distances_count}")
                
                # Increase resolution for better terrain sampling
                sample_azimuths = np.linspace(0, 360, sample_azimuths_count)
                sample_distances = np.linspace(0, self.max_distance, sample_distances_count)
                
                for i, az in enumerate(sample_azimuths):
                    if i % max(1, sample_azimuths_count // 10) == 0:
                        print(f"  Processing azimuth {az:.0f}° ({i+1}/{len(sample_azimuths)})")
                    
                    lat_points = []
                    lon_points = []
                    for d in sample_distances:
                        lat_offset = d * np.cos(np.radians(az)) / 111.0
                        lon_offset = d * np.sin(np.radians(az)) / (111.0 * np.cos(np.radians(self.tx_lat)))
                        
                        point_lat = self.tx_lat + lat_offset
                        point_lon = self.tx_lon + lon_offset
                        lat_points.append(point_lat)
                        lon_points.append(point_lon)
                    
                    elevations = TerrainHandler.get_elevations_batch(list(zip(lat_points, lon_points)))
                    
                    terrain_loss = PropagationModel.terrain_diffraction_loss(
                        self.height, 2, elevations, self.frequency
                    )
                    
                    # Apply terrain loss to nearby azimuths with interpolation
                    az_idx = np.argmin(np.abs(azimuths - az))
                    spread = max(1, int(180 / sample_azimuths_count))  # Adaptive spread based on granularity
                    for offset in range(-spread, spread + 1):
                        idx = (az_idx + offset) % len(azimuths)
                        weight = 1.0 - abs(offset) / (spread + 1)
                        terrain_loss_grid[:, idx] += terrain_loss * weight / spread
                
                print(f"Terrain loss range: {terrain_loss_grid.min():.2f} to {terrain_loss_grid.max():.2f} dB")
            
            rx_power_grid = eirp_dbm + gain_grid - fspl_grid - terrain_loss_grid
            
            print(f"FSPL range: {fspl_grid.min():.2f} to {fspl_grid.max():.2f} dB")
            print(f"Received power range: {rx_power_grid.min():.2f} to {rx_power_grid.max():.2f} dBm")
            
            print(f"Plotting propagation overlay...")
            self.plot_propagation_on_map(az_grid, dist_grid, rx_power_grid)
            
            print(f"{'='*60}")
            print(f"PROPAGATION CALCULATION COMPLETE")
            print(f"{'='*60}\n")
            
            self.status_var.set(f"Coverage calculated - EIRP: {eirp_dbm:.1f} dBm")
            
        except Exception as e:
            print(f"\nERROR in calculate_propagation:")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Calculation error: {e}")
            self.status_var.set("Error in calculation")
    
    def plot_propagation_on_map(self, az_grid, dist_grid, rx_power_grid):
        """Overlay propagation pattern on map"""
        self.ax.clear()
        
        if self.map_image:
            self.ax.imshow(self.map_image, extent=[0, self.map_image.size[0], self.map_image.size[1], 0])
            
            img_center = self.map_image.size[0] // 2
            
            scale = 30 * (2 ** (self.map_zoom - 13))
            
            az_rad = np.deg2rad(az_grid)
            x = img_center + dist_grid * scale * np.sin(az_rad)
            y = img_center - dist_grid * scale * np.cos(az_rad)
            
            # Create custom colormap: Red (strong) -> Yellow -> Green -> Cyan -> Blue (weak)
            colors = [
                '#0000FF',  # Blue (weakest)
                '#0080FF',  # Light blue
                '#00FFFF',  # Cyan
                '#00FF80',  # Cyan-green
                '#00FF00',  # Green
                '#80FF00',  # Yellow-green
                '#FFFF00',  # Yellow (mid)
                '#FFD000',  # Orange-yellow
                '#FFA000',  # Orange
                '#FF6000',  # Red-orange
                '#FF0000',  # Red (strongest)
            ]
            cmap = LinearSegmentedColormap.from_list('signal_strength', colors, N=256)
            
            # Mask areas below threshold (dead spots)
            rx_power_masked = np.ma.masked_where(rx_power_grid < self.signal_threshold, rx_power_grid)
            
            # Plot contours with transparency - more levels for smoother gradient
            levels = np.linspace(rx_power_masked.max(), self.signal_threshold, 40)
            contour = self.ax.contourf(x, y, rx_power_masked, levels=levels, cmap=cmap, alpha=0.6, extend='neither')
            
            if hasattr(self, 'colorbar') and self.colorbar is not None:
                try:
                    self.colorbar.remove()
                except:
                    pass
            self.colorbar = self.fig.colorbar(contour, ax=self.ax, pad=0.01, fraction=0.03, aspect=30)
            self.colorbar.set_label('Signal Strength (dBm)', rotation=270, labelpad=15, fontsize=9)
            self.colorbar.ax.tick_params(labelsize=8)
            
            # Mark transmitter
            self.ax.plot(img_center, img_center, 'r^', markersize=15, 
                        markeredgecolor='white', markeredgewidth=2, label='Transmitter', zorder=10)
            
            self.ax.set_xlim(0, self.map_image.size[0])
            self.ax.set_ylim(self.map_image.size[1], 0)
            self.ax.axis('off')
            self.ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
            
            # Remove all margins
            self.fig.tight_layout(pad=0)
            
        self.canvas.draw()