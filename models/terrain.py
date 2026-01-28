"""
Terrain elevation data handling with caching.
Uses local SRTM .hgt tiles for instant elevation lookups,
with automatic download and API fallback.
"""
import gzip
import json
import math
import os
import pickle

import numpy as np
from urllib.request import urlopen, Request


class SRTMTileManager:
    """Manages local SRTM .hgt elevation tiles for instant terrain lookups.

    SRTM tiles are 1°×1° binary files of 16-bit elevation values.
    Tiles are auto-downloaded from AWS on first access (free, no auth).
    Once loaded, elevation lookups are instant numpy array indexing.
    """

    SRTM_DIR = "terrain_data"
    SRTM1_SIZE = 3601       # 1 arc-second (~30m)
    SRTM3_SIZE = 1201       # 3 arc-second (~90m)
    SRTM1_BYTES = 3601 * 3601 * 2   # 25,934,402 bytes
    SRTM3_BYTES = 1201 * 1201 * 2   # 2,884,802 bytes
    NODATA = -32768

    # Session-persistent loaded tiles: {(tile_lat, tile_lon): (numpy_array, samples)}
    _tiles = {}
    # Track tiles we already failed to download (don't retry every lookup)
    _failed_downloads = set()

    @staticmethod
    def _tile_key(lat, lon):
        """Get tile identifier (SW corner) for a lat/lon point."""
        return (math.floor(lat), math.floor(lon))

    @staticmethod
    def _tile_filename(tile_lat, tile_lon):
        """Convert tile coordinates to SRTM filename, e.g. N43W112.hgt"""
        ns = "N" if tile_lat >= 0 else "S"
        ew = "E" if tile_lon >= 0 else "W"
        return f"{ns}{abs(tile_lat):02d}{ew}{abs(tile_lon):03d}.hgt"

    @staticmethod
    def _tile_path(tile_lat, tile_lon):
        """Full path to .hgt file on disk."""
        filename = SRTMTileManager._tile_filename(tile_lat, tile_lon)
        return os.path.join(SRTMTileManager.SRTM_DIR, filename)

    @staticmethod
    def _download_tile(tile_lat, tile_lon):
        """Download an SRTM tile from AWS (free, no auth required).
        Returns True if successful."""
        key = (tile_lat, tile_lon)
        if key in SRTMTileManager._failed_downloads:
            return False

        filename = SRTMTileManager._tile_filename(tile_lat, tile_lon)
        out_path = SRTMTileManager._tile_path(tile_lat, tile_lon)

        os.makedirs(SRTMTileManager.SRTM_DIR, exist_ok=True)

        # AWS Terrain Tiles (Mapzen/Tilezen skadi format) - free, no auth
        ns = "N" if tile_lat >= 0 else "S"
        lat_dir = f"{ns}{abs(tile_lat):02d}"
        url = f"https://elevation-tiles-prod.s3.amazonaws.com/skadi/{lat_dir}/{filename}.gz"

        print(f"Downloading SRTM tile {filename} from AWS...")
        try:
            req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})
            with urlopen(req, timeout=60) as response:
                compressed = response.read()

            decompressed = gzip.decompress(compressed)
            with open(out_path, 'wb') as f:
                f.write(decompressed)

            size_mb = len(decompressed) / 1024 / 1024
            print(f"Downloaded {filename} ({size_mb:.1f}MB)")
            return True
        except Exception as e:
            print(f"Warning: Failed to download SRTM tile {filename}: {e}")
            SRTMTileManager._failed_downloads.add(key)
            return False

    @staticmethod
    def _load_tile(tile_lat, tile_lon):
        """Load an .hgt tile into memory. Auto-downloads if not on disk.
        Returns (numpy_array, samples) tuple or None."""
        key = (tile_lat, tile_lon)

        # Already loaded this session?
        if key in SRTMTileManager._tiles:
            return SRTMTileManager._tiles[key]

        path = SRTMTileManager._tile_path(tile_lat, tile_lon)
        gz_path = path + ".gz"

        # Check for file on disk (or .gz variant)
        if not os.path.exists(path):
            if os.path.exists(gz_path):
                try:
                    print(f"Decompressing {gz_path}...")
                    with gzip.open(gz_path, 'rb') as gz_f:
                        with open(path, 'wb') as out_f:
                            out_f.write(gz_f.read())
                except Exception as e:
                    print(f"Warning: Failed to decompress {gz_path}: {e}")
                    return None
            else:
                # Try auto-download
                if not SRTMTileManager._download_tile(tile_lat, tile_lon):
                    return None
                # Verify download succeeded
                if not os.path.exists(path):
                    return None

        # Auto-detect SRTM1 vs SRTM3 from file size
        file_size = os.path.getsize(path)
        if file_size == SRTMTileManager.SRTM1_BYTES:
            samples = SRTMTileManager.SRTM1_SIZE
            res_label = "SRTM1 30m"
        elif file_size == SRTMTileManager.SRTM3_BYTES:
            samples = SRTMTileManager.SRTM3_SIZE
            res_label = "SRTM3 90m"
        else:
            print(f"Warning: Unknown .hgt file size {file_size} for {path}, skipping")
            return None

        # Load as big-endian signed 16-bit integers
        data = np.fromfile(path, dtype='>i2').reshape((samples, samples))

        result = (data, samples)
        SRTMTileManager._tiles[key] = result

        filename = SRTMTileManager._tile_filename(tile_lat, tile_lon)
        print(f"Loaded SRTM tile {filename} ({res_label}, {file_size / 1024 / 1024:.1f}MB)")
        return result

    @staticmethod
    def get_elevation(lat, lon):
        """Get elevation from SRTM tile with bilinear interpolation.
        Returns elevation in meters, or None if tile not available."""
        tile_lat, tile_lon = SRTMTileManager._tile_key(lat, lon)
        tile_data = SRTMTileManager._load_tile(tile_lat, tile_lon)

        if tile_data is None:
            return None

        data, samples = tile_data

        # Convert lat/lon to fractional row/col
        # Row 0 = north edge (tile_lat + 1), last row = south edge (tile_lat)
        # Col 0 = west edge (tile_lon), last col = east edge (tile_lon + 1)
        row_f = (tile_lat + 1 - lat) * (samples - 1)
        col_f = (lon - tile_lon) * (samples - 1)

        # Integer indices for 4 surrounding points
        row = int(row_f)
        col = int(col_f)
        row = max(0, min(row, samples - 2))
        col = max(0, min(col, samples - 2))

        # Fractional parts for interpolation
        row_frac = row_f - row
        col_frac = col_f - col

        # Read 4 corner values
        v00 = int(data[row, col])
        v01 = int(data[row, col + 1])
        v10 = int(data[row + 1, col])
        v11 = int(data[row + 1, col + 1])

        # Handle NODATA voids
        corners = [v00, v01, v10, v11]
        if SRTMTileManager.NODATA in corners:
            valid = [v for v in corners if v != SRTMTileManager.NODATA]
            if valid:
                return float(np.mean(valid))
            return None

        # Bilinear interpolation
        elevation = (v00 * (1 - row_frac) * (1 - col_frac) +
                     v01 * (1 - row_frac) * col_frac +
                     v10 * row_frac * (1 - col_frac) +
                     v11 * row_frac * col_frac)

        return float(elevation)

    @staticmethod
    def get_elevations_batch(lat_lon_pairs):
        """Vectorized batch lookup from SRTM tiles.
        Returns list of elevations (float or None where tile unavailable)."""
        results = [None] * len(lat_lon_pairs)

        # Group points by tile for efficient loading
        tile_groups = {}
        for i, (lat, lon) in enumerate(lat_lon_pairs):
            key = SRTMTileManager._tile_key(lat, lon)
            if key not in tile_groups:
                tile_groups[key] = []
            tile_groups[key].append((i, lat, lon))

        for (tile_lat, tile_lon), points in tile_groups.items():
            tile_data = SRTMTileManager._load_tile(tile_lat, tile_lon)
            if tile_data is None:
                continue  # Leave as None — will fall through to API

            data, samples = tile_data

            # Vectorize all points for this tile
            indices = [p[0] for p in points]
            lats = np.array([p[1] for p in points])
            lons = np.array([p[2] for p in points])

            rows_f = (tile_lat + 1 - lats) * (samples - 1)
            cols_f = (lons - tile_lon) * (samples - 1)

            rows = np.clip(rows_f.astype(int), 0, samples - 2)
            cols = np.clip(cols_f.astype(int), 0, samples - 2)

            row_fracs = rows_f - rows
            col_fracs = cols_f - cols

            v00 = data[rows, cols].astype(np.float64)
            v01 = data[rows, cols + 1].astype(np.float64)
            v10 = data[rows + 1, cols].astype(np.float64)
            v11 = data[rows + 1, cols + 1].astype(np.float64)

            # Bilinear interpolation (vectorized)
            elevations = (v00 * (1 - row_fracs) * (1 - col_fracs) +
                         v01 * (1 - row_fracs) * col_fracs +
                         v10 * row_fracs * (1 - col_fracs) +
                         v11 * row_fracs * col_fracs)

            # Handle NODATA voids
            nodata = float(SRTMTileManager.NODATA)
            has_void = ((v00 == nodata) | (v01 == nodata) |
                       (v10 == nodata) | (v11 == nodata))

            for j, idx in enumerate(indices):
                if has_void[j]:
                    corners = [v00[j], v01[j], v10[j], v11[j]]
                    valid = [c for c in corners if c != nodata]
                    results[idx] = float(np.mean(valid)) if valid else None
                else:
                    results[idx] = float(elevations[j])

        return results

    @classmethod
    def set_srtm_directory(cls, path):
        """Set the directory for SRTM .hgt files."""
        cls.SRTM_DIR = path
        cls._tiles.clear()


