"""
Propagation Controller Module
==============================
Orchestrates RF propagation calculations with terrain analysis.

🔥 THIS MODULE CONTAINS ALL THREE CRITICAL FIXES:
1. Segment-by-segment terrain diffraction (no shadow tunneling!)
2. 360° azimuth sampling (no radial artifacts!)
3. Proper grid resolution and interpolation

This is the "brain" that coordinates between terrain data, propagation models,
and the rendering system.
"""

import numpy as np
import os
import datetime
from models.propagation import PropagationModel
from models.terrain import TerrainHandler
from models.antenna import AntennaPattern


class PropagationController:
    """Orchestrates propagation calculations with terrain analysis"""
    
    def __init__(self, antenna_pattern=None):
        """Initialize controller
        
        Args:
            antenna_pattern: AntennaPattern instance (optional)
        """
        self.antenna_pattern = antenna_pattern or AntennaPattern()
        
        # Debug logging
        self.debug_log_path = os.path.join("logs", "propagation_debug.log")
        os.makedirs("logs", exist_ok=True)
    
    def _log_debug(self, message):
        """Write to debug log
        
        Args:
            message: Debug message to log
        """
        try:
            with open(self.debug_log_path, 'a') as f:
                f.write(f"[{datetime.datetime.now()}] {message}\n")
        except Exception as e:
            print(f"Warning: Failed to write debug log: {e}")
    
    def calculate_coverage(self, tx_lat, tx_lon, tx_height, erp_dbm, frequency_mhz,
                          max_distance_km, resolution, signal_threshold_dbm,
                          use_terrain=False, terrain_quality='Medium',
                          custom_azimuth_count=None, custom_distance_points=None):
        """Calculate RF propagation coverage with Cartesian grid (eliminates radial artifacts)
        
        Args:
            tx_lat: Transmitter latitude
            tx_lon: Transmitter longitude
            tx_height: Transmitter antenna height AGL (m)
            erp_dbm: Effective radiated power (dBm)
            frequency_mhz: Frequency (MHz)
            max_distance_km: Maximum coverage distance (km)
            resolution: Grid resolution (points per dimension)
            signal_threshold_dbm: Minimum signal threshold (dBm)
            use_terrain: Whether to use terrain analysis
            terrain_quality: Quality preset ('Low', 'Medium', 'High', 'Ultra', 'Custom')
            custom_azimuth_count: Custom azimuth count (overrides quality preset)
            custom_distance_points: Custom distance points (overrides quality preset)
            
        Returns:
            Tuple of (az_grid, dist_grid, rx_power_grid, terrain_loss_grid, stats_dict)
            or None if calculation fails
        """
        try:
            print(f"\n{'='*60}")
            print(f"CALCULATING PROPAGATION - CARTESIAN GRID")
            print(f"{'='*60}")
            print(f"Location: Lat={tx_lat:.6f}, Lon={tx_lon:.6f}")
            print(f"ERP: {erp_dbm} dBm, Frequency: {frequency_mhz} MHz")
            print(f"Antenna Height: {tx_height} m, Max Distance: {max_distance_km} km")
            
            # Convert ERP to EIRP
            eirp_dbm = PropagationModel.erp_to_eirp(erp_dbm)
            print(f"EIRP: {eirp_dbm:.2f} dBm")
            
            # 🔥 FIX #1: Adaptive grid resolution based on coverage distance
            if max_distance_km <= 50:
                grid_resolution = resolution
            elif max_distance_km <= 100:
                grid_resolution = max(300, resolution // 2)
            else:
                grid_resolution = max(200, resolution // 3)
            
            print(f"Grid resolution: {grid_resolution} (optimized for {max_distance_km}km)")
            self._log_debug(f"Grid resolution: {grid_resolution} for {max_distance_km}km coverage")
            
            # Create Cartesian grid (eliminates radial artifacts)
            print(f"Creating CARTESIAN grid (fixes radial artifacts)...")
            x_km = np.linspace(-max_distance_km, max_distance_km, grid_resolution)
            y_km = np.linspace(-max_distance_km, max_distance_km, grid_resolution)
            x_grid, y_grid = np.meshgrid(x_km, y_km)
            
            # Calculate polar coordinates FROM Cartesian
            dist_grid = np.sqrt(x_grid**2 + y_grid**2)
            az_grid = np.degrees(np.arctan2(x_grid, y_grid)) % 360
            
            # Mask points outside coverage circle
            mask = dist_grid > max_distance_km
            
            print(f"Coverage area: {np.sum(~mask)} points within {max_distance_km} km")
            
            # Calculate antenna gains
            print(f"Calculating antenna gains...")
            gain_grid = np.zeros_like(az_grid)
            for i in range(az_grid.shape[0]):
                for j in range(az_grid.shape[1]):
                    if not mask[i, j]:
                        gain_grid[i, j] = self.antenna_pattern.get_gain(az_grid[i, j], elevation=0)
            
            print(f"Gain range: {gain_grid[~mask].min():.2f} to {gain_grid[~mask].max():.2f} dBi")
            
            # Calculate free space path loss
            print(f"Calculating path loss...")
            fspl_grid = PropagationModel.free_space_loss(dist_grid, frequency_mhz)
            fspl_grid[mask] = 0
            
            debug_msg = f"FSPL range: {fspl_grid[~mask].min():.2f} to {fspl_grid[~mask].max():.2f} dB"
            print(debug_msg)
            self._log_debug(debug_msg)
            
            # Terrain analysis
            terrain_loss_grid = np.zeros_like(dist_grid)
            
            if use_terrain:
                terrain_loss_grid = self._calculate_terrain_loss(
                    tx_lat, tx_lon, tx_height, max_distance_km,
                    frequency_mhz, terrain_quality,
                    custom_azimuth_count, custom_distance_points,
                    mask, dist_grid, az_grid
                )
            
            # Calculate received power
            rx_power_grid = eirp_dbm + gain_grid - fspl_grid - terrain_loss_grid
            
            # Validate power calculations
            if np.any(np.isnan(rx_power_grid)) or np.any(np.isinf(rx_power_grid)):
                print("Warning: NaN/inf in power grid, sanitizing...")
                nan_mask = np.isnan(rx_power_grid) | np.isinf(rx_power_grid)
                rx_power_grid[nan_mask & ~mask] = -150  # Very weak signal
                rx_power_grid[nan_mask & mask] = -999  # Masked area
            
            rx_power_grid[mask] = -999  # Mark masked areas
            
            # Calculate statistics
            stats = {
                'min_power': float(rx_power_grid[~mask].min()),
                'max_power': float(rx_power_grid[~mask].max()),
                'mean_power': float(rx_power_grid[~mask].mean()),
                'points_above_threshold': int(np.sum(rx_power_grid >= signal_threshold_dbm)),
                'total_points': int(np.sum(~mask))
            }
            
            if use_terrain:
                stats['min_terrain_loss'] = float(terrain_loss_grid[~mask].min())
                stats['max_terrain_loss'] = float(terrain_loss_grid[~mask].max())
                stats['mean_terrain_loss'] = float(terrain_loss_grid[~mask].mean())
            
            print(f"\n{'='*60}")
            print(f"PROPAGATION COMPLETE")
            print(f"{'='*60}")
            print(f"Power range: {stats['min_power']:.2f} to {stats['max_power']:.2f} dBm")
            print(f"Points above threshold: {stats['points_above_threshold']}/{stats['total_points']}")
            
            return az_grid, dist_grid, rx_power_grid, terrain_loss_grid, stats
            
        except Exception as e:
            print(f"\nERROR in calculate_coverage: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_terrain_loss(self, tx_lat, tx_lon, tx_height, max_distance_km,
                                frequency_mhz, terrain_quality, custom_azimuth_count,
                                custom_distance_points, mask, dist_grid, az_grid):
        """Calculate terrain diffraction loss with segment-by-segment LOS
        
        🔥 FIX #2: This uses 360° azimuth sampling to eliminate radial artifacts
        🔥 FIX #3: This uses segment-by-segment terrain diffraction (no shadow tunneling!)
        
        Args:
            tx_lat, tx_lon: Transmitter location
            tx_height: Transmitter height AGL (m)
            max_distance_km: Coverage radius
            frequency_mhz: Frequency
            terrain_quality: Quality preset
            custom_azimuth_count: Custom azimuth override
            custom_distance_points: Custom distance points override
            mask: Grid mask
            dist_grid: Distance grid
            az_grid: Azimuth grid
            
        Returns:
            Terrain loss grid (dB)
        """
        print(f"Fetching terrain data...")
        
        # 🔥 FIX #2: Quality presets with MORE azimuths for smoother interpolation
        quality_presets = {
            'Low': (180, 100),      # 180° for low quality
            'Medium': (540, 200),   # 540° = every 0.67° (was 360°)
            'High': (720, 300),     # 720° = every 0.5° (was 360°)
            'Ultra': (1080, 500),   # 1080° = every 0.33° (was 360°)
        }
        
        # Get sampling parameters
        if custom_azimuth_count is not None and custom_distance_points is not None:
            sample_azimuths_count = custom_azimuth_count
            sample_distances_count = custom_distance_points
            print(f"Using CUSTOM terrain sampling: {sample_azimuths_count}° × {sample_distances_count} pts")
        else:
            sample_azimuths_count, sample_distances_count = quality_presets.get(
                terrain_quality, (360, 300)
            )
            print(f"Using {terrain_quality} quality: {sample_azimuths_count}° × {sample_distances_count} pts")
        
        self._log_debug(f"Terrain sampling: {sample_azimuths_count} azimuths × {sample_distances_count} distances")
        
        # Sample terrain at specific azimuths (polar sampling for efficiency)
        sample_azimuths = np.linspace(0, 360, sample_azimuths_count, endpoint=False)
        sample_distances = np.linspace(0.1, max_distance_km, sample_distances_count)
        
        terrain_loss_samples = np.zeros((sample_distances_count, sample_azimuths_count))
        
        rx_height = 2.0  # Mobile receiver height (people, cars)
        
        for i, az in enumerate(sample_azimuths):
            if i % max(1, sample_azimuths_count // 10) == 0:
                print(f"  Processing azimuth {az:.0f}° ({i+1}/{sample_azimuths_count})")
            
            # Get terrain profile for this azimuth
            lat_points = []
            lon_points = []
            for d in sample_distances:
                lat_offset = d * np.cos(np.radians(az)) / 111.0
                lon_offset = d * np.sin(np.radians(az)) / (111.0 * np.cos(np.radians(tx_lat)))
                lat_points.append(tx_lat + lat_offset)
                lon_points.append(tx_lon + lon_offset)
            
            elevations = TerrainHandler.get_elevations_batch(list(zip(lat_points, lon_points)))
            
            # Enhanced terrain profile interpolation
            if len(elevations) > 3:
                try:
                    from scipy import interpolate
                    elev_interp = interpolate.interp1d(
                        np.linspace(0, sample_distances[-1], len(elevations)),
                        elevations, kind='cubic'
                    )
                    high_res_distances = np.linspace(0, sample_distances[-1], len(elevations) * 4)
                    elevations = elev_interp(high_res_distances)
                except:
                    pass  # Use original elevations if interpolation fails
            
            # 🔥 FIX #3: Calculate terrain loss per receiver point (segment-by-segment!)
            terrain_loss = np.zeros_like(sample_distances)
            for j, dist in enumerate(sample_distances):
                # THE MAGIC: Use rx_distance_km parameter for segment-by-segment LOS
                terrain_loss[j] = PropagationModel.terrain_diffraction_loss(
                    tx_height, rx_height, elevations, frequency_mhz,
                    np.linspace(0, sample_distances[-1], len(elevations)),
                    debug_azimuth=None,
                    rx_distance_km=dist  # 🔥 THIS IS THE FIX!
                )
            
            terrain_loss_samples[:, i] = terrain_loss
        
        # 🔥 NEW: Apply Gaussian smoothing to reduce interpolation artifacts
        print(f"Applying Gaussian smoothing to terrain data...")
        try:
            from scipy.ndimage import gaussian_filter
            # Smooth along azimuth axis (axis=1) to blend adjacent directions
            # sigma=1.5 provides good smoothing without losing terrain detail
            terrain_loss_samples = gaussian_filter(terrain_loss_samples, sigma=(0, 1.5))
            print(f"  Smoothing applied (sigma=1.5 on azimuth axis)")
        except ImportError:
            print(f"  Warning: scipy not available, skipping smoothing")
        except Exception as e:
            print(f"  Warning: Smoothing failed: {e}")
        
        print(f"Interpolating terrain loss to Cartesian grid (cubic splines)...")
        
        # Use cubic spline interpolation for smooth transitions
        try:
            from scipy.interpolate import interp1d
            use_cubic = True
            print(f"  Using cubic spline interpolation")
        except ImportError:
            use_cubic = False
            print(f"  Warning: scipy not available, using linear interpolation")
        
        # Numpy-based bilinear interpolation
        terrain_loss_grid = np.zeros_like(dist_grid)
        
        # Wrap azimuth for smooth 0/360 boundary
        sample_azimuths_wrap = np.append(sample_azimuths, 360)
        terrain_loss_wrap = np.column_stack([terrain_loss_samples, terrain_loss_samples[:, 0]])
        
        for i in range(dist_grid.shape[0]):
            for j in range(dist_grid.shape[1]):
                if not mask[i, j] and dist_grid[i, j] > 0.1:
                    d = dist_grid[i, j]
                    az = az_grid[i, j]
                    
                    # Bilinear interpolation in distance
                    d_idx = np.searchsorted(sample_distances, d)
                    if d_idx == 0:
                        d_idx = 1
                    if d_idx >= len(sample_distances):
                        d_idx = len(sample_distances) - 1
                    
                    d0, d1 = sample_distances[d_idx-1], sample_distances[d_idx]
                    w_d = (d - d0) / (d1 - d0) if d1 != d0 else 0
                    
                    # Interpolate across azimuths with cubic splines for smooth transitions
                    if use_cubic:
                        try:
                            # Create cubic interpolators for this distance bracket
                            loss_interp_0 = interp1d(sample_azimuths_wrap, 
                                                    terrain_loss_wrap[d_idx-1, :],
                                                    kind='cubic', 
                                                    fill_value='extrapolate')
                            loss_interp_1 = interp1d(sample_azimuths_wrap,
                                                    terrain_loss_wrap[d_idx, :],
                                                    kind='cubic',
                                                    fill_value='extrapolate')
                            
                            loss0 = float(loss_interp_0(az))
                            loss1 = float(loss_interp_1(az))
                        except:
                            # Fallback to linear if cubic fails
                            loss0 = np.interp(az, sample_azimuths_wrap, terrain_loss_wrap[d_idx-1, :])
                            loss1 = np.interp(az, sample_azimuths_wrap, terrain_loss_wrap[d_idx, :])
                    else:
                        # Linear interpolation (fallback)
                        loss0 = np.interp(az, sample_azimuths_wrap, terrain_loss_wrap[d_idx-1, :])
                        loss1 = np.interp(az, sample_azimuths_wrap, terrain_loss_wrap[d_idx, :])
                    
                    # Blend between distances
                    terrain_loss_grid[i, j] = loss0 * (1 - w_d) + loss1 * w_d
        
        terrain_msg = f"Terrain loss range: {terrain_loss_grid[~mask].min():.2f} to {terrain_loss_grid[~mask].max():.2f} dB"
        print(terrain_msg)
        self._log_debug(terrain_msg)
        
        return terrain_loss_grid
