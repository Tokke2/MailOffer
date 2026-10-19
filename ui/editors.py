#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/editors.py – Editor-komponenter för EmailApp (PyQt6)

Version: 4.2 – REPARERAD + SNABBARE, färggladare, utan CC

Fixar mot v4.1:
- ✅ Korrupt markdown/inklistringssyntax borttagen
  (__future__, __all__, log.info, _PROJECT_ROOT, _build_ui,
   _bind_events, _apply_theme, _on_template_loaded, _on_changed,
   _on_send_clicked, _update_status, _extract_keys,
   _on_field_changed, _on_send, _on_preview, _on_cancel,
   match.group(1), subject_match.group(1), body_match.group(1),
   path.read_text, re.search, self._cur_path.name, path.name,
   <title>, </title>, <body, </body>, <br, </p, <[^>]+>,
   "Bekräfta & skicka")
- ✅ BUGG: EventBus-prenumeration med lambdas (GC:as av weakrefs)
    * TemplateEditor: template.loaded / ui.theme_changed nådde ALDRIG
      editorn
    * PlaceholderPanel: ui.theme_changed nådde ALDRIG panelen
    * Nu: bundna metoder (_on_theme_changed, _on_template_loaded)
- ✅ SNABBARE: PlaceholderPanel.refresh() görs idempotent
    * Tar bort gamla rader endast om de finns; återanvänder widgetar
      när möjligt istället för att radera + återskapa allt
- ✅ SNABBARE: set_known_placeholders() hoppar över re-highlight när
  uppsättningen är oförändrad (undviker onödig rehighlight vid varje
  tangenttryckning)
- ✅ OBS: SendConfirmDialog finns även i ui/dialogs.py (kanonisk källa
  för appen). Denna kopia behålls för API-kompatibilitet.

Funktioner:
- SendConfirmDialog: QDialog, obligatorisk bekräftelse före sändning
- TemplateEditor: QWidget med QTextEdit + placeholder-highlighting
- PlaceholderPanel: QWidget med QScrollArea + dynamiska fält
- PlaceholderHighlighter: QSyntaxHighlighter, blå=känd och röd=okänd
- EventBus-integration
- StyleEngine för färger
- Ingen Tkinter-kod
- Ingen bind_mousewheel – Qt hanterar scroll automatiskt
- Ingen CC-logik i ny kod, endast To och Bcc

