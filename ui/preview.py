#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/preview.py – PreviewTab för EmailApp (PyQt6)

Version: 4.3 – REPARERAD + SNABBARE, enklare, färgglad steg-för-steg-preview utan CC

Fixar mot v4.2:
- ✅ Korrupt markdown/inklistringssyntax borttagen
  (__future__, __all__, _PREVIEW_HTML_TEMPLATE, _PH_PATTERN,
   _SIGNATURE_MARKERS_SV, _SIGNATURE_MARKERS_EN, _apply_placeholders_safe,
   _extract_placeholders, _split_signature_plain, _insert_free_text_plain,
   _render_plain_section_html, _combine_sections,
   _extract_text_from_html_internal, _remove_prefix_lines,
   _build_ui, _bind_events, _apply_theme, _on_placeholder_changed,
   _on_view_toggled, _refresh_view, _render_plain_view, _render_html_view,
   _update_status, _open_in_browser, _cleanup_temp, _copy_to_clipboard,
   _build_browser_html, match.group(1), path.read_text, handle.name,
   datetime.now, path.name, webbrowser.open, log.info,
   self._plain_view.show(), self._html_view.show(),
   <!DOCTYPE>, <html>, <head>, <meta>, <title>, <style>, </style>,
   </head>, <body>, </body>, <div>, </div>, <h1>, <br>, <span>, <p>, </p>,
   <a>, </a>, "&" i text, <, >)
- ✅ BUGG: EventBus-prenumeration med lambdas (GC:as av weakrefs)
    * template.placeholder_changed / ui.theme_changed nådde ALDRIG
      preview-tabben (live-uppdatering fungerade inte)
    * Nu: bundna metoder _on_theme_changed / _on_placeholder_changed
- ✅ SNABBARE: live-render med minnescache
    * render_live() cachar parse-resultat per (sökväg, include_english)
      – mallfilsläsning+parsing sker endast när filen ändrats
    * Debounce (180 ms) av placeholder-changed → render_live
      (undviker tung re-render vid snabb inmatning)
- ✅ HTML-template med riktiga HTML-tecken (inte &lt;-escapes)
- ✅ open_in_browser/copy_to_clipboard som riktiga publika metoder
  (plus klassalias för bakåtkompatibilitet)

Funktioner:
- QWidget-baserad preview
- Tydligt steg ④: Förhandsgranska & skicka
- QTextBrowser för HTML-rendering (säker, ingen JS)
- QPlainTextEdit för plain-text
- Växla Text/HTML via QRadioButton
- Öppna i webbläsare
- Kopiera till urklipp via QClipboard
- EventBus-integration för live placeholder-uppdatering
- StyleEngine för färger
- Ingen bind_mousewheel – Qt hanterar scroll automatiskt
- Ingen CC-logik
- Fritext ovan signatur i render_live()-flödet

OBS:
- Den faktiska sändningslogiken och slutgiltig struktur ligger i
  core.email_sender.
- Preview ska dock i möjligaste mån spegla samma ordning:
  Malltext → Fritext → Signatur.

