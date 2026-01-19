"""
Propagation Plot Module
=======================
Handles coverage overlay plotting on maps with proper colormaps and legends.

This module contains all the logic for rendering RF propagation coverage overlays,
including the custom colormap, contour plotting, and shadow zone visualization.
"""

import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
import scipy.ndimage


class PropagationPlot:
    """Manages propagation coverage overlay rendering"""
    
    def __init__(self, ax, canvas, fig):
        """Initialize propagation plotter
        
        Args:
            ax: Matplotlib axis for rendering
            canvas: Matplotlib canvas for drawing
            fig: Matplotlib figure (for colorbar)
        """
        self.ax = ax
        self.canvas = canvas
        self.fig = fig
        self.colorbar = None
        
        # Create signal strength colormap (Blue->Cyan->Green->Yellow->Red)
        self.signal_cmap = LinearSegmentedColormap.from_list(
            'signal_strength',
            [
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
            ],
            N=256
        )
    
    def plot_coverage(self, map_image, tx_pixel_x, tx_pixel_y, 
                     az_grid, dist_grid, rx_power_grid, 
                     signal_threshold, pixel_scale,
                     terrain_loss_grid=None, show_shadow=False,
                     zoom_state=None, alpha=0.65):
        """Plot propagation coverage overlay on map
        
        Args:
            map_image: PIL Image of the map
            tx_pixel_x: Transmitter X pixel position
            tx_pixel_y: Transmitter Y pixel position
            az_grid: Azimuth grid (degrees)
            dist_grid: Distance grid (km)
            rx_power_grid: Received power grid (dBm)
            signal_threshold: Minimum signal threshold (dBm)
            pixel_scale: Pixels per km
            terrain_loss_grid: Optional terrain loss grid for shadow zones
            show_shadow: Whether to show shadow zones
            zoom_state: Tuple of (xlim, ylim) or None for full view
            alpha: Transparency of coverage overlay (0.0-1.0, default 0.65)
        """
        self.ax.clear()
        
        if map_image:
            # Display map
            self.ax.imshow(map_image, extent=[0, map_image.size[0], map_image.size[1], 0])
            
            # Convert distance/azimuth to pixel coordinates
            az_rad = np.deg2rad(az_grid)
            x = tx_pixel_x + dist_grid * pixel_scale * np.sin(az_rad)
            y = tx_pixel_y - dist_grid * pixel_scale * np.cos(az_rad)
            
            # =================================================================================
            # SMOOTHING FOR REDUCED GRID CHUNKING
            # =================================================================================
            # Apply Gaussian smoothing to reduce visible grid artifacts at low zoom
            # Sigma=0.5 provides subtle smoothing without losing detail
            # ROLLBACK: Remove this block
            # =================================================================================
            rx_power_smoothed = scipy.ndimage.gaussian_filter(rx_power_grid, sigma=0.5)
            # =================================================================================
            # END SMOOTHING
            # =================================================================================

            # Mask areas below threshold
            rx_power_masked = np.ma.masked_where(rx_power_smoothed < signal_threshold, rx_power_smoothed)

            # Create contour plot if we have valid data
            max_power = float(rx_power_masked.max())
            min_power = float(max(rx_power_masked.min(), signal_threshold))
            
            if max_power > min_power + 1:  # At least 1 dB difference
                levels = np.linspace(min_power, max_power, 60)
                
                print(f"DEBUG: Plotting contours - {np.sum(~rx_power_masked.mask)} valid points")
                print(f"DEBUG: Power range: {min_power:.1f} to {max_power:.1f} dBm")
                
                contour = self.ax.contourf(x, y, rx_power_masked, 
                                          levels=levels, 
                                          cmap=self.signal_cmap, 
                                          alpha=alpha, 
                                          extend='neither', 
                                          antialiased=True)
                
                # Update colorbar
                if self.colorbar is not None:
                    try:
                        self.colorbar.remove()
                    except:
                        pass
                
                self.colorbar = self.fig.colorbar(contour, ax=self.ax, 
                                                 pad=0.01, fraction=0.03, aspect=30)
                self.colorbar.set_label('Signal Strength (dBm)', 
                                       rotation=270, labelpad=15, fontsize=9)
                self.colorbar.ax.tick_params(labelsize=8)
            else:
                print("Warning: Insufficient signal range for contour plot")
            
            # Show shadow zones if requested
            if show_shadow and terrain_loss_grid is not None:
                shadow_mask = terrain_loss_grid > 40  # Severe obstruction
                if np.any(shadow_mask):
                    shadow_overlay = np.ma.masked_where(~shadow_mask, terrain_loss_grid)
                    self.ax.contourf(x, y, shadow_overlay, 
                                   levels=[40, 100], 
                                   colors=['red'], 
                                   alpha=0.15, 
                                   hatches=['///'])
                    
                    # Add legend entry for shadow zones
                    shadow_patch = Patch(facecolor='red', alpha=0.15, 
                                       hatch='///', label='Shadow Zone (>40dB loss)')
                    handles, labels = self.ax.get_legend_handles_labels()
                    handles.append(shadow_patch)
            
            # Mark transmitter
            self.ax.plot(tx_pixel_x, tx_pixel_y, 'r^', markersize=15,
                        markeredgecolor='white', markeredgewidth=2, 
                        label='Transmitter', zorder=10)
            
            # Force axes to map boundaries to prevent resizing
            self.ax.set_xlim(0, map_image.size[0])
            self.ax.set_ylim(map_image.size[1], 0)
            self.ax.set_aspect('equal', adjustable='box')  # Maintain aspect ratio

            self.ax.axis('off')
            self.ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
        
        self.canvas.draw()
    
    def clear_overlay(self):
        """Remove propagation overlay, keeping only the map"""
        # Colorbar removal is handled when new overlay is plotted
        pass
    
    def get_signal_at_pixel(self, pixel_x, pixel_y, tx_pixel_x, tx_pixel_y,
                           az_grid, dist_grid, rx_power_grid, pixel_scale):
        """Interpolate signal strength at a specific pixel location
        
        Args:
            pixel_x: Query pixel X coordinate
            pixel_y: Query pixel Y coordinate
            tx_pixel_x: Transmitter pixel X
            tx_pixel_y: Transmitter pixel Y
            az_grid: Azimuth grid
            dist_grid: Distance grid
            rx_power_grid: Power grid
            pixel_scale: Pixels per km
            
        Returns:
            Tuple of (signal_strength_dbm, distance_km, azimuth_deg) or (None, None, None)
        """
        try:
            # Calculate distance and azimuth from transmitter
            dx = pixel_x - tx_pixel_x
            dy = tx_pixel_y - pixel_y  # Flip y axis
            
            distance_pixels = np.sqrt(dx**2 + dy**2)
            distance_km = distance_pixels / pixel_scale
            
            azimuth = np.degrees(np.arctan2(dx, dy)) % 360
            
            # Find nearest point in grid
            az_idx = np.argmin(np.abs(az_grid[0, :] - azimuth))
            dist_idx = np.argmin(np.abs(dist_grid[:, 0] - distance_km))
            
            if dist_idx < rx_power_grid.shape[0] and az_idx < rx_power_grid.shape[1]:
                signal_strength = rx_power_grid[dist_idx, az_idx]
                return signal_strength, distance_km, azimuth
            else:
                return None, None, None
                
        except Exception as e:
            print(f"Error interpolating signal: {e}")
            return None, None, None
