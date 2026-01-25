#!/usr/bin/env python3
"""
Ingest collected RF components through Ollama and add to the application databases.

This script:
1. Takes the web-scraped component data
2. Sends each through the rf-component-extractor Ollama model
3. Adds results to component_cache.json
4. For antennas, also creates XML pattern files and updates antenna_library/index.json
"""

import json
import os
import sys
import requests
import re
import math
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent.parent.parent
COMPONENT_CACHE = BASE_DIR / "components" / "cache" / "component_cache.json"
ANTENNA_LIBRARY = BASE_DIR / "antenna_library"
ANTENNA_INDEX = ANTENNA_LIBRARY / "index.json"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "rf-component-extractor"


def extract_with_ollama(source_text: str) -> dict:
    """Send text to Ollama and get extracted JSON"""
    prompt = f"""Extract RF component specifications as JSON:

{source_text}

Return ONLY valid JSON with component_type, manufacturer, model, and all relevant specifications."""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                'model': MODEL_NAME,
                'prompt': prompt,
                'stream': False
            },
            timeout=120
        )

        if response.status_code != 200:
            print(f"  Ollama error: {response.status_code}")
            return None

        result = response.json()
        response_text = result.get('response', '').strip()

        # Parse JSON (handle markdown code blocks)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response_text)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = response_text.strip()

        data = json.loads(json_str)

        # Normalize type -> component_type
        if 'type' in data and 'component_type' not in data:
            data['component_type'] = data.pop('type')

        return data

    except Exception as e:
        print(f"  Extraction error: {e}")
        return None


def load_component_cache() -> dict:
    """Load the component cache"""
    if COMPONENT_CACHE.exists():
        with open(COMPONENT_CACHE, 'r') as f:
            return json.load(f)
    return {
        "cache_version": "1.0",
        "description": "Component cache",
        "components": []
    }


def save_component_cache(cache: dict):
    """Save the component cache"""
    with open(COMPONENT_CACHE, 'w') as f:
        json.dump(cache, f, indent=2)


def load_antenna_index() -> dict:
    """Load the antenna library index"""
    if ANTENNA_INDEX.exists():
        with open(ANTENNA_INDEX, 'r') as f:
            return json.load(f)
    return {}


def save_antenna_index(index: dict):
    """Save the antenna library index"""
    with open(ANTENNA_INDEX, 'w') as f:
        json.dump(index, f, indent=2)


def get_next_antenna_id(index: dict) -> int:
    """Get the next available antenna ID number"""
    max_id = 0
    for key in index.keys():
        # Extract number from key like "Antenna_Name_5"
        parts = key.rsplit('_', 1)
        if len(parts) == 2 and parts[1].isdigit():
            max_id = max(max_id, int(parts[1]))
    return max_id + 1


