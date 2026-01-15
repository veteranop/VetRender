@echo off
REM Alternative PyInstaller Build - Explicitly excludes Qt
REM =======================================================

echo.
echo ========================================
echo Building VetRender with PyInstaller
echo (Alternative method - excludes Qt)
echo ========================================
echo.

cd /d "%~dp0"

echo Building executable...
echo This may take 2-5 minutes...
echo.

pyinstaller ^
    --name=VetRender ^
    --onedir ^
    --console ^
    --clean ^
    --add-data "gui;gui" ^
    --add-data "controllers;controllers" ^
    --add-data "models;models" ^
    --add-data "auto_updater.py;." ^
    --add-data "debug_logger.py;." ^
    --add-data "README.md;." ^
    --add-data "LICENSE;." ^
    --hidden-import=PIL._tkinter_finder ^
    --hidden-import=packaging ^
    --hidden-import=packaging.version ^
    --exclude-module=PyQt5 ^
    --exclude-module=PyQt6 ^
    --exclude-module=PySide2 ^
    --exclude-module=PySide6 ^
    --exclude-module=pytest ^
    --exclude-module=jupyter ^
    --exclude-module=IPython ^
    --exclude-module=pandas ^
    --exclude-module=sklearn ^
    --exclude-module=tensorflow ^
    --exclude-module=torch ^
    vetrender.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo BUILD FAILED!
    echo ========================================
    echo.
    echo Common issues:
    echo   1. Missing dependencies - run: pip install -r requirements.txt
    echo   2. PyInstaller not installed - run: pip install pyinstaller
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD COMPLETE! ✓
echo ========================================
echo.
echo Executable created at:
echo   dist\VetRender\VetRender.exe
echo.
echo You can now run the full build_installer.bat to create MSI
echo.
pause
