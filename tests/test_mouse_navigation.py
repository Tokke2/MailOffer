import os
import unittest
from unittest import mock
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QDialog
    from PyQt6.QtTest import QTest
    from ui.mouse_navigation import install_mouse_navigation
    HAS_QT = True
except ImportError:
    HAS_QT = False

@unittest.skipUnless(HAS_QT, 'Qt required')
class MouseNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = QWidget()
        layout = QVBoxLayout(self.window)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        for name in ('Send', 'Contacts', 'Preview', 'Settings'):
            self.tabs.addTab(QWidget(), name)
        self.guard = install_mouse_navigation(self.window, self.tabs)
        self.window.show()
        self.window.activateWindow()
        self.app.processEvents()

    def tearDown(self):
        self.app.removeEventFilter(self.guard)
        self.window.close()
        self.window.deleteLater()
        self.app.processEvents()

    def test_back_forward_click_once_and_boundary(self):
        self.tabs.setCurrentIndex(1)
        self.tabs.setCurrentIndex(2)
        with mock.patch.object(QApplication, 'activeWindow', return_value=self.window):
            QTest.mouseClick(self.tabs.currentWidget(), Qt.MouseButton.BackButton)
            self.assertEqual(self.tabs.currentIndex(), 1)
            QTest.mouseClick(self.tabs.currentWidget(), Qt.MouseButton.ForwardButton)
            self.assertEqual(self.tabs.currentIndex(), 2)
            QTest.mouseClick(self.tabs.currentWidget(), Qt.MouseButton.ForwardButton)
            self.assertEqual(self.tabs.currentIndex(), 2)
        self.assertEqual(len(self.guard.history), 3)

    def test_new_choice_clears_forward_history(self):
        self.tabs.setCurrentIndex(1)
        self.tabs.setCurrentIndex(2)
        self.guard.navigate(-1)
        self.tabs.setCurrentIndex(3)
        self.assertFalse(self.guard.navigate(1))
        self.assertTrue(self.guard.navigate(-1))
        self.assertEqual(self.tabs.currentIndex(), 1)

    def test_hidden_disabled_removed_tabs_are_skipped(self):
        for index in (1, 2, 3):
            self.tabs.setCurrentIndex(index)
        self.tabs.setTabVisible(2, False)
        self.tabs.setTabEnabled(1, False)
        self.guard.navigate(-1)
        self.assertEqual(self.tabs.currentIndex(), 0)
        self.tabs.removeTab(2)
        self.guard.navigate(1)
        self.assertEqual(self.tabs.tabText(self.tabs.currentIndex()), 'Settings')

    def test_inactive_window_and_dialog_do_not_navigate(self):
        self.tabs.setCurrentIndex(1)
        with mock.patch.object(QApplication, 'activeWindow', return_value=None):
            QTest.mouseClick(self.tabs.currentWidget(), Qt.MouseButton.BackButton)
        self.assertEqual(self.tabs.currentIndex(), 1)
        dialog = QDialog(self.window)
        with mock.patch.object(QApplication, 'activeWindow', return_value=self.window), mock.patch.object(QApplication, 'activeModalWidget', return_value=dialog):
            QTest.mouseClick(self.tabs.currentWidget(), Qt.MouseButton.BackButton)
        self.assertEqual(self.tabs.currentIndex(), 1)
        dialog.close()
