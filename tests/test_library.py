from pathlib import Path

from PIL import Image

from screen_printer.library import (
    DEFAULT_KIOSK_IMAGE_DIR,
    image_directory_from_env,
    is_supported_library_path,
    scan_image_directory,
)


def test_image_directory_from_env_defaults_and_expands_home(monkeypatch):
    monkeypatch.setenv("HOME", "/tmp/home-for-test")
    assert image_directory_from_env(None) == DEFAULT_KIOSK_IMAGE_DIR
    assert image_directory_from_env("") == DEFAULT_KIOSK_IMAGE_DIR
    assert image_directory_from_env("~/prints") == Path("/tmp/home-for-test/prints")


def test_supported_library_paths():
    assert is_supported_library_path(Path("photo.JPG"))
    assert is_supported_library_path(Path("photo.jpeg"))
    assert is_supported_library_path(Path("photo.png"))
    assert is_supported_library_path(Path("photo.screen-printer.20260101-120000.json"))
    assert not is_supported_library_path(Path("notes.json"))
    assert not is_supported_library_path(Path("movie.gif"))


def test_scan_image_directory_is_top_level_newest_first_and_limited(tmp_path):
    old_image = tmp_path / "old.jpg"
    Image.new("RGB", (2, 2), "red").save(old_image)
    new_image = tmp_path / "new.png"
    Image.new("RGB", (2, 2), "blue").save(new_image)
    sidecar = tmp_path / "new.screen-printer.20260101-120000.json"
    sidecar.write_text("{}")
    (tmp_path / "ignore.txt").write_text("nope")
    subdir = tmp_path / "nested"
    subdir.mkdir()
    Image.new("RGB", (2, 2), "green").save(subdir / "nested.jpg")

    old_time = 1_700_000_000
    new_time = old_time + 10
    sidecar_time = new_time + 10
    old_image.touch()
    new_image.touch()
    sidecar.touch()
    import os

    os.utime(old_image, (old_time, old_time))
    os.utime(new_image, (new_time, new_time))
    os.utime(sidecar, (sidecar_time, sidecar_time))

    items = scan_image_directory(tmp_path, limit=2)

    assert [item.path.name for item in items] == [sidecar.name, new_image.name]
    assert items[0].is_sidecar is True
    assert items[1].is_sidecar is False


def test_scan_image_directory_missing_or_zero_limit(tmp_path):
    assert scan_image_directory(tmp_path / "missing") == []
    assert scan_image_directory(tmp_path, limit=0) == []
