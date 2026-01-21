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

        # Get frequency points
        freqs = sorted([float(f) for f in loss_data.keys()])

        if not freqs:
            return 0.0

        # If frequency is outside range, use nearest
        if frequency_mhz <= freqs[0]:
            loss_per_100ft = loss_data[str(freqs[0])]
        elif frequency_mhz >= freqs[-1]:
            loss_per_100ft = loss_data[str(freqs[-1])]
        else:
            # Linear interpolation
            for i in range(len(freqs) - 1):
                if freqs[i] <= frequency_mhz <= freqs[i + 1]:
                    f1, f2 = freqs[i], freqs[i + 1]
                    loss1 = loss_data[str(f1)]
                    loss2 = loss_data[str(f2)]

                    # Linear interpolation
                    ratio = (frequency_mhz - f1) / (f2 - f1)
                    loss_per_100ft = loss1 + ratio * (loss2 - loss1)
                    break

        # Calculate total loss for length
        total_loss = loss_per_100ft * (length_ft / 100.0)
        return total_loss
