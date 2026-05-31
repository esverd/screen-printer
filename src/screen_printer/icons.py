from __future__ import annotations

from PIL import Image, ImageDraw

ICON_SIZE = 32


def _canvas(size: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return image, ImageDraw.Draw(image)


def _draw_folder(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.rounded_rectangle((3, 9, 29, 26), radius=3, outline=color, width=3)
    draw.polygon([(5, 9), (5, 6), (14, 6), (18, 9)], outline=color, fill=None)
    draw.line((5, 9, 18, 9), fill=color, width=3)


def _draw_grayscale(draw: ImageDraw.ImageDraw, color: str) -> None:
    for index, shade in enumerate((235, 180, 120, 60)):
        x0 = 5 + index * 5
        draw.rounded_rectangle((x0, 7, x0 + 4, 25), radius=1, fill=(shade, shade, shade, 255))
    draw.rounded_rectangle((4, 6, 26, 26), radius=3, outline=color, width=2)


def _draw_exposure(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.ellipse((11, 11, 21, 21), outline=color, width=3)
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


def _draw_contrast(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.line((6, 25, 6, 6, 26, 6), fill=color, width=2)
    points = [(7, 23), (10, 23), (13, 20), (16, 16), (19, 11), (23, 9), (26, 9)]
    draw.line(points, fill=color, width=3, joint="curve")
    for point in (points[0], points[-1]):
        x, y = point
        draw.ellipse((x - 2, y - 2, x + 2, y + 2), fill=color)


def _draw_blur(draw: ImageDraw.ImageDraw, color: str) -> None:
    for y, offset in ((10, 0), (16, 2), (22, 0)):
        draw.arc((5 + offset, y - 5, 18 + offset, y + 5), start=205, end=335, fill=color, width=2)
        draw.arc((17 + offset, y - 5, 30 + offset, y + 5), start=25, end=155, fill=color, width=2)


def _draw_invert(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.pieslice((6, 6, 26, 26), start=90, end=270, fill=color)
    draw.pieslice((6, 6, 26, 26), start=270, end=90, fill=(0, 0, 0, 0), outline=color, width=2)
    draw.ellipse((6, 6, 26, 26), outline=color, width=2)


def _draw_rotate(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.arc((6, 5, 27, 26), start=35, end=315, fill=color, width=3)
    draw.polygon([(24, 6), (29, 7), (26, 12)], fill=color)


def _draw_flip_h(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.line((16, 5, 16, 27), fill=color, width=2)
    draw.polygon([(4, 16), (13, 8), (13, 24)], outline=color)
    draw.polygon([(28, 16), (19, 8), (19, 24)], outline=color)


def _draw_flip_v(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.line((5, 16, 27, 16), fill=color, width=2)
    draw.polygon([(16, 4), (8, 13), (24, 13)], outline=color)
    draw.polygon([(16, 28), (8, 19), (24, 19)], outline=color)


def _draw_save(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.rounded_rectangle((6, 4, 26, 28), radius=2, outline=color, width=3)
    draw.rectangle((10, 5, 21, 12), outline=color, width=2)
    draw.rectangle((11, 20, 22, 27), outline=color, width=2)
    draw.rectangle((18, 6, 21, 10), fill=color)


def _draw_camera(draw: ImageDraw.ImageDraw, color: str) -> None:
    draw.rounded_rectangle((4, 10, 28, 26), radius=3, outline=color, width=3)
    draw.rectangle((10, 7, 17, 11), fill=color)
    draw.ellipse((11, 13, 21, 23), outline=color, width=3)
    draw.ellipse((23, 13, 25, 15), fill=color)


def _draw_reset(draw: ImageDraw.ImageDraw, color: str) -> None:
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
    image, draw = _canvas(size)
    drawer = DRAWERS[name]
    drawer(draw, color)
    return image
