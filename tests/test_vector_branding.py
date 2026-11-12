from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]

class VectorBrandingTests(unittest.TestCase):
    def test_print_masters_have_outlines_without_rasters_or_fonts(self):
        for name in ('app_icon.svg', 'mailoffer-logo.svg', 'mailoffer-logo-black.svg'):
            svg = ET.parse(ROOT / 'icons' / name).getroot()
            self.assertIn('viewBox', svg.attrib)
            self.assertTrue(svg.attrib['width'].endswith('mm'))
            paths = [n for n in svg.iter() if n.tag.endswith('}path')]
            self.assertGreater(len(paths), 0)
            for node in svg.iter():
                self.assertNotIn(node.tag.rsplit('}', 1)[-1], ('image', 'text', 'script', 'foreignObject'))
                self.assertFalse(any('href' in key for key in node.attrib))

    def test_icon_exports_and_extension_are_current(self):
        for name in ('app_icon.png', 'app_icon.ico', 'app_icon.icns', 'mailoffer-logo.png'):
            self.assertGreater((ROOT / 'icons' / name).stat().st_size, 100)
        with ZipFile(ROOT / 'thunderbird/MailOffer.xpi') as archive:
            self.assertEqual(archive.read('icon.png'), (ROOT / 'thunderbird/icon.png').read_bytes())