def create_antenna_xml(antenna_data: dict, antenna_id: str) -> str:
    """Create XML content for an antenna pattern"""
    name = antenna_data.get('model', 'Unknown')
    manufacturer = antenna_data.get('manufacturer', 'Unknown')
    gain = antenna_data.get('gain_dbi', antenna_data.get('gain_dbd', 0))
    try:
        gain = float(gain) if gain else 0
    except (ValueError, TypeError):
        gain = 0
    if 'gain_dbd' in antenna_data and 'gain_dbi' not in antenna_data:
        try:
            gain = float(antenna_data['gain_dbd']) + 2.15  # Convert dBd to dBi
        except (ValueError, TypeError):
            pass

    pattern_type = str(antenna_data.get('pattern', 'omni-directional')).lower()
    is_directional = 'direct' in pattern_type or 'yagi' in pattern_type

    # Generate pattern data
    azimuth_points = []
    elevation_points = []

    if is_directional:
        # Directional pattern (yagi-like)
        try:
            front_to_back = float(antenna_data.get('front_to_back_db', 15))
        except (ValueError, TypeError):
            front_to_back = 15
        try:
            beamwidth_h = float(antenna_data.get('horizontal_beamwidth', 60))
        except (ValueError, TypeError):
            beamwidth_h = 60

        for angle in range(0, 360, 5):
            if angle <= beamwidth_h / 2 or angle >= 360 - beamwidth_h / 2:
                # Main lobe
                rel_gain = 1.0
            elif 90 <= angle <= 270:
                # Back lobe
                rel_gain = 10 ** (-front_to_back / 20)
            else:
                # Side lobes
                rel_gain = 0.3
            azimuth_points.append(f'    <point azimuth="{angle}" gain="{rel_gain:.4f}"/>')

        for angle in range(-90, 91, 5):
            if abs(angle) <= 30:
                rel_gain = 1.0
            else:
                rel_gain = max(0.1, 1.0 - abs(angle) / 90)
            elevation_points.append(f'    <point elevation="{angle}" gain="{rel_gain:.4f}"/>')
    else:
        # Omnidirectional pattern
        for angle in range(0, 360, 5):
            azimuth_points.append(f'    <point azimuth="{angle}" gain="1.0000"/>')

        for angle in range(-90, 91, 5):
            if abs(angle) <= 10:
                rel_gain = 1.0
            elif abs(angle) <= 30:
                rel_gain = 0.9
            elif abs(angle) <= 60:
                rel_gain = 0.5
            else:
                rel_gain = 0.2
            elevation_points.append(f'    <point elevation="{angle}" gain="{rel_gain:.4f}"/>')

    xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<antenna>
  <name>{name}</name>
  <manufacturer>{manufacturer}</manufacturer>
  <gain>{gain}</gain>
  <type>{"Directional" if is_directional else "Omni"}</type>
  <azimuth>
{chr(10).join(azimuth_points)}
  </azimuth>
  <elevation>
{chr(10).join(elevation_points)}
  </elevation>
