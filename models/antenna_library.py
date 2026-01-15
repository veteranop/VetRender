"""
Antenna Library Management
Stores and manages imported antenna patterns with metadata
"""
import json
import os
import shutil
from pathlib import Path


class AntennaLibrary:
    """Manages saved antenna patterns and their metadata"""
    
    LIBRARY_DIR = "antenna_library"
    LIBRARY_INDEX = "antenna_library/index.json"
    
    def __init__(self):
        """Initialize antenna library"""
        # Create library directory if it doesn't exist
        os.makedirs(self.LIBRARY_DIR, exist_ok=True)
        
        # Load or create index
        self.antennas = self.load_index()
    
    def load_index(self):
        """Load antenna index from file"""
        if os.path.exists(self.LIBRARY_INDEX):
            try:
                with open(self.LIBRARY_INDEX, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading antenna index: {e}")
                return {}
        return {}
    
    def save_index(self):
        """Save antenna index to file"""
        try:
            with open(self.LIBRARY_INDEX, 'w') as f:
                json.dump(self.antennas, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving antenna index: {e}")
            return False
    
    def add_antenna(self, name, xml_content, metadata=None):
        """Add a new antenna to the library
        
        Args:
            name: Unique name for the antenna
            xml_content: XML pattern data as string
            metadata: Dict with manufacturer, part_number, gain, band, etc.
        
        Returns:
            bool: Success status
        """
        if metadata is None:
            metadata = {}
        
        # Create safe filename
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_')
        
        # Generate unique ID
        antenna_id = f"{safe_name}_{len(self.antennas)}"
        xml_filename = f"{antenna_id}.xml"
        xml_path = os.path.join(self.LIBRARY_DIR, xml_filename)
        
        # Save XML file
        try:
            with open(xml_path, 'w') as f:
                f.write(xml_content)
        except Exception as e:
            print(f"Error saving antenna XML: {e}")
            return False
        
        # Add to index
        self.antennas[antenna_id] = {
            'name': name,
            'xml_file': xml_filename,
            'manufacturer': metadata.get('manufacturer', 'Unknown'),
            'part_number': metadata.get('part_number', 'N/A'),
            'gain': metadata.get('gain', 0),
            'band': metadata.get('band', 'N/A'),
            'frequency_range': metadata.get('frequency_range', 'N/A'),
            'type': metadata.get('type', 'Omni'),
            'notes': metadata.get('notes', ''),
            'import_date': metadata.get('import_date', '')
        }
        
        self.save_index()
        return True
    
    def get_antenna(self, antenna_id):
        """Get antenna metadata by ID"""
        return self.antennas.get(antenna_id)
    
    def get_antenna_xml_path(self, antenna_id):
        """Get full path to antenna XML file"""
        antenna = self.get_antenna(antenna_id)
        if antenna:
            return os.path.join(self.LIBRARY_DIR, antenna['xml_file'])
        return None
    
    def list_antennas(self):
        """Get list of all antennas
        
        Returns:
            List of tuples: [(antenna_id, name), ...]
        """
        return [(aid, data['name']) for aid, data in self.antennas.items()]
    
    def delete_antenna(self, antenna_id):
        """Delete an antenna from the library
        
        Args:
            antenna_id: ID of antenna to delete
            
        Returns:
            bool: Success status
        """
        antenna = self.get_antenna(antenna_id)
        if not antenna:
            return False
        
        # Delete XML file
        xml_path = os.path.join(self.LIBRARY_DIR, antenna['xml_file'])
        try:
            if os.path.exists(xml_path):
                os.remove(xml_path)
        except Exception as e:
            print(f"Error deleting antenna XML: {e}")
            return False
        
        # Remove from index
        del self.antennas[antenna_id]
        self.save_index()
        return True
    
    def get_antenna_info_text(self, antenna_id):
        """Get formatted antenna information for display
        
        Args:
            antenna_id: ID of antenna
            
        Returns:
            str: Formatted info text
        """
        antenna = self.get_antenna(antenna_id)
        if not antenna:
            return "No antenna selected"
        
        info = f"Manufacturer: {antenna['manufacturer']}\n"
        info += f"Part Number: {antenna['part_number']}\n"
        info += f"Gain: {antenna['gain']} dBi\n"
        info += f"Band: {antenna['band']}\n"
        info += f"Frequency: {antenna['frequency_range']}\n"
        info += f"Type: {antenna['type']}"
        
        if antenna['notes']:
            info += f"\nNotes: {antenna['notes']}"
        
        return info
