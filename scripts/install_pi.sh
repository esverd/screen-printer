#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$APP_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RUNNER="$APP_DIR/scripts/run_pi.sh"
FOLDER_LAUNCHER="$APP_DIR/run-screen-printer.sh"
COMMAND_LAUNCHER="$APP_DIR/START_SCREEN_PRINTER.command"

chmod +x "$RUNNER" "$FOLDER_LAUNCHER" "$COMMAND_LAUNCHER"
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
cat > "$APP_DIR/Screen Printer.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Screen Printer
Comment=Run Screen Printer from this folder
Exec=/bin/bash -lc 'cd "\$(dirname "\$1")" && ./START_SCREEN_PRINTER.command' dummy %k
Icon=applications-graphics
Terminal=true
Categories=Graphics;Photography;
StartupNotify=false
EOF
chmod +x "$DESKTOP_FILE" "$DESKTOP_DIR/screen-printer.desktop" "$APP_DIR/Screen Printer.desktop" "$COMMAND_LAUNCHER"

POWEROFF_FILE="$APP_DIR/Power Off Pi.desktop"
cat > "$POWEROFF_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Power Off Pi
Comment=Safely shut down the Raspberry Pi now
Exec=systemctl poweroff
Icon=system-shutdown
Terminal=false
Categories=System;
StartupNotify=false
EOF
cp "$POWEROFF_FILE" "$DESKTOP_DIR/power-off-pi.desktop"
chmod +x "$POWEROFF_FILE" "$DESKTOP_DIR/power-off-pi.desktop"

echo "Installed Screen Printer."
echo "Desktop launcher: $DESKTOP_DIR/screen-printer.desktop"
