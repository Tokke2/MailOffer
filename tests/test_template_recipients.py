from pathlib import Path
import tempfile
import unittest
from core.template_recipients import normalize_template_recipients, template_recipients

class TemplateRecipientTests(unittest.TestCase):
    def test_exact_template_selection_and_validation(self):
        rules = {'A.txt': [' a@example.com ', 'A@EXAMPLE.COM', 'invalid'], 'B.html': ['b@example.com'], '../bad': ['a@example.com']}
        self.assertEqual(normalize_template_recipients(rules), {'A.txt': ['a@example.com'], 'B.html': ['b@example.com']})
        self.assertEqual(template_recipients('B.html', rules), ['b@example.com'])
        self.assertEqual(template_recipients('other', rules), [])
        self.assertEqual(len(rules['A.txt']), 3)

    def test_settings_roundtrip_independent_of_bcc(self):
        from core.settings_manager import SettingsManager
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / '.portable').touch()
            settings = SettingsManager(root)
            settings.set('template_recipient_rules', {'A.txt': ['a@example.com']})
            settings.set('template_bcc_rules', {'A.txt': ['b@example.com']})
            self.assertTrue(settings.save())
            loaded = SettingsManager(root)
            self.assertEqual(loaded.get('template_recipient_rules'), {'A.txt': ['a@example.com']})
            self.assertEqual(loaded.get('template_bcc_rules'), {'A.txt': ['b@example.com']})

    def test_legacy_and_new_rules_union_as_bcc(self):
        from core.template_recipients import linked_bcc
        rules = {'A.txt': ['a@example.com', 'b@example.com'], 'B.txt': ['b@example.com']}
        bcc = {'A.txt': ['A@EXAMPLE.COM', 'c@example.com']}
        self.assertEqual(linked_bcc('A.txt', rules, bcc), ['a@example.com', 'b@example.com', 'c@example.com'])
        self.assertEqual(linked_bcc('B.txt', rules, bcc), ['b@example.com'])
        self.assertEqual(linked_bcc('', rules, bcc), [])
        self.assertEqual(len(bcc['A.txt']), 2)
