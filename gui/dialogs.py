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
import os
import math

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
    """Dialog for editing antenna information including bearing and downtilt"""
    def __init__(self, parent, pattern_name, current_bearing=0.0, current_downtilt=0.0):
        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Edit Antenna Information")
        self.dialog.geometry("450x280")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Current antenna pattern
        ttk.Label(self.dialog, text="Current Antenna Pattern:").grid(row=0, column=0, padx=10, pady=10, sticky=tk.W)
        ttk.Label(self.dialog, text=pattern_name, font=('Arial', 10, 'bold')).grid(row=0, column=1, columnspan=2, padx=10, pady=10, sticky=tk.W)

        # Bearing input
        ttk.Label(self.dialog, text="Bearing (°):").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        self.bearing_var = tk.StringVar(value=f"{current_bearing:.1f}")
        bearing_entry = ttk.Entry(self.dialog, textvariable=self.bearing_var, width=10)
        bearing_entry.grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        ttk.Label(self.dialog, text="0°=North, 90°=East, 180°=South, 270°=West",
                  font=('Arial', 8)).grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)

        # Downtilt input
        ttk.Label(self.dialog, text="Downtilt (°):").grid(row=2, column=0, padx=10, pady=5, sticky=tk.W)
        self.downtilt_var = tk.StringVar(value=f"{current_downtilt:.1f}")
        downtilt_entry = ttk.Entry(self.dialog, textvariable=self.downtilt_var, width=10)
        downtilt_entry.grid(row=2, column=1, padx=10, pady=5, sticky=tk.W)
        ttk.Label(self.dialog, text="Positive = down, Negative = up (typical: 0-15°)",
                  font=('Arial', 8)).grid(row=2, column=2, padx=5, pady=5, sticky=tk.W)

        # Pattern buttons
        pattern_frame = ttk.LabelFrame(self.dialog, text="Antenna Pattern", padding=5)
        pattern_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=10, sticky=tk.EW)
        ttk.Button(pattern_frame, text="Load New Pattern (XML)", command=self.load_pattern).pack(side=tk.LEFT, padx=5)
        ttk.Button(pattern_frame, text="Reset to Omni", command=self.reset_omni).pack(side=tk.LEFT, padx=5)

        # Action buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=4, column=0, columnspan=3, pady=15)
        ttk.Button(btn_frame, text="Apply", command=self.apply_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.close).pack(side=tk.LEFT, padx=5)

        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def apply_settings(self):
        """Apply bearing and downtilt settings"""
        try:
            bearing = float(self.bearing_var.get()) % 360
            downtilt = float(self.downtilt_var.get())
            # Clamp downtilt to reasonable range
            downtilt = max(-90, min(90, downtilt))
            self.result = ('settings', {'bearing': bearing, 'downtilt': downtilt})
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for bearing and downtilt")

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

        # Verbose logging state (initialize early so _vlog works)
        self.verbose_logging = tk.BooleanVar(value=True)
        self.verbose_log_file = None

        self._vlog("="*80)
        self._vlog("AI ANTENNA IMPORT DIALOG OPENED")
        self._vlog("="*80)

        self.result = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Import Antenna Pattern")
        self.dialog.geometry("500x450")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.on_import_callback = on_import_callback

        # Top frame for logging toggle
        top_frame = ttk.Frame(self.dialog)
        top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)
        ttk.Checkbutton(top_frame, text="Verbose Logging", variable=self.verbose_logging,
                       command=self._toggle_verbose_logging).pack(side=tk.LEFT)
        self.log_file_label = ttk.Label(top_frame, text="", font=('Arial', 8), foreground='gray')
        self.log_file_label.pack(side=tk.LEFT, padx=(10, 0))

        # URL input
        ttk.Label(self.dialog, text="Antenna Website URL:").grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)
        self.url_var = tk.StringVar()
        ttk.Entry(self.dialog, textvariable=self.url_var, width=40).grid(row=1, column=1, padx=10, pady=10)

        # Or PDF file
        ttk.Label(self.dialog, text="Or PDF Spec Sheet:").grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)
        self.pdf_path_var = tk.StringVar()
        pdf_frame = ttk.Frame(self.dialog)
        pdf_frame.grid(row=2, column=1, padx=10, pady=10, sticky=tk.W+tk.E)
        ttk.Entry(pdf_frame, textvariable=self.pdf_path_var, width=30).pack(side=tk.LEFT)
        ttk.Button(pdf_frame, text="Browse", command=self.browse_pdf).pack(side=tk.LEFT, padx=(5,0))

        # Process button
        ttk.Button(self.dialog, text="Process and Import", command=self.process).grid(row=3, column=0, columnspan=2, pady=20)

        # Status label
        self.status_var = tk.StringVar(value="")
        ttk.Label(self.dialog, textvariable=self.status_var).grid(row=4, column=0, columnspan=2, padx=10, pady=5)

        # Buttons
        button_frame = ttk.Frame(self.dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        ttk.Button(button_frame, text="OK", command=self.ok).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT)

    def _toggle_verbose_logging(self):
        """Toggle verbose logging on/off"""
        if self.verbose_logging.get():
            self._vlog("Verbose logging ENABLED")
        else:
            self._vlog("Verbose logging DISABLED")

    def _start_verbose_log(self, pdf_path=""):
        """Start a new verbose log file for this import run"""
        if not self.verbose_logging.get():
            return

        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_name = os.path.basename(pdf_path).replace('.pdf', '') if pdf_path else 'url_import'
        log_filename = f"antenna_import_{pdf_name}_{timestamp}.log"

        # Save in the same directory as the PDF, or in Downloads
        if pdf_path:
            log_dir = os.path.dirname(pdf_path)
        else:
            log_dir = os.path.expanduser("~/Downloads")

        self.verbose_log_path = os.path.join(log_dir, log_filename)
        self.verbose_log_file = open(self.verbose_log_path, 'w')
        self.log_file_label.config(text=f"Log: {log_filename}")
        self._vlog(f"{'='*80}")
        self._vlog(f"ANTENNA IMPORT VERBOSE LOG")
        self._vlog(f"Started: {datetime.now().isoformat()}")
        self._vlog(f"PDF: {pdf_path}")
        self._vlog(f"{'='*80}\n")

    def _vlog(self, message):
        """Write to verbose log file if enabled"""
        if self.verbose_logging.get() and self.verbose_log_file:
            self.verbose_log_file.write(message + "\n")
            self.verbose_log_file.flush()
        # Also write to main logger
        self.logger.log(message)

    def _close_verbose_log(self):
        """Close the verbose log file"""
        if self.verbose_log_file:
            self._vlog(f"\n{'='*80}")
            self._vlog("IMPORT COMPLETED")
            self._vlog(f"{'='*80}")
            self.verbose_log_file.close()
            self.verbose_log_file = None

    def browse_pdf(self):
        filepath = filedialog.askopenfilename(
            title="Select PDF Spec Sheet",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filepath:
            self.pdf_path_var.set(filepath)
            self._vlog(f"PDF selected: {filepath}")

    def process(self):
        url = self.url_var.get().strip()
        pdf_path = self.pdf_path_var.get().strip()

        # Start verbose logging for this run
        self._start_verbose_log(pdf_path)

        self._vlog("-"*80)
        self._vlog("AI ANTENNA IMPORT - PROCESSING STARTED")
        self._vlog(f"URL: {url if url else '(none)'}")
        self._vlog(f"PDF: {pdf_path if pdf_path else '(none)'}")
        self._vlog("-"*80)

        if not url and not pdf_path:
            self._vlog("ERROR: No input provided")
            messagebox.showerror("Input Required", "Please provide a URL or select a PDF file.")
            return

        self.status_var.set("Processing... Please wait.")
        self.dialog.update()

        try:
            # Extract text, send to LLM, generate XML
            xml_content, text = self.generate_xml_from_input(url, pdf_path)
            if xml_content:
                self.result = xml_content
                # Extract metadata for library fields
                self.metadata = self.extract_metadata(text)

                # Check if multiple antennas were found
                if getattr(self, 'has_multiple_antennas', False) and len(getattr(self, 'multi_antennas', [])) > 1:
                    self._vlog(f"Multiple antennas found - showing selection dialog")
                    self.status_var.set(f"Found {len(self.multi_antennas)} antennas! Select which to import.")
                    self.dialog.update()
                    # Show antenna selection dialog
                    self.show_antenna_selection_dialog()
                else:
                    self.status_var.set("XML generated successfully. Click OK to import.")
                    self._vlog("SUCCESS: XML generated successfully")
                    self._vlog(f"XML length: {len(xml_content)} characters")
                    self._vlog(f"Extracted metadata: {self.metadata}")
            else:
                self.status_var.set("Failed to generate XML. Check inputs and try again.")
                self._vlog("ERROR: XML generation failed (returned None)")
        except Exception as e:
            self.status_var.set(f"Error: {str(e)}")
            self._vlog(f"ERROR: Exception during processing: {str(e)}")
            import traceback
            self._vlog(f"Traceback: {traceback.format_exc()}")

    def show_antenna_selection_dialog(self):
        """Show dialog to select which antenna(s) to import from multi-antenna datasheet"""
        selection_dialog = tk.Toplevel(self.dialog)
        selection_dialog.title("Select Antenna to Import")
        selection_dialog.geometry("700x400")
        selection_dialog.transient(self.dialog)
        selection_dialog.grab_set()

        ttk.Label(selection_dialog, text="Multiple antennas found in datasheet. Select which to import:",
                  font=('Arial', 10, 'bold')).pack(pady=10)

        # Create a frame for the listbox with scrollbar
        list_frame = ttk.Frame(selection_dialog)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create treeview for better display
        columns = ('model', 'freq_range', 'gain', 'type', 'h_bw', 'v_bw')
        tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)

        tree.heading('model', text='Model')
        tree.heading('freq_range', text='Frequency')
        tree.heading('gain', text='Gain (dBi)')
        tree.heading('type', text='Type')
        tree.heading('h_bw', text='H-BW (°)')
        tree.heading('v_bw', text='V-BW (°)')

        tree.column('model', width=150)
        tree.column('freq_range', width=120)
        tree.column('gain', width=80)
        tree.column('type', width=100)
        tree.column('h_bw', width=70)
        tree.column('v_bw', width=70)

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Populate the list
        for i, ant in enumerate(self.multi_antennas):
            tree.insert('', tk.END, iid=str(i), values=(
                ant['model'],
                ant['freq_range'],
                ant['gain_dbi'],
                ant['type'],
                ant['h_beamwidth'],
                ant['v_beamwidth']
            ))

        # Select first item by default
        if self.multi_antennas:
            tree.selection_set('0')

        # Buttons
        btn_frame = ttk.Frame(selection_dialog)
        btn_frame.pack(pady=15)

        def import_selected():
            selection = tree.selection()
            if not selection:
                messagebox.showwarning("No Selection", "Please select an antenna to import")
                return

            idx = int(selection[0])
            selected_ant = self.multi_antennas[idx]
            self.result = selected_ant['xml']

            # Update metadata with selected antenna info
            self.metadata['name'] = selected_ant['model']
            self.metadata['manufacturer'] = selected_ant.get('manufacturer', '')
            self.metadata['freq_range'] = selected_ant.get('freq_range', '')
            try:
                self.metadata['gain'] = str(float(selected_ant.get('gain_dbi', '0')))
            except ValueError:
                self.metadata['gain'] = '0'
            self.metadata['type'] = selected_ant.get('type', 'Directional')

            self._vlog(f"User selected antenna: {selected_ant['model']}")
            self.status_var.set(f"Selected: {selected_ant['model']}. Click OK to import.")
            selection_dialog.destroy()

        def import_all():
            """Import all antennas one by one"""
            self._vlog("User chose to import ALL antennas")
            self.import_all_antennas = True
            self.status_var.set(f"Will import all {len(self.multi_antennas)} antennas. Click OK to proceed.")
            selection_dialog.destroy()

        def cancel_selection():
            selection_dialog.destroy()

        ttk.Button(btn_frame, text="Import Selected", command=import_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Import All", command=import_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=cancel_selection).pack(side=tk.LEFT, padx=5)

        # Center the dialog
        selection_dialog.update_idletasks()
        x = self.dialog.winfo_x() + (self.dialog.winfo_width() // 2) - (selection_dialog.winfo_width() // 2)
        y = self.dialog.winfo_y() + (self.dialog.winfo_height() // 2) - (selection_dialog.winfo_height() // 2)
        selection_dialog.geometry(f"+{x}+{y}")

        # Wait for dialog to close
        self.dialog.wait_window(selection_dialog)

    def generate_xml_from_input(self, url, pdf_path):
        """Extract text from URL or PDF, then use LLM to generate XML"""
        text = ""
        if url:
            self._vlog(f"Attempting to scrape URL: {url}")
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                self._vlog(f"HTTP Status: {response.status_code}")
                self._vlog(f"Content length: {len(response.content)} bytes")
                soup = BeautifulSoup(response.content, 'html.parser')
                text = soup.get_text()
                self._vlog(f"Extracted text length: {len(text)} characters")
                self._vlog(f"Text preview: {text[:200]}...")
            except Exception as e:
                self._vlog(f"ERROR scraping website: {e}")
                raise Exception(f"Failed to scrape website: {e}")
        elif pdf_path:
            self._vlog(f"Attempting to read PDF: {pdf_path}")
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    page_count = len(reader.pages)
                    self._vlog(f"PDF has {page_count} pages")
                    for i, page in enumerate(reader.pages):
                        page_text = page.extract_text()
                        text += page_text + "\n"
                        self._vlog(f"Page {i+1}: extracted {len(page_text)} characters")
                self._vlog(f"Total extracted text length: {len(text)} characters")
                self._vlog(f"Text preview: {text[:200]}...")
            except Exception as e:
                self._vlog(f"ERROR reading PDF: {e}")
                raise Exception(f"Failed to read PDF: {e}")

        # Analyze images for radiation pattern data
        image_pattern_data = {}
        if pdf_path:
            self._vlog("Analyzing images for radiation pattern data...")
            image_pattern_data = self.analyze_images_from_pdf(pdf_path)
            if image_pattern_data:
                self._vlog(f"Found pattern data from images: {list(image_pattern_data.keys())}")
            else:
                self._vlog("No pattern data found in images")

        if not text.strip() and not image_pattern_data:
            self._vlog("ERROR: No text or pattern data extracted from source")
            raise Exception("No text or pattern data extracted from the source.")

        # Check for azimuth table in text
        azimuth_pairs = self.parse_azimuth_table(text)
        if azimuth_pairs:
            self._vlog(f"Found azimuth table with {len(azimuth_pairs)} points in text")
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
                self._vlog(f"Converted to dB gains: max {max_value}, range {min(db_pairs, key=lambda x: x[1])[1]} to {max(db_pairs, key=lambda x: x[1])[1]} dB")

        # Check if this is an omnidirectional antenna - if so, use standard pattern
        if 'omni' in text.lower():
            self._vlog("Detected omnidirectional antenna - using standard uniform azimuth pattern")
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
            all_patterns = image_pattern_data.get('all_patterns', [])

            # If multiple patterns found, try to identify multiple antennas from the text
            if len(all_patterns) > 1:
                self._vlog(f"Found {len(all_patterns)} pattern images - checking for multi-antenna datasheet...")

                # Use LLM to extract antenna model info from text (metadata only, not patterns)
                antenna_models = self.extract_antenna_models_from_text(text)

                if len(antenna_models) > 1:
                    self._vlog(f"Found {len(antenna_models)} antenna models in text: {[m['model'] for m in antenna_models]}")

                    # Associate patterns with models (by order - patterns usually match model order)
                    self.multi_antennas = []
                    for i, model_info in enumerate(antenna_models):
                        # Use pattern at same index, or last pattern if we run out
                        pattern_idx = min(i, len(all_patterns) - 1)
                        pattern = all_patterns[pattern_idx]['points']

                        # Generate XML for this antenna with the digitized pattern
                        xml = self.generate_xml_for_antenna(model_info, pattern)

                        self.multi_antennas.append({
                            'model': model_info.get('model', f'Antenna_{i+1}'),
                            'manufacturer': model_info.get('manufacturer', ''),
                            'freq_range': model_info.get('freq_range', ''),
                            'gain_dbi': model_info.get('gain_dbi', '0'),
                            'type': model_info.get('type', 'Directional'),
                            'h_beamwidth': model_info.get('h_beamwidth', ''),
                            'v_beamwidth': model_info.get('v_beamwidth', ''),
                            'xml': xml
                        })

                    self.has_multiple_antennas = True
                    self._vlog(f"Created {len(self.multi_antennas)} antenna entries for selection")

                    # Return first antenna's XML (selection dialog will update this)
                    return self.multi_antennas[0]['xml'], text

            # Single pattern or single antenna - generate directly
            self._vlog("Generating XML from image-extracted pattern data...")
            self.has_multiple_antennas = False
            self.multi_antennas = []
            xml = self.generate_xml_from_image_data(image_pattern_data, text)
            return xml, text

        # Now send to LLM
        self._vlog("Sending text to LLM for XML generation...")
        xml = self.query_llm_for_xml(text)

        # If no pattern found and it's a dipole, generate standard single-bay dipole pattern
        if xml.strip() == "NO_PATTERN_DATA_FOUND" and 'dipole' in text.lower():
            self._vlog("No pattern data found, generating standard single-bay dipole pattern...")
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
            self._vlog("VALIDATION: Checking if pattern data looks realistic...")
            
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
                self._vlog(f"VALIDATION FAIL: {positive_count}/{len(gains)} gains are positive - likely hallucinated")
                return False, "Pattern has mostly positive gains - this is physically unrealistic. LLM likely invented data."

            # RED FLAG 2: Gains increase perfectly linearly (like 0, 10, 20, 30...)
            if len(gains) >= 4:
                differences = [gains[i+1] - gains[i] for i in range(len(gains)-1)]
                # Check if all differences are very similar (linear pattern)
                if len(set(differences)) <= 2 and all(d == differences[0] for d in differences):
                    self._vlog(f"VALIDATION FAIL: Gains increase linearly: {gains[:10]}...")
                    return False, "Pattern shows perfectly linear gain progression - this is not real data. LLM invented a fake pattern."

            # RED FLAG 3: All values are the same (constant pattern when it shouldn't be)
            unique_gains = len(set(gains))
            if unique_gains == 1:
                self._vlog(f"VALIDATION FAIL: All {len(gains)} points have same gain value {gains[0]}")
                return False, f"All gain values are identical ({gains[0]} dBi) - LLM generated placeholder data, not real pattern"

            # RED FLAG 3b: Too few unique values (like just repeating 0, 10, 20)
            if unique_gains < len(gains) * 0.3:  # Less than 30% unique
                self._vlog(f"VALIDATION FAIL: Only {unique_gains} unique values in {len(gains)} points")
                return False, f"Only {unique_gains} unique gain values - pattern looks artificial or incomplete"

            # RED FLAG 3c: No gain at 0° is 0 dB (the reference)
            gains_at_zero = [g for a, g in zip(angles, gains) if a == 0]
            if gains_at_zero and gains_at_zero[0] != 0:
                self._vlog(f"VALIDATION WARN: Gain at 0° is {gains_at_zero[0]}, not 0 (reference)")
                # Don't fail, but log it

            # RED FLAG 4: Gains are impossibly high (>20 dBi for omni, >30 dBi for directional)
            max_gain = max(gains)
            if max_gain > 30:
                self._vlog(f"VALIDATION FAIL: Maximum gain {max_gain} dBi is unrealistic")
                return False, f"Maximum gain {max_gain} dBi exceeds realistic limits for antennas"

            # PASS: Pattern looks reasonable
            self._vlog(f"VALIDATION PASS: Pattern has {len(gains)} points, {unique_gains} unique values")
            self._vlog(f"  Gain range: {min(gains):.1f} to {max(gains):.1f} dBi")
            self._vlog(f"  Positive gains: {positive_count}/{len(gains)}")
            return True, "Pattern looks physically realistic"

        except Exception as e:
            self._vlog(f"VALIDATION ERROR: {e}")
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
        """Extract and analyze images from PDF for radiation pattern data using computer vision"""
        pattern_data = {}

        try:
            import fitz  # PyMuPDF
            from PIL import Image
            import io

            doc = fitz.open(pdf_path)
            image_count = 0
            patterns_found = []

            self._vlog(f"Scanning PDF for polar pattern images...")

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()
                self._vlog(f"Page {page_num + 1}: found {len(image_list)} images")

                for img_index, img in enumerate(image_list):
                    try:
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        img_name = f"page{page_num}_img{img_index}"

                        # Open image with PIL
                        pil_image = Image.open(io.BytesIO(image_bytes))

                        # Check if image is large enough to be a pattern plot (not an icon)
                        width, height = pil_image.size
                        if width < 150 or height < 150:
                            self._vlog(f"  {img_name}: {width}x{height} - too small, skipping")
                            continue

                        self._vlog(f"  {img_name}: {width}x{height} - analyzing...")

                        # Save image for debugging
                        debug_dir = os.path.join(os.path.dirname(pdf_path), "debug_images")
                        os.makedirs(debug_dir, exist_ok=True)
                        debug_path = os.path.join(debug_dir, f"{img_name}.png")
                        pil_image.save(debug_path)
                        self._vlog(f"    Saved debug image: {debug_path}")

                        # Check if this looks like a polar plot (not a product photo)
                        if not self._is_polar_plot(pil_image, img_name):
                            self._vlog(f"  {img_name}: Not a polar plot (likely product photo), skipping")
                            continue

                        # Try to digitize as polar plot
                        digitized = self.digitize_polar_plot(pil_image, img_name)

                        if digitized and len(digitized) >= 8:
                            self._vlog(f"  {img_name}: SUCCESS - extracted {len(digitized)} points")
                            patterns_found.append({
                                'name': img_name,
                                'points': digitized,
                                'size': (width, height)
                            })
                            image_count += 1
                        else:
                            self._vlog(f"  {img_name}: Not recognized as polar plot or insufficient points")

                    except Exception as e:
                        self._vlog(f"Error processing image: {e}")

            doc.close()

            # Keep ALL patterns found for multi-antenna support
            if patterns_found:
                # Filter to find valid AZIMUTH patterns for directional antennas
                # NOTE: In datasheets, the main beam may point in ANY direction (often 90° = right)
                # We need to:
                # 1. Find where the max gain is
                # 2. Check if the opposite side is weak (directional, not omni/elevation)
                # 3. Rotate the pattern so max is at 0°
                valid_azimuth_patterns = []

                for p in patterns_found:
                    points = p['points']
                    if not points:
                        continue

                    all_gains = [g for a, g in points]
                    max_gain = max(all_gains)
                    min_gain = min(all_gains)

                    # Find the angle with maximum gain (main beam direction)
                    max_angle = next((a for a, g in points if g == max_gain), 0)

                    # Calculate the opposite angle (back of antenna)
                    back_angle = (max_angle + 180) % 360

                    # Get gain at back (find closest angle)
                    gain_at_back = None
                    for a, g in points:
                        if abs(a - back_angle) <= 5 or abs(a - back_angle) >= 355:
                            gain_at_back = g
                            break

                    # Get gains in the back region (90° to 180° away from max)
                    back_region_gains = []
                    for a, g in points:
                        # Calculate angular distance from max
                        diff = abs(a - max_angle)
                        if diff > 180:
                            diff = 360 - diff
                        # Back region is 90-180° away from main beam
                        if 90 <= diff <= 180:
                            back_region_gains.append(g)

                    avg_back = sum(back_region_gains) / len(back_region_gains) if back_region_gains else min_gain

                    # Check for valid AZIMUTH pattern:
                    # 1. Has significant variation (not omni)
                    # 2. Back is significantly weaker than front (not elevation/figure-8)
                    gain_range = max_gain - min_gain
                    has_variation = gain_range >= 10  # At least 10dB difference

                    # Back should be at least 10dB weaker than front
                    back_is_weak = gain_at_back is None or gain_at_back < max_gain - 10
                    has_good_fb_ratio = avg_back < max_gain - 8

                    # Check if it's an elevation pattern (figure-8: both top and bottom strong)
                    gain_at_0 = next((g for a, g in points if a == 0), None)
                    gain_at_180 = next((g for a, g in points if a == 180), None)
                    is_figure8 = (gain_at_0 is not None and gain_at_180 is not None and
                                  abs(gain_at_0 - gain_at_180) < 5 and
                                  gain_at_0 > max_gain - 3 and gain_at_180 > max_gain - 3)

                    self._vlog(f"  {p['name']}: max={max_gain:.1f}dB@{max_angle}°, back@{back_angle}°={gain_at_back}, avg_back={avg_back:.1f}dB")
                    self._vlog(f"    range={gain_range:.1f}dB, back_weak={back_is_weak}, good_fb={has_good_fb_ratio}, figure8={is_figure8}")

                    # Valid azimuth pattern: has variation, back is weak, not figure-8
                    if has_variation and back_is_weak and has_good_fb_ratio and not is_figure8:
                        # ROTATE the pattern so main beam is at 0°
                        rotation = -max_angle
                        rotated_points = []
                        for a, g in points:
                            new_angle = (a + rotation) % 360
                            rotated_points.append((new_angle, g))
                        # Sort by angle
                        rotated_points.sort(key=lambda x: x[0])

                        p['points'] = rotated_points
                        p['rotation'] = rotation
                        p['quality_score'] = gain_range + (max_gain - avg_back)
                        valid_azimuth_patterns.append(p)
                        self._vlog(f"    VALID azimuth pattern - rotated by {rotation}° to put main beam at 0°")

                if valid_azimuth_patterns:
                    # Sort by quality (best F/B ratio) then by size
                    valid_azimuth_patterns.sort(key=lambda x: (x.get('quality_score', 0), x['size'][0] * x['size'][1]), reverse=True)
                    self._vlog(f"Found {len(valid_azimuth_patterns)} valid azimuth patterns")
                    patterns_found = valid_azimuth_patterns
                else:
                    self._vlog("WARNING: No valid directional azimuth patterns found, using all patterns")
                    # Sort by size as fallback
                    patterns_found.sort(key=lambda x: x['size'][0] * x['size'][1], reverse=True)

                # Store all patterns
                pattern_data['all_patterns'] = patterns_found

                # For backwards compatibility, also store the best one as 'azimuth'
                best_pattern = patterns_found[0]
                pattern_data['azimuth'] = best_pattern['points']
                self._vlog(f"Best pattern from {best_pattern['name']} ({len(best_pattern['points'])} points)")

                for i, p in enumerate(patterns_found):
                    self._vlog(f"  Pattern {i+1}: {p['name']} - {len(p['points'])} points, size {p['size']}")

            self._vlog(f"Image analysis complete: {image_count} polar patterns found")

        except ImportError as e:
            self._vlog(f"Required library not available: {e}")
        except Exception as e:
            self._vlog(f"Error in image analysis: {e}")
            import traceback
            self._vlog(traceback.format_exc())

        return pattern_data

    def _is_polar_plot(self, pil_image, img_name=""):
        """
        Check if an image looks like a polar radiation pattern plot.
        Returns True if it appears to be a polar plot, False otherwise.

        A polar plot should have:
        1. Mostly white/light background
        2. Concentric circular grid lines
        3. Radial lines from center
        4. Roughly square aspect ratio
        """
        try:
            import numpy as np

            img_array = np.array(pil_image.convert('RGB'))
            height, width = img_array.shape[:2]

            # Check aspect ratio - polar plots are usually roughly square
            aspect_ratio = width / height
            if aspect_ratio < 0.7 or aspect_ratio > 1.4:
                self._vlog(f"    {img_name}: Aspect ratio {aspect_ratio:.2f} - not square enough for polar plot")
                return False

            # Convert to grayscale
            gray = np.mean(img_array, axis=2)

            # Check if background is mostly white/light
            # Polar plots have white backgrounds with thin dark lines
            light_pixels = np.sum(gray > 200)
            total_pixels = gray.size
            light_ratio = light_pixels / total_pixels

            if light_ratio < 0.5:
                self._vlog(f"    {img_name}: Only {light_ratio*100:.0f}% light pixels - too dark for polar plot")
                return False

            # Check for concentric circles by sampling at different radii from center
            center_x, center_y = width // 2, height // 2
            max_radius = min(width, height) * 0.45

            # Sample at multiple radii and check for circular symmetry
            radii_to_check = [0.3, 0.5, 0.7, 0.9]
            circle_scores = []

            for radius_frac in radii_to_check:
                radius = max_radius * radius_frac
                # Sample points around the circle
                angles = np.linspace(0, 2 * np.pi, 36)  # Every 10 degrees
                dark_count = 0

                for angle in angles:
                    px = int(center_x + radius * np.cos(angle))
                    py = int(center_y + radius * np.sin(angle))
                    if 0 <= px < width and 0 <= py < height:
                        if gray[py, px] < 150:  # Dark pixel
                            dark_count += 1

                # A grid ring should have dark pixels at regular intervals
                circle_scores.append(dark_count)

            # Polar plots have concentric rings - expect some dark pixels at each radius
            rings_with_content = sum(1 for s in circle_scores if s >= 4)

            if rings_with_content < 2:
                self._vlog(f"    {img_name}: Only {rings_with_content} rings detected - not a polar plot")
                return False

            # Check for radial lines from center
            # Sample along radial lines and count dark pixels
            radial_dark_counts = []
            for angle_deg in range(0, 360, 30):  # Every 30 degrees
                angle_rad = np.radians(angle_deg)
                dark_count = 0
                for r in np.linspace(max_radius * 0.2, max_radius * 0.9, 20):
                    px = int(center_x + r * np.cos(angle_rad))
                    py = int(center_y + r * np.sin(angle_rad))
                    if 0 <= px < width and 0 <= py < height:
                        if gray[py, px] < 150:
                            dark_count += 1
                radial_dark_counts.append(dark_count)

            # Polar plots should have some radial lines (at least some angles with multiple dark pixels)
            radials_with_content = sum(1 for c in radial_dark_counts if c >= 3)

            if radials_with_content < 4:
                self._vlog(f"    {img_name}: Only {radials_with_content} radial lines detected - not a polar plot")
                return False

            self._vlog(f"    {img_name}: Detected as polar plot (rings={rings_with_content}, radials={radials_with_content}, light={light_ratio*100:.0f}%)")
            return True

        except Exception as e:
            self._vlog(f"    {img_name}: Error checking if polar plot: {e}")
            return False

    def digitize_polar_plot(self, pil_image, img_name=""):
        """
        Digitize a polar radiation pattern plot image.
        Returns list of (angle, gain_db) tuples.

        Strategy: Find the DARKEST and THICKEST line along each radial.
        Grid/reference lines are typically thinner and lighter than the pattern line.
        The pattern trace is solid black, while dashed references are gray.
        """
        try:
            import numpy as np

            # Convert to numpy array
            img_array = np.array(pil_image.convert('RGB'))
            height, width = img_array.shape[:2]

            self._vlog(f"    Digitizing {img_name}: {width}x{height} pixels")

            # Convert to grayscale
            gray = np.mean(img_array, axis=2)

            # Find center of the plot (geometric center)
            center_x = width // 2
            center_y = height // 2

            # Estimate the outer radius of the plot (the 0 dB ring)
            outer_radius = min(width, height) * 0.45

            # The plot typically has rings at 0, -5, -10, -15, -20, -25, -30 dB
            total_db_range = 30  # 0 to -30 dB

            angles_to_sample = list(range(0, 360, 5))  # Every 5 degrees
            pattern_points = []

            # Threshold for "dark" pixels - pattern lines are typically < 80
            dark_threshold = 100

            for angle_deg in angles_to_sample:
                angle_rad = np.radians(angle_deg - 90)  # 0° = up (north)

                # Sample along the radial from center to edge
                num_samples = 100
                radii = np.linspace(outer_radius * 0.05, outer_radius * 0.98, num_samples)

                # Collect all dark regions along this radial
                dark_regions = []
                in_dark_region = False
                region_start_r = None
                region_pixels = []

                for r in radii:
                    px = int(center_x + r * np.cos(angle_rad))
                    py = int(center_y + r * np.sin(angle_rad))

                    if 0 <= px < width and 0 <= py < height:
                        pixel_val = gray[py, px]
                    else:
                        pixel_val = 255

                    if pixel_val < dark_threshold:
                        if not in_dark_region:
                            in_dark_region = True
                            region_start_r = r
                            region_pixels = [(r, pixel_val)]
                        else:
                            region_pixels.append((r, pixel_val))
                    else:
                        if in_dark_region and len(region_pixels) >= 1:
                            # End of a dark region - record it
                            darkest_val = min(p[1] for p in region_pixels)
                            darkest_r = next(p[0] for p in region_pixels if p[1] == darkest_val)
                            thickness = len(region_pixels)
                            avg_darkness = sum(p[1] for p in region_pixels) / len(region_pixels)
                            center_r = sum(p[0] for p in region_pixels) / len(region_pixels)

                            dark_regions.append({
                                'radius': center_r,
                                'darkest_r': darkest_r,
                                'thickness': thickness,
                                'darkest_val': darkest_val,
                                'avg_darkness': avg_darkness
                            })
                        in_dark_region = False
                        region_pixels = []

                # Don't forget the last region if we ended in dark
                if in_dark_region and len(region_pixels) >= 1:
                    darkest_val = min(p[1] for p in region_pixels)
                    darkest_r = next(p[0] for p in region_pixels if p[1] == darkest_val)
                    thickness = len(region_pixels)
                    avg_darkness = sum(p[1] for p in region_pixels) / len(region_pixels)
                    center_r = sum(p[0] for p in region_pixels) / len(region_pixels)

                    dark_regions.append({
                        'radius': center_r,
                        'darkest_r': darkest_r,
                        'thickness': thickness,
                        'darkest_val': darkest_val,
                        'avg_darkness': avg_darkness
                    })

                # Score each dark region to find the pattern line
                # Pattern line is: thicker, darker, and NOT at the very edge
                best_region = None
                best_score = -float('inf')

                for region in dark_regions:
                    # Skip regions at the very outer edge (likely reference circle)
                    if region['radius'] > outer_radius * 0.92:
                        continue

                    # Score: prefer thick, dark lines that aren't too close to edge
                    # Thickness is important - pattern lines are 2-5 pixels thick
                    thickness_score = min(region['thickness'], 5) * 10
                    # Darkness matters - solid black (0) is better than gray (100)
                    darkness_score = (100 - region['avg_darkness'])
                    # Penalize very edge regions slightly
                    edge_penalty = 0
                    if region['radius'] > outer_radius * 0.85:
                        edge_penalty = 20

                    score = thickness_score + darkness_score - edge_penalty
                    if score > best_score:
                        best_score = score
                        best_region = region

                if best_region:
                    normalized = best_region['radius'] / outer_radius
                    normalized = max(0, min(1, normalized))
                    gain_db = (normalized - 1.0) * total_db_range
                    pattern_points.append((angle_deg, round(gain_db, 1)))

            self._vlog(f"    {img_name}: Scanned {len(angles_to_sample)} angles, found {len(pattern_points)} pattern points")

            # Validate: need reasonable coverage
            if len(pattern_points) < 20:
                self._vlog(f"    {img_name}: Only found {len(pattern_points)} points - insufficient")
                return None

            # Interpolate missing angles and smooth the pattern
            pattern_points = self._smooth_and_interpolate_pattern(pattern_points)

            # Normalize so max gain is 0 dB
            if pattern_points:
                max_gain = max(p[1] for p in pattern_points)
                pattern_points = [(a, round(g - max_gain, 1)) for a, g in pattern_points]

            # Validate pattern has reasonable variation
            gains = [p[1] for p in pattern_points]
            gain_range = max(gains) - min(gains)

            gain_at_0 = next((g for a, g in pattern_points if a == 0), None)
            gains_at_back = [g for a, g in pattern_points if 120 <= a <= 180]
            avg_back_gain = sum(gains_at_back) / len(gains_at_back) if gains_at_back else 0

            self._vlog(f"    {img_name}: gain@0°={gain_at_0}, avg_back={avg_back_gain:.1f}, range={gain_range:.1f}dB")

            if gain_range < 5:
                self._vlog(f"    {img_name}: Pattern has only {gain_range:.1f}dB variation - rejecting")
                return None

            self._vlog(f"    {img_name}: SUCCESS - {len(pattern_points)} points, {gain_range:.1f}dB range")
            self._vlog(f"    Sample: 0°={gain_at_0}dB, 90°={self._get_gain_at_angle(pattern_points, 90)}, 180°={self._get_gain_at_angle(pattern_points, 180)}")

            return pattern_points

        except Exception as e:
            self._vlog(f"    {img_name}: Digitization failed: {e}")
            import traceback
            self._vlog(traceback.format_exc())
            return None

    def _smooth_and_interpolate_pattern(self, pattern_points):
        """
        Smooth the pattern and interpolate missing angles.
        Also detects and fixes outliers (sudden jumps in gain).
        """
        if not pattern_points:
            return pattern_points

        # Convert to dict for easier manipulation
        pattern_dict = {a: g for a, g in pattern_points}

        # Interpolate missing angles (fill gaps)
        all_angles = list(range(0, 360, 5))
        for angle in all_angles:
            if angle not in pattern_dict:
                # Find nearest neighbors
                prev_angle = None
                next_angle = None
                for offset in range(1, 180):
                    if prev_angle is None and (angle - offset * 5) % 360 in pattern_dict:
                        prev_angle = (angle - offset * 5) % 360
                    if next_angle is None and (angle + offset * 5) % 360 in pattern_dict:
                        next_angle = (angle + offset * 5) % 360
                    if prev_angle is not None and next_angle is not None:
                        break

                if prev_angle is not None and next_angle is not None:
                    # Linear interpolation
                    prev_gain = pattern_dict[prev_angle]
                    next_gain = pattern_dict[next_angle]
                    # Calculate distance (handling wrap-around)
                    dist_to_prev = (angle - prev_angle) % 360
                    dist_to_next = (next_angle - angle) % 360
                    total_dist = dist_to_prev + dist_to_next
                    if total_dist > 0:
                        weight = dist_to_prev / total_dist
                        interp_gain = prev_gain + weight * (next_gain - prev_gain)
                        pattern_dict[angle] = round(interp_gain, 1)

        # Detect and fix outliers (sudden jumps > 10dB from neighbors)
        angles = sorted(pattern_dict.keys())
        for i, angle in enumerate(angles):
            prev_angle = angles[(i - 1) % len(angles)]
            next_angle = angles[(i + 1) % len(angles)]

            curr_gain = pattern_dict[angle]
            prev_gain = pattern_dict[prev_angle]
            next_gain = pattern_dict[next_angle]

            # If current point jumps more than 10dB from BOTH neighbors, it's likely an outlier
            if abs(curr_gain - prev_gain) > 10 and abs(curr_gain - next_gain) > 10:
                # Replace with average of neighbors
                pattern_dict[angle] = round((prev_gain + next_gain) / 2, 1)

        # Apply light smoothing (3-point moving average)
        smoothed = {}
        for angle in angles:
            prev_angle = angles[(angles.index(angle) - 1) % len(angles)]
            next_angle = angles[(angles.index(angle) + 1) % len(angles)]

            # Weighted average: 25% prev, 50% current, 25% next
            smoothed_gain = (0.25 * pattern_dict[prev_angle] +
                            0.50 * pattern_dict[angle] +
                            0.25 * pattern_dict[next_angle])
            smoothed[angle] = round(smoothed_gain, 1)

        # Convert back to list of tuples
        return [(a, smoothed[a]) for a in sorted(smoothed.keys())]

    def _get_gain_at_angle(self, pattern_points, target_angle):
        """Helper to get gain at a specific angle from pattern points"""
        for angle, gain in pattern_points:
            if angle == target_angle:
                return f"{gain}dB"
        return "N/A"

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

    def extract_antenna_models_from_text(self, text):
        """Use LLM to extract antenna model metadata from text (without generating patterns)"""
        import json

        prompt = f"""Analyze this antenna datasheet text and extract information about EACH antenna model listed.

Return a JSON array of antenna objects. Each object should have:
- model: The exact model/part number
- manufacturer: Manufacturer name if found
- freq_range: Frequency range (e.g., "450-470 MHz")
- gain_dbi: Gain in dBi (convert from dBd by adding 2.15 if needed)
- type: "Directional" or "Omnidirectional"
- h_beamwidth: Horizontal beamwidth in degrees
- v_beamwidth: Vertical beamwidth in degrees

Look for tables or columns that list multiple models with different specifications.
If you find multiple distinct model numbers, return an entry for each one.

Example response for a datasheet with 3 antennas:
[
  {{"model": "DS4E06P18U-N", "manufacturer": "dbSpectra", "freq_range": "450-470 MHz", "gain_dbi": "6", "type": "Directional", "h_beamwidth": "180", "v_beamwidth": "65"}},
  {{"model": "DS4E08P12U-N", "manufacturer": "dbSpectra", "freq_range": "450-470 MHz", "gain_dbi": "8", "type": "Directional", "h_beamwidth": "120", "v_beamwidth": "45"}},
  {{"model": "DS7A12P90U-N", "manufacturer": "dbSpectra", "freq_range": "746-896 MHz", "gain_dbi": "12", "type": "Directional", "h_beamwidth": "90", "v_beamwidth": "30"}}
]

IMPORTANT: Return ONLY the JSON array, no other text.

DATASHEET TEXT:
{text[:4000]}
"""

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "rf-component-extractor", "prompt": prompt, "stream": False},
                timeout=120
            )
            response.raise_for_status()
            result = response.json().get("response", "")

            self._vlog(f"LLM model extraction response length: {len(result)}")

            # Parse JSON response
            # Clean up the response - remove markdown code blocks if present
            clean_result = result.strip()
            if clean_result.startswith("```"):
                clean_result = clean_result.split("```")[1]
                if clean_result.startswith("json"):
                    clean_result = clean_result[4:]
            if clean_result.endswith("```"):
                clean_result = clean_result[:-3]
            clean_result = clean_result.strip()

            models = json.loads(clean_result)

            if isinstance(models, list) and len(models) > 0:
                self._vlog(f"Extracted {len(models)} antenna models from text")
                return models

        except json.JSONDecodeError as e:
            self._vlog(f"Failed to parse model JSON: {e}")
        except Exception as e:
            self._vlog(f"Error extracting models: {e}")

        return []

    def generate_xml_for_antenna(self, model_info, pattern_points):
        """Generate XML for a single antenna using digitized pattern data"""
        xml_parts = ['<antenna>']
        xml_parts.append(f'<type>{model_info.get("type", "Directional")}</type>')
        xml_parts.append('<bays>1</bays>')

        # Add the digitized azimuth pattern
        xml_parts.append('<azimuth>')
        for angle, gain in pattern_points:
            xml_parts.append(f'<point angle="{angle}" gain="{gain}"/>')
        xml_parts.append('</azimuth>')

        # Default elevation
        xml_parts.append('<elevation>')
        xml_parts.append('<point angle="0" gain="0"/>')
        xml_parts.append('</elevation>')

        xml_parts.append('</antenna>')
        return '\n'.join(xml_parts)

    def query_llm_for_xml(self, text):
        """Query Ollama LLM to generate XML from text with improved prompting and validation"""
        text_to_send = text[:6000]  # Limit text length (increased for multi-antenna sheets)
        self._vlog(f"Preparing LLM prompt with {len(text_to_send)} characters")

        # IMPROVED PROMPT: Handles multi-antenna datasheets with realistic pattern generation
        prompt = f"""
Extract antenna data from this datasheet. This may contain MULTIPLE antenna models.

STEP 1 - IDENTIFY ALL ANTENNAS:
Look for multiple model numbers in tables or columns (e.g., DS4E06P18U-N, DS4E08P12U-N, DS7A12P90U-N).

STEP 2 - EXTRACT SPECS FOR EACH:
- Model/part number (exact from document)
- Frequency range (MHz)
- Gain in dBd (convert to dBi by adding 2.15)
- Horizontal beamwidth (degrees)
- Vertical beamwidth (degrees)
- Beam tilt (degrees, 0 if not specified)

STEP 3 - GENERATE REALISTIC AZIMUTH PATTERN:
The azimuth pattern MUST be based on horizontal beamwidth. Use this formula:
- At 0° (boresight): gain = 0 dB (reference)
- The -3dB points are at ±(beamwidth/2)
- The -10dB points are approximately at ±beamwidth
- Behind the antenna (180°): typically -20 to -25 dB

EXAMPLE for 90° horizontal beamwidth antenna:
<azimuth>
  <point angle="0" gain="0"/>
  <point angle="30" gain="-1.5"/>
  <point angle="45" gain="-3"/>
  <point angle="60" gain="-6"/>
  <point angle="90" gain="-12"/>
  <point angle="120" gain="-18"/>
  <point angle="150" gain="-22"/>
  <point angle="180" gain="-25"/>
  <point angle="210" gain="-22"/>
  <point angle="240" gain="-18"/>
  <point angle="270" gain="-12"/>
  <point angle="300" gain="-6"/>
  <point angle="315" gain="-3"/>
  <point angle="330" gain="-1.5"/>
</azimuth>

EXAMPLE for 120° horizontal beamwidth antenna:
<azimuth>
  <point angle="0" gain="0"/>
  <point angle="30" gain="-1"/>
  <point angle="60" gain="-3"/>
  <point angle="90" gain="-8"/>
  <point angle="120" gain="-15"/>
  <point angle="150" gain="-20"/>
  <point angle="180" gain="-25"/>
  <point angle="210" gain="-20"/>
  <point angle="240" gain="-15"/>
  <point angle="270" gain="-8"/>
  <point angle="300" gain="-3"/>
  <point angle="330" gain="-1"/>
</azimuth>

STEP 4 - OUTPUT FORMAT:
For MULTIPLE antennas:
<antennas>
  <antenna model="DS4E08P12U-N">
    <manufacturer>dbSpectra</manufacturer>
    <type>directional</type>
    <frequency_range>406-512 MHz</frequency_range>
    <gain_dbi>9.65</gain_dbi>
    <horizontal_beamwidth>120</horizontal_beamwidth>
    <vertical_beamwidth>27</vertical_beamwidth>
    <beam_tilt>0</beam_tilt>
    <azimuth>
      <point angle="0" gain="0"/>
      ... (pattern based on 120° beamwidth)
    </azimuth>
    <elevation>
      <point angle="0" gain="0"/>
    </elevation>
  </antenna>
</antennas>

For SINGLE antenna, omit the <antennas> wrapper.

CRITICAL RULES:
1. Gain at 0° MUST be 0 (it's the reference point)
2. Gains at other angles MUST be NEGATIVE (except 0°)
3. Pattern must match the beamwidth - wider beamwidth = slower rolloff
4. Extract ALL antennas from multi-model datasheets
5. NO markdown code blocks - raw XML only
6. If no data found: NO_ANTENNA_DATA_FOUND

Text to analyze:
{text_to_send}
"""

        try:
            self._vlog("Connecting to Ollama at http://localhost:11434...")
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "rf-component-extractor",
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            self._vlog(f"Ollama response status: {response.status_code}")

            result = response.json()
            self._vlog(f"LLM response keys: {result.keys()}")
            xml = result['response'].strip()
            self._vlog(f"LLM generated response length: {len(xml)} characters")
            self._vlog(f"Response preview: {xml[:300]}...")

            # Check if LLM said it couldn't find pattern data
            if "NO_PATTERN_DATA_FOUND" in xml or "NO_ANTENNA_DATA_FOUND" in xml or "no pattern data" in xml.lower():
                self._vlog("LLM reported: No pattern data found in source")
                raise Exception("LLM could not find antenna pattern data in the provided text. The document may not contain numerical pattern data.")

            # Strip markdown code blocks if present (```xml or ```)
            if xml.startswith('```'):
                self._vlog("Detected markdown code blocks, stripping...")
                # Remove opening code block
                lines = xml.split('\n')
                if lines[0].startswith('```'):
                    lines = lines[1:]  # Remove first line
                # Remove closing code block
                if lines and lines[-1].strip() == '```':
                    lines = lines[:-1]  # Remove last line
                xml = '\n'.join(lines).strip()
                self._vlog(f"After stripping: {xml[:300]}...")

            # Strip XML declaration if present
            xml_content = xml
            if xml_content.startswith('<?xml'):
                decl_end = xml_content.find('?>')
                if decl_end != -1:
                    xml_content = xml_content[decl_end + 2:].strip()

            # Check if this is a multi-antenna response
            if '<antennas>' in xml_content:
                self._vlog("Detected MULTI-ANTENNA response")
                # Parse and extract individual antennas
                try:
                    root = ET.fromstring(xml_content)
                    antenna_elements = root.findall('antenna')
                    self._vlog(f"Found {len(antenna_elements)} antennas in response")

                    # Store all antennas for selection
                    self.multi_antennas = []
                    for ant_elem in antenna_elements:
                        model = ant_elem.get('model', 'Unknown')
                        # Extract key specs for display
                        manufacturer = ant_elem.findtext('manufacturer', '')
                        freq_range = ant_elem.findtext('frequency_range', '')
                        gain = ant_elem.findtext('gain_dbi', '0')
                        ant_type = ant_elem.findtext('type', 'directional')
                        h_bw = ant_elem.findtext('horizontal_beamwidth', '')
                        v_bw = ant_elem.findtext('vertical_beamwidth', '')

                        # Convert element back to XML string
                        ant_xml = ET.tostring(ant_elem, encoding='unicode')

                        self.multi_antennas.append({
                            'model': model,
                            'manufacturer': manufacturer,
                            'freq_range': freq_range,
                            'gain_dbi': gain,
                            'type': ant_type,
                            'h_beamwidth': h_bw,
                            'v_beamwidth': v_bw,
                            'xml': ant_xml
                        })
                        self._vlog(f"  Antenna: {model} - {freq_range} - {gain} dBi")

                    # Return the first antenna but flag that there are multiple
                    self.has_multiple_antennas = True
                    return self.multi_antennas[0]['xml']

                except ET.ParseError as e:
                    self._vlog(f"ERROR parsing multi-antenna XML: {e}")
                    raise Exception(f"Failed to parse multi-antenna response: {e}")

            # Single antenna response
            self.has_multiple_antennas = False
            self.multi_antennas = []

            if not ('<antenna>' in xml_content or '<antenna ' in xml_content):
                self._vlog("ERROR: XML does not contain antenna element")
                self._vlog(f"XML starts with: {xml[:50]}")
                self._vlog(f"XML ends with: {xml[-50:]}")
                raise Exception("LLM did not return valid XML format with antenna element.")

            # Parse to ensure valid XML
            try:
                ET.fromstring(xml_content)
                self._vlog("SUCCESS: XML is valid and parseable")
            except ET.ParseError as e:
                self._vlog(f"ERROR: XML parse failed: {e}")
                self._vlog(f"Full XML:\n{xml}")
                raise Exception(f"Generated XML is invalid: {e}")

            # NEW: Validate that pattern looks realistic
            is_valid, validation_msg = self.validate_antenna_pattern(xml_content)
            if not is_valid:
                self._vlog(f"PATTERN VALIDATION FAILED: {validation_msg}")
                raise Exception(f"Generated pattern failed validation: {validation_msg}")

            self._vlog(f"PATTERN VALIDATION PASSED: {validation_msg}")
            return xml_content

        except requests.exceptions.RequestException as e:
            self._vlog(f"ERROR: Connection to Ollama failed: {e}")
            raise Exception(f"Failed to connect to Ollama. Ensure Ollama is running: {e}")
        except Exception as e:
            self._vlog(f"ERROR: LLM processing exception: {e}")
            raise Exception(f"LLM processing failed: {e}")

    def ok(self):
        # Check if user wants to import all antennas
        if getattr(self, 'import_all_antennas', False) and getattr(self, 'multi_antennas', []):
            self._vlog(f"Importing ALL {len(self.multi_antennas)} antennas")
            for i, ant in enumerate(self.multi_antennas):
                self._vlog(f"  Importing antenna {i+1}: {ant['model']}")
                metadata = {
                    'name': ant['model'],
                    'manufacturer': ant.get('manufacturer', ''),
                    'freq_range': ant.get('freq_range', ''),
                    'gain': str(ant.get('gain_dbi', '0')),
                    'type': ant.get('type', 'Directional'),
                }
                self.on_import_callback(ant['xml'], metadata)
        elif self.result:
            self._vlog("User clicked OK - importing antenna pattern")
            self.on_import_callback(self.result, getattr(self, 'metadata', {}))
        else:
            self._vlog("User clicked OK but no XML result to import")
            self.on_import_callback(None, {})
        self._vlog("="*80)
        self._vlog("AI ANTENNA IMPORT DIALOG CLOSED")
        self._vlog("="*80)
        self._close_verbose_log()
        self.dialog.destroy()

    def cancel(self):
        self._vlog("User cancelled antenna import")
        self._vlog("="*80)
        self._vlog("AI ANTENNA IMPORT DIALOG CLOSED (CANCELLED)")
        self._vlog("="*80)
        self._close_verbose_log()
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
        ttk.Button(button_frame, text="Save to Library", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.LEFT, padx=5)

        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def save(self):
        """Save the antenna metadata"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Antenna name is required")
            return

        try:
            gain = float(self.gain_var.get())
        except ValueError:
            messagebox.showerror("Error", "Invalid gain value")
            return

        self.result = {
            'name': name,
            'manufacturer': self.manufacturer_var.get().strip(),
            'part_number': self.part_number_var.get().strip(),
            'gain': gain,
            'band': self.band_var.get().strip(),
            'freq_range': self.freq_range_var.get().strip(),
            'type': self.type_var.get(),
            'notes': self.notes_text.get('1.0', tk.END).strip()
        }
        self.dialog.destroy()

    def cancel(self):
        """Cancel the dialog"""
        self.result = None
        self.dialog.destroy()


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