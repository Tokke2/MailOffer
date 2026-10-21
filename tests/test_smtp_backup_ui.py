#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offscreen-tester: SMTP-leverantörsförval, DNS-format och backup-UI."""

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


@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestSmtpBackupUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])
        try:
            from ui.main_window import MainWindow  # noqa: F401
        except Exception as exc:
            raise unittest.SkipTest(f"MainWindow otillgänglig: {exc}")

    def _make_window(self, **overrides):
        from core.event_bus import EventBus
        from core.recovery_manager import RecoveryManager
        from core.settings_manager import SettingsManager
        from ui.main_window import MainWindow

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        base = Path(tmp.name)
        (base / "Mallar").mkdir(exist_ok=True)
        (base / "Mallar" / "Test.txt").write_text("Hej", encoding="utf-8")
        with mock.patch.dict(os.environ, {"EMAILAPP_PORTABLE": "1"}):
            settings = SettingsManager(base)
        values = {
            "auto_update_check": False,
            "language": "sv",
            "close_to_tray": False,
            "sender_email": "anna@gmail.com",
            "smtp_server": "",
        }
        values.update(overrides)
        settings.update_from_dict(values)
        bus = EventBus()
        win = MainWindow(settings, bus, RecoveryManager(bus))
        self.addCleanup(win.close)
        return win, settings, base

    def test_provider_selection_fills_smtp_fields(self):
        win, _settings, _base = self._make_window()
        combo = win._smtp_provider_combo
        index = combo.findData("gmail")
        self.assertGreaterEqual(index, 0)
        combo.setCurrentIndex(index)
        QApplication.processEvents()
        self.assertEqual(
            win._settings_widgets["smtp_server"].text(), "smtp.gmail.com"
        )
        self.assertEqual(win._settings_widgets["smtp_port"].text(), "587")
        self.assertFalse(win._settings_widgets["use_ssl"].isChecked())
        self.assertEqual(
            win._settings_widgets["username"].text(), "anna@gmail.com"
        )
        self.assertTrue(win._smtp_provider_help.text())
        self.assertFalse(win._btn_app_password.isHidden())

    def test_autodetect_from_sender_email(self):
        win, _settings, _base = self._make_window()
        win._settings_widgets["smtp_server"].setText("")
        win._settings_widgets["sender_email"].setText("anna@icloud.com")
        win._autodetect_smtp_provider()
        QApplication.processEvents()
        self.assertEqual(win._smtp_provider_combo.currentData(), "icloud")
        self.assertEqual(
            win._settings_widgets["smtp_server"].text(), "smtp.mail.me.com"
        )

    def test_sync_combo_from_saved_server(self):
        win, _settings, _base = self._make_window(
            smtp_server="smtp.mail.yahoo.com", smtp_port=465, use_ssl=True
        )
        win._reload_settings_form()
        self.assertEqual(win._smtp_provider_combo.currentData(), "yahoo")

    def test_dns_report_formatting(self):
        from core.dns_checks import DnsReport

        win, _settings, _base = self._make_window()
        report = DnsReport(
            domain="exempel.se",
            spf_status="ok",
            dmarc_status="ok",
            dmarc_policy="reject",
            dkim_status="missing",
        )
        text = win._format_dns_report(report)
        self.assertIn("exempel.se", text)
        self.assertIn("reject", text)
        self.assertIn("SPF", text)
        self.assertTrue(hasattr(win, "_btn_dns_check"))

    def test_create_backup_via_ui_handler(self):
        import ui.main_window as main_window
        from core.i18n import tr

        win, _settings, base = self._make_window()
        texts = [b.text() for b in win.findChildren(QPushButton)]
        self.assertIn(tr("backup.create_btn"), texts)
        self.assertIn(tr("backup.restore_btn"), texts)

        dest = base / "min-backup.zip"
        with mock.patch.object(
            main_window.QFileDialog,
            "getSaveFileName",
            return_value=(str(dest), ""),
        ), mock.patch.object(
            main_window.QMessageBox, "information", return_value=None
        ):
            win._create_full_backup_ui()
        self.assertTrue(dest.is_file())

        from core.user_backup import inspect_backup

        manifest = inspect_backup(dest)
        self.assertFalse(manifest["passwords_included"])
        self.assertIn("Mallar", manifest["sections"])


if __name__ == "__main__":
    unittest.main()
