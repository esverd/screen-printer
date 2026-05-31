#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$APP_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RUNNER="$APP_DIR/scripts/run_pi.sh"

chmod +x "$RUNNER"
"$RUNNER" --help >/dev/null

DESKTOP_DIR="$HOME/Desktop"
APP_DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR" "$APP_DESKTOP_DIR"

DESKTOP_FILE="$APP_DESKTOP_DIR/screen-printer.desktop"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Screen Printer
Comment=Lightweight screen negative exposure app
Exec=$RUNNER
Icon=applications-graphics
Terminal=false
Categories=Graphics;Photography;
StartupNotify=false
EOF

cp "$DESKTOP_FILE" "$DESKTOP_DIR/screen-printer.desktop"
cp "$DESKTOP_FILE" "$APP_DIR/Screen Printer.desktop"
chmod +x "$DESKTOP_FILE" "$DESKTOP_DIR/screen-printer.desktop" "$APP_DIR/Screen Printer.desktop"

echo "Installed Screen Printer."
echo "Desktop launcher: $DESKTOP_DIR/screen-printer.desktop"
