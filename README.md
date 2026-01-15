# VetRender - RF Propagation Analysis Tool

**Professional RF propagation modeling software for analyzing radio coverage patterns with terrain analysis.**

<img width="1018" height="921" alt="image" src="https://github.com/user-attachments/assets/ccc7a692-d51b-4eab-880b-e0a16ffdf398" />
<img width="2550" height="1392" alt="image" src="https://github.com/user-attachments/assets/361d6a0b-f01f-4339-94f5-15496e9a02f6" />



## Features

✨ **Core Capabilities**
- 🗺️ **Interactive Map Viewer** - Multiple basemap styles (Satellite, Terrain, Street)
- 📡 **RF Propagation Engine** - Free-space path loss with terrain diffraction
- 🏔️ **Terrain Analysis** - Real elevation data with segment-by-segment LOS calculations
- 📊 **Coverage Visualization** - Beautiful gradient overlays with signal strength contours
- 🎯 **Antenna Patterns** - XML import for directional antenna modeling
- 💾 **Project Management** - Save/load complete coverage analyses

✨ **Advanced Features**
- 🔍 **Variable Zoom Levels** - 10-16 with intelligent caching
- 🎨 **Transparency Control** - Adjustable coverage overlay opacity
- 🎭 **Multiple Quality Presets** - Low/Medium/High/Ultra terrain analysis
- 📈 **Signal Probe** - Click-to-query signal strength at any location
- 🗂️ **Plot History** - Save and compare multiple coverage calculations
- ⚡ **Smart Caching** - Map tiles and terrain data cached for offline use
- 🤖 **AI Antenna Import** - Generate XML patterns from websites/PDFs using local LLM

## Installation

### Requirements
- Python 3.8 or higher
- Anaconda (recommended) or standard Python
- Ollama (automatically installed via AI Antenna Assistant)
- ~500MB disk space for cache

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/VetRender.git
cd VetRender
```

2. **Create virtual environment (optional but recommended)**
```bash
conda create -n vetrender python=3.10
conda activate vetrender
```

3. **Install dependencies**
```bash
pip install -r requirements.txt --break-system-packages
```

4. **Run VetRender**
```bash
python vetrender.py
```

5. **Setup AI Antenna Assistant (optional)**
   - Launch VetRender
   - Go to Antenna > AI Antenna Assistant
   - Click to auto-install Ollama and the AI model

## Quick Start

1. **Launch Application**
   ```bash
   python vetrender.py
   ```

2. **Project Setup**
   - Enter station details (callsign, frequency, location)
   - Optional: Setup AI Antenna Assistant via Antenna > AI Antenna Assistant (one-click install)
   - Optional: Import custom antenna pattern via Antenna > AI Antenna Import (provide website URL or PDF)
   - Select initial zoom level (13 recommended)
   - Choose basemap style
   - Application will cache map tiles automatically

3. **Calculate Coverage**
   - Click "Calculate" button in toolbar
   - Enable terrain analysis for realistic propagation
   - Adjust quality preset (Medium recommended)
   - Wait for calculation to complete

4. **Explore Results**
   - Use transparency slider to adjust overlay visibility
   - Right-click map to probe signal strength
   - Switch basemaps while preserving coverage
   - Save project for later analysis

## Usage Guide

### Basic Workflow

```
1. Configure Transmitter → 2. Calculate Coverage → 3. Analyze Results → 4. Save Project
```

### Transmitter Configuration
- **ERP (dBm)** - Effective Radiated Power
- **Frequency (MHz)** - Operating frequency
- **Height (m)** - Antenna height above ground level
- **Pattern** - Load XML antenna patterns or use default omni

### Quality Settings

| Quality | Azimuths | Distance Points | Calculation Time | Use Case |
|---------|----------|-----------------|------------------|----------|
| **Low** | 180 | 100 | Fast (~5-10s) | Quick preview |
| **Medium** | 540 | 200 | Moderate (~15-30s) | Daily use |
| **High** | 720 | 300 | Slow (~30-60s) | Detailed analysis |
| **Ultra** | 1080 | 500 | Very Slow (~1-2min) | Publication quality |

### Keyboard Shortcuts

- `Ctrl+N` - New Project
- `Ctrl+S` - Save Project
- `Ctrl+O` - Open Project
- `Ctrl+Q` - Quit Application

## Technical Details

### Propagation Model

VetRender uses a hybrid propagation model combining:

1. **Free Space Path Loss (FSPL)**
   ```
   FSPL(dB) = 20log₁₀(d) + 20log₁₀(f) + 32.45
   ```

2. **Terrain Diffraction Loss**
   - Knife-edge diffraction model
   - Segment-by-segment line-of-sight analysis
   - Fresnel zone clearance calculations

3. **Antenna Pattern Integration**
   - Azimuth-dependent gain
   - Elevation pattern support (future)

### Interpolation Methods

- **Gaussian Smoothing** - Reduces interpolation artifacts (σ=1.5)
- **Cubic Spline Interpolation** - Smooth azimuth transitions
- **Cartesian Grid** - Eliminates polar coordinate artifacts

### Data Sources

- **Maps** - OpenStreetMap, Esri, and other tile providers
- **Terrain** - Open-Elevation API (SRTM 30m resolution)
- **Caching** - Local SQLite database for offline capability

## Architecture

```
VetRender/
├── gui/                    # User interface modules
│   ├── main_window.py     # Application orchestration
│   ├── map_display.py     # Map rendering
│   ├── propagation_plot.py # Coverage overlays
│   ├── toolbar.py         # Top toolbar controls
│   ├── menus.py          # Menu bar
│   ├── info_panel.py     # Left sidebar info
│   └── dialogs.py        # Configuration dialogs
├── controllers/           # Business logic
│   └── propagation_controller.py # RF calculations
├── models/               # Data models
│   ├── antenna.py       # Antenna patterns
│   ├── propagation.py   # Propagation formulas
│   ├── terrain.py       # Terrain data handling
│   ├── map_handler.py   # Map tile management
│   └── map_cache.py     # Cache management
├── cache/                # Local cache (not in repo)
├── logs/                # Debug logs (not in repo)
└── vetrender.py         # Application entry point
```

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Credits

**Developer:** Mark D.  
**AI Assistant:** Claude (Anthropic)  
**Map Data:** OpenStreetMap contributors, Esri  
**Terrain Data:** Open-Elevation API

## Changelog

### Version 3.0 (Current)
- ✅ Complete refactor into modular architecture
- ✅ Fixed radial interpolation artifacts
- ✅ Added transparency control slider
- ✅ Improved terrain diffraction model
- ✅ Added plot history management
- ✅ Enhanced caching system
- ✅ Added multiple quality presets

### Version 2.0
- Initial terrain integration
- Basic GUI implementation
- Simple propagation calculations

### Version 1.0
- Proof of concept
- Basic free-space calculations

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Acknowledgments

Special thanks to:
- Anthropic for Claude AI assistance
- The RF engineering community
- Open-source mapping projects
- Python scientific computing ecosystem

---

**Built with ❤️ for RF engineers by RF engineers**
