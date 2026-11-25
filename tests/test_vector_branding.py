from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


class VectorBrandingTests(unittest.TestCase):
    def test_print_masters_have_outlines_without_rasters_or_fonts(self):
        svg_rel_paths = (
            'icons/app_icon.svg',
            'icons/mailoffer-logo.svg',
            'icons/mailoffer-logo-light.svg',
            'icons/mailoffer-logo-black.svg',
            'tryck/E-postofferten-farg.svg',
            'tryck/E-postofferten-svart.svg',
            'tryck/E-postofferten-symbol.svg',
            'tryck/E-postofferten-symbol-farg-plan.svg',
        )
        for rel in svg_rel_paths:
            svg = ET.parse(ROOT / rel).getroot()
            self.assertIn('viewBox', svg.attrib, rel)
            self.assertTrue(svg.attrib['width'].endswith('mm'), rel)
            paths = [n for n in svg.iter() if n.tag.endswith('}path')]
            self.assertGreater(len(paths), 8, rel)
            group_ids = {
                n.attrib.get('id', '')
                for n in svg.iter()
                if n.tag.endswith('}g')
            }
            for expected_layer in (
                'lager-symbolplatta',
                'lager-offertblad',
                'lager-kuvert-fram',
                'lager-offertsigill',
            ):
                self.assertIn(expected_layer, group_ids, f'{rel} missing {expected_layer}')
            for node in svg.iter():
                self.assertNotIn(
                    node.tag.rsplit('}', 1)[-1],
                    ('image', 'text', 'script', 'foreignObject'),
                    rel,
                )
                self.assertFalse(any('href' in key for key in node.attrib), rel)

    def test_icon_exports_and_extension_are_current(self):
        for name in (
            'app_icon.png',
            'app_icon.ico',
            'app_icon.icns',
            'mailoffer-logo.png',
            'mailoffer-logo-light.png',
        ):
            self.assertGreater((ROOT / 'icons' / name).stat().st_size, 100, name)
        self.assertEqual(
            (ROOT / 'E-postofferten-kontakter.xpi').read_bytes(),
            (ROOT / 'thunderbird/MailOffer.xpi').read_bytes(),
        )
        with ZipFile(ROOT / 'thunderbird/MailOffer.xpi') as archive:
            self.assertEqual(
                archive.read('icon.png'),
                (ROOT / 'thunderbird/icon.png').read_bytes(),
            )
            self.assertIn(b'icon.png', archive.read('popup.html'))

    def test_flat_print_masters_are_editable_flat_outlines(self):
        self.assertTrue((ROOT / 'tryck/README.md').is_file())
        for rel in (
            'tryck/E-postofferten-farg.svg',
            'tryck/E-postofferten-svart.svg',
            'tryck/E-postofferten-symbol-farg-plan.svg',
        ):
            svg = ET.parse(ROOT / rel).getroot()
            for node in svg.iter():
                self.assertNotIn(
                    node.tag.rsplit('}', 1)[-1],
                    ('linearGradient', 'radialGradient', 'filter'),
                    rel,
                )
                self.assertNotIn('opacity', node.attrib, rel)
                self.assertNotIn('stroke-opacity', node.attrib, rel)
                self.assertNotIn('stroke-width', node.attrib, rel)
                self.assertNotIn('transform', node.attrib, rel)
                self.assertNotIn('url(', str(node.attrib), rel)

    def test_non_reused_suggestion_ledger_has_unique_batches_of_ten(self):
        ledger = (ROOT / 'docs/forslagslogg.md').read_text(encoding='utf-8')
        ids = re.findall(r'^\d+\.\s+\*\*`#(F\d{2,})`', ledger, re.MULTILINE)
        self.assertGreaterEqual(len(ids), 10)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(ids) % 10, 0)
