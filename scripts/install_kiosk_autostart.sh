#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_PATH="$SERVICE_DIR/screen-printer-kiosk.service"
IMAGE_DIR="${SCREEN_PRINTER_IMAGE_DIR:-/home/sverd/Pictures/screen-prints}"

if [ "${1:-}" != "--yes" ]; then
  cat <<EOF
This opt-in helper writes a user systemd service at:
  $SERVICE_PATH

It will not overwrite an existing service. It enables Screen Printer kiosk mode
for this Linux user and starts it on graphical login.

Run to install:
  SCREEN_PRINTER_IMAGE_DIR="$IMAGE_DIR" $0 --yes

EOF
  exit 0
fi

mkdir -p "$SERVICE_DIR" "$IMAGE_DIR"
if [ -e "$SERVICE_PATH" ]; then
  echo "Refusing to overwrite existing service: $SERVICE_PATH" >&2
  exit 1
fi

cat > "$SERVICE_PATH" <<EOF
[Unit]
Description=Screen Printer kiosk
After=graphical-session.target

[Service]
Type=simple
Environment=SCREEN_PRINTER_IMAGE_DIR=$IMAGE_DIR
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/scripts/run_kiosk.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable screen-printer-kiosk.service
cat <<EOF
Installed $SERVICE_PATH

Start now with:
  systemctl --user start screen-printer-kiosk.service

View logs with:
  journalctl --user -u screen-printer-kiosk.service -f

Disable with:
  systemctl --user disable --now screen-printer-kiosk.service
EOF
