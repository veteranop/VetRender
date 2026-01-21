"""
VetRender Main Window - REFACTORED & FIXED
===========================================
Clean orchestration of all modules with ALL CRITICAL FIXES APPLIED:
✅ Segment-by-segment terrain diffraction (no shadow tunneling!)
✅ 360° azimuth sampling (no radial artifacts!)
✅ Simplified zoom (preserves overlays!)
✅ User-configurable terrain detail

This replaces the 2000-line monolithic main_window.py with clean module orchestration.
"""
import webbrowser
import urllib.parse
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import our refactored modules
from gui.map_display import MapDisplay
from gui.propagation_plot import PropagationPlot
from gui.info_panel import InfoPanel
from gui.toolbar import Toolbar
from gui.menus import MenuBar
from gui.dialogs import (TransmitterConfigDialog, AntennaInfoDialog,
                        CacheManagerDialog, ProjectSetupDialog, SetLocationDialog,
                        PlotsManagerDialog, AntennaImportDialog, AntennaMetadataDialog,
                        ManualAntennaDialog)

from controllers.propagation_controller import PropagationController

from models.antenna_models.antenna import AntennaPattern
from models.antenna_library import AntennaLibrary
from models.map_cache import MapCache
from models.terrain import TerrainHandler
from debug_logger import get_logger


