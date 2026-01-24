"""
Dialog windows for Cellfire RF Studio GUI
"""
import tkinter as tk
import numpy as np
from tkinter import ttk, filedialog, messagebox
import requests
from bs4 import BeautifulSoup
import PyPDF2
import xml.etree.ElementTree as ET
import tempfile
import subprocess
import os
import math
import xml.etree.ElementTree as ET
import xml.etree.ElementTree as ET

class TransmitterConfigDialog:
    """Dialog for editing transmitter configuration"""
    def __init__(self, parent, erp, freq, height, rx_height=1.5, min_signal=-110):
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

        ttk.Label(self.dialog, text="Receiver Height (m):").grid(row=3, column=0, padx=10, pady=10, sticky=tk.W)
        self.rx_height_var = tk.StringVar(value=str(rx_height))
        ttk.Entry(self.dialog, textvariable=self.rx_height_var, width=20).grid(row=3, column=1, padx=10, pady=10)

        ttk.Label(self.dialog, text="Min Signal Level (dBm):").grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)
        self.min_signal_var = tk.StringVar(value=str(min_signal))
        ttk.Entry(self.dialog, textvariable=self.min_signal_var, width=20).grid(row=4, column=1, padx=10, pady=10)
        ttk.Label(self.dialog, text="(Below this = no coverage)", font=('Arial', 8, 'italic'), foreground='gray').grid(row=5, column=0, columnspan=2, pady=(0, 5))

        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=20)
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
            
            rx_height = float(self.rx_height_var.get())
            min_signal = float(self.min_signal_var.get())
            self.result = (erp, freq, height_meters, rx_height, min_signal)
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
        self.dialog.title("Cellfire RF Studio - Project Setup")
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

        title_label = tk.Label(title_section, text="Cellfire RF Studio - Select Coverage Area",
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

        self.rx_height_var = tk.StringVar(value=str(existing_config.get('rx_height', 1.5) if existing_config else 1.5))
        self._add_field(location_frame, "Receiver Height (m):", self.rx_height_var, 3)

        self.erp_var = tk.StringVar(value=str(existing_config.get('erp', 40) if existing_config else 40))
        self._add_field(location_frame, "ERP (dBm):", self.erp_var, 4)

        go_btn = tk.Button(location_frame, text="→ Go To Location",
                          command=self.go_to_location,
                          font=('Segoe UI', 9),
                          fg='#ffffff', bg='#0078d4',
                          activebackground='#106ebe',
                          relief='flat', bd=0,
                          padx=10, pady=6,
                          cursor='hand2')
        go_btn.grid(row=5, column=0, columnspan=2, pady=(10, 5), sticky='ew')

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
            rx_height = float(self.rx_height_var.get())
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
                'rx_height': rx_height,
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
        if messagebox.askyesno("Exit", "Exit Cellfire RF Studio?"):
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


class AntennaImportDialog:
    """Dialog for importing antenna patterns from websites or PDFs using LLM"""

    def __init__(self, parent, on_import_callback):
        from debug_logger import get_logger
        self.logger = get_logger()
        self.logger.log("="*80)
        self.logger.log("AI ANTENNA IMPORT DIALOG OPENED")
        self.logger.log("="*80)
        
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Import Antenna Pattern")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.on_import_callback = on_import_callback

        # URL input
        ttk.Label(self.dialog, text="Antenna Website URL:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        self.url_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.url_var, width=40).grid(row=0, column=1, padx=10, pady=10)

        # Or PDF file
        ttk.Label(self.dialog, text="Or PDF Spec Sheet:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.pdf_path_var = tk.StringVar()
        pdf_frame = ttk.Frame(self.dialog)
        pdf_frame.grid(row=1, column=1, padx=10, pady=10, sticky=tk.W+tk.E)
        ttk.Entry(pdf_frame, textvariable=self.pdf_path_var, width=30).pack(side=tk.LEFT)
        ttk.Button(pdf_frame, text="Browse", command=self.browse_pdf).pack(side=tk.LEFT, padx=(5,0))

        # Process button
        ttk.Button(self.dialog, text="Process and Import", command=self.process).grid(row=2, column=0, columnspan=2, pady=20)

        # Status label
        self.status_var = tk.StringVar(value="")
        ttk.Label(self.dialog, textvariable=self.status_var).grid(row=3, column=0, columnspan=2, padx=10, pady=5)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT)

    def browse_pdf(self):
        filepath = filedialog.askopenfilename(
            title="Select PDF Spec Sheet",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filepath:
            self.pdf_path_var.set(filepath)
            self.logger.log(f"PDF selected: {filepath}")

    def process(self):
        url = self.url_var.get().strip()
        pdf_path = self.pdf_path_var.get().strip()

        self.logger.log("-"*80)
        self.logger.log("AI ANTENNA IMPORT - PROCESSING STARTED")
        self.logger.log(f"URL: {url if url else '(none)'}")
        self.logger.log(f"PDF: {pdf_path if pdf_path else '(none)'}")
        self.logger.log("-"*80)

        if not url and not pdf_path:
            self.logger.log("ERROR: No input provided")
            messagebox.showerror("Input Required", "Please provide a URL or select a PDF file.")
            return

        self.status_var.set("Processing... Please wait.")
        self.dialog.update()

        try:
            # Placeholder for processing logic
            # Extract text, send to LLM, generate XML
            xml_content, text = self.generate_xml_from_input(url, pdf_path)
            if xml_content:
                self.result = xml_content
                # Extract metadata for library fields
                self.metadata = self.extract_metadata(text)
                self.status_var.set("XML generated successfully. Click OK to import.")
                self.logger.log("SUCCESS: XML generated successfully")
                self.logger.log(f"XML length: {len(xml_content)} characters")
                self.logger.log(f"Extracted metadata: {self.metadata}")
            else:
                self.status_var.set("Failed to generate XML. Check inputs and try again.")
                self.logger.log("ERROR: XML generation failed (returned None)")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            self.logger.log(f"ERROR: Exception during processing: {str(e)}")
            import traceback
            self.logger.log(f"Traceback: {traceback.format_exc()}")

    def generate_xml_from_input(self, url, pdf_path):
        """Extract text from URL or PDF, then use LLM to generate XML"""
        text = ""
        if url:
            self.logger.log(f"Attempting to scrape URL: {url}")
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                self.logger.log(f"HTTP Status: {response.status_code}")
                self.logger.log(f"Content length: {len(response.content)} bytes")
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text()
                self.logger.log(f"Extracted text length: {len(text)} characters")
                self.logger.log(f"Text preview: {text[:200]}...")
            except Exception as e:
                self.logger.log(f"ERROR scraping website: {e}")
                raise Exception(f"Failed to scrape website: {e}")
        elif pdf_path:
            self.logger.log(f"Attempting to read PDF: {pdf_path}")
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    page_count = len(reader.pages)
                    self.logger.log(f"PDF has {page_count} pages")
                    for i, page in enumerate(reader.pages):
                        page_text = page.extract_text()
                        text += page_text + "\n"
                        self.logger.log(f"Page {i+1}: extracted {len(page_text)} characters")
                self.logger.log(f"Total extracted text length: {len(text)} characters")
                self.logger.log(f"Text preview: {text[:200]}...")
            except Exception as e:
                self.logger.log(f"ERROR reading PDF: {e}")
                raise Exception(f"Failed to read PDF: {e}")

        # Analyze images for radiation pattern data
        image_pattern_data = {}
        if pdf_path:
            self.logger.log("Analyzing images for radiation pattern data...")
            image_pattern_data = self.analyze_images_from_pdf(pdf_path)
            if image_pattern_data:
                self.logger.log(f"Found pattern data from images: {list(image_pattern_data.keys())}")
            else:
                self.logger.log("No pattern data found in images")

        if not text.strip() and not image_pattern_data:
            self.logger.log("ERROR: No text or pattern data extracted from source")
            raise Exception("No text or pattern data extracted from the source.")

        # Check for azimuth table in text
        azimuth_pairs = self.parse_azimuth_table(text)
        if azimuth_pairs:
            self.logger.log(f"Found azimuth table with {len(azimuth_pairs)} points in text")
            # Convert relative field to dB gains
            if azimuth_pairs:
                values = [p[1] for p in azimuth_pairs]
                max_value = max(values)
                db_pairs = []
                for angle, value in azimuth_pairs:
                    if max_value > 0 and value > 0:
                        gain_db = 20 * math.log10(value / max_value)
                        db_pairs.append((angle, round(gain_db, 2)))
                    else:
                        db_pairs.append((angle, -100.0))
                image_pattern_data['azimuth'] = db_pairs
                self.logger.log(f"Converted to dB gains: max {max_value}, range {min(db_pairs, key=lambda x: x[1])[1]} to {max(db_pairs, key=lambda x: x[1])[1]} dB")

        # Check if this is an omnidirectional antenna - if so, use standard pattern
        if 'omni' in text.lower():
            self.logger.log("Detected omnidirectional antenna - using standard uniform azimuth pattern")
            xml = '''<antenna>
    <type>omnidirectional</type>
    <bays>1</bays>
    <azimuth>
        <point angle="0" gain="0"/>
        <point angle="30" gain="0"/>
        <point angle="60" gain="0"/>
        <point angle="90" gain="0"/>
        <point angle="120" gain="0"/>
        <point angle="150" gain="0"/>
        <point angle="180" gain="0"/>
        <point angle="210" gain="0"/>
        <point angle="240" gain="0"/>
        <point angle="270" gain="0"/>
        <point angle="300" gain="0"/>
        <point angle="330" gain="0"/>
        <point angle="360" gain="0"/>
    </azimuth>
    <elevation>
        <point angle="0" gain="0"/>
    </elevation>
</antenna>'''
            return xml, text

        # Check if we have pattern data from images
        if image_pattern_data:
            self.logger.log("Generating XML from image-extracted pattern data...")
            xml = self.generate_xml_from_image_data(image_pattern_data, text)
            return xml, text

        # Now send to LLM
        self.logger.log("Sending text to LLM for XML generation...")
        xml = self.query_llm_for_xml(text)

        # If no pattern found and it's a dipole, generate standard single-bay dipole pattern
        if xml.strip() == "NO_PATTERN_DATA_FOUND" and 'dipole' in text.lower():
            self.logger.log("No pattern data found, generating standard single-bay dipole pattern...")
            metadata = self.extract_metadata(text)
            xml = f'''<antenna>
    <type>{metadata.get('type', 'Dipole')}</type>
    <bays>1</bays>
    <azimuth>
        <point angle="0" gain="0"/>
        <point angle="30" gain="0"/>
        <point angle="60" gain="0"/>
        <point angle="90" gain="0"/>
        <point angle="120" gain="0"/>
        <point angle="150" gain="0"/>
        <point angle="180" gain="0"/>
        <point angle="210" gain="0"/>
        <point angle="240" gain="0"/>
        <point angle="270" gain="0"/>
        <point angle="300" gain="0"/>
        <point angle="330" gain="0"/>
        <point angle="360" gain="0"/>
    </azimuth>
    <elevation>
        <point angle="0" gain="0"/>
    </elevation>
</antenna>'''

        return xml, text

    def validate_antenna_pattern(self, xml):
        """Validate that antenna pattern looks physically realistic, not hallucinated"""
        try:
            root = ET.fromstring(xml)
            self.logger.log("VALIDATION: Checking if pattern data looks realistic...")
            
            # Check azimuth section
            azimuth = root.find('azimuth')
            if azimuth is None:
                return False, "No azimuth section found"
            
            points = azimuth.findall('point')
            if len(points) < 3:
                return False, f"Too few azimuth points ({len(points)}), pattern likely incomplete"
            
            gains = []
            angles = []
            for point in points:
                try:
                    angle = float(point.get('angle', 0))
                    gain = float(point.get('gain', 0))
                    angles.append(angle)
                    gains.append(gain)
                except (ValueError, TypeError):
                    return False, "Invalid angle or gain values in pattern"
            
            # RED FLAG 1: All gains are positive (physically impossible for most antennas)
            positive_count = sum(1 for g in gains if g > 0)
            if positive_count > len(gains) * 0.8:  # More than 80% positive
                self.logger.log(f"VALIDATION FAIL: {positive_count}/{len(gains)} gains are positive - likely hallucinated")
                return False, "Pattern has mostly positive gains - this is physically unrealistic. LLM likely invented data."
            
            # RED FLAG 2: Gains increase perfectly linearly (like 0, 10, 20, 30...)
            if len(gains) >= 4:
                differences = [gains[i+1] - gains[i] for i in range(len(gains)-1)]
                # Check if all differences are very similar (linear pattern)
                if len(set(differences)) <= 2 and all(d == differences[0] for d in differences):
                    self.logger.log(f"VALIDATION FAIL: Gains increase linearly: {gains[:10]}...")
                    return False, "Pattern shows perfectly linear gain progression - this is not real data. LLM invented a fake pattern."
            
            # RED FLAG 3: Too few unique values (like just repeating 0, 10, 20)
            unique_gains = len(set(gains))
            if unique_gains < len(gains) * 0.3:  # Less than 30% unique
                self.logger.log(f"VALIDATION FAIL: Only {unique_gains} unique values in {len(gains)} points")
                return False, f"Only {unique_gains} unique gain values - pattern looks artificial or incomplete"
            
            # RED FLAG 4: Gains are impossibly high (>20 dBi for omni, >30 dBi for directional)
            max_gain = max(gains)
            if max_gain > 30:
                self.logger.log(f"VALIDATION FAIL: Maximum gain {max_gain} dBi is unrealistic")
                return False, f"Maximum gain {max_gain} dBi exceeds realistic limits for antennas"
            
            # PASS: Pattern looks reasonable
            self.logger.log(f"VALIDATION PASS: Pattern has {len(gains)} points, {unique_gains} unique values")
            self.logger.log(f"  Gain range: {min(gains):.1f} to {max(gains):.1f} dBi")
            self.logger.log(f"  Positive gains: {positive_count}/{len(gains)}")
            return True, "Pattern looks physically realistic"
            
        except Exception as e:
            self.logger.log(f"VALIDATION ERROR: {e}")
            return False, f"Validation error: {e}"

    def extract_metadata(self, text):
        """Extract metadata fields from antenna text for library form"""
        import re

        metadata = {
            'name': 'Imported Antenna',
            'manufacturer': '',
            'part_number': '',
            'gain': '0',
            'band': '',
            'freq_range': '',
            'type': 'Omni',
            'notes': ''
        }

        text_lower = text.lower()

        # Extract name - look for product names
        name_patterns = [
            r'product\s+(?:data\s+)?sheet\s+([\w\s\-]+)',
            r'([\w\s\-]+)\s+antenna',
            r'model\s+([\w\s\-]+)',
        ]
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up the name: remove extra spaces, special chars
                name = re.sub(r'\s+', ' ', name)  # Multiple spaces to single
                name = re.sub(r'[^\w\s\-]', '', name)  # Remove non-word chars except space and dash
                name = name.strip()
                if len(name) > 3 and len(name) < 100:  # Reasonable length
                    metadata['name'] = name
                    break

        # Extract manufacturer
        manufacturer_patterns = [
            r'by\s+([\w\s]+)',
            r'manufacturer\s*:\s*([\w\s]+)',
            r'([\w\s]+)\s+corporation',
            r'([\w\s]+)\s+inc',
            r'([\w\s]+)\s+ltd',
        ]
        for pattern in manufacturer_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                manufacturer = match.group(1).strip()
                if len(manufacturer) > 2:
                    metadata['manufacturer'] = manufacturer
                    break

        # Extract part number
        part_patterns = [
            r'part\s+(?:number|no\.?)\s*:\s*([\w\-]+)',
            r'model\s+(?:number|no\.?)\s*:\s*([\w\-]+)',
            r'p/n\s*:\s*([\w\-]+)',
            r'([\w\-]+(?:-\d+)+)',  # Common part number format
        ]
        for pattern in part_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                part = match.group(1).strip()
                if len(part) > 2:
                    metadata['part_number'] = part
                    break

        # Extract gain (handle dBi, dBd, dbi, dbd)
        gain_match = re.search(r'(\d+(?:\.\d+)?)\s*(dBd|dBi|dbi|dbd)\b', text, re.IGNORECASE)
        if gain_match:
            gain_value = float(gain_match.group(1))
            unit = gain_match.group(2).lower()
            if unit == 'dbd':  # dBd, convert to dBi
                gain_value += 2.15
            metadata['gain'] = str(round(gain_value, 2))

        # Extract number of bays
        bays_match = re.search(r'(\d+)\s*bays?|(\d+)\s*dipoles?', text, re.IGNORECASE)
        if bays_match:
            bays = int(bays_match.group(1) or bays_match.group(2))
            if 1 <= bays <= 10:  # Reasonable range
                metadata['bays'] = bays
        # Default to 1 if not found
        if 'bays' not in metadata:
            metadata['bays'] = 1

        # Special handling for relative field antennas
        if 'relative field' in text_lower and metadata.get('type') == 'Directional':
            # Assume dipole reference, 0 dBd = 2.15 dBi
            if metadata['gain'] == '0':
                metadata['gain'] = '2.15'

        # Extract frequency range
        freq_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*mhz',
            r'(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*mhz',
            r'(\d+(?:\.\d+)?)\s*mhz\s*(?:to|-)\s*(\d+(?:\.\d+)?)\s*mhz',
        ]
        for pattern in freq_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                start = match.group(1)
                end = match.group(2)
                metadata['freq_range'] = f"{start}-{end} MHz"
                break

        # Extract band
        if 'vhf' in text_lower:
            metadata['band'] = 'VHF'
        elif 'uhf' in text_lower:
            metadata['band'] = 'UHF'
        elif 'fm' in text_lower:
            metadata['band'] = 'FM'
        elif 'tv' in text_lower:
            metadata['band'] = 'TV'
        elif re.search(r'\d+(?:\.\d+)?\s*ghz', text_lower):
            metadata['band'] = 'Microwave'
        elif re.search(r'\d+(?:\.\d+)?\s*mhz', text_lower):
            metadata['band'] = 'RF'

        # Determine type
        if 'omni' in text_lower or 'omnidirectional' in text_lower:
            metadata['type'] = 'Omni'
        elif 'directional' in text_lower or 'panel' in text_lower:
            metadata['type'] = 'Directional'
        elif 'yagi' in text_lower:
            metadata['type'] = 'Yagi'
        elif 'sector' in text_lower:
            metadata['type'] = 'Sector'
        elif 'dipole' in text_lower:
            metadata['type'] = 'Dipole'
        elif 'sidemount' in text_lower or 'broadcast' in text_lower:
            metadata['type'] = 'Directional'  # Assume directional for broadcast antennas

        # Create summary notes
        notes_parts = []
        if metadata['manufacturer']:
            notes_parts.append(f"Manufacturer: {metadata['manufacturer']}")
        if metadata['part_number']:
            notes_parts.append(f"Part Number: {metadata['part_number']}")
        if metadata['gain'] != '0':
            notes_parts.append(f"Gain: {metadata['gain']} dBi")
        if metadata['band']:
            notes_parts.append(f"Band: {metadata['band']}")
        if metadata['freq_range']:
            notes_parts.append(f"Frequency Range: {metadata['freq_range']}")
        if 'omni' in text_lower:
            notes_parts.append("Omnidirectional antenna")
        elif 'directional' in text_lower:
            notes_parts.append("Directional antenna")

        # Add first few lines of description
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        description = ' '.join(lines[:3])[:200]  # First 200 chars of first 3 lines
        if description:
            notes_parts.append(f"Description: {description}...")

        metadata['notes'] = '\n'.join(notes_parts)

        return metadata

    def analyze_images_from_pdf(self, pdf_path):
        """Extract and analyze images from PDF for radiation pattern data"""
        pattern_data = {}

        try:
            # Try to extract images using pdfimages (from poppler-utils)
            with tempfile.TemporaryDirectory() as temp_dir:
                # Extract images
                result = subprocess.run([
                    'pdfimages', '-all', pdf_path, os.path.join(temp_dir, 'image')
                ], capture_output=True, text=True)

                if result.returncode != 0:
                    self.logger.log(f"pdfimages failed: {result.stderr}")
                    return pattern_data

                # Find extracted images
                image_files = [f for f in os.listdir(temp_dir) if f.startswith('image')]

                for img_file in image_files:
                    img_path = os.path.join(temp_dir, img_file)

                    # Use OCR to extract text from image
                    try:
                        import pytesseract
                        from PIL import Image

                        image = Image.open(img_path)
                        ocr_text = pytesseract.image_to_string(image)
                        self.logger.log(f"OCR result for {img_file}: {ocr_text[:200]}...")

                        # Look for radiation pattern indicators
                        if any(keyword in ocr_text.lower() for keyword in ['radiation', 'pattern', 'azimuth', 'elevation']):
                            self.logger.log(f"Found radiation pattern keywords in {img_file}")
                            # Parse for angle/gain data
                            angle_gain_pairs = self.extract_angle_gain_from_ocr(ocr_text)
                            self.logger.log(f"Extracted {len(angle_gain_pairs)} angle/gain pairs from {img_file}")
                            if angle_gain_pairs:
                                if 'azimuth' in ocr_text.lower():
                                    pattern_data['azimuth'] = angle_gain_pairs
                                elif 'elevation' in ocr_text.lower():
                                    pattern_data['elevation'] = angle_gain_pairs
                                else:
                                    # Assume azimuth if not specified
                                    pattern_data['azimuth'] = angle_gain_pairs
                        else:
                            self.logger.log(f"No radiation pattern keywords found in {img_file}")

                    except ImportError:
                        self.logger.log("OCR libraries not available - skipping image analysis")
                    except Exception as e:
                        self.logger.log(f"Error analyzing image {img_file}: {e}")

        except Exception as e:
            self.logger.log(f"Error in image analysis: {e}")

        return pattern_data

    def extract_angle_gain_from_ocr(self, ocr_text):
        """Extract angle/gain pairs from OCR text"""
        import re
        pairs = []

        # Look for patterns like "0°: 0 dBi", "45° -3.5", etc.
        patterns = [
            r'(\d+)\s*°?\s*:\s*([-\d.]+)\s*db',
            r'(\d+)\s*°?\s*-\s*([-\d.]+)',
            r'angle\s*(\d+)\s*gain\s*([-\d.]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, ocr_text, re.IGNORECASE)
            for match in matches:
                try:
                    angle = float(match[0])
                    gain = float(match[1])
                    pairs.append((angle, gain))
                except ValueError:
                    continue

        return pairs

    def parse_azimuth_table(self, text):
        """Parse azimuth table from text for relative field data"""
        import re
        pairs = []

        # Look for AZIMUTH FIELD followed by angle value lines
        azimuth_match = re.search(r'AZIMUTH\s+FIELD(.*?)(?:\n\n|\n[A-Z]|$)', text, re.DOTALL | re.IGNORECASE)
        if azimuth_match:
            table_text = azimuth_match.group(1)
            # Find lines with angle space value
            lines = table_text.split('\n')
            for line in lines:
                line = line.strip()
                match = re.match(r'(\d+)\s+([\d.]+)', line)
                if match:
                    angle = int(match.group(1))
                    value = float(match.group(2))
                    pairs.append((angle, value))

        return pairs

    def generate_xml_from_image_data(self, pattern_data, text):
        """Generate XML antenna pattern from OCR-extracted data"""
        # Extract metadata first
        metadata = self.extract_metadata(text)

        xml_parts = ['<antenna>']
        xml_parts.append(f'<type>{metadata.get("type", "Directional")}</type>')
        xml_parts.append(f'<bays>{metadata.get("bays", 1)}</bays>')

        # Add azimuth pattern
        if 'azimuth' in pattern_data:
            xml_parts.append('<azimuth>')
            for angle, gain in pattern_data['azimuth']:
                xml_parts.append(f'<point angle="{angle}" gain="{gain}"/>')
            xml_parts.append('</azimuth>')
        else:
            # Default azimuth
            xml_parts.append('<azimuth>')
            xml_parts.append('<point angle="0" gain="0"/>')
            xml_parts.append('<point angle="90" gain="0"/>')
            xml_parts.append('<point angle="180" gain="0"/>')
            xml_parts.append('<point angle="270" gain="0"/>')
            xml_parts.append('</azimuth>')

        # Add elevation pattern
        if 'elevation' in pattern_data:
            xml_parts.append('<elevation>')
            for angle, gain in pattern_data['elevation']:
                xml_parts.append(f'<point angle="{angle}" gain="{gain}"/>')
            xml_parts.append('</elevation>')
        else:
            # Default elevation
            xml_parts.append('<elevation>')
            xml_parts.append('<point angle="0" gain="0"/>')
            xml_parts.append('</elevation>')

        xml_parts.append('</antenna>')
        return '\n'.join(xml_parts)

    def query_llm_for_xml(self, text):
        """Query Ollama LLM to generate XML from text with improved prompting and validation"""
        text_to_send = text[:4000]  # Limit text length
        self.logger.log(f"Preparing LLM prompt with {len(text_to_send)} characters")
        
        # IMPROVED PROMPT: Much more explicit about what real data looks like vs fake data
        prompt = f"""
Extract REAL antenna pattern data from the PDF/website text below. Your task is to find ACTUAL numerical data, not to invent it.

CRITICAL RULES - READ CAREFULLY:
1. ONLY extract data if you find ACTUAL gain values at specific angles in the text
2. DO NOT make up, invent, or hallucinate pattern data
3. If you cannot find specific numerical pattern data, respond EXACTLY with: NO_PATTERN_DATA_FOUND

Real antenna pattern data looks like:
- Tables with "Angle" and "Gain" columns
- Charts showing azimuth or elevation patterns (NOT Smith charts - those are for impedance)
- Text like "At 0° = 0 dBi, at 45° = -2.1 dBi, at 90° = -3.5 dBi"
- Numerical data in degrees and dBi/dBd units
- Relative field values: tables like "0 0.91" where numbers are normalized field strength

For relative field data:
- Find the maximum value in the table
- Convert each value to dB: gain_dB = 20 * log10(value / max_value)
- This gives gains relative to the maximum (0 dB at peak direction)

Note: Smith charts show impedance/reflection coefficient data for matching, not radiation patterns. If you see Smith chart references, ignore them and look elsewhere in the document for gain vs angle data.

What real antenna gains look like:
- Maximum gain is usually 0 dBi (reference point)
- Other angles have NEGATIVE gains like -1.5, -3.2, -10.5, -20.0 dBi
- Gains are typically between 0 and -30 dBi
- Values vary somewhat irregularly (not perfectly linear)

EXAMPLES OF FAKE DATA (DO NOT DO THIS):
❌ <point angle="0" gain="0"/>
   <point angle="10" gain="10"/>
   <point angle="20" gain="20"/>
   ← This is WRONG: gains increase linearly and are positive

❌ <point angle="0" gain="5"/>
   <point angle="30" gain="5"/>
   <point angle="60" gain="5"/>
   ← This is WRONG: all same value, too simple

EXAMPLES OF REAL DATA (DO THIS):
✓ <point angle="0" gain="0"/>
   <point angle="30" gain="-1.2"/>
   <point angle="60" gain="-2.8"/>
   <point angle="90" gain="-4.1"/>
   ← This is RIGHT: realistic variation, mostly negative

SPECIAL CASE FOR OMNIDIRECTIONAL ANTENNAS:
- If the antenna is omnidirectional, azimuth gain should be CONSTANT (same value) at all angles, typically 0 dBi
- Example for omni: <point angle="0" gain="0"/> <point angle="90" gain="0"/> <point angle="180" gain="0"/> etc.

XML Format Requirements:
- ONE ROOT ELEMENT ONLY: <antenna> ... </antenna> (do not output multiple roots)
- Antenna type: <type>directional</type> or <type>omnidirectional</type> (based on text, default to directional for broadcast antennas)
- Number of bays: <bays>N</bays> where N is number found in text (default to 1 if not specified or unclear)
- Azimuth section: <azimuth> with child <point angle="X" gain="Y"/> elements
- Elevation section: <elevation> with child <point angle="X" gain="Y"/> elements
- Angles: 0 to 360 for azimuth, -90 to 90 for elevation
- If no elevation data found, use: <point angle="0" gain="0"/>

OUTPUT FORMAT:
- Output ONLY the XML
- NO markdown, NO code blocks (```), NO backticks, NO extra text
- Start with <antenna> and end with </antenna>
- OR if no pattern data exists, output exactly: NO_PATTERN_DATA_FOUND

Text to analyze:
{text_to_send}
"""

        try:
            self.logger.log("Connecting to Ollama at http://localhost:11434...")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:1b",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            response.raise_for_status()
            self.logger.log(f"Ollama response status: {response.status_code}")
            
            result = response.json()
            self.logger.log(f"LLM response keys: {result.keys()}")
            xml = result['response'].strip()
            self.logger.log(f"LLM generated response length: {len(xml)} characters")
            self.logger.log(f"Response preview: {xml[:300]}...")
            
            # Check if LLM said it couldn't find pattern data
            if "NO_PATTERN_DATA_FOUND" in xml or "no pattern data" in xml.lower():
                self.logger.log("LLM reported: No pattern data found in source")
                raise Exception("LLM could not find antenna pattern data in the provided text. The document may not contain numerical pattern data.")
            
            # Strip markdown code blocks if present (```xml or ```)
            if xml.startswith('```'):
                self.logger.log("Detected markdown code blocks, stripping...")
                # Remove opening code block
                lines = xml.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]  # Remove first line
                # Remove closing code block
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]  # Remove last line
                xml = '\n'.join(lines).strip()
                self.logger.log(f"After stripping: {xml[:300]}...")
            
            # Basic validation - check if XML contains antenna tags
            # Strip XML declaration if present
            xml_content = xml
            if xml_content.startswith('<?xml'):
                # Find the end of XML declaration and strip it
                decl_end = xml_content.find('?>') 
                if decl_end != -1:
                    xml_content = xml_content[decl_end + 2:].strip()
            
            if not ('<antenna>' in xml_content or '<antenna ' in xml_content):
                self.logger.log("ERROR: XML does not contain antenna element")
                self.logger.log(f"XML starts with: {xml[:50]}")
                self.logger.log(f"XML ends with: {xml[-50:]}")
                raise Exception("LLM did not return valid XML format with antenna element.")
            
            # Parse to ensure valid XML
            try:
                ET.fromstring(xml)
                self.logger.log("SUCCESS: XML is valid and parseable")
            except ET.ParseError as e:
                self.logger.log(f"ERROR: XML parse failed: {e}")
                self.logger.log(f"Full XML:\n{xml}")
                raise Exception(f"Generated XML is invalid: {e}")
            
            # NEW: Validate that pattern looks realistic
            is_valid, validation_msg = self.validate_antenna_pattern(xml)
            if not is_valid:
                self.logger.log(f"PATTERN VALIDATION FAILED: {validation_msg}")
                raise Exception(f"Generated pattern failed validation: {validation_msg}")
            
            self.logger.log(f"PATTERN VALIDATION PASSED: {validation_msg}")
            return xml
            
        except requests.exceptions.RequestException as e:
            self.logger.log(f"ERROR: Connection to Ollama failed: {e}")
            raise Exception(f"Failed to connect to Ollama. Ensure Ollama is running: {e}")
        except Exception as e:
            self.logger.log(f"ERROR: LLM processing exception: {e}")
            raise Exception(f"LLM processing failed: {e}")

    def ok(self):
        if self.result:
            self.logger.log("User clicked OK - importing antenna pattern")
            self.on_import_callback(self.result, getattr(self, 'metadata', {}))
        else:
            self.logger.log("User clicked OK but no XML result to import")
            self.on_import_callback(None, {})
        self.logger.log("="*80)
        self.logger.log("AI ANTENNA IMPORT DIALOG CLOSED")
        self.logger.log("="*80)
        self.dialog.destroy()

    def cancel(self):
        self.logger.log("User cancelled antenna import")
        self.logger.log("="*80)
        self.logger.log("AI ANTENNA IMPORT DIALOG CLOSED (CANCELLED)")
        self.logger.log("="*80)
        self.dialog.destroy()


class AntennaMetadataDialog:
    """Dialog for entering antenna metadata when saving to library"""

    def __init__(self, parent, default_name="Imported Antenna", initial_values=None):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Save Antenna to Library")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Instructions
        ttk.Label(self.dialog, text="Enter antenna details:", 
                 font=('Arial', 10, 'bold')).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)
        
        # Antenna Name (required)
        ttk.Label(self.dialog, text="*Antenna Name:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.name_var = tk.StringVar(value=default_name)
        ttk.Entry(self.dialog, textvariable=self.name_var, width=40).grid(row=1, column=1, padx=10, pady=5)

        # Manufacturer
        ttk.Label(self.dialog, text="Manufacturer:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.manufacturer_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.manufacturer_var, width=40).grid(row=2, column=1, padx=10, pady=5)

        # Part Number
        ttk.Label(self.dialog, text="Part Number:").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        self.part_number_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.part_number_var, width=40).grid(row=3, column=1, padx=10, pady=5)

        # Gain
        ttk.Label(self.dialog, text="Gain (dBi):").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        self.gain_var = tk.StringVar(value="0")
        ttk.Entry(self.dialog, textvariable=self.gain_var, width=40).grid(row=4, column=1, padx=10, pady=5)

        # Band
        ttk.Label(self.dialog, text="Band:").grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
        self.band_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.band_var, width=40).grid(row=5, column=1, padx=10, pady=5)
        ttk.Label(self.dialog, text="(e.g., VHF, UHF, 700 MHz)", font=('Arial', 8)).grid(row=5, column=1, padx=10, sticky=tk.E)

        # Frequency Range
        ttk.Label(self.dialog, text="Frequency Range:").grid(row=6, column=0, padx=10, pady=5, sticky=tk.W)
        self.freq_range_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.freq_range_var, width=40).grid(row=6, column=1, padx=10, pady=5)
        ttk.Label(self.dialog, text="(e.g., 746-869 MHz)", font=('Arial', 8)).grid(row=6, column=1, padx=10, sticky=tk.E)

        # Type
        ttk.Label(self.dialog, text="Type:").grid(row=7, column=0, padx=10, pady=5, sticky=tk.W)
        self.type_var = tk.StringVar(value="Omni")
        type_combo = ttk.Combobox(self.dialog, textvariable=self.type_var, width=37)
        type_combo['values'] = ('Omni', 'Directional', 'Yagi', 'Panel', 'Sector', 'Dipole', 'Other')
        type_combo.grid(row=7, column=1, padx=10, pady=5)

        # Notes
        ttk.Label(self.dialog, text="Notes:").grid(row=8, column=0, padx=10, pady=5, sticky=tk.W+tk.N)
        self.notes_text = tk.Text(self.dialog, width=40, height=4)
        self.notes_text.grid(row=8, column=1, padx=10, pady=5)

        # Set initial values if provided
        if initial_values:
            self.name_var.set(initial_values.get('name', default_name))
            self.manufacturer_var.set(initial_values.get('manufacturer', ''))
            self.part_number_var.set(initial_values.get('part_number', ''))
            self.gain_var.set(initial_values.get('gain', '0'))
            self.band_var.set(initial_values.get('band', ''))
            self.freq_range_var.set(initial_values.get('freq_range', ''))
            self.type_var.set(initial_values.get('type', 'Omni'))
            self.notes_text.insert('1.0', initial_values.get('notes', ''))

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=9, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)


