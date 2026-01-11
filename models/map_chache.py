"""
Map and terrain caching system for offline use
"""
import os
import pickle
import json
import hashlib
from pathlib import Path

class MapCache:
    """Handles local storage of map tiles and terrain data"""
    
    def __init__(self, cache_dir="map_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Subdirectories
        self.tiles_dir = self.cache_dir / "tiles"
        self.terrain_dir = self.cache_dir / "terrain"
        self.tiles_dir.mkdir(exist_ok=True)
        self.terrain_dir.mkdir(exist_ok=True)
        
    def _get_tile_path(self, basemap, zoom, x, y):
        """Get filesystem path for a tile"""
        tile_dir = self.tiles_dir / basemap / str(zoom) / str(x)
        tile_dir.mkdir(parents=True, exist_ok=True)
        return tile_dir / f"{y}.png"
    
    def _get_terrain_key(self, lat, lon, radius_km):
        """Generate unique key for terrain data"""
        # Round to avoid tiny differences
        lat_r = round(lat, 4)
        lon_r = round(lon, 4)
        radius_r = round(radius_km, 1)
        return f"{lat_r}_{lon_r}_{radius_r}"
    
    def _get_terrain_path(self, key):
        """Get filesystem path for terrain data"""
        return self.terrain_dir / f"{key}.pkl"
    
    def save_tile(self, basemap, zoom, x, y, tile_data):
        """Save a map tile to disk"""
        try:
            tile_path = self._get_tile_path(basemap, zoom, x, y)
            with open(tile_path, 'wb') as f:
                f.write(tile_data)
            return True
        except Exception as e:
            print(f"Error saving tile {basemap}/{zoom}/{x}/{y}: {e}")
            return False
    
    def load_tile(self, basemap, zoom, x, y):
        """Load a map tile from disk"""
        try:
            tile_path = self._get_tile_path(basemap, zoom, x, y)
            if tile_path.exists():
                with open(tile_path, 'rb') as f:
                    return f.read()
        except Exception as e:
            print(f"Error loading tile {basemap}/{zoom}/{x}/{y}: {e}")
        return None
    
    def save_terrain(self, lat, lon, radius_km, terrain_data):
        """Save terrain elevation data
        
        Args:
            lat: Center latitude
            lon: Center longitude
            radius_km: Radius of coverage area
            terrain_data: Dict with structure:
                {
                    'center': (lat, lon),
                    'radius_km': radius,
                    'radials': {
                        azimuth: [(lat, lon, elevation), ...]
                    }
                }
        """
        try:
            key = self._get_terrain_key(lat, lon, radius_km)
            terrain_path = self._get_terrain_path(key)
            
            with open(terrain_path, 'wb') as f:
                pickle.dump(terrain_data, f)
            
            print(f"Saved terrain data: {key}")
            return True
        except Exception as e:
            print(f"Error saving terrain data: {e}")
            return False
    
    def load_terrain(self, lat, lon, radius_km):
        """Load terrain elevation data from cache
        
        Returns:
            Terrain data dict or None if not cached
        """
        try:
            key = self._get_terrain_key(lat, lon, radius_km)
            terrain_path = self._get_terrain_path(key)
            
            if terrain_path.exists():
                with open(terrain_path, 'rb') as f:
                    data = pickle.load(f)
                print(f"Loaded cached terrain data: {key}")
                return data
        except Exception as e:
            print(f"Error loading terrain data: {e}")
        return None
    
    def get_cache_stats(self):
        """Get statistics about cached data"""
        stats = {
            'tiles': 0,
            'terrain': 0,
            'size_mb': 0
        }
        
        # Count tiles
        for basemap_dir in self.tiles_dir.iterdir():
            if basemap_dir.is_dir():
                for zoom_dir in basemap_dir.iterdir():
                    if zoom_dir.is_dir():
                        for x_dir in zoom_dir.iterdir():
                            if x_dir.is_dir():
                                stats['tiles'] += len(list(x_dir.glob('*.png')))
        
        # Count terrain files
        stats['terrain'] = len(list(self.terrain_dir.glob('*.pkl')))
        
        # Calculate total size
        total_size = 0
        for file in self.cache_dir.rglob('*'):
            if file.is_file():
                total_size += file.stat().st_size
        stats['size_mb'] = round(total_size / (1024 * 1024), 2)
        
        return stats
    
    def clear_cache(self, clear_tiles=True, clear_terrain=True):
        """Clear cached data"""
        import shutil
        
        if clear_tiles:
            shutil.rmtree(self.tiles_dir)
            self.tiles_dir.mkdir(exist_ok=True)
            print("Cleared tile cache")
        
        if clear_terrain:
            shutil.rmtree(self.terrain_dir)
            self.terrain_dir.mkdir(exist_ok=True)
            print("Cleared terrain cache")
    
    def export_project(self, output_file, lat, lon, radius_km):
        """Export map area as portable project file
        
        Creates a single file containing:
        - Map tiles for the area
        - Terrain data
        - Metadata
        """
        try:
            project_data = {
                'version': '1.0',
                'center': {'lat': lat, 'lon': lon},
                'radius_km': radius_km,
                'tiles': {},
                'terrain': None
            }
            
            # Load terrain data
            terrain = self.load_terrain(lat, lon, radius_km)
            if terrain:
                project_data['terrain'] = terrain
            
            # TODO: Package relevant tiles
            
            with open(output_file, 'wb') as f:
                pickle.dump(project_data, f)
            
            print(f"Exported project to {output_file}")
            return True
            
        except Exception as e:
            print(f"Error exporting project: {e}")
            return False
    
    def import_project(self, input_file):
        """Import project file"""
        try:
            with open(input_file, 'rb') as f:
                project_data = pickle.load(f)
            
            # Import terrain
            if project_data.get('terrain'):
                center = project_data['center']
                radius = project_data['radius_km']
                self.save_terrain(
                    center['lat'], 
                    center['lon'], 
                    radius, 
                    project_data['terrain']
                )
            
            # TODO: Import tiles
            
            print(f"Imported project from {input_file}")
            return project_data['center'], project_data['radius_km']
            
        except Exception as e:
            print(f"Error importing project: {e}")
            return None, None