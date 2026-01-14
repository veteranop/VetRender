"""
Test script to debug coordinate placement issue
"""
import numpy as np

# From screenshot
tx_lat = 43.713501
tx_lon = -113.010241
zoom = 10  # From screenshot

# Calculate exact fractional tile position of transmitter
lat_rad = np.radians(tx_lat)
n = 2.0 ** zoom
tx_xtile_exact = (tx_lon + 180.0) / 360.0 * n
tx_ytile_exact = (1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n

print(f"Transmitter coordinates: {tx_lat}, {tx_lon}")
print(f"Zoom level: {zoom}")
print(f"Exact tile position: ({tx_xtile_exact:.6f}, {tx_ytile_exact:.6f})")

# Integer tile (what get_map_tile returns)
map_xtile = int(tx_xtile_exact)
map_ytile = int(tx_ytile_exact)
print(f"Integer tile (map center): ({map_xtile}, {map_ytile})")

# Calculate offset
tile_offset_x = tx_xtile_exact - map_xtile
tile_offset_y = tx_ytile_exact - map_ytile
print(f"Tile offset: ({tile_offset_x:.6f}, {tile_offset_y:.6f})")

# Convert to pixel offset (256 pixels per tile)
tile_size = 256
pixel_offset_x = tile_offset_x * tile_size
pixel_offset_y = tile_offset_y * tile_size
print(f"Pixel offset from center: ({pixel_offset_x:.2f}, {pixel_offset_y:.2f})")

# Image size for 3x3 tile grid
img_size = 768
img_center = img_size // 2
tx_pixel_x = img_center + pixel_offset_x
tx_pixel_y = img_center + pixel_offset_y
print(f"TX marker position: ({tx_pixel_x:.2f}, {tx_pixel_y:.2f}) in {img_size}x{img_size} image")

# Now verify reverse: what lat/lon does the image center represent?
def num2deg(xtile, ytile, zoom):
    """Convert tile numbers to lat/lon"""
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * ytile / n)))
    lat_deg = np.degrees(lat_rad)
    return lat_deg, lon_deg

center_lat, center_lon = num2deg(map_xtile, map_ytile, zoom)
print(f"\nImage center represents: ({center_lat:.6f}, {center_lon:.6f})")
print(f"Difference from TX: ({tx_lat - center_lat:.6f}, {tx_lon - center_lon:.6f}) degrees")
print(f"Distance error: {(tx_lat - center_lat) * 111:.2f} km in latitude")
