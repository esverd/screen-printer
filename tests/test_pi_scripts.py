from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL_KIOSK = ROOT / "scripts" / "install_kiosk_autostart.sh"
RUN_KIOSK = ROOT / "scripts" / "run_kiosk.sh"
RUN_PI = ROOT / "scripts" / "run_pi.sh"
INSTALL_PI = ROOT / "scripts" / "install_pi.sh"


def run_script(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [str(INSTALL_KIOSK), *args],
        cwd=ROOT,
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def test_shell_scripts_parse() -> None:
    for script in [INSTALL_KIOSK, RUN_KIOSK, RUN_PI, INSTALL_PI]:
        subprocess.run(["bash", "-n", str(script)], cwd=ROOT, check=True)


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
    assert not (xdg / "systemd" / "user" / "screen-printer-kiosk.service").exists()
    assert not image_dir.exists()


def test_install_preview_is_default_and_does_not_write(tmp_path: Path) -> None:
    home = tmp_path / "home"
    xdg = tmp_path / "xdg"
    home.mkdir()

    result = run_script("install", env={"HOME": str(home), "XDG_CONFIG_HOME": str(xdg)})

    assert "Dry preview only" in result.stdout
    assert "install --yes" in result.stdout
    assert not (xdg / "systemd" / "user" / "screen-printer-kiosk.service").exists()
