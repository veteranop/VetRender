"""
Menu Bar Module
===============
Application menu bar with File, View, and Plot Settings menus.
"""

import tkinter as tk
from models.map_handler import MapHandler


class MenuBar:
    """Application menu bar"""
    
    def __init__(self, root, callbacks, variables):
        """Initialize menu bar
        
        Args:
            root: Root tkinter window
            callbacks: Dictionary of callback functions:
                - on_new_project
                - on_save_project
                - on_load_project
                - on_exit
                - on_basemap_change
                - on_toggle_coverage
                - on_toggle_shadow
                - on_max_distance_change
                - on_custom_distance
                - on_toggle_terrain
                - on_quality_change
                - on_terrain_detail_change
                - on_custom_terrain_detail
            variables: Dictionary of tkinter variables:
                - basemap_var
                - show_coverage_var
                - show_shadow_var
                - use_terrain_var
                - max_dist_var
                - quality_var
                - terrain_detail_var
        """
        self.root = root
        self.callbacks = callbacks
        self.vars = variables
        
        self.menubar = tk.Menu(root)
        root.config(menu=self.menubar)
        
        self.setup_menus()
    
    def setup_menus(self):
        """Create all menus"""
        self.setup_file_menu()
        self.setup_view_menu()
        self.setup_plot_settings_menu()
    
    def setup_file_menu(self):
        """Create File menu"""
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="New Project", 
                            command=self.callbacks['on_new_project'],
                            accelerator="Ctrl+N")
        file_menu.add_command(label="Save Project",
                            command=self.callbacks['on_save_project'],
                            accelerator="Ctrl+S")
        file_menu.add_command(label="Load Project",
                            command=self.callbacks['on_load_project'],
                            accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Exit",
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
            label="Use Terrain Analysis",
            variable=self.vars['use_terrain_var']
        )
        
        # Quality submenu
        quality_menu = tk.Menu(plot_menu, tearoff=0)
        plot_menu.add_cascade(label="Quality", menu=quality_menu)
        
        for quality in ['Low', 'Medium', 'High', 'Ultra']:
            quality_menu.add_radiobutton(
                label=quality,
                variable=self.vars['quality_var'],
                value=quality,
                command=lambda q=quality: self.callbacks['on_quality_change'](q)
            )
        
        quality_menu.add_separator()
        quality_menu.add_radiobutton(
            label="Custom",
            variable=self.vars['quality_var'],
            value="Custom",
            command=lambda: self.callbacks['on_quality_change']('Custom')
        )
        
        # Terrain Detail submenu (🔥 NEW FEATURE!)
        terrain_detail_menu = tk.Menu(plot_menu, tearoff=0)
        plot_menu.add_cascade(label="Terrain Detail", menu=terrain_detail_menu)
        
        terrain_details = [
            ("Low (100 points)", "100"),
            ("Medium (200 points)", "200"),
            ("High (300 points)", "300"),
            ("Ultra (500 points) ★", "500"),
            ("Maximum (1000 points)", "1000"),
        ]
        
        for label, value in terrain_details:
            terrain_detail_menu.add_radiobutton(
                label=label,
                variable=self.vars['terrain_detail_var'],
                value=value,
                command=lambda v=value: self.callbacks['on_terrain_detail_change'](v)
            )
        
        terrain_detail_menu.add_separator()
        terrain_detail_menu.add_command(
            label="Custom...",
            command=self.callbacks['on_custom_terrain_detail']
        )
