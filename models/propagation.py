"""
RF Propagation models and calculations
"""
import numpy as np

class PropagationModel:
    """RF Propagation calculations with terrain awareness"""
    
    @staticmethod
    def free_space_loss(distance_km, frequency_mhz):
        """Calculate free space path loss in dB
        FSPL(dB) = 32.45 + 20*log10(dist_km) + 20*log10(freq_MHz)
        """
        result = np.where(distance_km > 0, 
                         32.45 + 20 * np.log10(distance_km) + 20 * np.log10(frequency_mhz),
                         0)
        return result
    
    @staticmethod
    def terrain_diffraction_loss(tx_height, rx_height, terrain_profile, frequency_mhz):
        """Calculate additional loss due to terrain obstacles using knife-edge diffraction
        
        Args:
            tx_height: transmitter height above ground (m)
            rx_height: receiver height above ground (m)
            terrain_profile: array of elevations along path (m)
            frequency_mhz: frequency in MHz
            
        Returns:
            Additional loss in dB due to terrain diffraction
        """
        if len(terrain_profile) < 2:
            return 0
        
        wavelength = 300 / frequency_mhz
        
        tx_elev = terrain_profile[0] + tx_height
        rx_elev = terrain_profile[-1] + rx_height
        
        path_length = len(terrain_profile)
        los_line = np.linspace(tx_elev, rx_elev, path_length)
        
        clearances = (terrain_profile - los_line)
        max_obstruction = np.max(clearances)
        
        if max_obstruction <= 0:
            return 0
        
        # Fresnel-Kirchhoff diffraction parameter
        v = max_obstruction * np.sqrt(2 / wavelength)
        
        if v <= -0.8:
            loss = 0
        elif v <= 0:
            loss = 6.9 + 20 * np.log10(np.sqrt((v - 0.1)**2 + 1) + v - 0.1)
        elif v <= 1:
            loss = 6.9 + 20 * np.log10(np.sqrt((v - 0.1)**2 + 1) + v - 0.1)
        elif v <= 2.4:
            loss = 6.9 + 20 * np.log10(np.sqrt((v - 0.1)**2 + 1) + v - 0.1)
        else:
            loss = 13 + 20 * np.log10(v)
        
        return max(0, loss)
    
    @staticmethod
    def erp_to_eirp(erp_dbm):
        """Convert ERP to EIRP (add 2.15 dB for dipole reference)"""
        return erp_dbm + 2.15