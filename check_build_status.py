"""Check build status and look for WiX/PyInstaller logs"""
import os
import glob

print("="*60)
print("BUILD STATUS CHECK")
print("="*60)

# Check if dist was created
if os.path.exists('dist/VetRender'):
    print("\n✓ dist/VetRender folder exists")
    
    # Check for exe
    if os.path.exists('dist/VetRender/VetRender.exe'):
        size = os.path.getsize('dist/VetRender/VetRender.exe')
        print(f"  ✓ VetRender.exe found ({size/1024/1024:.1f} MB)")
    else:
        print("  ✗ VetRender.exe NOT FOUND")
    
    # Count files in dist
    files = []
    for root, dirs, filenames in os.walk('dist/VetRender'):
        files.extend(filenames)
    print(f"  Total files in dist: {len(files)}")
else:
    print("\n✗ dist/VetRender folder NOT FOUND")
    print("  Build may have failed or not run yet")

# Check for MSI
msi_files = glob.glob('*.msi')
if msi_files:
    print(f"\n✓ MSI file(s) found:")
    for msi in msi_files:
        size = os.path.getsize(msi)
        print(f"  - {msi} ({size/1024/1024:.1f} MB)")
else:
    print("\n✗ No MSI files found")

# Check for build artifacts
print("\nBuild artifacts:")
artifacts = ['*.wixobj', '*.wixpdb', 'harvested_files.wxs']
for pattern in artifacts:
    files = glob.glob(pattern)
    if files:
        print(f"  Found: {', '.join(files)}")

# Check for log files
print("\nLooking for error logs:")
if os.path.exists('build'):
    print("  build/ folder exists")
    
log_patterns = ['*.log', 'build/*.log', 'dist/*.log']
for pattern in log_patterns:
    logs = glob.glob(pattern)
    if logs:
        print(f"  Found logs: {', '.join(logs)}")

print("\n" + "="*60)
print("To see the actual build output:")
print("  Run: build_all.bat")
print("  Watch the console for errors")
print("="*60)
