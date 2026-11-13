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
    def test_no_bundled_executable_or_native_launcher(self):
        self.assertFalse((ROOT / 'MailOffer.exe').exists())
        self.assertFalse((ROOT / 'launcher').exists())
        self.assertNotIn('MailOffer.exe', (ROOT / 'Starta EmailApp.vbs').read_text(encoding='utf-8'))
        self.assertNotIn('MailOffer.exe', (ROOT / 'main.pyw').read_text(encoding='utf-8'))

    def test_extension_archive_contains_current_shared_icon(self):
        with ZipFile(ROOT / 'thunderbird/MailOffer.xpi') as package:
            self.assertEqual(package.read('icon.png'), (ROOT / 'thunderbird/icon.png').read_bytes())

    def make_settings(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        (base / '.portable').touch()
        return SettingsManager(base)

    def test_autostart_ignores_leftover_exe(self):
        settings = self.make_settings()
        (settings.base_dir / 'MailOffer.exe').touch()
        (settings.base_dir / 'Starta EmailApp.vbs').touch()
        with mock.patch('core.settings_manager.IS_WINDOWS', True), mock.patch('core.settings_manager.sys.frozen', False, create=True):
            self.assertEqual(Path(settings._get_autostart_args()[0]).name, 'wscript.exe')
            self.assertNotIn('MailOffer.exe', settings._get_autostart_command())

    def test_missing_exe_uses_script_host_never_direct_python(self):
        settings = self.make_settings()
        (settings.base_dir / 'Starta EmailApp.vbs').touch()
        with mock.patch('core.settings_manager.IS_WINDOWS', True), mock.patch('core.settings_manager.sys.frozen', False, create=True):
            args = settings._get_autostart_args()
            self.assertEqual(Path(args[0]).name, 'wscript.exe')
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
