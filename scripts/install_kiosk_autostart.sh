#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="screen-printer-kiosk.service"
DEFAULT_IMAGE_DIR="/home/sverd/Pictures/screen-prints"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOME_DIR="${HOME:?HOME must be set}"
XDG_CONFIG_HOME_VALUE="${XDG_CONFIG_HOME:-$HOME_DIR/.config}"
SERVICE_DIR="$XDG_CONFIG_HOME_VALUE/systemd/user"
SERVICE_PATH="$SERVICE_DIR/$SERVICE_NAME"
AUTOSTART_DIR="$XDG_CONFIG_HOME_VALUE/autostart"
AUTOSTART_PATH="$AUTOSTART_DIR/screen-printer-kiosk.desktop"
IMAGE_DIR="${SCREEN_PRINTER_IMAGE_DIR:-$DEFAULT_IMAGE_DIR}"
ACTION="help"
YES=0
FORCE=0
DRY_RUN=0
START_AFTER_INSTALL=0
WRITE_XDG_AUTOSTART=1

usage() {
  cat <<EOF
Screen Printer kiosk autostart helper (user systemd, opt-in)

Usage:
  $0 install [--yes] [--image-dir DIR] [--start] [--force] [--dry-run] [--no-xdg-autostart]
  $0 print-service|print-autostart [--image-dir DIR]
  $0 start|stop|restart|disable|status|logs
  $0 help

Modes are a choice:
  - Regular/manual desktop mode: run scripts/install_pi.sh, then launch from the desktop/menu.
  - Kiosk/SPI mode: run this helper to install an autostart service for $SERVICE_NAME.

Safety:
  - install only writes/enables autostart files when --yes is passed.
  - install refuses to overwrite $SERVICE_PATH or $AUTOSTART_PATH unless --force is passed.
  - no reboot or poweroff is performed.
  - the desktop autostart file needs the Pi user to auto-login to the graphical desktop.
  - loginctl enable-linger is not run automatically. If you explicitly want this
    service to run without a graphical login, run it yourself after understanding
    the tradeoff: loginctl enable-linger "${USER:-your-user}"

Default image directory:
  $DEFAULT_IMAGE_DIR

Examples:
  SCREEN_PRINTER_IMAGE_DIR="$IMAGE_DIR" $0 install --yes
  $0 install --yes --image-dir "$DEFAULT_IMAGE_DIR"
  $0 print-autostart
  $0 start
  $0 status
  $0 logs
  $0 disable
EOF
}

render_autostart() {
  local quoted_app_dir quoted_image_dir
  quoted_app_dir="$(quote_shell_single "$APP_DIR")"
  quoted_image_dir="$(quote_shell_single "$IMAGE_DIR")"
  cat <<EOF
[Desktop Entry]
Type=Application
Name=Screen Printer Kiosk
Comment=Start Screen Printer fullscreen kiosk mode
Exec=/bin/bash -lc "SCREEN_PRINTER_IMAGE_DIR=$quoted_image_dir $quoted_app_dir/scripts/run_kiosk.sh"
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
}

quote_shell_single() {
  printf "'%s'" "$(printf "%s" "$1" | sed "s/'/'\\\\''/g")"
}

quote_systemd_env() {
  # systemd Environment= uses shell-like quoting for spaces/special characters.
  printf '%q' "$1"
}

render_service() {
  local quoted_image_dir
  quoted_image_dir="$(quote_systemd_env "$IMAGE_DIR")"
  cat <<EOF
[Unit]
Description=Screen Printer kiosk
Documentation=file://$APP_DIR/README.md
After=graphical-session.target
PartOf=graphical-session.target

[Service]
Type=simple
Environment=SCREEN_PRINTER_IMAGE_DIR=$quoted_image_dir
Environment=DISPLAY=:0
Environment=XAUTHORITY=%h/.Xauthority
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/scripts/run_kiosk.sh
Restart=on-failure
RestartSec=3

[Install]
WantedBy=graphical-session.target
EOF
}

need_systemctl_user() {
  if ! command -v systemctl >/dev/null 2>&1; then
    echo "systemctl is not installed; user systemd service management is unavailable." >&2
    exit 1
  fi
}

run_systemctl_user() {
  need_systemctl_user
  systemctl --user "$@"
}

