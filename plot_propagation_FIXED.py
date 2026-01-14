# FIXED plot_propagation_on_map function
# Replace the existing function in main_window.py with this version
# Also RENAME the old function from "plot_propagation_on_map" to "plot_propagation_on_map_cartesian"

def plot_propagation_on_map_cartesian(self, x_grid, y_grid, rx_power_grid, mask, terrain_loss_grid=None):
    """Overlay propagation pattern on map using Cartesian coordinates (eliminates radial artifacts)
    
    Args:
        x_grid: X coordinates in km (Cartesian)
        y_grid: Y coordinates in km (Cartesian)
        rx_power_grid: Received power in dBm
        mask: Boolean mask for points outside coverage area
        terrain_loss_grid: Optional terrain loss data
    """
    self.ax.clear()

    if self.map_image:
        self.ax.imshow(self.map_image, extent=[0, self.map_image.size[0], self.map_image.size[1], 0])

        # Get exact transmitter pixel position
        tx_pixel_x, tx_pixel_y = self.get_tx_pixel_position()
        if tx_pixel_x is None:
            tx_pixel_x = self.map_image.size[0] // 2
            tx_pixel_y = self.map_image.size[1] // 2

        # Scale factor: km to pixels
        scale = 30 * (2 ** (self.map_zoom - 13))

        # Convert Cartesian km coordinates to pixel coordinates
        x_pixels = tx_pixel_x + x_grid * scale
        y_pixels = tx_pixel_y - y_grid * scale  # Flip Y axis (screen coords)
        
        # Create custom colormap: Red (strong) -> Yellow -> Green -> Cyan -> Blue (weak)
        colors = [
            '#0000FF',  # Blue (weakest)
            '#0080FF',  # Light blue
            '#00FFFF',  # Cyan
            '#00FF80',  # Cyan-green
            '#00FF00',  # Green
            '#80FF00',  # Yellow-green
            '#FFFF00',  # Yellow (mid)
            '#FFD000',  # Orange-yellow
            '#FFA000',  # Orange
            '#FF6000',  # Red-orange
            '#FF0000',  # Red (strongest)
        ]
        cmap = LinearSegmentedColormap.from_list('signal_strength', colors, N=256)
        
        # Mask areas below threshold AND outside coverage circle
        rx_power_masked = np.ma.masked_where(
            (rx_power_grid < self.signal_threshold) | mask, 
            rx_power_grid
        )
        
        # Create contour levels
        if not np.all(rx_power_masked.mask):  # Check if we have any valid data
            max_power = float(rx_power_masked.max())
            min_power = float(max(rx_power_masked.min(), self.signal_threshold))
            
            if max_power > min_power + 1:  # At least 1 dB difference
                levels = np.linspace(min_power, max_power, 60)  # Smooth gradients
                
                # KEY: Use pcolormesh instead of contourf for Cartesian data - this eliminates radial artifacts!
                contour = self.ax.pcolormesh(x_pixels, y_pixels, rx_power_masked, 
                                            shading='gouraud',  # Smooth interpolation
                                            cmap=cmap, 
                                            alpha=0.65,
                                            vmin=min_power,
                                            vmax=max_power)

                if hasattr(self, 'colorbar') and self.colorbar is not None:
                    try:
                        self.colorbar.remove()
                    except:
                        pass
                self.colorbar = self.fig.colorbar(contour, ax=self.ax, pad=0.01, fraction=0.03, aspect=30)
                self.colorbar.set_label('Signal Strength (dBm)', rotation=270, labelpad=15, fontsize=9)
                self.colorbar.ax.tick_params(labelsize=8)
            else:
                print("Warning: Insufficient signal range for plot")
        else:
            print("Warning: No signal above threshold within coverage area")

        # Show shadow zones if requested
        if self.show_shadow.get() and terrain_loss_grid is not None:
            shadow_mask = (terrain_loss_grid > 40) & (~mask)  # Severe obstruction within coverage
            if np.any(shadow_mask):
                shadow_overlay = np.ma.masked_where(~shadow_mask, terrain_loss_grid)
                self.ax.contourf(x_pixels, y_pixels, shadow_overlay, 
                               levels=[40, 100], colors=['red'], alpha=0.15, hatches=['///'])
                from matplotlib.patches import Patch
                shadow_patch = Patch(facecolor='red', alpha=0.15, hatch='///', label='Shadow Zone')
                handles, labels = self.ax.get_legend_handles_labels()
                handles.append(shadow_patch)
                labels.append('Shadow Zone')
        
        # Mark transmitter at exact position
        self.ax.plot(tx_pixel_x, tx_pixel_y, 'r^', markersize=15,
                    markeredgecolor='white', markeredgewidth=2, label='Transmitter', zorder=10)
        
        # Restore zoom state if user has zoomed
        if self.plot_xlim and self.plot_ylim:
            self.ax.set_xlim(self.plot_xlim)
            self.ax.set_ylim(self.plot_ylim)
        else:
            self.ax.set_xlim(0, self.map_image.size[0])
            self.ax.set_ylim(self.map_image.size[1], 0)

        self.ax.axis('off')
        self.ax.legend(loc='upper right', fontsize=10, framealpha=0.9)

    self.canvas.draw()
