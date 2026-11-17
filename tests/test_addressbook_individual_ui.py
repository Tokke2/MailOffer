import os
import unittest
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt6.QtWidgets import QApplication, QPushButton
    from PyQt6.QtCore import QPoint
    from script.recipients import AddressBookDialog
    QT = True
except ImportError:
    QT = False


@unittest.skipUnless(QT, 'Qt unavailable')
class AddressBookIndividualTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_no_copy_buttons_or_context_actions(self):
        dialog = AddressBookDialog()
        try:
            labels = [b.text().casefold() for b in dialog.findChildren(QPushButton)]
            self.assertFalse(any('bcc' in t or ' cc' in t or '→ to' in t or 'som to' in t for t in labels))
            self.assertIn('➕ lägg till markerade', labels)
            self.assertIn('eget mejl', dialog._feedback_lbl.text())
            menus = []
            def capture(menu, *_):
                menus.append([a.text().casefold() for a in menu.actions()])
                return None
            dialog._contact_list.addItem('Testkontakt')
            with mock.patch('script.recipients.QMenu.exec', capture), mock.patch.object(dialog, '_category_emails', return_value=['a@example.com']), mock.patch.object(dialog, '_get_selected_emails', return_value=['a@example.com']):
                dialog._cat_list.setCurrentRow(0)
                rect = dialog._cat_list.visualItemRect(dialog._cat_list.item(0))
                dialog._show_category_context_menu(rect.center())
                dialog._show_contact_context_menu(QPoint(0, 0))
            self.assertEqual(len(menus), 2)
            self.assertFalse(any('bcc' in text or ' cc' in text for menu in menus for text in menu))
        finally:
            dialog.close()

    def test_legacy_target_does_not_restore_bcc(self):
        callback = mock.Mock()
        dialog = AddressBookDialog(on_add=callback)
        try:
            dialog._emit_add(['a@example.com', 'a@example.com'], 'bcc')
            callback.assert_called_once_with(['a@example.com'], 'to')
            self.assertIn('eget mejl', dialog._feedback_lbl.text())
        finally:
            dialog.close()