install_service() {
  if [ "$YES" -ne 1 ]; then
    cat <<EOF
Dry preview only. This helper can write a user systemd service at:
  $SERVICE_PATH
and a desktop autostart file at:
  $AUTOSTART_PATH

It will scan images from:
  $IMAGE_DIR

Review the generated service with:
  $0 print-service --image-dir "$IMAGE_DIR"
  $0 print-autostart --image-dir "$IMAGE_DIR"

Install explicitly with:
  $0 install --yes --image-dir "$IMAGE_DIR"

EOF
    exit 0
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    echo "Would create image directory: $IMAGE_DIR"
    echo "Would write service: $SERVICE_PATH"
    if [ "$WRITE_XDG_AUTOSTART" -eq 1 ]; then
      echo "Would write desktop autostart: $AUTOSTART_PATH"
    fi
    echo "Would run: systemctl --user daemon-reload"
    echo "Would run: systemctl --user enable $SERVICE_NAME"
    if [ "$START_AFTER_INSTALL" -eq 1 ]; then
      echo "Would run: systemctl --user start $SERVICE_NAME"
    fi
    exit 0
  fi

  mkdir -p "$SERVICE_DIR" "$IMAGE_DIR"
  if [ -e "$SERVICE_PATH" ] && [ "$FORCE" -ne 1 ]; then
    echo "Refusing to overwrite existing service: $SERVICE_PATH" >&2
    echo "Re-run with --force only if you intend to replace it." >&2
    exit 1
  fi
  if [ "$WRITE_XDG_AUTOSTART" -eq 1 ] && [ -e "$AUTOSTART_PATH" ] && [ "$FORCE" -ne 1 ]; then
    echo "Refusing to overwrite existing desktop autostart: $AUTOSTART_PATH" >&2
    echo "Re-run with --force only if you intend to replace it." >&2
    exit 1
  fi

  local tmp_path
  tmp_path="$(mktemp "$SERVICE_DIR/.screen-printer-kiosk.XXXXXX")"
  render_service > "$tmp_path"
  mv "$tmp_path" "$SERVICE_PATH"

  if [ "$WRITE_XDG_AUTOSTART" -eq 1 ]; then
    mkdir -p "$AUTOSTART_DIR"
    tmp_path="$(mktemp "$AUTOSTART_DIR/.screen-printer-kiosk.XXXXXX")"
    render_autostart > "$tmp_path"
    mv "$tmp_path" "$AUTOSTART_PATH"
    chmod +x "$AUTOSTART_PATH"
  fi

  run_systemctl_user daemon-reload
  run_systemctl_user enable "$SERVICE_NAME"
  if [ "$START_AFTER_INSTALL" -eq 1 ]; then
    run_systemctl_user start "$SERVICE_NAME"
  fi

  cat <<EOF
Installed $SERVICE_PATH
Desktop autostart: $AUTOSTART_PATH
Image directory: $IMAGE_DIR

Commands:
  Start now:  $0 start
  Stop:       $0 stop
  Status:     $0 status
  Logs:       $0 logs
  Disable:    $0 disable

No reboot was performed.
EOF
}

if [ "$#" -gt 0 ]; then
  case "$1" in
    install|print-service|print-autostart|start|stop|restart|disable|status|logs|help|--help|-h)
      ACTION="$1"
      shift
      ;;
    --*)
      # Backwards-compatible shorthand: ./install_kiosk_autostart.sh --yes
      # means install with options. With no args, keep ACTION=help.
      ACTION="install"
      ;;
    *)
      ACTION="$1"
      shift
      ;;
  esac
fi

while [ "$#" -gt 0 ]; do
  case "$1" in
    --yes)
      YES=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --no-xdg-autostart)
      WRITE_XDG_AUTOSTART=0
      shift
      ;;
    --start)
      START_AFTER_INSTALL=1
      shift
      ;;
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
      ACTION="help"
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$ACTION" in
  help|--help|-h)
    usage
    ;;
  install)
    install_service
    ;;
  print-service)
    render_service
    ;;
  print-autostart)
    render_autostart
    ;;
  start)
    run_systemctl_user start "$SERVICE_NAME"
    ;;
  stop)
    run_systemctl_user stop "$SERVICE_NAME"
    ;;
  restart)
    run_systemctl_user restart "$SERVICE_NAME"
    ;;
  disable)
    run_systemctl_user disable --now "$SERVICE_NAME"
    ;;
  status)
    run_systemctl_user status "$SERVICE_NAME"
    ;;
  logs)
    if ! command -v journalctl >/dev/null 2>&1; then
      echo "journalctl is not installed." >&2
      exit 1
    fi
    journalctl --user -u "$SERVICE_NAME" -f
    ;;
  *)
    echo "Unknown action: $ACTION" >&2
    usage >&2
    exit 2
    ;;
esac
