# VetRender Cleanup & Build Guide
**Updated:** 2025-01-16

## What Was Fixed

### 1. **Cleaned Repository Structure**
- Removed 16+ unnecessary documentation files
- Removed duplicate/old dialog files
- Removed redundant batch files
- Repository is now clean and professional

### 2. **Fixed Build Configuration**
- **vetrender.spec** - Added explicit imports for antenna_models
- **installer.wxs** - Updated to use Heat for auto-harvesting files
- **build_installer.bat** - Now uses Heat to include ALL files automatically

### 3. **Added Verification Tools**
- **verify_build.py** - Checks that all modules are included in dist
- **cleanup_final.py** - Safe cleanup script
- **build_all.bat** - Master script that does everything

## Quick Start Guide

### Option 1: Build Everything (Recommended)
```batch
build_all.bat
```
This does everything in one go:
1. Cleans up the repo
2. Builds the executable
3. Verifies the build
4. Creates MSI installer

### Option 2: Step-by-Step Build
```batch
# 1. Clean repository (optional)
python cleanup_final.py

# 2. Build executable only
build_exe_only.bat

# 3. Verify the build
python verify_build.py

# 4. Create MSI installer
build_installer.bat
```

## File Structure

### Core Application Files
```
VetRender/
├── vetrender.py              # Main entry point
├── vetrender.spec            # PyInstaller config (FIXED)
├── auto_updater.py           # Update checker
├── debug_logger.py           # Logging system
├── requirements.txt          # Dependencies
│
├── gui/                      # GUI modules
│   ├── main_window.py        # Main application window
│   ├── map_display.py        # Map rendering
│   ├── propagation_plot.py   # Coverage plotting
│   ├── toolbar.py            # Toolbar controls
│   ├── menus.py              # Menu bar
│   ├── dialogs.py            # All dialogs
│   └── info_panel.py         # Info sidebar
│
├── controllers/              # Business logic
│   └── propagation_controller.py
│
├── models/                   # Data models
│   ├── antenna_models/
│   │   └── antenna.py        # AntennaPattern class
│   ├── antenna_library.py    # Library management
│   ├── map_cache.py          # Map tile caching
│   ├── map_handler.py        # Map fetching
│   ├── terrain.py            # Terrain data
│   └── propagation.py        # RF calculations
│
└── installer.wxs             # WiX installer config (FIXED)
```

### Build Files
```
build_exe_only.bat            # Build executable only
build_installer.bat           # Build MSI installer (FIXED)
build_all.bat                 # Master build script (NEW)
verify_build.py               # Verify build (NEW)
cleanup_final.py              # Cleanup script (NEW)
```

### Output Files
```
dist/VetRender/               # Standalone executable folder
  ├── VetRender.exe           # Main executable
  ├── gui/                    # GUI modules
  ├── controllers/            # Controllers
  ├── models/                 # Models (includes antenna_models!)
  ├── auto_updater.py
  ├── debug_logger.py
  ├── README.md
  └── LICENSE

VetRender-3.0.1.msi           # Windows installer
```

## Verification Checklist

After building, verify these features work:

### Application Launch
- [ ] Application starts without errors
- [ ] Console window shows version info
- [ ] Main window displays with map

### Core Features
- [ ] Map loads and displays correctly
- [ ] Transmitter location can be set
- [ ] Zoom controls work
- [ ] Different basemaps load

### Antenna System
- [ ] Default omni antenna is active
- [ ] Antenna info dialog opens
- [ ] XML antenna patterns can be loaded
- [ ] Antenna library functions

### Propagation
- [ ] Calculate coverage button works
- [ ] Coverage overlay displays
- [ ] Terrain mode can be enabled
- [ ] Shadow zones display correctly
- [ ] Signal probing works

### Project Management
- [ ] Projects can be saved (.vtr files)
- [ ] Projects can be loaded
- [ ] Auto-config saves/restores
- [ ] Plots manager works

### Installer
- [ ] MSI installs cleanly
- [ ] Start menu shortcut created
- [ ] Desktop shortcut created
- [ ] Application launches from shortcuts
- [ ] Uninstall works cleanly

## Troubleshooting

### Build Fails with "Module not found"
**Fix:** Run `pip install -r requirements.txt --break-system-packages`

### Heat.exe not found
**Fix:** Install WiX Toolset from https://wixtoolset.org/releases/
Or run: `add_wix_to_path.bat`

### Qt binding errors
**Fix:** This is normal - we use tkinter, not Qt. The build excludes Qt.

### Missing files in dist/
**Fix:** Check `verify_build.py` output. Rebuild with `build_exe_only.bat`

### MSI fails to build
**Fix:** 
1. Check that `dist/VetRender/VetRender.exe` exists
2. Verify WiX is in PATH: `where heat.exe`
3. Run `build_installer.bat` with verbose output

## What Changed from Original

### Removed Files
- 16 markdown documentation files (kept README and LICENSE)
- 3 duplicate dialog files
- 4 redundant batch files
- 2 one-time utility scripts

### Fixed Files
- **vetrender.spec** - Added explicit antenna_models imports
- **installer.wxs** - Switched to Heat auto-harvesting
- **build_installer.bat** - Added Heat workflow

### Added Files
- **verify_build.py** - Build verification tool
- **cleanup_final.py** - Safe cleanup script  
- **build_all.bat** - Master build script
- **CLEANUP_PLAN.md** - This guide

## Distribution

### For End Users
Distribute: `VetRender-3.0.1.msi`
- Double-click to install
- Creates Start Menu and Desktop shortcuts
- Installs to Program Files
- Can be uninstalled cleanly

### For Portable Use
Distribute: `dist/VetRender/` (entire folder as ZIP)
- Unzip anywhere
- Run VetRender.exe
- No installation needed
- Includes all dependencies

## Version History

### v3.0.1 (2025-01-16)
- Fixed module imports in spec file
- Implemented Heat auto-harvesting
- Added build verification
- Cleaned repository structure
- Improved installer workflow

### v3.0.0 (Previous)
- Initial refactored version
- Modular architecture
- Terrain diffraction fixes
- 360° azimuth sampling

## Support

For issues or questions:
1. Check `verify_build.py` output
2. Review console output during build
3. Check GitHub issues
4. Contact VetRender team

---

**Ready to build?** Run `build_all.bat` and you're done! 🚀
