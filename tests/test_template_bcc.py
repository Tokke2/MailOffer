from pathlib import Path
import tempfile
import unittest

from core.template_bcc import normalize_template_bcc, template_bcc
from core.send_preflight import build_send_preflight


class TemplateBccTests(unittest.TestCase):
    def test_only_selected_template_gets_defaults(self):
        rules = {"A.txt": ["a@example.com"], "B.docx": ["b@example.com"]}
        self.assertEqual(template_bcc("A.txt", rules), ["a@example.com"])
        self.assertEqual(template_bcc("B.docx", rules), ["b@example.com"])
        self.assertEqual(template_bcc("other.txt", rules), [])
        self.assertEqual(template_bcc("", rules), [])

    def test_validate_dedupe_and_do_not_mutate_input(self):
        rules = {"A.txt": [" a@example.com ", "A@EXAMPLE.COM", "invalid", None, "b@example.com"]}
        self.assertEqual(normalize_template_bcc(rules), {"A.txt": ["a@example.com", "b@example.com"]})
        self.assertEqual(len(rules["A.txt"]), 5)
        self.assertEqual(normalize_template_bcc({"../A.txt": ["a@example.com"], "A.txt": "a@example.com", "B.txt": []}), {})
        self.assertEqual(normalize_template_bcc(None), {})

    def test_defaults_are_in_final_bcc_and_deduplicated_with_to(self):
        params = {"recipients_to": ["to@example.com"], "recipients_bcc": ["BCC@example.com"],
                  "default_bcc": template_bcc("A.txt", {"A.txt": ["bcc@example.com", "to@example.com", "other@example.com"]})}
        report = build_send_preflight(params)
        self.assertEqual(report.bcc_final, ["BCC@example.com", "other@example.com"])
        self.assertEqual(report.overlap, ["to@example.com"])

    def test_test_mail_never_uses_template_defaults(self):
        report = build_send_preflight({"test_mode": True, "recipients_to": ["test@example.com"], "default_bcc": ["bcc@example.com"]})
        self.assertEqual(report.bcc_final, [])

    def test_settings_roundtrip(self):
        from core.settings_manager import SettingsManager
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp) / ".portable").touch()
            settings = SettingsManager(Path(temp))
            self.assertEqual(settings.get("template_bcc_rules"), {})
            settings.set("template_bcc_rules", {"A.txt": ["a@example.com"]})
            self.assertTrue(settings.save())
            restored = SettingsManager(Path(temp))
            self.assertEqual(restored.get("template_bcc_rules"), {"A.txt": ["a@example.com"]})
