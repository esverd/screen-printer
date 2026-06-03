from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from screen_printer.image_ops import ImageSettings
from screen_printer.sidecar import (
    append_develop_session,
    DevelopSessionMetadata,
    read_sidecar,
    sidecar_matches_context,
    source_and_settings_from_sidecar,
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
    assert payload["develop_sessions"] == []


def test_sidecar_can_restore_source_and_settings(tmp_path: Path) -> None:
    source = tmp_path / "print.png"
    source.write_bytes(b"placeholder")
    path = write_new_sidecar(
        source_image_path=source,
        source_image_size=(12, 34),
        screen_size=(480, 320),
        settings=ImageSettings(
            grayscale=False,
            exposure_percent=42,
            invert=True,
            rotation_degrees=90,
        ),
        created_at=datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc),
    )

    restored_source, restored_settings = source_and_settings_from_sidecar(path)

    assert restored_source == source.resolve()
    assert restored_settings.grayscale is False
    assert restored_settings.exposure_percent == 42
    assert restored_settings.invert is True
    assert restored_settings.rotation_degrees == 90


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
    assert payload["develop_sessions"][-1] == develop
    assert payload["updated_at_utc"] == "2026-05-31T12:01:02Z"


def test_matching_sidecar_can_append_multiple_develop_sessions(tmp_path: Path) -> None:
    source = tmp_path / "negative.png"
    source.write_bytes(b"placeholder")
    settings = ImageSettings(invert=True, exposure_percent=15)
    path = write_new_sidecar(
        source_image_path=source,
        source_image_size=(120, 80),
        screen_size=(480, 320),
        settings=settings,
        created_at=datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc),
    )

    assert sidecar_matches_context(
        sidecar_path=path,
        source_image_path=source,
        source_image_size=(120, 80),
        screen_size=(480, 320),
        settings=settings,
    )

    first = DevelopSessionMetadata(started_at_utc="2026-05-31T12:01:00Z")
    second = DevelopSessionMetadata(started_at_utc="2026-05-31T12:03:00Z")
    append_develop_session(
        sidecar_path=path,
        develop_session=first,
        updated_at=datetime(2026, 5, 31, 12, 1, tzinfo=timezone.utc),
    )
    update_develop_session(
        sidecar_path=path,
        ended_at=datetime(2026, 5, 31, 12, 2, tzinfo=timezone.utc),
        elapsed_seconds=60,
        exit_reason="confirmed",
        rendered_screen_size=(480, 320),
    )
    append_develop_session(
        sidecar_path=path,
        develop_session=second,
        updated_at=datetime(2026, 5, 31, 12, 3, tzinfo=timezone.utc),
    )

    payload = read_sidecar(path)
    assert len(payload["develop_sessions"]) == 2
    assert payload["develop_sessions"][0]["status"] == "complete"
    assert payload["develop_sessions"][0]["elapsed_seconds"] == 60
    assert payload["develop_sessions"][1]["started_at_utc"] == "2026-05-31T12:03:00Z"
    assert payload["develop_sessions"][1]["status"] == "running"
    assert payload["develop_session"] == payload["develop_sessions"][1]


def test_sidecar_context_rejects_changed_settings(tmp_path: Path) -> None:
    source = tmp_path / "negative.png"
    source.write_bytes(b"placeholder")
    path = write_new_sidecar(
        source_image_path=source,
        source_image_size=(120, 80),
        screen_size=(480, 320),
        settings=ImageSettings(exposure_percent=15),
    )

    assert not sidecar_matches_context(
        sidecar_path=path,
        source_image_path=source,
        source_image_size=(120, 80),
        screen_size=(480, 320),
        settings=ImageSettings(exposure_percent=16),
    )
