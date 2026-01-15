@echo off
REM Master Build Script - Clean, Build, Verify, Package
REM ====================================================
REM This script does everything in one go

echo.
echo ========================================
echo VetRender Master Build Script
echo ========================================
echo.
echo This will:
echo   1. Clean up unnecessary files
echo   2. Build the executable
echo   3. Verify the build
echo   4. Create MSI installer
echo.
pause

REM Step 1: Cleanup
echo.
echo [Step 1/4] Cleaning repository...
python cleanup_final.py
if %ERRORLEVEL% NEQ 0 (
    echo Cleanup encountered errors, but continuing...
)

REM Step 2: Build executable
echo.
echo [Step 2/4] Building executable...
call build_exe_only.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

REM Step 3: Verify build
echo.
echo [Step 3/4] Verifying build...
python verify_build.py
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Verification found issues
    echo Continue anyway? (Ctrl+C to abort)
    pause
)

REM Step 4: Create installer
echo.
echo [Step 4/4] Creating MSI installer...
call build_installer.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Installer creation failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo MASTER BUILD COMPLETE! ✓
echo ========================================
echo.
echo Output files:
echo   - dist\VetRender\VetRender.exe (standalone)
echo   - VetRender-3.0.1.msi (installer)
echo.
echo Ready to distribute!
echo.
pause
