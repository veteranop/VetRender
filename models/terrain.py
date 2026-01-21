"""
Terrain elevation data handling with caching
"""
import json
import os
import pickle
from urllib.request import urlopen, Request

class TerrainHandler:
    """Handles terrain elevation data from Open-Elevation API with local caching"""

    # Cache directory
    CACHE_DIR = "terrain_cache"

    # Grid resolution for caching (degrees)
    # 0.01 degrees ≈ 1km at equator
    GRID_RESOLUTION = 0.01

    # In-memory cache for quick access
    _memory_cache = {}

    @staticmethod
    def _get_cache_key(lat, lon):
        """Generate cache key for a lat/lon pair rounded to grid"""
        # Round to grid resolution
        grid_lat = round(lat / TerrainHandler.GRID_RESOLUTION) * TerrainHandler.GRID_RESOLUTION
        grid_lon = round(lon / TerrainHandler.GRID_RESOLUTION) * TerrainHandler.GRID_RESOLUTION
        return (grid_lat, grid_lon)

    @staticmethod
    def _get_cache_file_path(lat, lon):
        """Get file path for cached elevation data"""
        key = TerrainHandler._get_cache_key(lat, lon)
        # Create subdirectories based on lat/lon for organization
        lat_dir = int(key[0])
        lon_dir = int(key[1])
        subdir = os.path.join(TerrainHandler.CACHE_DIR, f"lat_{lat_dir}", f"lon_{lon_dir}")
        os.makedirs(subdir, exist_ok=True)
        filename = f"{key[0]:.3f}_{key[1]:.3f}.pkl"
        return os.path.join(subdir, filename)

    @staticmethod
    def _load_from_cache(lat, lon):
        """Load elevation from cache (memory or disk)"""
        key = TerrainHandler._get_cache_key(lat, lon)

        # Check memory cache first
        if key in TerrainHandler._memory_cache:
            print(f"DEBUG: Terrain cache hit (memory) for {lat},{lon}")
            return TerrainHandler._memory_cache[key]

        # Check disk cache
        cache_file = TerrainHandler._get_cache_file_path(lat, lon)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    elevation = pickle.load(f)
                    # Store in memory cache
                    TerrainHandler._memory_cache[key] = elevation
                    print(f"DEBUG: Terrain cache hit (disk) for {lat},{lon}: {elevation}m")
                    return elevation
            except Exception as e:
                print(f"Warning: Failed to load terrain cache: {e}")

        return None

    @staticmethod
    def _save_to_cache(lat, lon, elevation):
        """Save elevation to cache (memory and disk)"""
        key = TerrainHandler._get_cache_key(lat, lon)

        # Save to memory cache
        TerrainHandler._memory_cache[key] = elevation

        # Save to disk cache
        try:
            cache_file = TerrainHandler._get_cache_file_path(lat, lon)
            with open(cache_file, 'wb') as f:
                pickle.dump(elevation, f)
        except Exception as e:
            print(f"Warning: Failed to save terrain cache: {e}")

    @staticmethod
    def get_elevation(lat, lon):
        """Get elevation for a single point with caching

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            Elevation in meters
        """
        # Try to load from cache first
        cached = TerrainHandler._load_from_cache(lat, lon)
        if cached is not None:
            return cached

        # Not in cache, fetch from API
        print(f"DEBUG: Fetching new terrain data for {lat},{lon}")
        try:
            # Try multiple datasets for better resolution (US locations get priority)
            datasets = []
            if -125 <= lon <= -65 and 25 <= lat <= 50:  # US bounding box
                datasets = ['srtm3', 'aster30m', 'gtopo30']  # Try higher-res first for US
                print(f"DEBUG: US location detected, trying datasets: {datasets}")
            else:
                datasets = ['aster30m', 'srtm3', 'gtopo30']  # Global fallback
                print(f"DEBUG: Global location, trying datasets: {datasets}")

            elevation = None
            used_dataset = None

            for dataset in datasets:
                try:
                    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}&dataset={dataset}"
                    req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})

                    with urlopen(req, timeout=15) as response:
                        data = json.loads(response.read().decode())
                        if 'results' in data and len(data['results']) > 0:
                            test_elevation = data['results'][0]['elevation']
                            if test_elevation is not None and math.isfinite(test_elevation):
                                elevation = test_elevation
                                used_dataset = dataset
                                print(f"DEBUG: Successfully got elevation from {dataset} dataset")
                                break  # Use first successful dataset
                except Exception as e:
                    print(f"DEBUG: Dataset {dataset} failed: {e}")
                    continue  # Try next dataset

            # Fallback to default if no dataset worked
            if elevation is None:
                url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
                req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})

                with urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    if 'results' in data and len(data['results']) > 0:
                        elevation = data['results'][0]['elevation']
                        used_dataset = 'default'

            if elevation is not None:
                # BEGIN: Super-sampling for higher effective resolution (cross pattern for efficiency)
                # Only super-sample for US locations to avoid excessive API calls
                if -125 <= lon <= -65 and 25 <= lat <= 50:  # US region
                    print(f"DEBUG: Starting super-sampling for US location {lat},{lon}")
                    super_samples = []
                    grid_size = 0.0003  # ~30m spacing at 45° latitude

                    # Cross pattern: center + 4 cardinal directions (5 total vs 9)
                    offsets = [(0, 0), (0, grid_size), (0, -grid_size), (grid_size, 0), (-grid_size, 0)]

                    for dlat, dlon in offsets:
                        try:
                            sample_lat = lat + dlat
                            sample_lon = lon + dlon
                            sample_url = f"https://api.open-elevation.com/api/v1/lookup?locations={sample_lat},{sample_lon}"
                            if used_dataset and used_dataset != 'default':
                                sample_url += f"&dataset={used_dataset}"

                            sample_req = Request(sample_url, headers={'User-Agent': 'VetRender RF Tool/1.0'})
                            with urlopen(sample_req, timeout=3) as sample_response:
                                sample_data = json.loads(sample_response.read().decode())
                                if 'results' in sample_data and len(sample_data['results']) > 0:
                                    sample_elev = sample_data['results'][0]['elevation']
                                    if sample_elev is not None and math.isfinite(sample_elev):
                                        super_samples.append(sample_elev)
                        except Exception as e:
                            print(f"DEBUG: Super-sample failed for offset {dlat},{dlon}: {e}")
                            continue  # Skip failed samples

                    print(f"DEBUG: Super-sampling collected {len(super_samples)} samples for {lat},{lon}")

                    # Use median of super-samples for more robust elevation
                    if len(super_samples) >= 3:  # Need at least 3 samples for median
                        elevation = sorted(super_samples)[len(super_samples)//2]
                        print(f"Super-sampled elevation for {lat},{lon}: {len(super_samples)} samples, median: {elevation}m")
                    else:
                        print(f"DEBUG: Insufficient super-samples ({len(super_samples)}), using original elevation")
                else:
                    print(f"DEBUG: Location {lat},{lon} not in US region, skipping super-sampling")
                # END: Super-sampling for higher effective resolution

                # BEGIN: Add NaN and invalid data validation
                import math
                if math.isnan(elevation) or elevation is None:
                    print(f"Warning: Invalid elevation data (NaN/None) for {lat},{lon}, using fallback value 0")
                    elevation = 0
                elif elevation < -1000 or elevation > 9000:  # Reasonable elevation bounds
                    print(f"Warning: Out-of-range elevation {elevation}m for {lat},{lon}, clamping to valid range")
                    elevation = max(-1000, min(9000, elevation))
                # END: Add NaN and invalid data validation

                if used_dataset and used_dataset != 'default':
                    print(f"Using {used_dataset} dataset for {lat},{lon}: {elevation}m")

                # Save to cache
                TerrainHandler._save_to_cache(lat, lon, elevation)
                return elevation
        except Exception as e:
            print(f"Warning: Could not fetch elevation for {lat},{lon}: {e}")

        return 0
    
    @staticmethod
    def get_elevations_batch(lat_lon_pairs):
        """Get elevations for multiple points with caching

        Args:
            lat_lon_pairs: List of (lat, lon) tuples

        Returns:
            List of elevations in meters
        """
        elevations = []
        uncached_pairs = []
        uncached_indices = []

        # Check cache for each point
        for i, (lat, lon) in enumerate(lat_lon_pairs[:100]):
            cached = TerrainHandler._load_from_cache(lat, lon)
            if cached is not None:
                elevations.append(cached)
            else:
                elevations.append(None)  # Placeholder
                uncached_pairs.append((lat, lon))
                uncached_indices.append(i)

        # If all were cached, return immediately
        if not uncached_pairs:
            print(f"All {len(lat_lon_pairs)} terrain points loaded from cache")
            return elevations

        # Fetch uncached points from API
        print(f"Fetching {len(uncached_pairs)} uncached terrain points (cached: {len(lat_lon_pairs) - len(uncached_pairs)})")
        try:
            # Determine best dataset for the region (use first point as reference)
            if uncached_pairs:
                ref_lat, ref_lon = uncached_pairs[0]
                if -125 <= ref_lon <= -65 and 25 <= ref_lat <= 50:  # US region
                    preferred_dataset = 'srtm3'  # Try SRTM 3-arc-second first for US
                else:
                    preferred_dataset = 'aster30m'  # ASTER for global

                # Try preferred dataset first
                locations = "|".join([f"{lat},{lon}" for lat, lon in uncached_pairs])
                url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}&dataset={preferred_dataset}"
                req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})

                batch_success = False
                try:
                    with urlopen(req, timeout=30) as response:
                        data = json.loads(response.read().decode())
                        if 'results' in data:
                            print(f"Using {preferred_dataset} dataset for batch request")
                            batch_success = True
                except Exception as e:
                    print(f"{preferred_dataset} dataset failed, trying default: {e}")

                # Fallback to default if preferred failed
                if not batch_success:
                    url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}"
                    req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})

                    with urlopen(req, timeout=30) as response:
                        data = json.loads(response.read().decode())

                if 'results' in data:
                    # Save fetched elevations to cache and update results
                    for i, result in enumerate(data['results']):
                        elevation = result['elevation']
                        lat, lon = uncached_pairs[i]

                        # BEGIN: Add NaN and invalid data validation for batch
                        import math
                        if math.isnan(elevation) or elevation is None:
                            print(f"Warning: Invalid elevation data (NaN/None) for {lat},{lon} in batch, using fallback value 0")
                            elevation = 0
                        elif elevation < -1000 or elevation > 9000:  # Reasonable elevation bounds
                            print(f"Warning: Out-of-range elevation {elevation}m for {lat},{lon} in batch, clamping to valid range")
                            elevation = max(-1000, min(9000, elevation))
                        # END: Add NaN and invalid data validation for batch

                        TerrainHandler._save_to_cache(lat, lon, elevation)
                        elevations[uncached_indices[i]] = elevation
        except Exception as e:
            print(f"Warning: Batch elevation fetch failed: {e}")
            # Fill uncached with 0
            for idx in uncached_indices:
                if elevations[idx] is None:
                    elevations[idx] = 0

        # Fill any remaining Nones with 0
        elevations = [e if e is not None else 0 for e in elevations]

        return elevations

    @staticmethod
    def export_cache_for_area(center_lat, center_lon, radius_km):
        """Export terrain cache for a coverage area to include in project file

        Args:
            center_lat: Center latitude
            center_lon: Center longitude
            radius_km: Coverage radius in km

        Returns:
            Dictionary with lat/lon keys and elevation values (JSON serializable)
        """
        import math

        # Calculate bounding box
        lat_delta = radius_km / 111.0  # 1° latitude ≈ 111 km
        lon_delta = radius_km / (111.0 * math.cos(math.radians(center_lat)))

        min_lat = center_lat - lat_delta
        max_lat = center_lat + lat_delta
        min_lon = center_lon - lon_delta
        max_lon = center_lon + lon_delta

        # Extract relevant cache entries
        cache_export = {}

        # Check memory cache
        for (lat, lon), elevation in TerrainHandler._memory_cache.items():
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                cache_export[f"{lat:.6f},{lon:.6f}"] = elevation

        # Also check disk cache
        if os.path.exists(TerrainHandler.CACHE_DIR):
            for root, dirs, files in os.walk(TerrainHandler.CACHE_DIR):
                for file in files:
                    if file.endswith('.pkl'):
                        try:
                            filepath = os.path.join(root, file)
                            with open(filepath, 'rb') as f:
                                data = pickle.load(f)
                                lat, lon = data['location']
                                elevation = data['elevation']
                                if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                                    cache_export[f"{lat:.6f},{lon:.6f}"] = elevation
                        except:
                            pass

        return cache_export

    @staticmethod
    def import_cache(cache_data):
        """Import terrain cache from project file

        Args:
            cache_data: Dictionary with "lat,lon" keys and elevation values
        """
        if not cache_data:
            return

        imported_count = 0

        for key, elevation in cache_data.items():
            try:
                lat_str, lon_str = key.split(',')
                lat = float(lat_str)
                lon = float(lon_str)

                # Add to memory cache
                cache_key = TerrainHandler._get_cache_key(lat, lon)
                TerrainHandler._memory_cache[cache_key] = elevation

                # Also save to disk cache
                TerrainHandler._save_to_cache(lat, lon, elevation)

                imported_count += 1
            except:
                pass

        print(f"Imported {imported_count} terrain elevation points from project cache")