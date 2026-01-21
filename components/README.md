# VetRender Component Library

This directory contains RF component catalogs and cached lookups for building system loss budgets and equipment lists.

## Directory Structure

```
components/
├── catalogs/              # Pre-populated manufacturer catalogs
│   ├── manufacturers.json # Master list of manufacturers and resources
│   ├── andrew_commscope.json
│   ├── times_microwave.json
│   ├── polyphaser.json
│   ├── decibel_products.json
│   ├── bird_technologies.json
│   └── ...
│
├── cache/                 # User lookups and custom components
│   └── component_cache.json
│
└── README.md             # This file
```

## How It Works

### 1. Pre-populated Catalogs
Common RF components from major manufacturers are pre-loaded in JSON files:
- **Andrew/CommScope**: Heliax coax (LDF4, LDF5, LDF6, LDF7)
- **Times Microwave**: LMR flexible coax (LMR-195, 240, 400, 600, 900, 1200)
- **PolyPhaser**: Lightning arrestors (IS-B50LN, IS-50UX, DGXZ)
- **Decibel Products**: VHF/UHF antennas (DB224, DB404, DB408, DB420)
- **Bird Technologies**: Isolators, combiners, couplers, attenuators

These catalogs provide **instant lookup** without internet access.

### 2. Component Cache
When you search for a component not in the pre-populated catalogs:
1. VetRender queries **Ollama** (AI assistant) for specifications
2. Results are saved to `component_cache.json`
3. Future searches for the same part are instant

The cache **grows over time** as you look up more parts.

### 3. Component Database Fields

Each component includes:

**Common fields:**
- `component_type`: cable, connector, isolator, combiner, etc.
- `manufacturer`: Andrew, Times Microwave, PolyPhaser, etc.
- `model`: LDF4-50A, LMR-400, IS-B50LN-C0, etc.
- `part_number`: Manufacturer part number
- `description`: Human-readable description

**Cable-specific:**
- `loss_db_per_100ft`: Loss at various frequencies
- `velocity_factor`: Velocity factor (0.80-0.95)
- `impedance_ohms`: Characteristic impedance (usually 50)
- `power_rating_watts`: Maximum power at frequencies
- `outer_diameter_inches`: Physical size
- `minimum_bend_radius_inches`: Minimum bend radius

**Component-specific:**
- `insertion_loss_db`: Loss through device
- `isolation_db`: Isolation between ports (combiners, isolators)
- `frequency_range_mhz`: Valid frequency range
- `power_rating_watts`: Maximum power handling
- `connector_type`: N-type, SMA, etc.

**Optional:**
- `datasheet_url`: Link to manufacturer datasheet
- `common_uses`: Typical applications
- `notes`: Important information

## Usage in VetRender

### Station Information Window
1. Select transmitter, antenna, and other equipment
2. Build feedline by adding components in sequence
3. VetRender calculates:
   - Cable loss at your specific frequency (interpolated)
   - Total insertion loss from all components
   - System loss budget
   - ERP/EIRP

### Searching for Components
- Type part number or model name
- VetRender searches:
  1. Local pre-populated catalogs (instant)
  2. Component cache (instant if previously searched)
  3. Ollama AI search (if not found, requires internet)

### Adding Custom Components
- Manually enter specifications
- Save to component library for future use
- Export/import component libraries to share with colleagues

## Frequency Interpolation

Cable loss is stored at specific frequencies. VetRender interpolates for your exact frequency.

Example: LDF4-50A at 156.5 MHz
- Known: 150 MHz = 0.51 dB/100ft, 220 MHz = 0.63 dB/100ft
- Interpolated: 156.5 MHz ≈ 0.53 dB/100ft

## Ollama Integration (Future)

When Ollama integration is active:
- Search for unknown parts: "What are the specs for Belden 9913?"
- Get recommendations: "Best cable for 156 MHz, 200ft, max 1dB loss?"
- Auto-populate fields from manufacturer data

## Adding New Catalogs

To add a new manufacturer catalog:

1. Create `manufacturer_name.json` in `catalogs/`
2. Follow the existing JSON structure
3. Add entry to `manufacturers.json`
4. Include common products with full specifications

## Pre-populated Components Summary

### Andrew/CommScope Cables
- LDF4-50A (1/2"), LDF5-50A (7/8"), LDF6-50 (1-1/4"), LDF7-50A (1-5/8")
- Connectors and grounding kits

### Times Microwave Cables
- LMR-195, LMR-240, LMR-400, LMR-600, LMR-900, LMR-1200
- LMR-400-UF (ultra-flexible)

### PolyPhaser Lightning Protection
- IS-B50LN-C0/C2 (bulkhead)
- IS-50UX-C1 (ultra-low loss)
- DGXZ+05NF (inline)
- IS-B50HN-C0 (high power)

### Decibel Antennas
- VHF: DB220, DB224
- UHF: DB401, DB404, DB408
- Dual-band: DB420

### Bird Technologies
- Circulators/Isolators: CX series
- Combiners: APR-2, APR-4
- Couplers: 4240 series
- Attenuators, terminators

## Component Count
Current pre-populated components: **50+**

Components will grow as:
- More manufacturers added
- Users look up new parts (cached)
- Community shares component libraries

## File Format

All JSON files follow this structure:
```json
{
  "manufacturer": "Manufacturer Name",
  "manufacturer_id": "unique_id",
  "last_updated": "2026-01-19",
  "components": [
    {
      "component_type": "cable",
      "model": "PRODUCT-123",
      ...
    }
  ]
}
```

## Future Enhancements
- Import from CSV (bulk component loading)
- Price tracking for BOM estimates
- Photo attachments
- Availability checking
- Export to procurement systems
- Community-shared component database
