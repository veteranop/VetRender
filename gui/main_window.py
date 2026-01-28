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
import math

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Import our refactored modules
from gui.map_display import MapDisplay
from gui.propagation_plot import PropagationPlot
from gui.info_panel import InfoPanel, PlotConfirmationDialog
from gui.toolbar import Toolbar
from gui.menus import MenuBar
from gui.dialogs import (TransmitterConfigDialog, AntennaInfoDialog,
                        CacheManagerDialog, ProjectSetupDialog, SetLocationDialog,
                        PlotsManagerDialog, AntennaImportDialog, AntennaMetadataDialog,
                        ManualAntennaDialog, StationInfoDialog)
from gui.report_dialog import ReportConfigDialog
from gui.path_profile_dialog import PathProfileDialog

from controllers.propagation_controller import PropagationController
from controllers.export_handler import ExportHandler
from controllers.fcc_api import FCCAPIHandler
from controllers.report_generator import ReportGenerator

from models.antenna_models.antenna import AntennaPattern
from models.antenna_library import AntennaLibrary
from models.map_cache import MapCache
from models.terrain import TerrainHandler
from models.scan_timer import get_scan_timer
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
        self.root.minsize(1200, 700)
        
        # Initialize core components
        self.antenna_pattern = AntennaPattern()
        self.antenna_library = AntennaLibrary()
        self.current_antenna_id = None  # Track current antenna from library
        self.antenna_bearing = 0.0  # Antenna bearing in degrees (0=North, clockwise)
        self.antenna_downtilt = 0.0  # Antenna downtilt in degrees (positive=down)
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
            self.tx_lat, self.tx_lon, self.height, self.rx_height, self.tx_power, self.system_loss_db, self.system_gain_db, self.pattern_name,
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
        # Create matplotlib figure with dark theme - starts large, will resize to fit
        self.fig = Figure(figsize=(12, 10), dpi=100, frameon=False, facecolor='#1e1e1e')
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#1e1e1e')
        self.ax.set_aspect('auto')  # Fill available space
        self.ax.set_position([0, 0, 1, 1])  # Fill entire figure
        
        # Initialize display modules
        self.map_display = MapDisplay(self.ax, None)  # Canvas set below
        self.propagation_plot = PropagationPlot(self.ax, None, self.fig)  # Canvas set below
        self.propagation_controller = PropagationController(self.antenna_pattern)
        
        # Setup toolbar first so we can share its propagation_model_var with menus
        self.toolbar = Toolbar(self.root, self.get_toolbar_callbacks())
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        self.toolbar.set_zoom(self.zoom)
        self.toolbar.set_quality(self.terrain_quality)
        self.toolbar.set_custom_values(self.terrain_azimuths, self.terrain_distances)
        self.toolbar.update_location(self.tx_lat, self.tx_lon)

        # Setup menu bar - share propagation_model_var from toolbar
        menu_vars = {
            'basemap_var': tk.StringVar(value=self.basemap),
            'show_coverage_var': self.show_coverage,
            'show_shadow_var': self.show_shadow,
            'use_terrain_var': self.use_terrain,
            'max_dist_var': tk.StringVar(value=str(self.max_distance)),
            'quality_var': tk.StringVar(value=self.terrain_quality),
            'terrain_detail_var': tk.StringVar(value=str(self.terrain_distances)),
            'propagation_model_var': self.toolbar.propagation_model_var  # Share with toolbar
        }

        self.menubar = MenuBar(self.root, self.get_menu_callbacks(), menu_vars, main_window=self)
        
        # Main content area with tabs
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # ======= COVERAGE TAB =======
        coverage_tab = ttk.Frame(self.notebook)
        self.notebook.add(coverage_tab, text="Coverage")

        # Info panel on left (pack first with fixed width)
        self.info_panel = InfoPanel(coverage_tab)
        self.info_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0), pady=5)
        self.info_panel.set_plot_selected_callback(self.load_plot_from_history)

        # Map area fills remaining space (pack after info panel)
        map_frame = ttk.Frame(coverage_tab)
        map_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=map_frame)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        canvas_widget.configure(bg='#1e1e1e')

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

        # Bind resize event to redraw canvas
        self.canvas.get_tk_widget().bind('<Configure>', self._on_canvas_resize)
        
        # Context menu
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Set Transmitter Location (Click)", 
                                     command=self.set_tx_location)
        self.context_menu.add_command(label="Set Transmitter Location (Coordinates)...",
                                     command=self.set_tx_location_precise)
        self.context_menu.add_command(label="Probe Signal Strength Here",
                                     command=self.probe_signal)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Edit Station Details",
                                     command=self.edit_station_details)
        self.context_menu.add_command(label="Edit Transmitter Configuration",
                                     command=self.edit_tx_config)
        self.context_menu.add_command(label="Edit Antenna Information",
                                     command=self.edit_antenna_info)
        self.context_menu.add_command(label="Adjust Signal Threshold...",
                                     command=self.adjust_signal_threshold)
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
        self.root.bind('<Control-l>', lambda e: self.adjust_signal_threshold())
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
        """Setup the Station tab with RF chain builder - matches Station Builder design"""
        from models.component_library import ComponentLibrary

        # Initialize component library
        self.component_library = ComponentLibrary()

        # Main container
        main_frame = ttk.Frame(self.station_tab, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top section: Add components with browse buttons
        add_frame = ttk.LabelFrame(main_frame, text="Add Component", padding=8)
        add_frame.pack(fill=tk.X, pady=(0, 8))

        # Row of component type browse buttons - Antennas FIRST
        ttk.Label(add_frame, text="Browse:",
                 font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)

        btn_frame = ttk.Frame(add_frame)
        btn_frame.grid(row=0, column=1, columnspan=4, sticky=tk.W, padx=5, pady=3)

        # Antennas first, then common components, Other for filters/isolators
        ttk.Button(btn_frame, text="Antennas",
                  command=self._browse_antennas).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Cables",
                  command=lambda: self._browse_components('cable')).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Transmitters",
                  command=lambda: self._browse_components('transmitter')).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Amplifiers",
                  command=lambda: self._browse_components('amplifier')).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn_frame, text="Other...",
                  command=self._browse_other_components).pack(side=tk.LEFT, padx=3)

        # Quick search row
        ttk.Label(add_frame, text="Quick Search:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self._search_components())
        search_entry = ttk.Entry(add_frame, textvariable=self.search_var, width=35)
        search_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=5, pady=3)

        # Component type filter for quick search
        self.comp_type_var = tk.StringVar(value="all")
        comp_types = ['all'] + self.component_library.get_component_types()
        type_combo = ttk.Combobox(add_frame, textvariable=self.comp_type_var,
                                   values=comp_types, width=12, state='readonly')
        type_combo.grid(row=1, column=3, sticky=tk.W, padx=5, pady=3)
        type_combo.bind('<<ComboboxSelected>>', lambda e: self._search_components())

        # Results list (compact)
        results_frame = ttk.Frame(add_frame)
        results_frame.grid(row=2, column=0, columnspan=5, sticky=(tk.W, tk.E), padx=5, pady=3)

        self.results_listbox = tk.Listbox(results_frame, height=3, width=90,
                                          bg='#252526', fg='#cccccc',
                                          selectbackground='#0078d4',
                                          font=('Consolas', 9))
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_listbox.yview)
        self.results_listbox.config(yscrollcommand=scrollbar.set)
        self.results_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        # Add controls row
        controls_frame = ttk.Frame(add_frame)
        controls_frame.grid(row=3, column=0, columnspan=5, sticky=(tk.W, tk.E), padx=5, pady=3)

        ttk.Label(controls_frame, text="Length (ft):").pack(side=tk.LEFT, padx=3)
        self.length_var = tk.StringVar(value="100")
        ttk.Entry(controls_frame, textvariable=self.length_var, width=6).pack(side=tk.LEFT, padx=3)

        ttk.Button(controls_frame, text="Add to Chain",
                  command=self._add_to_chain).pack(side=tk.LEFT, padx=8)

        ttk.Button(controls_frame, text="Apply to Station",
                  command=self._apply_station_changes,
                  style='Accent.TButton').pack(side=tk.LEFT, padx=3)

        ttk.Separator(controls_frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # AI and Manual add buttons
        ttk.Button(controls_frame, text="AI Search...",
                  command=self._ollama_search).pack(side=tk.LEFT, padx=2)
        ttk.Button(controls_frame, text="Add Manual...",
                  command=self._quick_add_component).pack(side=tk.LEFT, padx=2)

        # ===== SYSTEM TOTALS - NOW ABOVE RF CHAIN =====
        totals_frame = ttk.LabelFrame(main_frame, text="System Totals", padding=8)
        totals_frame.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(totals_frame, text="Total Loss:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.total_loss_var = tk.StringVar(value="0.00 dB")
        ttk.Label(totals_frame, textvariable=self.total_loss_var,
                 font=('Segoe UI', 10, 'bold'), foreground='#f44336').grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(totals_frame, text="Total Gain:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        self.total_gain_var = tk.StringVar(value="0.00 dB")
        ttk.Label(totals_frame, textvariable=self.total_gain_var,
                 font=('Segoe UI', 10, 'bold'), foreground='#4caf50').grid(row=0, column=3, sticky=tk.W, padx=5)

        ttk.Label(totals_frame, text="Net Change:").grid(row=0, column=4, sticky=tk.W, padx=(20, 5))
        self.net_change_var = tk.StringVar(value="0.00 dB")
        self.net_label = ttk.Label(totals_frame, textvariable=self.net_change_var,
                                   font=('Segoe UI', 11, 'bold'))
        self.net_label.grid(row=0, column=5, sticky=tk.W, padx=5)

        # ===== RF CHAIN DISPLAY =====
        chain_frame = ttk.LabelFrame(main_frame, text="RF Chain (TX → Antenna)", padding=8)
        chain_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        # Chain tree view with fixed column widths and right alignment
        chain_tree_frame = ttk.Frame(chain_frame)
        chain_tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ('component', 'type', 'length', 'loss', 'gain')
        self.chain_tree = ttk.Treeview(chain_tree_frame, columns=columns,
                                        show='tree headings', height=10)

        # Configure alternating row colors for better visibility
        self.chain_tree.tag_configure('oddrow', background='#2d2d30')
        self.chain_tree.tag_configure('evenrow', background='#252526')
        self.chain_tree.tag_configure('antenna', background='#1a3a4a', foreground='#4fc3f7')

        # Configure headings with anchors
        self.chain_tree.heading('#0', text='#', anchor=tk.CENTER)
        self.chain_tree.heading('component', text='Component', anchor=tk.W)
        self.chain_tree.heading('type', text='Type', anchor=tk.W)
        self.chain_tree.heading('length', text='Length', anchor=tk.E)
        self.chain_tree.heading('loss', text='Loss (dB)', anchor=tk.E)
        self.chain_tree.heading('gain', text='Gain (dB)', anchor=tk.E)

        # Trim column widths - right align numeric columns
        self.chain_tree.column('#0', width=35, minwidth=35, stretch=False, anchor=tk.CENTER)
        self.chain_tree.column('component', width=220, minwidth=150, stretch=True, anchor=tk.W)
        self.chain_tree.column('type', width=80, minwidth=60, stretch=False, anchor=tk.W)
        self.chain_tree.column('length', width=60, minwidth=50, stretch=False, anchor=tk.E)
        self.chain_tree.column('loss', width=70, minwidth=60, stretch=False, anchor=tk.E)
        self.chain_tree.column('gain', width=70, minwidth=60, stretch=False, anchor=tk.E)

        chain_scrollbar = ttk.Scrollbar(chain_tree_frame, orient=tk.VERTICAL, command=self.chain_tree.yview)
        self.chain_tree.config(yscrollcommand=chain_scrollbar.set)
        self.chain_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        chain_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create context menu for RF chain
        self.chain_context_menu = tk.Menu(self.station_tab, tearoff=0)
        self.chain_context_menu.add_command(label="Move Up", command=self._move_up)
        self.chain_context_menu.add_command(label="Move Down", command=self._move_down)
        self.chain_context_menu.add_separator()
        self.chain_context_menu.add_command(label="Edit Component...", command=self._edit_chain_component)
        self.chain_context_menu.add_command(label="Remove", command=self._remove_component)
        self.chain_context_menu.add_separator()
        self.chain_context_menu.add_command(label="Clear All", command=self._clear_chain)

        # Bind right-click to show context menu
        self.chain_tree.bind('<Button-3>', self._show_chain_context_menu)
        self.chain_tree.bind('<Double-1>', lambda e: self._edit_chain_component())

        # Chain controls (compact row)
        chain_controls = ttk.Frame(chain_frame)
        chain_controls.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(chain_controls, text="Move Up", command=self._move_up, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(chain_controls, text="Move Down", command=self._move_down, width=10).pack(side=tk.LEFT, padx=2)
        ttk.Button(chain_controls, text="Edit", command=self._edit_chain_component, width=6).pack(side=tk.LEFT, padx=2)
        ttk.Button(chain_controls, text="Remove", command=self._remove_component, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(chain_controls, text="Clear All", command=self._clear_chain, width=8).pack(side=tk.LEFT, padx=2)

        ttk.Label(chain_controls, text="(Right-click or double-click to edit)",
                 font=('Segoe UI', 8, 'italic')).pack(side=tk.RIGHT, padx=5)

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
            'on_create_manual': self.create_manual_antenna,  # Fixed: menu uses on_create_manual
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
            'on_project_parameters': self.edit_station_info,
        }


    def calculate_propagation(self):
        """Calculate RF propagation coverage - shows confirmation dialog first"""
        # Update max distance from UI
        try:
            self.max_distance = float(self.menubar.vars['max_dist_var'].get())
        except ValueError:
            self.max_distance = 100

        # Get propagation model from toolbar
        propagation_model = self.toolbar.get_propagation_model()

        # Estimate calculation time using historical data
        scan_timer = get_scan_timer()
        estimated_time = scan_timer.estimate_time(
            self.max_distance, self.terrain_quality, self.use_terrain.get()
        )

        # Calculate TX power in watts and ERP
        tx_power_watts = 10 ** ((self.tx_power - 30) / 10)
        effective_erp = self.tx_power + self.system_gain_db - self.system_loss_db
        erp_watts = 10 ** ((effective_erp - 30) / 10)

        # Build settings summary for dialog
        settings = {
            'Coverage Distance': f"{self.max_distance} km",
            'Propagation Model': 'Longley-Rice (ITM)' if propagation_model == 'longley_rice' else 'Two-Ray + Diffraction',
            'Terrain Analysis': 'Enabled' if self.use_terrain.get() else 'Disabled',
            'Quality': self.terrain_quality,
            'Frequency': f"{self.frequency} MHz",
            'Tx Height': f"{self.height:.2f} m AGL",
            'TX Power': f"{tx_power_watts:.2f} W ({self.tx_power:.2f} dBm)",
            'Antenna': self.pattern_name,
            'ERP': f"{erp_watts:.2f} W ({effective_erp:.2f} dBm)"
        }

        # Show confirmation dialog
        def on_confirm():
            self._execute_propagation_calculation(propagation_model)

        def on_cancel():
            self.toolbar.set_status("Calculation cancelled")

        PlotConfirmationDialog(self.root, settings, estimated_time, on_confirm, on_cancel)

    def _execute_propagation_calculation(self, propagation_model):
        """Execute the actual propagation calculation after confirmation"""
        # Start timing the scan
        scan_timer = get_scan_timer()
        scan_timer.start_scan(self.max_distance, self.terrain_quality, self.use_terrain.get())

        # Launch a separate CMD window to show progress
        progress_process = self._launch_progress_terminal()

        try:
            # Stop AI to free up resources
            ai_was_active = self.info_panel.is_ai_active()
            if ai_was_active:
                self.info_panel.stop_ai_for_calculation()

            self.toolbar.set_status("Calculating propagation...")
            self.root.update()

            # Get custom values if in custom quality mode
            custom_az = None
            custom_dist = None
            if self.terrain_quality == 'Custom':
                custom_az, custom_dist = self.toolbar.get_custom_values()

            # Calculate effective ERP from tx_power + system gain/loss (antenna gain already in system_gain_db)
            effective_erp = self.tx_power + self.system_gain_db - self.system_loss_db

            # Define progress callback
            def progress_callback(percent, partial_terrain, distances, azimuths):
                try:
                    # Get current azimuth
                    current_az = azimuths[-1] if len(azimuths) > 0 else 0

                    # Update progress file for monitor window
                    self._write_progress('running', percent, current_az)

                    self.toolbar.set_status(f"Calculating... {percent}%")
                    self.root.update_idletasks()
                except Exception as e:
                    print(f"Progress callback error: {e}")

            # Write running status immediately so monitor starts its timer
            self._write_progress('running', 0, 0)

            # Run the calculation
            result = self.propagation_controller.calculate_coverage(
                self.tx_lat, self.tx_lon, self.height, effective_erp, self.frequency,
                self.max_distance, self.resolution, self.signal_threshold, self.rx_height,
                self.use_terrain.get(), self.terrain_quality,
                custom_az, custom_dist, propagation_model=propagation_model,
                progress_callback=progress_callback,
                zoom_level=self.zoom,
                antenna_bearing=self.antenna_bearing,
                antenna_downtilt=self.antenna_downtilt
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
            self.toolbar.set_status(f"Coverage calculated - {stats['points_above_threshold']}/{stats['total_points']} points above threshold")

            # Record scan time for future estimates
            elapsed = scan_timer.end_scan()
            print(f"\n{'='*50}")
            print(f"  COMPLETE! Calculation took {elapsed:.1f} seconds")
            print(f"{'='*50}")
            print(f"Stats: {stats}")

            # Close progress terminal
            self._close_progress_terminal(progress_process)

            # Restart AI if it was active before
            if ai_was_active:
                self.info_panel.start_ai_after_calculation()

        except Exception as e:
            # Still record the scan time even on error
            scan_timer.end_scan()
            print(f"ERROR in calculate_propagation: {e}")
            import traceback
            traceback.print_exc()

            # Write error to progress file and close terminal
            if hasattr(self, '_progress_file'):
                try:
                    with open(self._progress_file, 'w') as f:
                        f.write(f"status=error\n")
                        f.write(f"message={str(e)}\n")
                except:
                    pass
            self._close_progress_terminal(progress_process)

            messagebox.showerror("Error", f"Calculation error: {e}")
            self.toolbar.set_status("Error in calculation")
            # Restart AI even on error
            if ai_was_active:
                self.info_panel.start_ai_after_calculation()

    def _launch_progress_terminal(self):
        """Launch a separate CMD window to show calculation progress"""
        import subprocess
        import sys
        import threading

        # Path to progress file and monitor script
        app_dir = os.path.dirname(os.path.dirname(__file__))
        self._progress_file = os.path.join(app_dir, '.coverage_progress')
        monitor_script = os.path.join(app_dir, 'progress_monitor.py')

        print(f"Progress monitor script: {monitor_script}")
        print(f"Script exists: {os.path.exists(monitor_script)}")

        # Initialize progress file
        self._write_progress('starting', 0, 0)

        def launch_in_thread():
            """Launch the monitor in a background thread"""
            try:
                # Get the full path to Python (works with Anaconda)
                python_exe = sys.executable
                if python_exe.endswith('pythonw.exe'):
                    python_exe = python_exe.replace('pythonw.exe', 'python.exe')

                # Verify python.exe exists at that path
                if not os.path.exists(python_exe):
                    # Fallback: try finding python in the same directory as pythonw
                    exe_dir = os.path.dirname(sys.executable)
                    python_exe = os.path.join(exe_dir, 'python.exe')
                    if not os.path.exists(python_exe):
                        print(f"Could not find python.exe at {python_exe}")
                        return

                print(f"Python: {python_exe}")
                print(f"Script: {monitor_script}")

                # Launch with CREATE_NEW_CONSOLE flag for a visible CMD window
                # This is more reliable than cmd /c start which can fail silently
                CREATE_NEW_CONSOLE = 0x00000010
                subprocess.Popen(
                    [python_exe, monitor_script],
                    creationflags=CREATE_NEW_CONSOLE
                )
                print(f"Progress monitor launched")
            except Exception as e:
                print(f"Thread launch error: {e}")
                import traceback
                traceback.print_exc()

        try:
            if sys.platform == 'win32' and os.path.exists(monitor_script):
                # Launch in a separate thread to avoid blocking
                thread = threading.Thread(target=launch_in_thread, daemon=True)
                thread.start()
                print(f"Started launch thread")
                return True
            else:
                print(f"Platform: {sys.platform}, script exists: {os.path.exists(monitor_script)}")
                return None
        except Exception as e:
            print(f"Could not launch progress terminal: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _write_progress(self, status, percent, azimuth):
        """Write progress to file for monitor to read"""
        if hasattr(self, '_progress_file'):
            try:
                with open(self._progress_file, 'w') as f:
                    f.write(f"status={status}\n")
                    f.write(f"percent={percent}\n")
                    f.write(f"azimuth={azimuth}\n")
                    f.write(f"quality={self.terrain_quality}\n")
                    f.write(f"distance={self.max_distance}\n")
            except:
                pass

    def _close_progress_terminal(self, process):
        """Close the progress terminal window"""
        # Write complete status - the monitor will close itself after seeing this
        if hasattr(self, '_progress_file'):
            self._write_progress('complete', 100, 360)

    # ========================================================================
    # MAP INTERACTION
    # ========================================================================

    def _on_canvas_resize(self, event):
        """Handle canvas resize - resize figure to match widget"""
        if event.width > 100 and event.height > 100:
            # Resize figure to match widget
            dpi = self.fig.get_dpi()
            self.fig.set_size_inches(event.width / dpi, event.height / dpi, forward=True)
            self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
            self.ax.set_position([0, 0, 1, 1])

            # Check if we need to reload map for larger size
            if hasattr(self, '_last_canvas_size'):
                old_w, old_h = self._last_canvas_size
                # Reload if size changed significantly
                size_changed = abs(event.width - old_w) > 200 or abs(event.height - old_h) > 200
                if size_changed:
                    self._last_canvas_size = (event.width, event.height)
                    # Schedule reload (debounce to avoid excessive reloads)
                    if hasattr(self, '_resize_after_id'):
                        self.root.after_cancel(self._resize_after_id)
                    self._resize_after_id = self.root.after(300, lambda: self.reload_map(preserve_propagation=True))
            else:
                self._last_canvas_size = (event.width, event.height)
                # First resize - schedule a reload to get right size
                if hasattr(self, '_resize_after_id'):
                    self.root.after_cancel(self._resize_after_id)
                self._resize_after_id = self.root.after(500, lambda: self.reload_map(preserve_propagation=True))

            self.canvas.draw_idle()

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
        """Probe signal strength at clicked location with path profile visualization"""
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

            # Show path profile dialog with terrain visualization
            PathProfileDialog(
                self.root,
                tx_lat=self.tx_lat,
                tx_lon=self.tx_lon,
                tx_height=self.height,
                rx_lat=probe_lat,
                rx_lon=probe_lon,
                rx_height=self.rx_height,
                signal_strength=signal,
                frequency_mhz=self.frequency
            )
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
        # Convert tx_power from dBm to Watts for display
        tx_power_watts = 10 ** ((self.tx_power - 30) / 10)

        # Save old values to detect threshold-only changes
        old_threshold = self.signal_threshold
        old_power = self.tx_power
        old_freq = self.frequency
        old_height = self.height
        old_rx_height = self.rx_height

        dialog = TransmitterConfigDialog(self.root, tx_power_watts, self.frequency,
                                        self.height, self.rx_height, self.signal_threshold)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            new_tx_power_watts, self.frequency, self.height, self.rx_height, self.signal_threshold = dialog.result

            # Convert Watts to dBm and update tx_power
            self.tx_power = 10 * math.log10(new_tx_power_watts * 1000)  # W to mW to dBm

            # Update transmitter in rf_chain if present
            for i, (component, length_ft) in enumerate(self.rf_chain):
                if component.get('component_type') == 'transmitter':
                    component_copy = component.copy()
                    component_copy['transmit_power_watts'] = new_tx_power_watts
                    self.rf_chain[i] = (component_copy, length_ft)
                    break

            # Calculate effective ERP for display
            effective_erp = self.tx_power + self.system_gain_db - self.system_loss_db

            # Check if only the threshold changed (can re-plot without recalculating)
            threshold_changed = (self.signal_threshold != old_threshold)
            rf_params_changed = (
                abs(self.tx_power - old_power) > 0.01 or
                self.frequency != old_freq or
                self.height != old_height or
                self.rx_height != old_rx_height
            )

            if threshold_changed and not rf_params_changed and self.last_propagation is not None:
                # Only threshold changed - just re-plot with new color range
                self._replot_with_new_threshold()
                self.toolbar.set_status(f"Threshold updated to {self.signal_threshold} dBm (colors adjusted, no recalculation needed)")
            else:
                self.toolbar.set_status(f"Config updated - TX: {new_tx_power_watts:.2f}W, ERP: {effective_erp:.2f} dBm, Freq: {self.frequency} MHz")

            self.update_info_panel()
            self.save_auto_config()

    def _replot_with_new_threshold(self):
        """Re-plot existing propagation data with a new signal threshold (no recalculation)"""
        if self.last_propagation is None:
            return

        x_grid, y_grid, rx_power_grid = self.last_propagation
        tx_pixel_x, tx_pixel_y = self.map_display.get_tx_pixel_position(
            self.tx_lat, self.tx_lon
        )

        # Save current zoom state
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()

        self.propagation_plot.plot_coverage(
            self.map_display.map_image, tx_pixel_x, tx_pixel_y,
            x_grid, y_grid, rx_power_grid, self.signal_threshold,
            self.map_display.get_pixel_scale(),
            self.last_terrain_loss, self.show_shadow.get(),
            (current_xlim, current_ylim),
            alpha=self.toolbar.get_transparency()
        )

    def adjust_signal_threshold(self):
        """Quick-adjust signal threshold and re-plot without recalculating (Ctrl+L)"""
        new_threshold = simpledialog.askfloat(
            "Adjust Signal Threshold",
            "Enter minimum signal level (dBm):\n\n"
            "This adjusts the color range without recalculating.\n"
            "Common values: -120 (sensitive), -95 (moderate), -80 (strong)",
            initialvalue=self.signal_threshold,
            minvalue=-200, maxvalue=0
        )

        if new_threshold is not None and new_threshold != self.signal_threshold:
            self.signal_threshold = new_threshold
            if self.last_propagation is not None and self.show_coverage.get():
                self._replot_with_new_threshold()
                self.toolbar.set_status(f"Threshold adjusted to {self.signal_threshold} dBm (colors updated)")
            else:
                self.toolbar.set_status(f"Threshold set to {self.signal_threshold} dBm (will apply on next plot)")
            self.update_info_panel()
            self.save_auto_config()

    def edit_station_details(self):
        """Edit station details (callsign, frequency, tx type, mode) without re-downloading map"""
        dialog = StationInfoDialog(self.root, self.callsign, self.frequency,
                                   self.tx_type, self.transmission_mode)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            self.callsign = dialog.result['callsign']
            self.frequency = dialog.result['frequency']
            self.tx_type = dialog.result['tx_type']
            self.transmission_mode = dialog.result['transmission_mode']

            self.update_info_panel()
            self.toolbar.set_status(f"Station details updated - {self.callsign}, {self.frequency} MHz")
            self.save_auto_config()

    def edit_antenna_info(self):
        """Edit antenna information including bearing and downtilt"""
        dialog = AntennaInfoDialog(self.root, self.pattern_name,
                                   current_bearing=self.antenna_bearing,
                                   current_downtilt=self.antenna_downtilt)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            action, data = dialog.result
            if action == 'settings':
                # Update bearing and downtilt
                self.antenna_bearing = data['bearing']
                self.antenna_downtilt = data['downtilt']
                self.toolbar.set_status(f"Antenna: bearing={self.antenna_bearing:.1f}°, downtilt={self.antenna_downtilt:.1f}°")
                self.save_auto_config()
                print(f"Antenna settings updated: bearing={self.antenna_bearing:.1f}°, downtilt={self.antenna_downtilt:.1f}°")
            elif action == 'load':
                if self.antenna_pattern.load_from_xml(data):
                    self.pattern_name = data.split('/')[-1].split('\\')[-1]
                    self.toolbar.set_status(f"Antenna pattern loaded: {self.pattern_name}")
                    self.save_auto_config()
                else:
                    messagebox.showerror("Error", "Failed to load antenna pattern")
            elif action == 'reset':
                self.antenna_pattern.load_default_omni()
                self.pattern_name = "Default Omni (0 dBi)"
                self.antenna_bearing = 0.0
                self.antenna_downtilt = 0.0
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

        def update_system(total_loss, total_gain, net_change, rf_chain, antenna_id,
                          antenna_bearing=0.0, antenna_downtilt=0.0):
            """Callback to update system loss/gain, RF chain, antenna, bearing, and downtilt"""
            self.system_loss_db = total_loss
            self.system_gain_db = total_gain
            self.rf_chain = rf_chain
            self.antenna_bearing = antenna_bearing
            self.antenna_downtilt = antenna_downtilt

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
                        print(f"Loaded antenna: {self.pattern_name}, bearing: {antenna_bearing:.1f}°, downtilt: {antenna_downtilt:.1f}°")
            else:
                # No antenna selected - use default omni
                self.current_antenna_id = None

            # Save to project config
            self.save_auto_config()

            # Update displayed ERP (add net change to current ERP)
            print(f"System updated: Loss={total_loss:.2f} dB, Gain={total_gain:.2f} dB, Net={net_change:+.2f} dB")
            self.update_info_panel()

        StationBuilderDialog(self.root, self.frequency, callback=update_system,
                            initial_chain=self.rf_chain, initial_antenna=self.current_antenna_id,
                            initial_bearing=self.antenna_bearing, initial_downtilt=self.antenna_downtilt)

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
        """Open smart import dialog for AI-powered component/antenna import"""
        from gui.smart_import_dialog import SmartImportDialog

        def on_component_imported(component_data):
            """Handle component imported from smart import"""
            comp_type = component_data.get('component_type', 'unknown')

            # Handle transmitters specially
            if comp_type == 'transmitter':
                self._add_transmitter_with_power(component_data)
            else:
                # Add to RF chain with default length
                length_ft = 100 if comp_type == 'cable' else 0
                self.rf_chain.append((component_data, length_ft))
                self._update_chain_display()
                self._calculate_totals()

            # Refresh search results
            self._search_components()

        def on_antenna_imported(antenna_id):
            """Handle antenna imported from smart import"""
            # Reload antenna library and update current antenna
            self.antenna_library = AntennaLibrary()
            self.current_antenna_id = antenna_id
            self._update_chain_display()
            self._calculate_totals()

        SmartImportDialog(
            self.root,
            self.frequency,
            on_component_imported=on_component_imported,
            on_antenna_imported=on_antenna_imported
        )

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

    def _browse_antennas(self):
        """Open antenna browser dialog"""
        from gui.component_browser import ComponentBrowserDialog

        def on_antenna_selected(antenna_data, _):
            """Handle antenna selection from browser"""
            antenna_id = antenna_data.get('antenna_id')
            if antenna_id:
                self.current_antenna_id = antenna_id
                # Update bearing/downtilt if provided
                if 'bearing' in antenna_data:
                    self.antenna_bearing = antenna_data['bearing']
                if 'downtilt' in antenna_data:
                    self.antenna_downtilt = antenna_data['downtilt']
                self._update_chain_display()
                self._calculate_totals()

        ComponentBrowserDialog(
            self.root,
            'antenna',
            self.frequency,
            on_select=on_antenna_selected
        )

    def _browse_components(self, component_type: str):
        """Open component browser for a specific type"""
        from gui.component_browser import ComponentBrowserDialog

        def on_component_selected(component, length_ft):
            """Handle component selection from browser"""
            comp_type = component.get('component_type', component_type)

            # Handle transmitters specially (need power input)
            if comp_type == 'transmitter':
                self._add_transmitter_with_power(component)
            else:
                self.rf_chain.append((component, length_ft))
                self._update_chain_display()
                self._calculate_totals()

        ComponentBrowserDialog(
            self.root,
            component_type,
            self.frequency,
            on_select=on_component_selected
        )

    def _browse_other_components(self):
        """Show dialog to select other component types"""
        all_types = self.component_library.get_component_types()
        common_types = ['cable', 'transmitter', 'amplifier', 'filter', 'isolator']
        other_types = [t for t in all_types if t not in common_types]

        if not other_types:
            messagebox.showinfo("No Other Types", "No additional component types available")
            return

        # Create selection dialog
        select_dialog = tk.Toplevel(self.root)
        select_dialog.title("Select Component Type")
        select_dialog.geometry("300x200")
        select_dialog.transient(self.root)

        ttk.Label(select_dialog, text="Select component type:",
                 font=('Segoe UI', 10, 'bold')).pack(pady=10)

        type_listbox = tk.Listbox(select_dialog, height=6,
                                  bg='#252526', fg='#cccccc',
                                  selectbackground='#0078d4')
        for t in other_types:
            type_listbox.insert(tk.END, t.replace('_', ' ').title())
        type_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def on_select():
            sel = type_listbox.curselection()
            if sel:
                selected_type = other_types[sel[0]]
                select_dialog.destroy()
                self._browse_components(selected_type)

        ttk.Button(select_dialog, text="Browse",
                  command=on_select, style='Accent.TButton').pack(pady=10)

    def _add_transmitter_with_power(self, component):
        """Add transmitter with power input dialog"""
        max_power = component.get('power_output_watts', 1000)

        power_dialog = tk.Toplevel(self.root)
        power_dialog.title("Set Transmitter Power")
        power_dialog.geometry("350x150")
        power_dialog.transient(self.root)
        power_dialog.grab_set()

        ttk.Label(power_dialog, text=f"Transmitter: {component.get('model', 'Unknown')}",
                 font=('Segoe UI', 10, 'bold')).pack(pady=10)
        ttk.Label(power_dialog, text=f"Max Rated Power: {max_power} W").pack(pady=5)

        power_frame = ttk.Frame(power_dialog)
        power_frame.pack(pady=10)

        ttk.Label(power_frame, text="Transmit Power (W):").pack(side=tk.LEFT, padx=5)
        power_var = tk.StringVar(value=str(max_power))
        power_entry = ttk.Entry(power_frame, textvariable=power_var, width=10)
        power_entry.pack(side=tk.LEFT, padx=5)

        def on_ok():
            try:
                transmit_power = float(power_var.get())
                if transmit_power <= 0:
                    raise ValueError("Must be positive")
                if transmit_power > max_power * 1.1:
                    if not messagebox.askyesno("Power Warning",
                                             f"Transmit power ({transmit_power}W) exceeds rated maximum ({max_power}W).\nContinue anyway?"):
                        return
                component_copy = component.copy()
                component_copy['transmit_power_watts'] = transmit_power
                self.rf_chain.append((component_copy, 0))
                power_dialog.destroy()
                self._update_chain_display()
                self._calculate_totals()
            except ValueError:
                messagebox.showerror("Invalid Power", "Please enter a valid positive number")

        button_frame = ttk.Frame(power_dialog)
        button_frame.pack(pady=10)
        ttk.Button(button_frame, text="OK", command=on_ok).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=power_dialog.destroy).pack(side=tk.LEFT, padx=5)

        power_entry.focus()
        power_dialog.bind('<Return>', lambda e: on_ok())

    def _show_chain_context_menu(self, event):
        """Show context menu for RF chain treeview"""
        item = self.chain_tree.identify_row(event.y)
        if item:
            self.chain_tree.selection_set(item)

        try:
            self.chain_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.chain_context_menu.grab_release()

    def _edit_chain_component(self):
        """Edit selected component in chain"""
        selection = self.chain_tree.selection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a component to edit")
            return

        item_id = selection[0]
        if item_id == 'antenna_item':
            messagebox.showinfo("Edit Antenna", "Use the Antenna browser to change the antenna selection")
            return

        index = int(item_id.replace('item_', ''))
        component, current_length = self.rf_chain[index]

        # Create edit dialog
        edit_dialog = tk.Toplevel(self.root)
        edit_dialog.title("Edit Component")
        edit_dialog.geometry("400x200")
        edit_dialog.transient(self.root)

        ttk.Label(edit_dialog, text=f"Component: {component.get('model', 'Unknown')}",
                 font=('Segoe UI', 10, 'bold')).pack(pady=10)

        comp_type = component.get('component_type')
        if comp_type == 'cable':
            ttk.Label(edit_dialog, text="Length (ft):").pack(pady=5)
            length_var = tk.StringVar(value=str(current_length))
            length_entry = ttk.Entry(edit_dialog, textvariable=length_var, width=20)
            length_entry.pack(pady=5)

            def save_changes():
                try:
                    new_length = float(length_var.get())
                    self.rf_chain[index] = (component, new_length)
                    self._update_chain_display()
                    self._calculate_totals()
                    edit_dialog.destroy()
                except ValueError:
                    messagebox.showerror("Invalid Length", "Please enter a valid length in feet")

            ttk.Button(edit_dialog, text="Save", command=save_changes).pack(pady=10)
            ttk.Button(edit_dialog, text="Cancel", command=edit_dialog.destroy).pack()
        elif comp_type == 'transmitter':
            max_power = component.get('power_output_watts', 1000)
            current_power = component.get('transmit_power_watts', max_power)

            ttk.Label(edit_dialog, text=f"Max Rated Power: {max_power} W").pack(pady=5)
            ttk.Label(edit_dialog, text="Transmit Power (W):").pack(pady=5)

            power_var = tk.StringVar(value=str(current_power))
            power_entry = ttk.Entry(edit_dialog, textvariable=power_var, width=20)
            power_entry.pack(pady=5)

            def save_changes():
                try:
                    new_power = float(power_var.get())
                    if new_power <= 0:
                        raise ValueError("Must be positive")
                    if new_power > max_power * 1.1:
                        if not messagebox.askyesno("Power Warning",
                                                 f"Transmit power ({new_power}W) exceeds rated maximum ({max_power}W).\nContinue anyway?"):
                            return
                    component_copy = component.copy()
                    component_copy['transmit_power_watts'] = new_power
                    self.rf_chain[index] = (component_copy, current_length)
                    self._update_chain_display()
                    self._calculate_totals()
                    edit_dialog.destroy()
                except ValueError:
                    messagebox.showerror("Invalid Power", "Please enter a valid positive number")

            ttk.Button(edit_dialog, text="Save", command=save_changes).pack(pady=10)
            ttk.Button(edit_dialog, text="Cancel", command=edit_dialog.destroy).pack()
        else:
            ttk.Label(edit_dialog, text="This component type cannot be modified.\nYou can remove and re-add it if needed.").pack(pady=20)
            ttk.Button(edit_dialog, text="Close", command=edit_dialog.destroy).pack(pady=10)

    def _quick_add_component(self):
        """Quick add component dialog - easy manual entry"""
        try:
            from gui.quick_add_component_dialog import QuickAddComponentDialog

            def on_component_created(component_data):
                """Callback when component is created"""
                comp_type = component_data.get('component_type')

                # Add to component library
                self.component_library.add_custom_component(component_data)

                # If antenna was created, refresh
                if comp_type == 'antenna':
                    self.antenna_library = AntennaLibrary()

                # Refresh search results
                self._search_components()

            QuickAddComponentDialog(self.root, self.frequency, on_component_created)
        except ImportError:
            messagebox.showwarning("Not Available", "Quick add component dialog not available")

    def _update_chain_display(self):
        """Update chain tree view with alternating row colors"""
        # Clear existing
        for item in self.chain_tree.get_children():
            self.chain_tree.delete(item)

        # Add components with alternating row colors
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

            length_str = f"{length_ft:.1f} ft" if length_ft > 0 else "-"
            loss_str = f"{loss_db:.2f}" if loss_db > 0 else "-"
            gain_str = f"{gain_db:.2f}" if gain_db > 0 else "-"

            # Alternate row colors for better readability
            row_tag = 'oddrow' if idx % 2 == 0 else 'evenrow'
            self.chain_tree.insert('', tk.END, iid=f'item_{idx}',
                                   text=f"{idx + 1}",
                                   values=(model, comp_type, length_str, loss_str, gain_str),
                                   tags=(row_tag,))

        # Add antenna at the end if selected
        if self.current_antenna_id:
            antenna_data = self.antenna_library.antennas.get(self.current_antenna_id)
            if antenna_data:
                antenna_name = antenna_data.get('name', 'Unknown')
                antenna_gain = antenna_data.get('gain', 0)

                antenna_idx = len(self.rf_chain)
                self.chain_tree.insert('', tk.END, iid=f'antenna_item',
                                       text=f"{antenna_idx + 1}",
                                       values=(antenna_name, 'antenna', '-', '-', f"{antenna_gain:.2f}"),
                                       tags=('antenna',))

    def _calculate_totals(self):
        """Calculate total loss and gain including antenna"""
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

        # Add antenna gain if selected
        if self.current_antenna_id:
            antenna_data = self.antenna_library.antennas.get(self.current_antenna_id)
            if antenna_data:
                antenna_gain = antenna_data.get('gain', 0)
                total_gain += antenna_gain

        net_change = total_gain - total_loss

        self.total_loss_var.set(f"{total_loss:.2f} dB")
        self.total_gain_var.set(f"{total_gain:.2f} dB")
        self.net_change_var.set(f"{net_change:+.2f} dB")

        # Color code net change
        if net_change > 0:
            self.net_label.config(foreground='#4caf50')  # Green
        elif net_change < 0:
            self.net_label.config(foreground='#f44336')  # Red
        else:
            self.net_label.config(foreground='#cccccc')  # Neutral

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
                print("Saving project...")

                project_data = {
                    'version': '3.2',  # Bumped - terrain now uses SRTM tiles, no cache in project
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
                    'antenna_bearing': self.antenna_bearing,
                    'antenna_downtilt': self.antenna_downtilt,
                    'zoom': self.zoom,
                    'min_zoom': getattr(self.toolbar, 'min_zoom', self.zoom),
                    'basemap': self.basemap,
                    'saved_plots': self.saved_plots,
                    'fcc_data': self.fcc_data,
                    # Note: Terrain data now comes from SRTM tiles, not project file
                }

                with open(filename, 'w') as f:
                    json.dump(project_data, f, indent=2)

                messagebox.showinfo("Success",
                                  f"Project saved to:\n{filename}\n\n"
                                  f"Included {len(self.saved_plots)} coverage plots")
                print(f"  Project saved: {filename}")
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
                self.antenna_bearing = project_data.get('antenna_bearing', 0.0)
                self.antenna_downtilt = project_data.get('antenna_downtilt', 0.0)
                self.zoom = 10  # Always start at zoom 10
                self.basemap = project_data.get('basemap', 'Esri WorldImagery')
                self.saved_plots = project_data.get('saved_plots', [])
                self.fcc_data = project_data.get('fcc_data', None)

                # Load antenna pattern if specified
                if self.current_antenna_id:
                    self.load_antenna_from_library(self.current_antenna_id)

                # Note: Terrain data now comes from SRTM tiles automatically
                # Legacy terrain_cache in old project files is ignored

                # Update UI
                self.toolbar.update_location(self.tx_lat, self.tx_lon)
                min_zoom = project_data.get('min_zoom', self.zoom)
                self.toolbar.set_min_zoom(min_zoom)  # Set constraint first
                self.toolbar.set_zoom(max(10, min_zoom))  # Then set zoom
                self.menubar.vars['basemap_var'].set(self.basemap)
                self.menubar.vars['max_dist_var'].set(str(self.max_distance))
                self.toolbar.set_quality(self.terrain_quality)
                self.on_quality_change()

                self.update_info_panel()
                self.last_propagation = None
                self.reload_map(preserve_propagation=False)

                # Update plots dropdown
                self.info_panel.update_plots_dropdown(self.saved_plots)

                messagebox.showinfo("Success",
                                  f"Project loaded:\n{self.callsign}\n\n"
                                  f"{len(self.saved_plots)} coverage plots restored")
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

        # First check if server is already running (most common case)
        if self.is_ollama_server_running():
            self.logger.log("AI Assistant: Server is already running")
            messagebox.showinfo(
                "Ready",
                "Ollama is installed and running!\n\n"
                "You can now use AI Antenna Import from the Tools menu."
            )
            self.logger.log("="*80)
            self.logger.log("AI ANTENNA ASSISTANT - CHECK COMPLETED")
            self.logger.log("="*80)
            return

        # Server not running - check if Ollama CLI is in PATH so we can start it
        if self.is_ollama_installed():
            self.logger.log("AI Assistant: Ollama CLI found, attempting to start server...")
            self.start_ollama_server()
            self.logger.log("="*80)
            self.logger.log("AI ANTENNA ASSISTANT - CHECK COMPLETED")
            self.logger.log("="*80)
            return

        # Neither server running nor CLI available - offer to install
        self.logger.log("Ollama not found - asking user to install")
        response = messagebox.askyesno(
            "Ollama Not Found",
            "Ollama AI server is not running and the CLI is not in PATH.\n\n"
            "Would you like to install Ollama now?\n\n"
            "(This will download ~850MB)\n\n"
            "If Ollama is already installed, try starting it manually first."
        )
        if response:
            self.install_ollama()
        else:
            self.logger.log("User declined Ollama installation")
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
        self.zoom = dialog.result['zoom']
        self.basemap = dialog.result['basemap']
        self.max_distance = dialog.result['radius']
        
        self.toolbar.update_location(self.tx_lat, self.tx_lon)
        self.toolbar.set_zoom(self.zoom)
        self.toolbar.set_min_zoom(self.zoom)  # Constrain zoom to cached levels
        self.update_info_panel()

        # Cache map tiles starting from the selected zoom level
        self.cache_all_zoom_levels(self.tx_lat, self.tx_lon)
        # Note: Terrain data is fetched on-demand during propagation calculation

        self.reload_map(preserve_propagation=False)

        messagebox.showinfo("Project Ready",
                          "Map tiles cached!\n\n"
                          "Ready to calculate coverage!")
        
        self.save_auto_config()
    
    def refresh_map_dialog(self):
        """Show map refresh dialog"""
        self.edit_station_info()
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_canvas_size(self):
        """Get current canvas size in pixels"""
        widget = self.canvas.get_tk_widget()
        return widget.winfo_width(), widget.winfo_height()

    def reload_map(self, preserve_propagation=True):
        """Reload map with current settings"""
        canvas_w, canvas_h = self._get_canvas_size()
        success = self.map_display.load_map(self.tx_lat, self.tx_lon, self.zoom,
                                           self.basemap, self.cache,
                                           canvas_width=canvas_w, canvas_height=canvas_h)
        
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

        # Get transmitter name from RF chain
        transmitter_name = None
        for component, length_ft in self.rf_chain:
            if component.get('component_type') == 'transmitter':
                transmitter_name = component.get('model', component.get('name', 'Unknown'))
                break

        self.info_panel.update(
            self.callsign, self.frequency, self.transmission_mode, self.tx_type,
            self.tx_lat, self.tx_lon, self.height, self.rx_height, self.tx_power, self.system_loss_db, self.system_gain_db, self.pattern_name,
            self.max_distance, self.signal_threshold,
            self.use_terrain.get(), self.terrain_quality,
            antenna_details=antenna_details,
            transmitter_name=transmitter_name
        )
    
    def cache_all_zoom_levels(self, lat, lon):
        """Cache map tiles from project min zoom to max zoom (16)"""
        from models.map_handler import MapHandler

        # Get minimum zoom from toolbar (set during project setup)
        min_zoom = getattr(self.toolbar, 'min_zoom', 10)
        print(f"Caching zoom levels {min_zoom}-16 for {lat:.6f}, {lon:.6f}...")
        zoom_levels = list(range(min_zoom, 17))  # min_zoom to 16 inclusive

        for i, zoom in enumerate(zoom_levels):
            self.toolbar.set_status(f"Caching zoom level {zoom} [{i+1}/{len(zoom_levels)}]...")
            self.root.update()
            MapHandler.get_map_tile(lat, lon, zoom, tile_size=3,
                                   basemap=self.basemap, cache=self.cache)

        self.toolbar.set_status(f"Zoom levels {min_zoom}-16 cached")
    
    def precache_terrain_for_coverage(self):
        """Pre-cache terrain elevation data"""
        print(f"Pre-caching terrain data...")

        # Ensure terrain_quality has a valid value
        if not hasattr(self, 'terrain_quality') or self.terrain_quality is None:
            self.terrain_quality = 'Medium'

        # Ensure max_distance has a valid value
        if not hasattr(self, 'max_distance') or self.max_distance is None or self.max_distance <= 0:
            self.max_distance = 50.0

        presets = {
            'Low': (36, 25),
            'Medium': (72, 50),
            'High': (360, 100)
        }

        azimuths_count, distances_count = presets.get(self.terrain_quality, (72, 50))

        # Ensure we have valid counts
        if azimuths_count is None or azimuths_count <= 0:
            azimuths_count = 72
        if distances_count is None or distances_count <= 0:
            distances_count = 50

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

        # Update the plots dropdown in info panel
        self.info_panel.update_plots_dropdown(self.saved_plots)

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

            # Update plots dropdown
            self.info_panel.update_plots_dropdown(self.saved_plots)

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
                self.tx_power = config.get('tx_power', self.tx_power)

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
                'system_gain_db': self.system_gain_db,
                'tx_power': self.tx_power
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
