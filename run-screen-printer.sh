#!/usr/bin/env bash
set -u

APP_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$APP_DIR/screen-printer-launch.log"

cd "$APP_DIR" || exit 1

{
  echo "==== $(date -Is) Screen Printer launch ===="
  echo "APP_DIR=$APP_DIR"
  echo "USER=${USER:-unknown}"
  echo "DISPLAY=${DISPLAY:-unset}"
  echo "PATH=$PATH"
  echo

  if [ ! -x "$APP_DIR/scripts/run_pi.sh" ]; then
    echo "ERROR: missing executable $APP_DIR/scripts/run_pi.sh"
    echo "Try: chmod +x scripts/run_pi.sh run-screen-printer.sh 'Screen Printer.desktop'"
    exit 1
  fi

  exec "$APP_DIR/scripts/run_pi.sh"
} >>"$LOG_FILE" 2>&1

status=$?
if command -v zenity >/dev/null 2>&1; then
  zenity --error --title="Screen Printer failed to launch" --text="See log:\n$LOG_FILE" 2>/dev/null || true
elif command -v xmessage >/dev/null 2>&1; then
  xmessage "Screen Printer failed to launch. See log: $LOG_FILE" || true
else
  echo "Screen Printer failed to launch. See log: $LOG_FILE" >&2
fi
exit "$status"
