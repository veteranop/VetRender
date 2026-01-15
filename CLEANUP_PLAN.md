# VetRender Cleanup & Installer Fix Plan
**Generated:** 2025-01-16

## Files to DELETE (Safe to Remove)

### Documentation Files (Keep Only README.md and LICENSE)
- [ ] AI_BUTTON_FIX.md
- [ ] AI_LOGGING_GUIDE.md
- [ ] ANTENNA_LIBRARY_IMPLEMENTATION.md
- [ ] ANTENNA_METADATA_EXTRACTION.md
- [ ] BUG_FIXES_AI_IMPORT.md
- [ ] DEBUG_SUMMARY.md
- [ ] HOW_TO_ADD_TO_PATH.txt
- [ ] LLM_XML_BUG_FIX.md
- [ ] MSI_BUILD_README.md
- [ ] MSI_INSTALLER_GUIDE.txt
- [ ] OLLAMA_TROUBLESHOOTING.md
- [ ] POWERSHELL_SCRIPT_UPDATE.md
- [ ] PYINSTALLER_QT_FIX.txt
- [ ] QUICK_FIX_METADATA.md
- [ ] RUN_THIS_TO_CLEANUP.txt
- [ ] START_HERE.txt
- [ ] WIX_V6_INSTRUCTIONS.txt

### Duplicate/Old Files
- [ ] gui/dialogs_FIXED.py (superseded by dialogs.py)
- [ ] gui/dialogs_header_fix.py (superseded by dialogs.py)
- [ ] apply_metadata_extraction.py (one-time script)
- [ ] run_cleanup.py (redundant)
- [ ] main_window_TO_DEPLOY.py (not currently used)

### Batch Files to Keep
- [x] build_exe_only.bat (KEEP - builds executable)
- [x] build_installer.bat (KEEP - builds MSI)
- [x] git_push.bat (KEEP - convenience)
- [ ] CLEANUP_NOW.bat (DELETE after cleanup)
- [ ] cleanup_repo.bat (DELETE after cleanup)
- [ ] git_cleanup.bat (DELETE - redundant)
- [ ] add_wix_to_path.bat (KEEP - useful setup)

## Files to FIX

### 1. main_window_TO_DEPLOY.py
**Issue:** Wrong import path
```python
# CURRENT (WRONG):
from models.antenna import AntennaPattern

# SHOULD BE:
from models.antenna_models.antenna import AntennaPattern
```

### 2. vetrender.spec
**Issue:** Missing antenna_models subdirectory
```python
# ADD TO datas:
('models/antenna_models', 'models/antenna_models'),
```

### 3. installer.wxs
**Issue:** Hardcoded file references don't capture all files
**Fix:** Use heat.exe to auto-harvest all files

## Cleanup Script

See: `cleanup_final.py`

## Build Process After Cleanup

1. Run `cleanup_final.py`
2. Run `build_exe_only.bat`
3. Run `build_installer.bat`
4. Test the MSI installer

## Verification Checklist

After cleanup and rebuild:
- [ ] Application launches successfully
- [ ] All dialogs open correctly
- [ ] Antenna patterns can be loaded
- [ ] Propagation calculations work
- [ ] Terrain mode works
- [ ] MSI installs cleanly
- [ ] Desktop shortcut works
- [ ] Auto-updater functions
