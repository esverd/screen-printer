from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from screen_printer.image_ops import ImageSettings
from screen_printer.sidecar import (
    DevelopSessionMetadata,
    read_sidecar,
    update_develop_session,
    write_new_sidecar,
)


def test_repeated_sidecar_writes_create_unique_files(tmp_path: Path) -> None:
    source = tmp_path / "art.png"
    source.write_bytes(b"placeholder")
    stamp = datetime(2026, 5, 31, 12, 30, 4, tzinfo=timezone.utc)

    first = write_new_sidecar(
        source_image_path=source,
        source_image_size=(100, 50),
        screen_size=(480, 320),
        settings=ImageSettings(exposure_percent=25),
        created_at=stamp,
    )
    second = write_new_sidecar(
        source_image_path=source,
        source_image_size=(100, 50),
        screen_size=(480, 320),
        settings=ImageSettings(exposure_percent=25),
        created_at=stamp,
    )

    assert first.exists()
    assert second.exists()
    assert first != second
    assert first.name == "art.screen-printer.20260531-123004.json"
    assert second.name == "art.screen-printer.20260531-123004-2.json"


def test_sidecar_contains_settings_screen_and_source_metadata(tmp_path: Path) -> None:
    source = tmp_path / "print.jpg"
    source.write_bytes(b"placeholder")
    path = write_new_sidecar(
        source_image_path=source,
        source_image_size=(12, 34),
        screen_size=(480, 320),
        settings=ImageSettings(grayscale=False, invert=True, flip_horizontal=True, blur_radius=1.5),
        created_at=datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc),
    )

    payload = read_sidecar(path)

    assert payload["schema_version"] == 1
    assert payload["source_image_name"] == "print.jpg"
    assert payload["source_image"] == {"width": 12, "height": 34}
    assert payload["screen"] == {"width": 480, "height": 320}
    assert payload["settings"]["grayscale"] is False
    assert payload["settings"]["invert"] is True
    assert payload["settings"]["flip_horizontal"] is True
    assert payload["settings"]["blur_radius"] == 1.5


def test_develop_sidecar_is_updated_when_session_ends(tmp_path: Path) -> None:
    source = tmp_path / "negative.png"
    source.write_bytes(b"placeholder")
    started = datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc)
    ended = datetime(2026, 5, 31, 12, 1, 2, tzinfo=timezone.utc)
    session = DevelopSessionMetadata(
        started_at_utc="2026-05-31T12:00:00Z",
        rendered_screen_width=480,
        rendered_screen_height=320,
    )
    path = write_new_sidecar(
        source_image_path=source,
        source_image_size=(120, 80),
        screen_size=(480, 320),
        settings=ImageSettings(invert=True),
        develop_session=session,
        created_at=started,
    )

    update_develop_session(
        sidecar_path=path,
        ended_at=ended,
        elapsed_seconds=62.3456,
        exit_reason="confirmed",
        rendered_screen_size=(480, 320),
    )

    payload = json.loads(path.read_text(encoding="utf-8"))
    develop = payload["develop_session"]
    assert develop["started_at_utc"] == "2026-05-31T12:00:00Z"
    assert develop["ended_at_utc"] == "2026-05-31T12:01:02Z"
    assert develop["elapsed_seconds"] == 62.346
    assert develop["exit_reason"] == "confirmed"
    assert develop["status"] == "complete"
    assert payload["updated_at_utc"] == "2026-05-31T12:01:02Z"
