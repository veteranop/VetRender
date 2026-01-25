"""
Antenna pattern handling and interpolation
"""
import xml.etree.ElementTree as ET

class AntennaPattern:
    """Handles antenna pattern data from XML"""
    def __init__(self):
        self.azimuth_pattern = {}
        self.elevation_pattern = {}
        self.max_gain = 0
        self.load_default_omni()
        
    def load_default_omni(self):
        """Load default omnidirectional antenna pattern (0 dBi gain)"""
        for angle in range(0, 360, 1):
            self.azimuth_pattern[angle] = 0.0
        for angle in range(-90, 91, 1):
            self.elevation_pattern[angle] = 0.0
        self.max_gain = 0.0
        
    def load_from_xml(self, filepath):
        """Load antenna pattern from XML file"""
        try:
            tree = ET.parse(filepath)
            root = tree.getroot()
            
            self.azimuth_pattern = {}
            self.elevation_pattern = {}
            
            for elem in root.iter():
                if 'azimuth' in elem.tag.lower():
                    for child in elem:
                        angle = float(child.get('angle', child.get('deg', 0)))
                        gain = float(child.get('gain', child.get('db', 0)))
                        self.azimuth_pattern[angle] = gain
                        
                if 'elevation' in elem.tag.lower():
                    for child in elem:
                        angle = float(child.get('angle', child.get('deg', 0)))
                        gain = float(child.get('gain', child.get('db', 0)))
                        self.elevation_pattern[angle] = gain
            
            if self.azimuth_pattern:
                self.max_gain = max(self.azimuth_pattern.values())
            
            return True
        except Exception as e:
            print(f"Error loading XML: {e}")
            return False
    
    def get_gain(self, azimuth, elevation=0):
        """Get antenna gain for a given azimuth and elevation angle.

        Returns absolute gain in dBi:
        - max_gain is the peak antenna gain (dBi)
        - az_gain is the relative azimuth pattern (0 dB at boresight, negative off-axis)
        - el_gain is the relative elevation pattern (0 dB at boresight, negative off-axis)

        Absolute gain = max_gain + az_relative + el_relative
        """
        az_gain = self._interpolate_pattern(self.azimuth_pattern, azimuth)
        el_gain = self._interpolate_pattern(self.elevation_pattern, elevation)

        # Start with max gain (peak gain at boresight)
        total_gain = self.max_gain

        # Add relative pattern losses (az_gain and el_gain are 0 or negative)
        if az_gain is not None:
            total_gain += az_gain
        if el_gain is not None:
            total_gain += el_gain

        return total_gain
    
    def _interpolate_pattern(self, pattern, angle):
        """Interpolate gain from pattern dictionary"""
        if not pattern:
            return None
            
        if angle < 0:
            angle = max(-90, min(90, angle))
        else:
            angle = angle % 360
        
        if angle in pattern:
            return pattern[angle]
        
        angles = sorted(pattern.keys())
        lower = max([a for a in angles if a <= angle], default=angles[-1])
        upper = min([a for a in angles if a > angle], default=angles[0])
        
        if lower == upper:
            return pattern[lower]
        
        if upper < lower and angle >= 0:
            upper += 360
            if angle < lower:
                angle += 360
        
        if upper != lower:
            ratio = (angle - lower) / (upper - lower)
            gain = pattern[lower] + ratio * (pattern[upper % 360 if angle >= 0 else upper] - pattern[lower])
        else:
            gain = pattern[lower]
        
        return gain