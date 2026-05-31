from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance, ImageFilter, ImageOps

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MIN_EXPOSURE_PERCENT = -100
MAX_EXPOSURE_PERCENT = 300
MIN_CONTRAST_PERCENT = -100
MAX_CONTRAST_PERCENT = 300
MIN_BLUR_RADIUS = 0.0
MAX_BLUR_RADIUS = 20.0

try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
    RESAMPLE_BILINEAR = Image.Resampling.BILINEAR
except AttributeError:  # pragma: no cover - Pillow < 9 fallback
    RESAMPLE_LANCZOS = Image.LANCZOS
    RESAMPLE_BILINEAR = Image.BILINEAR


def _clamp_int(value: int | float, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(round(value))))


def _clamp_float(value: int | float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, float(value)))


def _coerce_bool(value: object, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return fallback


def _coerce_int(value: object, fallback: int) -> int:
    try:
        return int(round(float(str(value).strip())))
    except (TypeError, ValueError):
        return fallback


def _coerce_float(value: object, fallback: float) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return fallback


@dataclass(frozen=True, slots=True)
class ImageSettings:
    grayscale: bool = True
    exposure_percent: int = 0
    contrast_percent: int = 0
    blur_radius: float = 0.0
    invert: bool = False
    rotation_degrees: int = 0
    flip_horizontal: bool = False
    flip_vertical: bool = False

    def sanitized(self) -> "ImageSettings":
        rotation = int(round(self.rotation_degrees / 90.0)) * 90
        return ImageSettings(
            grayscale=bool(self.grayscale),
            exposure_percent=_clamp_int(
                self.exposure_percent,
                MIN_EXPOSURE_PERCENT,
                MAX_EXPOSURE_PERCENT,
            ),
            contrast_percent=_clamp_int(
                self.contrast_percent,
                MIN_CONTRAST_PERCENT,
                MAX_CONTRAST_PERCENT,
            ),
            blur_radius=_clamp_float(self.blur_radius, MIN_BLUR_RADIUS, MAX_BLUR_RADIUS),
            invert=bool(self.invert),
            rotation_degrees=rotation % 360,
            flip_horizontal=bool(self.flip_horizontal),
            flip_vertical=bool(self.flip_vertical),
        )

    def with_invert(self, invert: bool) -> "ImageSettings":
        return replace(self, invert=invert).sanitized()

    def to_dict(self) -> dict[str, Any]:
        clean = self.sanitized()
        return {
            "grayscale": clean.grayscale,
            "exposure_percent": clean.exposure_percent,
            "contrast_percent": clean.contrast_percent,
            "blur_radius": clean.blur_radius,
            "invert": clean.invert,
            "rotation_degrees": clean.rotation_degrees,
            "flip_horizontal": clean.flip_horizontal,
            "flip_vertical": clean.flip_vertical,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ImageSettings":
        return cls(
            grayscale=_coerce_bool(payload.get("grayscale"), True),
            exposure_percent=_coerce_int(payload.get("exposure_percent"), 0),
            contrast_percent=_coerce_int(payload.get("contrast_percent"), 0),
            blur_radius=_coerce_float(payload.get("blur_radius"), 0.0),
            invert=_coerce_bool(payload.get("invert"), False),
            rotation_degrees=_coerce_int(payload.get("rotation_degrees"), 0),
            flip_horizontal=_coerce_bool(payload.get("flip_horizontal"), False),
            flip_vertical=_coerce_bool(payload.get("flip_vertical"), False),
        ).sanitized()


def is_supported_image(path: Path) -> bool:
    return path.suffix.lower() in SUPPORTED_EXTENSIONS


def load_source_image(path: Path) -> Image.Image:
    if not is_supported_image(path):
        raise ValueError("Only JPG, JPEG, and PNG images are supported.")
    if not path.exists():
        raise FileNotFoundError(f"Source image does not exist: {path}")

    with Image.open(path) as source:
        oriented = ImageOps.exif_transpose(source)
        if oriented.mode in {"RGBA", "LA"} or (
            oriented.mode == "P" and "transparency" in oriented.info
        ):
            rgba = oriented.convert("RGBA")
            background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            background.alpha_composite(rgba)
            return background.convert("RGB")
        return oriented.convert("RGB")


def apply_geometry(image: Image.Image, settings: ImageSettings) -> Image.Image:
    clean = settings.sanitized()
    adjusted = image.convert("RGB")

    if clean.rotation_degrees:
        adjusted = adjusted.rotate(-clean.rotation_degrees, expand=True, fillcolor="white")
    if clean.flip_horizontal:
        adjusted = ImageOps.mirror(adjusted)
    if clean.flip_vertical:
        adjusted = ImageOps.flip(adjusted)
    return adjusted.convert("RGB")


def apply_tonal_adjustments(
    image: Image.Image,
    settings: ImageSettings,
    *,
    include_invert: bool = True,
) -> Image.Image:
    clean = settings.sanitized()
    adjusted = image.convert("RGB")

    if clean.grayscale:
        adjusted = adjusted.convert("L")

    if clean.exposure_percent != 0:
        factor = max(0.0, 1.0 + (clean.exposure_percent / 100.0))
        adjusted = ImageEnhance.Brightness(adjusted).enhance(factor)
    if clean.contrast_percent != 0:
        factor = max(0.0, 1.0 + (clean.contrast_percent / 100.0))
        adjusted = ImageEnhance.Contrast(adjusted).enhance(factor)
    if clean.blur_radius > 0.0:
        adjusted = adjusted.filter(ImageFilter.GaussianBlur(radius=clean.blur_radius))
    if include_invert and clean.invert:
        adjusted = ImageOps.invert(adjusted.convert("RGB") if adjusted.mode != "L" else adjusted)

    return adjusted.convert("RGB")


def apply_settings(image: Image.Image, settings: ImageSettings, *, include_invert: bool = True) -> Image.Image:
    return apply_tonal_adjustments(
        apply_geometry(image, settings),
        settings,
        include_invert=include_invert,
    )


def contain_image(
    image: Image.Image,
    max_size: tuple[int, int],
    *,
    allow_upscale: bool = False,
    resample: int = RESAMPLE_LANCZOS,
) -> Image.Image:
    max_width = max(1, int(max_size[0]))
    max_height = max(1, int(max_size[1]))
    width, height = image.size
    scale = min(max_width / max(width, 1), max_height / max(height, 1))
    if not allow_upscale:
        scale = min(1.0, scale)
    target_size = (
        max(1, int(round(width * scale))),
        max(1, int(round(height * scale))),
    )
    if target_size == image.size:
        return image.copy()
    return image.resize(target_size, resample=resample)


def render_preview_image(
    source_image: Image.Image,
    settings: ImageSettings,
    *,
    max_size: tuple[int, int],
) -> Image.Image:
    return contain_image(apply_settings(source_image, settings), max_size, allow_upscale=True)


def render_develop_image(
    source_image: Image.Image,
    settings: ImageSettings,
    *,
    screen_size: tuple[int, int],
) -> Image.Image:
    screen_width = max(1, int(screen_size[0]))
    screen_height = max(1, int(screen_size[1]))
    clean = settings.sanitized()
    source_fit_size = (
        (screen_height, screen_width)
        if clean.rotation_degrees in {90, 270}
        else (screen_width, screen_height)
    )
    source_work = contain_image(
        source_image,
        source_fit_size,
        allow_upscale=False,
        resample=RESAMPLE_BILINEAR,
    )
    pre_invert = apply_geometry(source_work, clean)
    contained = contain_image(
        pre_invert,
        (screen_width, screen_height),
        allow_upscale=True,
        resample=RESAMPLE_BILINEAR,
    )
    contained = apply_tonal_adjustments(contained, clean, include_invert=False)
    canvas = Image.new("RGB", (screen_width, screen_height), "black")
    offset = (
        (screen_width - contained.width) // 2,
        (screen_height - contained.height) // 2,
    )
    canvas.paste(contained, offset)
    if clean.invert:
        canvas = ImageOps.invert(canvas)
    return canvas