class VetRender:
    """Main VetRender application with refactored architecture"""
    
    CONFIG_FILE = ".vetrender_config.json"
    
    def __init__(self, root):
        """Initialize VetRender application
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("VetRender - RF Propagation Tool")
        self.root.geometry("1400x900")
        
        # Initialize core components
        self.antenna_pattern = AntennaPattern()
        self.antenna_library = AntennaLibrary()
        self.current_antenna_id = None  # Track current antenna from library
        self.pattern_name = "Default Omni (0 dBi)"
        self.cache = MapCache()
        self.logger = get_logger()
        
        # Station parameters
        self.callsign = "KDPI"
        self.tx_type = "Broadcast FM"
        self.transmission_mode = "FM"
        self.tx_lat = 43.4665
        self.tx_lon = -112.0340
        self.erp = 40
        self.frequency = 88.5
        self.height = 30
        self.rx_height = 1.5  # Receiver height in meters
        self.max_distance = 100
        self.resolution = 500
        self.signal_threshold = -110
        self.terrain_quality = 'Medium'
        self.zoom = 13
        self.basemap = 'Esri WorldImagery'
        
        # Terrain calculation parameters
        self.terrain_azimuths = 3600  # 🔥 LOCKED at 3600 (0.1° resolution) - eliminates blocks
        self.terrain_distances = 2200  # High detail by default (updated for accuracy)
        
        # UI state
        self.use_terrain = tk.BooleanVar(value=False)
        self.show_coverage = tk.BooleanVar(value=True)
        self.show_shadow = tk.BooleanVar(value=False)
        
        # Propagation results
        self.last_propagation = None
        self.last_terrain_loss = None
        self.saved_plots = []
        
        # Context menu state
        self.click_x = 0
        self.click_y = 0
        
        # Try to load previous config
        config_loaded = self.load_auto_config()
        
        # Setup UI
        self.setup_ui()
        
        # Load map
        self.map_display.load_map(self.tx_lat, self.tx_lon, self.zoom, 
                                  self.basemap, self.cache)
        self.map_display.display_map_only(self.tx_lat, self.tx_lon, show_marker=True)
        
        # Update info
        self.info_panel.update(
            self.callsign, self.frequency, self.transmission_mode, self.tx_type,
            self.tx_lat, self.tx_lon, self.height, self.rx_height, self.erp, self.pattern_name,
            self.max_distance, self.signal_threshold, 
            self.use_terrain.get(), self.terrain_quality
        )
        
        # Show project setup if no config
        if not config_loaded:
            self.root.after(100, self.show_project_setup)
        
        # Register close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.logger.log("VetRender application started (REFACTORED)")
    
    def setup_ui(self):
        """Setup user interface with all modules"""
        # Create matplotlib figure
        self.fig = Figure(dpi=100, frameon=False)
        self.fig.subplots_adjust(left=0, right=0.98, top=1, bottom=0, wspace=0, hspace=0)
        self.ax = self.fig.add_subplot(111)
        
        # Initialize display modules
        self.map_display = MapDisplay(self.ax, None)  # Canvas set below
        self.propagation_plot = PropagationPlot(self.ax, None, self.fig)  # Canvas set below
        self.propagation_controller = PropagationController(self.antenna_pattern)
        
        # Setup menu bar
        menu_vars = {
            'basemap_var': tk.StringVar(value=self.basemap),
            'show_coverage_var': self.show_coverage,
            'show_shadow_var': self.show_shadow,
            'use_terrain_var': self.use_terrain,
            'max_dist_var': tk.StringVar(value=str(self.max_distance)),
            'quality_var': tk.StringVar(value=self.terrain_quality),
            'terrain_detail_var': tk.StringVar(value=str(self.terrain_distances))
        }
        
        self.menubar = MenuBar(self.root, self.get_menu_callbacks(), menu_vars)
        
        # Setup toolbar
        self.toolbar = Toolbar(self.root, self.get_toolbar_callbacks())
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.toolbar.set_zoom(self.zoom)
        self.toolbar.set_quality(self.terrain_quality)
        self.toolbar.set_custom_values(self.terrain_azimuths, self.terrain_distances)
        self.toolbar.update_location(self.tx_lat, self.tx_lon)
        
        # Main content area
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Info panel on left
        self.info_panel = InfoPanel(content_frame)
        self.info_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0), pady=5)
        self.info_panel.add_button("Edit Station Info", self.edit_station_info)
        self.info_panel.add_button("Plots", self.show_plots_manager)
        
        # Map area on right
        map_frame = ttk.Frame(content_frame, padding="0")
        map_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Set canvas in display modules
        self.map_display.canvas = self.canvas
        self.propagation_plot.canvas = self.canvas
        
        # Connect events
        self.canvas.mpl_connect('button_press_event', self.on_map_click)
        # self.canvas.mpl_connect('scroll_event', self.on_scroll_zoom)  # Disabled - use toolbar zoom
        
        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Set Transmitter Location (Click)", 
                                     command=self.set_tx_location)
        self.context_menu.add_command(label="Set Transmitter Location (Coordinates)...",
                                     command=self.set_tx_location_precise)
        self.context_menu.add_command(label="Probe Signal Strength Here",
                                     command=self.probe_signal)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit Transmitter Configuration",
                                     command=self.edit_tx_config)
        self.context_menu.add_command(label="Edit Antenna Information",
                                     command=self.edit_antenna_info)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Manage Cache...",
                                     command=self.manage_cache)
        
        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-s>', lambda e: self.save_project())
        self.root.bind('<Control-o>', lambda e: self.load_project())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<F1>', lambda e: self.show_help())
    
    def get_toolbar_callbacks(self):
        """Get toolbar callback dictionary"""
        return {
            'on_zoom_change': self.on_zoom_change,
            'on_refresh_map': self.refresh_map_dialog,
            'on_quality_change': self.on_quality_change,
            'on_calculate': self.calculate_propagation,
            'on_transparency_change': self.on_transparency_change,
            'on_new_project': self.new_project,
            'on_save_project': self.save_project,
            'on_load_project': self.load_project
        }
    
    def get_menu_callbacks(self):
        """Get menu callback dictionary"""
        return {
            'on_new_project': self.new_project,
            'on_save_project': self.save_project,
            'on_load_project': self.load_project,
            'on_ai_assistant': self.ai_antenna_assistant,
            'on_ai_import_antenna': self.import_antenna_pattern,
            'on_manual_import': self.manual_import_antenna,
            'on_create_manual_antenna': self.create_manual_antenna,
            'on_view_antennas': self.view_antennas,
            'on_export_antenna': self.export_antenna,
            # 'on_toggle_live_probe': self.toggle_live_probe,  # Temporarily disabled
            'on_exit': self.on_closing,
            'on_basemap_change': self.on_basemap_change,
            'on_toggle_coverage': self.toggle_coverage_overlay,
            'on_toggle_shadow': self.update_shadow_display,
            'on_max_distance_change': self.on_max_distance_change,
            'on_custom_distance': self.set_custom_distance,
            'on_toggle_terrain': lambda: None,  # Handled by checkbox variable
            'on_quality_change': self.on_quality_change,
            'on_terrain_detail_change': self.on_terrain_detail_change,
            'on_custom_terrain_detail': self.set_custom_terrain_detail,
            'on_set_antenna': self.manual_import_antenna,
        }


    def calculate_propagation(self):
        """Calculate RF propagation coverage - orchestrates the controller"""
        try:
            # Update max distance from UI
            try:
                self.max_distance = float(self.menubar.vars['max_dist_var'].get())
            except ValueError:
                self.max_distance = 100
            
            self.toolbar.set_status("Calculating propagation...")
            self.root.update()
            
            # Get custom values if in custom quality mode
            custom_az = None
            custom_dist = None
            if self.terrain_quality == 'Custom':
                custom_az, custom_dist = self.toolbar.get_custom_values()
            
            # Get propagation model from toolbar
            propagation_model = self.toolbar.get_propagation_model()

            # Define progress callback for real-time rendering
            def progress_callback(percent, partial_terrain, distances, azimuths):
                try:
                    self.toolbar.set_status(f"Calculating... {percent}%")
                    self.root.update_idletasks()
                except Exception as e:
                    # Log error but don't crash the calculation
                    print(f"Progress callback error: {e}")

            # 🔥 ALL FIXES ARE IN THE CONTROLLER!
            result = self.propagation_controller.calculate_coverage(
                self.tx_lat, self.tx_lon, self.height, self.erp, self.frequency,
                self.max_distance, self.resolution, self.signal_threshold, self.rx_height,
                self.use_terrain.get(), self.terrain_quality,
                custom_az, custom_dist, propagation_model=propagation_model,
                progress_callback=progress_callback
            )
            
            if result is None:
                messagebox.showerror("Error", "Propagation calculation failed")
                self.toolbar.set_status("Calculation failed")
                return
            
            x_grid, y_grid, rx_power_grid, terrain_loss_grid, stats = result
            
            # Store results
            self.last_propagation = (x_grid, y_grid, rx_power_grid)
            self.last_terrain_loss = terrain_loss_grid if self.use_terrain.get() else None
            
            # Get transmitter pixel position
            tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
                self.tx_lat, self.tx_lon
            )
            
            # Plot coverage
            self.propagation_plot.plot_coverage(
                self.map_display.map_image,
                tx_pixel_x, tx_pixel_y,
                x_grid, y_grid, rx_power_grid,
                self.signal_threshold,
                self.map_display.get_pixel_scale(),
                terrain_loss_grid,
                self.show_shadow.get(),
                (self.map_display.plot_xlim, self.map_display.plot_ylim),
                alpha=self.toolbar.get_transparency()
            )
            
            # Auto-enable coverage overlay
            self.show_coverage.set(True)
            
            # Save plot to history
            self.save_current_plot_to_history()
            
            # Update status
            eirp = stats['max_power'] + (self.erp - stats['max_power'])
            self.toolbar.set_status(f"Coverage calculated - {stats['points_above_threshold']}/{stats['total_points']} points above threshold")
            
            print(f"Coverage calculation complete!")
            print(f"Stats: {stats}")
            
        except Exception as e:
            print(f"ERROR in calculate_propagation: {e}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Calculation error: {e}")
            self.toolbar.set_status("Error in calculation")
    
    # ========================================================================
    # MAP INTERACTION
    # ========================================================================
    
    def on_map_click(self, event):
        """Handle mouse clicks on map"""
        if event.inaxes == self.ax and self.map_display.map_image:
            if event.button == 3:  # Right click
                self.click_x = event.xdata
                self.click_y = event.ydata
                try:
                    self.context_menu.tk_popup(int(event.guiEvent.x_root), 
                                              int(event.guiEvent.y_root))
                finally:
                    self.context_menu.grab_release()
    
    def on_scroll_zoom(self, event):
        """Handle scroll wheel zoom"""
        self.map_display.handle_scroll_zoom(event)
    
    def set_tx_location(self):
        """Set transmitter location from click"""
        lat, lon = self.map_display.pixel_to_latlon(self.click_x, self.click_y)
        
        if lat is not None:
            print(f"Transmitter moved to: Lat={lat:.6f}, Lon={lon:.6f}")
            self.tx_lat = lat
            self.tx_lon = lon
            self.toolbar.update_location(lat, lon)
            self.update_info_panel()
            self.reload_map()
            self.save_auto_config()
    
    def set_tx_location_precise(self):
        """Set transmitter location with coordinates dialog"""
        dialog = SetLocationDialog(self.root, self.tx_lat, self.tx_lon)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.tx_lat = dialog.result['lat']
            self.tx_lon = dialog.result['lon']
            self.toolbar.update_location(self.tx_lat, self.tx_lon)
            self.update_info_panel()
            self.reload_map()
            self.save_auto_config()
    
    def probe_signal(self):
        """Probe signal strength at clicked location"""
        if self.last_propagation is None:
            messagebox.showinfo("No Coverage Data",
                              "Calculate coverage first before probing signal strength.")
            return
        
        x_grid, y_grid, rx_power_grid = self.last_propagation
        tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
            self.tx_lat, self.tx_lon
        )
        
        signal, distance, azimuth = self.propagation_plot.get_signal_at_pixel(
            self.click_x, self.click_y, tx_pixel_x, tx_pixel_y,
            x_grid, y_grid, rx_power_grid,
            self.map_display.get_pixel_scale()
        )
        
        if signal is not None:
            probe_lat, probe_lon = self.map_display.pixel_to_latlon(
                self.click_x, self.click_y
            )
            
            # Assess quality
            if signal > -70:
                quality = "Excellent"
            elif signal > -85:
                quality = "Good"
            elif signal > -95:
                quality = "Fair"
            elif signal > -110:
                quality = "Poor"
            else:
                quality = "No Signal"
            
            info = f"Signal Strength Probe\n\n"
            info += f"Location: {probe_lat:.6f}, {probe_lon:.6f}\n"
            info += f"Distance from TX: {distance:.2f} km\n"
            info += f"Azimuth from TX: {azimuth:.1f}°\n"
            info += f"Signal Strength: {signal:.2f} dBm\n\n"
            info += f"Signal Quality: {quality}"
            
            messagebox.showinfo("Signal Probe Results", info)
        else:
            messagebox.showwarning("Probe Failed", 
                                 "Click location is outside coverage area")
    
    # ========================================================================
    # UI CALLBACKS
    # ========================================================================
    
    def on_zoom_change(self):
        """Handle zoom level change"""
        self.zoom = self.toolbar.get_zoom()
        self.reload_map()
    
    def on_basemap_change(self):
        """Handle basemap change"""
        self.basemap = self.menubar.vars['basemap_var'].get()
        print(f"Basemap changed to: {self.basemap}")
        self.reload_map()
        self.save_auto_config()
    
    def on_quality_change(self, quality=None):
        """Handle quality preset change"""
        if quality is None:
            quality = self.toolbar.get_quality()
        
        self.terrain_quality = quality
        
        # Update terrain parameters based on preset
        presets = {
            'Low': (180, 100),
            'Medium': (540, 200),
            'High': (720, 300),
            'Ultra': (1080, 500)
        }
        
        if quality in presets:
            self.terrain_azimuths, self.terrain_distances = presets[quality]
            self.toolbar.set_custom_values(self.terrain_azimuths, self.terrain_distances)
            self.toolbar.hide_custom_controls()
        elif quality == 'Custom':
            self.toolbar.show_custom_controls()
        
        print(f"Quality: {quality} - Az: {self.terrain_azimuths}, Pts: {self.terrain_distances}")
    
    def on_transparency_change(self):
        """Handle transparency slider change - redraw overlay with new alpha"""
        if self.last_propagation is not None and self.show_coverage.get():
            # Save current zoom state BEFORE redrawing
            current_xlim = self.ax.get_xlim()
            current_ylim = self.ax.get_ylim()
            
            x_grid, y_grid, rx_power_grid = self.last_propagation
            tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
                self.tx_lat, self.tx_lon
            )
            alpha = self.toolbar.get_transparency()
            self.propagation_plot.plot_coverage(
                self.map_display.map_image, tx_pixel_x, tx_pixel_y,
                x_grid, y_grid, rx_power_grid, self.signal_threshold,
                self.map_display.get_pixel_scale(),
                self.last_terrain_loss, self.show_shadow.get(),
                (current_xlim, current_ylim),  # Pass saved limits!
                alpha=alpha
            )
    
    def on_terrain_detail_change(self, detail):
        """Handle terrain detail change"""
        self.terrain_distances = int(detail)
        self.toolbar.set_custom_values(self.terrain_azimuths, self.terrain_distances)
        print(f"Terrain detail set to {self.terrain_distances} points per radial")
    
    def set_custom_terrain_detail(self):
        """Set custom terrain detail via dialog"""
        current = int(self.menubar.vars['terrain_detail_var'].get())
        new_detail = simpledialog.askinteger(
            "Custom Terrain Detail",
            "Enter number of elevation points per radial:\n\n"
            "(Higher = more accurate, slower)\n\n"
            "Presets: Low=1000, Med=2200, High=4000, Ultra=5000\n"
            "Note: Azimuth locked at 3600 for all quality levels",
            initialvalue=current, minvalue=50, maxvalue=10000
        )
        
        if new_detail is not None:
            self.menubar.vars['terrain_detail_var'].set(str(new_detail))
            self.on_terrain_detail_change(str(new_detail))
    
    def on_max_distance_change(self):
        """Handle max distance change"""
        try:
            self.max_distance = float(self.menubar.vars['max_dist_var'].get())
            if self.last_propagation is not None:
                self.toolbar.set_status(
                    "Distance changed - recalculate coverage for new area"
                )
        except ValueError:
            pass
    
    def set_custom_distance(self):
        """Set custom coverage distance"""
        current = float(self.menubar.vars['max_dist_var'].get()) if self.menubar.vars['max_dist_var'].get() else 100
        new_distance = simpledialog.askfloat(
            "Custom Coverage Distance",
            "Enter coverage radius (km):",
            initialvalue=current, minvalue=1, maxvalue=500
        )
        
        if new_distance is not None:
            self.menubar.vars['max_dist_var'].set(str(int(new_distance)))
            self.on_max_distance_change()
    
    def toggle_coverage_overlay(self):
        """Toggle coverage overlay visibility"""
        if self.last_propagation is not None:
            if self.show_coverage.get():
                # Show coverage
                x_grid, y_grid, rx_power_grid = self.last_propagation
                tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
                    self.tx_lat, self.tx_lon
                )
                self.propagation_plot.plot_coverage(
                    self.map_display.map_image, tx_pixel_x, tx_pixel_y,
                    x_grid, y_grid, rx_power_grid, self.signal_threshold,
                    self.map_display.get_pixel_scale(),
                    self.last_terrain_loss, self.show_shadow.get(),
                    (self.map_display.plot_xlim, self.map_display.plot_ylim),
                    alpha=self.toolbar.get_transparency()
                )
                self.toolbar.set_status("Coverage overlay shown")
            else:
                # Hide coverage
                self.map_display.display_map_only(self.tx_lat, self.tx_lon, show_marker=True)
                self.toolbar.set_status("Coverage overlay hidden")
        else:
            self.show_coverage.set(False)
            self.toolbar.set_status("No coverage data - calculate propagation first")
    
    def update_shadow_display(self):
        """Update shadow zone display"""
        if self.last_propagation is not None and self.show_coverage.get():
            x_grid, y_grid, rx_power_grid = self.last_propagation
            tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
                self.tx_lat, self.tx_lon
            )
            self.propagation_plot.plot_coverage(
                self.map_display.map_image, tx_pixel_x, tx_pixel_y,
                x_grid, y_grid, rx_power_grid, self.signal_threshold,
                self.map_display.get_pixel_scale(),
                self.last_terrain_loss, self.show_shadow.get(),
                (self.map_display.plot_xlim, self.map_display.plot_ylim),
                alpha=self.toolbar.get_transparency()
            )
    
    # ========================================================================
    # DIALOGS
    # ========================================================================
    
    def edit_tx_config(self):
        """Edit transmitter configuration"""
        dialog = TransmitterConfigDialog(self.root, self.erp, self.frequency,
                                        self.height, self.rx_height, self.signal_threshold)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            self.erp, self.frequency, self.height, self.rx_height, self.signal_threshold = dialog.result
            self.update_info_panel()
            self.toolbar.set_status(f"Config updated - ERP: {self.erp} dBm, Freq: {self.frequency} MHz")
            self.save_auto_config()
    
    def edit_antenna_info(self):
        """Edit antenna information"""
        dialog = AntennaInfoDialog(self.root, self.pattern_name)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            action, data = dialog.result
            if action == 'load':
                if self.antenna_pattern.load_from_xml(data):
                    self.pattern_name = data.split('/')[-1].split('\\')[-1]
                    self.toolbar.set_status(f"Antenna pattern loaded: {self.pattern_name}")
                    self.save_auto_config()
                else:
                    messagebox.showerror("Error", "Failed to load antenna pattern")
            elif action == 'reset':
                self.antenna_pattern.load_default_omni()
                self.pattern_name = "Default Omni (0 dBi)"
                self.toolbar.set_status("Reset to default omnidirectional antenna")
                self.save_auto_config()
    
    def manage_cache(self):
        """Open cache management dialog"""
        CacheManagerDialog(self.root, self.cache)
    
    def edit_station_info(self):
        """Edit station information"""
        current_config = {
            'callsign': self.callsign,
            'frequency': self.frequency,
            'tx_type': self.tx_type,
            'transmission_mode': self.transmission_mode,
            'tx_lat': self.tx_lat,
            'tx_lon': self.tx_lon,
            'height': self.height,
            'rx_height': self.rx_height,
            'erp': self.erp,
            'zoom': self.zoom,
            'basemap': self.basemap,
            'radius': self.max_distance
        }
        
        dialog = ProjectSetupDialog(self.root, existing_config=current_config)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result is not None:
            self.callsign = dialog.result.get('callsign', self.callsign)
            self.frequency = dialog.result.get('frequency', self.frequency)
            self.tx_type = dialog.result.get('tx_type', self.tx_type)
            self.transmission_mode = dialog.result.get('transmission_mode', self.transmission_mode)
            self.tx_lat = dialog.result['tx_lat']
            self.tx_lon = dialog.result['tx_lon']
            self.height = dialog.result.get('height', self.height)
            self.rx_height = dialog.result.get('rx_height', self.rx_height)
            self.erp = dialog.result.get('erp', self.erp)
            self.zoom = dialog.result['zoom']
            self.basemap = dialog.result['basemap']
            self.max_distance = dialog.result['radius']
            
            self.toolbar.update_location(self.tx_lat, self.tx_lon)
            self.toolbar.set_zoom(self.zoom)
            self.menubar.vars['basemap_var'].set(self.basemap)
            self.menubar.vars['max_dist_var'].set(str(self.max_distance))
            
            self.reload_map()
            self.update_info_panel()
            self.save_auto_config()
    
    def show_plots_manager(self):
        """Show plots manager dialog"""
        if len(self.saved_plots) == 0:
            messagebox.showinfo("No Plots",
                              "No coverage plots have been calculated yet.\n\n"
                              "Calculate coverage first to save plots.")
            return
        
        dialog = PlotsManagerDialog(self.root, self.saved_plots, self)
        self.root.wait_window(dialog.dialog)
    
    # ========================================================================
    # PROJECT MANAGEMENT
    # ========================================================================
    
    def new_project(self):
        """Start new project"""
        # Reset to defaults
        self.callsign = "KDPI"
        self.tx_type = "Broadcast FM"
        self.transmission_mode = "FM"
        self.tx_lat = 43.4665
        self.tx_lon = -112.0340
        self.erp = 40
        self.frequency = 88.5
        self.height = 30
        self.max_distance = 100
        self.signal_threshold = -110
        self.terrain_quality = 'Medium'
        self.basemap = 'Esri WorldImagery'
        self.zoom = 13
        
        self.last_propagation = None
        self.last_terrain_loss = None
        self.saved_plots = []
        
        self.toolbar.update_location(self.tx_lat, self.tx_lon)
        self.toolbar.set_zoom(self.zoom)
        self.show_coverage.set(True)
        self.show_shadow.set(False)
        
        self.reload_map(preserve_propagation=False)
        self.update_info_panel()
        self.show_project_setup()
    
    def save_project(self):
        """Save project with terrain and land cover cache data"""
        from tkinter import filedialog
        from models.terrain import TerrainHandler

        filename = filedialog.asksaveasfilename(
            title="Save Project",
            defaultextension=".vtr",
            filetypes=[("VetRender Project", "*.vtr"), ("All Files", "*.*")],
            initialfile=f"{self.callsign}.vtr"
        )

        if filename:
            try:
                print("Saving project with cached data...")

                # Export terrain cache for coverage area
                terrain_cache_data = TerrainHandler.export_cache_for_area(
                    self.tx_lat, self.tx_lon, self.max_distance
                )

                # Export land cover cache if available
                land_cover_cache_data = None
                if hasattr(self, 'propagation_controller') and self.propagation_controller.land_cover_handler:
                    try:
                        land_cover_cache_data = self.propagation_controller.land_cover_handler.export_cache()
                    except:
                        pass

                project_data = {
                    'version': '3.1',  # Bumped for cache support
                    'callsign': self.callsign,
                    'tx_type': self.tx_type,
                    'transmission_mode': self.transmission_mode,
                    'tx_lat': self.tx_lat,
                    'tx_lon': self.tx_lon,
                    'erp': self.erp,
                    'frequency': self.frequency,
                    'height': self.height,
                    'max_distance': self.max_distance,
                    'signal_threshold': self.signal_threshold,
                    'terrain_quality': self.terrain_quality,
                    'pattern_name': self.pattern_name,
                    'zoom': self.zoom,
                    'basemap': self.basemap,
                    'saved_plots': self.saved_plots,

                    # Cached data for offline use
                    'terrain_cache': terrain_cache_data,
                    'land_cover_cache': land_cover_cache_data,
                }

                with open(filename, 'w') as f:
                    json.dump(project_data, f, indent=2)

                cache_info = f"Terrain cache: {len(terrain_cache_data) if terrain_cache_data else 0} points"
                if land_cover_cache_data:
                    cache_info += f"\nLand cover: {len(land_cover_cache_data.get('water', []))} water + {len(land_cover_cache_data.get('urban', []))} urban features"

                messagebox.showinfo("Success",
                                  f"Project saved to:\n{filename}\n\n"
                                  f"Included {len(self.saved_plots)} coverage plots\n"
                                  f"{cache_info}")
                print(f"  Saved terrain cache: {len(terrain_cache_data) if terrain_cache_data else 0} points")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save project:\n{e}")
    
    def load_project(self):
        """Load project with terrain and land cover cache data"""
        from tkinter import filedialog
        from models.terrain import TerrainHandler

        filename = filedialog.askopenfilename(
            title="Load Project",
            filetypes=[("VetRender Project", "*.vtr"), ("All Files", "*.*")]
        )

        if filename:
            try:
                with open(filename, 'r') as f:
                    project_data = json.load(f)

                print("Loading project with cached data...")

                # Load parameters
                self.callsign = project_data.get('callsign', 'UNKNOWN')
                self.tx_type = project_data.get('tx_type', 'Unknown')
                self.transmission_mode = project_data.get('transmission_mode', 'Unknown')
                self.tx_lat = project_data.get('tx_lat', 43.4665)
                self.tx_lon = project_data.get('tx_lon', -112.0340)
                self.erp = project_data.get('erp', 40)
                self.frequency = project_data.get('frequency', 88.5)
                self.height = project_data.get('height', 30)
                self.max_distance = project_data.get('max_distance', 100)
                self.signal_threshold = project_data.get('signal_threshold', -110)
                self.terrain_quality = project_data.get('terrain_quality', 'Medium')
                self.pattern_name = project_data.get('pattern_name', 'Default Omni (0 dBi)')
                self.zoom = 10  # Always start at zoom 10
                self.basemap = project_data.get('basemap', 'Esri WorldImagery')
                self.saved_plots = project_data.get('saved_plots', [])

                # Import terrain cache if available
                terrain_cache_data = project_data.get('terrain_cache')
                if terrain_cache_data:
                    TerrainHandler.import_cache(terrain_cache_data)
                    print(f"  Loaded terrain cache: {len(terrain_cache_data)} points")

                # Import land cover cache if available
                land_cover_cache_data = project_data.get('land_cover_cache')
                if land_cover_cache_data and hasattr(self, 'propagation_controller') and self.propagation_controller.land_cover_handler:
                    try:
                        self.propagation_controller.land_cover_handler.import_cache(land_cover_cache_data)
                        print(f"  Loaded land cover cache")
                    except Exception as e:
                        print(f"  Land cover cache load failed: {e}")

                # Update UI
                self.toolbar.update_location(self.tx_lat, self.tx_lon)
                self.toolbar.set_zoom(10)
                self.menubar.vars['basemap_var'].set(self.basemap)
                self.menubar.vars['max_dist_var'].set(str(self.max_distance))
                self.toolbar.set_quality(self.terrain_quality)
                self.on_quality_change()

                self.update_info_panel()
                self.last_propagation = None
                self.reload_map(preserve_propagation=False)

                cache_info = ""
                if terrain_cache_data:
                    cache_info = f"\n\nTerrain cache: {len(terrain_cache_data)} points loaded"
                if land_cover_cache_data:
                    cache_info += f"\nLand cover cache loaded"

                messagebox.showinfo("Success",
                                  f"Project loaded:\n{self.callsign}\n\n"
                                  f"{len(self.saved_plots)} coverage plots restored{cache_info}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load project:\n{e}")

    def import_antenna_pattern(self):
        """Import antenna pattern from website or PDF using LLM"""
        self.logger.log("="*80)
        self.logger.log("AI ANTENNA IMPORT STARTED")
        self.logger.log("="*80)
        
        def on_import(xml_content, initial_metadata=None):
            # Ask user for metadata
            self.logger.log("Asking user for antenna metadata...")
            metadata_dialog = AntennaMetadataDialog(self.root, initial_values=initial_metadata)
            self.root.wait_window(metadata_dialog.dialog)
            
            if not metadata_dialog.result:
                self.logger.log("User cancelled metadata entry")
                messagebox.showinfo("Cancelled", "Antenna import cancelled.")
                return
            
            metadata = metadata_dialog.result
            antenna_name = metadata['name']
            
            self.logger.log(f"Saving antenna to library: {antenna_name}")
            
            # Save to antenna library
            success = self.antenna_library.add_antenna(antenna_name, xml_content, metadata)
            
            if not success:
                self.logger.log("ERROR: Failed to save antenna to library")
                messagebox.showerror("Error", "Failed to save antenna to library.")
                return
            
            self.logger.log(f"SUCCESS: Antenna '{antenna_name}' saved to library")
            
            # Load the antenna pattern
            antenna_list = self.antenna_library.list_antennas()
            if antenna_list:
                # Get the ID of the antenna we just added (last one)
                new_antenna_id = antenna_list[-1][0]
                self.load_antenna_from_library(new_antenna_id)
                
                self.logger.log(f"Loaded antenna pattern: {antenna_name}")
                messagebox.showinfo("Success", 
                    f"Antenna '{antenna_name}' imported and loaded successfully!\n\n"
                    f"It has been saved to your antenna library.")
            else:
                self.logger.log("ERROR: Could not find newly added antenna")
                messagebox.showerror("Error", "Antenna saved but could not load it.")

        dialog = AntennaImportDialog(self.root, on_import)
        self.root.wait_window(dialog.dialog)
        self.logger.log("="*80)
        self.logger.log("AI ANTENNA IMPORT COMPLETED")
        self.logger.log("="*80)

    def ai_antenna_assistant(self):
        """Check/install/start Ollama for AI Antenna Assistant"""
        import subprocess
        import os

        self.logger.log("="*80)
        self.logger.log("AI ANTENNA ASSISTANT - BUTTON CLICKED")
        self.logger.log("="*80)

        # Check if Ollama is installed
        if not self.is_ollama_installed():
            self.logger.log("Ollama not found - asking user to install")
            # Ask user if they want to install
            response = messagebox.askyesno(
                "Ollama Not Found",
                "Ollama AI Assistant is not installed or not found in PATH.\n\n"
                "Would you like to install it now?\n\n"
                "(This will download ~850MB)"
            )
            if response:
                self.install_ollama()
            else:
                self.logger.log("User declined Ollama installation")
            self.logger.log("="*80)
            self.logger.log("AI ANTENNA ASSISTANT - CHECK COMPLETED")
            self.logger.log("="*80)
            return
        
        # Ollama is installed, check if server is running
        self.logger.log("AI Assistant: Ollama is installed")
        
        if self.is_ollama_server_running():
            self.logger.log("AI Assistant: Server is already running")
            messagebox.showinfo(
                "Ready", 
                "Ollama is installed and running!\n\n"
                "You can now use AI Antenna Import from the Tools menu."
            )
        else:
            self.logger.log("AI Assistant: Server not running, attempting to start...")
            self.start_ollama_server()
        
        self.logger.log("="*80)
        self.logger.log("AI ANTENNA ASSISTANT - CHECK COMPLETED")
        self.logger.log("="*80)

    def is_ollama_installed(self):
        """Check if Ollama is installed"""
        import subprocess
        self.logger.log("Checking if Ollama is installed...")
        try:
            result = subprocess.run(['ollama', '--version'], capture_output=True, text=True, timeout=10)
            installed = result.returncode == 0
            if installed:
                version = result.stdout.strip()
                self.logger.log(f"Ollama found: {version}")
            else:
                self.logger.log(f"Ollama command failed with return code: {result.returncode}")
            return installed
        except subprocess.TimeoutExpired:
            self.logger.log("Ollama check timed out")
            return False
        except FileNotFoundError:
            self.logger.log("Ollama executable not found in PATH")
            return False

    def is_ollama_server_running(self):
        """Check if Ollama server is running"""
        self.logger.log("Checking if Ollama server is running...")
        try:
            import requests
            response = requests.get('http://localhost:11434/api/tags', timeout=5)
            running = response.status_code == 200
            if running:
                self.logger.log("Ollama server is responding on port 11434")
                # Log available models
                data = response.json()
                if 'models' in data:
                    model_names = [m.get('name', 'unknown') for m in data.get('models', [])]
                    self.logger.log(f"Available models: {model_names}")
            else:
                self.logger.log(f"Ollama server responded with status: {response.status_code}")
            return running
        except Exception as e:
            self.logger.log(f"Ollama server check failed: {e}")
            return False

    def start_ollama_server(self):
        """Start Ollama server in background"""
        import subprocess
        self.logger.log("Attempting to start Ollama server...")
        try:
            process = subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.logger.log(f"AI Assistant: Started Ollama server (PID: {process.pid})")
            self.logger.log("Waiting 2 seconds for server initialization...")
            import time
            time.sleep(2)
            self.logger.log("Ollama server should now be ready")
            messagebox.showinfo("Started", "Ollama server started!\n\nGive it a moment to initialize, then use AI Antenna Import.")
        except FileNotFoundError:
            self.logger.log("AI Assistant: Failed to start server - ollama executable not found")
            messagebox.showerror("Error", "Failed to start Ollama server: ollama command not found in PATH")
        except Exception as e:
            self.logger.log(f"AI Assistant: Failed to start server: {str(e)}")
            messagebox.showerror("Error", f"Failed to start Ollama server: {str(e)}")

    def install_ollama(self):
        """Install Ollama using the script"""
        import subprocess
        self.logger.log("="*80)
        self.logger.log("OLLAMA INSTALLATION INITIATED")
        self.logger.log("="*80)
        
        script_path = os.path.join(os.path.dirname(__file__), '..', 'install_ollama.ps1')
        script_path = os.path.abspath(script_path)

        self.logger.log(f"AI Assistant: Looking for script at {script_path}")

        if not os.path.exists(script_path):
            self.logger.log(f"AI Assistant: Script not found at {script_path}")
            messagebox.showerror("Error", f"Installation script not found at {script_path}. Please reinstall VetRender.")
            self.logger.log("="*80)
            self.logger.log("OLLAMA INSTALLATION ABORTED - SCRIPT NOT FOUND")
            self.logger.log("="*80)
            return
        
        self.logger.log(f"Script found, size: {os.path.getsize(script_path)} bytes")

        # Show progress message
        messagebox.showinfo("Installing", 
            "Starting Ollama installation...\n\n"
            "This will take 5-10 minutes. The window may appear frozen.\n\n"
            "Please be patient and do NOT close VetRender.")
        self.logger.log("Starting installation...")
        
        # Update UI to show we're working
        self.root.update()

        try:
            self.logger.log("AI Assistant: Running PowerShell install script...")
            self.logger.log(f"Command: powershell.exe -ExecutionPolicy Bypass -File {script_path}")
            
            # Create a temporary log file for script output
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.log', delete=False) as temp_log:
                temp_log_path = temp_log.name
            
            self.logger.log(f"Script output will be logged to: {temp_log_path}")
            
            # Run PowerShell script with output redirected to file
            # This prevents blocking on large output
            with open(temp_log_path, 'w') as output_file:
                result = subprocess.run(
                    ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', script_path],
                    stdout=output_file,
                    stderr=subprocess.STDOUT,
                    timeout=600,  # 10 min timeout
                    text=True
                )
            
            # Read the output
            try:
                with open(temp_log_path, 'r') as output_file:
                    script_output = output_file.read()
                os.unlink(temp_log_path)  # Clean up temp file
            except Exception as e:
                self.logger.log(f"Warning: Could not read temp log file: {e}")
                script_output = "(Could not read script output)"

            self.logger.log(f"AI Assistant: Script return code: {result.returncode}")
            self.logger.log(f"AI Assistant: Script output:\n{script_output}")

            if result.returncode == 0:
                self.logger.log("SUCCESS: Ollama installation completed")
                messagebox.showinfo(
                    "Success", 
                    "Ollama installed successfully!\n\n"
                    "IMPORTANT: You must restart your computer for PATH changes to take effect.\n\n"
                    "After restart, click 'AI Antenna Assistant' again to start the server."
                )
            else:
                self.logger.log(f"ERROR: Installation failed with code {result.returncode}")
                messagebox.showerror(
                    "Installation Failed",
                    f"Installation failed with error code {result.returncode}\n\n"
                    f"Check the log file for details.\n\n"
                    f"You can try manual installation from https://ollama.ai"
                )
                
        except subprocess.TimeoutExpired:
            self.logger.log("AI Assistant: Script timed out after 10 minutes")
            messagebox.showerror(
                "Timeout", 
                "Installation timed out after 10 minutes.\n\n"
                "This might mean the installation is still running in the background.\n\n"
                "Check Task Manager for 'OllamaSetup.exe' or 'ollama.exe' processes."
            )
        except Exception as e:
            self.logger.log(f"AI Assistant: Exception during installation: {str(e)}")
            import traceback
            self.logger.log(f"Traceback:\n{traceback.format_exc()}")
            messagebox.showerror("Error", f"Installation error: {str(e)}")
        
        self.logger.log("="*80)
        self.logger.log("OLLAMA INSTALLATION PROCESS COMPLETED")
        self.logger.log("="*80)

    def manual_import_antenna(self):
        """Manually import antenna pattern from XML file"""
        from tkinter import filedialog
        filepath = filedialog.askopenfilename(
            title="Select Antenna XML File",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filepath:
            success = self.antenna_pattern.load_from_xml(filepath)
            if success:
                self.pattern_name = filepath.split('/')[-1].replace('.xml', '')
                self.current_antenna_id = None  # Not from library
                self.update_info_panel()
                messagebox.showinfo("Success", "Antenna pattern loaded successfully!")
            else:
                messagebox.showerror("Error", "Failed to load XML file. Check format.")

    def create_manual_antenna(self):
        """Create a custom antenna pattern manually"""
        def on_create(xml_content, metadata):
            # Open save dialog with pre-filled metadata
            self.logger.log("Manual antenna created, opening save dialog...")
            metadata_dialog = AntennaMetadataDialog(self.root, initial_values=metadata)
            self.root.wait_window(metadata_dialog.dialog)

            if not metadata_dialog.result:
                self.logger.log("User cancelled manual antenna save")
                return

            save_metadata = metadata_dialog.result
            antenna_name = save_metadata['name']

            self.logger.log(f"Saving manual antenna to library: {antenna_name}")

            # Save to antenna library
            success = self.antenna_library.add_antenna(antenna_name, xml_content, save_metadata)

            if not success:
                self.logger.log("ERROR: Failed to save manual antenna to library")
                messagebox.showerror("Error", "Failed to save antenna to library.")
                return

            self.logger.log(f"SUCCESS: Manual antenna '{antenna_name}' saved to library")

            # Load the antenna pattern
            antenna_list = self.antenna_library.list_antennas()
            if antenna_list:
                new_antenna_id = antenna_list[-1][0]
                self.load_antenna_from_library(new_antenna_id)

                self.logger.log(f"Loaded manual antenna pattern: {antenna_name}")
                messagebox.showinfo("Success",
                    f"Manual antenna '{antenna_name}' created and loaded successfully!")

        # Open manual creation dialog
        ManualAntennaDialog(self.root, on_create)
    
    def load_antenna_from_library(self, antenna_id):
        """Load an antenna pattern from the library
        
        Args:
            antenna_id: ID of antenna in library
        """
        self.logger.log(f"Loading antenna from library: {antenna_id}")
        
        # Get antenna XML path
        xml_path = self.antenna_library.get_antenna_xml_path(antenna_id)
        if not xml_path:
            self.logger.log(f"ERROR: Could not find XML for antenna {antenna_id}")
            messagebox.showerror("Error", "Could not find antenna in library.")
            return False
        
        # Load the pattern
        success = self.antenna_pattern.load_from_xml(xml_path)
        if not success:
            self.logger.log(f"ERROR: Failed to load antenna pattern from {xml_path}")
            messagebox.showerror("Error", "Failed to load antenna pattern.")
            return False
        
        # Get antenna info
        antenna_info = self.antenna_library.get_antenna(antenna_id)
        if antenna_info:
            self.pattern_name = antenna_info['name']
            self.current_antenna_id = antenna_id
            # Set the antenna gain from library metadata
            self.antenna_pattern.max_gain = antenna_info.get('gain', 0.0)
            self.logger.log(f"Successfully loaded antenna: {self.pattern_name} (gain: {self.antenna_pattern.max_gain} dBi)")
            self.update_info_panel()
            return True
        
        return False

    def view_antennas(self):
        """View available antennas"""
        info = f"Current Antenna: {self.pattern_name}\n\n"
        info += "Azimuth Gains (sample):\n"
        for angle in [0, 90, 180, 270]:
            gain = self.antenna_pattern.get_gain(angle)
            info += f"{angle}°: {gain:.1f} dBi\n"
        info += "\nElevation Gains (sample):\n"
        for angle in [-90, -45, 0, 45, 90]:
            gain = self.antenna_pattern.get_gain(0, angle)
            info += f"{angle}°: {gain:.1f} dBi\n"
        messagebox.showinfo("Antenna Details", info)

    def export_antenna(self):
        """Export current antenna pattern to XML file"""
        from tkinter import filedialog
        filepath = filedialog.asksaveasfilename(
            title="Save Antenna XML",
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")],
            initialfile=f"{self.pattern_name}.xml"
        )
        if filepath:
            # Generate XML
            xml_content = '<antenna>\n<azimuth>\n'
            for angle in range(0, 360, 10):  # Every 10 degrees
                gain = self.antenna_pattern.get_gain(angle)
                xml_content += f'<point angle="{angle}" gain="{gain:.1f}"/>\n'
            xml_content += '</azimuth>\n<elevation>\n'
            for angle in range(-90, 91, 10):
                gain = self.antenna_pattern.get_gain(0, angle)
                xml_content += f'<point angle="{angle}" gain="{gain:.1f}"/>\n'
            xml_content += '</elevation>\n</antenna>'

            try:
                with open(filepath, 'w') as f:
                    f.write(xml_content)
                messagebox.showinfo("Success", "Antenna exported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {e}")

    def show_project_setup(self):
        """Show project setup dialog"""
        dialog = ProjectSetupDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result is None:
            self.root.quit()
            return
        
        self.callsign = dialog.result.get('callsign', 'KDPI')
        self.frequency = dialog.result.get('frequency', 88.5)
        self.tx_type = dialog.result.get('tx_type', 'Broadcast FM')
        self.transmission_mode = dialog.result.get('transmission_mode', 'FM')
        self.tx_lat = dialog.result['tx_lat']
        self.tx_lon = dialog.result['tx_lon']
        self.height = dialog.result.get('height', 30)
        self.erp = dialog.result.get('erp', 40)
        self.zoom = dialog.result['zoom']
        self.basemap = dialog.result['basemap']
        self.max_distance = dialog.result['radius']
        
        self.toolbar.update_location(self.tx_lat, self.tx_lon)
        self.toolbar.set_zoom(self.zoom)
        self.update_info_panel()
        
        # Cache map tiles
        self.cache_all_zoom_levels(self.tx_lat, self.tx_lon)
        self.precache_terrain_for_coverage()
        
        self.reload_map(preserve_propagation=False)
        
        messagebox.showinfo("Project Ready",
                          "Map and terrain data fully cached!\n\n"
                          "Ready to calculate coverage!")
        
        self.save_auto_config()
    
    def refresh_map_dialog(self):
        """Show map refresh dialog"""
        self.edit_station_info()
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def reload_map(self, preserve_propagation=True):
        """Reload map with current settings"""
        success = self.map_display.load_map(self.tx_lat, self.tx_lon, self.zoom,
                                           self.basemap, self.cache)
        
        if success:
            if preserve_propagation and self.last_propagation is not None and self.show_coverage.get():
                # Redraw propagation overlay
                x_grid, y_grid, rx_power_grid = self.last_propagation
                tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
                    self.tx_lat, self.tx_lon
                )
                self.propagation_plot.plot_coverage(
                    self.map_display.map_image, tx_pixel_x, tx_pixel_y,
                    x_grid, y_grid, rx_power_grid, self.signal_threshold,
                    self.map_display.get_pixel_scale(),
                    self.last_terrain_loss, self.show_shadow.get(),
                    (self.map_display.plot_xlim, self.map_display.plot_ylim),
                    alpha=self.toolbar.get_transparency()
                )
            else:
                self.map_display.display_map_only(self.tx_lat, self.tx_lon, show_marker=True)
    
    def update_info_panel(self):
        """Update info panel with current settings"""
        # Get antenna details if from library
        antenna_details = None
        if self.current_antenna_id:
            antenna_details = self.antenna_library.get_antenna(self.current_antenna_id)
        
        self.info_panel.update(
            self.callsign, self.frequency, self.transmission_mode, self.tx_type,
            self.tx_lat, self.tx_lon, self.height, self.rx_height, self.erp, self.pattern_name,
            self.max_distance, self.signal_threshold,
            self.use_terrain.get(), self.terrain_quality,
            antenna_details=antenna_details
        )
    
    def cache_all_zoom_levels(self, lat, lon):
        """Cache map tiles at all zoom levels"""
        from models.map_handler import MapHandler
        
        print(f"Caching all zoom levels for {lat:.6f}, {lon:.6f}...")
        zoom_levels = [10, 11, 12, 13, 14, 15, 16]
        
        for i, zoom in enumerate(zoom_levels):
            self.toolbar.set_status(f"Caching zoom level {zoom} [{i+1}/{len(zoom_levels)}]...")
            self.root.update()
            MapHandler.get_map_tile(lat, lon, zoom, tile_size=3,
                                   basemap=self.basemap, cache=self.cache)
        
        self.toolbar.set_status("All zoom levels cached")
    
    def precache_terrain_for_coverage(self):
        """Pre-cache terrain elevation data"""
        print(f"Pre-caching terrain data...")
        
        presets = {
            'Low': (36, 25),
            'Medium': (72, 50),
            'High': (360, 100)
        }
        
        azimuths_count, distances_count = presets.get(self.terrain_quality, (72, 50))
        
        all_points = []
        azimuths = np.linspace(0, 360, azimuths_count, endpoint=False)
        distances = np.linspace(0.1, self.max_distance, distances_count)
        
        for az in azimuths:
            for d in distances:
                lat_offset = d * np.cos(np.radians(az)) / 111.0
                lon_offset = d * np.sin(np.radians(az)) / (111.0 * np.cos(np.radians(self.tx_lat)))
                point_lat = self.tx_lat + lat_offset
                point_lon = self.tx_lon + lon_offset
                all_points.append((point_lat, point_lon))
        
        batch_size = 100
        total_batches = (len(all_points) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(all_points))
            batch = all_points[start_idx:end_idx]
            
            self.toolbar.set_status(
                f"Caching terrain [{batch_num+1}/{total_batches}] - {end_idx}/{len(all_points)} points..."
            )
            self.root.update()
            
            TerrainHandler.get_elevations_batch(batch)
        
        self.toolbar.set_status("Terrain data cached")
    
    def save_current_plot_to_history(self):
        """Save current plot to history"""
        if self.last_propagation is None:
            return
        
        timestamp = datetime.datetime.now()
        plot_name = f"Plot_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        plot_data = {
            'timestamp': timestamp.isoformat(),
            'name': plot_name,
            'parameters': {
                'tx_lat': self.tx_lat,
                'tx_lon': self.tx_lon,
                'erp': self.erp,
                'frequency': self.frequency,
                'height': self.height,
                'max_distance': self.max_distance,
                'resolution': self.resolution,
                'signal_threshold': self.signal_threshold,
                'use_terrain': self.use_terrain.get(),
                'pattern_name': self.pattern_name,
                'zoom': self.zoom,
                'basemap': self.basemap
            },
            'x_grid': self.last_propagation[0].tolist(),
            'y_grid': self.last_propagation[1].tolist(),
            'rx_power_grid': self.last_propagation[2].tolist(),
            'terrain_loss_grid': self.last_terrain_loss.tolist() if self.last_terrain_loss is not None else None
        }
        
        self.saved_plots.append(plot_data)
        
        if len(self.saved_plots) > 20:
            self.saved_plots = self.saved_plots[-20:]
        
        # Save render
        renders_dir = os.path.join("logs", "renders")
        os.makedirs(renders_dir, exist_ok=True)
        
        try:
            filename = os.path.join(renders_dir, f"{plot_name}.jpg")
            self.fig.savefig(filename, dpi=150, bbox_inches='tight', format='jpg')
        except Exception as e:
            print(f"Warning: Failed to save plot render: {e}")
    
    def load_plot_from_history(self, idx):
        """Load a plot from history by index
        
        Args:
            idx: Index of plot in saved_plots list
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if idx < 0 or idx >= len(self.saved_plots):
                return False
            
            plot_data = self.saved_plots[idx]
            
            # Restore grids from saved data
            import numpy as np
            x_grid = np.array(plot_data.get('x_grid', plot_data.get('az_grid')))
            y_grid = np.array(plot_data.get('y_grid', plot_data.get('dist_grid')))
            rx_power_grid = np.array(plot_data['rx_power_grid'])
            
            terrain_loss_grid = None
            if plot_data['terrain_loss_grid'] is not None:
                terrain_loss_grid = np.array(plot_data['terrain_loss_grid'])
            
            # Store as current propagation
            self.last_propagation = (x_grid, y_grid, rx_power_grid)
            self.last_terrain_loss = terrain_loss_grid
            
            # Restore parameters
            params = plot_data['parameters']
            self.tx_lat = params['tx_lat']
            self.tx_lon = params['tx_lon']
            self.erp = params['erp']
            self.frequency = params['frequency']
            self.height = params['height']
            self.max_distance = params['max_distance']
            self.signal_threshold = params['signal_threshold']
            self.use_terrain.set(params['use_terrain'])
            self.pattern_name = params.get('pattern_name', 'Unknown')
            self.zoom = params.get('zoom', 13)
            self.basemap = params.get('basemap', 'Esri WorldImagery')
            
            # Update UI
            self.toolbar.update_location(self.tx_lat, self.tx_lon)
            self.toolbar.set_zoom(self.zoom)
            self.menubar.vars['basemap_var'].set(self.basemap)
            self.menubar.vars['max_dist_var'].set(str(self.max_distance))
            self.update_info_panel()
            
            # Reload map and redraw coverage
            self.reload_map(preserve_propagation=True)
            
            return True
            
        except Exception as e:
            print(f"Error loading plot from history: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def delete_plot_from_history(self, idx):
        """Delete a plot from history by index
        
        Args:
            idx: Index of plot in saved_plots list
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if idx < 0 or idx >= len(self.saved_plots):
                return False
            
            # Delete the plot
            del self.saved_plots[idx]
            
            return True
            
        except Exception as e:
            print(f"Error deleting plot from history: {e}")
            return False
    
    def load_auto_config(self):
        """Load auto-saved configuration"""
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                
                self.callsign = config.get('callsign', self.callsign)
                self.tx_type = config.get('tx_type', self.tx_type)
                self.transmission_mode = config.get('transmission_mode', self.transmission_mode)
                self.tx_lat = config.get('tx_lat', self.tx_lat)
                self.tx_lon = config.get('tx_lon', self.tx_lon)
                self.erp = config.get('erp', self.erp)
                self.frequency = config.get('frequency', self.frequency)
                self.height = config.get('height', self.height)
                self.max_distance = config.get('max_distance', self.max_distance)
                self.signal_threshold = config.get('signal_threshold', self.signal_threshold)
                self.terrain_quality = config.get('terrain_quality', self.terrain_quality)
                self.pattern_name = config.get('pattern_name', self.pattern_name)
                self.zoom = config.get('zoom', self.zoom)
                self.basemap = config.get('basemap', self.basemap)
                use_terrain = config.get('use_terrain', False)
                self.use_terrain.set(use_terrain)
                
                print(f"Auto-loaded previous session: {self.callsign}")
                return True
        except Exception as e:
            print(f"Could not load auto-config: {e}")
        
        return False
    
    def save_auto_config(self):
        """Save configuration automatically"""
        try:
            config = {
                'version': '3.0',
                'callsign': self.callsign,
                'tx_type': self.tx_type,
                'transmission_mode': self.transmission_mode,
                'tx_lat': self.tx_lat,
                'tx_lon': self.tx_lon,
                'erp': self.erp,
                'frequency': self.frequency,
                'height': self.height,
                'max_distance': self.max_distance,
                'signal_threshold': self.signal_threshold,
                'terrain_quality': self.terrain_quality,
                'pattern_name': self.pattern_name,
                'zoom': self.zoom,
                'basemap': self.basemap,
                'use_terrain': self.use_terrain.get()
            }
            
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving auto-config: {e}")
    
    def on_closing(self):
        """Handle window close"""
        print("Closing application...")
        self.save_auto_config()
        self.root.destroy()


def main():
    """Main entry point"""
    import numpy as np  # Ensure numpy is imported
    
    root = tk.Tk()
    app = VetRender(root)
    root.mainloop()


if __name__ == "__main__":
    main()
