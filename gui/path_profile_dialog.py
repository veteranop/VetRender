"""
Path Profile Dialog - Shows terrain elevation profile between TX and probed point.
Displays line-of-sight path with Fresnel zone visualization.
"""
import tkinter as tk
from tkinter import ttk
import numpy as np
import math

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from models.terrain import TerrainHandler


class PathProfileDialog:
    """Dialog showing terrain elevation profile from TX to a probed point."""

    def __init__(self, parent, tx_lat, tx_lon, tx_height, rx_lat, rx_lon, rx_height,
                 signal_strength, frequency_mhz):
        """
        Initialize path profile dialog.

        Args:
            parent: Parent tkinter window
            tx_lat, tx_lon: Transmitter coordinates
            tx_height: Transmitter antenna height (meters AGL)
            rx_lat, rx_lon: Receiver/probe point coordinates
            rx_height: Receiver height (meters AGL)
            signal_strength: Signal at probe point (dBm)
            frequency_mhz: Operating frequency in MHz
        """
        self.parent = parent
        self.tx_lat = tx_lat
        self.tx_lon = tx_lon
        self.tx_height = tx_height
        self.rx_lat = rx_lat
        self.rx_lon = rx_lon
        self.rx_height = rx_height
        self.signal_strength = signal_strength
        self.frequency_mhz = frequency_mhz

        # Calculate path distance
        self.distance_km = self._haversine_distance(tx_lat, tx_lon, rx_lat, rx_lon)
        self.azimuth = self._calculate_azimuth(tx_lat, tx_lon, rx_lat, rx_lon)

        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Path Profile Analysis")
        self.dialog.geometry("900x600")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self._create_widgets()
        self._plot_profile()

        # Center dialog
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Create dialog UI components."""
        # Info panel at top
        info_frame = ttk.Frame(self.dialog, padding=10)
        info_frame.pack(fill=tk.X)

        # Left info
        left_info = ttk.Frame(info_frame)
        left_info.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Label(left_info, text="Path Profile", font=('Arial', 14, 'bold')).pack(anchor=tk.W)
        ttk.Label(left_info, text=f"TX: {self.tx_lat:.5f}, {self.tx_lon:.5f}  |  "
                                  f"RX: {self.rx_lat:.5f}, {self.rx_lon:.5f}").pack(anchor=tk.W)

        # Right info
        right_info = ttk.Frame(info_frame)
        right_info.pack(side=tk.RIGHT)

        # Signal quality indicator
        quality, color = self._get_signal_quality(self.signal_strength)

        stats_text = f"Distance: {self.distance_km:.2f} km  |  Azimuth: {self.azimuth:.1f}\u00b0  |  "
        stats_text += f"Signal: {self.signal_strength:.1f} dBm ({quality})"

        stats_label = ttk.Label(right_info, text=stats_text, font=('Arial', 10))
        stats_label.pack(anchor=tk.E)

        # Matplotlib figure for profile plot
        self.fig = Figure(figsize=(8.5, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)

        canvas_frame = ttk.Frame(self.dialog)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Fresnel zone info panel
        fresnel_frame = ttk.LabelFrame(self.dialog, text="Fresnel Zone Analysis", padding=10)
        fresnel_frame.pack(fill=tk.X, padx=10, pady=5)

        self.fresnel_info = ttk.Label(fresnel_frame, text="Calculating...")
        self.fresnel_info.pack(anchor=tk.W)

        # Buttons
        btn_frame = ttk.Frame(self.dialog, padding=10)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="Close", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)

    def _plot_profile(self):
        """Generate and plot the terrain profile."""
        # Sample terrain along the path
        num_samples = max(100, int(self.distance_km * 10))  # ~10 samples per km, min 100

        # Generate sample points along path
        lats = np.linspace(self.tx_lat, self.rx_lat, num_samples)
        lons = np.linspace(self.tx_lon, self.rx_lon, num_samples)
        distances = np.linspace(0, self.distance_km, num_samples)

        # Get elevations for all points using static TerrainHandler
        lat_lon_pairs = list(zip(lats, lons))
        elevations = TerrainHandler.get_elevations_batch(lat_lon_pairs)
        elevations = np.array(elevations)

        # Handle any None values
        valid_mask = ~np.isnan(elevations.astype(float))
        if not valid_mask.all():
            # Interpolate missing values
            valid_indices = np.where(valid_mask)[0]
            invalid_indices = np.where(~valid_mask)[0]
            if len(valid_indices) > 1:
                elevations[invalid_indices] = np.interp(
                    invalid_indices, valid_indices, elevations[valid_indices]
                )

        tx_ground_elev = elevations[0]
        rx_ground_elev = elevations[-1]

        # Calculate antenna heights above sea level
        tx_antenna_asl = tx_ground_elev + self.tx_height
        rx_antenna_asl = rx_ground_elev + self.rx_height

        # Calculate line of sight
        los_elevations = np.linspace(tx_antenna_asl, rx_antenna_asl, num_samples)

        # Calculate Fresnel zone radii at each point
        fresnel_radii = self._calculate_fresnel_zone(distances, self.distance_km, self.frequency_mhz)

        # Upper and lower Fresnel boundaries
        fresnel_upper = los_elevations + fresnel_radii
        fresnel_lower = los_elevations - fresnel_radii

        # Check for Fresnel zone obstruction
        clearance = fresnel_lower - elevations
        min_clearance = np.min(clearance)
        min_clearance_dist = distances[np.argmin(clearance)]

        # Calculate 60% Fresnel clearance (typical requirement)
        fresnel_60_lower = los_elevations - (0.6 * fresnel_radii)
        clearance_60 = fresnel_60_lower - elevations
        min_clearance_60 = np.min(clearance_60)

        # Plot terrain profile
        self.ax.clear()

        # Fill terrain
        self.ax.fill_between(distances, 0, elevations, color='#8B4513', alpha=0.6, label='Terrain')
        self.ax.plot(distances, elevations, color='#5D3A1A', linewidth=1.5)

        # Plot Fresnel zone (first Fresnel zone)
        self.ax.fill_between(distances, fresnel_lower, fresnel_upper,
                            color='orange', alpha=0.2, label='1st Fresnel Zone')
        self.ax.plot(distances, fresnel_upper, 'orange', linestyle='--', linewidth=1, alpha=0.7)
        self.ax.plot(distances, fresnel_lower, 'orange', linestyle='--', linewidth=1, alpha=0.7)

        # Plot 60% Fresnel boundary
        self.ax.plot(distances, fresnel_60_lower, 'orange', linestyle=':', linewidth=1.5, alpha=0.9,
                    label='60% Fresnel Zone')

        # Plot line of sight
        self.ax.plot(distances, los_elevations, 'g-', linewidth=2, label='Line of Sight')

        # Mark TX and RX antennas
        self.ax.plot(0, tx_antenna_asl, 'r^', markersize=12, label='TX Antenna', zorder=5)
        self.ax.plot(self.distance_km, rx_antenna_asl, 'b^', markersize=10, label='RX Point', zorder=5)

        # Mark obstruction point if any
        if min_clearance < 0:
            obstruction_idx = np.argmin(clearance)
            self.ax.plot(distances[obstruction_idx], elevations[obstruction_idx],
                        'rx', markersize=15, markeredgewidth=3, label='Obstruction', zorder=6)

        # Labels and formatting
        self.ax.set_xlabel('Distance (km)', fontsize=10)
        self.ax.set_ylabel('Elevation (m ASL)', fontsize=10)
        self.ax.set_title(f'Terrain Profile: {self.distance_km:.2f} km @ {self.azimuth:.1f}\u00b0', fontsize=12)

        # Set y-axis limits with some padding
        min_elev = min(np.min(elevations), np.min(fresnel_lower)) - 20
        max_elev = max(np.max(elevations), tx_antenna_asl, rx_antenna_asl, np.max(fresnel_upper)) + 20
        self.ax.set_ylim(min_elev, max_elev)
        self.ax.set_xlim(0, self.distance_km)

        # Grid
        self.ax.grid(True, alpha=0.3)

        # Legend
        self.ax.legend(loc='upper right', fontsize=8)

        self.fig.tight_layout()
        self.canvas.draw()

        # Update Fresnel info
        self._update_fresnel_info(min_clearance, min_clearance_60, min_clearance_dist, fresnel_radii)

    def _calculate_fresnel_zone(self, distances, total_distance, freq_mhz):
        """
        Calculate first Fresnel zone radius at each point along path.

        Formula: r = sqrt(n * lambda * d1 * d2 / D)
        where n=1 (first Fresnel zone), lambda = c/f, d1 and d2 are distances
        from each end, D is total distance.
        """
        # Wavelength in meters
        wavelength = 299.792458 / freq_mhz  # c in km/s, freq in MHz -> wavelength in m

        d1 = distances  # Distance from TX (km)
        d2 = total_distance - distances  # Distance from RX (km)

        # Avoid division by zero at endpoints
        d1 = np.maximum(d1, 0.001)
        d2 = np.maximum(d2, 0.001)

        # Fresnel radius in meters (convert km to m for d1, d2)
        radii = np.sqrt(wavelength * (d1 * 1000) * (d2 * 1000) / (total_distance * 1000))

        return radii

    def _update_fresnel_info(self, min_clearance, min_clearance_60, min_clearance_dist, fresnel_radii):
        """Update Fresnel zone analysis text."""
        max_fresnel_radius = np.max(fresnel_radii)

        if min_clearance >= 0:
            if min_clearance_60 >= 0:
                status = "Clear LOS with good Fresnel clearance"
                status_detail = f"Minimum clearance: {min_clearance:.1f}m above terrain at {min_clearance_dist:.2f}km"
            else:
                status = "Clear LOS but partial Fresnel obstruction"
                status_detail = f"60% Fresnel zone obstructed by {abs(min_clearance_60):.1f}m at {min_clearance_dist:.2f}km"
        else:
            status = "Line of Sight OBSTRUCTED"
            status_detail = f"Obstruction of {abs(min_clearance):.1f}m at {min_clearance_dist:.2f}km from TX"

        info_text = f"{status}\n"
        info_text += f"{status_detail}\n"
        info_text += f"Max 1st Fresnel Zone radius: {max_fresnel_radius:.1f}m (at path midpoint)\n"
        info_text += f"Frequency: {self.frequency_mhz:.3f} MHz  |  Wavelength: {299.792458/self.frequency_mhz:.2f}m"

        self.fresnel_info.config(text=info_text)

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate great-circle distance between two points in km."""
        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    def _calculate_azimuth(self, lat1, lon1, lat2, lon2):
        """Calculate bearing/azimuth from point 1 to point 2 in degrees."""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon = math.radians(lon2 - lon1)

        x = math.sin(dlon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon)

        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360

    def _get_signal_quality(self, signal_dbm):
        """Get signal quality description and color."""
        if signal_dbm > -70:
            return "Excellent", "green"
        elif signal_dbm > -85:
            return "Good", "blue"
        elif signal_dbm > -95:
            return "Fair", "orange"
        elif signal_dbm > -110:
            return "Poor", "red"
        else:
            return "No Signal", "gray"
