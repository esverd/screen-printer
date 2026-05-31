#!/usr/bin/env bash
set -u

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
HOME_DESKTOP_DIR="${HOME:-$APP_DIR}/Desktop"
PARENT_DIR="$(dirname "$APP_DIR")"
FOLDER_LOG_FILE="$APP_DIR/screen-printer-launch.log"
LOG_TARGETS=("$FOLDER_LOG_FILE")
if [ -d "$HOME_DESKTOP_DIR" ] && [ "$HOME_DESKTOP_DIR" != "$APP_DIR" ]; then
  LOG_TARGETS+=("$HOME_DESKTOP_DIR/screen-printer-launch.log")
fi
if [ "$(basename "$PARENT_DIR")" = "Desktop" ] && [ "$PARENT_DIR" != "$HOME_DESKTOP_DIR" ]; then
  LOG_TARGETS+=("$PARENT_DIR/screen-printer-launch.log")
fi

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

  chmod +x "$APP_DIR/scripts/run_pi.sh" "$APP_DIR/run-screen-printer.sh" 2>/dev/null || true

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
    echo "Launch failed. Logs are saved at:"
    printf '  %s\n' "${LOG_TARGETS[@]}"
    read -r -p "Press Enter to close..." _
  fi
  exit "$status"
} 2>&1 | tee -a "${LOG_TARGETS[@]}"
exit "${PIPESTATUS[0]}"
