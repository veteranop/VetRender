"""
Dialog windows for VetRender GUI
"""
import tkinter as tk
import numpy as np
from tkinter import ttk, filedialog, messagebox

class TransmitterConfigDialog:
    """Dialog for editing transmitter configuration"""
    def __init__(self, parent, erp, freq, height, min_signal=-110):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Transmitter Configuration")
        self.dialog.geometry("400x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Height unit tracking (stored internally as meters)
        self.height_meters = height
        self.unit_var = tk.StringVar(value="meters")

        ttk.Label(self.dialog, text="ERP (dBm):").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.erp_var = tk.StringVar(value=str(erp))
        ttk.Entry(self.dialog, textvariable=self.erp_var, width=20).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.dialog, text="Frequency (MHz):").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.freq_var = tk.StringVar(value=str(freq))
        ttk.Entry(self.dialog, textvariable=self.freq_var, width=20).grid(row=1, column=1, padx=10, pady=10)

        # Antenna Height with unit selector
        height_frame = ttk.Frame(self.dialog)
        height_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W+tk.E)
        
        ttk.Label(height_frame, text="Antenna Height:").pack(side=tk.LEFT)
        
        self.height_var = tk.StringVar(value=str(height))
        height_entry = ttk.Entry(height_frame, textvariable=self.height_var, width=12)
        height_entry.pack(side=tk.LEFT, padx=(10, 5))
        
        # Unit selector
        unit_frame = ttk.Frame(height_frame)
        unit_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(unit_frame, text="meters", variable=self.unit_var, value="meters",
                       command=self.convert_height).pack(side=tk.LEFT)
        ttk.Radiobutton(unit_frame, text="feet", variable=self.unit_var, value="feet",
                       command=self.convert_height).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(self.dialog, text="Min Signal Level (dBm):").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        self.min_signal_var = tk.StringVar(value=str(min_signal))
        ttk.Entry(self.dialog, textvariable=self.min_signal_var, width=20).grid(row=3, column=1, padx=10, pady=10)
        ttk.Label(self.dialog, text="(Below this = no coverage)", font=('Arial', 8, 'italic'), foreground='gray').grid(row=4, column=0, columnspan=2, pady=(0, 5))

        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)
        
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
    
    def convert_height(self):
        """Convert height value when unit changes"""
        try:
            current_value = float(self.height_var.get())
            current_unit = self.unit_var.get()
            
            if current_unit == "meters":
                # Currently displaying meters, convert from feet
                new_value = current_value / 3.28084
            else:  # feet
                # Currently displaying feet, convert from meters  
                new_value = current_value * 3.28084
            
            self.height_var.set(f"{new_value:.2f}")
        except ValueError:
            pass  # Invalid input, ignore
        
    def ok(self):
        try:
            erp = float(self.erp_var.get())
            freq = float(self.freq_var.get())
            height_value = float(self.height_var.get())
            
            # Convert to meters if currently in feet
            if self.unit_var.get() == "feet":
                height_meters = height_value / 3.28084
            else:
                height_meters = height_value
            
            min_signal = float(self.min_signal_var.get())
            self.result = (erp, freq, height_meters, min_signal)
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values")
    
    def cancel(self):
        self.dialog.destroy()


