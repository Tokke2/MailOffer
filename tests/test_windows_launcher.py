"""Portable checks for the Windows artifact; no executable is run on Linux."""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest import mock
from zipfile import ZipFile

from core.settings_manager import SettingsManager

ROOT = Path(__file__).resolve().parents[1]


class WindowsLauncherTests(unittest.TestCase):
    def test_native_launcher_has_gui_subsystem_and_embedded_artwork(self):
        data = (ROOT / 'MailOffer.exe').read_bytes()
        self.assertEqual(data[:2], b'MZ')
        pe = struct.unpack_from('<I', data, 60)[0]
        self.assertEqual(data[pe:pe + 4], b'PE\x00\x00')
        self.assertEqual(struct.unpack_from('<H', data, pe + 4)[0], 0x8664)
        self.assertEqual(struct.unpack_from('<H', data, pe + 24 + 68)[0], 2)
        self.assertIn(b'\x89PNG\r\n\x1a\n', data)
        self.assertIn('Rickard Längkvist'.encode('utf-16le'), data)
        self.assertIn('MailOffer'.encode('utf-16le'), data)

    def test_extension_archive_contains_current_shared_icon(self):
        with ZipFile(ROOT / 'thunderbird/MailOffer.xpi') as package:
            self.assertEqual(package.read('icon.png'), (ROOT / 'thunderbird/icon.png').read_bytes())

    def make_settings(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        (base / '.portable').touch()
        return SettingsManager(base)

    def test_autostart_prefers_branded_exe_not_python_or_pyw(self):
        settings = self.make_settings()
        (settings.base_dir / 'MailOffer.exe').touch()
        (settings.base_dir / 'Starta EmailApp.vbs').touch()
        with mock.patch('core.settings_manager.IS_WINDOWS', True), mock.patch('core.settings_manager.sys.frozen', False, create=True):
            self.assertEqual(settings._get_autostart_args(), [str(settings.base_dir / 'MailOffer.exe'), '--background'])
            self.assertEqual(settings._get_autostart_command(), f'"{settings.base_dir / "MailOffer.exe"}" --background')

    def test_missing_exe_uses_script_host_never_direct_python(self):
        settings = self.make_settings()
        (settings.base_dir / 'Starta EmailApp.vbs').touch()
        with mock.patch('core.settings_manager.IS_WINDOWS', True), mock.patch('core.settings_manager.sys.frozen', False, create=True):
            args = settings._get_autostart_args()
            self.assertEqual(args[0], 'wscript.exe')
            self.assertNotIn('main.pyw', ' '.join(args))
            self.assertNotIn('python', settings._get_autostart_command().lower())

    def test_missing_both_launchers_does_not_register_python(self):
        settings = self.make_settings()
        with mock.patch('core.settings_manager.IS_WINDOWS', True), mock.patch('core.settings_manager.sys.frozen', False, create=True):
            with self.assertRaises(FileNotFoundError):
                settings._get_autostart_args()
            with self.assertRaises(FileNotFoundError):
                settings._get_autostart_command()

    def test_existing_autostart_migrates_to_new_command(self):
        settings = self.make_settings()
        settings.set('autostart', True)
        with mock.patch.object(settings, 'classify_autostart', return_value='different'), mock.patch.object(settings, 'set_autostart', return_value=True) as apply:
            self.assertTrue(settings.sync_autostart())
            apply.assert_called_once_with(True)
