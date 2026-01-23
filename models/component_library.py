"""
Component Library Manager
Loads and manages RF component catalogs for station building
"""

import json
import os
from typing import Dict, List, Optional


class ComponentLibrary:
    """Manages RF component catalogs and lookups"""

    CATALOGS_DIR = "components/catalogs"
    CACHE_DIR = "components/cache"
    CACHE_FILE = "component_cache.json"

    def __init__(self):
        """Initialize component library"""
        self.catalogs = {}
        self.cache = {}
        self._load_catalogs()
        self._load_cache()

    def _load_catalogs(self):
        """Load all manufacturer catalogs"""
        if not os.path.exists(self.CATALOGS_DIR):
            print(f"Warning: Catalogs directory not found: {self.CATALOGS_DIR}")
            return

        for filename in os.listdir(self.CATALOGS_DIR):
            if filename.endswith('.json') and filename != 'manufacturers.json':
                filepath = os.path.join(self.CATALOGS_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        catalog = json.load(f)
                        manufacturer_id = catalog.get('manufacturer_id', filename.replace('.json', ''))
                        self.catalogs[manufacturer_id] = catalog
                        print(f"Loaded catalog: {catalog.get('manufacturer', manufacturer_id)}")
                except Exception as e:
                    print(f"Error loading catalog {filename}: {e}")

    def _load_cache(self):
        """Load component cache"""
        cache_path = os.path.join(self.CACHE_DIR, self.CACHE_FILE)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    self.cache = json.load(f)
                    print(f"Loaded {len(self.cache)} cached components")
            except Exception as e:
                print(f"Error loading cache: {e}")
                self.cache = {}

    def _save_cache(self):
        """Save component cache"""
        os.makedirs(self.CACHE_DIR, exist_ok=True)
        cache_path = os.path.join(self.CACHE_DIR, self.CACHE_FILE)
        try:
            with open(cache_path, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Error saving cache: {e}")

    def search_component(self, query: str, component_type: Optional[str] = None) -> List[Dict]:
        """Search for components by model/part number

        Args:
            query: Search string (model, part number, description)
            component_type: Optional filter by type (cable, connector, isolator, etc.)

        Returns:
            List of matching components
        """
        results = []
        query_lower = query.lower()

        # Search catalogs
        for catalog_id, catalog in self.catalogs.items():
            for component in catalog.get('components', []):
                # Check component type filter
                if component_type and component.get('component_type') != component_type:
                    continue

                # Search in model, part_number, description
                model = component.get('model', '').lower()
                part_num = component.get('part_number', '').lower()
                desc = component.get('description', '').lower()

                if (query_lower in model or
                    query_lower in part_num or
                    query_lower in desc):
                    results.append({
                        **component,
                        'source': catalog.get('manufacturer', catalog_id)
                    })

        # Search cache
        for cached_id, component in self.cache.items():
            # Skip invalid cache entries
            if not isinstance(component, dict):
                continue

            if component_type and component.get('component_type') != component_type:
                continue

            model = component.get('model', '').lower()
            part_num = component.get('part_number', '').lower()
            desc = component.get('description', '').lower()

            if (query_lower in model or
                query_lower in part_num or
                query_lower in desc):
                results.append({
                    **component,
                    'source': 'cached'
                })

        return results

    def get_component_by_model(self, model: str) -> Optional[Dict]:
        """Get exact component by model number

        Args:
            model: Exact model number

        Returns:
            Component dict or None
        """
        # Search catalogs
        for catalog in self.catalogs.values():
            for component in catalog.get('components', []):
                if component.get('model') == model:
                    return component

        # Search cache
        return self.cache.get(model)

    def add_to_cache(self, component: Dict):
        """Add component to cache

        Args:
            component: Component dict with specifications
        """
        model = component.get('model')
        if model:
            self.cache[model] = component
            self._save_cache()

    def get_component_types(self) -> List[str]:
        """Get list of all component types

        Returns:
            Sorted list of unique component types
        """
        types = set()

        for catalog in self.catalogs.values():
            for component in catalog.get('components', []):
                comp_type = component.get('component_type')
                if comp_type:
                    types.add(comp_type)

        for component in self.cache.values():
            # Skip invalid cache entries
            if not isinstance(component, dict):
                continue
            comp_type = component.get('component_type')
            if comp_type:
                types.add(comp_type)

        return sorted(list(types))

    def interpolate_cable_loss(self, cable: Dict, frequency_mhz: float, length_ft: float) -> float:
        """Calculate cable loss at specific frequency and length

        Args:
            cable: Cable component dict
            frequency_mhz: Operating frequency in MHz
            length_ft: Cable length in feet

        Returns:
            Total loss in dB
        """
        loss_data = cable.get('loss_db_per_100ft', {})

        if not loss_data:
            return 0.0

        # Get frequency points and keep original keys for lookup
        freq_map = {float(f): f for f in loss_data.keys()}  # Maps numeric freq to original key
        freqs = sorted(freq_map.keys())

        if not freqs:
            return 0.0

        # Helper function to get loss value by numeric frequency
        def get_loss(freq):
            return loss_data[freq_map[freq]]

        # If frequency is outside range, use nearest
        if frequency_mhz <= freqs[0]:
            loss_per_100ft = get_loss(freqs[0])
        elif frequency_mhz >= freqs[-1]:
            loss_per_100ft = get_loss(freqs[-1])
        else:
            # Linear interpolation
            for i in range(len(freqs) - 1):
                if freqs[i] <= frequency_mhz <= freqs[i + 1]:
                    f1, f2 = freqs[i], freqs[i + 1]
                    loss1 = get_loss(f1)
                    loss2 = get_loss(f2)

                    # Linear interpolation
                    ratio = (frequency_mhz - f1) / (f2 - f1)
                    loss_per_100ft = loss1 + ratio * (loss2 - loss1)
                    break

        # Calculate total loss for length
        total_loss = loss_per_100ft * (length_ft / 100.0)
        return total_loss

    def ollama_search_component(self, query: str, frequency_mhz: float) -> Optional[Dict]:
        """Search for component using Ollama AI

        Args:
            query: Component name, model, or part number
            frequency_mhz: Operating frequency for loss calculations

        Returns:
            Component dict with specifications, or None if not found
        """
        import requests
        import json

        # Construct prompt for Ollama
        prompt = f"""You are an RF component database expert. I need detailed specifications for the following RF component:

Component: {query}
Operating Frequency: {frequency_mhz} MHz

Please provide the component specifications in VALID JSON format with the following structure:
{{
  "model": "exact model number",
  "manufacturer": "manufacturer name (REQUIRED - examples: Times Microwave, Jampro, Nautel, Broadcast Electronics, etc.)",
  "component_type": "cable|transmitter|isolator|circulator|combiner|filter|amplifier|attenuator|passive|connector|duplexer",
  "description": "brief description",
  "part_number": "manufacturer part number",

  // For cables only:
  "loss_db_per_100ft": {{
    "50": 1.0,
    "150": 1.8,
    "220": 2.2,
    "450": 3.0
  }},
  "impedance_ohms": 50,
  "velocity_factor": 0.84,

  // For isolators/circulators:
  "isolation_db": 30.0,
  "insertion_loss_db": 0.2,
  "port_configuration": "3-port",

  // For combiners/filters:
  "insertion_loss_db": 0.5,
  "rejection_db": 40.0,

  // For transmitters:
  "transmit_power_watts": 5000,
  "efficiency_percent": 75,

  // For amplifiers:
  "gain_dbi": 10.0,

  // General:
  "frequency_range_mhz": [50, 1000],
  "power_rating_watts": 100,
  "connector_type": "N-type"
}}

IMPORTANT:
1. Return ONLY valid JSON - no markdown, no code blocks, no explanations
2. Use real specifications from manufacturer datasheets
3. ALWAYS include manufacturer name - this is REQUIRED
4. If the component is a cable, include loss_db_per_100ft with multiple frequency points
5. For isolators/circulators: include isolation_db, insertion_loss_db, port_configuration
6. For transmitters: include transmit_power_watts, efficiency_percent
7. If you cannot find this component, return: {{"error": "Component not found"}}
"""

        try:
            # Query Ollama API
            response = requests.post(
                'http://localhost:11434/api/generate',
                json={
                    'model': 'llama3.2',
                    'prompt': prompt,
                    'stream': False,
                    'format': 'json'
                },
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '')

                # Parse JSON response
                try:
                    component_data = json.loads(response_text)

                    # Check for error
                    if 'error' in component_data:
                        print(f"Ollama: {component_data['error']}")
                        return None

                    # Validate required fields
                    if 'model' in component_data and 'component_type' in component_data:
                        # Add to cache
                        self.add_to_cache(component_data)
                        print(f"Ollama: Found {component_data.get('model')} - {component_data.get('description', 'N/A')}")
                        return component_data
                    else:
                        print("Ollama: Invalid component data (missing required fields)")
                        return None

                except json.JSONDecodeError as e:
                    print(f"Ollama: Failed to parse JSON response: {e}")
                    print(f"Raw response: {response_text[:200]}")
                    return None
            else:
                print(f"Ollama API error: {response.status_code}")
                return None

        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Ollama. Make sure Ollama is running (ollama serve)")
        except requests.exceptions.Timeout:
            raise Exception("Ollama request timed out. The model may be loading or too slow.")
        except Exception as e:
            raise Exception(f"Ollama search failed: {str(e)}")

    def add_custom_component(self, component_data: Dict) -> None:
        """Add a custom component to the cache

        Args:
            component_data: Component data dictionary
        """
        # Mark as custom
        component_data['custom'] = True
        component_data['source'] = 'Custom'

        # Add to cache
        self.add_to_cache(component_data)

        print(f"Added custom component: {component_data.get('model', 'Unknown')}")
