"""Native bridge self-test must not create or change user contacts."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from core.tb_bridge import test_native_host
from core.signatures import preview_signature

ROOT = Path(__file__).resolve().parents[1]


class ThunderbirdBridgeTests(unittest.TestCase):
    def test_real_native_protocol_ping(self):
        result = test_native_host(ROOT)
        self.assertTrue(result['ok'])
        self.assertEqual(Path(result['contacts_path']), ROOT / 'adresslistor' / 'contacts.json')

    def test_ping_does_not_write_contacts(self):
        spec = importlib.util.spec_from_file_location('mailoffer_native_test', ROOT / 'thunderbird' / 'native_host.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'contacts.json'
            with mock.patch.object(module, 'CONTACTS_PATH', path):
                self.assertTrue(module.handle({'action': 'ping'})['ok'])
                self.assertFalse(path.exists())

    def test_preview_uses_local_logo_and_escapes_text(self):
        plain, html = preview_signature('Body', '<body>Body</body>', {
            'signature_text': '<Test>', 'signature_contact': '123',
            'signature_logo': str(ROOT / 'thunderbird' / 'icon.png')})
        self.assertIn('<Test>', plain)
        self.assertIn('&lt;Test&gt;', html)
        self.assertIn((ROOT / 'thunderbird' / 'icon.png').as_uri(), html)
        self.assertNotIn('cid:', html)
