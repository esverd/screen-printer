from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

from screen_printer.image_ops import (
    ImageSettings,
    apply_settings,
    load_source_image,
    render_develop_image,
)


def _gradient(path: Path, *, width: int = 32, height: int = 16) -> None:
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    for x in range(width):
        draw.line((x, 0, x, height - 1), fill=(x * 8 % 256, 40, 255 - (x * 8 % 256)))
    image.save(path)


def test_load_supports_png_alpha_on_white(tmp_path: Path) -> None:
    path = tmp_path / "alpha.png"
    image = Image.new("RGBA", (2, 1), (255, 0, 0, 255))
    image.putpixel((1, 0), (0, 0, 0, 0))
    image.save(path)

    loaded = load_source_image(path)

    assert loaded.mode == "RGB"
    assert loaded.getpixel((0, 0)) == (255, 0, 0)
    assert loaded.getpixel((1, 0)) == (255, 255, 255)


def test_default_settings_render_grayscale(tmp_path: Path) -> None:
    path = tmp_path / "color.jpg"
    _gradient(path)

    loaded = load_source_image(path)
    rendered = apply_settings(loaded, ImageSettings())
    pixel = rendered.getpixel((5, 5))

    assert pixel[0] == pixel[1] == pixel[2]


def test_color_mode_keeps_color_channels(tmp_path: Path) -> None:
    path = tmp_path / "color.png"
    _gradient(path)

    loaded = load_source_image(path)
    rendered = apply_settings(loaded, ImageSettings(grayscale=False))
    pixel = rendered.getpixel((5, 5))

    assert len(set(pixel)) > 1


def test_exposure_contrast_and_blur_change_pixels() -> None:
    image = Image.new("L", (5, 5), 64).convert("RGB")
    image.putpixel((2, 2), (255, 255, 255))

    exposed = apply_settings(image, ImageSettings(exposure_percent=100))
    blurred = apply_settings(image, ImageSettings(blur_radius=2.0))
    contrasted = apply_settings(image, ImageSettings(contrast_percent=100))

    assert sum(exposed.convert("L").tobytes()) > sum(apply_settings(image, ImageSettings()).convert("L").tobytes())
    assert blurred.getpixel((0, 0))[0] > image.getpixel((0, 0))[0]
    assert ImageChops.difference(contrasted, image).getbbox() is not None


def test_invert_and_flips_are_applied() -> None:
    image = Image.new("RGB", (2, 2), "black")
    image.putpixel((0, 0), (10, 20, 30))
    image.putpixel((1, 0), (40, 50, 60))
    image.putpixel((0, 1), (70, 80, 90))
    image.putpixel((1, 1), (100, 110, 120))

    horizontal = apply_settings(image, ImageSettings(grayscale=False, flip_horizontal=True))
    vertical = apply_settings(image, ImageSettings(grayscale=False, flip_vertical=True))
    inverted = apply_settings(image, ImageSettings(grayscale=False, invert=True))

    assert horizontal.getpixel((0, 0)) == (40, 50, 60)
    assert vertical.getpixel((0, 0)) == (70, 80, 90)
    assert inverted.getpixel((0, 0)) == (245, 235, 225)


def test_develop_letterbox_is_black_before_inversion() -> None:
    image = Image.new("RGB", (2, 2), "white")
    rendered = render_develop_image(
        image,
        ImageSettings(grayscale=False, invert=True),
        screen_size=(6, 2),
    )

    assert rendered.size == (6, 2)
    assert rendered.getpixel((0, 0)) == (255, 255, 255)
    assert rendered.getpixel((3, 1)) == (0, 0, 0)
