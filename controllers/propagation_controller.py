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
from models.antenna_models.antenna import AntennaPattern
# from models.land_cover import LandCoverHandler  # TODO: Future feature


class PropagationController:
    """Orchestrates propagation calculations with terrain analysis"""
    
    def __init__(self, antenna_pattern=None, use_land_cover=False):
        """Initialize controller

        Args:
            antenna_pattern: AntennaPattern instance (optional)
            use_land_cover: Enable land cover (urban/water/forest) loss calculations (optional)
        """
        self.antenna_pattern = antenna_pattern or AntennaPattern()

        # Land cover handler (optional feature)
        self.use_land_cover = use_land_cover
        self.land_cover_handler = None
        if use_land_cover:
            self.land_cover_handler = LandCoverHandler()

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

    def _calculate_zoom_aware_parameters(self, quality, zoom_level, coverage_km):
        """Calculate optimal parameters based on quality, zoom, and coverage area

        Args:
            quality: User's quality selection ('Low', 'Medium', 'High', 'Ultra')
            zoom_level: Map zoom level (8-16)
            coverage_km: Coverage radius in km

        Returns:
            tuple: (grid_resolution, scaled_quality_dict)
                grid_resolution: Grid points per dimension
                scaled_quality_dict: {'azimuths': int, 'distances': int}
        """
        # Quality base multipliers (before zoom scaling)
        quality_multipliers = {
            'Low': 0.7,
            'Medium': 1.0,
            'High': 1.4,
            'Ultra': 1.8
        }

        # Zoom scale factors
        if zoom_level <= 9:
            zoom_scale = 0.7  # Wide view, reduce quality
        elif zoom_level <= 11:
            zoom_scale = 1.0  # Normal view, standard quality
        elif zoom_level <= 13:
            zoom_scale = 1.3  # Close view, increase quality
        else:  # 14+
            zoom_scale = 1.6  # Very close, maximum quality

        # Combined multiplier
        base_multiplier = quality_multipliers.get(quality, 1.0)
        combined_multiplier = base_multiplier * zoom_scale

        # Grid resolution based on coverage area and combined multiplier
        if coverage_km <= 25:
            base_grid = 800
        elif coverage_km <= 50:
            base_grid = 1000
        elif coverage_km <= 100:
            base_grid = 750
        elif coverage_km <= 200:
            base_grid = 600
        else:
            base_grid = 500

        grid_resolution = int(base_grid * combined_multiplier)
        grid_resolution = min(grid_resolution, 2500)  # Cap at 2500 to prevent memory issues
        grid_resolution = max(grid_resolution, 400)   # Minimum 400 for acceptable quality

        # Terrain sampling parameters
        base_azimuths = 3600  # Always use 3600 for smoothness
        base_distances = 1500  # Base distance samples

        scaled_azimuths = base_azimuths  # Keep azimuths locked at 3600
        scaled_distances = int(base_distances * combined_multiplier)
        scaled_distances = min(scaled_distances, 8000)  # Cap at 8000
        scaled_distances = max(scaled_distances, 800)   # Minimum 800

        scaled_quality = {
            'azimuths': scaled_azimuths,
            'distances': scaled_distances
        }

        return grid_resolution, scaled_quality

    def calculate_coverage(self, tx_lat, tx_lon, tx_height, erp_dbm, frequency_mhz,
                          max_distance_km, resolution, signal_threshold_dbm, rx_height=1.5,
                          use_terrain=False, terrain_quality='Medium',
                          custom_azimuth_count=None, custom_distance_points=None,
                          propagation_model='default', progress_callback=None, zoom_level=11,
                          antenna_bearing=0.0, antenna_downtilt=0.0):
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
            propagation_model: Propagation model ('default' for FSPL+diffraction, 'longley_rice' for Longley-Rice)
            antenna_bearing: Antenna bearing in degrees (0=North, clockwise) for directional antennas
            antenna_downtilt: Antenna downtilt in degrees (positive=down) for directional antennas

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
            eirp_dbm = PropagationModel.erp_to_eirp(erp_dbm, self.antenna_pattern.max_gain)
            print(f"EIRP: {eirp_dbm:.2f} dBm")
            
            # =================================================================================
            # ZOOM-AWARE QUALITY SCALING
            # =================================================================================
            # Auto-adjust grid resolution, azimuths, and distance points based on:
            # 1. User's quality selection (Low/Medium/High/Ultra)
            # 2. Current zoom level (higher zoom = more detail needed)
            # 3. Coverage distance (larger area = coarser acceptable)
            # =================================================================================
            grid_resolution, scaled_quality = self._calculate_zoom_aware_parameters(
                terrain_quality, zoom_level, max_distance_km
            )

            print(f"Quality: {terrain_quality} (zoom {zoom_level}) → Grid: {grid_resolution}x{grid_resolution} (~{2*max_distance_km/grid_resolution:.2f} km/pixel)")
            # =================================================================================
            # END ZOOM-AWARE SCALING
            # =================================================================================

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

            # Apply scaled quality parameters if custom values not provided
            if custom_azimuth_count is None and custom_distance_points is None:
                custom_azimuth_count = scaled_quality['azimuths']
                custom_distance_points = scaled_quality['distances']
                print(f"Using scaled quality: {custom_azimuth_count} az × {custom_distance_points} dist (quality={terrain_quality}, zoom={zoom_level})")

            print(f"Coverage area: {np.sum(~mask)} points within {max_distance_km} km")
            
            # Calculate antenna gains (with bearing and downtilt for directional antennas)
            print(f"Calculating antenna gains... (bearing: {antenna_bearing:.1f}°, downtilt: {antenna_downtilt:.1f}°)")
            gain_grid = np.zeros_like(az_grid)

            # Calculate elevation angles based on geometry (height difference over distance)
            # Height difference: tx_height - rx_height (usually positive, TX is higher)
            height_diff_m = tx_height - rx_height

            for i in range(az_grid.shape[0]):
                for j in range(az_grid.shape[1]):
                    if not mask[i, j]:
                        # Apply bearing offset: the antenna's 0° (main lobe) points in the bearing direction
                        # So we subtract bearing from the geographic azimuth to get antenna-relative angle
                        antenna_relative_az = (az_grid[i, j] - antenna_bearing) % 360

                        # Calculate geometric elevation angle to this point
                        # elevation = atan(height_diff / distance)
                        # Negative elevation = looking down (toward ground)
                        dist_m = dist_grid[i, j] * 1000  # km to m
                        if dist_m > 0:
                            geometric_elevation = np.degrees(np.arctan2(height_diff_m, dist_m))
                        else:
                            geometric_elevation = 0

                        # Apply downtilt: antenna's 0° elevation is tilted down by downtilt degrees
                        # So the effective elevation in antenna coordinates is:
                        # geometric_elevation + downtilt (if downtilt is positive/down)
                        antenna_relative_elev = geometric_elevation + antenna_downtilt

                        gain_grid[i, j] = self.antenna_pattern.get_gain(antenna_relative_az, elevation=antenna_relative_elev)
            
            print(f"Gain range: {gain_grid[~mask].min():.2f} to {gain_grid[~mask].max():.2f} dBi")
            
            # Calculate free space path loss
            print(f"Calculating path loss...")
            fspl_grid = PropagationModel.free_space_loss(dist_grid, frequency_mhz)
            fspl_grid[mask] = 0
            
            debug_msg = f"FSPL range: {fspl_grid[~mask].min():.2f} to {fspl_grid[~mask].max():.2f} dB"
            print(debug_msg)
            self._log_debug(debug_msg)
            
            # =================================================================================
            # PROPAGATION MODEL SELECTION
            # =================================================================================
            # Choose between default (FSPL + diffraction) or Longley-Rice model
            # ROLLBACK: Remove this block to revert to default model only
            # =================================================================================

            total_loss_grid = np.zeros_like(dist_grid)

            if propagation_model == 'longley_rice':
                print(f"Using Longley-Rice propagation model...")
                if grid_resolution > 200:
                    print("Warning: Longley-Rice calculations may be slow for high resolution grids")

                # Calculate Longley-Rice loss for each point
                for i in range(dist_grid.shape[0]):
                    for j in range(dist_grid.shape[1]):
                        if not mask[i, j] and dist_grid[i, j] > 0:
                            try:
                                total_loss_grid[i, j] = PropagationModel.longley_rice_loss(
                                    dist_grid[i, j], frequency_mhz, tx_height, rx_height
                                )
                            except Exception as e:
                                print(f"Warning: Longley-Rice failed at point ({i},{j}): {e}")
                                # Fallback to FSPL
                                total_loss_grid[i, j] = PropagationModel.free_space_loss(
                                    dist_grid[i, j], frequency_mhz
                                )

                # Still calculate terrain diffraction if enabled and add to total loss
                terrain_loss_grid = np.zeros_like(dist_grid)
                if use_terrain:
                    # =================================================================================
                    # TERRAIN ACCURACY IMPROVEMENT FOR LARGE AREAS
                    # =================================================================================
                    # Scale terrain sampling points with coverage distance for consistent accuracy
                    # at all zoom levels. More points = better resolution but slower calculation.
                    # High-accuracy mode: 2200 base points, up to 3300 max
                    # ROLLBACK: Reduce base_points to 500 and cap to 1000
                    # =================================================================================
                    if custom_distance_points is None:
                        # Use quality preset values, scale up slightly for very large areas
                        quality_distance_presets = {
                            'Low': 1000,
                            'Medium': 2200,
                            'High': 4000,
                            'Ultra': 5000,
                        }
                        base_points = quality_distance_presets.get(terrain_quality, 2200)

                        # Scale up for very large coverage areas (>200km)
                        if max_distance_km > 200:
                            scale_factor = min(1.0 + (max_distance_km - 200) / 400, 1.5)  # Up to 1.5x for 400km+
                            custom_distance_points = min(int(base_points * scale_factor), 10000)  # Cap at 10k
                        else:
                            custom_distance_points = base_points

                        print(f"Scaled terrain points to {custom_distance_points} for {max_distance_km}km coverage")

                    terrain_loss_grid = self._calculate_terrain_loss(
                        tx_lat, tx_lon, tx_height, rx_height, max_distance_km,
                        frequency_mhz, terrain_quality,
                        custom_azimuth_count, custom_distance_points,
                        mask, dist_grid, az_grid, x_grid, y_grid,
                        progress_callback
                    )
                    total_loss_grid += terrain_loss_grid

                    # =================================================================================
                    # CLAMP TERRAIN LOSS TO PREVENT NEGATIVE VALUES
                    # =================================================================================
                    # Ensure no negative terrain loss (gain) for realistic modeling
                    # ROLLBACK: Remove this line
                    # =================================================================================
                    total_loss_grid = np.maximum(total_loss_grid, fspl_grid)  # At least FSPL
                    # =================================================================================
                    # END TERRAIN ACCURACY IMPROVEMENT
                    # =================================================================================

            else:  # Default model (FSPL + diffraction)
                print(f"Using default propagation model (FSPL + diffraction)...")

                # Terrain analysis
                terrain_loss_grid = np.zeros_like(dist_grid)
                if use_terrain:
                    # =================================================================================
                    # TERRAIN ACCURACY IMPROVEMENT FOR LARGE AREAS
                    # =================================================================================
                    # Scale terrain sampling points with coverage distance for consistent accuracy
                    # at all zoom levels. More points = better resolution but slower calculation.
                    # High-accuracy mode: 2200 base points, up to 3300 max
                    # ROLLBACK: Reduce base_points to 500 and cap to 1000
                    # =================================================================================
                    if custom_distance_points is None:
                        # Use quality preset values, scale up slightly for very large areas
                        quality_distance_presets = {
                            'Low': 1000,
                            'Medium': 2200,
                            'High': 4000,
                            'Ultra': 5000,
                        }
                        base_points = quality_distance_presets.get(terrain_quality, 2200)

                        # Scale up for very large coverage areas (>200km)
                        if max_distance_km > 200:
                            scale_factor = min(1.0 + (max_distance_km - 200) / 400, 1.5)  # Up to 1.5x for 400km+
                            custom_distance_points = min(int(base_points * scale_factor), 10000)  # Cap at 10k
                        else:
                            custom_distance_points = base_points

                        print(f"Scaled terrain points to {custom_distance_points} for {max_distance_km}km coverage")

                    terrain_loss_grid = self._calculate_terrain_loss(
                        tx_lat, tx_lon, tx_height, rx_height, max_distance_km,
                        frequency_mhz, terrain_quality,
                        custom_azimuth_count, custom_distance_points,
                        mask, dist_grid, az_grid, x_grid, y_grid,
                        progress_callback
                    )
                    # =================================================================================
                    # END TERRAIN ACCURACY IMPROVEMENT
                    # =================================================================================

                # Total loss = FSPL + terrain diffraction
                total_loss_grid = fspl_grid + terrain_loss_grid

                # =================================================================================
                # CLAMP TERRAIN LOSS TO PREVENT NEGATIVE VALUES
                # =================================================================================
                # Ensure no negative terrain loss (gain) for realistic modeling
                # ROLLBACK: Remove this line
                # =================================================================================
                total_loss_grid = np.maximum(total_loss_grid, fspl_grid)  # At least FSPL

            # =================================================================================
            # END PROPAGATION MODEL SELECTION
            # =================================================================================

            # Calculate received power
            rx_power_grid = eirp_dbm + gain_grid - total_loss_grid
            
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

            # Return Cartesian grids (x_grid, y_grid) for direct plotting
            # This avoids double polar-to-Cartesian conversion in the plotter
            return x_grid, y_grid, rx_power_grid, terrain_loss_grid, stats
            
        except Exception as e:
            print(f"\nERROR in calculate_coverage: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_terrain_loss(self, tx_lat, tx_lon, tx_height, rx_height, max_distance_km,
                                frequency_mhz, terrain_quality, custom_azimuth_count,
                                custom_distance_points, mask, dist_grid, az_grid, x_grid, y_grid,
                                progress_callback=None):
        """Calculate terrain diffraction loss with segment-by-segment LOS
        
        🔥 FIX #2: This uses 360° azimuth sampling to eliminate radial artifacts
        🔥 FIX #3: This uses segment-by-segment terrain diffraction (no shadow tunneling!)
        
        Args:
            tx_lat, tx_lon: Transmitter location
            tx_height: Transmitter height AGL (m)
            rx_height: Receiver height AGL (m)
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
        
        # =================================================================================
        # FORCE 3600 AZIMUTH SAMPLING FOR SMOOTH INTERPOLATION
        # =================================================================================
        # ALWAYS use 3600 azimuths (0.1° resolution) to eliminate blocky square artifacts
        # This is locked and cannot be overridden by user settings
        # Only distance points vary based on quality/custom settings
        # =================================================================================
        LOCKED_AZIMUTH_COUNT = 3600  # Every 0.1 degree - NEVER CHANGE THIS

        # Quality presets for DISTANCE POINTS ONLY (azimuths are locked at 3600)
        # These control terrain elevation sampling density along each radial
        quality_distance_presets = {
            'Low': 1000,      # Fast, basic accuracy
            'Medium': 2200,   # Good accuracy, reasonable speed
            'High': 4000,     # High accuracy, slower
            'Ultra': 5000,    # MAXIMUM accuracy, slowest (perfect detail)
        }

        # Get distance sampling parameter
        if custom_distance_points is not None:
            sample_distances_count = custom_distance_points
            print(f"Using CUSTOM distance sampling: {sample_distances_count} pts (azimuth locked at {LOCKED_AZIMUTH_COUNT})")
        else:
            sample_distances_count = quality_distance_presets.get(terrain_quality, 2200)
            print(f"Using {terrain_quality} quality: {sample_distances_count} distance pts (azimuth locked at {LOCKED_AZIMUTH_COUNT})")

        # FORCE azimuth count - user cannot override this
        sample_azimuths_count = LOCKED_AZIMUTH_COUNT

        self._log_debug(f"Terrain sampling: {sample_azimuths_count} azimuths × {sample_distances_count} distances")
        # =================================================================================
        # END FORCED AZIMUTH SAMPLING
        # =================================================================================
        
        # Sample terrain at specific azimuths (polar sampling for efficiency)
        sample_azimuths = np.linspace(0, 360, sample_azimuths_count, endpoint=False)
        sample_distances = np.linspace(0.1, max_distance_km, sample_distances_count)
        
        terrain_loss_samples = np.zeros((sample_distances_count, sample_azimuths_count))
        
        # rx_height is passed as parameter
        
        # =================================================================================
        # VERBOSE PROGRESS LOGGING (overwrites same line)
        # =================================================================================
        import sys
        for i, az in enumerate(sample_azimuths):
            # Print progress on same line (overwriting) - updates every azimuth
            percent = int(100 * (i + 1) / sample_azimuths_count)
            sys.stdout.write(f"\r  Terrain calculation: {percent:3d}% | Azimuth: {az:6.1f}° ({i+1:4d}/{sample_azimuths_count})  ")
            sys.stdout.flush()

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

            # Progressive rendering: invoke callback every 10% completion
            if progress_callback and i % max(1, sample_azimuths_count // 10) == 0:
                progress_percent = int(100 * (i + 1) / sample_azimuths_count)
                progress_callback(progress_percent, terrain_loss_samples[:, :i+1],
                                sample_distances, sample_azimuths[:i+1])

        # Print newline after progress completes
        print()  # Move to next line after overwriting progress
        print(f"Interpolating terrain loss to Cartesian grid...")
        
        # Convert polar samples to Cartesian coordinates for proper interpolation
        # Create sample points in Cartesian space
        sample_x = []
        sample_y = []
        sample_loss = []
        
        for i, dist in enumerate(sample_distances):
            for j, azimuth in enumerate(sample_azimuths):
                # Convert polar (distance, azimuth) to Cartesian (x, y)
                # Azimuth measured clockwise from North
                x = dist * np.sin(np.radians(azimuth))
                y = dist * np.cos(np.radians(azimuth))
                sample_x.append(x)
                sample_y.append(y)
                sample_loss.append(terrain_loss_samples[i, j])
        
        # Stack into array for griddata
        points = np.column_stack([sample_x, sample_y])
        values = np.array(sample_loss)
        
        # Use the original Cartesian grids passed from calculate_coverage
        # This avoids polar-to-Cartesian conversion artifacts
        # (x_grid and y_grid are now function parameters)
        
        # Flatten the Cartesian grid for interpolation
        grid_points = np.column_stack([x_grid.flatten(), y_grid.flatten()])
        
        # =================================================================================
        # LINEAR INTERPOLATION (FAST AND ACCURATE)
        # =================================================================================
        # Linear interpolation is MUCH faster than cubic and produces great results
        # with 3600 azimuth sampling. Cubic was tested and found to be:
        #   - 40+ minutes for 1M grid points (vs. seconds for linear)
        #   - Minimal visual improvement over linear
        #   - Risk of phantom coverage in shadow zones
        # With high-res terrain cache (0.0001° = 11m) + 3600 azimuths, linear is optimal
        # ROLLBACK: Change 'linear' to 'cubic' to re-enable (not recommended)
        # =================================================================================
        from scipy.interpolate import griddata

        grid_res = dist_grid.shape[0]
        print(f"  Using linear interpolation on {grid_res}x{grid_res} grid ({len(points)} samples -> {len(grid_points)} points)...")

        terrain_loss_flat = griddata(points, values, grid_points, method='linear', fill_value=0.0)

        # Handle any NaNs (shouldn't happen with linear, but just in case)
        if np.any(np.isnan(terrain_loss_flat)):
            print(f"  Warning: Linear produced NaNs, filling with nearest neighbor")
            nan_mask = np.isnan(terrain_loss_flat)
            terrain_loss_flat[nan_mask] = griddata(points, values, grid_points[nan_mask],
                                                   method='nearest', fill_value=0.0)

        print(f"  ✓ Linear interpolation complete")
        # =================================================================================
        # END LINEAR INTERPOLATION
        # =================================================================================
        
        # Reshape back to grid
        terrain_loss_grid = terrain_loss_flat.reshape(dist_grid.shape)

        # =================================================================================
        # CLAMP TERRAIN LOSS TO PREVENT NEGATIVE VALUES (INTERPOLATION ARTIFACTS)
        # =================================================================================
        # Cubic interpolation can produce negative values between sample points
        # Terrain should never provide gain, only loss (minimum 0 dB)
        # ROLLBACK: Remove this line
        # =================================================================================
        terrain_loss_grid = np.maximum(terrain_loss_grid, 0)  # No negative terrain loss
        # =================================================================================

        # Ensure masked areas stay zero
        terrain_loss_grid[mask] = 0

        terrain_msg = f"Terrain loss range: {terrain_loss_grid[~mask].min():.2f} to {terrain_loss_grid[~mask].max():.2f} dB"
        print(terrain_msg)
        self._log_debug(terrain_msg)

        return terrain_loss_grid
