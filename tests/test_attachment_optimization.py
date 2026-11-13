from pathlib import Path
import tempfile
import unittest
try:
    from PIL import Image
except ImportError:
    Image = None
from core.email_sender import _compress_attachments


@unittest.skipUnless(Image, 'Pillow unavailable')
class AttachmentOptimizationTests(unittest.TestCase):
    def test_png_lossless_original_untouched_and_names_do_not_collide(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            sources = []
            originals = []
            for name, color in (('a', 'red'), ('b', 'blue')):
                directory = base / name
                directory.mkdir()
                src = directory / 'photo.png'
                Image.new('RGB', (600, 400), color).save(src, compress_level=0)
                sources.append(str(src))
                originals.append(src.read_bytes())
            paths, tmp, count = _compress_attachments(sources)
            try:
                self.assertEqual(count, 2)
                self.assertNotEqual(paths[0], paths[1])
                for src, out, original in zip(sources, paths, originals):
                    self.assertEqual(Path(src).read_bytes(), original)
                    self.assertLess(Path(out).stat().st_size, len(original))
                    with Image.open(src) as a, Image.open(out) as b:
                        self.assertEqual(a.size, b.size)
                        self.assertEqual(a.tobytes(), b.tobytes())
            finally:
                if tmp: tmp.cleanup()

    def test_animation_is_not_flattened(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / 'animated.webp'
            Image.new('RGB', (400, 400), 'red').save(src, save_all=True,
                append_images=[Image.new('RGB', (400, 400), 'blue')], duration=100, loop=0, lossless=True)
            paths, tmp, count = _compress_attachments([str(src)])
            self.assertEqual(paths, [str(src)])
            self.assertEqual(count, 0)
            self.assertIsNone(tmp)

    def test_larger_candidate_uses_original(self):
        with tempfile.TemporaryDirectory() as folder:
            src = Path(folder) / 'small.jpg'
            Image.new('RGB', (10, 10), 'white').save(src)
            paths, tmp, count = _compress_attachments([str(src)])
            self.assertEqual(paths, [str(src)])
            self.assertEqual(count, 0)
            self.assertIsNone(tmp)
