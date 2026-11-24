import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from core.compose_draft import read_draft, save_draft, validate as validate_draft
from core.email_sender import _strip_empty_vin_line, send_email
from core.update_session import read_session, save_session

try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QCheckBox, QLineEdit

    from core.event_bus import EventBus
    from core.recovery import RecoveryManager
    from core.settings import Settings
    from script.templates import create_template
    from ui.main_window import MainWindow, vin_required_missing

    HAS_QT = True
except ImportError:
    HAS_QT = False


class NoVinPureLogicTests(unittest.TestCase):
    def test_strip_empty_vin_line_removes_blank_vin_lines_for_english(self) -> None:
        text = (
            "Hello!\n"
            "Registration: ABC123\n"
            "VIN: \n"
            "VIN number:\n"
            "Chassis no: \n"
            "Glass: Windshield\n"
        )
        cleaned = _strip_empty_vin_line(text, "")
        self.assertNotIn("VIN:", cleaned)
        self.assertNotIn("VIN number", cleaned)
        self.assertNotIn("Chassis no", cleaned)
        self.assertIn("Registration: ABC123", cleaned)
        self.assertIn("Glass: Windshield", cleaned)

        # When VIN is actually provided, VIN line is preserved
        with_vin = _strip_empty_vin_line("Hello!\nVIN: YV1ABCDEF12345678\nThanks", "YV1ABCDEF12345678")
        self.assertIn("YV1ABCDEF12345678", with_vin)

    def test_compose_draft_and_update_session_accept_no_vin_bool(self) -> None:
        state = {
            "template_name": "Offert",
            "subject": "Test",
            "body": "Hej",
            "free_text": "",
            "replacements": {"reg": "ABC123", "vin": ""},
            "no_vin": True,
            "to": ["en@example.com"],
            "bcc": [],
            "to_lang": {"en@example.com": "en"},
            "bcc_lang": {},
            "attachment_paths": [],
            "profile_id": "default",
        }
        validated = validate_draft(state)
        self.assertIsNotNone(validated)
        self.assertIs(validated["no_vin"], True)
        with self.assertRaises(ValueError):
            validate_draft({**state, "no_vin": "not-a-bool"})

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            draft_file = base / "draft.json"
            save_draft(draft_file, state)
            loaded = read_draft(draft_file)
            self.assertIsNotNone(loaded)
            self.assertIs(loaded["no_vin"], True)

            session_file = base / "session.json"
            save_session(session_file, {**state, "tab": "send"})
            restored = read_session(session_file)
            self.assertIsNotNone(restored)
            self.assertIs(restored["no_vin"], True)

    def test_dry_run_english_email_without_vin_omits_vin_line_cleanly(self) -> None:
        from email import message_from_string
        from unittest import mock
        from docx import Document
        import core.email_sender as email_sender

        sent_messages = []

        def fake_send_with_retry(*, server, message_str, **kwargs):
            sent_messages.append(message_str)
            return server

        with tempfile.TemporaryDirectory() as tmp:
            tpl = Path(tmp) / "mall.docx"
            doc = Document()
            doc.add_paragraph("Ämne SV: Förfrågan ::reg::")
            doc.add_paragraph("Ämne EN: Inquiry ::reg::")
            doc.add_paragraph("SV:")
            doc.add_paragraph("Hej!\nRegnr: ::reg::\nTack!")
            doc.add_paragraph("EN:")
            doc.add_paragraph("Hello!\nReg: ::reg::\nVIN: ::vin::\nThank you!")
            doc.save(str(tpl))

            with (
                mock.patch.object(email_sender, "connect_smtp", return_value=mock.MagicMock()),
                mock.patch.object(email_sender, "send_with_retry", side_effect=fake_send_with_retry),
                mock.patch.object(email_sender, "close_smtp"),
            ):
                res = send_email(
                    smtp_server="smtp.example.com",
                    smtp_port=587,
                    username="agent@example.com",
                    password="secret",
                    sender_email="agent@example.com",
                    sender_name="Agent",
                    word_file_path=str(tpl),
                    recipients_to=["english@example.com"],
                    recipients_bcc=[],
                    attachments=[],
                    recipients_to_lang={"english@example.com": "en"},
                    replacements={"reg": "MLB87F", "vin": ""},
                    include_english=True,
                    dry_run=False,
                )
        self.assertTrue(res.success)
        self.assertEqual(len(sent_messages), 1)
        parsed = message_from_string(sent_messages[0])
        decoded_parts = [
            part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", errors="replace")
            for part in parsed.walk()
            if part.get_content_type() in ("text/plain", "text/html")
        ]
        self.assertTrue(decoded_parts)
        for body_text in decoded_parts:
            self.assertNotIn("VIN:", body_text)
            self.assertNotIn("::vin::", body_text)
            self.assertIn("MLB87F", body_text)


