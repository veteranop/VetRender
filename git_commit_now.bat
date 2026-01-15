@echo off
REM Quick Git Commit Script for v3.0.1
echo.
echo ========================================
echo Git Commit - VetRender v3.0.1
echo ========================================
echo.

cd /d "%~dp0"

echo [1/5] Checking git status...
git status

echo.
echo [2/5] Adding all changes...
git add .

echo.
echo [3/5] Committing changes...
git commit -m "Release v3.0.1: Fixed main_window indentation issues, updated help system"

echo.
echo [4/5] Creating version tag...
git tag -a v3.0.1 -m "Version 3.0.1 - Stable release with indentation fixes"

echo.
echo [5/5] Pushing to GitHub...
git push origin main
git push origin v3.0.1

echo.
echo ========================================
echo SUCCESS! v3.0.1 pushed to GitHub
echo ========================================
echo.
echo Next steps:
echo   1. Visit GitHub to verify the push
echo   2. Create a GitHub Release for v3.0.1
echo   3. Upload VetRender.exe from dist\VetRender\
echo.
pause
