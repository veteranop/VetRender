# VetRender - RF Propagation Tool

A professional RF propagation modeling tool with terrain awareness and multiple basemap support.

## Project Structure

```
VetRender/
├── vetrender.py              # Main entry point - run this
├── models/                   # Data models and calculation engines
│   ├── __init__.py
│   ├── antenna.py           # Antenna pattern handling
│   ├── propagation.py       # RF propagation calculations
│   ├── terrain.py           # Terrain elevation data
│   └── map_handler.py       # Map tile fetching
└── gui/                      # User interface components
    ├── __init__.py
    ├── main_window.py       # Main application window
    └── dialogs.py           # Configuration dialogs
```

## Installation

1. **Make sure your Anaconda environment is active:**
   ```bash
   conda activate vetrender
   ```

2. **Create the directory structure:**
   ```bash
   cd C:\Users\markd\VetRender
   mkdir models
   mkdir gui
   ```

3. **Create empty `__init__.py` files:**
   ```bash
   type nul > models\__init__.py
   type nul > gui\__init__.py
   ```

4. **Copy all the Python files** into their respective directories:
   - `vetrender.py` → root directory
   - All `models/*.py` files → `models/` directory
   - All `gui/*.py` files → `gui/` directory

## Running VetRender

```bash
cd C:\Users\markd\VetRender
conda activate vetrender
python vetrender.py
```

## Features

- **Multiple Basemaps**: OpenStreetMap, OpenTopoMap, Esri Imagery, and more
- **Terrain-Aware Propagation**: Uses real elevation data for accurate modeling
- **Antenna Patterns**: Support for custom XML antenna patterns
- **Interactive Map**: Click to place transmitters, right-click for options
- **Real-time Calculation**: See coverage overlay on actual maps
- **Debug Logging**: All operations logged to console for troubleshooting

## Usage

1. **Set Transmitter Location**: Right-click on map → "Set Transmitter Location"
2. **Configure Transmitter**: Right-click → "Edit Transmitter Configuration"
3. **Load Antenna Pattern**: Right-click → "Edit Antenna Information"
4. **Calculate Coverage**: Click "Calculate Coverage" button in toolbar
5. **Change Basemap**: Use dropdown to select different map styles
6. **Enable Terrain**: Check "Use Terrain Data" for realistic path loss

## Dependencies

- numpy
- matplotlib
- pillow
- tkinter (included with Python)

## Notes

- Terrain calculations require internet connection
- Map tiles are fetched from public tile servers
- First run may be slower as map tiles are downloaded