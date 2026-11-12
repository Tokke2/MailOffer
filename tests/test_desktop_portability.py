import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from core.desktop_startup import desktop_exec, linux_autostart_dir
from core.settings_manager import SettingsManager, APP_NAME, LAUNCH_AGENT_ID

class DesktopPortabilityTests(unittest.TestCase):
    def test_exec_escaping(self):
        command = desktop_exec(['/opt/My App/python3', '/opt/100%/$app`/main.pyw', '--background'])
        self.assertIn('"/opt/My App/python3"', command)
        self.assertIn('100%%', command)
        self.assertIn('\\$', command)
        self.assertIn('\\`', command)
        with self.assertRaises(ValueError):
            desktop_exec(['invalid\npath'])

    def test_linux_xdg_registration_classifies_python_as_correct(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            base = root / 'My App'
            base.mkdir()
            (base / '.portable').touch()
            settings = SettingsManager(base)
            with mock.patch.dict(os.environ, {'XDG_CONFIG_HOME': str(root / 'xdg')}), mock.patch('core.settings_manager.IS_WINDOWS', False), mock.patch('core.settings_manager.IS_MACOS', False):
                self.assertTrue(settings._set_autostart_linux(True))
                target = linux_autostart_dir() / (APP_NAME + '.desktop')
                self.assertTrue(target.exists())
                self.assertIn('Terminal=false', target.read_text())
                self.assertIn('Path=' + str(settings.base_dir), target.read_text())
                self.assertEqual(settings.classify_autostart(), 'correct')
                self.assertTrue(settings.is_autostart_enabled())
                self.assertTrue(settings._set_autostart_linux(False))
                self.assertFalse(target.exists())

    def test_macos_launch_agent_uses_existing_interpreter(self):
        import plistlib
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.portable').touch()
            settings = SettingsManager(root)
            with mock.patch('core.settings_manager.Path.home', return_value=root), mock.patch('core.settings_manager.IS_WINDOWS', False), mock.patch('core.settings_manager.IS_MACOS', True):
                self.assertTrue(settings._set_autostart_macos(True))
                target = root / 'Library/LaunchAgents' / (LAUNCH_AGENT_ID + '.plist')
                data = plistlib.loads(target.read_bytes())
                self.assertTrue(data['RunAtLoad'])
                self.assertIn('--background', data['ProgramArguments'])
                self.assertEqual(settings.classify_autostart(), 'correct')
                self.assertTrue(settings._set_autostart_macos(False))

    def test_relative_xdg_root_is_not_used(self):
        with mock.patch.dict(os.environ, {'XDG_CONFIG_HOME': 'relative'}):
            self.assertEqual(linux_autostart_dir(), Path.home() / '.config/autostart')
