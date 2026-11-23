import os
import unittest
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
    from PyQt6.QtGui import QPalette, QFontDatabase
    from ui.styles import StyleEngine, DARK_COLORS, LIGHT_COLORS, preferred_ui_font
    QT = True
except ImportError:
    QT = False


@unittest.skipUnless(QT, 'Qt unavailable')
class DesignSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_both_themes_update_native_palette_and_font(self):
        old_palette, old_font, old_qss = self.app.palette(), self.app.font(), self.app.styleSheet()
        try:
            settings = mock.Mock()
            for mode, colors in (('light', LIGHT_COLORS), ('dark', DARK_COLORS), ('light', LIGHT_COLORS)):
                settings.get.return_value = mode
                style = StyleEngine(settings, mock.Mock())
                style.apply(self.app)
                self.assertEqual(self.app.palette().color(QPalette.ColorRole.Window).name(), colors['background'].lower())
                self.assertEqual(self.app.palette().color(QPalette.ColorRole.Text).name(), colors['text'].lower())
                self.assertEqual(self.app.font().pointSizeF(), 10.5)
                installed = QFontDatabase.families()
                if installed:
                    self.assertIn(preferred_ui_font(), installed)
                else:
                    self.assertEqual(preferred_ui_font(), self.app.font().family())
                self.assertIn('QToolTip', self.app.styleSheet())
        finally:
            self.app.setPalette(old_palette)
            self.app.setFont(old_font)
            self.app.setStyleSheet(old_qss)

    def test_real_toolbar_wraps_instead_of_clipping_buttons(self):
        from ui.main_window import MainWindow
        from ui.responsive import WrapLayout
        host = QWidget()
        layout = QVBoxLayout(host)
        receiver = mock.Mock()
        MainWindow._build_toolbar(receiver, layout)
        try:
            toolbar = layout.itemAt(0).widget().layout()
            self.assertIsInstance(toolbar, WrapLayout)
            self.assertGreater(toolbar.heightForWidth(760), toolbar.heightForWidth(1440))
            receiver.btn_send.click()
            receiver._send.assert_called_once()
        finally:
            host.close()

    def test_app_icon_renders_for_high_density_without_fixed_raster_scaling(self):
        from PyQt6.QtCore import QSize
        from core.app_icon import get_app_icon, clear_icon_cache
        clear_icon_cache()
        icon = get_app_icon()
        for ratio in (1.0, 1.25, 1.5, 2.0):
            pixmap = icon.pixmap(QSize(32, 32), ratio)
            self.assertFalse(pixmap.isNull())
            self.assertGreaterEqual(pixmap.width(), int(32 * ratio))
            self.assertGreaterEqual(pixmap.devicePixelRatio(), ratio)
