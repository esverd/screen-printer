@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating local virtual environment...
  python -m venv .venv || exit /b 1
)

echo Installing Screen Printer and test dependencies into .venv...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -e ".[dev]" || exit /b 1

echo.
echo Ready. Run the app with:
echo   .\run.bat
