# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['vetrender.py'],
    pathex=[],
    binaries=[],
    datas=[('gui', 'gui'), ('controllers', 'controllers'), ('models', 'models'), ('auto_updater.py', '.'), ('debug_logger.py', '.'), ('README.md', '.'), ('LICENSE', '.')],
    hiddenimports=['PIL._tkinter_finder', 'packaging', 'packaging.version'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'pytest', 'jupyter', 'IPython', 'pandas', 'sklearn', 'tensorflow', 'torch'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='VetRender',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VetRender',
)