class TerrainHandler:
    """Handles terrain elevation data from Open-Elevation API with local caching"""

    # Cache directory
    CACHE_DIR = "terrain_cache"

    # =================================================================================
    # HIGH-RESOLUTION TERRAIN CACHING (FIXES 1KM BLOCK ARTIFACTS!)
    # =================================================================================
    # Grid resolution for caching (degrees)
    # OLD: 0.01 degrees ≈ 1.1km caused huge square blocks in coverage plots
    # NEW: 0.0001 degrees ≈ 11 meters for smooth terrain representation
    # This allows proper interpolation without visible grid artifacts
    # ROLLBACK: Change to 0.001 (110m) or 0.01 (1.1km) to reduce API calls/cache size
    # =================================================================================
    GRID_RESOLUTION = 0.0001  # 11 meters - smooth terrain without visible blocks
    # =================================================================================

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
            return TerrainHandler._memory_cache[key]

        # Check disk cache
        cache_file = TerrainHandler._get_cache_file_path(lat, lon)
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    elevation = pickle.load(f)
                    # Store in memory cache
                    TerrainHandler._memory_cache[key] = elevation
                    return elevation
            except:
                pass  # Silently fail, will fetch from SRTM/API

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

        # Try SRTM local tile lookup (instant if tile is loaded/downloaded)
        srtm_elev = SRTMTileManager.get_elevation(lat, lon)
        if srtm_elev is not None:
            TerrainHandler._save_to_cache(lat, lon, srtm_elev)
            return srtm_elev

        # Fallback: fetch from API (only when SRTM tile unavailable)
        try:
            # Try multiple datasets for better resolution
            datasets = ['srtm3', 'aster30m', 'gtopo30'] if (-125 <= lon <= -65 and 25 <= lat <= 50) else ['aster30m', 'srtm3', 'gtopo30']

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
                                break
                except:
                    continue

            # Fallback to default if no dataset worked
            if elevation is None:
                try:
                    url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
                    req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})
                    with urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode())
                        if 'results' in data and len(data['results']) > 0:
                            elevation = data['results'][0]['elevation']
                except:
                    pass

            if elevation is not None:
                # Validate elevation data
                if math.isnan(elevation) or elevation is None:
                    elevation = 0
                elif elevation < -1000 or elevation > 9000:
                    elevation = max(-1000, min(9000, elevation))

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
        for i, (lat, lon) in enumerate(lat_lon_pairs):
            cached = TerrainHandler._load_from_cache(lat, lon)
            if cached is not None:
                elevations.append(cached)
            else:
                elevations.append(None)  # Placeholder
                uncached_pairs.append((lat, lon))
                uncached_indices.append(i)

        # If all were cached, return immediately
        if not uncached_pairs:
            return elevations

        # Try SRTM local tile lookup first (vectorized, instant)
        srtm_results = SRTMTileManager.get_elevations_batch(uncached_pairs)

        still_uncached_pairs = []
        still_uncached_indices = []

        for j, srtm_elev in enumerate(srtm_results):
            orig_idx = uncached_indices[j]
            lat, lon = uncached_pairs[j]
            if srtm_elev is not None:
                elevations[orig_idx] = srtm_elev
                TerrainHandler._save_to_cache(lat, lon, srtm_elev)
            else:
                still_uncached_pairs.append((lat, lon))
                still_uncached_indices.append(orig_idx)

        # Update uncached lists — only points NOT resolved by SRTM fall through to API
        uncached_pairs = still_uncached_pairs
        uncached_indices = still_uncached_indices

        if not uncached_pairs:
            return elevations

        # Fallback: Fetch remaining uncached points from API in chunks
        CHUNK_SIZE = 80
        print(f"SRTM resolved {len(lat_lon_pairs) - len(uncached_pairs)}/{len(lat_lon_pairs)} points. "
              f"Fetching {len(uncached_pairs)} remaining from API...")
        try:
            import math

            # Determine best dataset for the region (use first point as reference)
            preferred_dataset = 'aster30m'
            if uncached_pairs:
                ref_lat, ref_lon = uncached_pairs[0]
                if -125 <= ref_lon <= -65 and 25 <= ref_lat <= 50:  # US region
                    preferred_dataset = 'srtm3'

            # Process in chunks
            for chunk_start in range(0, len(uncached_pairs), CHUNK_SIZE):
                chunk_end = min(chunk_start + CHUNK_SIZE, len(uncached_pairs))
                chunk_pairs = uncached_pairs[chunk_start:chunk_end]
                chunk_indices = uncached_indices[chunk_start:chunk_end]

                locations = "|".join([f"{lat},{lon}" for lat, lon in chunk_pairs])
                url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}&dataset={preferred_dataset}"
                req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})

                chunk_success = False
                try:
                    with urlopen(req, timeout=30) as response:
                        data = json.loads(response.read().decode())
                        if 'results' in data:
                            chunk_success = True
                except Exception as e:
                    # Fallback to default dataset
                    try:
                        url = f"https://api.open-elevation.com/api/v1/lookup?locations={locations}"
                        req = Request(url, headers={'User-Agent': 'VetRender RF Tool/1.0'})
                        with urlopen(req, timeout=30) as response:
                            data = json.loads(response.read().decode())
                            if 'results' in data:
                                chunk_success = True
                    except Exception as e2:
                        print(f"Warning: Chunk fetch failed: {e2}")

                if chunk_success and 'results' in data:
                    for i, result in enumerate(data['results']):
                        elevation = result['elevation']
                        lat, lon = chunk_pairs[i]

                        if elevation is None or math.isnan(elevation):
                            elevation = 0
                        elif elevation < -1000 or elevation > 9000:
                            elevation = max(-1000, min(9000, elevation))

                        TerrainHandler._save_to_cache(lat, lon, elevation)
                        elevations[chunk_indices[i]] = elevation
                else:
                    # Fill failed chunk with 0
                    for idx in chunk_indices:
                        if elevations[idx] is None:
                            elevations[idx] = 0

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