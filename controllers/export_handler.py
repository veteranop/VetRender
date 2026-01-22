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
    """Handles all export functionality for VetRender"""

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
            coverage_data: Optional coverage data to export
        """
        try:
            # Get current configuration
            tx_lat = self.config.get('tx_lat', 0)
            tx_lon = self.config.get('tx_lon', 0)
            frequency = self.config.get('frequency', 0)
            erp = self.config.get('erp', 0)
            max_distance = self.config.get('max_distance', 50)

            # Create KML object
            kml = simplekml.Kml()

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

            # Add coverage circle (approximate boundary)
            pol = kml.newpolygon(name=f"{max_distance} km Coverage")
            pol.outerboundaryis = self._generate_circle_coords(tx_lat, tx_lon, max_distance)
            pol.style.polystyle.color = simplekml.Color.changealphaint(100, simplekml.Color.blue)
            pol.style.linestyle.color = simplekml.Color.blue
            pol.style.linestyle.width = 2

            # TODO: Add coverage contours if coverage_data is provided
            # This would require processing the coverage data to generate
            # polygons for different signal strength levels

            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"VetRender_Coverage_{timestamp}.kml"
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