FIL: ui/preview.py
"""

from __future__ import annotations

# stdlib
import html as html_module
import logging
import os
import re
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# third-party
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QClipboard
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

# local
from core.event_bus import EventBus
from ui.styles import StyleEngine, get_colors

try:
    from script.templates import apply_placeholders, parse_subject_and_body
except ImportError:

    def apply_placeholders(  # type: ignore[misc]
        text: str, replacements: Dict[str, str], **kwargs: object
    ) -> str:
        """Fallback om script.templates inte kan importeras."""
        del kwargs
        if not text or not replacements:
            return text
        result = text
        for key, value in replacements.items():
            text_value = "" if value is None else str(value)
            result = result.replace(f"::{key}::", text_value)
            result = result.replace(f"{{{key}}}", text_value)
            result = result.replace(f"(({key}))", text_value)
        return result

    def parse_subject_and_body(  # type: ignore[misc]
        file_path: str, **kwargs: object
    ) -> Tuple[str, str]:
        """Fallback-parser för enkla textfiler."""
        del kwargs
        path = Path(file_path)
        if path.exists():
            return "Ämne", path.read_text(encoding="utf-8")
        return "Ämne", ""

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# HTML-template för browser-preview
# ═══════════════════════════════════════════════════════════════════════════

_PREVIEW_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  :root {{
    --bg: {bg};
    --surface: {surface};
    --surface-alt: {surface_alt};
    --fg: {fg};
    --fg-secondary: {fg_secondary};
    --border: {border};
    --accent: {accent};
    --success: {success};
    --warning: {warning};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
                 'Helvetica Neue', Arial, sans-serif;
    font-size: 15px;
    line-height: 1.65;
    color: var(--fg);
    background: var(--bg);
    margin: 0;
    padding: 28px;
  }}
  .page {{
    max-width: 820px;
    margin: 0 auto;
  }}
  .hero {{
    background: var(--accent);
    color: #fff;
    border-radius: 22px;
    padding: 22px 26px;
    margin-bottom: 18px;
  }}
  .hero h1 {{
    margin: 0 0 6px 0;
    font-size: 24px;
    line-height: 1.25;
  }}
  .hero .meta {{
    opacity: .92;
    font-weight: 600;
  }}
  .email-wrapper {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 28px 32px;
    box-shadow: 0 14px 34px rgba(15, 23, 42, .10);
  }}
  .subject {{
    font-size: 22px;
    font-weight: 800;
    color: var(--fg);
    margin: 0 0 14px 0;
    padding-bottom: 14px;
    border-bottom: 2px solid var(--border);
  }}
  .content {{
    white-space: pre-wrap;
    word-wrap: break-word;
    font-size: 15px;
    line-height: 1.75;
  }}
  .mail-section + .mail-section {{
    margin-top: 28px;
    padding-top: 18px;
    border-top: 1px solid var(--border);
  }}
  .free-text {{
    margin-top: 16px;
    padding-top: 12px;
    border-top: 1px dashed var(--border);
    color: var(--fg-secondary);
    font-style: italic;
  }}
  .signature {{
    margin-top: 18px;
    padding-top: 10px;
    border-top: 1px solid var(--border);
    color: var(--fg-secondary);
  }}
  .footer {{
    margin-top: 26px;
    padding-top: 14px;
    border-top: 1px solid var(--border);
    color: var(--fg-secondary);
    font-size: 12px;
    text-align: center;
  }}
  .pill {{
    display: inline-block;
    background: var(--surface-alt);
    color: var(--fg-secondary);
    border: 1px solid var(--border);
    border-radius: 999px;
    padding: 5px 10px;
    margin-top: 8px;
    font-size: 12px;
    font-weight: 700;
  }}
  a {{ color: var(--accent); text-decoration: none; }}
</style>
</head>
<body>
<div class="page">
  <div class="hero">
    <h1>④ Förhandsgranska & skicka</h1>
    <div class="meta">Förhandsgranskning skapad {timestamp}</div>
  </div>
  <div class="email-wrapper">
    <div class="subject">{subject}</div>
    <div class="content">{body}</div>
    <div class="footer">
      EmailApp – Förhandsgranskning, skickas inte automatiskt<br>
      <span class="pill">Kontrollera innehåll och mottagare innan du skickar</span>
    </div>
  </div>
</div>
</body>
</html>
"""

_PH_PATTERN = re.compile(
    r"\(\(([^)]+)\)\)|::([^:]+)::|\{([^}]+)\}", re.IGNORECASE
)

_SIGNATURE_MARKERS_SV = (
    "med vänlig hälsning",
    "med vänliga hälsningar",
    "vänliga hälsningar",
    "mvh",
    "hälsningar",
)

_SIGNATURE_MARKERS_EN = (
    "best regards",
    "kind regards",
    "regards",
    "sincerely",
    "with kind regards",
)


# ═══════════════════════════════════════════════════════════════════════════
# Hjälpfunktioner
# ═══════════════════════════════════════════════════════════════════════════

def _apply_placeholders_safe(
    text: str, replacements: Dict[str, str]
) -> str:
    """Anropa apply_placeholders med eller utan keep_unknown beroende på API."""
    try:
        return apply_placeholders(text, replacements, keep_unknown=True)
    except TypeError:
        return apply_placeholders(text, replacements)


