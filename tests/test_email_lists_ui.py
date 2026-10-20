#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offscreen-tester för e-postlistor i Kontakter och Mottagare (PyQt6)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from PyQt6.QtWidgets import QApplication, QPushButton

    HAS_QT = True
except Exception:  # pragma: no cover - beror på miljön
    HAS_QT = False


@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestContactStoreEmailLists(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])
        try:
            from script.contacts_ui import ContactStore  # noqa: F401
        except Exception as exc:
            raise unittest.SkipTest(f"ContactStore otillgänglig: {exc}")

    def test_import_text_merges_categories_and_preserves_existing(self):
        from script.contacts_ui import ContactStore

        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "adresslistor" / "contacts.json"
            store = ContactStore(path)
            store.upsert(
                "anna@example.se",
                name="Befintligt namn",
                language="en",
                categories=["Gammal lista"],
            )

            stats = store.import_email_list_text(
                "anna@example.se; bob@example.com\ninte-en-adress",
                category="Bilglas",
                default_language="sv",
            )
            self.assertEqual(stats["added"], 1)
            self.assertEqual(stats["updated"], 1)
            self.assertEqual(stats["invalid"], 1)

            anna = store.get("anna@example.se")
            bob = store.get("bob@example.com")
            self.assertIsNotNone(anna)
            self.assertIsNotNone(bob)
            self.assertEqual(anna.name, "Befintligt namn")
            self.assertEqual(anna.language, "en")
            self.assertIn("Gammal lista", anna.categories)
            self.assertIn("Bilglas", anna.categories)
            self.assertIn("Bilglas", bob.categories)
            self.assertTrue(path.exists())

            again = store.import_email_list_text(
                "anna@example.se; bob@example.com\ninte-en-adress",
                category="Bilglas",
                default_language="sv",
            )
            self.assertEqual(again["added"], 0)
            self.assertEqual(again["updated"], 0)
            self.assertEqual(again["duplicates"], 2)
            self.assertEqual(again["invalid"], 1)

    def test_import_plain_text_and_swedish_csv_files(self):
        from script.contacts_ui import ContactStore

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            store = ContactStore(base / "contacts.json")
            txt = base / "lista.txt"
            txt.write_text(
                "Anna <anna@example.se>\nbob@example.com\n",
                encoding="utf-8",
            )
            stats = store.import_email_list(str(txt), category="Lista A")
            self.assertEqual(stats["added"], 2)

            csv_path = base / "svensk.csv"
            csv_path.write_text(
                "E-post;Namn;Företag;Språk;Kategori\n"
                "carin@example.se;Carin;Exempel AB;en;VIP\n",
                encoding="utf-8",
            )
            stats = store.import_email_list(str(csv_path), category="Lista B")
            self.assertEqual(stats["added"], 1)
            carin = store.get("carin@example.se")
            self.assertIsNotNone(carin)
            self.assertEqual(carin.company, "Exempel AB")
            self.assertEqual(carin.language, "en")
            self.assertIn("VIP", carin.categories)
            self.assertIn("Lista B", carin.categories)

    def test_paste_dialog_values(self):
        from PyQt6.QtWidgets import QDialog

        from script.contacts_ui import _PasteEmailListDialog

        dialog = _PasteEmailListDialog(None)
        dialog._list_name_edit.setText("Bilglas")
        dialog._language_combo.setCurrentIndex(
            dialog._language_combo.findData("en")
        )
        dialog._text_edit.setPlainText("anna@example.se\nbob@example.com")
        self.assertEqual(dialog.list_name(), "Bilglas")
        self.assertEqual(dialog.language(), "en")
        dialog._on_accept()
        self.assertEqual(dialog.result(), QDialog.DialogCode.Accepted)
        dialog.close()


@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestMainWindowRecipientLists(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])
        try:
            from ui.main_window import MainWindow  # noqa: F401
        except Exception as exc:
            raise unittest.SkipTest(f"MainWindow otillgänglig: {exc}")

    def _make_window(self):
        from core.event_bus import EventBus
        from core.recovery_manager import RecoveryManager
        from core.settings_manager import SettingsManager
        from ui.main_window import MainWindow

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        settings = SettingsManager(Path(tmp.name))
        settings.set("auto_update_check", False)
        settings.set("ui_language", "sv")
        settings.set("close_to_tray", False)
        bus = EventBus()
        win = MainWindow(settings, bus, RecoveryManager(bus))
        self.addCleanup(win.close)
        return win

    def test_paste_many_addresses_into_single_input(self):
        win = self._make_window()
        win._to_input.setText(
            "Anna <anna@example.se>; bob@example.com, anna@example.se"
        )
        added = win._add_recipient("to")
        self.assertEqual(added, 2)
        self.assertEqual(
            win._list_items(win._to_list),
            ["anna@example.se", "bob@example.com"],
        )
        self.assertEqual(win._to_input.text(), "")

    def test_parsed_list_languages_and_stats(self):
        from core.email_lists import parse_email_list_text

        win = self._make_window()
        parsed = parse_email_list_text(
            "E-post;Språk\n"
            "anna@example.se;en\n"
            "bob@example.com;sv\n"
            "anna@example.se;en\n"
            "skräp\n"
        )
        stats = win._add_parsed_recipient_list("bcc", parsed)
        self.assertEqual(stats["added"], 2)
        self.assertEqual(stats["duplicates"], 1)
        self.assertEqual(stats["invalid"], 1)
        self.assertEqual(
            win._list_langs(win._bcc_list),
            {"anna@example.se": "en", "bob@example.com": "sv"},
        )

    def test_list_buttons_are_present_for_to_and_bcc(self):
        from core.i18n import tr

        win = self._make_window()
        texts = [button.text() for button in win.findChildren(QPushButton)]
        self.assertGreaterEqual(texts.count(tr("emaillist.paste_btn")), 2)
        self.assertGreaterEqual(texts.count(tr("emaillist.import_btn")), 2)


if __name__ == "__main__":
    unittest.main()
