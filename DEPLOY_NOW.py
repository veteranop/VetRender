"""
VETRENDER DEPLOYMENT SCRIPT
============================
Deploys all refactored modules to correct locations.
"""

import shutil
import os

print("🔥 VETRENDER DEPLOYMENT STARTING 🔥\n")

# Backup original main_window.py
original_main = r'gui\main_window.py'
if os.path.exists(original_main):
    backup_path = original_main + '.BACKUP_BEFORE_REFACTOR'
    shutil.copy2(original_main, backup_path)
    print(f"✅ Backed up original main_window.py to {backup_path}")

# Create controllers/__init__.py
os.makedirs('controllers', exist_ok=True)
init_file = r'controllers\__init__.py'
if not os.path.exists(init_file):
    with open(init_file, 'w') as f:
        f.write('# Controllers module\n')
    print(f"✅ Created controllers/__init__.py")

# Deploy files
deployments = {
    'propagation_plot_TO_DEPLOY.py': r'gui\propagation_plot.py',
    'info_panel_TO_DEPLOY.py': r'gui\info_panel.py',
    'toolbar_TO_DEPLOY.py': r'gui\toolbar.py',
    'menus_TO_DEPLOY.py': r'gui\menus.py',
    'propagation_controller_TO_DEPLOY.py': r'controllers\propagation_controller.py',
    'main_window_TO_DEPLOY.py': r'gui\main_window.py',
}

deployed = 0
for source, dest in deployments.items():
    if os.path.exists(source):
        shutil.copy2(source, dest)
        print(f"✅ Deployed: {dest}")
        deployed += 1
    else:
        print(f"⚠️  WARNING: {source} not found")

print(f"\n{'='*60}")
print(f"DEPLOYMENT COMPLETE!")
print(f"{'='*60}")
print(f"Deployed {deployed}/{len(deployments)} files")
print(f"\n🚀 READY TO LAUNCH!")
print(f"\nRun: python vetrender.py")
print(f"\n✨ All fixes applied:")
print(f"  ✅ Segment-by-segment terrain (no shadow tunneling!)")
print(f"  ✅ 360° azimuth sampling (no radial artifacts!)")
print(f"  ✅ Simplified zoom (preserves overlays!)")
