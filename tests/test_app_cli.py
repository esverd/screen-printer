from __future__ import annotations

from screen_printer.app import DEFAULT_POWEROFF_COMMAND, build_parser
from screen_printer.icons import make_icon


def test_parser_supports_fullscreen_editor_mode() -> None:
    args = build_parser().parse_args(["--fullscreen", "--geometry", "480x320"])

    assert args.fullscreen is True
    assert args.geometry == "480x320"


def test_parser_keeps_kiosk_as_separate_mode() -> None:
    args = build_parser().parse_args(["--kiosk"])

    assert args.kiosk is True
    assert args.fullscreen is False


def test_poweroff_command_default_is_systemd_poweroff() -> None:
    assert DEFAULT_POWEROFF_COMMAND == "systemctl poweroff"


def test_new_control_icons_render_at_compact_size() -> None:
    for name in ["fullscreen", "power"]:
        icon = make_icon(name, size=26)
        assert icon.size == (26, 26)