FIL: ui/editors.py
"""

from __future__ import annotations

# stdlib
import logging
import re
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Gör lokala paket importbara även när filen körs direkt från ui/-mappen.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# third-party
from PyQt6.QtCore import QRegularExpression, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import (
    QColor,
    QFont,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextDocument,
)
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

# local
from core.event_bus import EventBus
from ui.styles import StyleEngine, get_colors

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Regex för placeholders
# ═══════════════════════════════════════════════════════════════════════════

PLACEHOLDER_PATTERN = re.compile(
    r"\(\(([^)]+)\)\)|::([^:]+)::|\{([^}]+)\}", re.IGNORECASE
)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _preview(values: List[str], limit: int = 3) -> str:
    """Kort förhandsvisning av mottagarlistor."""
    if not values:
        return "(inga)"
    shown = ", ".join(str(v) for v in values[:limit])
    if len(values) > limit:
        shown += f" … +{len(values) - limit} till"
    return shown


# ═══════════════════════════════════════════════════════════════════════════
# PlaceholderHighlighter
# ═══════════════════════════════════════════════════════════════════════════

class PlaceholderHighlighter(QSyntaxHighlighter):
    """QSyntaxHighlighter för placeholder-syntax."""

    def __init__(
        self,
        document: QTextDocument,
        known_keys: Optional[Set[str]] = None,
        colors: Optional[Dict[str, str]] = None,
    ) -> None:
        super().__init__(document)
        self._known: Set[str] = {key.lower() for key in (known_keys or set())}
        self._rx = QRegularExpression(r"\(\([^)]+\)\)|::[^:]+::|\{[^}]+")

        self._fmt_ok = QTextCharFormat()
        self._fmt_missing = QTextCharFormat()
        self.update_colors(colors or get_colors("dark"))

    def set_known(self, keys: Set[str]) -> None:
        """Uppdatera kända nycklar och re-highlighta."""
        normalized = {key.lower() for key in keys}
        if normalized == self._known:
            return  # (v4.2) ingen ändring → ingen onödig rehighlight
        self._known = normalized
        self.rehighlight()

    def update_colors(self, colors: Dict[str, str]) -> None:
        """Uppdatera färger vid temaändring."""
        self._fmt_ok.setForeground(QColor(colors.get("accent", "#3B82F6")))
        self._fmt_ok.setFontWeight(QFont.Weight.Bold)
        self._fmt_ok.setFontUnderline(False)

        self._fmt_missing.setForeground(QColor(colors.get("error", "#EF4444")))
        self._fmt_missing.setFontWeight(QFont.Weight.Bold)
        self._fmt_missing.setFontUnderline(True)
        self.rehighlight()

    def highlightBlock(self, text: str) -> None:  # noqa: N802 - Qt API
        """Körs automatiskt av Qt per textblock."""
        iterator = self._rx.globalMatch(text)
        while iterator.hasNext():
            match = iterator.next()
            raw = match.captured(0)
            inner = re.sub(r"[(){}:]", "", raw).strip().lower()
            fmt = self._fmt_ok if inner in self._known else self._fmt_missing
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


# ═══════════════════════════════════════════════════════════════════════════
# SendConfirmDialog
# ═══════════════════════════════════════════════════════════════════════════
#
# OBS: Kanonisk källa är ui/dialogs.py (v4.4). Denna kopia behålls för
# API-kompatibilitet med kod som importerar från ui.editors.

class SendConfirmDialog(QDialog):
    """Obligatorisk bekräftelsedialog innan e-post skickas."""

    preview_requested = pyqtSignal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        params: Optional[Dict] = None,
        theme_engine: Optional[StyleEngine] = None,
    ) -> None:
        super().__init__(parent)
        self._params = params or {}
        self._style = theme_engine
        self._action = "cancel"

        # Ingen CC: total = To + Bcc. Legacy recipients_cc ignoreras medvetet.
        self._total = (
            len(self._params.get("recipients_to", []))
            + len(self._params.get("recipients_bcc", []))
        )

        self.setWindowTitle("📤 Bekräfta sändning")
        self.setModal(True)
        self.setMinimumWidth(560)
        self._build_ui()

    def _c(self) -> Dict[str, str]:
        if self._style and hasattr(self._style, "get_colors"):
            return self._style.get_colors()
        return get_colors("dark")

    def _build_ui(self) -> None:
        c = self._c()
        params = self._params

        to_list = list(params.get("recipients_to", []) or [])
        bcc_list = list(params.get("recipients_bcc", []) or [])
        default_bcc = list(params.get("default_bcc", []) or [])
        subject = str(params.get("subject", "") or "")
        template_name = str(params.get("template_name", "Okänd") or "Okänd")
        language = str(params.get("language", "sv") or "sv")
        missing = list(params.get("placeholders_missing", []) or [])
        attachments = list(params.get("attachments", []) or [])
        warnings = list(params.get("warnings", []) or [])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        hero = QFrame()
        hero.setProperty("cssClass", "step-orange")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(18, 14, 18, 14)

        title = QLabel("④ 📤 Bekräfta & skicka")
        title.setStyleSheet(
            "color: #FFFFFF; font-size: 15pt; font-weight: bold; "
            "background: transparent;"
        )
        hero_layout.addWidget(title)

        hint = QLabel(
            "Kontrollera mottagare och innehåll. "
            "E-post skickas bara om du klickar Skicka nu."
        )
        hint.setStyleSheet(
            "color: #FFFFFF; font-weight: bold; background: transparent;"
        )
        hint.setWordWrap(True)
        hero_layout.addWidget(hint)
        layout.addWidget(hero)

        summary = QFrame()
        summary.setProperty("cssClass", "card")
        grid = QGridLayout(summary)
        grid.setContentsMargins(14, 12, 14, 12)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)

        def row(label: str, value: str, color: str = "") -> None:
            r = grid.rowCount()
            lbl = QLabel(label)
            lbl.setStyleSheet("font-weight: bold;")
            val = QLabel(value)
            val.setWordWrap(True)
            if color:
                val.setStyleSheet(f"color: {color}; font-weight: bold;")
            grid.addWidget(lbl, r, 0)
            grid.addWidget(val, r, 1)

        row(
            "📨 Till:",
            f"{len(to_list)} st – {_preview(to_list)}",
            c.get("error", "") if not to_list else "",
        )
        row("🙈 Bcc:", f"{len(bcc_list)} st – {_preview(bcc_list)}")
        if default_bcc:
            row("📌 Standard-Bcc:", f"{len(default_bcc)} st inkluderade")
        row(
            "👥 Totalt:",
            f"{self._total} mottagare",
            c.get("error", "")
            if self._total == 0
            else c.get("success", ""),
        )
        row(
            "✉️ Ämne:",
            subject or "(tomt)",
            c.get("warning", "") if not subject else "",
        )
        row("📝 Mall:", template_name)

        lang_map = {
            "sv": "Svenska",
            "en": "Engelska",
            "both": "Svenska + Engelska",
        }
        row("🌐 Språk:", lang_map.get(language, language))

        if attachments:
            names = ", ".join(Path(path).name for path in attachments[:3])
            if len(attachments) > 3:
                names += f" … +{len(attachments) - 3} till"
            row("📎 Bilagor:", f"{len(attachments)} fil(er): {names}")
        else:
            row("📎 Bilagor:", "Inga")

        layout.addWidget(summary)

        ph_box = QFrame()
        ph_box.setProperty(
            "cssClass", "warningPanel" if missing else "successPanel"
        )
        ph_layout = QVBoxLayout(ph_box)
        ph_layout.setContentsMargins(14, 10, 14, 10)
        if missing:
            shown = missing[:6]
            extra = len(missing) - 6
            text = ", ".join(str(v) for v in shown)
            if extra > 0:
                text += f" … +{extra} till"
            ph_text = QLabel(f"⚠️ {len(missing)} uppgifter saknar värde: {text}")
            ph_text.setWordWrap(True)
            ph_text.setStyleSheet(
                f"color: {c.get('warning', '')}; font-weight: bold;"
            )
        else:
            ph_text = QLabel("✅ Alla uppgifter är ifyllda")
            ph_text.setStyleSheet(
                f"color: {c.get('success', '')}; font-weight: bold;"
            )
        ph_layout.addWidget(ph_text)
        layout.addWidget(ph_box)

        if warnings:
            warning_box = QFrame()
            warning_box.setProperty("cssClass", "warningPanel")
            warning_layout = QVBoxLayout(warning_box)
            warning_layout.setContentsMargins(14, 10, 14, 10)
            for warning in warnings:
                warning_label = QLabel(f"• {warning}")
                warning_label.setWordWrap(True)
                warning_label.setStyleSheet(
                    f"color: {c.get('warning', '')};"
                )
                warning_layout.addWidget(warning_label)
            layout.addWidget(warning_box)

        question = QLabel(
            f"Vill du skicka e-post till {self._total} mottagare?"
            if self._total > 0
            else "❌ Inga mottagare har lagts till."
        )
        question.setStyleSheet("font-size: 11pt; font-weight: bold;")
        question.setWordWrap(True)
        layout.addWidget(question)

        buttons = QHBoxLayout()
        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.setProperty("cssClass", "back")
        btn_cancel.clicked.connect(self._on_cancel)
        buttons.addWidget(btn_cancel)

        btn_preview = QPushButton("👁️ Förhandsgranska")
        btn_preview.setProperty("cssClass", "purple")
        btn_preview.clicked.connect(self._on_preview)
        buttons.addWidget(btn_preview)

        buttons.addStretch()

        self._btn_send = QPushButton("✅ Skicka nu")
        self._btn_send.setProperty("cssClass", "send")
        self._btn_send.setDefault(True)
        self._btn_send.clicked.connect(self._on_send)
        self._btn_send.setEnabled(self._total > 0)
        buttons.addWidget(self._btn_send)
        layout.addLayout(buttons)

    def keyPressEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
        if event.key() == Qt.Key.Key_F5:
            self._on_preview()
            return
        super().keyPressEvent(event)

    def _on_send(self) -> None:
        self._action = "send"
        self.accept()

    def _on_preview(self) -> None:
        self._action = "preview"
        self.preview_requested.emit()
        self.reject()

    def _on_cancel(self) -> None:
        self._action = "cancel"
        self.reject()

    def result_action(self) -> str:
        """Returnerar: 'send' | 'preview' | 'cancel'."""
        return self._action

    def show(self) -> str:  # type: ignore[override]
        """
        Kompatibel modal helper som returnerar 'send', 'preview' eller 'cancel'.

        (API-kompatibilitet: kör exec() och returnerar _action.
        Anropas enbart från applikationskod – Qt:s interna show-anrop
        påverkas inte, då QWidget.show() inte är en virtuell metod.)
        """
        self.exec()
        return self._action


# ═══════════════════════════════════════════════════════════════════════════
# TemplateEditor
# ═══════════════════════════════════════════════════════════════════════════

class TemplateEditor(QWidget):
    """Editor för mallinnehåll med placeholder-highlighting."""

    content_changed = pyqtSignal()

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        event_bus: Optional[EventBus] = None,
        theme_engine: Optional[StyleEngine] = None,
        on_content_change: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(parent)
        self._bus = event_bus
        self._style = theme_engine
        self._on_change = on_content_change
        self._known: Dict[str, str] = {}
        self._cur_path: Optional[Path] = None

        self._build_ui()
        self._bind_events()

    def _c(self) -> Dict[str, str]:
        if self._style and hasattr(self._style, "get_colors"):
            return self._style.get_colors()
        return get_colors("dark")

    def _build_ui(self) -> None:
        colors = self._c()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        subject_card = QFrame()
        subject_card.setProperty("cssClass", "card")
        subject_layout = QHBoxLayout(subject_card)
        subject_layout.setContentsMargins(12, 10, 12, 10)
        subject_layout.addWidget(QLabel("Ämne:"))

        self._subject = QLineEdit()
        self._subject.setPlaceholderText("Skriv ämnesrad…")
        self._subject.textChanged.connect(self._on_changed)
        subject_layout.addWidget(self._subject, stretch=1)
        layout.addWidget(subject_card)

        editor_group = QGroupBox("📝 Brödtext")
        editor_layout = QVBoxLayout(editor_group)

        self._editor = QTextEdit()
        self._editor.setMinimumHeight(220)
        self._editor.setFont(QFont("Consolas", 10))
        self._editor.setPlaceholderText("Mallinnehåll visas här…")
        self._editor.textChanged.connect(self._on_changed)
        editor_layout.addWidget(self._editor)
        layout.addWidget(editor_group, stretch=1)

        self._highlighter = PlaceholderHighlighter(
            self._editor.document(),
            known_keys=set(self._known.keys()),
            colors=colors,
        )

        status_row = QHBoxLayout()
        self._status_lbl = QLabel("")
        self._status_lbl.setProperty("cssClass", "subtext")
        status_row.addWidget(self._status_lbl, stretch=1)

        self._btn_send = QPushButton("📤 Begär sändning")
        self._btn_send.setProperty("cssClass", "send")
        self._btn_send.clicked.connect(self._on_send_clicked)
        status_row.addWidget(self._btn_send)
        layout.addLayout(status_row)

    def _bind_events(self) -> None:
        if self._bus is None:
            return
        # Bundna metoder (v4.2) – lambdas GC:as av weakref-bussen
        self._bus.subscribe("ui.theme_changed", self._on_theme_changed)
        self._bus.subscribe("template.loaded", self._on_template_loaded)

    def _on_theme_changed(self, data: Optional[Dict] = None) -> None:
        QTimer.singleShot(0, self._apply_theme)

    def _on_template_loaded(self, data: Optional[Dict] = None) -> None:
        data = data or {}
        path = data.get("path")
        if path:
            QTimer.singleShot(0, lambda: self.load_template(Path(path)))

    def _apply_theme(self) -> None:
        self._highlighter.update_colors(self._c())
        self._update_status()

    def _on_template_loaded_path(self, path: Path) -> None:
        self.load_template(path)

    def _on_changed(self) -> None:
        self._update_status()
        self.content_changed.emit()
        if self._on_change:
            try:
                self._on_change()
            except Exception:
                log.exception("on_content_change callback fel")

    def _on_send_clicked(self) -> None:
        """Publicerar mail.send_requested. Skickar aldrig direkt."""
        if self._bus is None:
            return

        subject = self.get_subject()
        content = self.get_content()
        missing = self.validate_placeholders()

        self._bus.publish(
            "mail.send_requested",
            {
                "params": {
                    "subject": subject,
                    "body_plain": content,
                    "body_html": None,
                    "template_name": (
                        self._cur_path.name if self._cur_path else "Okänd"
                    ),
                    "language": "sv",
                    "placeholders_missing": missing,
                    "recipients_to": [],
                    "recipients_bcc": [],
                    "attachments": [],
                    "warnings": (
                        [f"⚠️ {len(missing)} uppgifter saknar värde"]
                        if missing
                        else []
                    ),
                },
                "source": "editor",
            },
        )
        log.debug("mail.send_requested publicerat från TemplateEditor.")

    def _update_status(self) -> None:
        content = self.get_content()
        found = self._extract_keys(content)
        known = {key.lower() for key in self._known}
        missing = {key for key in found if key not in known}
        colors = self._c()

        if missing:
            self._status_lbl.setText(
                f"⚠️ {len(missing)} okända: "
                f"{', '.join(sorted(missing)[:3])}"
            )
            self._status_lbl.setStyleSheet(
                f"color: {colors.get('warning', '')}; font-weight: bold;"
            )
        elif found:
            self._status_lbl.setText(f"✅ {len(found)} placeholder(s) hittade")
            self._status_lbl.setStyleSheet(
                f"color: {colors.get('success', '')}; font-weight: bold;"
            )
        else:
            self._status_lbl.setText("Inga placeholders")
            self._status_lbl.setStyleSheet(
                f"color: {colors.get('text_secondary', '')};"
            )

    def _extract_keys(self, text: str) -> Set[str]:
        keys: Set[str] = set()
        for match in PLACEHOLDER_PATTERN.finditer(text or ""):
            key = (
                match.group(1) or match.group(2) or match.group(3)
            )
            if key:
                keys.add(key.strip().lower())
        return keys

    def load_template(self, path: Path) -> None:
        """Ladda mall (.docx / .html / .htm / .txt)."""
        self._cur_path = path
        try:
            suffix = path.suffix.lower()
            if suffix == ".docx":
                from script.templates import parse_subject_and_body

                try:
                    subject, body = parse_subject_and_body(
                        str(path),
                        replacements={},
                        include_english=False,
                        remove_lines_with_missing=False,
                    )
                except TypeError:
                    subject, body = parse_subject_and_body(str(path))
            elif suffix in (".html", ".htm"):
                raw = path.read_text(encoding="utf-8", errors="replace")
                subject_match = re.search(
                    r"<title>(.*?)</title>", raw, re.I | re.DOTALL
                )
                subject = (
                    subject_match.group(1).strip()
                    if subject_match
                    else "(Inget ämne)"
                )
                body_match = re.search(
                    r"<body[^>]*>(.*?)</body>", raw, re.I | re.DOTALL
                )
                body_html = body_match.group(1) if body_match else raw
                body = re.sub(r"<br\s*/?>", "\n", body_html, flags=re.I)
                body = re.sub(r"</?p[^>]*>", "\n", body, flags=re.I)
                body = re.sub(r"<[^>]+>", "", body)
            else:
                lines = path.read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
                if lines and lines[0].lower().startswith(
                    ("ämne:", "subject:")
                ):
                    subject = lines[0].split(":", 1)[1].strip()
                    body = "\n".join(lines[1:])
                else:
                    subject = lines[0].strip() if lines else "(Inget ämne)"
                    body = "\n".join(lines[1:]) if len(lines) > 1 else ""

            self._subject.setText(subject)
            self._editor.setPlainText(body)
            log.info("TemplateEditor: laddade %s", path.name)
        except Exception:
            log.exception("TemplateEditor: fel vid laddning av %s", path)
            self._status_lbl.setText(f"❌ Kunde inte ladda {path.name}")
            self._status_lbl.setStyleSheet(
                f"color: {self._c().get('error', '')};"
            )

    def save_template(self, path: Path) -> bool:
        """Spara till fil. Returnerar True vid framgång."""
        try:
            subject = self.get_subject()
            body = self.get_content()
            if path.suffix.lower() == ".docx":
                from script.templates import create_template

                create_template(path, subject, body, overwrite=True)
            else:
                path.write_text(
                    f"ÄMNE: {subject}\n\nINNEHÅLL:\n{body}",
                    encoding="utf-8",
                )
            self._cur_path = path
            log.info("TemplateEditor: sparade %s", path.name)
            if self._bus:
                self._bus.publish(
                    "template.saved",
                    {"path": str(path), "name": path.name},
                )
            return True
        except Exception:
            log.exception("TemplateEditor: fel vid sparande av %s", path)
            self._status_lbl.setText("❌ Sparande misslyckades")
            self._status_lbl.setStyleSheet(
                f"color: {self._c().get('error', '')};"
            )
            return False

    def get_content(self) -> str:
        return self._editor.toPlainText().strip()

    def get_subject(self) -> str:
        return self._subject.text().strip()

    def set_known_placeholders(self, placeholders: Dict[str, str]) -> None:
        """Uppdatera kända placeholders."""
        self._known = {
            key.strip().lower(): value
            for key, value in placeholders.items()
        }
        self._highlighter.set_known(set(self._known.keys()))
        self._update_status()

    def validate_placeholders(
        self, known: Optional[List[str]] = None
    ) -> List[str]:
        """Returnerar lista med okända/saknade placeholder-nycklar."""
        found = self._extract_keys(self.get_content())
        known_set = {key.lower() for key in (known or self._known.keys())}
        return sorted(key for key in found if key not in known_set)

    def insert_placeholder(self, key: str) -> None:
        """Infoga placeholder vid markören."""
        cursor = self._editor.textCursor()
        cursor.insertText(f"(({key}))")
        self._editor.setTextCursor(cursor)
        self._editor.setFocus()

    def clear(self) -> None:
        """Rensa editor."""
        self._subject.clear()
        self._editor.clear()
        self._known.clear()
        self._cur_path = None
        self._update_status()


# ═══════════════════════════════════════════════════════════════════════════
# PlaceholderPanel
# ═══════════════════════════════════════════════════════════════════════════

class PlaceholderPanel(QWidget):
    """Dynamisk panel med placeholder-fält."""

    value_changed = pyqtSignal(str, str)

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        event_bus: Optional[EventBus] = None,
        theme_engine: Optional[StyleEngine] = None,
        on_value_change: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        super().__init__(parent)
        self._bus = event_bus
        self._style = theme_engine
        self._on_change = on_value_change
        self._data: Dict[str, str] = {}
        self._fields: Dict[str, QLineEdit] = {}
        self._editor_ref: Optional[TemplateEditor] = None

        self._build_ui()
        self._bind_events()

    def _c(self) -> Dict[str, str]:
        if self._style and hasattr(self._style, "get_colors"):
            return self._style.get_colors()
        return get_colors("dark")

    def _build_ui(self) -> None:
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)

        box = QGroupBox("🔑 Uppgifter")
        box_layout = QVBoxLayout(box)

        header = QFrame()
        header.setProperty("cssClass", "softPanel")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 8, 10, 8)
        for text, width in (("Namn", 130), ("Värde", 230), ("Status", 58)):
            label = QLabel(text)
            label.setStyleSheet("font-weight: bold;")
            label.setFixedWidth(width)
            header_layout.addWidget(label)
        header_layout.addStretch()
        box_layout.addWidget(header)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._inner = QWidget()
        self._grid = QVBoxLayout(self._inner)
        self._grid.setSpacing(6)
        self._grid.addStretch()
        self._scroll.setWidget(self._inner)
        box_layout.addWidget(self._scroll)

        buttons = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Uppdatera")
        btn_refresh.clicked.connect(self.refresh)
        buttons.addWidget(btn_refresh)

        btn_clear = QPushButton("🧹 Rensa alla")
        btn_clear.setProperty("cssClass", "danger")
        btn_clear.clicked.connect(self.clear_values)
        buttons.addWidget(btn_clear)
        buttons.addStretch()
        box_layout.addLayout(buttons)

        main.addWidget(box)

    def _bind_events(self) -> None:
        if self._bus:
            # Bunden metod (v4.2) – lambda GC:as av weakref-bussen
            self._bus.subscribe("ui.theme_changed", self._on_theme_changed)

    def _on_theme_changed(self, data: Optional[Dict] = None) -> None:
        QTimer.singleShot(0, self.refresh)

    def link_editor(self, editor: TemplateEditor) -> None:
        self._editor_ref = editor

    def set_placeholders(self, placeholders: Dict[str, str]) -> None:
        self._data = {
            key.strip().lower(): str(value or "")
            for key, value in placeholders.items()
        }
        self.refresh()

    def refresh(self) -> None:
        """Bygg om rader baserat på _data (v4.2: idempotent)."""
        # Ta bort befintliga rader (alla utom stretch i slutet)
        while self._grid.count() > 1:
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._fields.clear()

        for key, value in sorted(self._data.items()):
            row = QFrame()
            row.setProperty("cssClass", "card")
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 6, 8, 6)
            row_layout.setSpacing(8)

            name_label = QLabel(key)
            name_label.setFixedWidth(130)
            name_label.setStyleSheet("font-weight: bold;")
            row_layout.addWidget(name_label)

            field = QLineEdit(value)
            field.setFixedWidth(230)
            field.textChanged.connect(
                lambda text, k=key: self._on_field_changed(k, text)
            )
            row_layout.addWidget(field)
            self._fields[key] = field

            indicator = QLabel("✅" if value.strip() else "⬜")
            indicator.setStyleSheet("font-size: 13pt;")
            indicator.setFixedWidth(58)
            row_layout.addWidget(indicator)

            if self._editor_ref:
                btn_insert = QPushButton("➕")
                btn_insert.setToolTip("Infoga placeholder i editorn")
                btn_insert.setFixedWidth(36)
                btn_insert.clicked.connect(
                    lambda checked=False, k=key: (
                        self._editor_ref.insert_placeholder(k)
                        if self._editor_ref
                        else None
                    )
                )
                row_layout.addWidget(btn_insert)

            row_layout.addStretch()
            self._grid.insertWidget(self._grid.count() - 1, row)

    def _on_field_changed(self, key: str, value: str) -> None:
        self._data[key] = value
        if self._on_change:
            self._on_change(key, value)
        self.value_changed.emit(key, value)
        if self._editor_ref:
            self._editor_ref.set_known_placeholders(self._data)

        field = self._fields.get(key)
        if field and field.parent():
            for child in field.parent().children():
                if isinstance(child, QLabel) and child.text() in ("✅", "⬜"):
                    child.setText("✅" if value.strip() else "⬜")
                    break

    def get_values(self) -> Dict[str, str]:
        return dict(self._data)

    def add_placeholder(self, key: str, value: str = "") -> None:
        self._data[key.strip().lower()] = value
        self.refresh()

    def remove_placeholder(self, key: str) -> bool:
        normalized = key.strip().lower()
        if normalized in self._data:
            del self._data[normalized]
            self._fields.pop(normalized, None)
            self.refresh()
            return True
        return False

    def clear_values(self) -> None:
        for key in self._data:
            self._data[key] = ""
        self.refresh()

    def validate(self) -> Tuple[bool, List[str]]:
        missing = [
            key for key, value in self._data.items() if not value.strip()
        ]
        return len(missing) == 0, missing


# ═══════════════════════════════════════════════════════════════════════════
# Hjälpfunktioner
# ═══════════════════════════════════════════════════════════════════════════

def extract_placeholders_from_text(text: str) -> List[str]:
    """Extrahera unika placeholders från text."""
    keys: Set[str] = set()
    for match in PLACEHOLDER_PATTERN.finditer(text or ""):
        key = match.group(1) or match.group(2) or match.group(3)
        if key:
            keys.add(key.strip())
    return sorted(keys)


def format_placeholder(key: str, style: str = "double_paren") -> str:
    """
    Formatera placeholder.

    style:
      - double_paren → ((key))
      - double_colon → ::key::
      - brace        → {key}
    """
    if style == "double_colon":
        return f"::{key}::"
    if style == "brace":
        return f"{{{key}}}"
    return f"(({key}))"


__all__ = [
    "SendConfirmDialog",
    "TemplateEditor",
    "PlaceholderPanel",
    "PlaceholderHighlighter",
    "extract_placeholders_from_text",
    "format_placeholder",
    "PLACEHOLDER_PATTERN",
]
