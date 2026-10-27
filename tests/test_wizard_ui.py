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
from unittest import mock
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
    """Tyst autosökning, manuell installation och säker tyst omstart."""

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
        self.assertEqual(len(notices), 0)              # ingen tray-notis
        self.assertIs(win._pending_update_info, info)  # information finns kvar för manuell kontroll
        win.show()
        QApplication.processEvents()
        win._maybe_prompt_pending_update()  # samma anrop som timern i show()
        self.assertEqual(prompted, [])

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

        with mock.patch.object(win, "_finish_update_restart") as restart, mock.patch.object(main_mod.QMessageBox, "question", side_effect=AssertionError("No restart question")):
            win._on_update_installed(
                {"copied": ["main.pyw"], "errors": [], "fingerprint": "fp-ny"}
            )
            restart.assert_called_once()
        self.assertEqual(
            win.settings.get("installed_release_fingerprint"), "fp-ny"
        )

    def test_cache_cleanup_timer_and_manual_smart_filter(self):
        win = self._make_window()
        self.assertTrue(win._cache_cleanup_timer.isActive())
        self.assertEqual(win._cache_cleanup_timer.interval(), 60_000)
        with mock.patch("core.smart_cache.run_due_cleanup", return_value={"removed": 1, "bytes": 20, "errors": 0}) as clean:
            win._run_cache_cleanup(manual=True)
            clean.assert_called_once_with(win._base_dir(), win.settings, force=True)

    def test_cache_cleanup_waits_for_sending_and_install(self):
        win = self._make_window()
        with mock.patch("core.smart_cache.run_due_cleanup") as clean:
            worker = mock.Mock()
            worker.isRunning.return_value = True
            win._worker = worker
            win._run_cache_cleanup()
            clean.assert_not_called()
            win._worker = None
            win._update_install_active = True
            win._run_cache_cleanup()
            clean.assert_not_called()
            win._update_install_active = False

    def test_periodic_timer_and_quiet_visible_check(self):
        win = self._make_window()
        self.assertTrue(win._update_schedule.isActive())
        self.assertEqual(win._update_schedule.interval(), 60_000)
        win.show()
        with mock.patch.object(win, "_prompt_update_install") as prompt, mock.patch.object(win, "_notify_update_via_tray") as notify:
            win._update_check_manual = False
            win._on_update_checked(self._info())
            win._maybe_prompt_pending_update()
            prompt.assert_not_called()
            notify.assert_not_called()

    def test_silent_restart_saves_and_restores_compose_state(self):
        win = self._make_window()
        win._free_edit.setPlainText("Unsent text")
        win._editor.setPlainText("Unsent body")
        win._add_recipient("to", email="draft@example.com", show_warning=False, lang="en")
        path = win._update_session_path()
        self.addCleanup(lambda: path.unlink(missing_ok=True))
        with mock.patch.dict(os.environ, {}, clear=False), mock.patch.object(win, "_restart_app") as restart:
            win._finish_update_restart()
            restart.assert_called_once()
        self.assertNotIn("password", path.read_text())
        win._free_edit.clear()
        win._to_list.clear()
        win._restore_update_session()
        self.assertEqual(win._free_edit.toPlainText(), "Unsent text")
        self.assertIn("draft@example.com", win._list_items(win._to_list))
        self.assertFalse(path.exists())

    def test_restart_waits_for_active_send(self):
        win = self._make_window()
        worker = mock.Mock()
        worker.isRunning.return_value = True
        win._worker = worker
        with mock.patch("ui.main_window.QTimer.singleShot") as later, mock.patch.object(win, "_restart_app") as restart:
            win._finish_update_restart()
            restart.assert_not_called()
            later.assert_called_once()
        win._worker = None

    def test_restart_aborts_if_session_cannot_be_saved(self):
        win = self._make_window()
        with mock.patch("core.update_session.save_session", side_effect=OSError("disk full")), mock.patch.object(win, "_restart_app") as restart:
            win._finish_update_restart()
            restart.assert_not_called()

    def test_partial_update_does_not_restart(self):
        win = self._make_window()
        import ui.main_window as main_mod
        with mock.patch.object(main_mod.QMessageBox, "warning"), mock.patch.object(win, "_finish_update_restart") as restart:
            win._on_update_installed({"copied": ["a.py"], "errors": ["locked file"], "fingerprint": "not-installed"})
            restart.assert_not_called()
        self.assertNotEqual(win.settings.get("installed_release_fingerprint"), "not-installed")

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
