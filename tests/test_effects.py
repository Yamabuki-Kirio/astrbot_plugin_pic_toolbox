import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from meme import effects
from meme.input_source import acquire_image
from meme.qq_face import make_qq_face_source, qq_face_candidates
from meme.gif_utils import save_rgba_gif


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

    def test_qq_face_source_supports_new_face_ids(self):
        source = make_qq_face_source(480)
        self.assertEqual(source, "qqface://480")
        candidates = qq_face_candidates(source)
        self.assertEqual(
            candidates[0],
            "https://koishi.js.org/QFace/assets/qq_emoji/480/apng/480.png",
        )
        self.assertIn(
            "https://qzonestyle.gtimg.cn/qzone/em/e480.gif",
            candidates,
        )

    def test_qq_face_source_rejects_invalid_ids(self):
        self.assertIsNone(make_qq_face_source("not-a-number"))
        self.assertEqual(qq_face_candidates("qqface://bad"), [])

    def test_gif_writer_ignores_apng_transparency_bytes(self):
        output = self.root / "apng-transparency.gif"
        palette = [value for index in range(256) for value in (index, index, index)]
        frames = [Image.open(self.png).convert("RGBA")]
        save_rgba_gif(
            frames,
            [41.666666666666664],
            str(output),
            source_palette=palette,
            source_trans_idx=b"\x00\x15/Je\x7f\x9a\xae\xc1\xd4\xe1\xfc\xfe",
        )
        with Image.open(output) as result:
            self.assertEqual(result.format, "GIF")
            self.assertEqual(result.size, frames[0].size)


if __name__ == "__main__":
    unittest.main()
