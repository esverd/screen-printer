#!/usr/bin/env bash
set -u

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$APP_DIR/screen-printer-kiosk-install.log"

cd "$APP_DIR" || exit 1

{
  echo "==== $(date -Is) Screen Printer kiosk autostart install ===="
  echo "APP_DIR=$APP_DIR"
  echo "HOME=${HOME:-unset}"
  echo "USER=${USER:-unknown}"
  echo "DISPLAY=${DISPLAY:-unset}"
  echo "XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-unset}"
  echo "SCREEN_PRINTER_IMAGE_DIR=${SCREEN_PRINTER_IMAGE_DIR:-unset}"
  echo "PATH=$PATH"
  echo

  chmod +x "$APP_DIR/scripts/run_pi.sh" "$APP_DIR/scripts/run_kiosk.sh" "$APP_DIR/scripts/install_kiosk_autostart.sh" "$APP_DIR/scripts/confirm_poweroff.sh" "$APP_DIR/START_SCREEN_PRINTER.command" "$APP_DIR/START_SCREEN_PRINTER_KIOSK.command" "$APP_DIR/INSTALL_KIOSK_AUTOSTART.command" "$APP_DIR/Screen Printer.desktop" "$APP_DIR/Screen Printer Kiosk.desktop" 2>/dev/null || true

  echo "Installing kiosk autostart with the default image folder."
  echo "Existing Screen Printer kiosk autostart files will be replaced."
  "$APP_DIR/scripts/install_kiosk_autostart.sh" install --yes --force --start
  status=$?
  echo "Kiosk autostart installer exited with status $status"
  echo
  echo "Log is saved at: $LOG_FILE"
  echo "Close this window, then reboot to verify boot-to-kiosk."
  read -r -p "Press Enter to close..." _
  exit "$status"
} 2>&1 | tee -a "$LOG_FILE"
exit "${PIPESTATUS[0]}"
