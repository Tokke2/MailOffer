import os
import unittest
from unittest import mock
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLineEdit,
        QPlainTextEdit, QPushButton, QScrollArea, QListWidget, QLabel, QDialog)
    from PyQt6.QtTest import QTest
    from ui.keyboard_navigation import configure_tab_flow, install_keyboard_navigation
    HAS_QT = True
except ImportError:
    HAS_QT = False

@unittest.skipUnless(HAS_QT, 'Qt required')
class KeyboardNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        install_keyboard_navigation()

    def test_tab_and_reverse_leave_text_and_do_not_click_send(self):
        window = QWidget()
        layout = QVBoxLayout(window)
        first, text, button = QLineEdit(), QPlainTextEdit(), QPushButton('Send')
        for widget in (first, text, button):
            layout.addWidget(widget)
        sent = mock.Mock()
        button.clicked.connect(sent)
        try:
            self.assertEqual(configure_tab_flow([window]), [first, text, button])
            window.show()
            window.activateWindow()
            first.setFocus()
            self.app.processEvents()
            QTest.keyClick(first, Qt.Key.Key_Tab)
            self.assertIs(self.app.focusWidget(), text)
            QTest.keyClick(text, Qt.Key.Key_Tab)
            self.assertIs(self.app.focusWidget(), button)
            QTest.keyClick(button, Qt.Key.Key_Tab, Qt.KeyboardModifier.ShiftModifier)
            self.assertIs(self.app.focusWidget(), text)
            self.assertEqual(text.toPlainText(), '')
            sent.assert_not_called()
        finally:
            window.close()

    def test_dynamic_layout_labels_and_dialog(self):
        dialog = QDialog()
        layout = QVBoxLayout(dialog)
        label, first, last = QLabel('Model:'), QLineEdit(), QPushButton('Next')
        layout.addWidget(label)
        layout.addWidget(first)
        layout.addWidget(last)
        configure_tab_flow([dialog])
        self.assertIs(label.buddy(), first)
        self.assertEqual(first.accessibleName(), 'Model')
        extra = QLineEdit()
        layout.insertWidget(2, extra)
        self.assertEqual(configure_tab_flow([dialog]), [first, extra, last])
        dialog.close()

    def test_keyboard_context_menu_is_available_without_mouse(self):
        choices = QListWidget()
        choices.addItem('Recipient')
        choices.setCurrentRow(0)
        choices.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        requested = mock.Mock()
        choices.customContextMenuRequested.connect(requested)
        try:
            choices.show()
            choices.activateWindow()
            choices.setFocus()
            self.app.processEvents()
            QTest.keyClick(choices, Qt.Key.Key_F10, Qt.KeyboardModifier.ShiftModifier)
            self.assertEqual(requested.call_count, 1)
            QTest.keyClick(choices, Qt.Key.Key_Menu)
            self.assertEqual(requested.call_count, 2)
        finally:
            choices.close()

    def test_focus_scrolls_field_into_view(self):
        scroll = QScrollArea()
        inner = QWidget()
        layout = QVBoxLayout(inner)
        fields = [QLineEdit() for _ in range(30)]
        for field in fields:
            field.setMinimumHeight(35)
            layout.addWidget(field)
        scroll.setWidget(inner)
        scroll.setWidgetResizable(True)
        scroll.resize(300, 180)
        try:
            scroll.show()
            scroll.activateWindow()
            self.app.processEvents()
            scroll.verticalScrollBar().setValue(0)
            fields[-1].setFocus(Qt.FocusReason.TabFocusReason)
            self.app.processEvents()
            self.assertGreater(scroll.verticalScrollBar().value(), 0)
        finally:
            scroll.close()
