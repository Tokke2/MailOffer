#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offscreen-tester för avsändarprofiler + testläge i huvudfönstret."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from PyQt6.QtWidgets import QApplication, QPushButton

    HAS_QT = True
except Exception:  # pragma: no cover
    HAS_QT = False


def _profile_b() -> dict:
    return {
        "name": "Företag B",
        "smtp_server": "smtp.b.se",
        "smtp_port": 465,
        "sender_email": "b@example.com",
        "sender_name": "Företag B",
        "username": "b@example.com",
        "password": "hemligt-b",
        "reply_to": "svar-b@example.com",
        "own_email": "egen-b@example.com",
        "archive_copy_email": "arkiv-b@example.com",
        "use_ssl": True,
    }


@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestSenderProfilesUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])
        try:
            from ui.main_window import MainWindow  # noqa: F401
        except Exception as exc:
            raise unittest.SkipTest(f"MainWindow otillgänglig: {exc}")

    def _make_settings(self, tmp: Path):
        from core.settings_manager import SettingsManager

        with mock.patch.dict(os.environ, {"EMAILAPP_PORTABLE": "1"}):
            settings = SettingsManager(tmp)
        settings.update_from_dict(
            {
                "auto_update_check": False,
                "language": "sv",
                "ui_language": "sv",
                "close_to_tray": False,
                "smtp_server": "smtp.a.se",
                "smtp_port": 587,
                "sender_email": "a@example.se",
                "sender_name": "Företag A",
                "username": "a@example.se",
                "password": "hemligt-a",
                "reply_to": "svar-a@example.se",
                "own_email": "egen-a@example.se",
                "archive_copy_email": "arkiv-a@example.se",
                "use_ssl": False,
            }
        )
        profile_b = settings.upsert_sender_profile(
            _profile_b(), make_active=False, save=True
        )
        return settings, str(profile_b["id"])

    def _make_window(self):
        from core.event_bus import EventBus
        from core.recovery_manager import RecoveryManager
        from ui.main_window import MainWindow

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        settings, profile_b_id = self._make_settings(Path(tmp.name))
        bus = EventBus()
        win = MainWindow(settings, bus, RecoveryManager(bus))
        self.addCleanup(win.close)
        return win, settings, profile_b_id

    def test_signature_fields_follow_profile(self):
        win, settings, profile_b_id = self._make_window()
        profile = settings.get_sender_profile(profile_b_id) if hasattr(settings, "get_sender_profile") else next(p for p in settings.get_sender_profiles() if p["id"] == profile_b_id)
        profile.update(signature_text="Hälsningar\nFöretag B", signature_contact="Telefon 123", signature_logo="")
        settings.upsert_sender_profile(profile)
        win._refresh_sender_profile_combos()
        win._settings_profile_combo.setCurrentIndex(win._settings_profile_combo.findData(profile_b_id))
        win._apply_sender_profile_to_settings_form(profile)
        self.assertEqual(win._settings_widgets["signature_text"].toPlainText(), "Hälsningar\nFöretag B")
        self.assertEqual(win._sender_profile_from_form()["signature_contact"], "Telefon 123")
        self.assertIn("auto_backup_keep", win._settings_widgets)

    def test_send_combo_gather_uses_selected_profile(self):
        from core.i18n import tr

        win, _settings, profile_b_id = self._make_window()
        texts = [button.text() for button in win.findChildren(QPushButton)]
        self.assertIn(tr("send.preflight_btn"), texts)
        self.assertIn(tr("send.test_btn"), texts)
        self.assertGreaterEqual(win._send_profile_combo.count(), 2)

        index = win._send_profile_combo.findData(profile_b_id)
        self.assertGreaterEqual(index, 0)
        win._send_profile_combo.setCurrentIndex(index)
        QApplication.processEvents()

        params = win._gather_send_params()
        self.assertEqual(params["sender_profile_id"], profile_b_id)
        self.assertEqual(params["sender_profile_name"], "Företag B")
        self.assertEqual(params["sender_email"], "b@example.com")
        self.assertIn("arkiv-b@example.com", params["default_bcc"])
        self.assertIn("b@example.com", win._send_summary.text())

    def test_settings_combo_loads_and_saves_profile_fields(self):
        win, settings, profile_b_id = self._make_window()
        settings.sync_autostart = lambda: True  # type: ignore[method-assign]

        index = win._settings_profile_combo.findData(profile_b_id)
        self.assertGreaterEqual(index, 0)
        win._settings_profile_combo.setCurrentIndex(index)
        QApplication.processEvents()
        self.assertEqual(
            win._settings_widgets["sender_email"].text(), "b@example.com"
        )

        win._settings_widgets["sender_email"].setText("ny-b@example.com")
        win._save_settings_form()
        saved = settings.get_sender_profile(profile_b_id)
        self.assertEqual(saved["sender_email"], "ny-b@example.com")
        self.assertEqual(settings.get_active_sender_profile_id(), profile_b_id)
        self.assertEqual(settings.get("sender_email"), "ny-b@example.com")

    def test_make_test_params_isolates_recipients(self):
        win, _settings, profile_b_id = self._make_window()
        index = win._send_profile_combo.findData(profile_b_id)
        win._send_profile_combo.setCurrentIndex(index)
        win._add_recipients(
            "bcc", ["kund1@example.se", "kund2@example.com"]
        )
        params = win._gather_send_params()
        test_params = win._make_test_params(params, "test@example.se")

        self.assertTrue(test_params["test_mode"])
        self.assertEqual(test_params["recipients_to"], ["test@example.se"])
        self.assertEqual(test_params["recipients_bcc"], [])
        self.assertEqual(test_params["default_bcc"], [])
        self.assertFalse(test_params["request_receipts"])
        report = win._preflight_report(test_params)
        self.assertEqual(report.total, 1)
        self.assertEqual(report.to_final, ["test@example.se"])


