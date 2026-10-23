import os
import unittest
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt6.QtCore import QRect
    from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QMainWindow, QWidget, QWizard, QWizardPage
    HAS_QT = True
except ImportError:
    HAS_QT = False


@unittest.skipUnless(HAS_QT, 'PyQt6 saknas')
class ScreenFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_geometry_negative_monitor_and_removed_screen(self):
        from ui.screen_fit import bounded_geometry
        available = QRect(-1280, 0, 1280, 720)
        result = bounded_geometry(QRect(3000, 2500, 2000, 1000), available)
        self.assertTrue(available.contains(result))
        self.assertLess(result.x(), 0)

    def test_oversized_dialog_gets_scroll_and_fits(self):
        from ui.screen_fit import fit_window
        dialog = QDialog()
        layout = QVBoxLayout(dialog)
        for _ in range(30):
            layout.addWidget(QLabel('A full line of content'))
        dialog.setMinimumSize(1000, 900)
        dialog.resize(1200, 1000)
        dialog.show()
        self.app.processEvents()
        try:
            fit_window(dialog, QRect(0, 0, 800, 480))
            self.app.processEvents()
            self.assertLessEqual(dialog.width(), 776)
            self.assertLessEqual(dialog.height(), 456)
            self.assertTrue(hasattr(dialog, '_screen_scroll'))
            self.assertGreater(dialog._screen_scroll.verticalScrollBar().maximum(), 0)
        finally:
            dialog.close()

    def test_main_window_content_is_not_lost(self):
        from ui.screen_fit import fit_window
        window = QMainWindow()
        content = QWidget()
        content.setMinimumSize(1100, 800)
        window.setCentralWidget(content)
        window.setMinimumSize(1080, 760)
        window.show()
        self.app.processEvents()
        try:
            fit_window(window, QRect(0, 0, 800, 480))
            self.app.processEvents()
            self.assertIs(window._screen_central_scroll.widget(), content)
            self.assertLessEqual(window.width(), 776)
        finally:
            window.close()

    def test_wizard_pages_remain_reachable(self):
        from ui.screen_fit import fit_window
        wizard = QWizard()
        page = QWizardPage()
        layout = QVBoxLayout(page)
        for _ in range(30):
            layout.addWidget(QLabel('Wizard field'))
        wizard.addPage(page)
        wizard.setMinimumSize(780, 640)
        wizard.show()
        self.app.processEvents()
        try:
            fit_window(wizard, QRect(0, 0, 800, 480))
            self.app.processEvents()
            self.assertTrue(hasattr(page, '_screen_scroll'))
            self.assertLessEqual(wizard.height(), 456)
        finally:
            wizard.close()

    def test_install_idempotent(self):
        from ui.screen_fit import install_screen_fit
        self.assertIs(install_screen_fit(self.app), install_screen_fit(self.app))
