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

        # Tomma inställningar -> inbyggda standardlänkar (ägarens riktiga)
        empty = DonateDialog(None, donation_url="")
        self.assertEqual(empty._url, "https://ko-fi.com/tokke2")
        self.assertEqual(empty._paypal_url, "https://paypal.me/Rickard3dPrint")
        self.assertEqual(empty._swish_payload, "")  # inget nummer inställt
        empty.close()

    def test_dialog_paypal_and_swish(self) -> None:
        from ui.donate import DonateDialog

        dialog = DonateDialog(
            None, paypal_url="mittnamn", swish_number="070-123 45 67"
        )
        self.assertEqual(dialog._paypal_url, "https://paypal.me/mittnamn")
        self.assertEqual(dialog._swish_payload, "C0701234567;;E-postofferten;6")
        dialog._copy_swish()
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            self.assertEqual(clipboard.text(), "0701234567")
        try:
            import qrcode  # noqa: F401

            self.assertIsNotNone(dialog._qr_pixmap)
            self.assertFalse(dialog._qr_pixmap.isNull())
        except ImportError:
            self.assertIsNone(dialog._qr_pixmap)  # fail-soft utan QR-paket
        dialog.close()




@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestUpdateDeferralUi(unittest.TestCase):
    """Autouppdatering i tray-läge: notis direkt, fråga när fönstret öppnas."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])
        try:
            from ui.main_window import MainWindow  # noqa: F401
        except Exception as exc:  # saknade deps i lätt miljö
            raise unittest.SkipTest(f"MainWindow otillgänglig: {exc}")

    def _make_window(self):
        import tempfile

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

    @staticmethod
    def _info():
        from core.github_update import UpdateInfo

        return UpdateInfo(
            available=True,
            latest_version="9.9.9",
            tag="v9.9.9",
            download_url="https://example.invalid/x.zip",
        )

    def test_tray_defers_prompt_until_shown(self) -> None:
        win = self._make_window()
        self.assertFalse(win.isVisible())
        prompted: list = []
        win._prompt_update_install = lambda info: prompted.append(info)  # type: ignore[method-assign]
        notices: list = []

        class FakeTray:
            def show_notification(self, title, message):
                notices.append((title, message))

        win._tray_ref = FakeTray()
        info = self._info()
        win._update_check_manual = False
        win._on_update_checked(info)
        self.assertEqual(prompted, [])                 # ingen modal i tray-läge
        self.assertEqual(len(notices), 1)              # tray-notis i stället
        self.assertIs(win._pending_update_info, info)  # frågan är uppskjuten
        win.show()
        QApplication.processEvents()
        win._maybe_prompt_pending_update()  # samma anrop som timern i show()
        self.assertEqual(prompted, [info])

    def test_same_version_check_baselines_fingerprint(self) -> None:
        from core.github_update import UpdateInfo
        from core.version import __version__

        win = self._make_window()
        info = UpdateInfo(
            available=False,
            latest_version=__version__,
            tag="v" + __version__,
            download_url="https://example.invalid/x.zip",
            fingerprint="fp-aktuell",
        )
        win._update_check_manual = False
        win._on_update_checked(info)
        self.assertEqual(
            win.settings.get("installed_release_fingerprint"), "fp-aktuell"
        )

    def test_same_version_files_changed_flow(self) -> None:
        from core.github_update import UpdateInfo
        from core.version import __version__

        win = self._make_window()
        win.settings.set("installed_release_fingerprint", "fp-gammal")
        prompted: list = []
        win._prompt_update_install = lambda info: prompted.append(info)  # type: ignore[method-assign]
        info = UpdateInfo(
            available=True,
            latest_version=__version__,
            tag="v" + __version__,
            download_url="https://example.invalid/x.zip",
            fingerprint="fp-ny",
            same_version_files_changed=True,
        )
        win._update_check_manual = True
        win._on_update_checked(info)
        self.assertEqual(prompted, [info])
        # Fingeravtrycket skrivs INTE över förrän uppdateringen installerats
        self.assertEqual(
            win.settings.get("installed_release_fingerprint"), "fp-gammal"
        )

        import ui.main_window as main_mod

        original = main_mod.QMessageBox.question
        main_mod.QMessageBox.question = staticmethod(
            lambda *a, **k: main_mod.QMessageBox.StandardButton.No
        )
        try:
            win._on_update_installed(
                {"copied": ["main.pyw"], "errors": [], "fingerprint": "fp-ny"}
            )
        finally:
            main_mod.QMessageBox.question = original
        self.assertEqual(
            win.settings.get("installed_release_fingerprint"), "fp-ny"
        )

    def test_manual_check_prompts_immediately(self) -> None:
        win = self._make_window()
        prompted: list = []
        win._prompt_update_install = lambda info: prompted.append(info)  # type: ignore[method-assign]
        info = self._info()
        win._update_check_manual = True
        win._on_update_checked(info)
        self.assertEqual(prompted, [info])


if __name__ == "__main__":
    unittest.main()
