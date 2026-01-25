"""
Info Panel Module
=================
Displays station information in a formatted text panel.
"""

import tkinter as tk
from tkinter import ttk
from models.propagation import PropagationModel


class InfoPanel:
    """Station information display panel"""

    # Dark theme colors
    COLORS = {
        'bg': '#252526',
        'fg': '#cccccc',
        'accent': '#4fc3f7',
        'border': '#3f3f46'
    }

    def __init__(self, parent):
        """Initialize info panel

        Args:
            parent: Parent tkinter widget
        """
        self.frame = ttk.Frame(parent, padding="10")

        # Title with modern styling
        title_label = ttk.Label(self.frame, text="Station Information",
                               style='Header.TLabel')
        title_label.pack(pady=(0, 10))

        # Info text display with dark theme colors
        self.info_text = tk.Text(self.frame, width=32, height=30, state='disabled',
                                bg=self.COLORS['bg'], fg=self.COLORS['fg'],
                                relief='flat', font=('Consolas', 9),
                                insertbackground=self.COLORS['fg'],
                                selectbackground='#0078d4',
                                selectforeground='#ffffff',
                                borderwidth=0, highlightthickness=1,
                                highlightbackground=self.COLORS['border'],
                                highlightcolor=self.COLORS['border'])
        self.info_text.pack(fill=tk.BOTH, expand=True)

        # Button frame at bottom
        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.pack(fill=tk.X, pady=(10, 0))
    
    def pack(self, **kwargs):
        """Pack the frame"""
        self.frame.pack(**kwargs)
    
    def add_button(self, text, command):
        """Add a button to the bottom of the panel
        
        Args:
            text: Button text
            command: Button command callback
            
        Returns:
            The created button
        """
        btn = ttk.Button(self.button_frame, text=text, command=command)
        btn.pack(fill=tk.X, pady=2)
        return btn
    
    def update(self, callsign, frequency, tx_mode, tx_type,
              tx_lat, tx_lon, height, rx_height, erp, tx_power, system_loss_db, system_gain_db, pattern_name,
              max_distance, signal_threshold, use_terrain, terrain_quality,
              antenna_details=None):
        """Update the information display
        
        Args:
            callsign: Station callsign
            frequency: Frequency (MHz)
            tx_mode: Transmission mode
            tx_type: Transmitter type
            tx_lat: Transmitter latitude
            tx_lon: Transmitter longitude
            height: Antenna height AGL (m)
            erp: ERP (dBm) - legacy, calculated from tx_power
            tx_power: Transmitter output power (dBm)
            system_loss_db: System loss (dB)
            system_gain_db: System gain (dB)
            pattern_name: Antenna pattern name
            max_distance: Maximum coverage distance (km)
            signal_threshold: Signal threshold (dBm)
            use_terrain: Whether terrain is enabled
            terrain_quality: Terrain quality setting
            antenna_details: Optional dict with manufacturer, part_number, gain, band, etc.
        """
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)

        # Calculate ERP from transmitter power + system gain/loss (antenna gain already included in system_gain_db)
        calculated_erp = tx_power + system_gain_db - system_loss_db
        if antenna_details:
            antenna_gain = antenna_details.get('gain', 0.0)
        calculated_erp = tx_power + system_gain_db - system_loss_db
        eirp = calculated_erp  # EIRP equals ERP when antenna gain is properly accounted for
        
        # Build antenna section with details if available
        antenna_section = f"Antenna:      {pattern_name}\n"
        if antenna_details:
            antenna_section += f"Manufacturer: {antenna_details.get('manufacturer', 'Unknown')}\n"
            antenna_section += f"Part Number:  {antenna_details.get('part_number', 'N/A')}\n"
            antenna_section += f"Gain:         {antenna_details.get('gain', 0)} dBi\n"
            antenna_section += f"Band:         {antenna_details.get('band', 'N/A')}\n"
            freq_range = antenna_details.get('frequency_range', 'N/A')
            if freq_range != 'N/A':
                antenna_section += f"Freq Range:   {freq_range}\n"
            ant_type = antenna_details.get('type', 'N/A')
            if ant_type != 'N/A':
                antenna_section += f"Type:         {ant_type}"
        
        info = f"""
╔═══════════════════════════════╗
║      STATION DETAILS          ║
╚═══════════════════════════════╝

Callsign:     {callsign}
Frequency:    {frequency} MHz
Tx Mode:      {tx_mode}
Tx Type:      {tx_type}

╔═══════════════════════════════╗
║      LOCATION                 ║
╚═══════════════════════════════╝

Latitude:     {tx_lat:.6f}°
Longitude:    {tx_lon:.6f}°
Height AGL:   {height} m
Rx Height:    {rx_height} m

╔═══════════════════════════════╗
║      POWER & ANTENNA          ║
╚═══════════════════════════════╝

Tx Power:     {tx_power} dBm ({10**((tx_power-30)/10):.1f} W)
ERP:          {calculated_erp:.2f} dBm ({10**((calculated_erp-30)/10):.1f} W)

{antenna_section}

╔═══════════════════════════════╗
║      COVERAGE SETTINGS        ║
╚═══════════════════════════════╝

Max Range:    {max_distance} km
Min Signal:   {signal_threshold} dBm
Terrain:      {'Enabled' if use_terrain else 'Disabled'}
Quality:      {terrain_quality}
"""
        
        self.info_text.insert('1.0', info)
        self.info_text.config(state='disabled')
