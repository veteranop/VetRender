# CORRECTED calculate_propagation function - Works WITHOUT scipy
# Replace the existing function in main_window.py with this version

def calculate_propagation(self):
    """Calculate and overlay propagation on map using Cartesian grid to eliminate radial artifacts"""
    try:
        # Get max distance from UI
        try:
            self.max_distance = float(self.max_dist_var.get())
        except ValueError:
            self.max_distance = 100
            self.max_dist_var.set("100")
        
        print(f"\n{'='*60}")
        print(f"CALCULATING PROPAGATION - CARTESIAN GRID")
        print(f"{'='*60}")
        print(f"Transmitter Location: Lat={self.tx_lat:.6f}, Lon={self.tx_lon:.6f}")
        print(f"ERP: {self.erp} dBm")
        print(f"Frequency: {self.frequency} MHz")
        print(f"Antenna Height: {self.height} m")
        print(f"Max Distance: {self.max_distance} km")
        print(f"Resolution: {self.resolution} points")
        print(f"Antenna Pattern: {self.pattern_name}")
        print(f"Use Terrain: {self.use_terrain.get()}")
        
        self.status_var.set("Calculating propagation...")
        self.root.update()
        
        eirp_dbm = PropagationModel.erp_to_eirp(self.erp)
        print(f"EIRP: {eirp_dbm:.2f} dBm")
        
        # *** KEY FIX: Create grid in CARTESIAN coordinates (x/y km), not polar (azimuth/distance) ***
        print(f"\nCreating CARTESIAN grid (fixes radial artifacts)...")
        
        # Create square grid in kilometers
        x_km = np.linspace(-self.max_distance, self.max_distance, self.resolution)
        y_km = np.linspace(-self.max_distance, self.max_distance, self.resolution)
        x_grid, y_grid = np.meshgrid(x_km, y_km)
        
        # Calculate distance and azimuth FROM the Cartesian positions
        dist_grid = np.sqrt(x_grid**2 + y_grid**2)
        az_grid = np.degrees(np.arctan2(x_grid, y_grid)) % 360
        
        # Mask points outside max distance (circular coverage)
        mask = dist_grid > self.max_distance
        
        print(f"Grid shape: {x_grid.shape}")
        print(f"Coverage area: {np.sum(~mask)} points within {self.max_distance} km")
        
        print(f"Calculating antenna gains...")
        gain_grid = np.zeros_like(az_grid)
        for i in range(az_grid.shape[0]):
            for j in range(az_grid.shape[1]):
                if not mask[i, j]:
                    gain_grid[i, j] = self.antenna_pattern.get_gain(az_grid[i, j], elevation=0)
        
        print(f"Gain range: {gain_grid[~mask].min():.2f} to {gain_grid[~mask].max():.2f} dBi")
        
        print(f"Calculating path loss...")
        fspl_grid = PropagationModel.free_space_loss(dist_grid, self.frequency)
        fspl_grid[mask] = 0  # Zero out masked areas
        
        terrain_loss_grid = np.zeros_like(dist_grid)
        if self.use_terrain.get():
            print(f"Fetching terrain data...")
            self.status_var.set("Fetching terrain data...")
            self.root.update()

            # Get user-defined granularity
            try:
                sample_azimuths_count = int(self.azimuth_var.get())
                sample_distances_count = int(self.dist_points_var.get())
            except ValueError:
                sample_azimuths_count = 72
                sample_distances_count = 50

            print(f"Terrain sampling: {sample_azimuths_count} azimuths × {sample_distances_count} distances")

            # Sample terrain at specific points (still use polar for efficiency)
            sample_azimuths = np.linspace(0, 360, sample_azimuths_count, endpoint=False)
            sample_distances = np.linspace(0.1, self.max_distance, sample_distances_count)

            terrain_loss_samples = np.zeros((sample_distances_count, sample_azimuths_count))

            for i, az in enumerate(sample_azimuths):
                if i % max(1, sample_azimuths_count // 10) == 0:
                    print(f"  Processing azimuth {az:.0f}° ({i+1}/{len(sample_azimuths)})")

                lat_points = []
                lon_points = []
                for d in sample_distances:
                    lat_offset = d * np.cos(np.radians(az)) / 111.0
                    lon_offset = d * np.sin(np.radians(az)) / (111.0 * np.cos(np.radians(self.tx_lat)))
                    lat_points.append(self.tx_lat + lat_offset)
                    lon_points.append(self.tx_lon + lon_offset)

                elevations = TerrainHandler.get_elevations_batch(list(zip(lat_points, lon_points)))
                rx_height = 10.0

                terrain_loss = np.zeros_like(sample_distances)
                for j, dist in enumerate(sample_distances):
                    terrain_loss[j] = PropagationModel.terrain_diffraction_loss(
                        self.height, rx_height, elevations, self.frequency,
                        np.linspace(0, dist, len(elevations))
                    )

                terrain_loss_samples[:, i] = terrain_loss

            print(f"Interpolating terrain loss to Cartesian grid (using numpy fallback)...")
            
            # Numpy-based interpolation (no scipy required)
            # Wrap azimuth samples for smooth 0/360 boundary
            sample_azimuths_wrap = np.append(sample_azimuths, 360)
            terrain_loss_wrap = np.column_stack([terrain_loss_samples, terrain_loss_samples[:, 0]])
            
            # Interpolate for each point in the Cartesian grid
            for i in range(dist_grid.shape[0]):
                for j in range(dist_grid.shape[1]):
                    if not mask[i, j] and dist_grid[i, j] > 0.1:
                        d = dist_grid[i, j]
                        az = az_grid[i, j]
                        
                        # Find closest sample distances (bilinear interpolation in distance)
                        d_idx = np.searchsorted(sample_distances, d)
                        if d_idx == 0:
                            d_idx = 1
                        if d_idx >= len(sample_distances):
                            d_idx = len(sample_distances) - 1
                        
                        d0, d1 = sample_distances[d_idx-1], sample_distances[d_idx]
                        w_d = (d - d0) / (d1 - d0) if d1 != d0 else 0
                        
                        # Interpolate across azimuths at both distance points
                        loss0 = np.interp(az, sample_azimuths_wrap, terrain_loss_wrap[d_idx-1, :])
                        loss1 = np.interp(az, sample_azimuths_wrap, terrain_loss_wrap[d_idx, :])
                        
                        # Blend between distances
                        terrain_loss_grid[i, j] = loss0 * (1 - w_d) + loss1 * w_d

            print(f"Terrain loss range: {terrain_loss_grid[~mask].min():.2f} to {terrain_loss_grid[~mask].max():.2f} dB")
        
        # Calculate received power
        rx_power_grid = eirp_dbm + gain_grid - fspl_grid - terrain_loss_grid
        rx_power_grid[mask] = -999  # Mark masked areas

        print(f"Path loss range: {(fspl_grid[~mask] + terrain_loss_grid[~mask]).min():.2f} to {(fspl_grid[~mask] + terrain_loss_grid[~mask]).max():.2f} dB")
        print(f"Received power range: {rx_power_grid[~mask].min():.2f} to {rx_power_grid[~mask].max():.2f} dBm")
        
        print(f"Plotting propagation overlay...")
        # NOW pass x_grid, y_grid (Cartesian) instead of az_grid, dist_grid (polar)
        self.plot_propagation_on_map_cartesian(x_grid, y_grid, rx_power_grid, mask, terrain_loss_grid if self.use_terrain.get() else None)

        # Store propagation results - now with Cartesian coordinates and mask
        self.last_propagation = (x_grid, y_grid, rx_power_grid, mask)
        self.last_terrain_loss = terrain_loss_grid if self.use_terrain.get() else None

        # Auto-save this plot
        self.save_current_plot_to_history()

        print(f"{'='*60}")
        print(f"PROPAGATION COMPLETE")
        print(f"{'='*60}\n")

        self.status_var.set(f"Coverage calculated - EIRP: {eirp_dbm:.1f} dBm")
        
    except Exception as e:
        print(f"\nERROR in calculate_propagation:")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Error", f"Calculation error: {e}")
        self.status_var.set("Error in calculation")
