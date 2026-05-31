@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating local virtual environment...
  python -m venv .venv || exit /b 1
)

".venv\Scripts\python.exe" -m pytest --version >nul 2>nul
if errorlevel 1 (
  echo Installing test dependencies into .venv...
  ".venv\Scripts\python.exe" -m pip install -e ".[dev]" || exit /b 1
)

".venv\Scripts\python.exe" -m pytest %*