</antenna>
'''
    return xml_content


def determine_band(freq_range: list) -> str:
    """Determine the band name from frequency range"""
    if not freq_range or len(freq_range) < 2:
        return "Unknown"

    # Ensure numeric values
    try:
        f0 = float(freq_range[0]) if freq_range[0] else 0
        f1 = float(freq_range[1]) if freq_range[1] else 0
        center_freq = (f0 + f1) / 2
    except (ValueError, TypeError):
        return "Unknown"

    if center_freq < 50:
        return "HF"
    elif center_freq < 88:
        return "VHF-Low"
    elif center_freq <= 108:
        return "FM"
    elif center_freq < 174:
        return "VHF"
    elif center_freq < 400:
        return "UHF-Low"
    elif center_freq < 512:
        return "UHF"
    elif center_freq < 700:
        return "600 MHz"
    elif center_freq < 900:
        return "700/800"
    elif center_freq < 1000:
        return "900 MHz"
    else:
        return "Microwave"


def add_antenna_to_library(antenna_data: dict, antenna_index: dict) -> str:
    """Add an antenna to the library and return its ID"""
    next_id = get_next_antenna_id(antenna_index)
    model = antenna_data.get('model', 'Unknown').replace(' ', '_').replace('/', '-')
    antenna_id = f"{model}_{next_id}"

    # Create XML file
    xml_content = create_antenna_xml(antenna_data, antenna_id)
    xml_filename = f"{antenna_id}.xml"
    xml_path = ANTENNA_LIBRARY / xml_filename

    with open(xml_path, 'w') as f:
        f.write(xml_content)

    # Determine frequency range
    freq_range = antenna_data.get('frequency_range_mhz', [0, 0])
    if isinstance(freq_range, list) and len(freq_range) >= 2:
        freq_str = f"{freq_range[0]}-{freq_range[1]} MHz"
    else:
        freq_str = "Unknown"

    # Add to index
    gain = antenna_data.get('gain_dbi', antenna_data.get('gain_dbd', 0))
    try:
        gain = float(gain) if gain else 0
    except (ValueError, TypeError):
        gain = 0
    if 'gain_dbd' in antenna_data and 'gain_dbi' not in antenna_data:
        try:
            gain = float(antenna_data['gain_dbd']) + 2.15
        except (ValueError, TypeError):
            pass

    pattern_type = str(antenna_data.get('pattern', 'omni-directional')).lower()
    is_directional = 'direct' in pattern_type or 'yagi' in pattern_type

    antenna_index[antenna_id] = {
        "name": antenna_data.get('model', 'Unknown'),
        "xml_file": xml_filename,
        "manufacturer": antenna_data.get('manufacturer', 'Unknown'),
        "part_number": antenna_data.get('part_number', antenna_data.get('model', 'N/A')),
        "gain": round(gain, 2),
        "band": determine_band(freq_range),
        "frequency_range": freq_str,
        "type": "Directional" if is_directional else "Omni",
        "notes": f"Imported via Ollama extraction. VSWR: {antenna_data.get('vswr', 'N/A')}, Power: {antenna_data.get('power_rating_watts', 'N/A')}W, Polarization: {antenna_data.get('polarization', 'N/A')}",
        "import_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    return antenna_id


def add_component_to_cache(component_data: dict, cache: dict) -> str:
    """Add a component to the cache"""
    model = component_data.get('model', 'Unknown')
    component_type = component_data.get('component_type', 'unknown')

    # Build cache entry based on component type
    entry = {
        "component_type": component_type,
        "source": "Ollama",
        "custom": False,
        "model": model,
        "manufacturer": component_data.get('manufacturer', 'Unknown'),
    }

    # Add type-specific fields
    if component_type == 'cable':
        entry.update({
            "description": f"{component_data.get('manufacturer', '')} {model} coaxial cable",
            "cable_type": model,
            "impedance_ohms": component_data.get('impedance_ohms', 50),
            "velocity_factor": component_data.get('velocity_factor', 0.85),
            "loss_db_per_100ft": component_data.get('loss_db_per_100ft', {}),
        })
        # Calculate single loss value at a common frequency
        loss_data = component_data.get('loss_db_per_100ft', {})
        if loss_data:
            # Use 450 MHz as default, or first available
            for freq in ['450', '500', '400', '150', '100']:
                if freq in loss_data:
                    entry['loss_per_100ft'] = loss_data[freq]
                    break

    elif component_type == 'antenna':
        gain = component_data.get('gain_dbi', component_data.get('gain_dbd', 0))
        try:
            gain = float(gain) if gain else 0
        except (ValueError, TypeError):
            gain = 0
        if 'gain_dbd' in component_data and 'gain_dbi' not in component_data:
            try:
                gain = float(component_data['gain_dbd']) + 2.15
            except (ValueError, TypeError):
                pass
        entry.update({
            "description": f"{component_data.get('manufacturer', '')} {model} antenna",
            "gain_dbi": round(gain, 2),
            "pattern": component_data.get('pattern', 'Omni'),
            "vswr": component_data.get('vswr', 1.5),
            "power_rating_watts": component_data.get('power_rating_watts', 100),
            "polarization": component_data.get('polarization', 'vertical'),
        })
        freq_range = component_data.get('frequency_range_mhz', [0, 0])
        if freq_range:
            entry['freq_min'] = freq_range[0] if isinstance(freq_range, list) else 0
            entry['freq_max'] = freq_range[1] if isinstance(freq_range, list) and len(freq_range) > 1 else 0
            entry['frequency_range_mhz'] = freq_range

    elif component_type == 'transmitter':
        power = component_data.get('power_output_watts', 0)
        try:
            power = float(power) if power else 0
        except (ValueError, TypeError):
            power = 0
        efficiency = component_data.get('efficiency_percent', 70)
        try:
            efficiency = float(efficiency) if efficiency else 70
        except (ValueError, TypeError):
            efficiency = 70
        entry.update({
            "description": f"{component_data.get('manufacturer', '')} {model} transmitter",
            "power_output_watts": power,
            "efficiency_percent": efficiency,
        })
        if power > 0:
            entry['power_output_dbm'] = 10 * math.log10(power * 1000)
            entry['power_output_dbw'] = 10 * math.log10(power)
        freq_range = component_data.get('frequency_range_mhz', [0, 0])
        if freq_range:
            entry['freq_min'] = freq_range[0] if isinstance(freq_range, list) else 0
            entry['freq_max'] = freq_range[1] if isinstance(freq_range, list) and len(freq_range) > 1 else 0
            entry['frequency_range_mhz'] = freq_range

    elif component_type == 'lightning_arrestor':
        entry.update({
            "description": f"{component_data.get('manufacturer', '')} {model} lightning arrestor",
            "passive_type": "lightning_arrestor",
            "insertion_loss_db": component_data.get('insertion_loss_db', 0.2),
            "dc_pass": component_data.get('dc_pass', True),
            "voltage_rating_kv": component_data.get('voltage_rating_kv', 5),
            "connector_type": component_data.get('connector_type', 'N-type'),
        })
        freq_range = component_data.get('frequency_range_mhz', [0, 1000])
        if freq_range:
            entry['freq_min'] = freq_range[0] if isinstance(freq_range, list) else 0
            entry['freq_max'] = freq_range[1] if isinstance(freq_range, list) and len(freq_range) > 1 else 1000
            entry['frequency_range_mhz'] = freq_range

    elif component_type == 'filter':
        entry.update({
            "description": f"{component_data.get('manufacturer', '')} {model} filter",
            "passive_type": "filter",
            "insertion_loss_db": component_data.get('insertion_loss_db', 0.5),
            "rejection_db": component_data.get('rejection_db', 40),
            "power_rating_watts": component_data.get('power_rating_watts', 1000),
        })
        freq_range = component_data.get('frequency_range_mhz', component_data.get('passband_mhz', [0, 0]))
        if freq_range:
            entry['freq_min'] = freq_range[0] if isinstance(freq_range, list) else 0
            entry['freq_max'] = freq_range[1] if isinstance(freq_range, list) and len(freq_range) > 1 else 0
            entry['frequency_range_mhz'] = freq_range

    elif component_type in ['isolator', 'combiner']:
        entry.update({
            "description": f"{component_data.get('manufacturer', '')} {model} {component_type}",
            "passive_type": component_type,
            "insertion_loss_db": component_data.get('insertion_loss_db', 0.5),
            "isolation_db": component_data.get('isolation_db', 20),
            "power_rating_watts": component_data.get('power_rating_watts', 100),
        })
        freq_range = component_data.get('frequency_range_mhz', [0, 0])
        if freq_range:
            entry['freq_min'] = freq_range[0] if isinstance(freq_range, list) else 0
            entry['freq_max'] = freq_range[1] if isinstance(freq_range, list) and len(freq_range) > 1 else 0
            entry['frequency_range_mhz'] = freq_range

    else:
        entry['description'] = f"{component_data.get('manufacturer', '')} {model}"

    # Add notes
    entry['notes'] = f"Extracted via Ollama from web data"

    # Add to cache using model as key
    cache[model] = entry
    return model


# All component data to ingest
COMPONENTS_TO_INGEST = [
    # VHF Antennas
    {
        "source_text": """Commander Technologies 150-5N VHF Antenna
Model: 150-5N
Frequency Range: 148 - 174 MHz
Gain: 5.1 dBi / 3 dBd
Polarization: Vertical
VSWR: 1.5:1
Impedance: 50 Ohm
Connector Type: N Female
Power Rating: 500 W
Weight: 8.5 lb
Features: Broadband, superior lightning protection""",
        "component_type": "antenna"
    },
    {
        "source_text": """PCTEL MAXRAD MBX150 VHF Base Station Antenna
Model: MBX150
Frequency: 144-174 MHz
Gain: 3.0 dBd / 5.15 dBi
Power: 250 watts
Connector: UHF female
Polarization: Vertical
Type: Collinear omni with phasing stub""",
        "component_type": "antenna"
    },

    # UHF Antennas
    {
        "source_text": """TE Connectivity FG4505W UHF Antenna
Model: FG4505W
Frequency Range: 450-470 MHz
Gain: 5 dBd / 7.15 dBi
Polarization: Vertical
VSWR: 2:1
Impedance: 50 ohms
Connector Type: N-Female
Power Rating: 200 W
Length: 76 inches
Weight: 6 lbs
Fiberglass construction, UV coating""",
        "component_type": "antenna"
    },
    {
        "source_text": """Andrew DB411-B UHF Quasi-Omni Antenna
Model: DB411-B
Manufacturer: Andrew/Amphenol
Frequency: 450-470 MHz
Gain: 11.1 dBi / 9 dBd
Connector: N Male
Power: 250 watts max
Length: 113 inches
Weight: 25 lb
Type: Exposed dipole quasi-omni""",
        "component_type": "antenna"
    },
    {
        "source_text": """PCTEL MBX450 UHF Base Station Antenna
Model: MBX450
Frequency: 450-470 MHz
Gain: 5.15 dBi
Polarization: Vertical
Connector: UHF Female
Power: 250 W
Beamwidth: 30 degrees vertical
Type: Collinear omnidirectional""",
        "component_type": "antenna"
    },
    {
        "source_text": """dbSpectra DS4F06P3IU-D UHF Omni Antenna
Model: DS4F06P3IU-D
Manufacturer: dbSpectra
Frequency: 450-470 MHz
Gain: 6 dBd / 8.15 dBi
Pattern: Omni Directional
Connector: 7-16 DIN
Low-PIM/Hi-PIP Certified""",
        "component_type": "antenna"
    },

    # 700/800 MHz Antennas
    {
        "source_text": """Sinclair SC46A-HF1LDF Aurora Collinear Omni Antenna
Model: SC46A-HF1LDF
Manufacturer: Sinclair Technologies
Frequency: 746-869 MHz
Gain: 10 dBd / 12.15 dBi
Pattern: Omnidirectional collinear
Features: HD, low PIM, PIP certified
Application: Public safety 700/800 MHz""",
        "component_type": "antenna"
    },
    {
        "source_text": """Alive Telecom ATC-GC4V1O-1-D4 UHF Omni Antenna
Model: ATC-GC4V1O-1-D4
Manufacturer: Alive Telecom
Frequency: 380-400 MHz
Gain: 0.0 dBd (unity) / 2.15 dBi
Polarization: Vertical
Connector: 4.3-10 DIN Female
Power: 250 Watts
PIM: -150 dBc
IP Rating: IP66
Type: Omnidirectional base station""",
        "component_type": "antenna"
    },

    # FM Broadcast Antennas
    {
        "source_text": """Jampro JHPC High Power Circular Penetrator FM Antenna
Model: JHPC
Manufacturer: Jampro Antennas
Frequency: 87.5-108 MHz (FM Band II)
Power: 40 kW maximum per bay
Polarization: Circular
VSWR: 1.1:1 +/- 200 kHz
Feed: 3-1/8 inch shunt feed line
Construction: Marine brass and copper""",
        "component_type": "antenna"
    },
    {
        "source_text": """Jampro JMPC Medium Power Circular Penetrator FM Antenna
Model: JMPC
Manufacturer: Jampro Antennas
Frequency: 87.5-108 MHz
Power: 10 kW maximum per bay
Polarization: Circular
VSWR: 1.1:1
Feed: 1-5/8 inch shunt feed line
Construction: Marine brass/copper""",
        "component_type": "antenna"
    },
    {
        "source_text": """Jampro JLCP Low Power FM Antenna
Model: JLCP
Manufacturer: Jampro Antennas
Frequency: 87.5-108 MHz (FM Band II)
Power: 500W to 2kW
Polarization: Circular
VSWR: 1.5:1 or better
Construction: Stainless steel
Application: Low power translators, LPFM""",
        "component_type": "antenna"
    },
    {
        "source_text": """Jampro JBVP Vertical Dipole FM Antenna
Model: JBVP
Manufacturer: Jampro Antennas
Frequency: 87.5-108 MHz
Power: 2.5kW to 20kW
Polarization: Vertical
VSWR: 1.25:1 over 6 MHz bandwidth
Construction: Stainless steel, brass conductors
Features: Balun-fed, custom directional patterns available""",
        "component_type": "antenna"
    },
    {
        "source_text": """Jampro ADB-FM1 FM Broadcast Antenna
Model: ADB-FM1
Manufacturer: Jampro Antennas
Frequency: 87.5-108 MHz
Power: 1kW per bay, up to 8kW (8-bay)
Polarization: Vertical
VSWR: 1.4:1 typical
Configurations: 2, 4, 6, or 8 bays
Features: Broadband, no field tuning required""",
        "component_type": "antenna"
    },

    # Yagi/Directional Antennas
    {
        "source_text": """RFI Americas YH03 VHF 3-Element Yagi Antenna
Model: YH03
Manufacturer: RFI Americas
Frequency: 100-250 MHz (custom tuned)
Gain: 6 dBd / 8.15 dBi
VSWR: 1.5:1
Connector: N female with RG213 cable tail
Power: 250 watts
Vertical Beamwidth: 60 degrees
Horizontal Beamwidth: 75 degrees
Front-to-Back Ratio: 15 dB
Pattern: Directional
Construction: Thick-walled aluminum boom""",
        "component_type": "antenna"
    },
    {
        "source_text": """RFI Americas RDA6-99 UHF Ruggedized 6-Element Yagi Antenna
Model: RDA6-99
Manufacturer: RFI Americas
Frequency: 330-600 MHz (custom tuned)
Gain: 11.1 dBi / 9 dBd
VSWR: 1.5:1
Connector: N female with 9302 cable tail
Power: 250 watts
Vertical Beamwidth: 45 degrees
Horizontal Beamwidth: 54 degrees
Front-to-Back Ratio: 20 dB
Pattern: Directional
Construction: All welded aluminum, black powder coated""",
        "component_type": "antenna"
    },

    # Coaxial Cables
    {
        "source_text": """Andrew/CommScope LDF4-50A HELIAX Coaxial Cable
Model: LDF4-50A
Manufacturer: Andrew/CommScope
Impedance: 50 ohms
Velocity Factor: 88%
Outer Diameter: 0.5 inches
Max Frequency: 8.8 GHz
Peak Power: 40 kW
Attenuation at 100 MHz: 0.661 dB/100ft
Attenuation at 500 MHz: 1.53 dB/100ft
Attenuation at 800 MHz: 1.97 dB/100ft
Attenuation at 1000 MHz: 2.22 dB/100ft
Inner Conductor: Copper-clad aluminum
Outer Conductor: Corrugated copper""",
        "component_type": "cable"
    },
    {
        "source_text": """Times Microwave LMR-400 Coaxial Cable
Model: LMR-400
Manufacturer: Times Microwave Systems
Impedance: 50 ohms
Velocity Factor: 85%
Outer Diameter: 0.405 inches
Attenuation at 150 MHz: 0.7 dB/100ft
Attenuation at 450 MHz: 1.3 dB/100ft
Attenuation at 900 MHz: 1.9 dB/100ft
Attenuation at 1500 MHz: 2.5 dB/100ft
Power at 150 MHz: 1800W
Power at 900 MHz: 750W""",
        "component_type": "cable"
    },
    {
        "source_text": """Andrew LDF5-50A 7/8 inch HELIAX Cable
Model: LDF5-50A
Manufacturer: Andrew/CommScope
Impedance: 50 ohms
Velocity Factor: 89%
Outer Diameter: 0.875 inches (7/8 inch)
Attenuation at 100 MHz: 0.37 dB/100ft
Attenuation at 500 MHz: 0.87 dB/100ft
Attenuation at 1000 MHz: 1.27 dB/100ft
Peak Power: 80 kW
Construction: Corrugated copper outer conductor""",
        "component_type": "cable"
    },

    # Lightning Arrestors
    {
        "source_text": """PolyPhaser IS-B50LN-C2 Lightning Arrestor
Model: IS-B50LN-C2
Manufacturer: PolyPhaser
Type: Bulkhead Coaxial RF Surge Protector
Frequency: 10 MHz to 1 GHz
Power: 1.5 kW maximum
Let-Through Energy: 120uJ
Surge Current: 20kA
Connector: N-Female both ends
Mounting: Bulkhead
DC: Block
Technology: Blocking cap and gas tube""",
        "component_type": "lightning_arrestor"
    },
    {
        "source_text": """PolyPhaser IS-B50LN-C0 Lightning Arrestor
Model: IS-B50LN-C0
Manufacturer: PolyPhaser
Frequency: DC to 1 GHz
Insertion Loss: 0.2 dB
Power: 1.5 kW
Surge Current: 20kA
Connector: N-Female both ends
Mounting: Bulkhead
DC: Pass
Application: Tower base protection, repeater sites""",
        "component_type": "lightning_arrestor"
    },
    {
        "source_text": """PolyPhaser IS-B50HN-C0 High Power Lightning Arrestor
Model: IS-B50HN-C0
Manufacturer: PolyPhaser
Frequency: 1.5 MHz to 700 MHz
Power: 3 kW maximum
Connector: N-Female both ends
DC: Pass
Application: High power transmitters, broadcast""",
        "component_type": "lightning_arrestor"
    },

    # FM Transmitters
    {
        "source_text": """Nautel VS1 FM Broadcast Transmitter
Model: VS1
Manufacturer: Nautel
Power Output: 1400 W analog
Frequency: 87.5-108 MHz
Power Supply: Single unit
AC Input: 180-264 V, 1 phase
Form Factor: 3 RU
SNR: -90 dB
Features: Direct-to-channel digital exciter, RDS generator, GPS input""",
        "component_type": "transmitter"
    },
    {
        "source_text": """Nautel VS2.5 FM Broadcast Transmitter
Model: VS2.5
Manufacturer: Nautel
Power Output: 2800 W analog
Frequency: 87.5-108 MHz
Power Supply: Dual units
AC Input: 180-264 V, 1 phase
Form Factor: 5 RU
Features: Direct-to-channel digital exciter""",
        "component_type": "transmitter"
    },
    {
        "source_text": """Nautel VX5 FM Broadcast Transmitter
Model: VX5
Manufacturer: Nautel
Power Output: 5500 W analog
Frequency: 87.5-108 MHz
Efficiency: 72%
Form Factor: 3U compact design
Power Supply: Hot-swappable, 96% efficient
Features: Direct-to-channel digital exciter""",
        "component_type": "transmitter"
    },
    {
        "source_text": """BW Broadcast TX1000 V3 FM Transmitter
Model: TX1000 V3
Manufacturer: BW Broadcast
Power Output: 10-1100 watts adjustable
Frequency: 87.5-108 MHz
Power Supply Efficiency: 96%
Form Factor: 2U rack mount
Features: Direct-to-channel digital modulation, GPS for SFN, XLR analog/digital inputs, RDS generator, DSPX multi-band processor""",
        "component_type": "transmitter"
    },
    {
        "source_text": """BW Broadcast TX600 V3 FM Transmitter
Model: TX600 V3
Manufacturer: BW Broadcast
Power Output: 600 W
Frequency: 87.5-108 MHz
Power Supply Efficiency: 96%
Form Factor: 2RU
Features: 4-band DSP audio processing, Ethernet control, RDS encoder, hot-swappable power supply, integrated DSPX audio processor""",
        "component_type": "transmitter"
    },
    {
        "source_text": """Nautel VX1 FM Broadcast Transmitter
Model: VX1
Manufacturer: Nautel
Power Output: 1100 W analog
Frequency: 87.5-108 MHz
Efficiency: 68%
Form Factor: 2 RU
Power Supply: Hot-swappable, 96% efficient
Features: Direct-to-channel digital exciter, -90 dB SNR""",
        "component_type": "transmitter"
    },

    # Filters
    {
        "source_text": """ERI 785 FM Notch Filter
Model: 785
Manufacturer: Electronics Research Inc (ERI)
Frequency: 88-108 MHz
Power Handling: 35 kW at greater than 1 MHz separation
Notch Suppression: -40 dB at greater than 1 MHz separation
Insertion Loss: 0.03 dB at greater than 1 MHz separation
VSWR: 1.05:1 +/-150kHz
Connectors: 1-5/8 inch or 3-1/8 inch EIA Flange
Configurations: 1, 2, 3, 4, or 5 cavities
Cooling: Convection""",
        "component_type": "filter"
    },
    {
        "source_text": """PCS Electronics ECOMAX CAVFM2N Double Cavity Filter
Model: CAVFM2N
Manufacturer: PCS Electronics
Frequency: 87.5-108 MHz
Power: 1000W
-3dB Bandwidth: 800 kHz - 1.5 MHz
Attenuation at +/-2MHz: 22 dB
Attenuation at +/-6MHz: 40 dB
Insertion Loss: 0.3 dB
Connectors: N female""",
        "component_type": "filter"
    },
    {
        "source_text": """PCS Electronics ECOMAX CAVFM3M Triple Cavity Filter
Model: CAVFM3M
Manufacturer: PCS Electronics
Frequency: 87.5-108 MHz
Power: 2000W
-3dB Bandwidth: 500 kHz
Attenuation at +/-2MHz: 37 dB
Attenuation at +/-6MHz: 60 dB
Insertion Loss: 0.4 dB
Connectors: 7-16 DIN female""",
        "component_type": "filter"
    },
]


def main():
    print("=" * 60)
    print("RF Component Ingestion via Ollama")
    print("=" * 60)

    # Load existing data
    cache = load_component_cache()
    antenna_index = load_antenna_index()

    # Track stats
    stats = {
        'processed': 0,
        'antennas_added': 0,
        'components_added': 0,
        'errors': 0
    }

    for i, component in enumerate(COMPONENTS_TO_INGEST, 1):
        source_text = component['source_text']
        expected_type = component['component_type']

        # Extract model name from source text for display
        model_match = re.search(r'Model:\s*(\S+)', source_text)
        model_name = model_match.group(1) if model_match else f"Component {i}"

        print(f"\n[{i}/{len(COMPONENTS_TO_INGEST)}] Processing: {model_name}")

        # Extract through Ollama
        extracted = extract_with_ollama(source_text)

        if not extracted:
            print(f"  ERROR: Failed to extract")
            stats['errors'] += 1
            continue

        # Ensure component type is set
        if 'component_type' not in extracted:
            extracted['component_type'] = expected_type

        component_type = extracted.get('component_type', 'unknown')
        print(f"  Type: {component_type}")
        print(f"  Model: {extracted.get('model', 'Unknown')}")

        # Add to appropriate database
        if component_type == 'antenna':
            # Add to both component cache and antenna library
            cache_key = add_component_to_cache(extracted, cache)
            antenna_id = add_antenna_to_library(extracted, antenna_index)
            cache[cache_key]['antenna_id'] = antenna_id
            print(f"  Added to cache: {cache_key}")
            print(f"  Added to antenna library: {antenna_id}")
            stats['antennas_added'] += 1
        else:
            # Add to component cache only
            cache_key = add_component_to_cache(extracted, cache)
            print(f"  Added to cache: {cache_key}")

        stats['components_added'] += 1
        stats['processed'] += 1

    # Save everything
    print("\n" + "=" * 60)
    print("Saving databases...")
    save_component_cache(cache)
    save_antenna_index(antenna_index)

    print("\n" + "=" * 60)
    print("INGESTION COMPLETE")
    print("=" * 60)
    print(f"Processed: {stats['processed']}")
    print(f"Components added to cache: {stats['components_added']}")
    print(f"Antennas added to library: {stats['antennas_added']}")
    print(f"Errors: {stats['errors']}")
    print(f"\nComponent cache: {COMPONENT_CACHE}")
    print(f"Antenna library: {ANTENNA_INDEX}")


if __name__ == "__main__":
    main()
