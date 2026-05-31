#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_IMAGE_DIR="/home/sverd/Pictures/screen-prints"
IMAGE_DIR="${SCREEN_PRINTER_IMAGE_DIR:-$DEFAULT_IMAGE_DIR}"
ARGS=()

usage() {
  cat <<EOF
Usage: $0 [--image-dir DIR] [screen-printer args...]

Starts Screen Printer in kiosk/SPI mode. The image directory defaults to:
  $DEFAULT_IMAGE_DIR

Override with either:
  SCREEN_PRINTER_IMAGE_DIR=/path/to/images $0
  $0 --image-dir /path/to/images

Any remaining arguments are passed to screen-printer, for example:
  $0 --image-dir /tmp/screen-prints --geometry 480x320
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --image-dir)
      if [ "$#" -lt 2 ]; then
        echo "Missing value for --image-dir" >&2
        exit 2
      fi
      IMAGE_DIR="$2"
      shift 2
      ;;
    --image-dir=*)
      IMAGE_DIR="${1#--image-dir=}"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done

mkdir -p "$IMAGE_DIR"
exec "$APP_DIR/scripts/run_pi.sh" --kiosk --image-dir "$IMAGE_DIR" "${ARGS[@]}"
