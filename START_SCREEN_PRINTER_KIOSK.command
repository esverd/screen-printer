#!/usr/bin/env bash
set -u

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$APP_DIR/screen-printer-kiosk-launch.log"
DESKTOP_DIR="${HOME:-$APP_DIR}/Desktop"

cd "$APP_DIR" || exit 1

{
  echo "==== $(date -Is) Screen Printer kiosk launch ===="
  echo "APP_DIR=$APP_DIR"
  echo "HOME=${HOME:-unset}"
  echo "USER=${USER:-unknown}"
  echo "DISPLAY=${DISPLAY:-unset}"
  echo "XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-unset}"
  echo "SCREEN_PRINTER_IMAGE_DIR=${SCREEN_PRINTER_IMAGE_DIR:-unset}"
  echo "PATH=$PATH"
  echo

  chmod +x "$APP_DIR/scripts/run_pi.sh" "$APP_DIR/scripts/run_kiosk.sh" "$APP_DIR/scripts/install_kiosk_autostart.sh" "$APP_DIR/scripts/confirm_poweroff.sh" "$APP_DIR/START_SCREEN_PRINTER.command" "$APP_DIR/START_SCREEN_PRINTER_KIOSK.command" "$APP_DIR/INSTALL_KIOSK_AUTOSTART.command" "$APP_DIR/Screen Printer.desktop" "$APP_DIR/Screen Printer Kiosk.desktop" 2>/dev/null || true

  if [ -d "$DESKTOP_DIR" ]; then
    cp "$APP_DIR/Screen Printer Kiosk.desktop" "$DESKTOP_DIR/screen-printer-kiosk.desktop" 2>/dev/null || true
    cp "$APP_DIR/Install Kiosk Autostart.desktop" "$DESKTOP_DIR/install-kiosk-autostart.desktop" 2>/dev/null || true
    cp "$APP_DIR/Power Off Pi.desktop" "$DESKTOP_DIR/power-off-pi.desktop" 2>/dev/null || true
    chmod +x "$DESKTOP_DIR/screen-printer-kiosk.desktop" "$DESKTOP_DIR/install-kiosk-autostart.desktop" "$DESKTOP_DIR/power-off-pi.desktop" 2>/dev/null || true
  fi

  if [ ! -x "$APP_DIR/scripts/run_kiosk.sh" ]; then
    echo "ERROR: missing executable $APP_DIR/scripts/run_kiosk.sh"
    echo "The repo copy may be incomplete."
    read -r -p "Press Enter to close..." _
    exit 1
  fi

  echo "Starting Screen Printer kiosk..."
  "$APP_DIR/scripts/run_kiosk.sh"
  status=$?
  echo "Screen Printer kiosk exited with status $status"
  if [ "$status" -ne 0 ]; then
    echo
    echo "Launch failed. Log is saved at: $LOG_FILE"
    read -r -p "Press Enter to close..." _
  fi
  exit "$status"
} 2>&1 | tee -a "$LOG_FILE"
exit "${PIPESTATUS[0]}"
