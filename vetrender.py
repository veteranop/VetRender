import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import xml.etree.ElementTree as ET
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from io import BytesIO
from urllib.request import urlopen, Request
from PIL import Image
import json

class AntennaPattern:
    """Handles antenna pattern data from XML"""
    def __init__(self):
        self.azimuth_pattern = {}
        self.elevation_pattern = {}
        self.max_gain = 0
        self.load_default_omni()
        
    def load_default_omni(self):
        """Load default omnidirectional antenna pattern (0 dBi gain)"""
        for angle in range(0, 360, 1):
            self.azimuth_pattern[angle] = 0.0
        for angle in range(-90, 91, 1):
            self.elevation_pattern[angle] = 0.0
        self.max_gain = 0.0
        
    def load_from_xml(self, filepath):
        """Load antenna pattern from XML file"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            self.azimuth_pattern = {}
            self.elevation_pattern = {}
            
            for elem in root.iter():
                if 'azimuth' in elem.tag.lower():
                    for child in elem:
                        angle = float(child.get('angle', child.get('deg', 0)))
                        gain = float(child.get('gain', child.get('db', 0)))
                        self.azimuth_pattern[angle] = gain
                        
                if 'elevation' in elem.tag.lower():
                    for child in elem:
                        angle = float(child.get('angle', child.get('deg', 0)))
                        gain = float(child.get('gain', child.get('db', 0)))
                        self.elevation_pattern[angle] = gain
            
            if self.azimuth_pattern:
                self.max_gain = max(self.azimuth_pattern.values())
            
            return True
        except Exception as e:
            print(f"Error loading XML: {e}")
            return False
    
    def get_gain(self, azimuth, elevation=0):
        """Get antenna gain for a given azimuth and elevation angle"""
        az_gain = self._interpolate_pattern(self.azimuth_pattern, azimuth)
        el_gain = self._interpolate_pattern(self.elevation_pattern, elevation)
        
        if az_gain is not None and el_gain is not None:
            return az_gain + el_gain - self.max_gain
        elif az_gain is not None:
            return az_gain
        elif el_gain is not None:
            return el_gain
        else:
            return 0
    
    def _interpolate_pattern(self, pattern, angle):
        """Interpolate gain from pattern dictionary"""
        if not pattern:
            return None
            
        if angle < 0:
            angle = max(-90, min(90, angle))
        else:
            angle = angle % 360
        
        if angle in pattern:
            return pattern[angle]
        
        angles = sorted(pattern.keys())
        lower = max([a for a in angles if a <= angle], default=angles[-1])
        upper = min([a for a in angles if a > angle], default=angles[0])
        
        if lower == upper:
            return pattern[lower]
        
        if upper < lower and angle >= 0:
            upper += 360
            if angle < lower:
                angle += 360
        
        if upper != lower:
            ratio = (angle - lower) / (upper - lower)
            gain = pattern[lower] + ratio * (pattern[upper % 360 if angle >= 0 else upper] - pattern[lower])
        else:
            gain = pattern[lower]
        
        return gain


class TerrainHandler:
    """Handles terrain elevation data from Open-Elevation API"""
    
    @staticmethod
    def get_elevation(lat, lon):
        """Get elevation for a single point using Open-Elevation API"""
        try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
            req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})
            
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if 'results' in data and len(data['results']) > 0:
                    elevation = data['results'][0]['elevation']
                    return elevation
        except Exception as e:
            print(f"Warning: Could not fetch elevation for {lat},{lon}: {e}")
        
        return 0
    
    @staticmethod
    def get_elevations_batch(lat_lon_pairs):
        """Get elevations for multiple points (max 100 per request)"""
        try:
            locations = "|".join([f"{lat},{lon}" for lat, lon in lat_lon_pairs[:100]])
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}"
            req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})
            
            with urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
                if 'results' in data:
                    return [result['elevation'] for result in data['results']]
        except Exception as e:
            print(f"Warning: Batch elevation fetch failed: {e}")
        
        return [0] * len(lat_lon_pairs)


class PropagationModel:
    """RF Propagation calculations with terrain awareness"""
    
    @staticmethod
    def free_space_loss(distance_km, frequency_mhz):
        """Calculate free space path loss in dB"""
        result = np.where(distance_km > 0, 
                         32.45 + 20 * np.log10(distance_km) + 20 * np.log10(frequency_mhz),
                         0)
        return result
    
    @staticmethod
    def terrain_diffraction_loss(tx_height, rx_height, terrain_profile, frequency_mhz):
        """Calculate additional loss due to terrain obstacles using knife-edge diffraction"""
        if len(terrain_profile) < 2:
            return 0
        
        wavelength = 300 / frequency_mhz
        
        tx_elev = terrain_profile[0] + tx_height
        rx_elev = terrain_profile[-1] + rx_height
        
        path_length = len(terrain_profile)
        los_line = np.linspace(tx_elev, rx_elev, path_length)
        
        clearances = (terrain_profile - los_line)
        max_obstruction = np.max(clearances)
        
        if max_obstruction <= 0:
            return 0
        
        v = max_obstruction * np.sqrt(2 / wavelength)
        
        if v <= -0.8:
            loss = 0
        elif v <= 0:
            loss = 6.9 + 20 * np.log10(np.sqrt((v - 0.1)**2 + 1) + v - 0.1)
        elif v <= 1:
            loss = 6.9 + 20 * np.log10(np.sqrt((v - 0.1)**2 + 1) + v - 0.1)
        elif v <= 2.4:
            loss = 6.9 + 20 * np.log10(np.sqrt((v - 0.1)**2 + 1) + v - 0.1)
        else:
            loss = 13 + 20 * np.log10(v)
        
        return max(0, loss)
    
    @staticmethod
    def erp_to_eirp(erp_dbm):
        """Convert ERP to EIRP (add 2.15 dB for dipole reference)"""
        return erp_dbm + 2.15


class MapHandler:
    """Handles map tile fetching and display"""
    
    BASEMAPS = {
        'OpenStreetMap': {
            'url': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            'attribution': 'OpenStreetMap'
        },
        'OpenTopoMap': {
            'url': 'https://tile.opentopomap.org/{z}/{x}/{y}.png',
            'attribution': 'OpenTopoMap'
        },
        'Esri WorldImagery': {
            'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            'attribution': 'Esri'
        },
        'Esri WorldTopo': {
            'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            'attribution': 'Esri'
        },
        'Stamen Terrain': {
            'url': 'https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png',
            'attribution': 'Stamen Design'
        },
        'CartoDB Positron': {
            'url': 'https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
            'attribution': 'CartoDB'
        },
        'CartoDB Dark': {
            'url': 'https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png',
            'attribution': 'CartoDB'
        }
    }
    
    @staticmethod
    def deg2num(lat_deg, lon_deg, zoom):
        """Convert lat/lon to tile numbers"""
        lat_rad = np.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n)
        return xtile, ytile
    
    @staticmethod
    def num2deg(xtile, ytile, zoom):
        """Convert tile numbers to lat/lon"""
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * ytile / n)))
        lat_deg = np.degrees(lat_rad)
        return lat_deg, lon_deg
    
    @staticmethod
    def pixel_to_latlon(pixel_x, pixel_y, center_lat, center_lon, zoom, img_size):
        """Convert pixel coordinates to lat/lon"""
        center_xtile, center_ytile = MapHandler.deg2num(center_lat, center_lon, zoom)
        
        tile_size = 256
        tiles_offset_x = (pixel_x - img_size / 2) / tile_size
        tiles_offset_y = (pixel_y - img_size / 2) / tile_size
        
        new_xtile = center_xtile + tiles_offset_x
        new_ytile = center_ytile + tiles_offset_y
        
        lat, lon = MapHandler.num2deg(new_xtile, new_ytile, zoom)
        return lat, lon
    
    @staticmethod
    def get_map_tile(lat, lon, zoom=13, tile_size=3, basemap='OpenStreetMap'):
        """Fetch map tiles centered on lat/lon"""
        try:
            if basemap not in MapHandler.BASEMAPS:
                basemap = 'OpenStreetMap'
            
            url_template = MapHandler.BASEMAPS[basemap]['url']
            
            xtile, ytile = MapHandler.deg2num(lat, lon, zoom)
            tile_range = tile_size // 2
            img_size = 256 * tile_size
            composite = Image.new('RGB', (img_size, img_size))
            
            print(f"Fetching {basemap} tiles...")
            
            for dx in range(-tile_range, tile_range + 1):
                for dy in range(-tile_range, tile_range + 1):
                    x = xtile + dx
                    y = ytile + dy
                    
                    url = url_template.replace('{z}', str(zoom)).replace('{x}', str(x)).replace('{y}', str(y))
                    req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})
                    
                    try:
                        with urlopen(req, timeout=5) as response:
                            tile_data = response.read()
                            tile_img = Image.open(BytesIO(tile_data))
                            
                            px = (dx + tile_range) * 256
                            py = (dy + tile_range) * 256
                            composite.paste(tile_img, (px, py))
                    except Exception as e:
                        print(f"Failed to fetch tile {x},{y}: {e}")
            
            return composite, zoom, xtile, ytile
        except Exception as e:
            print(f"Error fetching map: {e}")
            return None, zoom, 0, 0


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


class VetRender:
    def __init__(self, root):
        self.root = root
        self.root.title("VetRender - RF Propagation Tool")
        self.root.geometry("1400x900")
        
        self.antenna_pattern = AntennaPattern()
        self.pattern_name = "Default Omni (0 dBi)"
        
        self.tx_lat = 43.4665
        self.tx_lon = -112.0340
        self.erp = 40
        self.frequency = 900
        self.height = 30
        self.max_distance = 100
        self.resolution = 500
        
        self.zoom = 13
        self.basemap = 'OpenStreetMap'
        self.map_image = None
        self.map_zoom = 13
        self.map_xtile = 0
        self.map_ytile = 0
        
        self.use_terrain = tk.BooleanVar(value=False)
        
        self.setup_ui()
        self.load_map()
        
    def setup_ui(self):
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
        
        ttk.Button(toolbar, text="Calculate Coverage", command=self.calculate_propagation).pack(side=tk.LEFT, padx=20)
        
        ttk.Separator(toolbar, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.status_var = tk.StringVar(value="Ready - Right-click on map for options")
        ttk.Label(toolbar, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        map_frame = ttk.Frame(self.root, padding="10")
        map_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(12, 10), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.canvas.mpl_connect('button_press_event', self.on_map_click)
        
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Set Transmitter Location", command=self.set_tx_location)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit Transmitter Configuration", command=self.edit_tx_config)
        self.context_menu.add_command(label="Edit Antenna Information", command=self.edit_antenna_info)
        
        self.click_x = 0
        self.click_y = 0
        
    def change_basemap(self):
        self.basemap = self.basemap_var.get()
        print(f"\n{'='*60}")
        print(f"BASEMAP CHANGED")
        print(f"{'='*60}")
        print(f"New basemap: {self.basemap}")
        self.load_map()
        
    def load_map(self):
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
                self.tx_lat, self.tx_lon, self.zoom, tile_size=3, basemap=self.basemap
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
        if event.inaxes == self.ax and self.map_image:
            if event.button == 3:
                self.click_x = event.xdata
                self.click_y = event.ydata
                try:
                    self.context_menu.tk_popup(int(event.guiEvent.x_root), int(event.guiEvent.y_root))
                finally:
                    self.context_menu.grab_release()
    
    def set_tx_location(self):
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
        dialog = TransmitterConfigDialog(self.root, self.erp, self.frequency, self.height)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            old_erp, old_freq, old_height = self.erp, self.frequency, self.height
            self.erp, self.frequency, self.height = dialog.result
            
            print(f"\n{'='*60}")
            print(f"TRANSMITTER CONFIGURATION UPDATED")
            print(f"{'='*60}")
            print(f"ERP:       {old_erp} dBm -> {self.erp} dBm")
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
                
                sample_azimuths = np.linspace(0, 360, 36)
                sample_distances = np.linspace(0, self.max_distance, 20)
                
                for i, az in enumerate(sample_azimuths):
                    if i % 5 == 0:
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
                    
                    az_idx = np.argmin(np.abs(azimuths - az))
                    terrain_loss_grid[:, max(0, az_idx-5):min(len(azimuths), az_idx+5)] += terrain_loss / 10
                
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
        self.ax.clear()
        
        if self.map_image:
            self.ax.imshow(self.map_image)
            
            img_center = self.map_image.size[0] // 2
            
            scale = 30 * (2 ** (self.map_zoom - 13))
            
            az_rad = np.deg2rad(az_grid)
            x = img_center + dist_grid * scale * np.sin(az_rad)
            y = img_center - dist_grid * scale * np.cos(az_rad)
            
            colors = ['red', 'orange', 'yellow', 'lightgreen', 'green']
            cmap = LinearSegmentedColormap.from_list('signal', colors, N=100)
            
            contour = self.ax.contourf(x, y, rx_power_grid, levels=20, cmap=cmap, alpha=0.5)
            
            if hasattr(self, 'colorbar'):
                self.colorbar.remove()
            self.colorbar = self.fig.colorbar(contour, ax=self.ax, pad=0.02, fraction=0.046)
            self.colorbar.set_label('Received Power (dBm)', rotation=270, labelpad=20)
            
            self.ax.plot(img_center, img_center, 'r^', markersize=20, 
                        markeredgecolor='white', markeredgewidth=2, label='Transmitter')
            
            self.ax.axis('off')
            self.ax.legend(loc='upper right', fontsize=12)
            
        self.canvas.draw()


if __name__ == "__main__":
    print("="*60)
    print("VetRender - RF Propagation Tool")
    print("="*60)
    print("Debug logging enabled - all operations will be printed to console")
    print("You can copy/paste this output for troubleshooting")
    print("="*60 + "\n")
    
    root = tk.Tk()
    app = VetRender(root)
    root.mainloop() {old_freq} MHz -> {self.frequency} MHz")
            print(f"Height:    {old_height} m -> {self.height} m")
            
            self.status_var.set(f"Configuration updated - ERP: {self.erp} dBm, Freq: {self.frequency} MHz")
    
    def edit_antenna_info(self):
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
    
    def calculate_propagation(self):
        try:
            print(f"\n{'='*60}")
            print(f"CALCULATING PROPAGATION")
            print(f"{'='*60}")
            print(f"Transmitter Location: Lat={self.tx_lat:.6f}, Lon={self.tx_lon:.6f}")
            print(f"ERP: {self.erp} dBm")
            print(f"Frequency: