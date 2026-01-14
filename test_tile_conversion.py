"""
Debug script to test coordinate to tile conversion
"""
import numpy as np

def deg2num(lat_deg, lon_deg, zoom):
    """Convert lat/lon to tile numbers"""
    lat_rad = np.radians(lat_deg)
    n = 2.0 ** zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n)
    return xtile, ytile

def num2deg(xtile, ytile, zoom):
    """Convert tile numbers to lat/lon"""
    n = 2.0 ** zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * ytile / n)))
    lat_deg = np.degrees(lat_rad)
    return lat_deg, lon_deg

# Your coordinates from the screenshot
tx_lat = 43.713501
tx_lon = -113.010241
zoom = 10

print("="*60)
print("COORDINATE TO TILE CONVERSION TEST")
print("="*60)
print(f"\nInput coordinates:")
print(f"  Latitude:  {tx_lat}")
print(f"  Longitude: {tx_lon}")
print(f"  Zoom:      {zoom}")

# Convert to tile
xtile, ytile = deg2num(tx_lat, tx_lon, zoom)
print(f"\nInteger tile position:")
print(f"  X tile: {xtile}")
print(f"  Y tile: {ytile}")

# Convert back to see what the tile center represents
center_lat, center_lon = num2deg(xtile, ytile, zoom)
print(f"\nTile center represents:")
print(f"  Latitude:  {center_lat:.6f}")
print(f"  Longitude: {center_lon:.6f}")

# Calculate the difference
diff_lat = tx_lat - center_lat
diff_lon = tx_lon - center_lon
print(f"\nDifference (TX - Tile center):")
print(f"  Latitude:  {diff_lat:.6f}° ({diff_lat * 111:.2f} km)")
print(f"  Longitude: {diff_lon:.6f}° ({diff_lon * 111 * np.cos(np.radians(tx_lat)):.2f} km)")

# Calculate exact fractional tile position
lat_rad = np.radians(tx_lat)
n = 2.0 ** zoom
tx_xtile_exact = (tx_lon + 180.0) / 360.0 * n
tx_ytile_exact = (1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n

print(f"\nExact fractional tile position:")
print(f"  X tile: {tx_xtile_exact:.6f}")
print(f"  Y tile: {tx_ytile_exact:.6f}")

# Fractional part
frac_x = tx_xtile_exact - xtile
frac_y = tx_ytile_exact - ytile
print(f"\nFractional offset within tile:")
print(f"  X: {frac_x:.6f} tiles ({frac_x * 256:.2f} pixels)")
print(f"  Y: {frac_y:.6f} tiles ({frac_y * 256:.2f} pixels)")

# For 3x3 tile grid (768x768 pixels)
img_size = 768
img_center = img_size // 2
tx_pixel_x = img_center + frac_x * 256
tx_pixel_y = img_center + frac_y * 256

print(f"\nTransmitter marker position in 768x768 image:")
print(f"  X: {tx_pixel_x:.2f} pixels (center is {img_center})")
print(f"  Y: {tx_pixel_y:.2f} pixels (center is {img_center})")
print(f"  Offset from center: ({tx_pixel_x - img_center:.2f}, {tx_pixel_y - img_center:.2f}) pixels")

print("\n" + "="*60)
print("If marker is drawn at image center instead of calculated position,")
print(f"it will be off by {abs(tx_pixel_x - img_center):.0f} pixels in X")
print(f"and {abs(tx_pixel_y - img_center):.0f} pixels in Y")
print("="*60)
