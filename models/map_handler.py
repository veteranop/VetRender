"""
Map tile fetching and coordinate conversions
"""
import numpy as np
from io import BytesIO
from urllib.request import urlopen, Request
from PIL import Image

class MapHandler:
    """Handles map tile fetching and display with caching support"""
    
    BASEMAPS = {
        'OpenStreetMap': {
            'url': 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            'attribution': 'OpenStreetMap'
        },
        'OpenTopoMap': {
            'url': 'https://tile.opentopomap.org/{z}/{x}/{y}.png',
            'attribution': 'OpenTopoMap'
        },
        'Esri WorldImagery': {
            'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            'attribution': 'Esri'
        },
        'Esri WorldTopo': {
            'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}',
            'attribution': 'Esri'
        },
        'Stamen Terrain': {
            'url': 'https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png',
            'attribution': 'Stamen Design'
        },
        'CartoDB Positron': {
            'url': 'https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
            'attribution': 'CartoDB'
        },
        'CartoDB Dark': {
            'url': 'https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png',
            'attribution': 'CartoDB'
        }
    }
    
    @staticmethod
    def deg2num(lat_deg, lon_deg, zoom):
        """Convert lat/lon to tile numbers"""
        lat_rad = np.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - np.log(np.tan(lat_rad) + (1 / np.cos(lat_rad))) / np.pi) / 2.0 * n)
        return xtile, ytile
    
    @staticmethod
    def num2deg(xtile, ytile, zoom):
        """Convert tile numbers to lat/lon"""
        n = 2.0 ** zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = np.arctan(np.sinh(np.pi * (1 - 2 * ytile / n)))
        lat_deg = np.degrees(lat_rad)
        return lat_deg, lon_deg
    
    @staticmethod
    def pixel_to_latlon(pixel_x, pixel_y, center_lat, center_lon, zoom, img_size):
        """Convert pixel coordinates to lat/lon"""
        center_xtile, center_ytile = MapHandler.deg2num(center_lat, center_lon, zoom)
        
        tile_size = 256
        tiles_offset_x = (pixel_x - img_size / 2) / tile_size
        tiles_offset_y = (pixel_y - img_size / 2) / tile_size
        
        new_xtile = center_xtile + tiles_offset_x
        new_ytile = center_ytile + tiles_offset_y
        
        lat, lon = MapHandler.num2deg(new_xtile, new_ytile, zoom)
        return lat, lon
    
    @staticmethod
    def get_map_tile(lat, lon, zoom=13, tile_size=3, basemap='OpenStreetMap', cache=None):
        """Fetch map tiles centered on lat/lon with optional caching
        
        Args:
            lat: Center latitude
            lon: Center longitude
            zoom: Zoom level (10-16)
            tile_size: Number of tiles in each direction (default 3 = 3x3 grid)
            basemap: Name of basemap from BASEMAPS dict
            cache: MapCache instance for caching (optional)
            
        Returns:
            Tuple of (composite_image, zoom, xtile, ytile)
        """
        try:
            if basemap not in MapHandler.BASEMAPS:
                basemap = 'OpenStreetMap'
            
            url_template = MapHandler.BASEMAPS[basemap]['url']
            
            xtile, ytile = MapHandler.deg2num(lat, lon, zoom)
            tile_range = tile_size // 2
            img_size = 256 * tile_size
            composite = Image.new('RGB', (img_size, img_size))
            
            print(f"Fetching {basemap} tiles...")
            
            tiles_cached = 0
            tiles_downloaded = 0
            
            for dx in range(-tile_range, tile_range + 1):
                for dy in range(-tile_range, tile_range + 1):
                    x = xtile + dx
                    y = ytile + dy
                    
                    # Try to load from cache first
                    tile_data = None
                    if cache:
                        tile_data = cache.load_tile(basemap, zoom, x, y)
                        if tile_data:
                            tiles_cached += 1
                    
                    # Download if not cached
                    if not tile_data:
                        url = url_template.replace('{z}', str(zoom)).replace('{x}', str(x)).replace('{y}', str(y))
                        req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})
                        
                        try:
                            with urlopen(req, timeout=5) as response:
                                tile_data = response.read()
                                tiles_downloaded += 1
                                
                                # Save to cache
                                if cache:
                                    cache.save_tile(basemap, zoom, x, y, tile_data)
                        except Exception as e:
                            print(f"Failed to fetch tile {x},{y}: {e}")
                            continue
                    
                    # Add tile to composite
                    if tile_data:
                        try:
                            tile_img = Image.open(BytesIO(tile_data))
                            px = (dx + tile_range) * 256
                            py = (dy + tile_range) * 256
                            composite.paste(tile_img, (px, py))
                        except Exception as e:
                            print(f"Error processing tile {x},{y}: {e}")
            
            if cache:
                print(f"Tiles: {tiles_cached} from cache, {tiles_downloaded} downloaded")
            
            return composite, zoom, xtile, ytile
        except Exception as e:
            print(f"Error fetching map: {e}")
            return None, zoom, 0, 0