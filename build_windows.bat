@echo off
setlocal enabledelayedexpansion

REM One-click Windows build script for launcher + updater.
REM Requires Python 3.10+ on Windows.

cd /d "%~dp0"

echo [1/5] Creating virtual environment...
if not exist .venv (
  py -3 -m venv .venv
)

call .venv\Scripts\activate.bat
if errorlevel 1 (
  echo Failed to activate virtual environment.
  exit /b 1
)

echo [2/5] Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 (
  echo Failed to install dependencies.
  exit /b 1
)

echo [3/5] Cleaning old build folders...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [4/5] Building updater.exe...
pyinstaller --noconfirm --clean --windowed --onefile --name updater updater.py
if errorlevel 1 (
  echo Failed to build updater.exe
  exit /b 1
)

echo [5/5] Building game_launcher.exe...
pyinstaller --noconfirm --clean --windowed --onefile --name game_launcher app.py
if errorlevel 1 (
  echo Failed to build game_launcher.exe
  exit /b 1
)

if not exist dist\package mkdir dist\package
copy /Y dist\updater.exe dist\package\updater.exe >nul
copy /Y dist\game_launcher.exe dist\package\game_launcher.exe >nul
copy /Y version.json dist\package\version.json >nul
copy /Y config.py dist\package\config.py >nul

echo Done. Ready files are in dist\package\
endlocal
