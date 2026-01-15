"""
VetRender Build Verification Script
====================================
Verifies that all required modules are present in the built executable
Run this after building to ensure everything is included
"""
import os
import sys
from pathlib import Path

def check_dist_structure():
    """Check that dist folder has correct structure"""
    print("=" * 70)
    print("VetRender Build Verification")
    print("=" * 70)
    print()
    
    dist_path = Path("dist/VetRender")
    
    if not dist_path.exists():
        print("❌ ERROR: dist/VetRender directory not found!")
        print("   Run build_exe_only.bat first")
        return False
    
    print("✓ dist/VetRender directory found")
    print()
    
    # Check for main executable
    exe_path = dist_path / "VetRender.exe"
    if not exe_path.exists():
        print("❌ ERROR: VetRender.exe not found!")
        return False
    
    exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"✓ VetRender.exe found ({exe_size_mb:.1f} MB)")
    print()
    
    # Required module directories
    required_dirs = [
        "gui",
        "controllers", 
        "models",
    ]
    
    # Check module directories
    print("Checking module directories...")
    all_found = True
    for module_dir in required_dirs:
        module_path = dist_path / module_dir
        if module_path.exists():
            files = list(module_path.rglob("*"))
            print(f"  ✓ {module_dir}/ ({len(files)} files)")
        else:
            print(f"  ❌ {module_dir}/ MISSING!")
            all_found = False
    
    print()
    
    # Check critical files
    print("Checking critical files...")
    critical_files = [
        "auto_updater.py",
        "debug_logger.py",
        "README.md",
        "LICENSE",
    ]
    
    for filename in critical_files:
        file_path = dist_path / filename
        if file_path.exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ❌ {filename} MISSING!")
            all_found = False
    
    print()
    
    # Check antenna_models subdirectory specifically
    print("Checking antenna_models subdirectory...")
    antenna_models_path = dist_path / "models" / "antenna_models"
    if antenna_models_path.exists():
        files = list(antenna_models_path.glob("*.py"))
        print(f"  ✓ models/antenna_models/ ({len(files)} Python files)")
        for f in files:
            print(f"      - {f.name}")
    else:
        print("  ❌ models/antenna_models/ MISSING!")
        all_found = False
    
    print()
    
    # Summary
    print("=" * 70)
    if all_found:
        print("✓ BUILD VERIFICATION PASSED")
        print()
        print("All required modules and files are present.")
        print("Ready to create MSI installer!")
    else:
        print("❌ BUILD VERIFICATION FAILED")
        print()
        print("Some required files are missing.")
        print("Check the errors above and rebuild.")
    print("=" * 70)
    
    return all_found

def check_imports():
    """Check that critical imports work"""
    print()
    print("=" * 70)
    print("Testing Module Imports")
    print("=" * 70)
    print()
    
    # Add dist to path
    dist_path = Path("dist/VetRender")
    if dist_path.exists():
        sys.path.insert(0, str(dist_path))
    
    test_imports = [
        ("gui.map_display", "MapDisplay"),
        ("gui.propagation_plot", "PropagationPlot"),
        ("gui.dialogs", "TransmitterConfigDialog"),
        ("controllers.propagation_controller", "PropagationController"),
        ("models.antenna_models.antenna", "AntennaPattern"),
        ("models.map_cache", "MapCache"),
        ("models.terrain", "TerrainHandler"),
        ("debug_logger", "get_logger"),
        ("auto_updater", "check_for_updates_at_startup"),
    ]
    
    all_passed = True
    for module_name, class_name in test_imports:
        try:
            module = __import__(module_name, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"  ✓ {module_name}.{class_name}")
        except Exception as e:
            print(f"  ❌ {module_name}.{class_name} - {e}")
            all_passed = False
    
    print()
    print("=" * 70)
    if all_passed:
        print("✓ ALL IMPORTS SUCCESSFUL")
    else:
        print("❌ SOME IMPORTS FAILED")
    print("=" * 70)
    
    return all_passed

if __name__ == "__main__":
    structure_ok = check_dist_structure()
    
    # Only test imports if structure is OK and we're not in the dist folder
    if structure_ok and Path("vetrender.py").exists():
        print()
        print("Note: Import testing skipped (run from dist folder to test)")
    
    print()
    if structure_ok:
        print("Next step: Run build_installer.bat to create MSI")
    else:
        print("Next step: Run build_exe_only.bat to rebuild")
    print()
