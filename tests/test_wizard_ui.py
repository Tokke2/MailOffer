#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offscreen-tester för mall-wizarden + donationsdialogen (PyQt6).

Hopppas över automatiskt om PyQt6 inte kan importeras (t.ex. i ren
CI utan Qt). På Windows/utvecklingsmaskiner körs de headless via
QT_QPA_PLATFORM=offscreen.
"""
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
    from PyQt6.QtWidgets import QApplication

    HAS_QT = True
except Exception:  # pragma: no cover - beror på miljön
    HAS_QT = False


@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestTemplateWizardUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])

    def _make_wizard(self, tmp: Path, **kwargs):
        from ui.template_wizard import TemplateWizard

        wizard = TemplateWizard(
            None, templates_dir=tmp / "Mallar",
            translate_func=lambda text: text + " [translated]",
            **kwargs,
        )
        wizard.show()
        self.app.processEvents()
        return wizard

    def test_create_txt_template_end_to_end(self) -> None:
        from script.templates import list_placeholders, parse_subject_and_body

        with tempfile.TemporaryDirectory() as td:
            wizard = self._make_wizard(Path(td))
            wizard._name_edit.setText("UI-testmall")
            self.assertEqual(wizard._filename(), "UI-testmall.txt")
            self.assertTrue(wizard.validateCurrentPage())
            wizard.next()  # SV-sidan – exemplet laddas
            self.app.processEvents()
            self.assertIn("::ruta::", wizard._subject_edit.text())
            self.assertTrue(wizard.validateCurrentPage())
            wizard.next()  # EN-sidan
            self.app.processEvents()
            self.assertTrue(wizard._include_en.isChecked())
            self.assertTrue(wizard.validateCurrentPage())
            wizard.next()  # Förhandsgranskning
            self.app.processEvents()
            self.assertIn("Vindruta", wizard._preview_sv.toPlainText())
            self.assertIn("YV1UZ", wizard._preview_en.toPlainText())
            wizard.next()  # Spara
            self.app.processEvents()
            wizard.accept()
            self.assertIsNotNone(wizard.created_path)
            self.assertTrue(wizard.created_path.exists())
            self.assertIn("vin", list_placeholders(wizard.created_path))
            _s, sv = parse_subject_and_body(
                wizard.created_path, {"modell": "V70"}, keep_unknown=True
            )
            self.assertNotIn("VIN", sv)
            _s2, en = parse_subject_and_body(
                wizard.created_path, {"modell": "V70"},
                include_english=True, keep_unknown=True,
            )
            self.assertIn("VIN: ::vin::", en)
            wizard.close()

    def test_validation_blocks_empty_name(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wizard = self._make_wizard(Path(td))
            wizard._name_edit.setText("???")  # saneras till tomt
            # QMessageBox.warning skulle blocka – stubba den i testet
            import ui.template_wizard as wiz_mod

            original = wiz_mod.QMessageBox.warning
            wiz_mod.QMessageBox.warning = staticmethod(lambda *a, **k: None)
            try:
                self.assertFalse(wizard.validateCurrentPage())
            finally:
                wiz_mod.QMessageBox.warning = original
            wizard.close()

    def test_blank_start_gives_empty_fields(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            wizard = self._make_wizard(Path(td))
            wizard._radio_blank.setChecked(True)
            wizard._name_edit.setText("Tom")
            wizard.next()
            self.app.processEvents()
            self.assertEqual(wizard._subject_edit.text(), "")
            self.assertEqual(wizard._sv_body_edit.toPlainText(), "")
            wizard.close()


@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestDonateDialogUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])

    def test_dialog_with_and_without_url(self) -> None:
        from ui.donate import DonateDialog

        dialog = DonateDialog(None, donation_url="ko-fi.com/exempel")
        self.assertEqual(dialog._url, "https://ko-fi.com/exempel")
        dialog._copy_url()
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            self.assertEqual(clipboard.text(), "https://ko-fi.com/exempel")
        dialog.close()

        empty = DonateDialog(None, donation_url="")
        self.assertEqual(empty._url, "")
        empty.close()


if __name__ == "__main__":
    unittest.main()
