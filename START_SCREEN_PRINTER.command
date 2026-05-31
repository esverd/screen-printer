#!/usr/bin/env bash
set -u

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$APP_DIR/screen-printer-launch.log"
DESKTOP_DIR="${HOME:-$APP_DIR}/Desktop"

cd "$APP_DIR" || exit 1

{
  echo "==== $(date -Is) Screen Printer launch ===="
  echo "APP_DIR=$APP_DIR"
  echo "HOME=${HOME:-unset}"
  echo "USER=${USER:-unknown}"
  echo "DISPLAY=${DISPLAY:-unset}"
  echo "XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-unset}"
  echo "PATH=$PATH"
  echo

  chmod +x "$APP_DIR/scripts/run_pi.sh" "$APP_DIR/run-screen-printer.sh" "$APP_DIR/START_SCREEN_PRINTER.command" "$APP_DIR/Screen Printer.desktop" 2>/dev/null || true

  if [ -d "$DESKTOP_DIR" ]; then
    cp "$APP_DIR/Screen Printer.desktop" "$DESKTOP_DIR/screen-printer.desktop" 2>/dev/null || true
    chmod +x "$DESKTOP_DIR/screen-printer.desktop" 2>/dev/null || true
  fi

  if [ ! -x "$APP_DIR/scripts/run_pi.sh" ]; then
    echo "ERROR: missing executable $APP_DIR/scripts/run_pi.sh"
    echo "The repo copy may be incomplete."
    read -r -p "Press Enter to close..." _
    exit 1
  fi

  echo "Starting Screen Printer..."
  "$APP_DIR/scripts/run_pi.sh"
  status=$?
  echo "Screen Printer exited with status $status"
  if [ "$status" -ne 0 ]; then
    echo
    echo "Launch failed. Log is saved at: $LOG_FILE"
    read -r -p "Press Enter to close..." _
  fi
  exit "$status"
} 2>&1 | tee -a "$LOG_FILE"
exit "${PIPESTATUS[0]}"
