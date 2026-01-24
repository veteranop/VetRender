"""
Menu Bar Module
===============
Application menu bar with File, View, Plot Settings, and Help menus.
"""

import tkinter as tk
from models.map_handler import MapHandler


class MenuBar:
    """Application menu bar"""

    def __init__(self, root, callbacks, variables, main_window=None):
        """Initialize menu bar

        Args:
            root: Root tkinter window
            callbacks: Dictionary of callback functions
            variables: Dictionary of tkinter variables
            main_window: Main application window instance (for direct method access)
        """
        self.root = root
        self.callbacks = callbacks
        self.vars = variables
        self.main_window = main_window

        self.menubar = tk.Menu(root)
        root.config(menu=self.menubar)

        self.setup_menus()

    def setup_menus(self):
        """Create all menus"""
        self.setup_project_menu()
        self.setup_view_menu()
        self.setup_antenna_menu()
        self.setup_station_menu()
        self.setup_fcc_menu()
        self.setup_plot_settings_menu()
        self.setup_export_menu()
        self.setup_help_menu()

    def setup_project_menu(self):
        """Create Project menu"""
        project_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Project", menu=project_menu)

        project_menu.add_command(label="New Project",
                            command=self.callbacks['on_new_project'],
                            accelerator="Ctrl+N")
        project_menu.add_command(label="Load Project",
                            command=self.callbacks['on_load_project'],
                            accelerator="Ctrl+O")
        project_menu.add_command(label="Save Project",
                            command=self.callbacks['on_save_project'],
                            accelerator="Ctrl+S")
        project_menu.add_separator()
        project_menu.add_command(label="Exit",
                            command=self.callbacks['on_exit'],
                            accelerator="Ctrl+Q")

    def setup_view_menu(self):
        """Create View menu"""
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=view_menu)

        # Basemap submenu
        basemap_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Basemap", menu=basemap_menu)

        for name in MapHandler.BASEMAPS.keys():
            basemap_menu.add_radiobutton(
                label=name,
                variable=self.vars['basemap_var'],
                value=name,
                command=self.callbacks['on_basemap_change']
            )

        # Layer submenu
        layer_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="Layers", menu=layer_menu)

        layer_menu.add_checkbutton(
            label="Coverage Overlay",
            variable=self.vars['show_coverage_var'],
            command=self.callbacks['on_toggle_coverage']
        )
        layer_menu.add_checkbutton(
            label="Shadow Zones",
            variable=self.vars['show_shadow_var'],
            command=self.callbacks['on_toggle_shadow']
        )

    def setup_antenna_menu(self):
        """Create Antenna menu"""
        antenna_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Antenna", menu=antenna_menu)

        antenna_menu.add_command(label="AI Antenna Assistant",
                                command=self.callbacks.get('on_ai_assistant', lambda: None))
        antenna_menu.add_separator()
        antenna_menu.add_command(label="AI Antenna Import",
                                command=self.callbacks.get('on_ai_import', lambda: None))
        antenna_menu.add_separator()
        antenna_menu.add_command(label="Manual Antenna Import",
                                command=self.callbacks.get('on_manual_import', lambda: None))
        antenna_menu.add_command(label="Create Manual Antenna",
                                command=self.callbacks.get('on_create_manual', lambda: None))
        antenna_menu.add_separator()
        antenna_menu.add_command(label="View Antennas",
                                command=self.callbacks.get('on_view_antennas', lambda: None))
        antenna_menu.add_command(label="Export Antenna",
                                command=self.callbacks.get('on_export_antenna', lambda: None))

    def setup_station_menu(self):
        """Create Station menu"""
        station_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Station", menu=station_menu)

        station_menu.add_command(label="Station Builder",
                                command=self.callbacks.get('on_station_builder', lambda: None),
                                accelerator="Ctrl+B")
        station_menu.add_separator()
        station_menu.add_command(label="Configure Transmitter",
                                command=self.callbacks.get('on_configure_transmitter', lambda: None),
                                accelerator="Ctrl+T")

    def setup_fcc_menu(self):
        """Create FCC Query menu"""
        print("MENUBAR: Setting up FCC menu")
        fcc_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Query FCC", menu=fcc_menu)
        print("MENUBAR: FCC menu created and added to menu bar")

        # Use main window instance for direct method calls
        if self.main_window:
            fcc_menu.add_command(label="Pull Report for Current Station",
                                command=self.main_window.fcc_pull_current_station)
            fcc_menu.add_command(label="View FCC Data for This Project",
                                command=self.main_window.fcc_view_data)
            fcc_menu.add_command(label="Purge FCC Data from Project",
                                command=self.main_window.fcc_purge_data)
            fcc_menu.add_separator()
            fcc_menu.add_command(label="Pull Report from Station ID",
                                command=self.main_window.fcc_manual_query)
        else:
            # Fallback if main_window not provided
            fcc_menu.add_command(label="Pull Report for Current Station",
                                command=self.callbacks.get('on_fcc_pull_current', lambda: None))
            fcc_menu.add_command(label="View FCC Data for This Project",
                                command=self.callbacks.get('on_fcc_view', lambda: None))
            fcc_menu.add_command(label="Purge FCC Data from Project",
                                command=self.callbacks.get('on_fcc_purge', lambda: None))
            fcc_menu.add_separator()
            fcc_menu.add_command(label="Pull Report from Station ID",
                                command=self.callbacks.get('on_fcc_manual', lambda: None))

    def setup_plot_settings_menu(self):
        """Create Plot Settings menu"""
        plot_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Plot Settings", menu=plot_menu)

        # Coverage Distance submenu
        distance_menu = tk.Menu(plot_menu, tearoff=0)
        plot_menu.add_cascade(label="Coverage Distance", menu=distance_menu)

        distances = [25, 50, 75, 100, 125, 150, 175, 200]
        for dist in distances:
            distance_menu.add_radiobutton(
                label=f"{dist} km",
                variable=self.vars['max_dist_var'],
                value=str(dist),
                command=self.callbacks['on_max_distance_change']
            )

        distance_menu.add_separator()
        distance_menu.add_command(
            label="Custom...",
            command=self.callbacks['on_custom_distance']
        )

        # Terrain checkbox
        plot_menu.add_checkbutton(
            label="Enable Terrain",
            variable=self.vars['use_terrain_var'],
            command=self.callbacks['on_toggle_terrain']
        )

        # Quality submenu
        quality_menu = tk.Menu(plot_menu, tearoff=0)
        plot_menu.add_cascade(label="Terrain Quality", menu=quality_menu)

        quality_menu.add_radiobutton(
            label="Low",
            variable=self.vars['quality_var'],
            value="Low",
            command=self.callbacks['on_quality_change']
        )
        quality_menu.add_radiobutton(
            label="Medium",
            variable=self.vars['quality_var'],
            value="Medium",
            command=self.callbacks['on_quality_change']
        )
        quality_menu.add_radiobutton(
            label="High",
            variable=self.vars['quality_var'],
            value="High",
            command=self.callbacks['on_quality_change']
        )
        quality_menu.add_radiobutton(
            label="Ultra",
            variable=self.vars['quality_var'],
            value="Ultra",
            command=self.callbacks['on_quality_change']
        )
        quality_menu.add_radiobutton(
            label="Custom",
            variable=self.vars['quality_var'],
            value="Custom",
            command=self.callbacks['on_quality_change']
        )

    def setup_export_menu(self):
        """Create Export menu"""
        export_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Export", menu=export_menu)

        # Get reference to main window instance for direct method calls
        main_window = self.main_window if self.main_window else self.root

        export_menu.add_command(label="Generate Report",
                               command=getattr(main_window, 'generate_report', lambda: print("WARNING: generate_report not found on main_window")))
        export_menu.add_separator()
        export_menu.add_command(label="KML Coverage",
                               command=self.callbacks.get('on_export_kml', lambda: None))
        export_menu.add_command(label="Images (All Zooms)",
                               command=self.callbacks.get('on_export_images', lambda: None))

    def setup_help_menu(self):
        """Create Help menu"""
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)

        help_menu.add_command(
            label="Quick Start Guide",
            command=self.callbacks.get('on_quick_start', lambda: None)
        )
        help_menu.add_command(
            label="User Manual",
            command=self.callbacks.get('on_user_manual', lambda: None)
        )
        help_menu.add_separator()
        help_menu.add_command(
            label="About VetRender",
            command=self.callbacks.get('on_about', lambda: None)
        )
        help_menu.add_command(
            label="Report a Bug",
            command=self.callbacks.get('on_report_bug', lambda: None)
        )