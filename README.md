# Screen Printer

Screen Printer is a lightweight Tkinter/Pillow app for showing adjusted image negatives on a small Linux display. It is designed for old Raspberry Pi-class hardware and a 3.5-inch screen.

## Features

- Load JPG, JPEG, and PNG images.
- Default grayscale preview, with a color toggle.
- Exposure, contrast, and blur sliders.
- Invert, rotate clockwise, horizontal flip, and vertical flip toggles.
- Full-screen Develop mode that hides the editor and mouse cursor.
- Full-screen editor/kiosk surface that hides the desktop taskbar while keeping controls visible.
- Confirmed in-app power-off control for dedicated Pi use.
- Triple-click or press Escape in Develop mode to show the exit confirmation.
- Versioned JSON sidecar files for settings and exposure metadata.

## Quick Start

On Windows PowerShell:

```powershell
.\setup.bat
.\run.bat
```

Or set up manually:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m screen_printer --geometry 480x320
```

Run tests:

```powershell
.\test.bat
```

On Linux:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
python -m screen_printer
```

For a small-screen local test:

```bash
python -m screen_printer --geometry 480x320
```

## Quick Start With uv

`uv` is a good fit for development because it keeps setup fast and repeatable. After installing `uv`, run:

```powershell
uv sync --extra dev
uv run screen-printer --geometry 480x320
uv run pytest
```

On Windows, `python3` and `.venv/bin/activate` usually will not work in PowerShell. If script activation is blocked by execution policy, use `.\run.bat` or call `.\.venv\Scripts\python.exe` directly instead of activating the environment.

## Raspberry Pi Install

### Easiest copy-from-USB flow

1. Copy the whole `screen-printer` folder from the USB stick to the Pi Desktop.
2. Open the copied folder.
3. Double-click `START_SCREEN_PRINTER.command`.

That is the most reliable mouse-only launcher. It opens a terminal, creates `.venv` inside the folder on first run, installs Screen Printer there, creates/refreshes a Desktop shortcut at `~/Desktop/screen-printer.desktop`, and keeps setup/error messages visible. Later runs reuse that local environment.

For the SPI screen, double-click `START_SCREEN_PRINTER_KIOSK.command` instead. It starts the app fullscreen, uses the in-app image library, and creates/refreshes a `~/Desktop/screen-printer-kiosk.desktop` shortcut. This is the best manual mouse-only launcher because it avoids the desktop taskbar and OS file picker.

To make the Pi boot into Screen Printer kiosk mode, double-click `INSTALL_KIOSK_AUTOSTART.command` after the regular launcher has successfully installed the Python environment. It installs/replaces the kiosk autostart files with the default image folder and starts the kiosk once immediately.

There are also `.desktop` launchers for desktop/menu integration, but if the Raspberry Pi desktop is picky about `.desktop` files, use the `.command` files once first. After that, try the generated Desktop shortcuts.

If double-click is blocked or nothing appears, open a terminal in the folder and run:

```bash
chmod +x START_SCREEN_PRINTER.command START_SCREEN_PRINTER_KIOSK.command INSTALL_KIOSK_AUTOSTART.command run-screen-printer.sh scripts/*.sh "Screen Printer.desktop" "Screen Printer Kiosk.desktop" "Install Kiosk Autostart.desktop"
./START_SCREEN_PRINTER.command
```

If launch fails, check `screen-printer-launch.log` in the project folder.

The installer creates launchers in three places:

- `START_SCREEN_PRINTER_KIOSK.command` inside the project folder - recommended SPI fullscreen launcher
- `INSTALL_KIOSK_AUTOSTART.command` inside the project folder - mouse-friendly kiosk boot installer
- `Screen Printer Kiosk.desktop` inside the project folder
- `Install Kiosk Autostart.desktop` inside the project folder
- `~/Desktop/screen-printer-kiosk.desktop`

- `START_SCREEN_PRINTER.command` inside the project folder — recommended double-click launcher
- `Screen Printer.desktop` inside the project folder
- `~/Desktop/screen-printer.desktop`
- `~/.local/share/applications/screen-printer.desktop`

It also creates a mouse-only shutdown launcher with a confirmation dialog:

- `Power Off Pi.desktop` inside the project folder
- `~/Desktop/power-off-pi.desktop`

Double-click **Power Off Pi**, then confirm shutdown before pulling power.

After that, Screen Printer can be launched from the desktop icon or the Raspberry Pi application menu.

If Tkinter or venv support is missing, install it first:

```bash
sudo apt update
sudo apt install python3-tk python3-venv
```

For the 3.5-inch screen, you can force a small window size:

```bash
SCREEN_PRINTER_GEOMETRY=480x320 ./scripts/run_pi.sh
```

Or hide the desktop taskbar while keeping the editor controls visible:

```bash
DISPLAY=:0 ./scripts/run_pi.sh --fullscreen
```

## Raspberry Pi: No HDMI / SSH Setup

Screen Printer supports two Raspberry Pi setup choices. Regular/manual desktop mode still works and is the safest first install. Kiosk/SPI mode is opt-in for a Pi that should boot into one fullscreen app and scan an image folder without using a file picker.

SSH into the Pi, then from this project folder run one of these paths.

### Choice 1: regular/manual desktop mode

Use this when the Pi has a normal desktop session and you want to launch Screen Printer manually from the desktop/menu:

```bash
sudo apt update
sudo apt install -y python3-tk python3-venv
chmod +x START_SCREEN_PRINTER.command run-screen-printer.sh scripts/*.sh
./scripts/install_pi.sh
```

