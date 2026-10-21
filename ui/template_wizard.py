#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ui/template_wizard.py – Wizard för att skapa nya mallar (PyQt6).

Fem steg:
  1. Namn & format (TXT/HTML/DOCX) – börja från exempel, tomt eller
     kopia av befintlig mall.
  2. Svensk text (ämne + brödtext) med infoga-knappar för uppgifter
     (placeholders, t.ex. ::modell::).
  3. Engelsk text (valfritt [en]-block) med autoöversättning från SV.
  4. Uppgifter & förhandsgranskning med testvärden (SV + EN).
  5. Spara – filnamnskoll, standardmall-val och direktval i Skicka.

Wizarden kan även redigera en befintlig mall. Innan en befintlig
fil skrivs över sparas automatiskt en mallversion som kan
återställas. Färdiga mallpaket kan användas som startinnehåll
eller kopieras direkt till mallmappen.

Spara sker via ``script.templates.create_template`` (samma väg som
resten av appen läser), filnamnet saneras med
``sanitize_template_filename`` och brödtexten byggs med
``build_template_body``. All UI-text via ``core.i18n.tr`` (sv/en).

Resultat efter ``exec()``:
  - ``created_path``: Path till den skapade mallen (None = avbrutet)
  - ``set_as_default`` / ``select_after``: användarens slutval

FIL: ui/template_wizard.py
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from core.i18n import get_language, tr
from script.templates import (
    apply_placeholders,
    build_template_body,
    clear_scan_cache,
    create_template,
    find_placeholders_in_text,
    parse_subject_and_body,
    sanitize_template_filename,
)
from script.template_packs import (
    all_template_packs,
    install_template_items,
    template_pack_by_id,
    template_pack_item_by_id,
)
from script.template_versions import (
    TemplateVersionInfo,
    delete_template_version,
    list_template_versions,
    restore_template_version,
    snapshot_template_version,
)

log = logging.getLogger(__name__)

# Uppgifter som erbjuds som infoga-knappar (samma nycklar som resten
# av appen känner igen – se _PH_SV/_PH_EN i ui/main_window.py).
INSERT_PLACEHOLDER_KEYS: List[str] = [
    "modell", "reg", "ruta", "vin", "kommentar",
    "name", "company", "price", "date",
]

# Testvärden som förifylls i förhandsgranskningen (steg 4).
_EXAMPLE_TEST_VALUES: Dict[str, str] = {
    "modell": "Volvo XC60",
    "reg": "ABC 123",
    "ruta": "Vindruta",
    "vin": "YV1UZLF19K1000001",
    "kommentar": "Stenskott i synfältet",
    "name": "Anna Andersson",
    "company": "Exempel AB",
    "price": "4 500 kr",
    "date": "2026-10-19",
}

EXAMPLE_SUBJECT = "Offertförfrågan ::ruta:: – ::modell:: (::reg::)"
EXAMPLE_BODY_SV = (
    "Hej,\n\n"
    "Vi önskar pris och leveranstid på följande glas:\n\n"
    "Bilmodell: ::modell::\n"
    "Reg.nr: ::reg::\n"
    "Glastyp: ::ruta::\n\n"
    "Kommentar: ::kommentar::\n\n"
    "Tack på förhand!"
)
EXAMPLE_BODY_EN = (
    "Hello,\n\n"
    "Please quote price and delivery time for the following glass:\n\n"
    "Car model: ::modell::\n"
    "Reg. no.: ::reg::\n"
    "Glass type: ::ruta::\n"
    "VIN: ::vin::\n\n"
    "Comment: ::kommentar::\n\n"
    "Thank you in advance!"
)

_FORMATS = ((".txt", "wizard.format.txt"), (".html", "wizard.format.html"),
            (".docx", "wizard.format.docx"))

_PAGE_START, _PAGE_SV, _PAGE_EN, _PAGE_PREVIEW, _PAGE_SAVE = range(5)


def _clean_placeholder_name(raw: str) -> str:
    """Sanera ett eget uppgiftsnamn till en giltig placeholder-nyckel."""
    text = re.sub(r"[^\w\- ]", "", str(raw or ""), flags=re.UNICODE)
    return text.strip()


