"""艺术特效：万花筒、像素化、浮雕、油画和故障风，支持静态图/GIF。"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

from .gif_utils import is_gif, save_rgba_gif, unfold_frames


def _kaleidoscope_frame(image: Image.Image) -> Image.Image:
    """按 meme-generator-rs 的同心圆布局生成万花筒。"""
    rgba = image.convert("RGBA")
    circle_count = 10
    images_per_circle = 4
    angle_step = 360.0 / images_per_circle
    center = float((circle_count * 50) + 100)
    canvas = Image.new("RGBA", (int(center * 2), int(center * 2)), "white")

    current_angle = 0.0
    for ring in range(circle_count):
        radius = float((ring * 50) + 100)
        target_width = (ring * 35) + 100
        target_height = max(1, round(rgba.height * target_width / max(rgba.width, 1)))
        resized = rgba.resize(
            (target_width, target_height), Image.Resampling.LANCZOS
        )

        for position in range(images_per_circle):
            angle = current_angle + angle_step * position
            rotated = resized.rotate(
                90.0 - angle,
                resample=Image.Resampling.BICUBIC,
                expand=True,
            )
            x = round(
                center
                + radius * np.cos(np.deg2rad(angle))
                - rotated.width / 2
            )
            y = round(
                center
                - radius * np.sin(np.deg2rad(angle))
                - rotated.height / 2
            )
            canvas.alpha_composite(rotated, (x, y))
        current_angle += angle_step / 2.0

    return canvas


def _pixelate_frame(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    block = max(4, min(width, height) // 32)
    small = rgba.resize(
        (max(1, width // block), max(1, height // block)),
        Image.Resampling.BOX,
    )
    return small.resize((width, height), Image.Resampling.NEAREST)


def _emboss_frame(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    embossed = rgba.convert("RGB").filter(ImageFilter.EMBOSS)
    embossed = ImageEnhance.Contrast(embossed).enhance(1.35)
    return Image.merge("RGBA", (*embossed.split(), alpha))


def _oil_paint_frame(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    painted = rgba.convert("RGB").filter(ImageFilter.ModeFilter(size=7))
    painted = ImageEnhance.Color(painted).enhance(1.35)
    painted = ImageEnhance.Contrast(painted).enhance(1.12)
    return Image.merge("RGBA", (*painted.split(), alpha))


def _glitch_frame(image: Image.Image) -> Image.Image:
    rgba = np.asarray(image.convert("RGBA")).copy()
    height, width = rgba.shape[:2]
    shift = max(2, width // 40)
    source = rgba.copy()
    rgba[:, :, 0] = np.roll(source[:, :, 0], shift, axis=1)
    rgba[:, :, 2] = np.roll(source[:, :, 2], -shift, axis=1)

    band_height = max(2, height // 30)
    for index, y in enumerate(range(band_height * 3, height, band_height * 6)):
        offset = shift * (2 if index % 2 == 0 else -2)
        rgba[y : y + band_height] = np.roll(
            rgba[y : y + band_height], offset, axis=1
        )
    return Image.fromarray(rgba, "RGBA")


def _apply(input_path: str, output_path: str, transform) -> str:
    with Image.open(input_path) as source:
        if not is_gif(input_path):
            transform(source).save(output_path, "PNG")
            return output_path

        frames, durations = unfold_frames(source)
        processed = [transform(frame) for frame in frames]
        save_rgba_gif(
            processed,
            durations,
            output_path,
            loop=source.info.get("loop", 0),
        )
    return output_path


def kaleidoscope(input_path: str, output_path: str) -> str:
    return _apply(input_path, output_path, _kaleidoscope_frame)


def pixelate(input_path: str, output_path: str) -> str:
    return _apply(input_path, output_path, _pixelate_frame)


def emboss(input_path: str, output_path: str) -> str:
    return _apply(input_path, output_path, _emboss_frame)


def oil_paint(input_path: str, output_path: str) -> str:
    return _apply(input_path, output_path, _oil_paint_frame)


def glitch(input_path: str, output_path: str) -> str:
    return _apply(input_path, output_path, _glitch_frame)