Start it from SSH only if a graphical desktop is already running on the Pi display:

```bash
DISPLAY=:0 ./scripts/run_pi.sh
```

Or start with a small-window geometry:

```bash
DISPLAY=:0 SCREEN_PRINTER_GEOMETRY=480x320 ./scripts/run_pi.sh
```

### Choice 2: kiosk/SPI autostart mode

Kiosk mode is intended for the SPI screen: boot the Pi, launch one fullscreen Screen Printer app, and avoid desktop icons, taskbars, OS file pickers, terminals, and draggable windows on the small display.

For boot-to-app behavior on Raspberry Pi OS, the Pi user must log into a graphical desktop session automatically. In Raspberry Pi Configuration, set **Boot / Auto Login** to **Desktop Autologin**. Without desktop auto-login, the app cannot appear on the SPI display until a graphical session starts.

The default kiosk image folder is:

```text
/home/sverd/Pictures/screen-prints
```

Copy JPG/PNG images there by SSH/SFTP/Samba/USB. Override the folder with `--image-dir DIR` or `SCREEN_PRINTER_IMAGE_DIR=DIR`.

Install the kiosk autostart service explicitly:

```bash
sudo apt update
sudo apt install -y python3-tk python3-venv
chmod +x START_SCREEN_PRINTER.command run-screen-printer.sh scripts/*.sh
./scripts/install_kiosk_autostart.sh install --yes --image-dir /home/sverd/Pictures/screen-prints
```

Mouse-only equivalent after a successful first launch:

```text
Double-click INSTALL_KIOSK_AUTOSTART.command
```

The installer is intentionally non-destructive: by default it only previews; with `--yes` it writes/enables a user systemd service and a desktop autostart file at `~/.config/autostart/screen-printer-kiosk.desktop`; it refuses to overwrite existing autostart files unless you also pass `--force`; it does not reboot or power off.

Useful kiosk commands:

```bash
# Preview the service file without installing
./scripts/install_kiosk_autostart.sh print-service --image-dir /home/sverd/Pictures/screen-prints

# Preview the desktop autostart file without installing
./scripts/install_kiosk_autostart.sh print-autostart --image-dir /home/sverd/Pictures/screen-prints

# Start now, stop, disable, status, logs
./scripts/install_kiosk_autostart.sh start
./scripts/install_kiosk_autostart.sh stop
./scripts/install_kiosk_autostart.sh disable
./scripts/install_kiosk_autostart.sh status
./scripts/install_kiosk_autostart.sh logs
```

Run kiosk mode manually without installing autostart:

```bash
DISPLAY=:0 ./scripts/run_kiosk.sh --image-dir /home/sverd/Pictures/screen-prints
```

Kiosk mode opens the editor fullscreen, so the desktop taskbar should not consume screen space. The fullscreen toolbar button toggles this same editor fullscreen state in regular mode. Develop mode remains separate: it still shows only the rendered exposure image and uses the triple-click/Escape confirmation to exit.

If you intentionally want the user service to exist while no graphical login is active, read about systemd user lingering first, then run it manually yourself:

```bash
loginctl enable-linger "$USER"
```

The installer does not enable lingering automatically. The service is tied to `graphical-session.target` and sets `DISPLAY=:0`/`XAUTHORITY=%h/.Xauthority`, which matches the common Raspberry Pi desktop/X11 case. If your Pi uses a different display server or display number, edit the generated user service accordingly.

In kiosk mode, the folder button opens the in-app image library instead of an OS file picker. The app scans only the top level of the image directory, newest files first, and shows JPG/PNG images plus Screen Printer sidecar JSON files. Tap/click an image to open it, then use the compact custom controls for fullscreen, grayscale, exposure, contrast, blur, rotate, flip, invert, save, Develop, and confirmed power off.

## Develop Mode

Develop mode renders the active image to the connected screen size with full-image fit. If the image aspect ratio does not match the display, letterbox bars are inserted before inversion, so inverted negatives use white bars.

Triple-click the image to open the confirmation box. Confirm stops the timer, updates the Develop sidecar with elapsed exposure time, and returns to the editor. Cancel keeps Develop mode running. The confirmation box auto-cancels after 30 seconds.

## Sidecars

Manual saves and Develop sessions create new sidecar files next to the source image:

```text
<image-stem>.screen-printer.<YYYYMMDD-HHMMSS>.json
<image-stem>.screen-printer.<YYYYMMDD-HHMMSS>-2.json
```

New sidecars are never overwritten. The sidecar created for an active Develop session is updated when that session ends.

Use the open-folder button to load either an image or a `.json` sidecar. Loading a sidecar restores its source image and saved settings.

## Raspberry Pi Performance Notes

The editor keeps a smaller preview copy in memory so slider movement stays responsive on older hardware. Develop mode renders to the connected screen size before applying the expensive tonal adjustments, because pixels beyond the display resolution cannot be shown.

For the smoothest Pi 3B experience, use images reasonably close to the target display aspect ratio, keep other desktop apps closed while exposing, and avoid very high blur values on huge source photos.

## Tests

```bash
pytest
```

The tests cover image adjustment behavior, PNG alpha handling, Develop letterboxing before inversion, sidecar uniqueness/update behavior, and timer/triple-click logic.

## Icon Attribution

The app vendors a tiny SVG subset from Google's Material Design Icons / Material Symbols repository for offline packaging reference. The live Tkinter buttons use lightweight text glyphs to avoid runtime SVG/font dependencies on small devices.

Source: https://github.com/google/material-design-icons
License: Apache License 2.0
