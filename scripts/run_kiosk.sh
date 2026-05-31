#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_DIR="${SCREEN_PRINTER_IMAGE_DIR:-/home/sverd/Pictures/screen-prints}"
mkdir -p "$IMAGE_DIR"
exec "$APP_DIR/scripts/run_pi.sh" --kiosk --image-dir "$IMAGE_DIR" "$@"