def _extract_placeholders(text: str) -> Set[str]:
    keys: Set[str] = set()
    for match in _PH_PATTERN.finditer(text or ""):
        raw = (
            match.group(1) or match.group(2) or match.group(3) or ""
        )
        key = raw.strip()
        if key:
            keys.add(key)
    return keys


def _split_signature_plain(text: str, language: str) -> Tuple[str, str]:
    """Dela plain text i body + signatur via enkel heuristik."""
    raw = text or ""
    if not raw.strip():
        return "", ""

    markers = (
        _SIGNATURE_MARKERS_EN if language == "en" else _SIGNATURE_MARKERS_SV
    )
    lines = raw.splitlines()
    match_index: Optional[int] = None

    for index in range(len(lines) - 1, -1, -1):
        stripped = lines[index].strip().lower()
        if any(stripped.startswith(marker) for marker in markers):
            match_index = index
            break

    if match_index is None:
        return raw.strip(), ""

    body = "\n".join(lines[:match_index]).rstrip()
    signature = "\n".join(lines[match_index:]).strip()
    return body, signature


def _insert_free_text_plain(
    section_text: str, free_text: str, language: str
) -> str:
    """Placera fritext ovan signatur i plain text-sektion."""
    from core.free_text import insert_free_text
    return insert_free_text(section_text, free_text)


def _paragraphize(raw: str) -> str:
    escaped = html_module.escape(raw)
    paragraphs = escaped.split("\n\n")
    parts: List[str] = []
    for paragraph in paragraphs:
        stripped = paragraph.strip()
        if stripped:
            lines = stripped.replace("\n", "<br>\n")
            parts.append(f"<p>{lines}</p>")
    return "\n".join(parts)


def _render_plain_section_html(
    main_text: str, free_text: str = "", signature_text: str = ""
) -> str:
    blocks: List[str] = []
    if main_text.strip():
        blocks.append(_paragraphize(main_text))
    if free_text.strip():
        blocks.append(
            f'<div class="free-text">{_paragraphize(free_text)}</div>'
        )
    if signature_text.strip():
        blocks.append(
            f'<div class="signature">{_paragraphize(signature_text)}</div>'
        )
    return "\n".join(block for block in blocks if block.strip())


def _combine_sections(
    section_sv: str, section_en: str, body_is_html: bool
) -> str:
    sv = (section_sv or "").strip()
    en = (section_en or "").strip()
    if sv and en:
        if body_is_html:
            return (
                f'<div class="mail-section mail-section-sv">{sv}</div>\n'
                f'<div class="mail-section mail-section-en">{en}</div>'
            )
        return f"{sv}\n\n{en}"
    return sv or en


