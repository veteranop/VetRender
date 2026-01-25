"""
Debug logger for Cellfire RF Studio coordinate tracking
"""
import os
import datetime
from pathlib import Path

class DebugLogger:
    def __init__(self):
        # Create logs directory
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = self.log_dir / f"coordinate_debug_{timestamp}.log"

        # Logging enabled state (default: disabled to reduce noise)
        self._enabled = False

        # Write header (always, to indicate log file was created)
        self._write_to_file("="*80)
        self._write_to_file("Cellfire RF Studio Coordinate Debug Log")
        self._write_to_file(f"Started: {datetime.datetime.now()}")
        self._write_to_file("="*80)

    @property
    def enabled(self):
        """Check if logging is enabled"""
        return self._enabled

    @enabled.setter
    def enabled(self, value):
        """Enable or disable logging"""
        self._enabled = value
        status = "ENABLED" if value else "DISABLED"
        self._write_to_file(f">>> Debug logging {status} at {datetime.datetime.now()}")
        print(f"Debug logging {status}")

    def _write_to_file(self, message):
        """Write message to log file (always, regardless of enabled state)"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] {message}"
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")

    def log(self, message):
        """Write message to log file and print to console (only if enabled)"""
        if not self._enabled:
            return

        timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_line = f"[{timestamp}] {message}"

        # Write to file with UTF-8 encoding to handle special characters
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_line + "\n")

        # Also print to console
        print(log_line)

    def log_map_load(self, tx_lat, tx_lon, zoom, map_xtile, map_ytile, map_center_lat, map_center_lon):
        """Log map loading details"""
        self.log("")
        self.log("="*80)
        self.log("MAP LOADED")
        self.log("="*80)
        self.log(f"Requested center: Lat={tx_lat:.6f}, Lon={tx_lon:.6f}")
        self.log(f"Zoom level: {zoom}")
        self.log(f"Map tile (integer): X={map_xtile}, Y={map_ytile}")
        self.log(f"Map tile center represents: Lat={map_center_lat:.6f}, Lon={map_center_lon:.6f}")
        self.log(f"Offset from requested: ({tx_lat - map_center_lat:.6f}°, {tx_lon - map_center_lon:.6f}°)")
        self.log(f"Distance offset: {(tx_lat - map_center_lat) * 111:.2f} km N/S, {(tx_lon - map_center_lon) * 111:.2f} km E/W")
        self.log("="*80)

    def log_marker_position(self, tx_lat, tx_lon, tx_pixel_x, tx_pixel_y, img_center, img_size):
        """Log transmitter marker positioning"""
        self.log("")
        self.log("-"*80)
        self.log("TRANSMITTER MARKER POSITION")
        self.log("-"*80)
        self.log(f"TX coordinates: Lat={tx_lat:.6f}, Lon={tx_lon:.6f}")
        self.log(f"Marker drawn at pixel: ({tx_pixel_x:.2f}, {tx_pixel_y:.2f})")
        self.log(f"Image center: ({img_center}, {img_center})")
        self.log(f"Offset from center: ({tx_pixel_x - img_center:.2f}, {tx_pixel_y - img_center:.2f}) pixels")
        self.log(f"Image size: {img_size}x{img_size}")
        self.log("-"*80)

    def log_set_location(self, old_lat, old_lon, new_lat, new_lon):
        """Log location change"""
        self.log("")
        self.log("*"*80)
        self.log("SET TRANSMITTER LOCATION")
        self.log("*"*80)
        self.log(f"Old location: Lat={old_lat:.6f}, Lon={old_lon:.6f}")
        self.log(f"New location: Lat={new_lat:.6f}, Lon={new_lon:.6f}")
        self.log(f"Change: ({new_lat - old_lat:.6f}°, {new_lon - old_lon:.6f}°)")
        self.log("*"*80)

    def log_probe(self, click_x, click_y, probe_lat, probe_lon, tx_lat, tx_lon, distance_km, azimuth):
        """Log signal probe"""
        self.log("")
        self.log("#"*80)
        self.log("SIGNAL PROBE")
        self.log("#"*80)
        self.log(f"Click position: Pixel ({click_x:.1f}, {click_y:.1f})")
        self.log(f"Probe coordinates: Lat={probe_lat:.6f}, Lon={probe_lon:.6f}")
        self.log(f"TX coordinates: Lat={tx_lat:.6f}, Lon={tx_lon:.6f}")
        self.log(f"Distance from TX: {distance_km:.2f} km")
        self.log(f"Azimuth from TX: {azimuth:.1f}°")
        self.log(f"Coordinate difference: ({probe_lat - tx_lat:.6f}°, {probe_lon - tx_lon:.6f}°)")
        self.log("#"*80)

# Global logger instance
logger = None

def get_logger():
    """Get or create logger instance"""
    global logger
    if logger is None:
        logger = DebugLogger()
    return logger