class TemplateWizard(QWizard):
    """Steg-för-steg-wizard som skapar en ny mallfil i mallmappen."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        templates_dir: Path,
        existing_names: Sequence[str] = (),
        translate_func: Optional[Callable[[str], str]] = None,
        edit_path: Optional[Path] = None,
    ) -> None:
        super().__init__(parent)
        self.templates_dir = Path(templates_dir)
        self._existing_names = list(existing_names)
        self._translate_func = translate_func
        self.edit_path = Path(edit_path) if edit_path is not None else None
        self.is_editing = self.edit_path is not None

        self.created_path: Optional[Path] = None
        self.saved_path: Optional[Path] = None
        self.edited_existing = False
        self.version_snapshot_path: Optional[Path] = None
        self.set_as_default = False
        self.select_after = True

        self._loaded_start_key: Optional[tuple] = None
        self._last_pack_name = ""
        self._load_error = ""
        self._test_inputs: Dict[str, QLineEdit] = {}

        self.setWindowTitle(
            tr("wizard.edit_title") if self.is_editing else tr("wizard.title")
        )
        self.setMinimumSize(780, 640)
        self.setButtonText(QWizard.WizardButton.BackButton, tr("wizard.btn_back"))
        self.setButtonText(QWizard.WizardButton.NextButton, tr("wizard.btn_next"))
        self.setButtonText(
            QWizard.WizardButton.FinishButton,
            tr("wizard.btn_finish_edit")
            if self.is_editing
            else tr("wizard.btn_finish"),
        )
        self.setButtonText(QWizard.WizardButton.CancelButton, tr("wizard.btn_cancel"))

        self.addPage(self._build_start_page())
        self.addPage(self._build_sv_page())
        self.addPage(self._build_en_page())
        self.addPage(self._build_preview_page())
        self.addPage(self._build_save_page())
        self.currentIdChanged.connect(self._on_page_changed)
        self._update_filename_preview()

    # ────────────────────────────────────────────────────────────────
    # Sida 1 – namn & format
    # ────────────────────────────────────────────────────────────────

    def _build_start_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle(tr("wizard.page_start.title"))
        page.setSubTitle(tr("wizard.page_start.subtitle"))
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        layout.addWidget(QLabel(f"<b>{tr('wizard.name.label')}</b>"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText(tr("wizard.name.placeholder"))
        self._name_edit.textChanged.connect(self._update_filename_preview)
        layout.addWidget(self._name_edit)

        self._filename_label = QLabel("")
        self._filename_label.setProperty("cssClass", "subtext")
        layout.addWidget(self._filename_label)

        layout.addWidget(QLabel(f"<b>{tr('wizard.format.label')}</b>"))
        self._format_group = QButtonGroup(self)
        self._format_buttons: Dict[str, QRadioButton] = {}
        for ext, key in _FORMATS:
            radio = QRadioButton(tr(key))
            if ext == ".txt":
                radio.setChecked(True)
            radio.toggled.connect(self._update_filename_preview)
            self._format_group.addButton(radio)
            self._format_buttons[ext] = radio
            layout.addWidget(radio)

        layout.addWidget(QLabel(f"<b>{tr('wizard.start_from.label')}</b>"))
        self._start_group = QButtonGroup(self)
        self._radio_example = QRadioButton(tr("wizard.start.example"))
        self._radio_example.setChecked(True)
        self._radio_blank = QRadioButton(tr("wizard.start.blank"))
        copy_row = QHBoxLayout()
        self._radio_copy = QRadioButton(tr("wizard.start.copy"))
        self._copy_combo = QComboBox()
        self._copy_combo.addItems(self._existing_names)
        self._copy_combo.setEnabled(False)
        self._radio_copy.toggled.connect(self._copy_combo.setEnabled)
        if not self._existing_names:
            self._radio_copy.setEnabled(False)
        pack_row = QHBoxLayout()
        self._radio_pack = QRadioButton(tr("wizard.start.pack"))
        self._pack_combo = QComboBox()
        language = get_language()
        for pack in all_template_packs():
            for item in pack.templates:
                self._pack_combo.addItem(
                    f"{pack.display_name(language)} – "
                    f"{item.display_name(language)}",
                    item.item_id,
                )
        self._pack_combo.setEnabled(False)
        self._radio_pack.toggled.connect(self._pack_combo.setEnabled)
        self._radio_pack.toggled.connect(self._on_pack_radio_toggled)
        self._pack_combo.currentIndexChanged.connect(
            self._on_pack_selection_changed
        )
        for radio in (
            self._radio_example,
            self._radio_blank,
            self._radio_copy,
            self._radio_pack,
        ):
            self._start_group.addButton(radio)
        copy_row.addWidget(self._radio_copy)
        copy_row.addWidget(self._copy_combo, stretch=1)
        pack_row.addWidget(self._radio_pack)
        pack_row.addWidget(self._pack_combo, stretch=1)
        layout.addWidget(self._radio_example)
        layout.addWidget(self._radio_blank)
        layout.addLayout(copy_row)
        layout.addLayout(pack_row)

        self._editing_info_label = QLabel(tr("wizard.editing_info"))
        self._editing_info_label.setWordWrap(True)
        self._editing_info_label.setProperty("cssClass", "subtext")
        self._editing_info_label.setVisible(self.is_editing)
        layout.addWidget(self._editing_info_label)

        layout.addStretch()
        if self.is_editing:
            self._apply_edit_start_state()
        return page

    # ────────────────────────────────────────────────────────────────
    # Sida 2 – svensk text
    # ────────────────────────────────────────────────────────────────

    def _build_sv_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle(tr("wizard.page_sv.title"))
        page.setSubTitle(tr("wizard.page_sv.subtitle"))
        layout = QVBoxLayout(page)
        layout.setSpacing(8)

        layout.addWidget(QLabel(f"<b>{tr('wizard.subject.label')}</b>"))
        self._subject_edit = QLineEdit()
        layout.addWidget(self._subject_edit)

        layout.addWidget(QLabel(f"<b>{tr('wizard.body.label')}</b>"))
        self._sv_body_edit = QPlainTextEdit()
        self._sv_body_edit.setMinimumHeight(200)
        layout.addWidget(self._sv_body_edit)

        insert_row = QHBoxLayout()
        insert_row.addWidget(QLabel(tr("wizard.insert.label")))
        for key in INSERT_PLACEHOLDER_KEYS:
            btn = QPushButton(f"::{key}::")
            btn.clicked.connect(
                lambda _checked=False, k=key: self._insert_placeholder(k)
            )
            insert_row.addWidget(btn)
        btn_custom = QPushButton(tr("wizard.insert.custom_btn"))
        btn_custom.clicked.connect(self._insert_custom_placeholder)
        insert_row.addWidget(btn_custom)
        insert_row.addStretch()
        layout.addLayout(insert_row)
        return page

    def _insert_placeholder(self, key: str) -> None:
        token = f"::{key}::"
        if self._subject_edit.hasFocus():
            self._subject_edit.insert(token)
            self._subject_edit.setFocus()
        else:
            self._sv_body_edit.insertPlainText(token)
            self._sv_body_edit.setFocus()

    def _insert_custom_placeholder(self) -> None:
        raw, ok = QInputDialog.getText(
            self, tr("wizard.title"), tr("wizard.insert.custom_prompt")
        )
        name = _clean_placeholder_name(raw) if ok else ""
        if name:
            self._insert_placeholder(name)

    # ────────────────────────────────────────────────────────────────
    # Sida 3 – engelsk text
    # ────────────────────────────────────────────────────────────────

    def _build_en_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle(tr("wizard.page_en.title"))
        page.setSubTitle(tr("wizard.page_en.subtitle"))
        layout = QVBoxLayout(page)
        layout.setSpacing(8)

        self._include_en = QCheckBox(tr("wizard.include_en"))
        self._include_en.toggled.connect(self._on_include_en_toggled)
        layout.addWidget(self._include_en)

        layout.addWidget(QLabel(f"<b>{tr('wizard.en_body.label')}</b>"))
        self._en_body_edit = QPlainTextEdit()
        self._en_body_edit.setMinimumHeight(180)
        layout.addWidget(self._en_body_edit)

        self._btn_translate = QPushButton(tr("wizard.translate_btn"))
        self._btn_translate.clicked.connect(self._translate_sv_body)
        if self._translate_func is None:
            self._btn_translate.setEnabled(False)
        layout.addWidget(self._btn_translate)

        hint = QLabel(tr("wizard.en.hint"))
        hint.setWordWrap(True)
        hint.setProperty("cssClass", "subtext")
        layout.addWidget(hint)
        self._on_include_en_toggled(False)
        return page

    def _on_include_en_toggled(self, checked: bool) -> None:
        self._en_body_edit.setEnabled(bool(checked))
        if self._translate_func is not None:
            self._btn_translate.setEnabled(bool(checked))

    def _translate_sv_body(self) -> None:
        if self._translate_func is None:
            return
        source = self._sv_body_edit.toPlainText()
        try:
            result = self._translate_func(source)
        except Exception:
            log.warning("Autoöversättning i wizarden misslyckades", exc_info=True)
            result = ""
        if not result or result.strip() == source.strip():
            QMessageBox.information(
                self, tr("wizard.title"), tr("wizard.translate.failed")
            )
            return
        self._en_body_edit.setPlainText(result)

    # ────────────────────────────────────────────────────────────────
    # Sida 4 – uppgifter & förhandsgranskning
    # ────────────────────────────────────────────────────────────────

    def _build_preview_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle(tr("wizard.page_preview.title"))
        page.setSubTitle(tr("wizard.page_preview.subtitle"))
        layout = QVBoxLayout(page)
        layout.setSpacing(8)

        self._detected_label = QLabel("")
        self._detected_label.setWordWrap(True)
        layout.addWidget(self._detected_label)

        layout.addWidget(QLabel(f"<b>{tr('wizard.test_values.label')}</b>"))
        self._test_area = QVBoxLayout()
        layout.addLayout(self._test_area)

        layout.addWidget(QLabel(f"<b>{tr('wizard.preview.sv')}</b>"))
        self._preview_sv = QPlainTextEdit()
        self._preview_sv.setReadOnly(True)
        self._preview_sv.setMinimumHeight(110)
        layout.addWidget(self._preview_sv)

        self._preview_en_label = QLabel(f"<b>{tr('wizard.preview.en')}</b>")
        layout.addWidget(self._preview_en_label)
        self._preview_en = QPlainTextEdit()
        self._preview_en.setReadOnly(True)
        self._preview_en.setMinimumHeight(110)
        layout.addWidget(self._preview_en)
        return page

    def _all_placeholders(self) -> List[str]:
        texts = [
            self._subject_edit.text(),
            self._sv_body_edit.toPlainText(),
        ]
        if self._include_en.isChecked():
            texts.append(self._en_body_edit.toPlainText())
        return find_placeholders_in_text("\n".join(texts))

    def _refresh_preview_page(self) -> None:
        keys = self._all_placeholders()
        if keys:
            self._detected_label.setText(
                tr("wizard.detected", placeholders=", ".join(f"::{k}::" for k in keys))
            )
        else:
            self._detected_label.setText(tr("wizard.detected.none"))

        # Bygg om testvärdesfälten (behåll det användaren hunnit skriva)
        old_values = {k: w.text() for k, w in self._test_inputs.items()}
        while self._test_area.count():
            item = self._test_area.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._test_inputs = {}
        for key in keys:
            row = QHBoxLayout()
            row.addWidget(QLabel(f"::{key}::"))
            line = QLineEdit(old_values.get(key, _EXAMPLE_TEST_VALUES.get(key.lower(), "")))
            line.textChanged.connect(self._render_preview)
            row.addWidget(line, stretch=1)
            container = QWidget()
            container.setLayout(row)
            self._test_area.addWidget(container)
            self._test_inputs[key] = line

        show_en = self._include_en.isChecked()
        self._preview_en_label.setVisible(show_en)
        self._preview_en.setVisible(show_en)
        self._render_preview()

    def _render_preview(self) -> None:
        values = {
            key: widget.text()
            for key, widget in self._test_inputs.items()
            if widget.text().strip()
        }
        subject = apply_placeholders(
            self._subject_edit.text(), values, keep_unknown=True
        )
        sv_body = apply_placeholders(
            self._sv_body_edit.toPlainText(), values, keep_unknown=True
        )
        self._preview_sv.setPlainText(f"{subject}\n\n{sv_body}" if subject else sv_body)
        if self._include_en.isChecked():
            en_body = apply_placeholders(
                self._en_body_edit.toPlainText(), values, keep_unknown=True
            )
            self._preview_en.setPlainText(
                f"{subject}\n\n{en_body}" if subject else en_body
            )

    # ────────────────────────────────────────────────────────────────
    # Sida 5 – spara
    # ────────────────────────────────────────────────────────────────

    def _build_save_page(self) -> QWizardPage:
        page = QWizardPage()
        page.setTitle(tr("wizard.page_save.title"))
        page.setSubTitle(tr("wizard.page_save.subtitle"))
        layout = QVBoxLayout(page)
        layout.setSpacing(10)

        self._summary_label = QLabel("")
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

        self._exists_label = QLabel(tr("wizard.exists_warning"))
        self._exists_label.setWordWrap(True)
        self._exists_label.setStyleSheet("color: #B45309; font-weight: bold;")
        layout.addWidget(self._exists_label)

        self._chk_default = QCheckBox(tr("wizard.set_default"))
        layout.addWidget(self._chk_default)
        self._chk_select = QCheckBox(tr("wizard.select_after"))
        self._chk_select.setChecked(True)
        layout.addWidget(self._chk_select)
        layout.addStretch()
        return page

    def _refresh_save_page(self) -> None:
        keys = self._all_placeholders()
        self._summary_label.setText(
            tr(
                "wizard.summary",
                filename=self._filename() or "—",
                folder=str(self.templates_dir),
                placeholders=", ".join(f"::{k}::" for k in keys) or "—",
            )
        )
        target = self._target_path()
        if self.is_editing:
            self._exists_label.setText(tr("wizard.version_saved_note"))
            self._exists_label.setStyleSheet("")
            self._exists_label.setVisible(True)
        else:
            self._exists_label.setText(tr("wizard.exists_warning"))
            self._exists_label.setStyleSheet(
                "color: #B45309; font-weight: bold;"
            )
            self._exists_label.setVisible(bool(target and target.exists()))

    # ────────────────────────────────────────────────────────────────
    # Logik: filnamn, startinnehåll, validering, spara
    # ────────────────────────────────────────────────────────────────

    def _selected_extension(self) -> str:
        for ext, radio in self._format_buttons.items():
            if radio.isChecked():
                return ext
        return ".txt"

    def _filename(self) -> str:
        if self.is_editing and self.edit_path is not None:
            return self.edit_path.name
        return sanitize_template_filename(
            self._name_edit.text(), self._selected_extension()
        )

    def _target_path(self) -> Optional[Path]:
        name = self._filename()
        return self.templates_dir / name if name else None

    def _update_filename_preview(self) -> None:
        name = self._filename()
        self._filename_label.setText(
            tr("wizard.filename.preview", filename=name) if name else ""
        )

    def _apply_edit_start_state(self) -> None:
        if self.edit_path is None:
            return
        self._name_edit.setText(self.edit_path.stem)
        self._name_edit.setEnabled(False)
        suffix = self.edit_path.suffix.lower()
        if suffix == ".htm":
            suffix = ".html"
        for ext, radio in self._format_buttons.items():
            radio.setChecked(ext == suffix)
            radio.setEnabled(False)
        for radio in (
            self._radio_example,
            self._radio_blank,
            self._radio_copy,
            self._radio_pack,
        ):
            radio.setEnabled(False)
        self._copy_combo.setEnabled(False)
        self._pack_combo.setEnabled(False)

    def _on_pack_radio_toggled(self, checked: bool) -> None:
        if checked:
            self._on_pack_selection_changed()

    def _on_pack_selection_changed(self, _index: int = -1) -> None:
        if self.is_editing or not self._radio_pack.isChecked():
            return
        item = template_pack_item_by_id(self._pack_combo.currentData())
        if item is None:
            return
        txt_radio = self._format_buttons.get(".txt")
        if txt_radio is not None:
            txt_radio.setChecked(True)
        suggested = item.display_name(get_language())
        current = self._name_edit.text().strip()
        if not current or current == self._last_pack_name:
            self._name_edit.setText(suggested)
        self._last_pack_name = suggested

    def _start_key(self) -> tuple:
        if self.is_editing and self.edit_path is not None:
            return ("edit", self.edit_path.name)
        if self._radio_pack.isChecked():
            return ("pack", str(self._pack_combo.currentData() or ""))
        if self._radio_copy.isChecked():
            return ("copy", self._copy_combo.currentText())
        if self._radio_blank.isChecked():
            return ("blank",)
        return ("example",)

    def _load_start_content_if_needed(self) -> None:
        key = self._start_key()
        if key == self._loaded_start_key:
            return
        self._loaded_start_key = key
        if key[0] == "example":
            self._subject_edit.setText(EXAMPLE_SUBJECT)
            self._sv_body_edit.setPlainText(EXAMPLE_BODY_SV)
            self._en_body_edit.setPlainText(EXAMPLE_BODY_EN)
            self._include_en.setChecked(True)
        elif key[0] == "blank":
            self._subject_edit.clear()
            self._sv_body_edit.clear()
            self._en_body_edit.clear()
            self._include_en.setChecked(False)
        elif key[0] == "edit" and self.edit_path is not None:
            if not self._load_template_content(self.edit_path):
                QMessageBox.critical(
                    self,
                    tr("wizard.edit_title"),
                    tr(
                        "wizard.error.load_failed",
                        error=self._load_error or self.edit_path.name,
                    ),
                )
        elif key[0] == "pack":
            self._load_pack_content(str(key[1]))
        else:
            self._load_copy_content(str(key[1]))

    def _load_template_content(self, path: Path) -> bool:
        try:
            subject, sv_body = parse_subject_and_body(
                path, replacements={}, include_english=False, keep_unknown=True
            )
            _en_subject, en_body = parse_subject_and_body(
                path, replacements={}, include_english=True, keep_unknown=True
            )
        except Exception as exc:
            self._load_error = str(exc)
            log.warning("Kunde inte läsa mallen %s", path, exc_info=True)
            return False
        self._subject_edit.setText(subject)
        self._sv_body_edit.setPlainText(sv_body)
        has_en = bool(en_body.strip()) and en_body.strip() != sv_body.strip()
        self._en_body_edit.setPlainText(en_body if has_en else "")
        self._include_en.setChecked(has_en)
        return True

    def _load_copy_content(self, template_name: str) -> None:
        self._load_template_content(self.templates_dir / template_name)

    def _load_pack_content(self, item_id: str) -> None:
        item = template_pack_item_by_id(item_id)
        if item is None:
            return
        self._subject_edit.setText(item.subject)
        self._sv_body_edit.setPlainText(item.body_sv)
        self._en_body_edit.setPlainText(item.body_en)
        self._include_en.setChecked(bool(item.body_en.strip()))

    def _warn(self, message_key: str) -> None:
        QMessageBox.warning(self, tr("wizard.error.title"), tr(message_key))

    def validateCurrentPage(self) -> bool:  # noqa: N802 (Qt-API)
        page_id = self.currentId()
        if page_id == _PAGE_START:
            if not self._filename():
                self._warn("wizard.error.name_required")
                return False
        elif page_id == _PAGE_SV:
            if not self._subject_edit.text().strip():
                self._warn("wizard.error.subject_required")
                return False
            if not self._sv_body_edit.toPlainText().strip():
                self._warn("wizard.error.body_required")
                return False
        elif page_id == _PAGE_EN:
            if self._include_en.isChecked() and not self._en_body_edit.toPlainText().strip():
                self._warn("wizard.error.en_body_required")
                return False
        return True

    def _on_page_changed(self, page_id: int) -> None:
        if page_id in (_PAGE_SV, _PAGE_EN, _PAGE_PREVIEW, _PAGE_SAVE):
            self._load_start_content_if_needed()
        if page_id == _PAGE_PREVIEW:
            self._refresh_preview_page()
        elif page_id == _PAGE_SAVE:
            self._refresh_save_page()

    def accept(self) -> None:  # noqa: N802 (Qt-API)
        target = self._target_path()
        if target is None:
            self._warn("wizard.error.name_required")
            return
        body = build_template_body(
            self._sv_body_edit.toPlainText(),
            self._en_body_edit.toPlainText() if self._include_en.isChecked() else "",
        )
        had_existing = target.exists()
        try:
            self.templates_dir.mkdir(parents=True, exist_ok=True)
            if had_existing:
                self.version_snapshot_path = snapshot_template_version(target)
            create_template(target, self._subject_edit.text().strip(), body,
                            overwrite=True)
            clear_scan_cache()
        except Exception as exc:
            log.warning("Wizarden kunde inte spara %s", target, exc_info=True)
            QMessageBox.critical(
                self, tr("wizard.title"),
                tr("wizard.error.save_failed", error=str(exc)),
            )
            return
        self.created_path = target
        self.saved_path = target
        self.edited_existing = bool(self.is_editing or had_existing)
        self.set_as_default = self._chk_default.isChecked()
        self.select_after = self._chk_select.isChecked()
        log.info("Mall sparad via wizarden: %s", target)
        super().accept()



class TemplateVersionsDialog(QDialog):
    """Visa, spara, radera och återställ versioner av en mall."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        template_path: Path,
    ) -> None:
        super().__init__(parent)
        self.template_path = Path(template_path)
        self.restored = False
        self.changed = False
        self._versions: Dict[str, TemplateVersionInfo] = {}

        self.setWindowTitle(
            tr("template_versions.title", name=self.template_path.name)
        )
        self.setMinimumSize(760, 560)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info = QLabel(tr("template_versions.text"))
        info.setWordWrap(True)
        layout.addWidget(info)

        self._empty_label = QLabel(tr("template_versions.empty"))
        self._empty_label.setWordWrap(True)
        self._empty_label.setProperty("cssClass", "subtext")
        layout.addWidget(self._empty_label)

        self._list = QListWidget()
        self._list.currentItemChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list, stretch=1)

        layout.addWidget(QLabel(f"<b>{tr('template_versions.preview_title')}</b>"))
        self._preview = QPlainTextEdit()
        self._preview.setReadOnly(True)
        self._preview.setMinimumHeight(150)
        layout.addWidget(self._preview)

        row = QHBoxLayout()
        self._btn_snapshot = QPushButton(tr("template_versions.snapshot_btn"))
        self._btn_snapshot.clicked.connect(self._snapshot_current)
        row.addWidget(self._btn_snapshot)
        self._btn_delete = QPushButton(tr("template_versions.delete_btn"))
        self._btn_delete.setProperty("cssClass", "danger")
        self._btn_delete.clicked.connect(self._delete_selected)
        row.addWidget(self._btn_delete)
        row.addStretch()
        self._btn_restore = QPushButton(tr("template_versions.restore_btn"))
        self._btn_restore.setProperty("cssClass", "success")
        self._btn_restore.clicked.connect(self._restore_selected)
        row.addWidget(self._btn_restore)
        btn_close = QPushButton(tr("template_versions.close"))
        btn_close.clicked.connect(self.reject)
        row.addWidget(btn_close)
        layout.addLayout(row)

        self._reload_versions()

    def _reload_versions(self, select_path: Optional[Path] = None) -> None:
        versions = list_template_versions(self.template_path)
        self._versions = {str(version.path): version for version in versions}
        self._list.clear()
        for version in versions:
            item = QListWidgetItem(
                f"{version.label} · {version.size} B · {version.path.name}"
            )
            item.setData(Qt.ItemDataRole.UserRole, str(version.path))
            self._list.addItem(item)
        self._empty_label.setVisible(not versions)
        target_row = 0 if versions else -1
        if select_path is not None:
            for row, version in enumerate(versions):
                if version.path == select_path:
                    target_row = row
                    break
        if target_row >= 0:
            self._list.setCurrentRow(target_row)
        else:
            self._preview.clear()
            self._update_buttons()

    def _selected_version(self) -> Optional[TemplateVersionInfo]:
        item = self._list.currentItem()
        if item is None:
            return None
        return self._versions.get(str(item.data(Qt.ItemDataRole.UserRole)))

    def _update_buttons(self) -> None:
        selected = self._selected_version() is not None
        self._btn_restore.setEnabled(selected)
        self._btn_delete.setEnabled(selected)

    def _on_selection_changed(self, *_args: object) -> None:
        version = self._selected_version()
        self._update_buttons()
        if version is None:
            self._preview.clear()
            return
        try:
            subject, sv_body = parse_subject_and_body(
                version.path,
                replacements={},
                include_english=False,
                keep_unknown=True,
            )
            _en_subject, en_body = parse_subject_and_body(
                version.path,
                replacements={},
                include_english=True,
                keep_unknown=True,
            )
        except Exception as exc:
            self._preview.setPlainText(str(exc))
            return
        separator = chr(10) * 2
        text = f"{subject}{separator}{sv_body}" if subject else sv_body
        if en_body.strip() and en_body.strip() != sv_body.strip():
            text += separator + "[en]" + chr(10) + en_body
        self._preview.setPlainText(text)

    def _show_error(self, exc: Exception) -> None:
        QMessageBox.warning(
            self,
            tr("template_versions.title", name=self.template_path.name),
            tr("template_versions.error", error=str(exc)),
        )

    def _snapshot_current(self) -> None:
        try:
            path = snapshot_template_version(self.template_path)
        except Exception as exc:
            self._show_error(exc)
            return
        if path is None:
            self._show_error(FileNotFoundError(str(self.template_path)))
            return
        self.changed = True
        self._reload_versions(path)

    def _restore_selected(self) -> None:
        version = self._selected_version()
        if version is None:
            return
        reply = QMessageBox.question(
            self,
            tr("template_versions.title", name=self.template_path.name),
            tr(
                "template_versions.confirm_restore",
                when=version.label,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            restore_template_version(self.template_path, version.path)
            clear_scan_cache()
        except Exception as exc:
            self._show_error(exc)
            return
        self.restored = True
        self.changed = True
        self.accept()

    def _delete_selected(self) -> None:
        version = self._selected_version()
        if version is None:
            return
        reply = QMessageBox.question(
            self,
            tr("template_versions.title", name=self.template_path.name),
            tr("template_versions.confirm_delete", when=version.label),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            delete_template_version(self.template_path, version.path)
        except Exception as exc:
            self._show_error(exc)
            return
        self.changed = True
        self._reload_versions()


class TemplatePackDialog(QDialog):
    """Kopiera valda mallar från de inbyggda mallpaketen."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        *,
        templates_dir: Path,
    ) -> None:
        super().__init__(parent)
        self.templates_dir = Path(templates_dir)
        self.install_result = None

        self.setWindowTitle(tr("template_packs.title"))
        self.setMinimumSize(680, 520)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        info = QLabel(tr("template_packs.text"))
        info.setWordWrap(True)
        layout.addWidget(info)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(1)
        self._tree.setHeaderHidden(True)
        self._tree.currentItemChanged.connect(self._on_current_changed)
        language = get_language()
        for pack in all_template_packs():
            parent_item = QTreeWidgetItem([pack.display_name(language)])
            parent_item.setData(0, Qt.ItemDataRole.UserRole, "")
            parent_item.setData(0, Qt.ItemDataRole.UserRole + 1, pack.pack_id)
            font = parent_item.font(0)
            font.setBold(True)
            parent_item.setFont(0, font)
            self._tree.addTopLevelItem(parent_item)
            for template in pack.templates:
                child = QTreeWidgetItem([template.display_name(language)])
                child.setData(0, Qt.ItemDataRole.UserRole, template.item_id)
                child.setData(
                    0, Qt.ItemDataRole.UserRole + 1, pack.pack_id
                )
                child.setFlags(
                    child.flags() | Qt.ItemFlag.ItemIsUserCheckable
                )
                child.setCheckState(0, Qt.CheckState.Checked)
                parent_item.addChild(child)
            parent_item.setExpanded(True)
        layout.addWidget(self._tree, stretch=1)

        self._description = QLabel("")
        self._description.setWordWrap(True)
        self._description.setProperty("cssClass", "subtext")
        layout.addWidget(self._description)
        if self._tree.topLevelItemCount():
            self._tree.setCurrentItem(self._tree.topLevelItem(0))
            self._on_current_changed(self._tree.topLevelItem(0), None)

        row = QHBoxLayout()
        row.addStretch()
        btn_cancel = QPushButton(tr("template_packs.cancel"))
        btn_cancel.clicked.connect(self.reject)
        row.addWidget(btn_cancel)
        btn_install = QPushButton(tr("template_packs.install_btn"))
        btn_install.setProperty("cssClass", "success")
        btn_install.clicked.connect(self.accept)
        row.addWidget(btn_install)
        layout.addLayout(row)

    def _on_current_changed(
        self, current: Optional[QTreeWidgetItem], _previous: object
    ) -> None:
        if current is None:
            self._description.clear()
            return
        pack = template_pack_by_id(
            current.data(0, Qt.ItemDataRole.UserRole + 1)
        )
        self._description.setText(
            pack.display_description(get_language()) if pack else ""
        )

    def selected_item_ids(self) -> List[str]:
        selected: List[str] = []
        for top_index in range(self._tree.topLevelItemCount()):
            parent_item = self._tree.topLevelItem(top_index)
            for child_index in range(parent_item.childCount()):
                child = parent_item.child(child_index)
                if child.checkState(0) == Qt.CheckState.Checked:
                    item_id = str(child.data(0, Qt.ItemDataRole.UserRole) or "")
                    if item_id:
                        selected.append(item_id)
        return selected

    def accept(self) -> None:  # noqa: N802 (Qt-API)
        item_ids = self.selected_item_ids()
        if not item_ids:
            QMessageBox.warning(
                self,
                tr("template_packs.title"),
                tr("template_packs.select_none"),
            )
            return
        try:
            self.install_result = install_template_items(
                self.templates_dir, item_ids
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                tr("template_packs.title"),
                tr("template_packs.error", error=str(exc)),
            )
            return
        super().accept()


__all__ = [
    "EXAMPLE_BODY_EN",
    "EXAMPLE_BODY_SV",
    "EXAMPLE_SUBJECT",
    "INSERT_PLACEHOLDER_KEYS",
    "TemplatePackDialog",
    "TemplateVersionsDialog",
    "TemplateWizard",
]
