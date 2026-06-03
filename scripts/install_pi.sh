#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$APP_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RUNNER="$APP_DIR/scripts/run_pi.sh"
KIOSK_RUNNER="$APP_DIR/scripts/run_kiosk.sh"
POWEROFF_SCRIPT="$APP_DIR/scripts/confirm_poweroff.sh"
FOLDER_LAUNCHER="$APP_DIR/run-screen-printer.sh"
COMMAND_LAUNCHER="$APP_DIR/START_SCREEN_PRINTER.command"
KIOSK_COMMAND_LAUNCHER="$APP_DIR/START_SCREEN_PRINTER_KIOSK.command"
AUTOSTART_COMMAND_LAUNCHER="$APP_DIR/INSTALL_KIOSK_AUTOSTART.command"

chmod +x "$RUNNER" "$KIOSK_RUNNER" "$POWEROFF_SCRIPT" "$FOLDER_LAUNCHER" "$COMMAND_LAUNCHER" "$KIOSK_COMMAND_LAUNCHER" "$AUTOSTART_COMMAND_LAUNCHER"
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

KIOSK_DESKTOP_FILE="$APP_DESKTOP_DIR/screen-printer-kiosk.desktop"
cat > "$KIOSK_DESKTOP_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Screen Printer Kiosk
Comment=Fullscreen Screen Printer for the SPI display
Exec=$KIOSK_RUNNER
Icon=applications-graphics
Terminal=false
Categories=Graphics;Photography;
StartupNotify=false
EOF

cp "$KIOSK_DESKTOP_FILE" "$DESKTOP_DIR/screen-printer-kiosk.desktop"
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
cat > "$APP_DIR/Screen Printer Kiosk.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Screen Printer Kiosk
Comment=Run Screen Printer fullscreen kiosk mode from this folder
Exec=/bin/bash -lc 'cd "\$(dirname "\$1")" && ./START_SCREEN_PRINTER_KIOSK.command' dummy %k
Icon=applications-graphics
Terminal=true
Categories=Graphics;Photography;
StartupNotify=false
EOF
cat > "$APP_DIR/Install Kiosk Autostart.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Install Kiosk Autostart
Comment=Install Screen Printer kiosk boot startup
Exec=/bin/bash -lc 'cd "\$(dirname "\$1")" && ./INSTALL_KIOSK_AUTOSTART.command' dummy %k
Icon=preferences-system
Terminal=true
Categories=Settings;System;
StartupNotify=false
EOF
chmod +x "$DESKTOP_FILE" "$KIOSK_DESKTOP_FILE" "$DESKTOP_DIR/screen-printer.desktop" "$DESKTOP_DIR/screen-printer-kiosk.desktop" "$APP_DIR/Screen Printer.desktop" "$APP_DIR/Screen Printer Kiosk.desktop" "$APP_DIR/Install Kiosk Autostart.desktop" "$COMMAND_LAUNCHER" "$KIOSK_COMMAND_LAUNCHER" "$AUTOSTART_COMMAND_LAUNCHER"
cp "$APP_DIR/Install Kiosk Autostart.desktop" "$DESKTOP_DIR/install-kiosk-autostart.desktop"
chmod +x "$DESKTOP_DIR/install-kiosk-autostart.desktop"

POWEROFF_FILE="$APP_DIR/Power Off Pi.desktop"
cat > "$POWEROFF_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Power Off Pi
Comment=Confirm and safely shut down the Raspberry Pi
Exec=$POWEROFF_SCRIPT
Icon=system-shutdown
Terminal=false
Categories=System;
StartupNotify=false
EOF
cp "$POWEROFF_FILE" "$DESKTOP_DIR/power-off-pi.desktop"
chmod +x "$POWEROFF_FILE" "$DESKTOP_DIR/power-off-pi.desktop"

echo "Installed Screen Printer."
echo "Desktop launcher: $DESKTOP_DIR/screen-printer.desktop"
echo "Kiosk launcher: $DESKTOP_DIR/screen-printer-kiosk.desktop"
echo "Kiosk autostart installer: $DESKTOP_DIR/install-kiosk-autostart.desktop"
