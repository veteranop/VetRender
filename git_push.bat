@echo off
REM VetRender Git Setup and Push Script
REM =====================================

echo.
echo ========================================
echo VetRender - Git Setup and Push
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Git is installed
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Git is not installed or not in PATH!
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Check if already initialized
if not exist ".git" (
    echo [1/6] Initializing Git repository...
    git init
    echo.
) else (
    echo [1/6] Git repository already initialized ✓
    echo.
)

REM Add all files (respecting .gitignore)
echo [2/6] Adding files to Git...
git add .
echo.

REM Show what will be committed
echo [3/6] Files to be committed:
git status --short
echo.

REM Prompt for commit message
set /p COMMIT_MSG="Enter commit message (or press Enter for default): "
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update VetRender codebase

echo.
echo [4/6] Committing changes...
git commit -m "%COMMIT_MSG%"
echo.

REM Check if remote exists
git remote -v | find "origin" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [5/6] Setting up remote repository...
    echo.
    echo Please enter your GitHub repository URL
    echo Example: https://github.com/username/VetRender.git
    set /p REPO_URL="Repository URL: "
    git remote add origin !REPO_URL!
    echo Remote added: origin
    echo.
) else (
    echo [5/6] Remote 'origin' already exists ✓
    echo.
)

REM Push to GitHub
echo [6/6] Pushing to GitHub...
echo.
echo This will push to the main branch.
echo If this is your first push, you may need to authenticate.
echo.
pause

git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Code pushed to GitHub! 🎉
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Push failed. Common issues:
    echo ========================================
    echo 1. Branch might be named 'master' instead of 'main'
    echo    Try: git branch -M main
    echo    Then run this script again
    echo.
    echo 2. Authentication might have failed
    echo    Make sure you're logged into Git
    echo.
    echo 3. Remote URL might be incorrect
    echo    Check: git remote -v
    echo ========================================
)

echo.
pause
