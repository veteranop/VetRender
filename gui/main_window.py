"""
Cellfire RF Studio - Main Window
==================================
Professional RF Propagation Analysis with Advanced Features:
✅ Segment-by-segment terrain diffraction (no shadow tunneling!)
✅ 360° azimuth sampling (no radial artifacts!)
✅ Simplified zoom (preserves overlays!)
✅ User-configurable terrain detail
✅ FCC database integration
✅ Professional report generation

Clean modular architecture for professional RF engineering workflows.
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
from gui.report_dialog import ReportConfigDialog

from controllers.propagation_controller import PropagationController
from controllers.export_handler import ExportHandler
from controllers.fcc_api import FCCAPIHandler
from controllers.report_generator import ReportGenerator

from models.antenna_models.antenna import AntennaPattern
from models.antenna_library import AntennaLibrary
from models.map_cache import MapCache
from models.terrain import TerrainHandler
from debug_logger import get_logger


class CellfireRFStudio:
    """Main Cellfire RF Studio application with professional architecture"""

    CONFIG_FILE = ".cellfire_config.json"

    def __init__(self, root):
        """Initialize Cellfire RF Studio application

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Cellfire RF Studio - Professional RF Propagation Analysis")
        self.root.geometry("1400x900")
        
        # Initialize core components
        self.antenna_pattern = AntennaPattern()
        self.antenna_library = AntennaLibrary()
        self.current_antenna_id = None  # Track current antenna from library
        self.pattern_name = "Default Omni (0 dBi)"
        self.cache = MapCache()
        self.logger = get_logger()

        # Initialize export and reporting handlers
        self.config_manager = self  # Use self as config manager (has get/set methods)
        self.export_handler = ExportHandler(self.config_manager)
        self.fcc_api = FCCAPIHandler()
        self.report_generator = ReportGenerator(self.config_manager, self.fcc_api, self.antenna_pattern)

        # FCC data storage
        self.fcc_data = None  # Will store FCC query results
        print("INIT: FCC data storage initialized")
        
        # Station parameters
        self.callsign = "KDPI"
        self.tx_type = "Broadcast FM"
        self.transmission_mode = "FM"
        self.tx_lat = 43.4665
        self.tx_lon = -112.0340
        self.erp = 40
        self.tx_power = 40  # Transmitter output power in dBm (from Station Builder)
        self.frequency = 88.5
        self.height = 30
        self.rx_height = 1.5  # Receiver height in meters
        self.max_distance = 100
        self.resolution = 500
        self.signal_threshold = -110
        self.terrain_quality = 'Medium'
        self.zoom = 13
        self.basemap = 'Esri WorldImagery'

        # RF chain system loss/gain (from Station Builder)
        self.system_loss_db = 0.0
        self.system_gain_db = 0.0
        self.rf_chain = []  # List of (component_dict, length_ft) tuples
        
        # Terrain calculation parameters
        self.terrain_azimuths = 3600  # 🔥 LOCKED at 3600 (0.1° resolution) - eliminates blocks
        self.terrain_distances = 2200  # High detail by default (updated for accuracy)
        
        # UI state
        self.use_terrain = tk.BooleanVar(value=False)
        self.show_coverage = tk.BooleanVar(value=True)
        self.show_shadow = tk.BooleanVar(value=False)
        self.live_probe_enabled = False

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
            self.tx_lat, self.tx_lon, self.height, self.rx_height, self.erp, self.tx_power, self.system_loss_db, self.system_gain_db, self.pattern_name,
            self.max_distance, self.signal_threshold, 
            self.use_terrain.get(), self.terrain_quality
        )
        
        # Show project setup if no config
        if not config_loaded:
            self.root.after(100, self.show_project_setup)
        
        # Register close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Set window icon if logo exists
        self.set_window_icon()

        self.logger.log("Cellfire RF Studio application started")
    
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
        
        self.menubar = MenuBar(self.root, self.get_menu_callbacks(), menu_vars, main_window=self)
        
        # Setup toolbar
        self.toolbar = Toolbar(self.root, self.get_toolbar_callbacks())
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.toolbar.set_zoom(self.zoom)
        self.toolbar.set_quality(self.terrain_quality)
        self.toolbar.set_custom_values(self.terrain_azimuths, self.terrain_distances)
        self.toolbar.update_location(self.tx_lat, self.tx_lon)
        
        # Main content area with tabs
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # ======= COVERAGE TAB =======
        coverage_tab = ttk.Frame(self.notebook)
        self.notebook.add(coverage_tab, text="Coverage")

        # Info panel on left
        self.info_panel = InfoPanel(coverage_tab)
        self.info_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0), pady=5)
        self.info_panel.add_button("Edit Station Info", self.edit_station_info)
        self.info_panel.add_button("Plots", self.show_plots_manager)

        # Map area on right
        map_frame = ttk.Frame(coverage_tab, padding="0")
        map_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Bind mouse motion for live probe
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_motion)

        # ======= STATION TAB =======
        self.station_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.station_tab, text="Station")
        self.setup_station_tab()
        
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
        self.root.bind('<Control-b>', lambda e: self.open_station_builder())
        self.root.bind('<Control-t>', lambda e: self.edit_tx_config())
        self.root.bind('<F1>', lambda e: self.show_help())

    def set_window_icon(self):
        """Set window icon using Cellfire logo"""
        try:
            from PIL import Image, ImageTk
            import os

            # Try to load the logo from assets/branding
            logo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'branding', 'cellfire_logo.png')

            if os.path.exists(logo_path):
                # Load and resize logo for window icon
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((32, 32), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(logo_image)
                self.root.iconphoto(True, photo)
                # Keep reference to prevent garbage collection
                self.root._icon_image = photo
                self.logger.log("Window icon set successfully")
            else:
                self.logger.log(f"Logo not found at {logo_path}")
        except Exception as e:
            self.logger.log(f"Could not set window icon: {e}")

    def setup_station_tab(self):
        """Setup the Station tab with RF chain builder"""
        from models.component_library import ComponentLibrary

        # Initialize component library
        self.component_library = ComponentLibrary()

        # Main container
        main_frame = ttk.Frame(self.station_tab, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top section: Add components
        add_frame = ttk.LabelFrame(main_frame, text="Add Component", padding=10)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        # Component type selector
        ttk.Label(add_frame, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.comp_type_var = tk.StringVar(value="all")
        comp_types = ['all'] + self.component_library.get_component_types()
        type_combo = ttk.Combobox(add_frame, textvariable=self.comp_type_var,
                                   values=comp_types, width=15, state='readonly')
        type_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        type_combo.bind('<<ComboboxSelected>>', lambda e: self._search_components())

        # Search box
        ttk.Label(add_frame, text="Search:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._search_components())
        search_entry = ttk.Entry(add_frame, textvariable=self.search_var, width=30)
        search_entry.grid(row=0, column=3, sticky=tk.W, padx=5)

        # Ollama search button
        ttk.Button(add_frame, text="AI Search (Ollama)", command=self._ollama_search).grid(
            row=0, column=4, sticky=tk.W, padx=5)

        # Results list
        ttk.Label(add_frame, text="Results:").grid(row=1, column=0, sticky=tk.NW, padx=5, pady=5)

        results_frame = ttk.Frame(add_frame)
        results_frame.grid(row=1, column=1, columnspan=4, sticky=(tk.W, tk.E), padx=5, pady=5)

        self.results_listbox = tk.Listbox(results_frame, height=5, width=70)
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        self.results_listbox.config(yscrollcommand=scrollbar.set)
        self.results_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Length entry (for cables)
        ttk.Label(add_frame, text="Length (ft):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.length_var = tk.StringVar(value="100")
        length_entry = ttk.Entry(add_frame, textvariable=self.length_var, width=10)
        length_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # Add button
        add_btn = ttk.Button(add_frame, text="Add to Chain", command=self._add_to_chain)
        add_btn.grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)

        # Middle section: RF Chain display
        chain_frame = ttk.LabelFrame(main_frame, text="RF Chain (TX → Antenna)", padding=10)
        chain_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Chain tree view
        chain_tree_frame = ttk.Frame(chain_frame)
        chain_tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('component', 'type', 'length', 'loss', 'gain')
        self.chain_tree = ttk.Treeview(chain_tree_frame, columns=columns, show='tree headings', height=10)

        self.chain_tree.heading('component', text='Component')
        self.chain_tree.heading('type', text='Type')
        self.chain_tree.heading('length', text='Length (ft)')
        self.chain_tree.heading('loss', text='Loss (dB)')
        self.chain_tree.heading('gain', text='Gain (dB)')

        self.chain_tree.column('#0', width=50)
        self.chain_tree.column('component', width=250)
        self.chain_tree.column('type', width=100)
        self.chain_tree.column('length', width=80)
        self.chain_tree.column('loss', width=80)
        self.chain_tree.column('gain', width=80)

        chain_scrollbar = ttk.Scrollbar(chain_tree_frame, orient=tk.VERTICAL, command=self.chain_tree.yview)
        self.chain_tree.config(yscrollcommand=chain_scrollbar.set)
        self.chain_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chain_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Chain controls
        chain_controls = ttk.Frame(chain_frame)
        chain_controls.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(chain_controls, text="Move Up", command=self._move_up).pack(side=tk.LEFT, padx=5)
        ttk.Button(chain_controls, text="Move Down", command=self._move_down).pack(side=tk.LEFT, padx=5)
        ttk.Button(chain_controls, text="Remove", command=self._remove_component).pack(side=tk.LEFT, padx=5)
        ttk.Button(chain_controls, text="Clear All", command=self._clear_chain).pack(side=tk.LEFT, padx=5)

        # Bottom section: Totals
        totals_frame = ttk.LabelFrame(main_frame, text="System Totals", padding=10)
        totals_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(totals_frame, text="Total Loss:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.total_loss_var = tk.StringVar(value="0.00 dB")
        ttk.Label(totals_frame, textvariable=self.total_loss_var, font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(totals_frame, text="Total Gain:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.total_gain_var = tk.StringVar(value="0.00 dB")
        ttk.Label(totals_frame, textvariable=self.total_gain_var, font=('TkDefaultFont', 10, 'bold')).grid(row=0, column=3, sticky=tk.W, padx=5)

        ttk.Label(totals_frame, text="Net Change:").grid(row=0, column=4, sticky=tk.W, padx=5)
        self.net_change_var = tk.StringVar(value="0.00 dB")
        self.net_label = ttk.Label(totals_frame, textvariable=self.net_change_var, font=('TkDefaultFont', 10, 'bold'))
        self.net_label.grid(row=0, column=5, sticky=tk.W, padx=5)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Apply to Station", command=self._apply_station_changes).pack(side=tk.RIGHT, padx=5)

        # Initialize search results and chain display
        self.search_results = []
        self._update_chain_display()
        self._calculate_totals()
        self._search_components()  # Auto-populate on startup

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
            'on_station_builder': self.open_station_builder,
            'on_configure_transmitter': self.edit_tx_config,
            'on_toggle_live_probe': self.toggle_live_probe,
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
            'on_export_kml': self.export_kml,
            'on_export_images': self.export_images_all_zoom,
            'on_generate_report': self.generate_report,
            'on_quick_start': self.show_quick_start,
            'on_user_manual': self.show_user_manual,
            'on_about': self.show_about,
            'on_report_bug': self.report_bug,
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

            # Calculate effective ERP from tx_power + system gain/loss (antenna gain already in system_gain_db)
            effective_erp = self.tx_power + self.system_gain_db - self.system_loss_db

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
                self.tx_lat, self.tx_lon, self.height, effective_erp, self.frequency,
                self.max_distance, self.resolution, self.signal_threshold, self.rx_height,
                self.use_terrain.get(), self.terrain_quality,
                custom_az, custom_dist, propagation_model=propagation_model,
                progress_callback=progress_callback,
                zoom_level=self.zoom
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
    
    def toggle_live_probe(self):
        """Toggle live probe mode"""
        self.live_probe_enabled = not self.live_probe_enabled

        if self.live_probe_enabled:
            if self.last_propagation is None:
                messagebox.showinfo("No Coverage Data",
                                  "Calculate coverage first to enable live probe.")
                self.live_probe_enabled = False
                self.toolbar.live_probe_var.set(False)
                return
            self.toolbar.set_status("Live Probe: Move cursor to see signal strength")
        else:
            self.toolbar.set_status("")
            self.toolbar.signal_var.set("")

    def on_mouse_motion(self, event):
        """Handle mouse motion for live probe"""
        if not self.live_probe_enabled or self.last_propagation is None:
            return

        # Check if mouse is inside the plot area
        if event.xdata is None or event.ydata is None:
            return

        try:
            # Get pixel coordinates
            pixel_x = event.x
            pixel_y = event.y

            x_grid, y_grid, rx_power_grid = self.last_propagation
            tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
                self.tx_lat, self.tx_lon
            )

            signal, distance, azimuth = self.propagation_plot.get_signal_at_pixel(
                pixel_x, pixel_y, tx_pixel_x, tx_pixel_y,
                x_grid, y_grid, rx_power_grid,
                self.map_display.get_pixel_scale()
            )

            if signal is not None:
                # Update toolbar display
                self.toolbar.signal_var.set(f"{signal:.1f} dBm @ {distance:.2f} km")
            else:
                self.toolbar.signal_var.set("Out of range")

        except Exception as e:
            # Silently ignore errors during mouse motion
            pass

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

    def open_station_builder(self):
        """Open Station Builder dialog"""
        from gui.station_builder import StationBuilderDialog

        def update_system(total_loss, total_gain, net_change, rf_chain, antenna_id):
            """Callback to update system loss/gain, RF chain, and antenna"""
            self.system_loss_db = total_loss
            self.system_gain_db = total_gain
            self.rf_chain = rf_chain

            # Extract transmitter power if present in RF chain
            tx_power_found = False
            for component, length_ft in rf_chain:
                if component.get('component_type') == 'transmitter' and 'transmit_power_watts' in component:
                    import math
                    self.tx_power = 10 * math.log10(component['transmit_power_watts'] * 1000)  # Convert watts to dBm
                    tx_power_found = True
                    break
            if not tx_power_found and rf_chain:
                # If no transmitter found but chain exists, keep current tx_power
                pass

            # Update antenna if selected
            if antenna_id:
                self.current_antenna_id = antenna_id
                antenna_data = self.antenna_library.antennas.get(antenna_id)
                if antenna_data:
                    # Load antenna pattern from library
                    xml_path = self.antenna_library.get_antenna_xml_path(antenna_id)
                    if xml_path:
                        self.antenna_pattern.load_from_xml(xml_path)
                        self.pattern_name = antenna_data.get('name', 'Unknown')
                        print(f"Loaded antenna: {self.pattern_name}")
            else:
                # No antenna selected - use default omni
                self.current_antenna_id = None

            # Save to project config
            self.save_auto_config()

            # Update displayed ERP (add net change to current ERP)
            print(f"System updated: Loss={total_loss:.2f} dB, Gain={total_gain:.2f} dB, Net={net_change:+.2f} dB")
            self.update_info_panel()

        StationBuilderDialog(self.root, self.frequency, callback=update_system,
                            initial_chain=self.rf_chain, initial_antenna=self.current_antenna_id)

    def _search_components(self):
        """Search for components based on filters"""
        query = self.search_var.get()
        comp_type = self.comp_type_var.get()

        if comp_type == 'all':
            comp_type = None

        results = self.component_library.search_component(query, comp_type)

        # Update listbox
        self.results_listbox.delete(0, tk.END)
        self.search_results = results

        for component in results:
            model = component.get('model', 'Unknown')
            desc = component.get('description', '')
            source = component.get('source', '')
            display = f"{model} - {desc} ({source})"
            self.results_listbox.insert(tk.END, display)

    def _ollama_search(self):
        """Search for component using Ollama AI"""
        query = self.search_var.get().strip()
        if not query:
            messagebox.showwarning("No Query", "Please enter a component name or part number to search")
            return

        # Show progress dialog
        progress_dialog = tk.Toplevel(self.root)
        progress_dialog.title("AI Search")
        progress_dialog.geometry("400x150")
        progress_dialog.transient(self.root)
        progress_dialog.grab_set()

        ttk.Label(progress_dialog, text=f"Searching for: {query}",
                 font=('TkDefaultFont', 10, 'bold')).pack(pady=10)
        ttk.Label(progress_dialog, text="Querying Ollama AI...\nThis may take a moment.").pack(pady=5)

        progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start(10)

        def do_search():
            """Run search in background"""
            try:
                component = self.component_library.ollama_search_component(query, self.frequency)
                progress_dialog.after(0, lambda: on_search_complete(component))
            except Exception as e:
                progress_dialog.after(0, lambda: on_search_error(str(e)))

        def on_search_complete(component):
            """Handle successful search"""
            progress_bar.stop()
            progress_dialog.destroy()

            if component:
                messagebox.showinfo("Component Found",
                                  f"Found: {component.get('model', 'Unknown')}\n\n"
                                  f"Description: {component.get('description', 'N/A')}\n"
                                  f"Type: {component.get('component_type', 'N/A')}\n\n"
                                  f"Component added to cache and search results.")
                self._search_components()  # Refresh search to show new component
            else:
                messagebox.showwarning("Not Found",
                                     f"Could not find specifications for '{query}'.\n\n"
                                     f"Try a different part number or manufacturer name.")

        def on_search_error(error_msg):
            """Handle search error"""
            progress_bar.stop()
            progress_dialog.destroy()
            messagebox.showerror("Search Error",
                               f"Error searching with Ollama:\n\n{error_msg}\n\n"
                               f"Make sure Ollama is running and accessible.")

        # Start search in background thread
        import threading
        search_thread = threading.Thread(target=do_search, daemon=True)
        search_thread.start()

    def _add_to_chain(self):
        """Add selected component to RF chain"""
        selection = self.results_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a component to add")
            return

        component = self.search_results[selection[0]]

        # Get length for cables
        length_ft = 0
        if component.get('component_type') == 'cable':
            try:
                length_ft = float(self.length_var.get())
            except ValueError:
                messagebox.showerror("Invalid Length", "Please enter a valid length in feet")
                return

        self.rf_chain.append((component, length_ft))
        self._update_chain_display()
        self._calculate_totals()

    def _remove_component(self):
        """Remove selected component from chain"""
        selection = self.chain_tree.selection()
        if not selection:
            return

        # Get index from item ID
        item_id = selection[0]
        index = int(item_id.replace('item_', ''))

        del self.rf_chain[index]
        self._update_chain_display()
        self._calculate_totals()

    def _move_up(self):
        """Move selected component up in chain"""
        selection = self.chain_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        index = int(item_id.replace('item_', ''))

        if index > 0:
            self.rf_chain[index], self.rf_chain[index - 1] = self.rf_chain[index - 1], self.rf_chain[index]
            self._update_chain_display()
            self._calculate_totals()

    def _move_down(self):
        """Move selected component down in chain"""
        selection = self.chain_tree.selection()
        if not selection:
            return

        item_id = selection[0]
        index = int(item_id.replace('item_', ''))

        if index < len(self.rf_chain) - 1:
            self.rf_chain[index], self.rf_chain[index + 1] = self.rf_chain[index + 1], self.rf_chain[index]
            self._update_chain_display()
            self._calculate_totals()

    def _clear_chain(self):
        """Clear all components from chain"""
        if messagebox.askyesno("Clear Chain", "Remove all components from RF chain?"):
            self.rf_chain = []
            self._update_chain_display()
            self._calculate_totals()

    def _update_chain_display(self):
        """Update chain tree view"""
        # Clear existing
        for item in self.chain_tree.get_children():
            self.chain_tree.delete(item)

        # Add components
        for idx, (component, length_ft) in enumerate(self.rf_chain):
            model = component.get('model', 'Unknown')
            comp_type = component.get('component_type', 'unknown')

            # Calculate loss/gain for this component
            loss_db = 0
            gain_db = 0

            if comp_type == 'cable':
                loss_db = self.component_library.interpolate_cable_loss(component, self.frequency, length_ft)
            elif 'insertion_loss_db' in component:
                loss_db = component['insertion_loss_db']
            elif 'gain_dbi' in component:
                gain_db = component['gain_dbi']

            length_str = f"{length_ft:.1f}" if length_ft > 0 else "-"
            loss_str = f"{loss_db:.2f}" if loss_db > 0 else "-"
            gain_str = f"{gain_db:.2f}" if gain_db > 0 else "-"

            self.chain_tree.insert('', tk.END, iid=f'item_{idx}',
                                   text=f"{idx + 1}",
                                   values=(model, comp_type, length_str, loss_str, gain_str))

    def _calculate_totals(self):
        """Calculate total loss and gain"""
        total_loss = 0
        total_gain = 0

        for component, length_ft in self.rf_chain:
            comp_type = component.get('component_type', 'unknown')

            if comp_type == 'cable':
                loss = self.component_library.interpolate_cable_loss(component, self.frequency, length_ft)
                total_loss += loss
            elif 'insertion_loss_db' in component:
                total_loss += component['insertion_loss_db']
            elif 'gain_dbi' in component:
                total_gain += component['gain_dbi']

        net_change = total_gain - total_loss

        self.total_loss_var.set(f"{total_loss:.2f} dB")
        self.total_gain_var.set(f"{total_gain:.2f} dB")
        self.net_change_var.set(f"{net_change:+.2f} dB")

        # Color code net change
        if net_change > 0:
            self.net_label.config(foreground='green')
        elif net_change < 0:
            self.net_label.config(foreground='red')
        else:
            self.net_label.config(foreground='black')

    def _apply_station_changes(self):
        """Apply changes to station"""
        total_loss = 0
        total_gain = 0

        for component, length_ft in self.rf_chain:
            comp_type = component.get('component_type', 'unknown')

            if comp_type == 'cable':
                loss = self.component_library.interpolate_cable_loss(component, self.frequency, length_ft)
                total_loss += loss
            elif 'insertion_loss_db' in component:
                total_loss += component['insertion_loss_db']
            elif 'gain_dbi' in component:
                total_gain += component['gain_dbi']

        self.system_loss_db = total_loss
        self.system_gain_db = total_gain

        # Save to project config
        self.save_auto_config()

        # Update displayed info
        self.update_info_panel()

        messagebox.showinfo("Applied", f"Station updated with {total_gain - total_loss:+.2f} dB system change")

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
            filetypes=[("Cellfire Project", "*.cfr"), ("VetRender Project (legacy)", "*.vtr"), ("All Files", "*.*")],
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
                    'tx_power': self.tx_power,
                    'system_loss_db': self.system_loss_db,
                    'system_gain_db': self.system_gain_db,
                    'rf_chain': self.rf_chain,
                    'frequency': self.frequency,
                    'height': self.height,
                    'max_distance': self.max_distance,
                    'signal_threshold': self.signal_threshold,
                    'terrain_quality': self.terrain_quality,
                    'pattern_name': self.pattern_name,
                    'current_antenna_id': self.current_antenna_id,
                    'zoom': self.zoom,
                    'basemap': self.basemap,
                    'saved_plots': self.saved_plots,
                    'fcc_data': self.fcc_data,

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
            filetypes=[("Cellfire Project", "*.cfr"), ("VetRender Project (legacy)", "*.vtr"), ("All Files", "*.*")]
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
                self.tx_power = project_data.get('tx_power', 40)
                self.system_loss_db = project_data.get('system_loss_db', 0.0)
                self.system_gain_db = project_data.get('system_gain_db', 0.0)
                self.rf_chain = project_data.get('rf_chain', [])
                self.frequency = project_data.get('frequency', 88.5)
                self.height = project_data.get('height', 30)
                self.max_distance = project_data.get('max_distance', 100)
                self.signal_threshold = project_data.get('signal_threshold', -110)
                self.terrain_quality = project_data.get('terrain_quality', 'Medium')
                self.pattern_name = project_data.get('pattern_name', 'Default Omni (0 dBi)')
                self.current_antenna_id = project_data.get('current_antenna_id', None)
                self.zoom = 10  # Always start at zoom 10
                self.basemap = project_data.get('basemap', 'Esri WorldImagery')
                self.saved_plots = project_data.get('saved_plots', [])
                self.fcc_data = project_data.get('fcc_data', None)

                # Load antenna pattern if specified
                if self.current_antenna_id:
                    self.load_antenna_from_library(self.current_antenna_id)

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
            messagebox.showerror("Error", f"Installation script not found at {script_path}. Please reinstall Cellfire RF Studio.")
            self.logger.log("="*80)
            self.logger.log("OLLAMA INSTALLATION ABORTED - SCRIPT NOT FOUND")
            self.logger.log("="*80)
            return
        
        self.logger.log(f"Script found, size: {os.path.getsize(script_path)} bytes")

        # Show progress message
        messagebox.showinfo("Installing", 
            "Starting Ollama installation...\n\n"
            "This will take 5-10 minutes. The window may appear frozen.\n\n"
            "Please be patient and do NOT close Cellfire RF Studio.")
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
            self.tx_lat, self.tx_lon, self.height, self.rx_height, self.erp, self.tx_power, self.system_loss_db, self.system_gain_db, self.pattern_name,
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

                # Load RF chain if present
                self.rf_chain = config.get('rf_chain', [])
                self.system_loss_db = config.get('system_loss_db', 0.0)
                self.system_gain_db = config.get('system_gain_db', 0.0)

                print(f"Auto-loaded previous session: {self.callsign}")
                if self.rf_chain:
                    print(f"  RF chain: {len(self.rf_chain)} components, Net: {self.system_gain_db - self.system_loss_db:+.2f} dB")
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
                'use_terrain': self.use_terrain.get(),
                'rf_chain': self.rf_chain,
                'system_loss_db': self.system_loss_db,
                'system_gain_db': self.system_gain_db
            }
            
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving auto-config: {e}")

    def get(self, key, default=None):
        """Get configuration value (for export/report handlers)

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return getattr(self, key, default)

    # FCC query methods
    def fcc_pull_current_station(self):
        """Pull FCC data for current station"""
        print("=== FCC MENU: Pull Report for Current Station clicked ===")
        print("FCC: fcc_pull_current_station() called")

        # Ensure fcc_data exists
        if not hasattr(self, 'fcc_data'):
            print("FCC: Initializing missing fcc_data attribute")
            self.fcc_data = None

        try:
            from gui.fcc_dialog import FCCDialog
            print("FCC: Creating FCCDialog...")
            dialog = FCCDialog(self.root, self.fcc_api, self.tx_lat, self.tx_lon, self.frequency, self.fcc_data)
            print("FCC: Dialog created, opening...")
            self.root.wait_window(dialog.dialog)
            print("FCC: Dialog closed")
            # Update our FCC data if it was modified
            self.fcc_data = dialog.fcc_data
            print(f"FCC: Updated fcc_data: {self.fcc_data is not None}")
        except Exception as e:
            print(f"FCC ERROR in fcc_pull_current_station: {e}")
            import traceback
            traceback.print_exc()

    def fcc_view_data(self):
        """View FCC data"""
        print("=== FCC MENU: View FCC Data for This Project clicked ===")
        print("FCC: fcc_view_data() called")

        # Ensure fcc_data exists
        if not hasattr(self, 'fcc_data'):
            print("FCC: Initializing missing fcc_data attribute")
            self.fcc_data = None

        try:
            from gui.fcc_dialog import FCCDialog
            dialog = FCCDialog(self.root, self.fcc_api, self.tx_lat, self.tx_lon, self.frequency, self.fcc_data)
            self.root.wait_window(dialog.dialog)
            self.fcc_data = dialog.fcc_data
        except Exception as e:
            print(f"FCC ERROR in fcc_view_data: {e}")
            import traceback
            traceback.print_exc()

    def fcc_purge_data(self):
        """Purge FCC data"""
        print("=== FCC MENU: Purge FCC Data from Project clicked ===")
        print("FCC: fcc_purge_data() called")

        # Ensure fcc_data exists
        if not hasattr(self, 'fcc_data'):
            print("FCC: Initializing missing fcc_data attribute")
            self.fcc_data = None

        try:
            from gui.fcc_dialog import FCCDialog
            dialog = FCCDialog(self.root, self.fcc_api, self.tx_lat, self.tx_lon, self.frequency, self.fcc_data)
            self.root.wait_window(dialog.dialog)
            self.fcc_data = dialog.fcc_data
        except Exception as e:
            print(f"FCC ERROR in fcc_purge_data: {e}")
            import traceback
            traceback.print_exc()

    def fcc_manual_query(self):
        """Manual FCC query"""
        print("=== FCC MENU: Pull Report from Station ID clicked ===")
        print("FCC: fcc_manual_query() called")

        # Ensure fcc_data exists
        if not hasattr(self, 'fcc_data'):
            print("FCC: Initializing missing fcc_data attribute")
            self.fcc_data = None

        try:
            from gui.fcc_dialog import FCCDialog
            dialog = FCCDialog(self.root, self.fcc_api, self.tx_lat, self.tx_lon, self.frequency, self.fcc_data)
            # Switch to manual query tab
            dialog.notebook.select(dialog.manual_tab)
            self.root.wait_window(dialog.dialog)
            self.fcc_data = dialog.fcc_data
        except Exception as e:
            print(f"FCC ERROR in fcc_manual_query: {e}")
            import traceback
            traceback.print_exc()

    # ===== EXPORT AND REPORTING METHODS =====

    def export_kml(self):
        """Export coverage plot as KML"""
        try:
            self.export_handler.export_kml(self.last_propagation)
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export KML:\n{str(e)}")

    def export_images_all_zoom(self):
        """Export images at all zoom levels"""
        try:
            def render_at_zoom(zoom_level, output_path):
                """Render coverage at specific zoom level"""
                # Save current zoom
                original_zoom = self.zoom

                # Set new zoom
                self.zoom = zoom_level

                # Reload map and recalculate
                self.map_display.load_map(self.tx_lat, self.tx_lon, self.zoom,
                                         self.basemap, self.cache)

                # Redraw with existing propagation data if available
                if self.last_propagation:
                    x_grid, y_grid, rx_power_grid = self.last_propagation
                    tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
                        self.tx_lat, self.tx_lon
                    )
                    self.propagation_plot.plot_coverage(
                        self.map_display.map_image, tx_pixel_x, tx_pixel_y,
                        x_grid, y_grid, rx_power_grid, self.signal_threshold,
                        self.map_display.get_pixel_scale(),
                        self.last_terrain_loss, self.show_shadow.get()
                    )

                # Save figure
                self.fig.savefig(output_path, dpi=150, bbox_inches='tight')

                # Restore original zoom
                self.zoom = original_zoom

            # Export images
            exported = self.export_handler.export_images_all_zoom(render_at_zoom)

            if exported:
                # Restore original display
                self.map_display.load_map(self.tx_lat, self.tx_lon, self.zoom,
                                         self.basemap, self.cache)
                if self.last_propagation:
                    x_grid, y_grid, rx_power_grid = self.last_propagation
                    tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
                        self.tx_lat, self.tx_lon
                    )
                    self.propagation_plot.plot_coverage(
                        self.map_display.map_image, tx_pixel_x, tx_pixel_y,
                        x_grid, y_grid, rx_power_grid, self.signal_threshold,
                        self.map_display.get_pixel_scale(),
                        self.last_terrain_loss, self.show_shadow.get()
                    )

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export images:\n{str(e)}")

    def generate_report(self):
        """Generate comprehensive PDF report"""
        try:
            # Show report configuration dialog
            dialog = ReportConfigDialog(self.root, self.config_manager)
            config = dialog.show()

            if not config:
                return  # User cancelled

            # Generate coverage images if requested
            coverage_images = None
            if config['sections'].get('coverage_maps'):
                # Create temporary directory for images
                import tempfile
                temp_dir = tempfile.mkdtemp()

                coverage_images = []
                for zoom in config.get('zoom_levels', [11, 12]):
                    # Save current state
                    original_zoom = self.zoom

                    # Render at zoom level
                    self.zoom = zoom
                    self.map_display.load_map(self.tx_lat, self.tx_lon, self.zoom,
                                             self.basemap, self.cache)

                    if self.last_propagation:
                        x_grid, y_grid, rx_power_grid = self.last_propagation
                        tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
                            self.tx_lat, self.tx_lon
                        )
                        self.propagation_plot.plot_coverage(
                            self.map_display.map_image, tx_pixel_x, tx_pixel_y,
                            x_grid, y_grid, rx_power_grid, self.signal_threshold,
                            self.map_display.get_pixel_scale(),
                            self.last_terrain_loss, self.show_shadow.get(),
                            alpha=0.3  # 30% transparency for reports
                        )

                    # Save image
                    img_path = os.path.join(temp_dir, f"coverage_zoom{zoom}.jpg")
                    self.fig.savefig(img_path, dpi=150, bbox_inches='tight')
                    coverage_images.append(img_path)

                    # Restore zoom
                    self.zoom = original_zoom

                # Restore display
                self.map_display.load_map(self.tx_lat, self.tx_lon, self.zoom,
                                         self.basemap, self.cache)
                if self.last_propagation:
                    x_grid, y_grid, rx_power_grid = self.last_propagation
                    tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
                        self.tx_lat, self.tx_lon
                    )
                    self.propagation_plot.plot_coverage(
                        self.map_display.map_image, tx_pixel_x, tx_pixel_y,
                        x_grid, y_grid, rx_power_grid, self.signal_threshold,
                        self.map_display.get_pixel_scale(),
                        self.last_terrain_loss, self.show_shadow.get()
                    )

            # Generate report
            report_path = self.report_generator.generate_report(config, coverage_images)

            if report_path:
                self.logger.log(f"Report generated: {report_path}")

        except Exception as e:
            messagebox.showerror("Report Error", f"Failed to generate report:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def show_quick_start(self):
        """Show Quick Start Guide in browser"""
        help_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'help', 'quick_start.html')
        if os.path.exists(help_path):
            webbrowser.open(f'file:///{os.path.abspath(help_path)}')
        else:
            messagebox.showerror("Error", "Quick Start Guide not found")

    def show_user_manual(self):
        """Show User Manual in browser"""
        help_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'help.html')
        if os.path.exists(help_path):
            webbrowser.open(f'file:///{os.path.abspath(help_path)}')
        else:
            messagebox.showerror("Error", "User Manual not found")

    def show_about(self):
        """Show About Cellfire RF Studio page in browser"""
        help_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'help', 'about.html')
        if os.path.exists(help_path):
            webbrowser.open(f'file:///{os.path.abspath(help_path)}')
        else:
            messagebox.showerror("Error", "About page not found")

    def report_bug(self):
        """Open email client to report a bug"""
        subject = "Cellfire RF Studio Bug Report"
        body = """Please describe the bug you encountered:

Bug Description:


Steps to Reproduce:
1.
2.
3.

Expected Behavior:


Actual Behavior:


VetRender Version: 3.0.1
Operating System:

Additional Information:
"""
        # URL encode the subject and body
        mailto_url = f"mailto:mark@veteranop.com?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
        webbrowser.open(mailto_url)

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