class ManualAntennaDialog:
    """Dialog for manually creating antenna patterns with custom azimuth points"""

    def __init__(self, parent, on_create_callback):
        from debug_logger import get_logger
        self.logger = get_logger()
        self.logger.log("="*80)
        self.logger.log("MANUAL ANTENNA CREATION DIALOG OPENED")
        self.logger.log("="*80)

        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Create Manual Antenna")
        self.dialog.geometry("600x700")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.on_create_callback = on_create_callback

        # Instructions
        ttk.Label(self.dialog, text="Create Custom Antenna Pattern", font=('Arial', 12, 'bold')).pack(pady=10)

        # Create scrollable frame
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Metadata fields
        ttk.Label(scrollable_frame, text="Antenna Name:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.name_var = tk.StringVar(value="Custom Antenna")
        ttk.Entry(scrollable_frame, textvariable=self.name_var, width=40).grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(scrollable_frame, text="Manufacturer:").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.manufacturer_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.manufacturer_var, width=40).grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(scrollable_frame, text="Part Number:").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.part_number_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.part_number_var, width=40).grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(scrollable_frame, text="Gain (dBi):").grid(row=3, column=0, padx=10, pady=5, sticky=tk.W)
        self.gain_var = tk.StringVar(value="0")
        ttk.Entry(scrollable_frame, textvariable=self.gain_var, width=40).grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(scrollable_frame, text="Band:").grid(row=4, column=0, padx=10, pady=5, sticky=tk.W)
        self.band_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.band_var, width=40).grid(row=4, column=1, padx=10, pady=5)

        ttk.Label(scrollable_frame, text="Frequency Range:").grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)
        self.freq_range_var = tk.StringVar()
        ttk.Entry(scrollable_frame, textvariable=self.freq_range_var, width=40).grid(row=5, column=1, padx=10, pady=5)

        ttk.Label(scrollable_frame, text="Type:").grid(row=6, column=0, padx=10, pady=5, sticky=tk.W)
        self.type_var = tk.StringVar(value="Directional")
        type_combo = ttk.Combobox(scrollable_frame, textvariable=self.type_var, width=37)
        type_combo['values'] = ('Omni', 'Directional', 'Yagi', 'Panel', 'Sector', 'Dipole', 'Other')
        type_combo.grid(row=6, column=1, padx=10, pady=5)

        ttk.Label(scrollable_frame, text="Bays:").grid(row=7, column=0, padx=10, pady=5, sticky=tk.W)
        self.bays_var = tk.StringVar(value="1")
        ttk.Entry(scrollable_frame, textvariable=self.bays_var, width=40).grid(row=7, column=1, padx=10, pady=5)

        # Azimuth points selection
        ttk.Label(scrollable_frame, text="Azimuth Points:").grid(row=8, column=0, padx=10, pady=10, sticky=tk.W)
        self.azimuth_points_var = tk.StringVar(value="12")
        azimuth_combo = ttk.Combobox(scrollable_frame, textvariable=self.azimuth_points_var, width=37)
        azimuth_combo['values'] = ('4', '12', '24', '36')
        azimuth_combo.grid(row=8, column=1, padx=10, pady=10)
        azimuth_combo.bind('<<ComboboxSelected>>', self.update_azimuth_inputs)

        # Container for azimuth inputs
        self.azimuth_frame = ttk.Frame(scrollable_frame)
        self.azimuth_frame.grid(row=9, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W+tk.E)

        # Notes
        ttk.Label(scrollable_frame, text="Notes:").grid(row=10, column=0, padx=10, pady=5, sticky=tk.W+tk.N)
        self.notes_text = tk.Text(scrollable_frame, width=50, height=3)
        self.notes_text.grid(row=10, column=1, padx=10, pady=5)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Buttons at bottom
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, pady=10)
        ttk.Button(button_frame, text="Create Antenna", command=self.create).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=10)

        # Initialize with 12 points
        self.update_azimuth_inputs()

    def update_azimuth_inputs(self, event=None):
        """Update the azimuth gain input fields based on selected point count"""
        # Clear existing inputs
        for widget in self.azimuth_frame.winfo_children():
            widget.destroy()

        points = int(self.azimuth_points_var.get())
        angles = self.get_angles_for_points(points)

        ttk.Label(self.azimuth_frame, text="Azimuth Gains (dB relative):", font=('Arial', 10, 'bold')).pack(pady=5)

        self.gain_entries = []
        for i, angle in enumerate(angles):
            frame = ttk.Frame(self.azimuth_frame)
            frame.pack(fill=tk.X, pady=2)

            ttk.Label(frame, text=f"{angle}°:", width=8).pack(side=tk.LEFT)
            gain_var = tk.StringVar(value="0")
            entry = ttk.Entry(frame, textvariable=gain_var, width=10)
            entry.pack(side=tk.LEFT, padx=5)
            self.gain_entries.append((angle, gain_var))

    def get_angles_for_points(self, points):
        """Get angle list for given point count"""
        if points == 4:
            return [0, 90, 180, 270]
        elif points == 12:
            return [i * 30 for i in range(12)]
        elif points == 24:
            return [i * 15 for i in range(24)]
        elif points == 36:
            return [i * 10 for i in range(36)]
        return []

    def create(self):
        """Create the antenna XML and metadata"""
        try:
            # Collect metadata
            metadata = {
                'name': self.name_var.get(),
                'manufacturer': self.manufacturer_var.get(),
                'part_number': self.part_number_var.get(),
                'gain': self.gain_var.get(),
                'band': self.band_var.get(),
                'freq_range': self.freq_range_var.get(),
                'type': self.type_var.get(),
                'bays': self.bays_var.get(),
                'notes': self.notes_text.get('1.0', tk.END).strip()
            }

            # Generate XML
            xml = self.generate_xml(metadata)

            self.result = (xml, metadata)
            self.logger.log("Manual antenna created successfully")
            self.logger.log(f"XML length: {len(xml)} characters")
            self.on_create_callback(xml, metadata)
            self.dialog.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to create antenna: {e}")

    def generate_xml(self, metadata):
        """Generate antenna XML from metadata and azimuth gains"""
        xml_parts = ['<antenna>']
        xml_parts.append(f'<type>{metadata["type"]}</type>')
        xml_parts.append(f'<bays>{metadata["bays"]}</bays>')

        # Azimuth pattern
        xml_parts.append('<azimuth>')
        for angle, gain_var in self.gain_entries:
            gain = gain_var.get()
            try:
                gain_float = float(gain)
            except ValueError:
                gain_float = 0.0
            xml_parts.append(f'<point angle="{angle}" gain="{gain_float:.2f}"/>')
        xml_parts.append('</azimuth>')

        # Elevation (default)
        xml_parts.append('<elevation>')
        xml_parts.append('<point angle="0" gain="0"/>')
        xml_parts.append('</elevation>')

        xml_parts.append('</antenna>')
        return '\n'.join(xml_parts)

    def cancel(self):
        self.logger.log("User cancelled manual antenna creation")
        self.logger.log("="*80)
        self.logger.log("MANUAL ANTENNA CREATION DIALOG CLOSED")
        self.logger.log("="*80)
        self.dialog.destroy()
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Antenna name is required")
            return
        
        try:
            gain = float(self.gain_var.get())
        except ValueError:
            messagebox.showerror("Error", "Gain must be a number")
            return
        
        import datetime
        
        self.result = {
            'name': name,
            'manufacturer': self.manufacturer_var.get().strip() or 'Unknown',
            'part_number': self.part_number_var.get().strip() or 'N/A',
            'gain': gain,
            'band': self.band_var.get().strip() or 'N/A',
            'frequency_range': self.freq_range_var.get().strip() or 'N/A',
            'type': self.type_var.get(),
            'notes': self.notes_text.get('1.0', tk.END).strip(),
            'import_date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.dialog.destroy()
    
    def cancel(self):
        """Cancel without saving"""
        self.result = None
        self.dialog.destroy()