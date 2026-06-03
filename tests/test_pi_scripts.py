from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
INSTALL_KIOSK = ROOT / "scripts" / "install_kiosk_autostart.sh"
CONFIRM_POWEROFF = ROOT / "scripts" / "confirm_poweroff.sh"
RUN_KIOSK = ROOT / "scripts" / "run_kiosk.sh"
RUN_PI = ROOT / "scripts" / "run_pi.sh"
INSTALL_PI = ROOT / "scripts" / "install_pi.sh"
START_COMMAND = ROOT / "START_SCREEN_PRINTER.command"
START_KIOSK_COMMAND = ROOT / "START_SCREEN_PRINTER_KIOSK.command"
INSTALL_KIOSK_COMMAND = ROOT / "INSTALL_KIOSK_AUTOSTART.command"


def find_usable_bash() -> str | None:
    candidate = shutil.which("bash")
    if candidate is None:
        return None
    try:
        subprocess.run(
            [candidate, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return candidate


BASH = find_usable_bash()

pytestmark = pytest.mark.skipif(BASH is None, reason="bash is required for Pi shell script tests")


def run_script(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [BASH or "bash", str(INSTALL_KIOSK), *args],
        cwd=ROOT,
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def test_shell_scripts_parse() -> None:
    for script in [
        INSTALL_KIOSK,
        CONFIRM_POWEROFF,
        RUN_KIOSK,
        RUN_PI,
        INSTALL_PI,
        START_COMMAND,
        START_KIOSK_COMMAND,
        INSTALL_KIOSK_COMMAND,
    ]:
        subprocess.run([BASH or "bash", "-n", str(script)], cwd=ROOT, check=True)


def test_print_service_uses_configured_image_dir_and_graphical_target(tmp_path: Path) -> None:
    image_dir = tmp_path / "screen prints"
    result = run_script("print-service", "--image-dir", str(image_dir))

    assert "Description=Screen Printer kiosk" in result.stdout
    assert "ExecStart=" in result.stdout
    assert "scripts/run_kiosk.sh" in result.stdout
    assert "WantedBy=graphical-session.target" in result.stdout
    assert "After=graphical-session.target" in result.stdout
    assert "SCREEN_PRINTER_IMAGE_DIR=" in result.stdout
    assert str(image_dir).replace(" ", "\\ ") in result.stdout


def test_print_autostart_launches_kiosk_with_configured_image_dir(tmp_path: Path) -> None:
    image_dir = tmp_path / "screen prints"
    result = run_script("print-autostart", "--image-dir", str(image_dir))

    assert "Name=Screen Printer Kiosk" in result.stdout
    assert "scripts/run_kiosk.sh" in result.stdout
    assert "SCREEN_PRINTER_IMAGE_DIR=" in result.stdout
    assert str(image_dir) in result.stdout


def test_install_dry_run_does_not_write_service_or_image_dir(tmp_path: Path) -> None:
    home = tmp_path / "home"
    xdg = tmp_path / "xdg"
    image_dir = tmp_path / "images"
    home.mkdir()

    result = run_script(
        "install",
        "--yes",
        "--dry-run",
        "--image-dir",
        str(image_dir),
        env={"HOME": str(home), "XDG_CONFIG_HOME": str(xdg)},
    )

    assert "Would write service" in result.stdout
    assert "Would write desktop autostart" in result.stdout
    assert not (xdg / "systemd" / "user" / "screen-printer-kiosk.service").exists()
    assert not (xdg / "autostart" / "screen-printer-kiosk.desktop").exists()
    assert not image_dir.exists()


def test_install_preview_is_default_and_does_not_write(tmp_path: Path) -> None:
    home = tmp_path / "home"
    xdg = tmp_path / "xdg"
    home.mkdir()

    result = run_script("install", env={"HOME": str(home), "XDG_CONFIG_HOME": str(xdg)})

    assert "Dry preview only" in result.stdout
    assert "install --yes" in result.stdout
    assert not (xdg / "systemd" / "user" / "screen-printer-kiosk.service").exists()
    assert not (xdg / "autostart" / "screen-printer-kiosk.desktop").exists()
