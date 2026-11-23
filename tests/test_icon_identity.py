import sys
import unittest
from unittest import mock
from core.app_icon import set_windows_app_id, WINDOWS_APP_ID


class IconIdentityTests(unittest.TestCase):
    def test_non_windows_no_native_call(self):
        with mock.patch('core.app_icon.sys.platform', 'linux'):
            self.assertFalse(set_windows_app_id())

    def test_windows_sets_stable_identity(self):
        native = mock.Mock()
        native.shell32.SetCurrentProcessExplicitAppUserModelID.return_value = 0
        with mock.patch('core.app_icon.sys.platform', 'win32'), mock.patch('ctypes.windll', native, create=True):
            self.assertTrue(set_windows_app_id())
        native.shell32.SetCurrentProcessExplicitAppUserModelID.assert_called_once_with(WINDOWS_APP_ID)
        self.assertNotIn('1.0.0', WINDOWS_APP_ID)

    def test_qt_uses_fractional_monitor_scaling_not_legacy_auto_scaling(self):
        from pathlib import Path
        text = (Path(__file__).resolve().parents[1] / 'main.pyw').read_text(encoding='utf-8')
        self.assertIn('HighDpiScaleFactorRoundingPolicy.PassThrough', text)
        self.assertNotIn('setdefault("QT_AUTO_SCREEN_SCALE_FACTOR"', text)
        self.assertNotIn('SetProcessDPIAware(', text)
