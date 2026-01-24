"""
Export Handler Module
=====================
Handles KML export, image exports at multiple zoom levels, and report generation.
"""

import os
import json
import simplekml
from datetime import datetime
from tkinter import messagebox, filedialog


class ExportHandler:
    """Handles all export functionality for Cellfire RF Studio"""

    def __init__(self, config_manager):
        """Initialize export handler

        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.export_dir = os.path.join(os.getcwd(), 'exports')

        # Create exports directory if it doesn't exist
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)

    def export_kml(self, coverage_data=None):
        """Export coverage plot as KML file

        Args:
            coverage_data: Tuple of (x_grid, y_grid, rx_power_grid) from propagation calculation
        """
        try:
            # Get current configuration
            tx_lat = self.config.get('tx_lat', 0)
            tx_lon = self.config.get('tx_lon', 0)
            frequency = self.config.get('frequency', 0)
            erp = self.config.get('erp', 0)
            max_distance = self.config.get('max_distance', 50)
            signal_threshold = self.config.get('signal_threshold', -110)

            # Create KML object
            kml = simplekml.Kml()
            kml.document.name = f"RF Coverage - {frequency} MHz"

            # Add transmitter location as a placemark
            pnt = kml.newpoint(name="Transmitter")
            pnt.coords = [(tx_lon, tx_lat)]
            pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/ranger_station.png'
            pnt.style.iconstyle.scale = 1.5

            # Add description with station details
            pnt.description = f"""
            <![CDATA[
            <b>Frequency:</b> {frequency} MHz<br>
            <b>ERP:</b> {erp} dBW<br>
            <b>Coverage Radius:</b> {max_distance} km<br>
            <b>Location:</b> {tx_lat:.6f}, {tx_lon:.6f}
            ]]>
            """

            # Add coverage overlay if coverage data is provided
            if coverage_data is not None:
                x_grid, y_grid, rx_power_grid = coverage_data

                print("Generating coverage overlay image...")

                # Create ground overlay with coverage image
                overlay_path = self._create_coverage_overlay(x_grid, y_grid, rx_power_grid,
                                                             tx_lat, tx_lon, max_distance,
                                                             signal_threshold)

                if overlay_path:
                    # Calculate overlay bounds
                    earth_radius = 6371.0  # km

                    # North/South/East/West boundaries
                    north = tx_lat + (max_distance / earth_radius) * (180 / 3.14159)
                    south = tx_lat - (max_distance / earth_radius) * (180 / 3.14159)
                    east = tx_lon + (max_distance / earth_radius) * (180 / 3.14159) / \
                           (3.14159 * tx_lat / 180)
                    west = tx_lon - (max_distance / earth_radius) * (180 / 3.14159) / \
                           (3.14159 * tx_lat / 180)

                    # Create ground overlay
                    ground = kml.newgroundoverlay(name="RF Coverage")
                    ground.icon.href = overlay_path
                    ground.latlonbox.north = north
                    ground.latlonbox.south = south
                    ground.latlonbox.east = east
                    ground.latlonbox.west = west
                    ground.latlonbox.rotation = 0

                    print(f"  Ground overlay created: {overlay_path}")
            else:
                # Fallback: Add simple coverage circle if no coverage data
                messagebox.showwarning("No Coverage Data",
                                     "No propagation data available. Exporting simple coverage boundary.\n"
                                     "Calculate coverage first for detailed signal strength contours.")

                pol = kml.newpolygon(name=f"{max_distance} km Boundary")
                pol.outerboundaryis = self._generate_circle_coords(tx_lat, tx_lon, max_distance)
                pol.style.polystyle.color = simplekml.Color.changealphaint(100, simplekml.Color.blue)
                pol.style.linestyle.color = simplekml.Color.blue
                pol.style.linestyle.width = 2

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"CellfireRF_Coverage_{timestamp}.kml"
            filepath = os.path.join(self.export_dir, filename)

            # Ask user where to save
            save_path = filedialog.asksaveasfilename(
                defaultextension=".kml",
                filetypes=[("KML files", "*.kml"), ("All files", "*.*")],
                initialdir=self.export_dir,
                initialfile=filename,
                title="Export KML"
            )

            if save_path:
                kml.save(save_path)
                messagebox.showinfo("Export Successful",
                                  f"KML file exported to:\n{save_path}")
                return save_path

        except Exception as e:
            messagebox.showerror("Export Error",
                               f"Failed to export KML:\n{str(e)}")
            return None

    def _generate_contours(self, x_grid, y_grid, rx_power_grid, tx_lat, tx_lon, signal_level):
        """Generate contour polygons for a specific signal level

        Args:
            x_grid: X coordinate grid (km from transmitter)
            y_grid: Y coordinate grid (km from transmitter)
            rx_power_grid: Received power grid (dBm)
            tx_lat: Transmitter latitude
            tx_lon: Transmitter longitude
            signal_level: Signal level threshold (dBm)

        Returns:
            List of contour polygons (each is a list of (lon, lat) tuples)
        """
        import numpy as np

        contours = []

        try:
            import matplotlib.pyplot as plt

            # Check if any signal exceeds this level
            max_signal = np.max(rx_power_grid)
            min_signal = np.min(rx_power_grid)
            print(f"    Signal range: {min_signal:.1f} to {max_signal:.1f} dBm")

            if max_signal < signal_level:
                print(f"    Max signal ({max_signal:.1f} dBm) < threshold ({signal_level} dBm), no contours")
                return []

            # Use matplotlib's contour finding
            fig, ax = plt.subplots(figsize=(10, 10))
            cs = ax.contour(x_grid, y_grid, rx_power_grid, levels=[signal_level])
            plt.close(fig)

            # Get paths directly from QuadContourSet (matplotlib 3.8+)
            all_paths = []
            for path_collection in cs.get_paths():
                all_paths.append(path_collection)

            print(f"    Matplotlib found {len(all_paths)} path(s)")

            # Extract contour coordinates from paths
            for path in all_paths:
                vertices = path.vertices
                print(f"      Path has {len(vertices)} vertices")

                if len(vertices) > 3:  # Need at least 3 points for a polygon
                    # Apply aggressive simplification for smooth contours
                    # Use Ramer-Douglas-Peucker-style decimation
                    from matplotlib.path import Path

                    # Start with aggressive decimation - keep every 50th point for very detailed contours
                    if len(vertices) > 5000:
                        simplification_factor = len(vertices) // 100  # Max ~100 points
                    elif len(vertices) > 1000:
                        simplification_factor = len(vertices) // 200  # Max ~200 points
                    else:
                        simplification_factor = max(1, len(vertices) // 500)  # Max ~500 points

                    simplified_vertices = vertices[::simplification_factor]

                    # Ensure we have first and last points
                    if len(simplified_vertices) > 0:
                        if not np.array_equal(simplified_vertices[0], vertices[0]):
                            simplified_vertices = np.vstack([vertices[0], simplified_vertices])
                        if not np.array_equal(simplified_vertices[-1], vertices[-1]):
                            simplified_vertices = np.vstack([simplified_vertices, vertices[-1]])

                    # Convert from km offset to lat/lon
                    coords = []
                    for x_km, y_km in simplified_vertices:
                        lat, lon = self._km_to_latlon(x_km, y_km, tx_lat, tx_lon)
                        coords.append((lon, lat))

                    # Close the polygon if not already closed
                    if len(coords) > 1 and coords[0] != coords[-1]:
                        coords.append(coords[0])

                    if len(coords) > 3:
                        contours.append(coords)
                        print(f"      Added contour with {len(coords)} points (simplified from {len(vertices)})")
                else:
                    print(f"      Skipped path (too few vertices)")

        except Exception as e:
            print(f"    Contour generation error: {e}")
            import traceback
            traceback.print_exc()

        return contours

    def _km_to_latlon(self, x_km, y_km, origin_lat, origin_lon):
        """Convert km offset to lat/lon

        Args:
            x_km: East offset in km
            y_km: North offset in km
            origin_lat: Origin latitude
            origin_lon: Origin longitude

        Returns:
            Tuple of (lat, lon)
        """
        import math

        earth_radius = 6371.0  # km

        # Convert offsets to lat/lon
        lat = origin_lat + (y_km / earth_radius) * (180 / math.pi)
        lon = origin_lon + (x_km / earth_radius) * (180 / math.pi) / math.cos(origin_lat * math.pi / 180)

        return lat, lon

    def _generate_circle_coords(self, lat, lon, radius_km, num_points=64):
        """Generate coordinates for a circle

        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Radius in kilometers
            num_points: Number of points to generate

        Returns:
            List of (lon, lat) tuples
        """
        import math

        coords = []
        earth_radius = 6371.0  # km

        for i in range(num_points + 1):
            angle = (2 * math.pi * i) / num_points

            # Calculate offset
            dx = radius_km * math.cos(angle)
            dy = radius_km * math.sin(angle)

            # Convert to lat/lon
            new_lat = lat + (dy / earth_radius) * (180 / math.pi)
            new_lon = lon + (dx / earth_radius) * (180 / math.pi) / math.cos(lat * math.pi / 180)

            coords.append((new_lon, new_lat))

        return coords

    def export_images_all_zoom(self, render_callback):
        """Export coverage images at multiple zoom levels

        Args:
            render_callback: Function to call to render at different zoom levels
        """
        try:
            # Define zoom levels to export
            zoom_levels = [9, 10, 11, 12, 13]

            # Ask user for output directory
            output_dir = filedialog.askdirectory(
                initialdir=self.export_dir,
                title="Select Output Directory for Image Export"
            )

            if not output_dir:
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_folder = os.path.join(output_dir, f"Coverage_Export_{timestamp}")
            os.makedirs(export_folder, exist_ok=True)

            exported_files = []

            # Export each zoom level
            for zoom in zoom_levels:
                filename = f"Coverage_Zoom{zoom}_{timestamp}.jpg"
                filepath = os.path.join(export_folder, filename)

                # Call render callback with zoom level and output path
                if render_callback:
                    render_callback(zoom, filepath)
                    exported_files.append(filepath)

            messagebox.showinfo("Export Successful",
                              f"Exported {len(exported_files)} images to:\n{export_folder}")

            return exported_files

        except Exception as e:
            messagebox.showerror("Export Error",
                               f"Failed to export images:\n{str(e)}")
            return None