def _extract_text_from_html_internal(html: str) -> str:
    if not html:
        return ""
    html = re.sub(
        r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.I | re.DOTALL
    )
    html = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    html = re.sub(r"</p\s*>", "\n\n", html, flags=re.I)
    text = re.sub(r"<[^>]+>", "", html)
    text = html_module.unescape(text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _remove_prefix_lines(full_text: str, prefix_text: str) -> str:
    full_lines = full_text.splitlines(keepends=True)
    prefix_lines = prefix_text.splitlines(keepends=True)
    index = 0
    while index < len(full_lines) and index < len(prefix_lines):
        if full_lines[index] != prefix_lines[index]:
            break
        index += 1
    return "".join(full_lines[index:]).lstrip("\r\n")


# ═══════════════════════════════════════════════════════════════════════════
# PreviewTab (PyQt6)
# ═══════════════════════════════════════════════════════════════════════════

class PreviewTab(QWidget):
    """Tab/panel för tydlig förhandsgranskning av e-post."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        event_bus: Optional[EventBus] = None,
        theme_engine: Optional[StyleEngine] = None,
    ) -> None:
        super().__init__(parent)
        self._bus = event_bus
        self._style = theme_engine

        self._subject = ""
        self._body_plain = ""
        self._body_html: Optional[str] = None
        self._body_rendered = ""
        self._placeholders: Dict[str, str] = {}
        self._missing: Set[str] = set()
        self._temp_files: List[str] = []

        # Live-render state
        self._live_template_path: Optional[str] = None
        self._live_include_english: bool = False
        self._live_free_text: str = ""

        # Cache (v4.3): parse-resultat per (sökväg, include_english)
        self._parse_cache: Dict[Tuple[str, bool], Tuple[str, str]] = {}
        self._parse_cache_mtime: Dict[Tuple[str, bool], float] = {}

        self._build_ui()
        self._bind_events()

    # ─────────────────────────────────────────────────────────────────
    # Färger / UI
    # ─────────────────────────────────────────────────────────────────

    def _c(self) -> Dict[str, str]:
        if self._style and hasattr(self._style, "get_colors"):
            return self._style.get_colors()
        return get_colors("dark")

    def _build_ui(self) -> None:
        main = QVBoxLayout(self)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        # Färgglad steg-header
        hero = QFrame()
        hero.setProperty("cssClass", "step-orange")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(18, 14, 18, 14)
        hero_layout.setSpacing(3)

        title = QLabel("④ Förhandsgranska & skicka")
        title.setProperty("cssClass", "onColor")
        title.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        hero_layout.addWidget(title)

        hint = QLabel(
            "Kontrollera ämne, text, bilagor och mottagare innan du skickar."
        )
        hint.setProperty("cssClass", "onColor")
        hero_layout.addWidget(hint)
        main.addWidget(hero)

        # Ämne och vyval
        top_card = QFrame()
        top_card.setProperty("cssClass", "card")
        top = QHBoxLayout(top_card)
        top.setContentsMargins(14, 12, 14, 12)
        top.setSpacing(10)

        subj_caption = QLabel("Ämne")
        subj_caption.setProperty("cssClass", "pillOrange")
        top.addWidget(subj_caption)

        self._subject_label = QLabel("(Ingen mall vald)")
        self._subject_label.setProperty("cssClass", "heading")
        self._subject_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self._subject_label.setWordWrap(True)
        top.addWidget(self._subject_label, stretch=1)

        self._radio_plain = QRadioButton("📄 Text")
        self._radio_html = QRadioButton("🌐 HTML")
        self._radio_plain.setChecked(True)

        self._view_group = QButtonGroup(self)
        self._view_group.addButton(self._radio_plain, 0)
        self._view_group.addButton(self._radio_html, 1)
        self._view_group.idClicked.connect(self._on_view_toggled)

        top.addWidget(self._radio_plain)
        top.addWidget(self._radio_html)
        main.addWidget(top_card)

        # Status + actions
        status_card = QFrame()
        status_card.setProperty("cssClass", "softPanel")
        status_row = QHBoxLayout(status_card)
        status_row.setContentsMargins(14, 10, 14, 10)
        status_row.setSpacing(8)

        self._status_label = QLabel("Ingen förhandsgranskning")
        self._status_label.setProperty("cssClass", "subtext")
        self._status_label.setWordWrap(True)
        status_row.addWidget(self._status_label, stretch=1)

        btn_refresh = QPushButton("🔄 Uppdatera")
        btn_refresh.clicked.connect(self._refresh_view)
        status_row.addWidget(btn_refresh)
        main.addWidget(status_card)

        # Preview-vyer
        self._plain_view = QPlainTextEdit()
        self._plain_view.setReadOnly(True)
        self._plain_view.setPlaceholderText(
            "Välj en mall och fyll i uppgifter för att se "
            "förhandsgranskningen här…"
        )
        main.addWidget(self._plain_view, stretch=1)

        self._html_view = QTextBrowser()
        self._html_view.setOpenExternalLinks(False)
        self._html_view.hide()
        main.addWidget(self._html_view, stretch=1)

        # Footer-knappar
        footer_card = QFrame()
        footer_card.setProperty("cssClass", "card")
        footer = QHBoxLayout(footer_card)
        footer.setContentsMargins(14, 10, 14, 10)
        footer.setSpacing(8)

        btn_browser = QPushButton("🌐 Öppna i webbläsare")
        btn_browser.setProperty("cssClass", "purple")
        btn_browser.clicked.connect(self.open_in_browser)
        footer.addWidget(btn_browser)

        btn_copy = QPushButton("📋 Kopiera text")
        btn_copy.clicked.connect(self.copy_to_clipboard)
        footer.addWidget(btn_copy)

        btn_clear = QPushButton("🧹 Rensa")
        btn_clear.setProperty("cssClass", "danger")
        btn_clear.clicked.connect(self.clear)
        footer.addWidget(btn_clear)

        footer.addStretch()

        self._info_label = QLabel("")
        self._info_label.setProperty("cssClass", "muted")
        footer.addWidget(self._info_label)

        main.addWidget(footer_card)

    # ─────────────────────────────────────────────────────────────────
    # EventBus (v4.3: bundna metoder – lambdas GC:as av weakrefs)
    # ─────────────────────────────────────────────────────────────────

    def _bind_events(self) -> None:
        if self._bus is None:
            return
        self._bus.subscribe("ui.theme_changed", self._on_theme_changed)
        self._bus.subscribe(
            "template.placeholder_changed", self._on_placeholder_changed
        )

    def _on_theme_changed(self, data: Optional[Dict[str, Any]] = None) -> None:
        del data
        QTimer.singleShot(0, self._apply_theme)

    def _apply_theme(self) -> None:
        """Tema ändrat – global QSS sköter det mesta, status uppdateras."""
        self._update_status()
        self._refresh_view()

    def _on_placeholder_changed(
        self, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Live-uppdatering när placeholder ändras (debounce, v4.3)."""
        data = data or {}
        key = str(data.get("key", "") or "")
        value = str(data.get("value", "") or "")
        all_values = data.get("all_values")

        if isinstance(all_values, dict):
            self.set_placeholders(
                {str(k): str(v or "") for k, v in all_values.items()}
            )
            if self._live_template_path:
                self._schedule_live_render()
            return

        if key and self._body_plain:
            self._placeholders[key] = value
            self._missing = {
                k for k, v in self._placeholders.items() if not str(v).strip()
            }
            self._body_rendered = _apply_placeholders_safe(
                self._body_plain, self._placeholders
            )
            self._update_status()
            self._refresh_view()

    def _schedule_live_render(self) -> None:
        """Debounce av render_live (v4.3) – undviker tung re-render
        vid snabb inmatning."""
        if not hasattr(self, "_live_debounce"):
            self._live_debounce = QTimer(self)
            self._live_debounce.setSingleShot(True)
            self._live_debounce.setInterval(180)
            self._live_debounce.timeout.connect(self._do_live_render)
        self._live_debounce.start()

    def _do_live_render(self) -> None:
        if self._live_template_path:
            self.render_live(
                self._live_template_path,
                self._placeholders,
                include_english=self._live_include_english,
                free_text=self._live_free_text,
            )

    # ─────────────────────────────────────────────────────────────────
    # Vy-hantering
    # ─────────────────────────────────────────────────────────────────

    def _on_view_toggled(self, btn_id: int) -> None:
        if btn_id == 0:
            self._plain_view.show()
            self._html_view.hide()
        else:
            self._plain_view.hide()
            self._html_view.show()
        self._refresh_view()

    def _refresh_view(self) -> None:
        if self._radio_html.isChecked():
            self._render_html_view()
        else:
            self._render_plain_view()

    def _render_plain_view(self) -> None:
        if not self._body_plain and not self._subject:
            self._plain_view.setPlainText(
                "(Ingen förhandsgranskning tillgänglig)"
            )
            return

        display = self._body_rendered or self._body_plain
        header = f"Ämne: {self._subject}\n{'─' * 58}\n\n"
        self._plain_view.setPlainText(header + display)

    def _render_html_view(self) -> None:
        """Rendera HTML i QTextBrowser (säker, ingen JS)."""
        self._html_view.setHtml(self._build_browser_html())

    # ─────────────────────────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────────────────────────

    def _update_status(self) -> None:
        colors = self._c()
        total = len(self._placeholders)
        missing = len(self._missing)

        if not self._body_plain and not self._subject:
            self._status_label.setText("Ingen förhandsgranskning")
            self._status_label.setStyleSheet(
                f"color: {colors.get('text_secondary', '')};"
            )
        elif missing > 0:
            keys = ", ".join(sorted(self._missing)[:4])
            extra = "…" if missing > 4 else ""
            self._status_label.setText(
                f"⚠️ {missing}/{total} uppgifter saknas: {keys}{extra}"
            )
            self._status_label.setStyleSheet(
                f"color: {colors.get('warning', '')}; font-weight: bold;"
            )
        elif total > 0:
            self._status_label.setText(
                f"✅ Alla {total} uppgifter är ifyllda – redo att granskas"
            )
            self._status_label.setStyleSheet(
                f"color: {colors.get('success', '')}; font-weight: bold;"
            )
        else:
            self._status_label.setText(
                "✅ Preview klar – inga uppgifter behöver fyllas i"
            )
            self._status_label.setStyleSheet(
                f"color: {colors.get('success', '')}; font-weight: bold;"
            )

    # ─────────────────────────────────────────────────────────────────
    # Publikt API
    # ─────────────────────────────────────────────────────────────────

    def render(
        self,
        subject: str,
        body_plain: str,
        body_html: Optional[str] = None,
        placeholders: Optional[Dict[str, str]] = None,
    ) -> None:
        """Rendera förhandsgranskning."""
        raw_subject = subject or "(Inget ämne)"
        self._body_plain = body_plain or ""
        self._body_html = body_html
        self._live_template_path = None

        if placeholders is not None:
            self._placeholders = {
                str(k): str(v or "") for k, v in placeholders.items()
            }
            self._missing = {
                k
                for k, v in self._placeholders.items()
                if not str(v).strip()
            }
            self._body_rendered = _apply_placeholders_safe(
                self._body_plain, self._placeholders
            )
            self._subject = _apply_placeholders_safe(
                raw_subject, self._placeholders
            )
        else:
            self._placeholders = {}
            self._missing = set()
            self._body_rendered = self._body_plain
            self._subject = raw_subject

        self._subject_label.setText(self._subject)
        self._update_status()
        self._refresh_view()
        self._info_label.setText(f"{len(self._body_rendered)} tecken")

        log.debug(
            "PreviewTab renderade: '%s', %d tecken, %d placeholders",
            self._subject,
            len(self._body_rendered),
            len(self._placeholders),
        )

    def render_live(
        self,
        template_path: str,
        placeholder_values: Dict[str, str],
        include_english: bool = False,
        free_text: str = "",
    ) -> None:
        """Rendera live direkt från mallfil.

        Målet här är att preview ska spegla den logiska strukturen:
        Malltext → Fritext → Signatur.
        """
        try:
            path = Path(template_path)
            self._live_template_path = template_path
            self._live_include_english = include_english
            self._live_free_text = free_text or ""

            if not path.exists():
                log.warning("render_live: saknas: %s", template_path)
                self._subject = "(Mall saknas)"
                self._body_plain = ""
                self._body_rendered = ""
                self._body_html = None
                self._subject_label.setText(self._subject)
                self._update_status()
                self._refresh_view()
                return

            placeholders = {
                str(k): str(v or "") for k, v in placeholder_values.items()
            }

            # ── Cachad parsing (v4.3) ──────────────────────────────
            def _cached_parse(key: Tuple[str, bool]) -> Tuple[str, str]:
                cache_key = (str(path), key[1])
                try:
                    mtime = path.stat().st_mtime
                except OSError:
                    mtime = -1.0
                if (
                    cache_key in self._parse_cache
                    and self._parse_cache_mtime.get(cache_key) == mtime
                ):
                    return self._parse_cache[cache_key]
                result = parse_subject_and_body(
                    str(path),
                    replacements=placeholders,
                    include_english=key[1],
                )
                self._parse_cache[cache_key] = result
                self._parse_cache_mtime[cache_key] = mtime
                return result

            # Svensk del utan engelsk blockrendering
            subject_sv, body_sv = _cached_parse((str(path), False))

            if include_english:
                subject_both, body_both = _cached_parse(
                    (str(path), True)
                )
                body_en = _remove_prefix_lines(body_both, body_sv)
                subject_rendered = subject_both or subject_sv or "(Inget ämne)"
            else:
                body_en = ""
                subject_rendered = subject_sv or "(Inget ämne)"

            section_sv_plain = _insert_free_text_plain(
                body_sv, free_text, "sv"
            )
            section_en_plain = (
                _insert_free_text_plain(body_en, free_text, "en")
                if body_en
                else ""
            )
            body_rendered = _combine_sections(
                section_sv_plain, section_en_plain, False
            )

            sv_main, sv_signature = _split_signature_plain(body_sv, "sv")
            en_main, en_signature = (
                _split_signature_plain(body_en, "en") if body_en else ("", "")
            )
            section_sv_html = _render_plain_section_html(
                sv_main, free_text, sv_signature
            )
            section_en_html = (
                _render_plain_section_html(en_main, free_text, en_signature)
                if body_en
                else ""
            )
            html_inner = _combine_sections(
                section_sv_html, section_en_html, True
            )
            body_html = f'<div class="preview-mail">{html_inner}</div>'

            self._placeholders = placeholders
            self._missing = {
                key
                for key in (
                    _extract_placeholders(subject_rendered)
                    | _extract_placeholders(body_rendered)
                    | set(placeholders.keys())
                )
                if not str(placeholders.get(key, "")).strip()
            }
            self._subject = subject_rendered
            self._body_plain = body_rendered
            self._body_rendered = body_rendered
            self._body_html = body_html
            self._subject_label.setText(self._subject)

            self._update_status()
            self._refresh_view()
            self._info_label.setText(f"{len(self._body_rendered)} tecken")

            log.debug(
                "render_live: %s, %d tecken",
                path.name, len(self._body_rendered),
            )
        except Exception as exc:
            log.error("render_live misslyckades", exc_info=True)
            self._subject = "(Fel vid rendering)"
            self._body_plain = f"Fel: {exc}"
            self._body_rendered = self._body_plain
            self._body_html = None
            self._subject_label.setText(self._subject)
            self._update_status()
            self._refresh_view()

    def set_placeholders(self, placeholders: Dict[str, str]) -> None:
        """Uppdatera placeholder-värden."""
        self._placeholders = {
            str(k): str(v or "") for k, v in placeholders.items()
        }
        self._missing = {
            k for k, v in self._placeholders.items() if not str(v).strip()
        }
        if self._body_plain:
            self._body_rendered = _apply_placeholders_safe(
                self._body_plain, self._placeholders
            )
        self._update_status()
        self._refresh_view()

    def get_current_view(self) -> str:
        return "html" if self._radio_html.isChecked() else "plain"

    def set_view(self, view: str) -> None:
        if view == "html":
            self._radio_html.setChecked(True)
            self._plain_view.hide()
            self._html_view.show()
        else:
            self._radio_plain.setChecked(True)
            self._plain_view.show()
            self._html_view.hide()
        self._refresh_view()

    def clear(self) -> None:
        """Rensa preview."""
        self._subject = ""
        self._body_plain = ""
        self._body_html = None
        self._body_rendered = ""
        self._placeholders = {}
        self._missing = set()
        self._live_template_path = None
        self._live_include_english = False
        self._live_free_text = ""

        self._subject_label.setText("(Ingen mall vald)")
        self._info_label.setText("")
        self._plain_view.clear()
        self._html_view.clear()
        self._update_status()

        self._radio_plain.setChecked(True)
        self._plain_view.show()
        self._html_view.hide()
        log.debug("PreviewTab rensad.")

    def flash_status(self, message: str, duration_ms: int = 2500) -> None:
        """Visa tillfälligt statusmeddelande."""
        original = self._status_label.text()
        original_style = self._status_label.styleSheet()
        colors = self._c()
        self._status_label.setText(message)
        self._status_label.setStyleSheet(
            f"color: {colors.get('accent', '')}; font-weight: bold;"
        )

        def restore() -> None:
            self._status_label.setText(original)
            self._status_label.setStyleSheet(original_style)

        QTimer.singleShot(duration_ms, restore)

    # ─────────────────────────────────────────────────────────────────
    # Actions (publika metoder + klassalias för bakåtkompatibilitet)
    # ─────────────────────────────────────────────────────────────────

    def open_in_browser(self) -> None:
        if not self._body_plain and not self._body_html:
            self.flash_status("⚠️ Ingen förhandsgranskning att visa.")
            return
        try:
            html_content = self._build_browser_html()
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".html",
                delete=False,
                encoding="utf-8",
                prefix="emailapp_preview_",
            ) as handle:
                handle.write(html_content)
                temp_path = handle.name
            self._temp_files.append(temp_path)
            webbrowser.open(f"file:///{temp_path}")
            log.info("Preview i webbläsare: %s", temp_path)
            QTimer.singleShot(
                30_000, lambda path=temp_path: self._cleanup_temp(path)
            )
        except Exception as exc:
            log.error("Öppna browser misslyckades", exc_info=True)
            self.flash_status(f"❌ Kunde inte öppna webbläsare: {exc}")

    def _cleanup_temp(self, path: str) -> None:
        try:
            if os.path.exists(path):
                os.unlink(path)
            self._temp_files = [
                temp for temp in self._temp_files if temp != path
            ]
        except Exception:
            log.debug(
                "Rensning tempfil misslyckades: %s", path, exc_info=True
            )

    def copy_to_clipboard(self) -> None:
        content = (
            self._body_html
            if self._radio_html.isChecked() and self._body_html
            else self._body_rendered
        )
        if not content:
            self.flash_status("⚠️ Inget innehåll att kopiera.")
            return
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(content, QClipboard.Mode.Clipboard)
            self.flash_status("📋 Kopierat till urklipp!")
        except Exception:
            log.error("Kopiering misslyckades", exc_info=True)
            self.flash_status("❌ Kopiering misslyckades.")

    def _build_browser_html(self) -> str:
        colors = self._c()
        if self._body_html:
            body = self._body_html
        else:
            body = html_module.escape(
                self._body_rendered or self._body_plain or ""
            ).replace("\n", "<br>")

        return _PREVIEW_HTML_TEMPLATE.format(
            title=html_module.escape(self._subject[:80]),
            subject=html_module.escape(self._subject),
            body=body,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            bg=colors.get("background", colors.get("bg", "")),
            surface=colors.get("surface", ""),
            surface_alt=colors.get(
                "surface_alt", colors.get("bg_secondary", "")
            ),
            fg=colors.get("text", colors.get("fg", "")),
            fg_secondary=colors.get("text_secondary", ""),
            border=colors.get("border", ""),
            accent=colors.get("accent", ""),
            success=colors.get("success", ""),
            warning=colors.get("warning", ""),
        )

    # Bakåtkompatibla publika aliases (v4.2-API)
    _open_in_browser = open_in_browser
    _copy_to_clipboard = copy_to_clipboard


# ═══════════════════════════════════════════════════════════════════════════
# Fristående hjälpfunktioner
# ═══════════════════════════════════════════════════════════════════════════

def generate_preview_html(
    subject: str,
    body: str,
    theme_colors: Optional[Dict[str, str]] = None,
) -> str:
    """Generera HTML-sida för förhandsgranskning utan PreviewTab-instans."""
    colors = theme_colors or get_colors("light")
    return _PREVIEW_HTML_TEMPLATE.format(
        title=html_module.escape(subject[:80]),
        subject=html_module.escape(subject),
        body=body,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
        bg=colors.get("background", colors.get("bg", "")),
        surface=colors.get("surface", ""),
        surface_alt=colors.get("surface_alt", colors.get("bg_secondary", "")),
        fg=colors.get("text", colors.get("fg", "")),
        fg_secondary=colors.get("text_secondary", ""),
        border=colors.get("border", ""),
        accent=colors.get("accent", ""),
        success=colors.get("success", ""),
        warning=colors.get("warning", ""),
    )


def extract_text_from_html(html: str) -> str:
    """Extrahera ren text från HTML."""
    return _extract_text_from_html_internal(html)


__all__ = [
    "PreviewTab",
    "generate_preview_html",
    "extract_text_from_html",
]
