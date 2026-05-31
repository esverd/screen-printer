@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating local virtual environment...
  python -m venv .venv || exit /b 1
)

".venv\Scripts\python.exe" -m pip show screen-printer >nul 2>nul
if errorlevel 1 (
  echo Installing Screen Printer into .venv...
  ".venv\Scripts\python.exe" -m pip install -e . || exit /b 1
)

".venv\Scripts\python.exe" -m screen_printer --geometry 480x320 %*
