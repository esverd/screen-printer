#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$APP_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"

if ! "$PYTHON_BIN" - <<'PY'
import tkinter  # noqa: F401
PY
then
  echo "Tkinter is missing. Install it with: sudo apt install python3-tk" >&2
  exit 1
fi

"$PYTHON_BIN" -m venv "$VENV_DIR"
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -e "$APP_DIR"

DESKTOP_DIR="$HOME/Desktop"
APP_DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR" "$APP_DESKTOP_DIR"

DESKTOP_FILE="$APP_DESKTOP_DIR/screen-printer.desktop"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Screen Printer
Comment=Lightweight screen negative exposure app
Exec=$VENV_DIR/bin/screen-printer
Icon=$APP_DIR/src/screen_printer/assets/material_symbols/fullscreen.svg
Terminal=false
Categories=Graphics;Photography;
StartupNotify=false
EOF

cp "$DESKTOP_FILE" "$DESKTOP_DIR/screen-printer.desktop"
chmod +x "$DESKTOP_FILE" "$DESKTOP_DIR/screen-printer.desktop"

echo "Installed Screen Printer."
echo "Desktop launcher: $DESKTOP_DIR/screen-printer.desktop"
