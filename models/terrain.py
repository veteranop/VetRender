"""
Terrain elevation data handling
"""
import json
from urllib.request import urlopen, Request

class TerrainHandler:
    """Handles terrain elevation data from Open-Elevation API"""
    
    @staticmethod
    def get_elevation(lat, lon):
        """Get elevation for a single point using Open-Elevation API
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            
        Returns:
            Elevation in meters
        """
        try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
            req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})
            
            with urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                if 'results' in data and len(data['results']) > 0:
                    elevation = data['results'][0]['elevation']
                    return elevation
        except Exception as e:
            print(f"Warning: Could not fetch elevation for {lat},{lon}: {e}")
        
        return 0
    
    @staticmethod
    def get_elevations_batch(lat_lon_pairs):
        """Get elevations for multiple points (max 100 per request)
        
        Args:
            lat_lon_pairs: List of (lat, lon) tuples
            
        Returns:
            List of elevations in meters
        """
        try:
            locations = "|".join([f"{lat},{lon}" for lat, lon in lat_lon_pairs[:100]])
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}"
            req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})
            
            with urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode())
                if 'results' in data:
                    return [result['elevation'] for result in data['results']]
        except Exception as e:
            print(f"Warning: Batch elevation fetch failed: {e}")
        
        return [0] * len(lat_lon_pairs)