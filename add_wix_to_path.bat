@echo off
REM Add WiX Toolset v6.0 to PATH
REM ==============================

echo.
echo ========================================
echo Adding WiX Toolset v6.0 to PATH
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: This script must be run as Administrator!
    echo.
    echo Right-click this file and choose "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo Adding WiX to system PATH...

REM Add WiX v6.0 bin folder to PATH
setx PATH "%PATH%;C:\Program Files\WiX Toolset v6.0\bin" /M

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! WiX added to PATH ✓
    echo ========================================
    echo.
    echo IMPORTANT:
    echo   1. Close ALL Command Prompt windows
    echo   2. Open a NEW Command Prompt
    echo   3. Test: wix --version
    echo   4. Then run: build_installer.bat
    echo.
) else (
    echo.
    echo ========================================
    echo FAILED!
    echo ========================================
    echo.
    echo Try the manual method:
    echo   1. Press Windows key
    echo   2. Type: environment
    echo   3. Click: Edit system environment variables
    echo   4. Click: Environment Variables
    echo   5. Edit Path
    echo   6. Add: C:\Program Files\WiX Toolset v6.0\bin
    echo.
)

pause