@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestSendWorkerProfile(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])

    def test_worker_uses_profile_and_test_mode_guards(self):
        import ui.main_window as main_window
        from core.settings_manager import SettingsManager

        with tempfile.TemporaryDirectory() as td:
            with mock.patch.dict(os.environ, {"EMAILAPP_PORTABLE": "1"}):
                settings = SettingsManager(Path(td))
            settings.update_from_dict(
                {
                    "smtp_server": "smtp.global.se",
                    "sender_email": "global@example.se",
                    "username": "global@example.se",
                    "password": "global",
                    "own_email": "global-egen@example.se",
                    "archive_copy_email": "global-arkiv@example.se",
                    "default_bcc": ["global-bcc@example.se"],
                }
            )
            profile = _profile_b()
            captured = {}

            def fake_send(**kwargs):
                captured.update(kwargs)
                return object()

            base_params = {
                "sender_profile": profile,
                "recipients_to": ["test@example.se"],
                "recipients_bcc": [],
                "recipients_to_lang": {"test@example.se": "sv"},
                "recipients_bcc_lang": {},
                "template_path": "",
                "replacements": {},
                "include_english": False,
                "attachments": [],
                "free_text": "",
                "default_bcc": ["ska-inte-användas@example.se"],
                "request_receipts": True,
                "test_mode": True,
            }
            with mock.patch.object(main_window, "send_email", fake_send):
                worker = main_window.SendWorker(settings, dict(base_params))
                worker.run()

            self.assertEqual(captured["smtp_server"], "smtp.b.se")
            self.assertEqual(captured["sender_email"], "b@example.com")
            self.assertEqual(captured["username"], "b@example.com")
            self.assertEqual(captured["password"], "hemligt-b")
            self.assertEqual(captured["reply_to"], "svar-b@example.com")
            self.assertTrue(captured["use_ssl"])
            self.assertEqual(captured["own_email"], "")
            self.assertEqual(captured["default_bcc"], [])
            self.assertFalse(captured["request_receipts"])
            self.assertEqual(
                captured["extra_headers"], {"X-Epostofferten-Test": "1"}
            )


if __name__ == "__main__":
    unittest.main()
