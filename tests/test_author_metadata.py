"""Owner attribution in shipped app and extension metadata."""
import json
import unittest
from pathlib import Path
from zipfile import ZipFile
from core.version import AUTHOR, COPYRIGHT, __version__
from core.i18n import tr, set_language, get_language

ROOT = Path(__file__).resolve().parents[1]


class AuthorMetadataTests(unittest.TestCase):
    def test_owner_and_frozen_version(self):
        self.assertEqual(AUTHOR, 'Rickard Längkvist')
        self.assertEqual(COPYRIGHT, '© 2026 Rickard Längkvist')
        self.assertEqual(__version__, '1.0.0')
        self.assertIn(COPYRIGHT, (ROOT / 'README.md').read_text())

    def test_about_both_languages(self):
        previous = get_language()
        try:
            for language in ('sv', 'en'):
                set_language(language)
                text = tr('about.text', version=__version__, repo_url='https://github.com/Tokke2/MailOffer')
                self.assertIn(AUTHOR, text)
                self.assertIn(COPYRIGHT, text)
        finally:
            set_language(previous)

    def test_packaged_extension_author(self):
        with ZipFile(ROOT / 'thunderbird' / 'MailOffer.xpi') as archive:
            self.assertEqual(json.loads(archive.read('manifest.json'))['author'], AUTHOR)
            self.assertIn(COPYRIGHT, archive.read('popup.html').decode())
