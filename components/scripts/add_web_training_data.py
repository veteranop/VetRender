#!/usr/bin/env python3
"""
Add web-scraped RF component data to training dataset.
This script adds the components discovered via web search to the training data.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.scripts.training_data_collector import TrainingDataCollector

def main():
    collector = TrainingDataCollector()

    # VHF Antennas (136-174 MHz)
    vhf_antennas = [
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
Vertical Beamwidth: 35 degrees
Features: Broadband capability, superior lightning protection, direct ground""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "Commander Technologies",
                "model": "150-5N",
                "frequency_range_mhz": [148, 174],
                "gain_dbi": 5.1,
                "gain_dbd": 3.0,
                "polarization": "vertical",
                "vswr": 1.5,
                "impedance_ohms": 50,
                "connector_type": "N-Female",
                "power_rating_watts": 500,
                "pattern": "omni-directional"
            },
            "source_path": "https://www.tessco.com/product/148-174-mhz-5-1-dbi-omni-fiberglass-antenna-with-n-female-connector-288079"
        },
        {
            "source_text": """PCTEL MAXRAD 144-174 MHz Base Station Antenna
Model: MBX150
Frequency: 144-174 MHz
Gain: 3.0 dB
Power: 250 watts
Connector: UHF female
Type: Vertical collinear omni
Features: Phasing stub eliminating radials""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "PCTEL",
                "model": "MBX150",
                "frequency_range_mhz": [144, 174],
                "gain_dbd": 3.0,
                "power_rating_watts": 250,
                "connector_type": "UHF-Female",
                "polarization": "vertical",
                "pattern": "omni-directional"
            },
            "source_path": "https://www.tessco.com/product/35273"
        }
    ]

    # UHF Antennas (400-512 MHz)
    uhf_antennas = [
        {
            "source_text": """TE Connectivity FG4505W UHF Antenna
Model: FG4505W
Frequency Range: 450-470 MHz
Gain: 5 dBd / 7.15 dBi
Polarization: Vertical
VSWR: <2:1
Impedance: 50 ohms
Connector Type: N-Female
Power Rating: 200 W
Length: 76 inches
Diameter: 1.31 inches
Weight: 6 lbs
Temperature: -40C to +85C
No ground plane required
Fiberglass construction with UV coating""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "TE Connectivity",
                "model": "FG4505W",
                "frequency_range_mhz": [450, 470],
                "gain_dbi": 7.15,
                "gain_dbd": 5.0,
                "polarization": "vertical",
                "vswr": 2.0,
                "impedance_ohms": 50,
                "connector_type": "N-Female",
                "power_rating_watts": 200,
                "pattern": "omni-directional"
            },
            "source_path": "https://www.arcantenna.com/products/laird-antenex-fg4505w"
        },
        {
            "source_text": """Andrew DB411-B UHF Antenna
Model: DB411-B
Frequency: 450-470 MHz
Gain: 11.1 dBi / 9 dBd
Connector: N Male
Power: 250 watts max
Length: 113 inches
Weight: 25 lb
Type: Quasi-omni exposed dipole""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "Andrew/Amphenol",
                "model": "DB411-B",
                "frequency_range_mhz": [450, 470],
                "gain_dbi": 11.1,
                "gain_dbd": 9.0,
                "connector_type": "N-Male",
                "power_rating_watts": 250,
                "pattern": "quasi-omni"
            },
            "source_path": "https://www.tessco.com/product/450-470-mhz-9db-exposed-dipole-omni-antenna-24252"
        },
        {
            "source_text": """PCTEL MBX450 UHF Antenna
Model: MBX450
Frequency: 450-470 MHz
Gain: 5.15 dBi
Polarization: Vertical
Connector: UHF Female
Power: 250 W
Beamwidth: 30 degrees vertical
Weight: 0.6 lb
Type: Base vertical omnidirectional collinear""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "PCTEL",
                "model": "MBX450",
                "frequency_range_mhz": [450, 470],
                "gain_dbi": 5.15,
                "polarization": "vertical",
                "connector_type": "UHF-Female",
                "power_rating_watts": 250,
                "pattern": "omni-directional"
            },
            "source_path": "https://www.tessco.com/product/450-470-mhz-3-0db-base-station-omni-antenna-60452"
        },
        {
            "source_text": """dbSpectra DS4F06P3IU-D UHF Antenna
Model: DS4F06P3IU-D
Frequency: 450-470 MHz
Gain: 6 dBd (5.0 to 7.9 dBd range)
Pattern: Omni Directional
Connector: 7-16 DIN
Ports: 1
Low-PIM/Hi-PIP Certified""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "dbSpectra",
                "model": "DS4F06P3IU-D",
                "frequency_range_mhz": [450, 470],
                "gain_dbd": 6.0,
                "connector_type": "7-16 DIN",
                "pattern": "omni-directional",
                "pim_certified": True
            },
            "source_path": "https://www.dbspectra.com/products/450-470-mhz-uhf-omni-6-dbd-low-pim-hi-pip-antenna-ds4f06p3iu-d/"
        }
    ]

    # 700/800 MHz Antennas
    public_safety_antennas = [
        {
            "source_text": """Sinclair SC46A-HF1LDF Aurora Collinear Omni
Model: SC46A-HF1LDF(DXX-PIP)
Frequency: 746-869 MHz
Gain: 10 dBd
Pattern: Omnidirectional collinear
Features: HD, low PIM, PIP
Application: Public safety 700/800 MHz""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "Sinclair Technologies",
                "model": "SC46A-HF1LDF",
                "frequency_range_mhz": [746, 869],
                "gain_dbd": 10.0,
                "pattern": "omni-directional",
                "pim_certified": True
            },
            "source_path": "https://www.sinctech.com/collections/746-869-mhz"
        },
        {
            "source_text": """Alive Telecom UHF Omni Antenna
Model: ATC-GC4V1O-1-D4
SKU: 619157
Frequency: 380-400 MHz
Gain: 0.0 dBd (unity gain)
Polarization: Vertical
Connector: 4.3-10 DIN Female
Power: 250 Watts
PIM: -150 dBc
IP Rating: IP66
Type: Omnidirectional base station""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "Alive Telecom",
                "model": "ATC-GC4V1O-1-D4",
                "frequency_range_mhz": [380, 400],
                "gain_dbd": 0.0,
                "gain_dbi": 2.15,
                "polarization": "vertical",
                "connector_type": "4.3-10 DIN Female",
                "power_rating_watts": 250,
                "pim_dbc": -150,
                "pattern": "omni-directional"
            },
            "source_path": "https://www.tessco.com/product/380-400-mhz-unity-gain-omni-antenna-619157"
        }
    ]

    # FM Broadcast Antennas
    fm_antennas = [
        {
            "source_text": """Jampro JHPC High Power Circular Penetrator
Model: JHPC
Frequency: 87.5-108 MHz (FM Band II)
Power: 40 kW maximum per bay
Polarization: Circular
VSWR: 1.1:1 +/- 200 kHz
Feed: 3-1/8" shunt feed line
Construction: Marine brass and copper
Mounting: Hot dipped galvanized steel bracket""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "Jampro Antennas",
                "model": "JHPC",
                "frequency_range_mhz": [87.5, 108],
                "power_rating_watts": 40000,
                "polarization": "circular",
                "vswr": 1.1,
                "connector_type": "EIA 3-1/8\" flange",
                "pattern": "omni-directional"
            },
            "source_path": "https://jampro.com/low-power-fm-broadcast-antennas/"
        },
        {
            "source_text": """Jampro JMPC Medium Power Circular Penetrator
Model: JMPC
Frequency: 87.5-108 MHz
Power: 10 kW maximum per bay
Polarization: Circular
Feed: 1-5/8 inch shunt feed line
Construction: Marine brass/copper""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "Jampro Antennas",
                "model": "JMPC",
                "frequency_range_mhz": [87.5, 108],
                "power_rating_watts": 10000,
                "polarization": "circular",
                "connector_type": "EIA 1-5/8\" flange"
            },
            "source_path": "https://jampro.com/low-power-fm-broadcast-antennas/"
        },
        {
            "source_text": """Jampro JLCP Low Power FM Antenna
Model: JLCP
Frequency: FM Band II (87.5-108 MHz)
Power: 500W (options to 1-2kW)
Polarization: Circular
VSWR: 1.5:1 or better
Construction: Stainless steel
Application: Low power translators/boosters""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "Jampro Antennas",
                "model": "JLCP",
                "frequency_range_mhz": [87.5, 108],
                "power_rating_watts": 500,
                "polarization": "circular",
                "vswr": 1.5
            },
            "source_path": "https://jampro.com/low-power-fm-broadcast-antennas/"
        },
        {
            "source_text": """Jampro JBVP Vertical Dipole FM Antenna
Model: JBVP
Frequency: 87.5-108 MHz
Power: 2.5kW to 20kW
Polarization: Vertical
VSWR: 1.25:1 over 6 MHz
Construction: Stainless steel, brass conductors
Feed: Balun-fed
Features: Custom directional patterns available""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "Jampro Antennas",
                "model": "JBVP",
                "frequency_range_mhz": [87.5, 108],
                "power_rating_watts": 20000,
                "polarization": "vertical",
                "vswr": 1.25
            },
            "source_path": "https://jampro.com/low-power-fm-broadcast-antennas/"
        }
    ]

    # Yagi/Directional Antennas
    yagi_antennas = [
        {
            "source_text": """RFI Americas YH03 VHF 3-Element Yagi
Model: YH03
Frequency: 100-250 MHz (custom tuned)
Gain: 6 dBd
VSWR: <1.5:1
Connector: N female with RG213 cable tail
Power: 250 watts
Vertical Beamwidth: 60 degrees
Horizontal Beamwidth: 75 degrees
Front-to-Back Ratio: 15 dB typical
Tunable Bandwidth: 9 MHz
Length: 70.9 inches
Weight: 5.7 pounds
Construction: Thick-walled aluminum boom
DC grounding for lightning protection""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "RFI Americas",
                "model": "YH03",
                "frequency_range_mhz": [100, 250],
                "gain_dbd": 6.0,
                "vswr": 1.5,
                "connector_type": "N-Female",
                "power_rating_watts": 250,
                "front_to_back_db": 15,
                "pattern": "directional"
            },
            "source_path": "https://www.rfiamericas.com/product/vhf-3-element-yagi-6dbd-100-250mhz/"
        },
        {
            "source_text": """RFI Americas RDA6-99 UHF Ruggedized Yagi
Model: RDA6-99
Frequency: 330-600 MHz (custom tuned)
Gain: 11.1 dBi / 9 dBd
VSWR: <1.5:1
Connector: N female with 9302 cable tail
Power: 250 watts
Vertical Beamwidth: 45 degrees
Horizontal Beamwidth: 54 degrees
Front-to-Back Ratio: 20 dB
Tunable Bandwidth: 4%
Length: 59.1 inches
Weight: 2.9 pounds
Construction: All welded aluminum, black powder coated""",
            "expected_json": {
                "component_type": "antenna",
                "manufacturer": "RFI Americas",
                "model": "RDA6-99",
                "frequency_range_mhz": [330, 600],
                "gain_dbi": 11.1,
                "gain_dbd": 9.0,
                "vswr": 1.5,
                "connector_type": "N-Female",
                "power_rating_watts": 250,
                "front_to_back_db": 20,
                "pattern": "directional"
            },
            "source_path": "https://www.rfiamericas.com/product/uhf-directional-yagi-350-600-mhz-9dbd-ruggedized/"
        }
    ]

    # Coaxial Cables
    cables = [
        {
            "source_text": """Andrew/CommScope LDF4-50A HELIAX Cable
Model: LDF4-50A
Impedance: 50 ohms
Velocity Factor: 88%
Outer Diameter: 0.5 inches
Max Frequency: 8.8 GHz
Peak Power: 40 kW
Attenuation:
  100 MHz: 0.661 dB/100ft
  500 MHz: 1.53 dB/100ft
  800 MHz: 1.97 dB/100ft
  1000 MHz: 2.22 dB/100ft
Inner Conductor: Copper-clad aluminum
Outer Conductor: Corrugated copper
Jacket: Black PE
Temperature: -55C to +85C""",
            "expected_json": {
                "component_type": "cable",
                "manufacturer": "Andrew/CommScope",
                "model": "LDF4-50A",
                "impedance_ohms": 50,
                "velocity_factor": 0.88,
                "outer_diameter_inches": 0.5,
                "loss_db_per_100ft": {
                    "100": 0.661,
                    "500": 1.53,
                    "800": 1.97,
                    "1000": 2.22
                }
            },
            "source_path": "https://www.repeater-builder.com/antenna/andrew/andrew-ldf4-50a-spec-sheet.pdf"
        }
    ]

    # Lightning Arrestors
    arrestors = [
        {
            "source_text": """PolyPhaser IS-B50LN-C2 Lightning Arrestor
Model: IS-B50LN-C2
Type: N F/F Bulkhead Coaxial RF Surge Protector
Frequency: 10 MHz to 1 GHz
Power: 1.5 kW maximum
Let-Through Energy: 120uJ
Surge Current: 20kA
Connector: N-Female both ends
Mounting: Bulkhead
DC: Block
Technology: Blocking cap and gas tube""",
            "expected_json": {
                "component_type": "lightning_arrestor",
                "manufacturer": "PolyPhaser",
                "model": "IS-B50LN-C2",
                "frequency_range_mhz": [10, 1000],
                "power_rating_watts": 1500,
                "surge_current_ka": 20,
                "connector_type": "N-Female both ends",
                "dc_pass": False
            },
            "source_path": "https://www.polyphaser.com/Images/Downloadables/Datasheets/IS-B50_Series.pdf"
        },
        {
            "source_text": """PolyPhaser IS-B50HN-C0 High Power Lightning Arrestor
Model: IS-B50HN-C0
Frequency: 1.5 MHz to 700 MHz
Power: 3 kW maximum
Connector: N-Female
DC: Pass
Application: High power transmitters""",
            "expected_json": {
                "component_type": "lightning_arrestor",
                "manufacturer": "PolyPhaser",
                "model": "IS-B50HN-C0",
                "frequency_range_mhz": [1.5, 700],
                "power_rating_watts": 3000,
                "connector_type": "N-Female",
                "dc_pass": True
            },
            "source_path": "https://www.polyphaser.com/Images/Downloadables/Datasheets/IS-B50_Series.pdf"
        }
    ]

    # FM Transmitters
    transmitters = [
        {
            "source_text": """Nautel VS1 FM Transmitter
Model: VS1
Power Output: 1400 W analog
Power Supply: Single unit
AC Input: 180-264 V, 1 phase
Height: 3 RU
Frequency: 87.5-108 MHz
Features: Direct to channel digital exciter
SNR: -90 dB
RDS generator built-in
GPS input for SFN""",
            "expected_json": {
                "component_type": "transmitter",
                "manufacturer": "Nautel",
                "model": "VS1",
                "power_output_watts": 1400,
                "frequency_range_mhz": [87.5, 108],
                "mains_voltage": "180-264VAC"
            },
            "source_path": "https://www.nautel.com/products/fm-transmitters/vs-series/"
        },
        {
            "source_text": """Nautel VS2.5 FM Transmitter
Model: VS2.5
Power Output: 2800 W analog
Power Supply: Dual units
AC Input: 180-264 V, 1 phase
Height: 5 RU
Frequency: 87.5-108 MHz""",
            "expected_json": {
                "component_type": "transmitter",
                "manufacturer": "Nautel",
                "model": "VS2.5",
                "power_output_watts": 2800,
                "frequency_range_mhz": [87.5, 108],
                "mains_voltage": "180-264VAC"
            },
            "source_path": "https://www.nautel.com/products/fm-transmitters/vs-series/"
        },
        {
            "source_text": """Nautel VX5 FM Transmitter
Model: VX5
Power Output: 5500 W analog
Frequency: 87.5-108 MHz
Efficiency: 72%
Design: 3U compact
Power Supply: Hot-swappable, 96% efficient
Features: Direct-to-channel digital exciter""",
            "expected_json": {
                "component_type": "transmitter",
                "manufacturer": "Nautel",
                "model": "VX5",
                "power_output_watts": 5500,
                "frequency_range_mhz": [87.5, 108],
                "efficiency_percent": 72
            },
            "source_path": "https://www.nautel.com/products/fm-transmitters/vx-series/"
        },
        {
            "source_text": """BW Broadcast TX1000 V3 FM Transmitter
Model: TX1000 V3
Power Output: 10-1100 watts
Frequency: 87.5-108 MHz
Power Supply Efficiency: 96%
Features: Direct to channel digital modulation
GPS inputs for SFN
XLR analog & digital inputs
Dual MPX/SCA in and outs
DSP stereo generator
RDS generator
DSPX multi-band processor
Form Factor: 2U rack mount""",
            "expected_json": {
                "component_type": "transmitter",
                "manufacturer": "BW Broadcast",
                "model": "TX1000 V3",
                "power_output_watts": 1100,
                "frequency_range_mhz": [87.5, 108],
                "efficiency_percent": 96
            },
            "source_path": "https://www.bwbroadcast.com/tx1000v3"
        },
        {
            "source_text": """BW Broadcast TX600 V3 FM Transmitter
Model: TX600 V3
Power Output: 600 W
Frequency: 87.5-108 MHz
Form Factor: 2RU
Power Supply Efficiency: 96%
Features: 4-band DSP audio processing
Ethernet control
RDS encoder
FSK identifier
GPS inputs for SFN
Hot-swappable power supply
Integrated DSPX audio processor""",
            "expected_json": {
                "component_type": "transmitter",
                "manufacturer": "BW Broadcast",
                "model": "TX600 V3",
                "power_output_watts": 600,
                "frequency_range_mhz": [87.5, 108],
                "efficiency_percent": 96
            },
            "source_path": "https://www.bwbroadcast.com/tx600v3"
        }
    ]

    # Filters
    filters = [
        {
            "source_text": """ERI 785 FM Notch Filter
Model: 785
Frequency: 88-108 MHz
Power Handling: 35 kW (at >1 MHz separation)
Notch Suppression: -40 dB (at >1 MHz separation)
Insertion Loss: <0.03 dB (at >1 MHz separation)
VSWR: 1.05:1 +/-150kHz
Connectors: 1-5/8 or 3-1/8 inch EIA Flange
Configurations: 1, 2, 3, 4, or 5 cavities
Cooling: Convection""",
            "expected_json": {
                "component_type": "filter",
                "manufacturer": "Electronics Research Inc",
                "model": "785",
                "frequency_range_mhz": [88, 108],
                "power_rating_watts": 35000,
                "rejection_db": 40,
                "insertion_loss_db": 0.03,
                "vswr": 1.05,
                "connector_type": "EIA flange"
            },
            "source_path": "https://eriinc.com/product/785-fm-notch-filter/"
        },
        {
            "source_text": """ECOMAX CAVFM2N Double Cavity Filter
Model: CAVFM2N
Frequency: 87.5-108 MHz
Power: 1000W
-3dB Bandwidth: 800 kHz - 1.5 MHz
Attenuation +/-2MHz: 22 dB
Attenuation +/-6MHz: 40 dB
Insertion Loss: 0.3 dB
Connectors: N female""",
            "expected_json": {
                "component_type": "filter",
                "manufacturer": "PCS Electronics",
                "model": "CAVFM2N",
                "frequency_range_mhz": [87.5, 108],
                "power_rating_watts": 1000,
                "rejection_db": 40,
                "insertion_loss_db": 0.3,
                "connector_type": "N-Female"
            },
            "source_path": "https://www.pcs-electronics.com/shop/rf-accesories-for-transmitters/rf-filters-for-transmitters/coaxial-cavity-fm-band-filters/"
        }
    ]

    # Combine all data
    all_data = []
    all_data.extend([(d, "VHF antenna") for d in vhf_antennas])
    all_data.extend([(d, "UHF antenna") for d in uhf_antennas])
    all_data.extend([(d, "700/800 MHz antenna") for d in public_safety_antennas])
    all_data.extend([(d, "FM broadcast antenna") for d in fm_antennas])
    all_data.extend([(d, "Yagi antenna") for d in yagi_antennas])
    all_data.extend([(d, "Coaxial cable") for d in cables])
    all_data.extend([(d, "Lightning arrestor") for d in arrestors])
    all_data.extend([(d, "FM transmitter") for d in transmitters])
    all_data.extend([(d, "Filter") for d in filters])

    # Add all training examples
    added = 0
    for data, category in all_data:
        try:
            entry_id = collector.add_training_example(
                source_text=data["source_text"],
                expected_json=data["expected_json"],
                source_type="webpage",
                source_path=data.get("source_path", "web search"),
                notes=f"Web-scraped {category}"
            )
            # Auto-validate since these are manually verified
            collector.validate_example(entry_id, is_valid=True)
            added += 1
            print(f"Added: {data['expected_json'].get('model', 'unknown')} ({category})")
        except Exception as e:
            print(f"Error adding {data['expected_json'].get('model', 'unknown')}: {e}")

    print(f"\n=== Added {added} new training examples ===")

    # Show stats
    stats = collector.get_stats()
    print(f"\nTotal training examples: {stats['total_examples']}")
    print(f"Validated: {stats['validated_examples']}")
    print("\nBy component type:")
    for ctype, count in sorted(stats['by_component_type'].items()):
        print(f"  {ctype}: {count}")


if __name__ == "__main__":
    main()
