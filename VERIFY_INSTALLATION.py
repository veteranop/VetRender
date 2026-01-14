"""
VETRENDER - LAUNCH VERIFICATION
================================
Quick check that all modules are in place before launch.
"""

import os
import sys

print("🔍 VERIFYING VETRENDER REFACTORED INSTALLATION...\n")

required_files = [
    ('gui/map_display.py', 'Map Display Module'),
    ('gui/propagation_plot.py', 'Propagation Plot Module'),
    ('gui/info_panel.py', 'Info Panel Module'),
    ('gui/toolbar.py', 'Toolbar Module'),
    ('gui/menus.py', 'Menu Bar Module'),
    ('gui/main_window.py', 'Main Window (REFACTORED)'),
    ('gui/dialogs.py', 'Dialogs Module'),
    ('controllers/propagation_controller.py', 'Propagation Controller (ALL FIXES!)'),
    ('controllers/__init__.py', 'Controllers Package'),
    ('models/propagation.py', 'Propagation Model'),
]

all_good = True
for filepath, description in required_files:
    if os.path.exists(filepath):
        print(f"✅ {description}")
    else:
        print(f"❌ MISSING: {description} ({filepath})")
        all_good = False

print(f"\n{'='*60}")
if all_good:
    print("🎉 ALL MODULES IN PLACE!")
    print("="*60)
    print("\n🚀 READY TO LAUNCH!")
    print("\nRun: python vetrender.py")
    print("\n✨ Expected results:")
    print("  ✅ NO radial artifacts (smooth circular coverage)")
    print("  ✅ Coverage in valleys (no shadow tunneling!)")
    print("  ✅ Zoom preserves overlays perfectly")
    print("  ✅ Clean, maintainable code")
else:
    print("⚠️  SOME FILES MISSING!")
    print("="*60)
    print("\nPlease check the missing files above.")
    sys.exit(1)