@unittest.skipUnless(HAS_QT, "PyQt6 krävs för UI-test av 'Har ej VIN'-kryssrutan")
class NoVinCheckboxUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_no_vin_checkbox_for_english_recipients_and_log_tabs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            settings_path = root / "settings.json"
            tpl_dir = root / "templates"
            tpl_dir.mkdir(parents=True)
            # Template intentionally WITHOUT explicit ::vin:: token to verify VIN + checkbox still appear for [EN]!
            tpl_path = tpl_dir / "en_test.docx"
            create_template(
                tpl_path,
                "Förfrågan ::modell:: ::reg::",
                "Hej!\nBil: ::modell::\nRegnr: ::reg::\nMed vänlig hälsning\nKundtjänst",
                overwrite=True,
            )

            settings = Settings(settings_path)
            settings.set("templates_dir", str(tpl_dir))
            settings.set("default_bcc", [])
            settings.set("archive_bcc_Confirmation", False)
            bus = EventBus()
            rec = RecoveryManager(root / "recovery.json")
            win = MainWindow(settings, bus, rec)
            try:
                idx = win._tpl_combo.findText("en_test.docx")
                if idx >= 0:
                    win._tpl_combo.setCurrentIndex(idx)
                self.app.processEvents()

                # 1. With only [SV] recipient, VIN is not required and hidden
                win._add_recipient(win._to_list, "svensk@example.com", "sv")
                self.app.processEvents()
                self.assertFalse(win._has_en_recipient())
                self.assertFalse(vin_required_missing(win._get_ph(), False, win._is_no_vin_checked()))

                # 2. Add [EN] recipient -> VIN field + 'Har ej VIN' checkbox appear!
                win._add_recipient(win._to_list, "english@example.com", "en")
                self.app.processEvents()
                self.assertTrue(win._has_en_recipient())
                self.assertIsNotNone(win._no_vin_cb)
                self.assertIsInstance(win._no_vin_cb, QCheckBox)
                self.assertEqual(win._no_vin_cb.objectName(), "noVinCheckbox")
                self.assertEqual(win._no_vin_cb.text(), "Har ej VIN")
                self.assertFalse(win._no_vin_cb.isChecked())

                vin_widget = next(
                    w for k, w in win._ph_inputs.items() if k.lower() == "vin"
                )
                self.assertIsInstance(vin_widget, QLineEdit)
                self.assertTrue(vin_widget.isEnabled())

                # Empty VIN + unchecked 'Har ej VIN' -> missing VIN blocks send
                params_blocked = win._gather_send_params()
                self.assertTrue(
                    vin_required_missing(
                        params_blocked["replacements"],
                        params_blocked["include_english"],
                        params_blocked["no_vin"],
                    )
                )

                # 3. Check 'Har ej VIN' -> VIN input disabled, send allowed, 'vin' not missing!
                win._no_vin_cb.setChecked(True)
                self.app.processEvents()
                self.assertTrue(win._is_no_vin_checked())
                self.assertFalse(vin_widget.isEnabled())

                params_ok = win._gather_send_params()
                self.assertTrue(params_ok["no_vin"])
                self.assertNotIn("vin", [k.lower() for k in params_ok["placeholders_missing"]])
                self.assertFalse(
                    vin_required_missing(
                        params_ok["replacements"],
                        params_ok["include_english"],
                        params_ok["no_vin"],
                    )
                )

                # Draft snapshot preserves no_vin=True
                snap = win._draft_snapshot()
                self.assertIs(snap["no_vin"], True)

                # Reset after send unchecks 'Har ej VIN' and re-enables VIN field
                win._reset_form_after_send()
                self.app.processEvents()
                self.assertFalse(win._is_no_vin_checked())

                # Verify Loggar tab mode buttons exist and switch cleanly
                self.assertTrue(hasattr(win, "_log_mode_today_btn"))
                self.assertTrue(hasattr(win, "_log_mode_errors_btn"))
                win._set_log_view_mode("errors")
                self.assertEqual(win._log_view_mode, "errors")
                win._set_log_view_mode("today")
                self.assertEqual(win._log_view_mode, "today")
            finally:
                win.close()


if __name__ == "__main__":
    unittest.main()
