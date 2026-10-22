import json
import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from zipfile import ZipFile
from unittest.mock import patch
from core.auto_backup import run_due_backup
from core.signatures import append_signature, logo_part
from core.sender_profiles import normalize_sender_profile
from tools.build_thunderbird import build


class Settings(dict):
    settings_path = None
    def set(self, key, value):
        self[key] = value


class FeatureTests(unittest.TestCase):
    def test_backup_schedule_retention_and_redaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            settings = Settings(auto_backup_enabled=True, auto_backup_hours='24', auto_backup_keep='2')
            settings.settings_path = base / 'settings.json'
            settings.settings_path.write_text(json.dumps({'password': 'secret', 'sender_profiles': [{'password': 'secret2'}]}))
            now = datetime(2026, 10, 22, tzinfo=timezone.utc)
            for day in range(4):
                result = run_due_backup(base, settings, now=now + timedelta(days=day))
                self.assertTrue(result.is_file())
                with ZipFile(result) as archive:
                    content = b''.join(archive.read(name) for name in archive.namelist())
                    self.assertNotIn(b'secret', content)
                self.assertIsNone(run_due_backup(base, settings, now=now + timedelta(days=day, minutes=1)))
            self.assertEqual(len(list(result.parent.glob('auto-*.zip'))), 2)

    def test_backup_failure_keeps_previous_and_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            settings = Settings(auto_backup_enabled=True)
            with patch('core.auto_backup.create_full_backup', side_effect=OSError('disk')):
                with self.assertRaises(OSError):
                    run_due_backup(tmp, settings)
            self.assertNotIn('auto_backup_last', settings)
            self.assertFalse(list(Path(tmp).rglob('*.partial')))

    def test_backup_disabled(self):
        self.assertIsNone(run_due_backup('.', Settings()))

    def test_signature_profile_and_escape(self):
        p = normalize_sender_profile({'signature_text': 'Hej\n<script>', 'signature_contact': 'Telefon 123', 'signature_logo': 'logo.png'})
        plain, html = append_signature('Body', '<html><body>Body</body></html>', p['signature_text'], p['signature_contact'], True)
        self.assertIn('Telefon 123', plain)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>', html)
        self.assertLess(html.index('cid:mailoffer-signature'), html.index('</body>'))

    def test_no_signature_unchanged(self):
        self.assertEqual(append_signature('abc', None), ('abc', None))

    def test_logo_embedded_and_invalid_rejected(self):
        part = logo_part('thunderbird/icon.png')
        self.assertEqual(part['Content-ID'], '<mailoffer-signature>')
        self.assertTrue(part.get_content_type().startswith('image/'))
        with self.assertRaises(ValueError):
            logo_part('README.md')

    def test_xpi(self):
        with ZipFile(build()) as archive:
            manifest = json.loads(archive.read('manifest.json'))
            self.assertEqual(manifest['version'], '1.0.0')
            self.assertIn('nativeMessaging', manifest['permissions'])
            js = archive.read('background.js').decode()
            self.assertIn('mailto:*', js)
            self.assertNotIn('native_host.py', archive.namelist())
