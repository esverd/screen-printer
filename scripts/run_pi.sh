#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$APP_DIR/.venv"
PYTHON_BIN="${PYTHON_BIN:-python3}"
GEOMETRY="${SCREEN_PRINTER_GEOMETRY:-}"

ensure_tkinter() {
  "$PYTHON_BIN" - <<'PY'
import tkinter  # noqa: F401
PY
}

if [ ! -x "$VENV_DIR/bin/screen-printer" ]; then
  if ! ensure_tkinter; then
    echo "Tkinter is missing. Install it with:" >&2
    echo "  sudo apt update && sudo apt install -y python3-tk python3-venv" >&2
    exit 1
  fi
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip
  "$VENV_DIR/bin/python" -m pip install -e "$APP_DIR"
fi

if [ -n "$GEOMETRY" ]; then
  exec "$VENV_DIR/bin/screen-printer" --geometry "$GEOMETRY" "$@"
fi

exec "$VENV_DIR/bin/screen-printer" "$@"
