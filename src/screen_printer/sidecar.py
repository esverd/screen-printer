from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .image_ops import ImageSettings

SIDECAR_SCHEMA_VERSION = 1


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime | None = None) -> str:
    stamp = value or utc_now()
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    return stamp.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _timestamp_for_filename(value: datetime | None = None) -> str:
    stamp = value or utc_now()
    if stamp.tzinfo is not None:
        stamp = stamp.astimezone(timezone.utc)
    return stamp.strftime("%Y%m%d-%H%M%S")


def _safe_resolved_path(path: Path) -> Path:
    try:
        return path.resolve()
    except OSError:
        return path


@dataclass(frozen=True, slots=True)
class DevelopSessionMetadata:
    started_at_utc: str
    ended_at_utc: str | None = None
    elapsed_seconds: float | None = None
    exit_reason: str | None = None
    rendered_screen_width: int | None = None
    rendered_screen_height: int | None = None
    status: str = "running"

    def to_dict(self) -> dict[str, Any]:
        return {
            "started_at_utc": self.started_at_utc,
            "ended_at_utc": self.ended_at_utc,
            "elapsed_seconds": self.elapsed_seconds,
            "exit_reason": self.exit_reason,
            "rendered_screen_width": self.rendered_screen_width,
            "rendered_screen_height": self.rendered_screen_height,
            "status": self.status,
        }


def next_sidecar_path(image_path: Path, *, timestamp: datetime | None = None) -> Path:
    stem = image_path.stem
    folder = image_path.parent
    suffix = _timestamp_for_filename(timestamp)
    candidate = folder / f"{stem}.screen-printer.{suffix}.json"
    if not candidate.exists():
        return candidate
    for index in range(2, 10_000):
        candidate = folder / f"{stem}.screen-printer.{suffix}-{index}.json"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not find an unused sidecar filename.")


def build_sidecar_payload(
    *,
    source_image_path: Path,
    source_image_size: tuple[int, int],
    screen_size: tuple[int, int],
    settings: ImageSettings,
    develop_session: DevelopSessionMetadata | None = None,
    created_at: datetime | None = None,
) -> dict[str, Any]:
    created = created_at or utc_now()
    resolved_source = _safe_resolved_path(source_image_path)
    return {
        "schema_version": SIDECAR_SCHEMA_VERSION,
        "app_name": "screen-printer",
        "app_version": __version__,
        "created_at_utc": iso_utc(created),
        "updated_at_utc": iso_utc(created),
        "source_image_path": str(resolved_source),
        "source_image_name": source_image_path.name,
        "source_image": {
            "width": int(source_image_size[0]),
            "height": int(source_image_size[1]),
        },
        "screen": {
            "width": int(screen_size[0]),
            "height": int(screen_size[1]),
        },
        "settings": settings.sanitized().to_dict(),
        "develop_session": develop_session.to_dict() if develop_session else None,
    }


def _write_json_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def write_new_sidecar(
    *,
    source_image_path: Path,
    source_image_size: tuple[int, int],
    screen_size: tuple[int, int],
    settings: ImageSettings,
    develop_session: DevelopSessionMetadata | None = None,
    created_at: datetime | None = None,
) -> Path:
    path = next_sidecar_path(source_image_path, timestamp=created_at)
    payload = build_sidecar_payload(
        source_image_path=source_image_path,
        source_image_size=source_image_size,
        screen_size=screen_size,
        settings=settings,
        develop_session=develop_session,
        created_at=created_at,
    )
    try:
        _write_json_exclusive(path, payload)
    except FileExistsError:
        path = next_sidecar_path(source_image_path, timestamp=created_at)
        _write_json_exclusive(path, payload)
    return path


def update_develop_session(
    *,
    sidecar_path: Path,
    ended_at: datetime | None,
    elapsed_seconds: float,
    exit_reason: str,
    rendered_screen_size: tuple[int, int],
) -> None:
    payload = json.loads(sidecar_path.read_text(encoding="utf-8"))
    now = ended_at or utc_now()
    session_payload = payload.get("develop_session")
    if not isinstance(session_payload, dict):
        session_payload = {}
    session_payload.update(
        {
            "ended_at_utc": iso_utc(now),
            "elapsed_seconds": round(max(0.0, float(elapsed_seconds)), 3),
            "exit_reason": exit_reason,
            "rendered_screen_width": int(rendered_screen_size[0]),
            "rendered_screen_height": int(rendered_screen_size[1]),
            "status": "complete",
        }
    )
    payload["develop_session"] = session_payload
    payload["updated_at_utc"] = iso_utc(now)
    sidecar_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_sidecar(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_and_settings_from_sidecar(path: Path) -> tuple[Path, ImageSettings]:
    payload = read_sidecar(path)
    source_raw = str(payload.get("source_image_path", "")).strip()
    if not source_raw:
        raise ValueError("Sidecar is missing source_image_path.")
    source_path = Path(source_raw)
    if not source_path.is_absolute():
        source_path = (path.parent / source_path).resolve()

    settings_payload = payload.get("settings", {})
    if not isinstance(settings_payload, dict):
        settings_payload = {}
    return source_path, ImageSettings.from_dict(settings_payload)