class StationInfoDialog:
    """Dialog for editing station information"""
    def __init__(self, parent, callsign, tx_type, transmission_mode):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Station Information")
        self.dialog.geometry("400x350")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        ttk.Label(self.dialog, text="Station Callsign:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.callsign_var = tk.StringVar(value=callsign)
        ttk.Entry(self.dialog, textvariable=self.callsign_var, width=20).grid(row=0, column=1, padx=10, pady=10)

        ttk.Label(self.dialog, text="Transmitter Type:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.tx_type_var = tk.StringVar(value=tx_type)
        tx_type_combo = ttk.Combobox(self.dialog, textvariable=self.tx_type_var, width=18,
                                      values=['Broadcast FM', 'Broadcast AM', 'LPFM', 'HAM Radio',
                                              'Amateur Radio', 'Commercial', 'Public Safety',
                                              'Land Mobile', 'Point-to-Point', 'Other'])
        tx_type_combo.grid(row=1, column=1, padx=10, pady=10)

        ttk.Label(self.dialog, text="Transmission Mode:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.tx_mode_var = tk.StringVar(value=transmission_mode)
        tx_mode_combo = ttk.Combobox(self.dialog, textvariable=self.tx_mode_var, width=18,
                                      values=['FM', 'AM', 'SSB', 'C4FM', 'DMR', 'P25',
                                              'NXDN', 'D-STAR', 'Analog', 'Digital', 'Other'])
        tx_mode_combo.grid(row=2, column=1, padx=10, pady=10)

        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="OK", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)

        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def ok(self):
        self.result = (self.callsign_var.get(), self.tx_type_var.get(), self.tx_mode_var.get())
        self.dialog.destroy()

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
    def __init__(self, parent, existing_config=None):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("VetRender - Project Setup")
        self.dialog.geometry("1200x800")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.configure(bg='#2b2b2b')

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
        self.current_zoom = existing_config.get('zoom', 13) if existing_config else 13
        self.current_lat = existing_config.get('tx_lat', 43.4665) if existing_config else 43.4665
        self.current_lon = existing_config.get('tx_lon', -112.0340) if existing_config else -112.0340
        self.current_basemap = existing_config.get('basemap', 'Esri WorldImagery') if existing_config else 'Esri WorldImagery'

        # Header with title and action buttons
        header_frame = tk.Frame(self.dialog, bg='#1e1e1e', relief='flat')
        header_frame.pack(fill=tk.X)

        # Title section
        title_section = tk.Frame(header_frame, bg='#1e1e1e')
        title_section.pack(side=tk.LEFT, padx=20, pady=15)

        title_label = tk.Label(title_section, text="VetRender - Select Coverage Area",
                               font=('Segoe UI', 18, 'bold'), fg='#ffffff', bg='#1e1e1e')
        title_label.pack(anchor='w')

        subtitle_label = tk.Label(title_section,
                                 text="Navigate the map and define your RF propagation area",
                                 font=('Segoe UI', 10), fg='#a0a0a0', bg='#1e1e1e')
        subtitle_label.pack(anchor='w')

        # Action buttons section (right side of header)
        action_section = tk.Frame(header_frame, bg='#1e1e1e')
        action_section.pack(side=tk.RIGHT, padx=20, pady=15)

        # Set Area button
        set_btn = tk.Button(action_section, text="📍 Set This Area",
                           command=self.set_area,
                           font=('Segoe UI', 11, 'bold'),
                           fg='#ffffff', bg='#0078d4',
                           activebackground='#106ebe',
                           activeforeground='#ffffff',
                           relief='flat', bd=0,
                           padx=20, pady=10,
                           cursor='hand2')
        set_btn.pack(side=tk.LEFT, padx=5)

        # Download button
        self.download_btn = tk.Button(action_section, text="✓ Download & Continue",
                                     command=self.download_and_create,
                                     font=('Segoe UI', 11, 'bold'),
                                     fg='#ffffff', bg='#107c10',
                                     activebackground='#0e6b0e',
                                     activeforeground='#ffffff',
                                     relief='flat', bd=0,
                                     padx=20, pady=10,
                                     cursor='hand2',
                                     state='disabled')
        self.download_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = tk.Button(action_section, text="✕ Cancel",
                              command=self.cancel,
                              font=('Segoe UI', 10),
                              fg='#ffffff', bg='#6b6b6b',
                              activebackground='#5a5a5a',
                              activeforeground='#ffffff',
                              relief='flat', bd=0,
                              padx=15, pady=10,
                              cursor='hand2')
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Status bar below header
        status_bar = tk.Frame(self.dialog, bg='#323232', height=35)
        status_bar.pack(fill=tk.X)
        status_bar.pack_propagate(False)

        self.status_label = tk.Label(status_bar,
                                     text="  💡 Explore the map, then click 'Set This Area' when ready",
                                     font=('Segoe UI', 10), fg='#e0e0e0', bg='#323232',
                                     anchor='w')
        self.status_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Main content with map on left, controls on right
        content_frame = tk.Frame(self.dialog, bg='#2b2b2b')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Left: Map viewer
        map_container = tk.Frame(content_frame, bg='#1e1e1e', relief='solid', bd=1)
        map_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        map_header = tk.Frame(map_container, bg='#1e1e1e', height=30)
        map_header.pack(fill=tk.X)
        map_header.pack_propagate(False)

        tk.Label(map_header, text="🗺️  Map Viewer",
                font=('Segoe UI', 11, 'bold'), fg='#ffffff', bg='#1e1e1e').pack(side=tk.LEFT, padx=10, pady=5)

        tk.Label(map_header, text="Click & drag to pan  •  Scroll to zoom",
                font=('Segoe UI', 9), fg='#a0a0a0', bg='#1e1e1e').pack(side=tk.RIGHT, padx=10, pady=5)

        self.fig = Figure(figsize=(8, 8), dpi=85, facecolor='#1e1e1e')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=map_container)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Bind mouse events for panning
        self.drag_start = None
        self.canvas.mpl_connect('button_press_event', self.on_mouse_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_drag)
        self.canvas.mpl_connect('button_release_event', self.on_mouse_release)
        self.canvas.mpl_connect('scroll_event', self.on_scroll)

        # Right: Controls panel with modern styling
        control_panel = tk.Frame(content_frame, bg='#1e1e1e', width=320, relief='flat')
        control_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        control_panel.pack_propagate(False)

        # Create a scrollable frame for controls
        canvas_scroll = tk.Canvas(control_panel, bg='#1e1e1e', highlightthickness=0)
        scrollbar = ttk.Scrollbar(control_panel, orient="vertical", command=canvas_scroll.yview)
        scrollable_frame = tk.Frame(canvas_scroll, bg='#1e1e1e')

        scrollable_frame.bind("<Configure>",
                             lambda e: canvas_scroll.configure(scrollregion=canvas_scroll.bbox("all")))

        canvas_scroll.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_scroll.configure(yscrollcommand=scrollbar.set)

        canvas_scroll.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Station Information section
        self._add_section_header(scrollable_frame, "📡 Station Information")
        station_frame = tk.Frame(scrollable_frame, bg='#2b2b2b', relief='flat')
        station_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        self.callsign_var = tk.StringVar(value=existing_config.get('callsign', 'KDPI') if existing_config else 'KDPI')
        self._add_field(station_frame, "Callsign:", self.callsign_var, 0)

        self.freq_var = tk.StringVar(value=str(existing_config.get('frequency', 88.5) if existing_config else 88.5))
        self._add_field(station_frame, "Frequency (MHz):", self.freq_var, 1)

        self.tx_type_var = tk.StringVar(value=existing_config.get('tx_type', 'Broadcast FM') if existing_config else 'Broadcast FM')
        self._add_combo(station_frame, "TX Type:", self.tx_type_var,
                       ['Broadcast FM', 'Broadcast AM', 'LPFM', 'HAM Radio', 'Other'], 2)

        self.tx_mode_var = tk.StringVar(value=existing_config.get('transmission_mode', 'FM') if existing_config else 'FM')
        self._add_combo(station_frame, "TX Mode:", self.tx_mode_var,
                       ['FM', 'AM', 'SSB', 'C4FM', 'DMR', 'P25', 'Other'], 3)

        # Location section
        self._add_section_header(scrollable_frame, "📍 Transmitter Location")
        location_frame = tk.Frame(scrollable_frame, bg='#2b2b2b', relief='flat')
        location_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        self.lat_var = tk.StringVar(value=str(existing_config.get('tx_lat', 43.4665) if existing_config else 43.4665))
        self._add_field(location_frame, "Latitude:", self.lat_var, 0)

        self.lon_var = tk.StringVar(value=str(existing_config.get('tx_lon', -112.0340) if existing_config else -112.0340))
        self._add_field(location_frame, "Longitude:", self.lon_var, 1)

        self.height_var = tk.StringVar(value=str(existing_config.get('height', 30) if existing_config else 30))
        self._add_field(location_frame, "Height AGL (m):", self.height_var, 2)

        self.erp_var = tk.StringVar(value=str(existing_config.get('erp', 40) if existing_config else 40))
        self._add_field(location_frame, "ERP (dBm):", self.erp_var, 3)

        go_btn = tk.Button(location_frame, text="→ Go To Location",
                          command=self.go_to_location,
                          font=('Segoe UI', 9),
                          fg='#ffffff', bg='#0078d4',
                          activebackground='#106ebe',
                          relief='flat', bd=0,
                          padx=10, pady=6,
                          cursor='hand2')
        go_btn.grid(row=4, column=0, columnspan=2, pady=(10, 5), sticky='ew')

        # Zoom Level section
        self._add_section_header(scrollable_frame, "🔍 Zoom Level")
        zoom_frame = tk.Frame(scrollable_frame, bg='#2b2b2b', relief='flat')
        zoom_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        self.zoom_var = tk.StringVar(value="13")
        for i, (zoom, desc) in enumerate([
            ('10', '~300 km'), ('11', '~150 km'), ('12', '~75 km'), ('13', '~40 km'),
            ('14', '~20 km'), ('15', '~10 km'), ('16', '~5 km')
        ]):
            rb = tk.Radiobutton(zoom_frame, text=f" Zoom {zoom} ({desc})",
                              variable=self.zoom_var, value=zoom,
                              command=self.update_map,
                              font=('Segoe UI', 9), fg='#e0e0e0', bg='#2b2b2b',
                              selectcolor='#1e1e1e', activebackground='#2b2b2b',
                              activeforeground='#ffffff', cursor='hand2')
            rb.pack(anchor='w', pady=2)

        # Basemap section
        self._add_section_header(scrollable_frame, "🎨 Basemap Style")
        basemap_frame = tk.Frame(scrollable_frame, bg='#2b2b2b', relief='flat')
        basemap_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        self.basemap_var = tk.StringVar(value="Esri WorldImagery")
        basemap_combo = ttk.Combobox(basemap_frame, textvariable=self.basemap_var,
                                     values=list(MapHandler.BASEMAPS.keys()), state='readonly', width=28)
        basemap_combo.pack(fill=tk.X, padx=5, pady=5)
        basemap_combo.bind('<<ComboboxSelected>>', lambda e: self.update_map())

        # Coverage Distance section
        self._add_section_header(scrollable_frame, "📏 Coverage Distance")
        radius_frame = tk.Frame(scrollable_frame, bg='#2b2b2b', relief='flat')
        radius_frame.pack(fill=tk.X, padx=10, pady=(0, 15))

        self.radius_var = tk.StringVar(value="50")
        self._add_field(radius_frame, "Max Radius (km):", self.radius_var, 0)
        
        # Track if area has been set
        self.area_set = False

        # Load initial map
        self.update_map()

        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _add_section_header(self, parent, text):
        """Add a styled section header"""
        header = tk.Frame(parent, bg='#1e1e1e', height=35)
        header.pack(fill=tk.X, padx=10, pady=(10, 5))
        header.pack_propagate(False)
        tk.Label(header, text=text, font=('Segoe UI', 10, 'bold'),
                fg='#ffffff', bg='#1e1e1e').pack(side=tk.LEFT, padx=5, pady=8)

    def _add_field(self, parent, label_text, var, row):
        """Add a labeled entry field"""
        tk.Label(parent, text=label_text, font=('Segoe UI', 9),
                fg='#c0c0c0', bg='#2b2b2b').grid(row=row, column=0, sticky='w', padx=5, pady=5)
        entry = tk.Entry(parent, textvariable=var, font=('Segoe UI', 9),
                        bg='#3c3c3c', fg='#ffffff', insertbackground='#ffffff',
                        relief='flat', bd=0)
        entry.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
        parent.grid_columnconfigure(1, weight=1)

    def _add_combo(self, parent, label_text, var, values, row):
        """Add a labeled combobox"""
        tk.Label(parent, text=label_text, font=('Segoe UI', 9),
                fg='#c0c0c0', bg='#2b2b2b').grid(row=row, column=0, sticky='w', padx=5, pady=5)
        combo = ttk.Combobox(parent, textvariable=var, values=values,
                            state='readonly', font=('Segoe UI', 9))
        combo.grid(row=row, column=1, sticky='ew', padx=5, pady=5)
        parent.grid_columnconfigure(1, weight=1)

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
        if event.inaxes:
            current_zoom = int(self.zoom_var.get())
            # event.button is 'up' or 'down' in matplotlib
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
        self.download_btn.config(state='normal', bg='#107c10')

        # Update lat/lon to current view center
        self.current_lat = float(self.lat_var.get())
        self.current_lon = float(self.lon_var.get())

        self.status_label.config(text=f"  ✓ Area set! Click 'Download & Continue' to cache and proceed")
        print(f"Area set: Lat={self.current_lat:.4f}, Lon={self.current_lon:.4f}, Zoom={self.current_zoom}")
    
    def download_and_create(self):
        """Download map area and create project"""
        try:
            # Station info
            callsign = self.callsign_var.get()
            frequency = float(self.freq_var.get())
            tx_type = self.tx_type_var.get()
            tx_mode = self.tx_mode_var.get()

            # Location
            lat = float(self.lat_var.get())
            lon = float(self.lon_var.get())
            height = float(self.height_var.get())
            erp = float(self.erp_var.get())

            # Map settings
            zoom = int(self.zoom_var.get())
            basemap = self.basemap_var.get()
            radius = float(self.radius_var.get())

            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                messagebox.showerror("Error", "Invalid coordinates")
                return

            self.download_btn.config(state='disabled')
            self.status_label.config(text="Downloading and caching map area...")
            self.dialog.update()

            self.result = {
                'callsign': callsign,
                'frequency': frequency,
                'tx_type': tx_type,
                'transmission_mode': tx_mode,
                'tx_lat': lat,
                'tx_lon': lon,
                'height': height,
                'erp': erp,
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


class SetLocationDialog:
    """Dialog for precisely setting transmitter location by coordinates"""
    def __init__(self, parent, current_lat, current_lon):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Set Transmitter Location")
        self.dialog.geometry("400x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Instructions
        ttk.Label(self.dialog, text="Enter precise coordinates for transmitter location:",
                  font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky=tk.W)

        ttk.Label(self.dialog, text="(Decimal degrees format)",
                  font=('Arial', 8, 'italic'), foreground='gray').grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky=tk.W)

        # Latitude field
        ttk.Label(self.dialog, text="Latitude:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.lat_var = tk.StringVar(value=f"{current_lat:.6f}")
        lat_entry = ttk.Entry(self.dialog, textvariable=self.lat_var, width=25)
        lat_entry.grid(row=2, column=1, padx=10, pady=10)
        ttk.Label(self.dialog, text="(-90 to 90)",
                  font=('Arial', 8, 'italic'), foreground='gray').grid(row=3, column=1, pady=(0, 5), sticky=tk.W)

        # Longitude field
        ttk.Label(self.dialog, text="Longitude:").grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        self.lon_var = tk.StringVar(value=f"{current_lon:.6f}")
        lon_entry = ttk.Entry(self.dialog, textvariable=self.lon_var, width=25)
        lon_entry.grid(row=4, column=1, padx=10, pady=10)
        ttk.Label(self.dialog, text="(-180 to 180)",
                  font=('Arial', 8, 'italic'), foreground='gray').grid(row=5, column=1, pady=(0, 5), sticky=tk.W)

        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Set Location", command=self.ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)

        # Center on parent
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        # Focus on latitude field
        lat_entry.focus()
        lat_entry.select_range(0, tk.END)

    def ok(self):
        try:
            lat = float(self.lat_var.get())
            lon = float(self.lon_var.get())

            if not (-90 <= lat <= 90):
                messagebox.showerror("Error", "Latitude must be between -90 and 90")
                return

            if not (-180 <= lon <= 180):
                messagebox.showerror("Error", "Longitude must be between -180 and 180")
                return

            self.result = {'lat': lat, 'lon': lon}
            self.dialog.destroy()

        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric coordinates")

    def cancel(self):
        self.result = None
        self.dialog.destroy()


class PlotsManagerDialog:
    """Dialog for managing saved coverage plots"""
    def __init__(self, parent, saved_plots, main_window):
        self.saved_plots = saved_plots
        self.main_window = main_window

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Coverage Plots")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Header
        header_frame = ttk.Frame(self.dialog, padding="10")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text=f"Saved Coverage Plots ({len(saved_plots)})",
                 font=('Arial', 12, 'bold')).pack(anchor=tk.W)
        ttk.Label(header_frame, text="Click a plot to load it, or delete unwanted plots",
                 font=('Arial', 9), foreground='gray').pack(anchor=tk.W)

        # Plots list frame with scrollbar
        list_frame = ttk.Frame(self.dialog, padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Create scrollable listbox
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set,
                                   font=('Courier', 9), height=15)
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Populate listbox
        self.populate_listbox()

        # Selection event
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        # Details frame
        details_frame = ttk.LabelFrame(self.dialog, text="Plot Details", padding="10")
        details_frame.pack(fill=tk.X, padx=10, pady=5)

        self.details_text = tk.Text(details_frame, height=6, wrap=tk.WORD,
                                    font=('Courier', 9), state=tk.DISABLED)
        self.details_text.pack(fill=tk.X)

        # Buttons
        btn_frame = ttk.Frame(self.dialog, padding="10")
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Load Plot", command=self.load_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Delete Plot", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Close", command=self.close).pack(side=tk.RIGHT, padx=5)

        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def populate_listbox(self):
        """Populate the listbox with plot summaries"""
        self.listbox.delete(0, tk.END)

        for i, plot in enumerate(self.saved_plots):
            params = plot['parameters']
            terrain_str = "Terrain" if params.get('use_terrain', False) else "No terrain"

            # Format: timestamp | ERP | Freq | Height | Distance | Terrain
            line = f"{i+1:2d}. {plot['timestamp'][:19]} | {params['erp']:5.1f}dBm | {params['frequency']:6.1f}MHz | {params['height']:4.1f}m | {params['max_distance']:5.1f}km | {terrain_str}"
            self.listbox.insert(tk.END, line)

    def on_select(self, event):
        """Handle plot selection - show details"""
        selection = self.listbox.curselection()
        if not selection:
            return

        idx = selection[0]
        plot = self.saved_plots[idx]
        params = plot['parameters']

        # Format details
        details = f"Plot: {plot['name']}\n"
        details += f"Created: {plot['timestamp'][:19]}\n"
        details += f"Location: Lat {params['tx_lat']:.6f}, Lon {params['tx_lon']:.6f}\n"
        details += f"Parameters: {params['erp']:.1f} dBm ERP, {params['frequency']:.1f} MHz, {params['height']:.1f}m height\n"
        details += f"Coverage: {params['max_distance']:.1f} km radius, {params['resolution']} points resolution\n"
        details += f"Terrain: {'Enabled' if params.get('use_terrain', False) else 'Disabled'}, Pattern: {params.get('pattern_name', 'Unknown')}"

        # Display details
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.insert(1.0, details)
        self.details_text.config(state=tk.DISABLED)

    def load_selected(self):
        """Load the selected plot"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a plot to load")
            return

        idx = selection[0]
        success = self.main_window.load_plot_from_history(idx)

        if success:
            messagebox.showinfo("Plot Loaded", f"Coverage plot loaded successfully!")
            self.dialog.destroy()
        else:
            messagebox.showerror("Error", "Failed to load plot")

    def delete_selected(self):
        """Delete the selected plot"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a plot to delete")
            return

        idx = selection[0]
        plot_name = self.saved_plots[idx]['name']

        # Confirm deletion
        if messagebox.askyesno("Confirm Delete", f"Delete this plot?\n\n{plot_name}"):
            success = self.main_window.delete_plot_from_history(idx)

            if success:
                # Refresh list
                self.populate_listbox()

                # Clear details
                self.details_text.config(state=tk.NORMAL)
                self.details_text.delete(1.0, tk.END)
                self.details_text.config(state=tk.DISABLED)

                # Update count in header
                if len(self.saved_plots) == 0:
                    messagebox.showinfo("No Plots", "No more saved plots. Closing dialog.")
                    self.dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to delete plot")

    def close(self):
        """Close the dialog"""
        self.dialog.destroy()