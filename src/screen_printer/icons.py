from __future__ import annotations

from typing import Iterable, Sequence

from PIL import Image, ImageDraw

ICON_SIZE = 32
ICON_SCALE = 4

try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # pragma: no cover - Pillow < 9 fallback
    RESAMPLE_LANCZOS = Image.LANCZOS


def _canvas(size: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def _scale_tuple(values: Sequence[float], scale: int) -> tuple[int, ...]:
    return tuple(int(round(value * scale)) for value in values)


def _scale_points(points: Iterable[tuple[float, float]], scale: int) -> list[tuple[int, int]]:
    return [(int(round(x * scale)), int(round(y * scale))) for x, y in points]


class IconDraw:
    def __init__(self, draw: ImageDraw.ImageDraw, *, scale: int) -> None:
        self._draw = draw
        self._scale = scale

    def line(self, xy: Sequence[float] | Iterable[tuple[float, float]], **kwargs: object) -> None:
        if "width" in kwargs:
            kwargs["width"] = max(1, int(kwargs["width"]) * self._scale)
        if isinstance(xy, tuple) and xy and isinstance(xy[0], (int, float)):
            self._draw.line(_scale_tuple(xy, self._scale), **kwargs)
        else:
            self._draw.line(_scale_points(xy, self._scale), **kwargs)

    def rounded_rectangle(self, xy: Sequence[float], *, radius: float = 0.0, **kwargs: object) -> None:
        if "width" in kwargs:
            kwargs["width"] = max(1, int(kwargs["width"]) * self._scale)
        self._draw.rounded_rectangle(
            _scale_tuple(xy, self._scale),
            radius=int(round(radius * self._scale)),
            **kwargs,
        )

    def rectangle(self, xy: Sequence[float], **kwargs: object) -> None:
        if "width" in kwargs:
            kwargs["width"] = max(1, int(kwargs["width"]) * self._scale)
        self._draw.rectangle(_scale_tuple(xy, self._scale), **kwargs)

    def ellipse(self, xy: Sequence[float], **kwargs: object) -> None:
        if "width" in kwargs:
            kwargs["width"] = max(1, int(kwargs["width"]) * self._scale)
        self._draw.ellipse(_scale_tuple(xy, self._scale), **kwargs)

    def arc(self, xy: Sequence[float], **kwargs: object) -> None:
        if "width" in kwargs:
            kwargs["width"] = max(1, int(kwargs["width"]) * self._scale)
        self._draw.arc(_scale_tuple(xy, self._scale), **kwargs)

    def polygon(self, xy: Iterable[tuple[float, float]], **kwargs: object) -> None:
        self._draw.polygon(_scale_points(xy, self._scale), **kwargs)

    def pieslice(self, xy: Sequence[float], **kwargs: object) -> None:
        if "width" in kwargs:
            kwargs["width"] = max(1, int(kwargs["width"]) * self._scale)
        self._draw.pieslice(_scale_tuple(xy, self._scale), **kwargs)


def _draw_folder(draw: IconDraw, color: str) -> None:
    draw.rounded_rectangle((4, 10, 28, 26), radius=3, outline=color, width=2)
    draw.line((6, 10, 6, 7, 14, 7, 18, 10), fill=color, width=2)
    draw.line((6, 14, 27, 14), fill=color, width=2)


def _draw_grayscale(draw: IconDraw, color: str) -> None:
    shades = (240, 192, 128, 64)
    for index, shade in enumerate(shades):
        x0 = 6 + index * 5
        draw.rounded_rectangle((x0, 8, x0 + 4, 24), radius=1.5, fill=(shade, shade, shade, 255))
    draw.rounded_rectangle((5, 7, 27, 25), radius=3, outline=color, width=1)


def _draw_exposure(draw: IconDraw, color: str) -> None:
    draw.ellipse((11, 11, 21, 21), outline=color, width=2)
    for start, end in [
        ((16, 3), (16, 7)),
        ((16, 25), (16, 29)),
        ((3, 16), (7, 16)),
        ((25, 16), (29, 16)),
        ((7, 7), (10, 10)),
        ((22, 22), (25, 25)),
        ((25, 7), (22, 10)),
        ((10, 22), (7, 25)),
    ]:
        draw.line((*start, *end), fill=color, width=2)


def _draw_contrast(draw: IconDraw, color: str) -> None:
    draw.line((6, 25, 6, 6, 26, 6), fill=color, width=1)
    points = [(7, 23), (10, 23), (13, 20), (16, 16), (19, 11), (23, 9), (26, 9)]
    draw.line(points, fill=color, width=2)
    for point in (points[0], points[-1]):
        x, y = point
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=color)


