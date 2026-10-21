#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offscreen-tester för mallredigering, mallversioner och mallpaket."""

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
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QMessageBox, QPushButton

    HAS_QT = True
except Exception:  # pragma: no cover
    HAS_QT = False


def _seed_template(mallar: Path) -> Path:
    from script.templates import build_template_body, create_template

    mallar.mkdir(parents=True, exist_ok=True)
    path = mallar / "Befintlig mall.txt"
    create_template(
        path,
        "Original ::modell::",
        build_template_body(
            "Originaltext för ::modell::",
            "Original text for ::modell::",
        ),
    )
    return path


@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestTemplateEditUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])
        try:
            from ui.template_wizard import TemplateWizard  # noqa: F401
        except Exception as exc:
            raise unittest.SkipTest(f"TemplateWizard otillgänglig: {exc}")

    def test_edit_existing_template_saves_version(self):
        from script.template_versions import list_template_versions
        from script.templates import parse_subject_and_body
        from ui.template_wizard import TemplateWizard

        with tempfile.TemporaryDirectory() as td:
            mallar = Path(td) / "Mallar"
            path = _seed_template(mallar)
            wizard = TemplateWizard(
                None,
                templates_dir=mallar,
                existing_names=[path.name],
                edit_path=path,
            )
            self.addCleanup(wizard.close)
            wizard.show()
            QApplication.processEvents()

            self.assertTrue(wizard.is_editing)
            self.assertFalse(wizard._name_edit.isEnabled())
            self.assertEqual(wizard._filename(), path.name)

            wizard.next()  # Svensk text laddas
            QApplication.processEvents()
            self.assertEqual(wizard._subject_edit.text(), "Original ::modell::")
            self.assertIn("Originaltext", wizard._sv_body_edit.toPlainText())
            wizard._subject_edit.setText("Uppdaterad ::modell::")
            wizard._sv_body_edit.setPlainText("Uppdaterad text ::modell::")

            wizard.next()
            QApplication.processEvents()
            self.assertTrue(wizard._include_en.isChecked())
            wizard.next()
            QApplication.processEvents()
            wizard.next()
            QApplication.processEvents()
            wizard.accept()

            self.assertTrue(wizard.edited_existing)
            self.assertEqual(wizard.saved_path, path)
            subject, body = parse_subject_and_body(
                path, {"modell": "Volvo"}, keep_unknown=True
            )
            self.assertEqual(subject, "Uppdaterad Volvo")
            self.assertIn("Uppdaterad text", body)
            versions = list_template_versions(path)
            self.assertEqual(len(versions), 1)
            self.assertIn(
                "Originaltext",
                versions[0].path.read_text(encoding="utf-8"),
            )

    def test_pack_start_loads_ready_template(self):
        from ui.template_wizard import TemplateWizard

        with tempfile.TemporaryDirectory() as td:
            mallar = Path(td) / "Mallar"
            mallar.mkdir()
            wizard = TemplateWizard(None, templates_dir=mallar)
            self.addCleanup(wizard.close)
            wizard.show()
            QApplication.processEvents()

            index = wizard._pack_combo.findData("seasonal_campaign")
            self.assertGreaterEqual(index, 0)
            wizard._pack_combo.setCurrentIndex(index)
            wizard._radio_pack.setChecked(True)
            QApplication.processEvents()
            self.assertIn("Säsongskampanj", wizard._name_edit.text())
            self.assertTrue(wizard._filename().endswith(".txt"))

            wizard.next()
            QApplication.processEvents()
            self.assertIn("Säsongskampanj", wizard._subject_edit.text())
            self.assertIn("::price::", wizard._sv_body_edit.toPlainText())

    def test_versions_dialog_restores_selected_version(self):
        import ui.template_wizard as wizard_module
        from script.template_versions import snapshot_template_version
        from ui.template_wizard import TemplateVersionsDialog

        with tempfile.TemporaryDirectory() as td:
            mallar = Path(td) / "Mallar"
            path = _seed_template(mallar)
            snapshot_template_version(path)
            path.write_text(
                "ÄMNE: Ny\n\nINNEHÅLL:\nNytt innehåll", encoding="utf-8"
            )

            dialog = TemplateVersionsDialog(None, template_path=path)
            self.addCleanup(dialog.close)
            dialog.show()
            QApplication.processEvents()
            self.assertEqual(dialog._list.count(), 1)
            self.assertIn("Originaltext", dialog._preview.toPlainText())

            with mock.patch.object(
                wizard_module.QMessageBox,
                "question",
                return_value=QMessageBox.StandardButton.Yes,
            ):
                dialog._restore_selected()
            self.assertTrue(dialog.restored)
            self.assertIn(
                "Originaltext", path.read_text(encoding="utf-8")
            )

    def test_pack_dialog_installs_selected_templates(self):
        from script.template_packs import iter_template_pack_items
        from ui.template_wizard import TemplatePackDialog

        with tempfile.TemporaryDirectory() as td:
            mallar = Path(td) / "Mallar"
            dialog = TemplatePackDialog(None, templates_dir=mallar)
            self.addCleanup(dialog.close)
            dialog.show()
            QApplication.processEvents()
            expected = len(list(iter_template_pack_items()))
            self.assertEqual(len(dialog.selected_item_ids()), expected)
            dialog.accept()
            self.assertIsNotNone(dialog.install_result)
            self.assertEqual(len(dialog.install_result.created), expected)
            self.assertEqual(
                len(list(mallar.glob("*.txt"))), expected
            )


@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestTemplateToolsMainWindowUi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])
        try:
            from ui.main_window import MainWindow  # noqa: F401
        except Exception as exc:
            raise unittest.SkipTest(f"MainWindow otillgänglig: {exc}")

    def test_template_tab_edit_button_opens_selected_template(self):
        from core.event_bus import EventBus
        from core.i18n import tr
        from core.recovery_manager import RecoveryManager
        from core.settings_manager import SettingsManager
        from ui.main_window import MainWindow

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            template = _seed_template(base / "Mallar")
            with mock.patch.dict(os.environ, {"EMAILAPP_PORTABLE": "1"}):
                settings = SettingsManager(base)
            settings.update_from_dict(
                {
                    "auto_update_check": False,
                    "language": "sv",
                    "ui_language": "sv",
                    "close_to_tray": False,
                }
            )
            bus = EventBus()
            window = MainWindow(settings, bus, RecoveryManager(bus))
            self.addCleanup(window.close)
            window._refresh_template_tools_list()
            matches = window._tpl_tools_list.findItems(
                template.name, Qt.MatchFlag.MatchExactly
            )
            row = next(
                index
                for index in range(window._tpl_tools_list.count())
                if window._tpl_tools_list.item(index).text() == template.name
            )
            window._tpl_tools_list.setCurrentRow(row)

            texts = [b.text() for b in window.findChildren(QPushButton)]
            self.assertIn(tr("templates_tab.edit_btn"), texts)
            self.assertIn(tr("templates_tab.versions_btn"), texts)
            self.assertIn(tr("templates_tab.pack_btn"), texts)

            captured = []
            window._open_template_wizard = lambda name=None: captured.append(name)  # type: ignore[method-assign]
            window._edit_selected_template_tool()
            self.assertEqual(captured, [template.name])
            self.assertTrue(matches is not None)


if __name__ == "__main__":
    unittest.main()
