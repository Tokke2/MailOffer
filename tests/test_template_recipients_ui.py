import ast
import os
from pathlib import Path
import unittest
from unittest import mock

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt6.QtWidgets import QApplication, QComboBox, QPushButton, QDialog
    from ui.template_recipients import TemplateRecipientsDialog
    HAS_QT = True
except ImportError:
    HAS_QT = False

ROOT = Path(__file__).resolve().parents[1]

@unittest.skipUnless(HAS_QT, 'Qt unavailable')
class TemplateRecipientsUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_manual_dropdown_dedup_and_remove(self):
        dialog = TemplateRecipientsDialog(None, 'A.txt', ['old@example.com'], [('a@example.com', 'Anna')])
        try:
            dialog.combo.setCurrentIndex(1)
            dialog.add_from_combo()
            dialog.combo.setEditText('A@EXAMPLE.COM')
            dialog.add_from_combo()
            self.assertEqual(dialog.emails(), ['old@example.com', 'a@example.com'])
            dialog.choices.setCurrentRow(0)
            dialog.remove_selected()
            self.assertEqual(dialog.emails(), ['a@example.com'])
            dialog.reject()
            self.assertEqual(dialog.result(), QDialog.DialogCode.Rejected)
        finally:
            dialog.close()

    def harness(self):
        tree = ast.parse((ROOT / 'ui/main_window.py').read_text(encoding='utf-8'))
        methods = [node for parent in tree.body if isinstance(parent, ast.ClassDef)
                   for node in parent.body if isinstance(node, ast.FunctionDef) and node.name in
                   ('_refresh_template_recipients', '_add_template_recipient')]
        scope = {}
        exec(compile(ast.Module(body=methods, type_ignores=[]), 'recipient-ui', 'exec'), scope)
        obj = type('Harness', (), {key: value for key, value in scope.items() if key.startswith('_')})()
        obj._last_tpl = Path('A.txt')
        obj.settings = {'template_recipient_rules': {'A.txt': ['a@example.com', 'b@example.com'], 'B.txt': ['other@example.com']}}
        obj._template_recipient_combo = QComboBox()
        obj._template_recipient_add = QPushButton()
        obj._contact_lang = lambda email: 'sv'
        obj._refresh_preview = mock.Mock()
        obj._status = mock.Mock()
        obj._add_recipient = mock.Mock(return_value=1)
        return obj

    def test_switching_templates_never_adds_or_sends(self):
        obj = self.harness()
        obj._refresh_template_recipients()
        self.assertEqual(obj._template_recipient_combo.count(), 3)
        obj._add_recipient.assert_not_called()
        obj._template_recipient_combo.setCurrentIndex(2)
        obj._add_template_recipient()
        self.assertEqual(obj._add_recipient.call_args.kwargs['email'], 'b@example.com')
        obj._add_recipient.reset_mock()
        obj._last_tpl = Path('B.txt')
        obj._refresh_template_recipients()
        obj._add_recipient.assert_not_called()
        self.assertEqual(obj._template_recipient_combo.itemData(1), 'other@example.com')
        obj._last_tpl = None
        obj._refresh_template_recipients()
        self.assertFalse(obj._template_recipient_add.isEnabled())

    def test_add_all_only_after_explicit_action(self):
        obj = self.harness()
        obj._refresh_template_recipients()
        obj._add_recipient.assert_not_called()
        obj._add_template_recipient()
        self.assertEqual([c.kwargs['email'] for c in obj._add_recipient.call_args_list], ['a@example.com', 'b@example.com'])
        self.assertTrue(all(c.args == ('bcc',) for c in obj._add_recipient.call_args_list))

    def sync_harness(self):
        from PyQt6.QtCore import Qt
        from PyQt6.QtWidgets import QListWidget, QListWidgetItem
        from core.email_lists import extract_email_addresses
        tree = ast.parse((ROOT / 'ui/main_window.py').read_text(encoding='utf-8'))
        methods = [node for parent in tree.body if isinstance(parent, ast.ClassDef)
                   for node in parent.body if isinstance(node, ast.FunctionDef) and node.name == '_sync_template_bcc']
        scope = {'Qt': Qt, 'extract_email_addresses': extract_email_addresses}
        exec(compile(ast.Module(body=methods, type_ignores=[]), 'sync-ui', 'exec'), scope)
        obj = type('SyncHarness', (), {'_sync_template_bcc': scope['_sync_template_bcc']})()
        obj._last_tpl = Path('A.txt')
        obj.settings = {'template_recipient_rules': {'A.txt': ['a@example.com'], 'B.txt': ['b@example.com']},
                        'template_bcc_rules': {'A.txt': ['legacy@example.com']}}
        obj._bcc_list = QListWidget()
        obj._to_list = QListWidget()
        obj._contact_lang = lambda email: 'en' if email == 'legacy@example.com' else 'sv'
        obj._list_items = lambda widget: [extract_email_addresses(widget.item(i).text())[0] for i in range(widget.count())]
        def add(target, email, show_warning=False, lang='sv'):
            item = QListWidgetItem(email + ' [' + lang + ']')
            item.setData(Qt.ItemDataRole.UserRole, lang)
            obj._bcc_list.addItem(item)
            obj._sync_template_bcc()  # real add refreshes preview: verify recursion guard
            return 1
        obj._add_recipient = add
        return obj

    def test_automatic_bcc_switch_preserves_manual_rows_and_language(self):
        from PyQt6.QtCore import Qt
        obj = self.sync_harness()
        obj._bcc_list.addItem('manual@example.com [sv]')
        obj._sync_template_bcc()
        self.assertEqual(obj._list_items(obj._bcc_list), ['manual@example.com', 'a@example.com', 'legacy@example.com'])
        obj._bcc_list.item(1).setData(Qt.ItemDataRole.UserRole, 'en')
        obj._sync_template_bcc()
        self.assertEqual(obj._bcc_list.count(), 3)
        self.assertEqual(obj._bcc_list.item(1).data(Qt.ItemDataRole.UserRole), 'en')
        obj._last_tpl = Path('B.txt')
        obj._sync_template_bcc()
        self.assertEqual(obj._list_items(obj._bcc_list), ['manual@example.com', 'b@example.com'])
        obj._last_tpl = None
        obj._sync_template_bcc()
        self.assertEqual(obj._list_items(obj._bcc_list), ['manual@example.com'])

    def test_linked_addresses_moved_out_of_visible_to(self):
        obj = self.sync_harness()
        obj._to_list.addItem('A@EXAMPLE.COM [sv]')
        obj._to_list.addItem('visible@example.com [sv]')
        obj._sync_template_bcc()
        self.assertEqual(obj._list_items(obj._to_list), ['visible@example.com'])
        self.assertIn('a@example.com', obj._list_items(obj._bcc_list))

    def test_removing_saved_link_removes_owned_row_not_manual(self):
        obj = self.sync_harness()
        obj._bcc_list.addItem('a@example.com [sv]')
        obj._sync_template_bcc()
        obj.settings['template_recipient_rules'] = {}
        obj.settings['template_bcc_rules'] = {}
        obj._sync_template_bcc()
        self.assertEqual(obj._list_items(obj._bcc_list), ['a@example.com'])
