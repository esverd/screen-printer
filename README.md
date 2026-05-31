# Screen Printer

Screen Printer is a lightweight Tkinter/Pillow app for showing adjusted image negatives on a small Linux display. It is designed for old Raspberry Pi-class hardware and a 3.5-inch screen.

## Features

- Load JPG, JPEG, and PNG images.
- Default grayscale preview, with a color toggle.
- Exposure, contrast, and blur sliders.
- Invert, rotate clockwise, horizontal flip, and vertical flip toggles.
- Full-screen Develop mode that hides the editor and mouse cursor.
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

From the project directory:

```bash
chmod +x scripts/install_pi.sh
./scripts/install_pi.sh
```

The installer creates `.venv`, installs the app, and writes desktop launchers to:

- `~/Desktop/screen-printer.desktop`
- `~/.local/share/applications/screen-printer.desktop`

If Tkinter is missing, install it first:

```bash
sudo apt update
sudo apt install python3-tk
```

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
