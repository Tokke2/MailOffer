import os
import time
import unittest

@unittest.skipUnless(os.name == 'nt', 'Windows event requires Windows')
class WindowFocusTests(unittest.TestCase):
    def test_event_reveals_hidden_window_without_native_host(self):
        from PyQt6.QtWidgets import QApplication, QWidget
        from core.window_focus import install_focus_handler, request_focus
        app = QApplication.instance() or QApplication([])
        window = QWidget()
        try:
            install_focus_handler(window)
            window.hide()
            self.assertTrue(request_focus())
            deadline = time.monotonic() + 3
            while not window.isVisible() and time.monotonic() < deadline:
                app.processEvents()
                time.sleep(0.01)
            self.assertTrue(window.isVisible())
        finally:
            window.close()
            window.deleteLater()
            app.processEvents()
