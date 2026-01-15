@echo off
REM VetRender MSI Builder with Auto-Harvesting
REM ===========================================
REM Creates a standalone MSI installer for VetRender
REM Uses WiX Heat to automatically include all files

echo.
echo ========================================
echo VetRender MSI Builder v3.0.1
echo ========================================
echo.

cd /d "%~dp0"

REM Step 1: Check Python
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed!
    pause
    exit /b 1
)
echo Python found!

REM Step 2: Install dependencies
echo.
echo [2/6] Installing dependencies...
pip install -r requirements.txt --break-system-packages
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Step 3: Build executable with PyInstaller
echo.
echo [3/6] Building executable with PyInstaller...
echo This may take 2-5 minutes...
echo.
pyinstaller vetrender.spec --clean
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)
echo Executable built successfully!

REM Step 4: Check for WiX Toolset
echo.
echo [4/6] Checking for WiX Toolset...
where heat.exe >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo WiX Toolset Not Found!
    echo ========================================
    echo.
    echo To create MSI installers, you need WiX Toolset.
    echo.
    echo Download from: https://wixtoolset.org/releases/
    echo Install WiX Toolset v3.11 or later
    echo.
    echo After installing, add WiX bin folder to PATH:
    echo   C:\Program Files (x86)\WiX Toolset v3.11\bin
    echo.
    echo Or run: add_wix_to_path.bat
    echo.
    echo ========================================
    echo.
    echo The standalone executable is ready at:
    echo   dist\VetRender\VetRender.exe
    echo.
    echo You can zip this folder and distribute it manually.
    echo.
    pause
    exit /b 0
)

REM Step 5: Harvest all files with Heat
echo.
echo [5/6] Harvesting files with WiX Heat...
heat.exe dir "dist\VetRender" -cg HarvestedFiles -gg -sfrag -srd -dr INSTALLFOLDER -var var.SourceDir -out harvested_files.wxs
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Heat harvesting failed
    pause
    exit /b 1
)
echo Files harvested successfully!

REM Step 6: Build MSI with WiX
echo.
echo [6/6] Building MSI installer with WiX...

REM Compile both WXS files to WIXOBJ
echo Compiling main installer...
candle installer.wxs -out installer.wixobj -dSourceDir=dist\VetRender
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Main WXS compilation failed
    pause
    exit /b 1
)

echo Compiling harvested files...
candle harvested_files.wxs -out harvested_files.wixobj -dSourceDir=dist\VetRender
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Harvested WXS compilation failed
    pause
    exit /b 1
)

REM Link all WIXOBJ files to MSI
echo Linking MSI...
light installer.wixobj harvested_files.wixobj -out VetRender-3.0.1.msi -ext WixUIExtension -b dist\VetRender
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: MSI linking failed
    pause
    exit /b 1
)

REM Cleanup temporary files
echo Cleaning up...
del installer.wixobj 2>nul
del harvested_files.wixobj 2>nul
del harvested_files.wxs 2>nul
del VetRender-3.0.1.wixpdb 2>nul

echo.
echo ========================================
echo BUILD COMPLETE! ✓
echo ========================================
echo.
echo MSI Installer created:
echo   VetRender-3.0.1.msi
echo   Size: %~z1 bytes
echo.
echo Standalone executable:
echo   dist\VetRender\VetRender.exe
echo.
echo Included modules:
echo   - gui (map_display, propagation_plot, dialogs, etc.)
echo   - controllers (propagation_controller)
echo   - models (antenna_models/antenna, map_cache, terrain, etc.)
echo   - auto_updater
echo   - debug_logger
echo.
echo Next steps:
echo   1. Test the MSI installer on a clean machine
echo   2. Verify all features work:
echo      - Application launches
echo      - Antenna patterns load
echo      - Propagation calculations work
echo      - Terrain mode functions
echo   3. Upload to GitHub as a release
echo   4. Users can download and install with one click!
echo.
pause
