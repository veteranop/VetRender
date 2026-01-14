# VetRender Project System - User Guide

## Overview
VetRender now includes a comprehensive project management system that lets you save and load complete station configurations, including callsign, location, power settings, and antenna information.

## New Features

### 1. Station Information Panel (Left Side)

A permanent information panel now displays all your station details:

```
╔═══════════════════════════════╗
║      STATION DETAILS          ║
╚═══════════════════════════════╝

Callsign:     KDPI
Frequency:    88.5 MHz
Tx Mode:      FM
Tx Type:      Broadcast FM

╔═══════════════════════════════╗
║      LOCATION                 ║
╚═══════════════════════════════╝

Latitude:     43.661474°
Longitude:    -114.403802°
Height AGL:   30 m

╔═══════════════════════════════╗
║      POWER & ANTENNA          ║
╚═══════════════════════════════╝

ERP:          40 dBm
EIRP:         42.15 dBm
Antenna:      Default Omni (0 dBi)

╔═══════════════════════════════╗
║      COVERAGE SETTINGS        ║
╚═══════════════════════════════╝

Max Range:    50 km
Min Signal:   -110 dBm
Terrain:      Enabled
Quality:      High
```

### 2. Enhanced Initial Setup Dialog

When you first start VetRender or click "Reset Location", you'll see a comprehensive setup dialog with:

**Station Information Section:**
- **Callsign**: Your station identifier (e.g., KDPI, W1ABC, etc.)
- **Frequency (MHz)**: Operating frequency (e.g., 88.5 for FM, 146.52 for 2m, etc.)
- **TX Type**: Dropdown with options:
  - Broadcast FM
  - Broadcast AM
  - LPFM
  - HAM Radio
  - Amateur Radio
  - Commercial
  - Public Safety
  - Land Mobile
  - Point-to-Point
  - Other

- **TX Mode**: Dropdown with options:
  - FM
  - AM
  - SSB
  - C4FM
  - DMR
  - P25
  - NXDN
  - D-STAR
  - Analog
  - Digital
  - Other

**Transmitter Location Section:**
- **Latitude**: Decimal degrees (e.g., 43.661474)
- **Longitude**: Decimal degrees (e.g., -114.403802)
- **Height AGL (m)**: Antenna height above ground level
- **ERP (dBm)**: Effective Radiated Power
- **Go To Location** button to navigate map to entered coordinates

**Map Settings:** (same as before)
- Zoom level selection
- Basemap style
- Coverage radius

### 3. Project Save/Load System

#### Saving Projects

Click **"Save Project"** button in the left panel:
- Opens file dialog
- Default filename: `{Callsign}.vtr` (e.g., `KDPI.vtr`)
- File extension: `.vtr` (VetRender project)
- Saves in JSON format for easy editing

**What Gets Saved:**
- Station callsign
- Transmitter type and mode
- Location (lat/lon)
- Antenna height
- ERP
- Frequency
- Max distance
- Min signal threshold
- Terrain quality setting
- Antenna pattern name
- Map zoom and basemap style

#### Loading Projects

Click **"Load Project"** button in the left panel:
- Opens file dialog
- Select any `.vtr` file
- Instantly restores all settings
- Updates map to project location
- Refreshes information panel

### 4. Edit Station Info

Click **"Edit Station Info"** button to update:
- Station callsign
- Transmitter type
- Transmission mode

Updates are immediately reflected in the information panel.

## Usage Workflow

### First Time Setup
1. Launch VetRender
2. **Initial Setup Dialog** appears
3. Enter your station information:
   ```
   Callsign:    KDPI
   Frequency:   88.5 MHz
   TX Type:     Broadcast FM
   TX Mode:     FM
   Latitude:    43.661474
   Longitude:   -114.403802
   Height:      30 m
   ERP:         40 dBm
   ```
4. Set your map preferences
5. Click "Set This Area" → "Download & Continue"
6. Your station info panel is populated
7. Calculate coverage

### Saving Your Work
1. After configuring everything, click **"Save Project"**
2. Choose location and filename (e.g., `KDPI_SunValley.vtr`)
3. Project is saved

### Loading Existing Project
1. Click **"Load Project"**
2. Select your `.vtr` file
3. Everything is restored:
   - Station info
   - Location
   - Power settings
   - Antenna
   - Map position
   - Terrain settings

### Multiple Stations/Sites
You can manage multiple configurations:
```
Projects/
├── KDPI_SunValley.vtr       # Main FM broadcast site
├── KDPI_Repeater_East.vtr   # Eastern repeater
├── W7ABC_Home.vtr            # HAM station
└── TestSite_100km.vtr        # High-power test configuration
```

Each project loads independently with all settings.

## Project File Format

Projects are saved as JSON files (`.vtr`) that look like this:

