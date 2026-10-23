import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock
from zipfile import ZipFile
from core.sender_profiles import normalize_profile_color, normalize_sender_profile
from core.tb_protocol import compatible
from core.tb_bridge import test_native_host

ROOT = Path(__file__).resolve().parents[1]


class ProfileColourProtocolTests(unittest.TestCase):
    def test_safe_colour_normalization(self):
        self.assertEqual(normalize_profile_color('#ABC123'), '#abc123')
        for value in (None, '', 'red', '#fff', 'red; border: none', '#12ZZ00'):
            self.assertEqual(normalize_profile_color(value), '#4f78b8')
        profile = normalize_sender_profile({'name': 'A', 'profile_color': '#AABBCC'})
        self.assertEqual(profile['profile_color'], '#aabbcc')

    def test_protocol_is_strict(self):
        self.assertTrue(compatible(1))
        for value in (True, '1', 0, 2, None, 1.0):
            self.assertFalse(compatible(value))

    def test_host_rejects_old_extension_before_contact_write(self):
        spec = importlib.util.spec_from_file_location('native_color_protocol_test', ROOT / 'thunderbird' / 'native_host.py')
        host = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(host)
        with mock.patch.object(host, '_save') as save:
            for version in (None, 2, '1'):
                result = host.handle({'action': 'add_contacts', 'protocol_version': version,
                                      'contacts': [{'email': 'test@example.com'}]})
                self.assertFalse(result['ok'])
                self.assertIn('MailOffer.xpi', result['error'])
            save.assert_not_called()

    def test_bundled_xpi_incompatible(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / 'thunderbird'
            directory.mkdir()
            with ZipFile(directory / 'MailOffer.xpi', 'w') as archive:
                archive.writestr('protocol.json', json.dumps({'protocol_version': 2}))
            with self.assertRaisesRegex(RuntimeError, 'XPI'):
                test_native_host(Path(tmp))

    def test_xpi_declares_matching_contract(self):
        with ZipFile(ROOT / 'thunderbird' / 'MailOffer.xpi') as archive:
            protocol = json.loads(archive.read('protocol.json'))
            self.assertTrue(compatible(protocol['protocol_version']))
            self.assertIn('const PROTOCOL_VERSION = 1;', archive.read('background.js').decode())
