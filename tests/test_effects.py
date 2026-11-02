import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from meme import effects
from meme.input_source import acquire_image


class EffectsTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        image = Image.new("RGBA", (96, 72), (20, 40, 80, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((8, 8, 42, 50), fill=(240, 80, 40, 220))
        draw.ellipse((48, 12, 88, 62), fill=(30, 220, 130, 180))
        self.png = self.root / "source.png"
        image.save(self.png)

        frame_two = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        self.gif = self.root / "source.gif"
        image.save(
            self.gif,
            save_all=True,
            append_images=[frame_two],
            duration=[80, 120],
            loop=0,
            disposal=2,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_all_effects_support_static_images(self):
        for name in ("kaleidoscope", "pixelate", "emboss", "oil_paint", "glitch"):
            with self.subTest(effect=name):
                output = self.root / f"{name}.png"
                getattr(effects, name)(str(self.png), str(output))
                with Image.open(output) as result:
                    expected_size = (1200, 1200) if name == "kaleidoscope" else (96, 72)
                    self.assertEqual(result.size, expected_size)
                    self.assertEqual(result.format, "PNG")

    def test_kaleidoscope_supports_animated_gif(self):
        output = self.root / "kaleidoscope.gif"
        effects.kaleidoscope(str(self.gif), str(output))
        with Image.open(output) as result:
            self.assertTrue(result.is_animated)
            self.assertEqual(result.n_frames, 2)
            self.assertEqual(result.info.get("loop"), 0)

    def test_input_source_accepts_local_absolute_path(self):
        output = self.root / "copied-local.png"
        acquire_image(str(self.png.resolve()), str(output))
        self.assertEqual(output.read_bytes(), self.png.read_bytes())

    def test_input_source_accepts_file_uri(self):
        output = self.root / "copied-uri.png"
        acquire_image(self.png.resolve().as_uri(), str(output))
        self.assertEqual(output.read_bytes(), self.png.read_bytes())


if __name__ == "__main__":
    unittest.main()