def _draw_blur(draw: IconDraw, color: str) -> None:
    for y, offset in ((10, 0), (16, 2), (22, 0)):
        draw.arc((5 + offset, y - 5, 18 + offset, y + 5), start=205, end=335, fill=color, width=2)
        draw.arc((17 + offset, y - 5, 30 + offset, y + 5), start=25, end=155, fill=color, width=2)


def _draw_invert(draw: IconDraw, color: str) -> None:
    draw.pieslice((6, 6, 26, 26), start=90, end=270, fill=color)
    draw.pieslice((6, 6, 26, 26), start=270, end=90, fill=(0, 0, 0, 0), outline=color, width=2)
    draw.ellipse((6, 6, 26, 26), outline=color, width=2)


def _draw_rotate(draw: IconDraw, color: str) -> None:
    draw.arc((6, 5, 27, 26), start=35, end=315, fill=color, width=3)
    draw.polygon([(24, 6), (29, 7), (26, 12)], fill=color)


def _draw_flip_h(draw: IconDraw, color: str) -> None:
    draw.line((16, 5, 16, 27), fill=color, width=2)
    draw.line((5, 16, 13, 8, 13, 24, 5, 16), fill=color, width=2)
    draw.line((27, 16, 19, 8, 19, 24, 27, 16), fill=color, width=2)


def _draw_flip_v(draw: IconDraw, color: str) -> None:
    draw.line((5, 16, 27, 16), fill=color, width=2)
    draw.line((16, 5, 8, 13, 24, 13, 16, 5), fill=color, width=2)
    draw.line((16, 27, 8, 19, 24, 19, 16, 27), fill=color, width=2)


def _draw_save(draw: IconDraw, color: str) -> None:
    draw.rounded_rectangle((6, 4, 26, 28), radius=2, outline=color, width=2)
    draw.rectangle((10, 5, 21, 12), outline=color, width=2)
    draw.rectangle((11, 20, 22, 27), outline=color, width=2)
    draw.rectangle((18, 6, 21, 10), fill=color)


def _draw_camera(draw: IconDraw, color: str) -> None:
    draw.rounded_rectangle((4, 10, 28, 26), radius=3, outline=color, width=2)
    draw.rectangle((10, 7, 17, 11), fill=color)
    draw.ellipse((11, 13, 21, 23), outline=color, width=2)
    draw.ellipse((23, 13, 25, 15), fill=color)


def _draw_reset(draw: IconDraw, color: str) -> None:
    draw.arc((7, 7, 26, 26), start=45, end=330, fill=color, width=3)
    draw.polygon([(10, 7), (17, 6), (14, 13)], fill=color)


DRAWERS = {
    "folder": _draw_folder,
    "grayscale": _draw_grayscale,
    "exposure": _draw_exposure,
    "contrast": _draw_contrast,
    "blur": _draw_blur,
    "invert": _draw_invert,
    "rotate": _draw_rotate,
    "flip_h": _draw_flip_h,
    "flip_v": _draw_flip_v,
    "save": _draw_save,
    "camera": _draw_camera,
    "reset": _draw_reset,
}


def make_icon(name: str, *, size: int = ICON_SIZE, color: str = "#f2f5f7") -> Image.Image:
    scale = max(1, ICON_SCALE)
    image, raw_draw = _canvas(size * scale)
    draw = IconDraw(raw_draw, scale=scale)
    drawer = DRAWERS[name]
    drawer(draw, color)
    return image.resize((size, size), RESAMPLE_LANCZOS)