```json
{
  "version": "2.0",
  "callsign": "KDPI",
  "tx_type": "Broadcast FM",
  "transmission_mode": "FM",
  "tx_lat": 43.661474,
  "tx_lon": -114.403802,
  "erp": 40,
  "frequency": 88.5,
  "height": 30,
  "max_distance": 50,
  "signal_threshold": -85,
  "terrain_quality": "High",
  "pattern_name": "Default Omni (0 dBi)",
  "zoom": 13,
  "basemap": "Esri WorldImagery"
}
```

**Advantage**: Human-readable and editable! You can:
- Open in any text editor
- Batch edit multiple files
- Use version control (Git)
- Share configurations with colleagues
- Script automated parameter sweeps

## Tips & Best Practices

### Naming Conventions
Use descriptive names:
- `{Callsign}_{Location}.vtr` - e.g., `KDPI_Bald_Mountain.vtr`
- `{Callsign}_{Purpose}.vtr` - e.g., `W1ABC_EmComm_Plan.vtr`
- `{Callsign}_{Power}W.vtr` - e.g., `KDPI_10W.vtr`

### Project Organization
Create folders for different scenarios:
```
VetRender_Projects/
├── Current/
│   └── KDPI_Active.vtr          # Current configuration
├── Planning/
│   ├── KDPI_50W_Option.vtr      # Power comparison
│   ├── KDPI_100W_Option.vtr
│   └── KDPI_Directional.vtr     # Antenna comparison
├── Sites/
│   ├── Site_A_Primary.vtr       # Multi-site setup
│   ├── Site_B_Repeater.vtr
│   └── Site_C_Backup.vtr
└── Archive/
    └── KDPI_2023_Original.vtr   # Historical records
```

### Documentation Workflow
1. Save initial configuration: `KDPI_Baseline.vtr`
2. Calculate coverage, take screenshots
3. Make changes (power, antenna, etc.)
4. Save as new version: `KDPI_Modified_v2.vtr`
5. Compare coverage plots
6. Keep final version: `KDPI_Final_FCC.vtr`

### FCC/Regulatory Filing
Your project files serve as documentation:
- Exact coordinates
- Power levels (ERP)
- Antenna height
- Frequency
- Calculated coverage

Save project file with your filing documents.

### Collaborative Work
Share project files with:
- Engineering consultants
- FCC coordinators
- Other station operators
- Equipment vendors

They can load your exact configuration and see your coverage predictions.

## Keyboard Shortcuts & Workflow

1. **Ctrl+S equivalent**: Click "Save Project" after changes
2. **Ctrl+O equivalent**: Click "Load Project" to switch projects
3. **Quick switch**: Keep multiple `.vtr` files in one folder, load as needed

## Information Panel Updates

The panel updates automatically when you:
- Change transmitter config (right-click → Edit Transmitter Configuration)
- Change antenna (right-click → Edit Antenna Information)
- Load a project
- Complete initial setup
- Reset location
- Edit station info

## Power Planning with Projects

**Example Workflow**:
1. Create base project: `KDPI_10W.vtr` (ERP: 37 dBm = 5W)
2. Calculate coverage
3. Save as `KDPI_20W.vtr`, change ERP to 40 dBm (10W)
4. Calculate coverage
5. Save as `KDPI_40W.vtr`, change ERP to 43 dBm (20W)
6. Calculate coverage
7. Compare all three plots
8. Choose minimum power that meets requirements

## Antenna Comparison with Projects

**Example Workflow**:
1. Load `KDPI_Base.vtr` with omni antenna
2. Calculate coverage
3. Load custom antenna XML pattern
4. Save as `KDPI_Directional.vtr`
5. Calculate coverage
6. Compare coverage and noise impact

## Integration with Existing Features

All existing features work with projects:
- ✅ Terrain calculations
- ✅ Shadow zone display
- ✅ Signal probing
- ✅ Zoom/pan (preserved per session, not per project)
- ✅ Custom antenna patterns
- ✅ Map cache (shared across projects)

## Troubleshooting

**"Project won't load"**
- Check file is valid JSON
- Ensure all required fields present
- Look for typos in coordinates

**"Information panel doesn't update"**
- Close and reopen application
- Check console for errors
- Verify project file format

**"Want to share project but it has cached data"**
- Just share the `.vtr` file
- Cache is separate (not in project)
- Recipient will download maps when they load it

## Advanced: Batch Processing (Future)

Since projects are JSON, you can script parameter sweeps:
```python
import json

# Load base project
with open('KDPI_Base.vtr') as f:
    config = json.load(f)

# Create power sweep
for erp in range(37, 46, 3):  # 5W to 25W in 3dB steps
    config['erp'] = erp
    with open(f'KDPI_{erp}dBm.vtr', 'w') as f:
        json.dump(config, f, indent=2)
```

Then load each project and calculate coverage in VetRender.

## Summary

The project system gives you:
- **Professional documentation** for FCC filings
- **Easy comparison** of different configurations
- **Quick switching** between sites/stations
- **Shareable configurations** with colleagues
- **Version control** for your planning
- **At-a-glance information** about current setup

Perfect for broadcast engineers, HAM operators, and RF professionals managing multiple sites or configurations.
