from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png"})
SIDECAR_EXTENSION = ".json"
DEFAULT_KIOSK_IMAGE_DIR = Path("/home/sverd/Pictures/screen-prints")
DEFAULT_SCAN_LIMIT = 200


@dataclass(frozen=True)
class LibraryItem:
    path: Path
    display_name: str
    is_sidecar: bool = False


def image_directory_from_env(value: str | None) -> Path:
    if value and value.strip():
        return Path(value).expanduser()
    return DEFAULT_KIOSK_IMAGE_DIR


def is_supported_library_path(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return True
    # Sidecars are useful in the kiosk because they restore saved settings.
    return suffix == SIDECAR_EXTENSION and ".screen-printer." in path.name


def scan_image_directory(directory: Path, *, limit: int = DEFAULT_SCAN_LIMIT) -> list[LibraryItem]:
    """Return supported files in *directory* without recursively walking huge trees.

    The newest files are returned first. Missing directories simply produce an empty
    list so kiosk startup can show a useful empty-state message instead of crashing.
    """
    directory = directory.expanduser()
    if limit < 1:
        return []
    try:
        candidates = [entry for entry in directory.iterdir() if entry.is_file()]
    except FileNotFoundError:
        return []
    except NotADirectoryError:
        return []

    supported = [entry for entry in candidates if is_supported_library_path(entry)]
    supported.sort(key=lambda path: (path.stat().st_mtime, path.name.lower()), reverse=True)
    items: list[LibraryItem] = []
    for path in supported[:limit]:
        items.append(
            LibraryItem(
                path=path,
                display_name=path.name,
                is_sidecar=path.suffix.lower() == SIDECAR_EXTENSION,
            )
        )
    return items
