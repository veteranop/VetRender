"""
Toolbar Module - ENHANCED
==========================
Top toolbar with transmitter location, zoom, quality controls, transparency slider, and action buttons.

NEW FEATURES:
✅ Transparency slider for coverage overlay (0-100%)
"""

import tkinter as tk
from tkinter import ttk


class Toolbar:
    """Main toolbar with controls and action buttons"""
    
    def __init__(self, parent, callbacks):
        """Initialize toolbar
        
        Args:
            parent: Parent tkinter widget
            callbacks: Dictionary of callback functions:
                - on_zoom_change: Called when zoom level changes
                - on_refresh_map: Called when refresh map clicked
                - on_quality_change: Called when quality preset changes
                - on_calculate: Called when calculate button clicked
                - on_new_project: Called when new project clicked
                - on_save_project: Called when save project clicked
                - on_load_project: Called when load project clicked
                - on_transparency_change: Called when transparency slider moves (NEW!)
        """
        self.frame = ttk.Frame(parent, padding="5")
        self.callbacks = callbacks
        
        # Variables
        self.zoom_var = tk.StringVar()
        self.quality_var = tk.StringVar()
        self.propagation_model_var = tk.StringVar(value='default')  # Propagation model selector
        self.azimuth_var = tk.StringVar()
        self.dist_points_var = tk.StringVar()
        self.transparency_var = tk.DoubleVar(value=0.3)  # 🔥 NEW: Default 30% transparency
        self.status_var = tk.StringVar(value="Ready - Right-click on map for options")
        
        # Custom controls frame (shown/hidden based on quality)
        self.custom_frame = None
        
        self.setup_widgets()
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def setup_widgets(self):
        """Create all toolbar widgets"""
        # Transmitter location
        ttk.Label(self.frame, text="Transmitter:").pack(side=tk.LEFT, padx=5)
        self.tx_label = ttk.Label(self.frame, text="Lat: 0.0000, Lon: 0.0000")
        self.tx_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(self.frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Zoom control
        ttk.Label(self.frame, text="Zoom:").pack(side=tk.LEFT, padx=5)
        zoom_combo = ttk.Combobox(self.frame, textvariable=self.zoom_var, width=5,
                                  values=['8', '9', '10', '11', '12', '13', '14', '15', '16'])
        zoom_combo.pack(side=tk.LEFT, padx=5)
        zoom_combo.bind('<<ComboboxSelected>>', 
                       lambda e: self.callbacks['on_zoom_change']())
        
        ttk.Button(self.frame, text="Refresh Map", 
                  command=self.callbacks['on_refresh_map']).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(self.frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Quality preset
        ttk.Label(self.frame, text="Quality:").pack(side=tk.LEFT, padx=(10, 5))
        quality_combo = ttk.Combobox(self.frame, textvariable=self.quality_var, width=10,
                                     values=['Low', 'Medium', 'High', 'Ultra', 'Custom'],
                                     state='readonly')
        quality_combo.pack(side=tk.LEFT, padx=2)
        quality_combo.bind('<<ComboboxSelected>>', 
                          lambda e: self.callbacks['on_quality_change']())
        
        # =================================================================================
        # PROPAGATION MODEL SELECTOR
        # =================================================================================
        # Dropdown to choose between default and Longley-Rice models
        # ROLLBACK: Remove this block and propagation_model_var to revert
        # =================================================================================
        ttk.Label(self.frame, text="Model:").pack(side=tk.LEFT, padx=(10, 5))
        model_combo = ttk.Combobox(self.frame, textvariable=self.propagation_model_var, width=12,
                                   values=['default', 'longley_rice'],
                                   state='readonly')
        model_combo.pack(side=tk.LEFT, padx=2)
        # Note: No callback needed - model is read when calculating
        # =================================================================================
        # END PROPAGATION MODEL SELECTOR
        # =================================================================================

        # Custom controls (hidden by default)
        self.custom_frame = ttk.Frame(self.frame)
        ttk.Label(self.custom_frame, text="Az:").pack(side=tk.LEFT, padx=(5, 2))
        ttk.Entry(self.custom_frame, textvariable=self.azimuth_var, width=4).pack(side=tk.LEFT, padx=2)
        ttk.Label(self.custom_frame, text="Pts:").pack(side=tk.LEFT, padx=(5, 2))
        ttk.Entry(self.custom_frame, textvariable=self.dist_points_var, width=4).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(self.frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # 🔥 NEW: Transparency slider
        ttk.Label(self.frame, text="Overlay:").pack(side=tk.LEFT, padx=5)
        self.transparency_slider = ttk.Scale(
            self.frame, from_=0.0, to=1.0,
            variable=self.transparency_var,
            orient='horizontal', length=120,
            command=self._on_transparency_change
        )
        self.transparency_slider.pack(side=tk.LEFT, padx=5)
        self.transparency_label = ttk.Label(self.frame, text="30%", width=4)
        self.transparency_label.pack(side=tk.LEFT, padx=2)
        ttk.Button(self.frame, text="Apply",
                  command=self._apply_transparency).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.frame, text="Reset",
                  command=self._reset_transparency).pack(side=tk.LEFT, padx=2)

        ttk.Separator(self.frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Project buttons
        ttk.Button(self.frame, text="New",
                  command=self.callbacks['on_new_project']).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.frame, text="Save",
                  command=self.callbacks['on_save_project']).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.frame, text="Load",
                  command=self.callbacks['on_load_project']).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(self.frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Calculate button - use accent style for primary action
        ttk.Button(self.frame, text="Calculate Coverage",
                  command=self.callbacks['on_calculate'],
                  style='Accent.TButton').pack(side=tk.LEFT, padx=10)
        
        ttk.Separator(self.frame, orient='vertical').pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Live probe checkbox - use ttk for consistent theming
        self.live_probe_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self.frame, text="Live Probe", variable=self.live_probe_var,
                       command=self._toggle_live_probe).pack(side=tk.LEFT, padx=5)

        # Signal level display - use ttk for consistent theming
        self.signal_var = tk.StringVar(value="")
        ttk.Label(self.frame, textvariable=self.signal_var, width=15).pack(side=tk.LEFT, padx=5)

        # Status label
        ttk.Label(self.frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
    
    def _on_transparency_change(self, value):
        """Handle transparency slider change (internal)"""
        percent = int(float(value) * 100)
        self.transparency_label.config(text=f"{percent}%")

        # Call callback if available (disabled to prevent map resizing)
        # if 'on_transparency_change' in self.callbacks:
        #     self.callbacks['on_transparency_change']()

    def _apply_transparency(self):
        """Apply current transparency setting"""
        if 'on_transparency_change' in self.callbacks:
            self.callbacks['on_transparency_change']()

    def _reset_transparency(self):
        """Reset transparency to default 30% (doesn't apply automatically)"""
        self.transparency_var.set(0.3)
        self.transparency_label.config(text="30%")
        # Note: Doesn't automatically apply - use Apply button

    def _toggle_live_probe(self):
        """Toggle live probe mode"""
        if 'on_toggle_live_probe' in self.callbacks:
            self.callbacks['on_toggle_live_probe']()

    def get_transparency(self):
        """Get current transparency value (0.0 to 1.0)
        
        Returns:
            float: Transparency value
        """
        return self.transparency_var.get()
    
    def set_transparency(self, value):
        """Set transparency value
        
        Args:
            value: Transparency (0.0 to 1.0)
        """
        self.transparency_var.set(value)
        percent = int(value * 100)
        self.transparency_label.config(text=f"{percent}%")
    
    def update_location(self, lat, lon):
        """Update transmitter location display
        
        Args:
            lat: Latitude
            lon: Longitude
        """
        self.tx_label.config(text=f"Lat: {lat:.4f}, Lon: {lon:.4f}")
    
    def set_zoom(self, zoom):
        """Set zoom level
        
        Args:
            zoom: Zoom level (10-16)
        """
        self.zoom_var.set(str(zoom))
    
    def get_zoom(self):
        """Get current zoom level

        Returns:
            int: Zoom level
        """
        try:
            return int(self.zoom_var.get())
        except ValueError:
            return 13

    def get_propagation_model(self):
        """Get selected propagation model

        Returns:
            str: 'default' or 'longley_rice'
        """
        return self.propagation_model_var.get()

    def set_quality(self, quality):
        """Set quality preset
        
        Args:
            quality: Quality preset name
        """
        self.quality_var.set(quality)
    
    def get_quality(self):
        """Get current quality preset
        
        Returns:
            str: Quality preset name
        """
        return self.quality_var.get()
    
    def show_custom_controls(self):
        """Show custom azimuth/distance controls"""
        self.custom_frame.pack(side=tk.LEFT, padx=(5, 0))
    
    def hide_custom_controls(self):
        """Hide custom azimuth/distance controls"""
        try:
            self.custom_frame.pack_forget()
        except:
            pass
    
    def set_custom_values(self, azimuth, dist_points):
        """Set custom azimuth and distance point values
        
        Args:
            azimuth: Azimuth count
            dist_points: Distance points
        """
        self.azimuth_var.set(str(azimuth))
        self.dist_points_var.set(str(dist_points))
    
    def get_custom_values(self):
        """Get custom azimuth and distance point values
        
        Returns:
            Tuple of (azimuth, dist_points)
        """
        try:
            azimuth = int(self.azimuth_var.get())
            dist_points = int(self.dist_points_var.get())
            return azimuth, dist_points
        except ValueError:
            return 360, 500
    
    def set_status(self, message):
        """Set status message
        
        Args:
            message: Status message text
        """
        self.status_var.set(message)
    
    def get_status(self):
        """Get current status message
        
        Returns:
            str: Status message
        """
        return self.status_var.get()
