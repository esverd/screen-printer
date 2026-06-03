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
    draw.rounded_rectangle((6, 6, 26, 26), radius=3, outline=color, width=2)
    draw.polygon([(8, 24), (24, 8), (24, 24)], fill=color)
    draw.line((10, 24, 24, 10), fill=color, width=2)


def _draw_blur(draw: IconDraw, color: str) -> None:
    draw.ellipse((9, 9, 23, 23), outline=color, width=2)
    for xy in ((6, 14, 10, 18), (22, 14, 26, 18), (14, 6, 18, 10), (14, 22, 18, 26)):
        draw.ellipse(xy, fill=color)
    draw.ellipse((13, 13, 19, 19), fill=color)


def _draw_invert(draw: IconDraw, color: str) -> None:
    draw.pieslice((6, 6, 26, 26), start=90, end=270, fill=color)
    draw.pieslice((6, 6, 26, 26), start=270, end=90, fill=(0, 0, 0, 0), outline=color, width=2)
    draw.ellipse((6, 6, 26, 26), outline=color, width=2)


def _draw_rotate(draw: IconDraw, color: str) -> None:
    draw.arc((6, 5, 27, 26), start=35, end=315, fill=color, width=3)
    draw.polygon([(24, 6), (29, 7), (26, 12)], fill=color)


def _draw_flip_h(draw: IconDraw, color: str) -> None:
    draw.line((16, 5, 16, 27), fill=color, width=2)
    draw.line((6, 16, 13, 16), fill=color, width=2)
    draw.line((26, 16, 19, 16), fill=color, width=2)
    draw.polygon([(6, 16), (12, 10), (12, 22)], fill=color)
    draw.polygon([(26, 16), (20, 10), (20, 22)], fill=color)


def _draw_flip_v(draw: IconDraw, color: str) -> None:
    draw.line((5, 16, 27, 16), fill=color, width=2)
    draw.line((16, 6, 16, 13), fill=color, width=2)
    draw.line((16, 26, 16, 19), fill=color, width=2)
    draw.polygon([(16, 6), (10, 12), (22, 12)], fill=color)
    draw.polygon([(16, 26), (10, 20), (22, 20)], fill=color)


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


def _draw_develop(draw: IconDraw, color: str) -> None:
    draw.rounded_rectangle((5, 8, 27, 24), radius=2, outline=color, width=2)
    draw.ellipse((12, 11, 20, 19), outline=color, width=2)
    for start, end in [
        ((16, 3), (16, 6)),
        ((16, 26), (16, 29)),
        ((2, 16), (5, 16)),
        ((27, 16), (30, 16)),
        ((6, 6), (8, 8)),
        ((24, 24), (26, 26)),
        ((26, 6), (24, 8)),
        ((8, 24), (6, 26)),
    ]:
        draw.line((*start, *end), fill=color, width=2)


def _draw_fullscreen(draw: IconDraw, color: str) -> None:
    draw.line((5, 13, 5, 5, 13, 5), fill=color, width=3)
    draw.line((19, 5, 27, 5, 27, 13), fill=color, width=3)
    draw.line((27, 19, 27, 27, 19, 27), fill=color, width=3)
    draw.line((13, 27, 5, 27, 5, 19), fill=color, width=3)


def _draw_power(draw: IconDraw, color: str) -> None:
    draw.line((16, 5, 16, 16), fill=color, width=3)
    draw.arc((7, 9, 25, 28), start=130, end=410, fill=color, width=3)


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
    "develop": _draw_develop,
    "fullscreen": _draw_fullscreen,
    "power": _draw_power,
    "reset": _draw_reset,
}


def make_icon(name: str, *, size: int = ICON_SIZE, color: str = "#f2f5f7") -> Image.Image:
    scale = max(1, ICON_SCALE)
    image, raw_draw = _canvas(size * scale)
    draw = IconDraw(raw_draw, scale=scale)
    drawer = DRAWERS[name]
    drawer(draw, color)
    return image.resize((size, size), RESAMPLE_LANCZOS)
