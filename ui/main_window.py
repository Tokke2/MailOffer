#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/main_window.py – Huvudfönster för EmailApp (PyQt6)

Version: 5.8 – TEMA-KNAPP + TYDLIGARE ÖPPNA I HISTORIK

ÄNDRINGAR mot v5.7:
- ✅ Tema-knapp 🌙/☀️ i verktygsraden (ett klick, StyleEngine.toggle)
- ✅ Historik: egen knapp «✏️ Öppna / skicka om», hint och tooltip
  (dubbelklick och högerklick finns kvar)

Version: 5.7 – VIN ENDAST I ENGELSKT MAIL (EN-mottagare)

ÄNDRINGAR mot v5.6:
- ✅ VIN-fält (::vin::) syns BARA när minst en mottagare är [EN]
- ✅ VIN skickas BARA i den engelska versionen (aldrig till SV)
- ✅ Tom VIN → raden utelämnas (ingen tom "VIN:"-rad)

ÄNDRINGAR mot v5.5:
- ✅ Efter formulärrensning (skickat mail) återställs dropdown-
    placeholders (::ruta:: = glastyp) till FÖRSTA alternativet:
    "Vindruta" – dropdownen finns kvar och är förinställd, men
    användaren kan alltid välja i menyn
    * _reset_form_after_send(): efter tömning sätts varje fält vars
      nyckel finns i PLACEHOLDER_DROPDOWNS till options[0]
    * Spara: settings "replacements_values" = {"ruta": "Vindruta"}
      → förinställningen gäller även när man byter mall
    * Övriga fält (modell/reg/kommentar/…) töms som förut

ÄNDRINGAR mot v5.4:
- ✅ MUSHJULSSKYDD installeras även från MainWindow (idempotent –
    installeras normalt av main.pyw steg 9.6 via ui/wheel_guard v1.0):
    mushjulet över dropdowns/spinnrutor/reglage/radfält skrollar
    närmaste skrollområde i stället för att ändra värdet

ÄNDRINGAR mot v5.3:
- ✅ "Inkludera engelsk version"-checkboxen BORTTAGEN (steg 1 + 
    inställningsfliken) – språket styrs helt per mottagare
- ✅ include_english härleds automatiskt i _gather_send_params:
    om någon mottagare (To ELLER Bcc) är märkt EN → engelsk version
    skickas till EN-mottagarna, alltid
- ✅ Ersatt med info-text i steg 1: "🌐 Språk per mottagare: EN får
    engelsk version, SV får svensk – skickas automatiskt"
- ✅ Placeholder-labels alltid svenska (_PH_SV)
- ✅ _on_en_toggle borttagen · historik-återställning hoppar över
    engelsk-knappen (mottagarnas språktaggar styr) · inställningen
    include_english lämnas som legacy (oanvänd)

ÄNDRINGAR mot v5.2:
- ✅ Kontakter kan ha eget språk (contacts_ui v4.4: fältet language)
    * Redigera kontakt → "🌐 Språk": 🇸🇪 Svenska / 🇬🇧 Engelska
    * Kontaktfliken visar språkkolumn (🇸🇪 SV / 🇬🇧 EN) + sortering
- ✅ När en kontakt läggs till i To/Bcc (adressboken eller
    kontaktfliken) märks den automatiskt med kontaktens språk
    * _contact_lang(email) slår upp språket i ContactStore
    * Används i _address_book_add_callback, _contacts_tab_add_to och
      fallback-adressboken – _add_recipient(..., lang=...)
    * Handinmatade mottagare får språk från dropdownen (som förut)

ÄNDRINGAR mot v5.1:
- ✅ SPRÅK PER MOTTAGARE i steg ③ (Mottagare):
    * "🌐 Språk för nya mottagare"-dropdown (SV/EN) – alla nya
      mottagare märks med valt språk
    * Varje mottagare visas med tagg: "namn@example.se [SV]" / [EN]
    * Högerklick på mottagare → "🇸🇪 Sätt svenska / 🇬🇧 Sätt engelska"
    * Dubbelklick på en mottagare växlar språk snabbt
    * _gather_send_params() skickar recipients_to_lang/bcc_lang
      → email_sender v3.9 skickar SV-gruppen svensk version och
      EN-gruppen engelsk version (även när "Inkludera engelsk
      version" är ikryssad – SV får ALDRIG engelsk)
    * Engelska av → alla får svensk version (som förut)
- ✅ SendConfirmDialog (dialogs v4.8) visar "🌐 Språk: SV n · EN n"
    + varning om EN-markerade finns men engelska är av
- ✅ Historiken sparar språktaggarna (to_lang/bcc_lang) och återställer
    dem vid "Öppna för redigering / Skicka om"

ÄNDRINGAR mot v5.0:
- ✅ STANDARDMALL: ny inställning "default_template" (settings v24.5)
    * Inställningar → ny grupp "📝 Standardmall": dropdown med alla
      mallar i Mallar/ + "(ingen – senast valda)"
    * Vid start väljs standardmallen automatiskt (om satt och finns);
      annars första mallen som förut
    * Manuella val i dropdown-menyn på Skicka-fliken VINNER alltid –
      standardmallen gäller tills användaren byter eller appen
      startas om
    * När standardmallen sparas i inställningarna appliceras den direkt
    * "🔄 Uppdatera mallista"-knapp + kombo uppdateras vid "Läs om"
    * _scan_tpls(): vid omskanning behålls användarens val om mallen
      fortfarande finns (byter inte tillbaka till första mallen)

ÄNDRINGAR mot v4.9:
- ✅ LÄSKVITTO: checkbox i SendConfirmDialog (dialogs v4.7)
    * _gather_send_params() inkluderar request_receipts (settings v24.4)
    * _confirm_send() hämtar dialogens result_params() efter bekräftelse
      → request_receipts skickas till send_email() (email_sender v3.8)
- ✅ LEVERANSBARHETS-GUIDE: ny inställningsgrupp
    * _build_settings_group_deliverability() – checkbox (standard för
      kvitton) + knapp "📖 Leveransbarhets-guide"
    * _open_deliverability_guide() → DeliverabilityGuideDialog
    * Guide: SPF/DKIM/DMARC (WebSupport), SMTP, innehållstips,
      Thunderbird-träning, kvitton
- ✅ ANTISPAM-MALL: Mallar/Offertförfrågan – anti-spam.txt (ren signatur,
    rak ämnesrad, [en]-block behålls)

Fixar mot v4.8:
- ✅ STANDARD-TO (spec): settings "default_to" – fasta To-adresser
    som alltid fylls i vid start och efter formulärrensning
    * Inställningar → Sökvägar → "Standard-To (kommaseparerat)"
    * _load_default_recipients() (ny) laddar To + Bcc + arkivkopia
    * _load_default_bcc() finns kvar som alias
- ✅ DUBBELKLICK på historikrad → "Öppna för redigering / Skicka om"
    (samma som högerklicksmenyn, v4.9)
- ✅ RENSNING sker INNAN "✅ Klart"-dialogen visas – när användaren
    stänger dialogen är alla fält redan tomma (v4.9)
- ✅ Standard-To sparas/valideras som lista (settings v24.3)

Bevarat från v4.8:
- ✅ ARKIVKOPIA: "archive_copy_email" – fast e-postadress som alltid
    får kopia (dold Bcc) på varje skickat mail
    * Inställningar → SMTP → "Arkivkopia (alltid kopia)"
    * _load_default_bcc() laddar tillbaka den efter formulärrensning
    * SendWorker._resolve_default_bcc() + _default_bcc_with_archive()
      inkluderar den (deduplicerat, case-insensitivt)
- ✅ ÖPPNA FRÅN HISTORIK (spec): högerklick på historikpost →
    "✏️ Öppna för redigering / Skicka om"
    * Återställer mall, ämne, brödtext, platshållarvärden, mottagare,
      fritext, engelska + bilagor (via sparade sökvägar)
    * Historikposter sparar nu extra data (template_name, body,
      free_text, replacements, include_english, attachment_paths)
    * Tydlig status om mall/bilagor saknas
- ✅ RENSNING: _reset_form_after_send() tömmer även ämnesraden,
    duck-typad (kraschar aldrig), visar status
- ✅ _load_default_bcc(): bus-guard (kraschar ej utan EventBus)

Bevarat från v4.6:

Flöde:
  ① Mall
  ② Bilagor/Bilder
  ③ Mottagare
  ④ Skicka mail

Fixar mot v4.5:
- ✅ Korrupt markdown/inklistringssyntax borttagen
  (__future__, __all__, _PROJECT_ROOT, _PH_SV/_PH_EN/_PH_PATTERN,
   _EMAIL_RE, _IMAGE_SUFFIXES, _PLACEHOLDER_VALUE_EN,
   _NO_TRANSLATE_PLACEHOLDERS, alla _-metoder, path.name, path.read_text,
   re.search, match.group, dialog.show, self.select_tab,
   self.settings.save, datetime.datetime.now, subprocess.run,
   self._contact_store.save, item.data, mailto.group, angle.group,
   bracket.group, plain.group, path.is_file, QMessageBox.StandardButton.No,
   namn@example.se, <title>, <body, <br, </p, <[^>]+>,
   "Bekräfta & skicka", "Drag & drop", "Bilder & bifogade filer",
   "SMTP & Avsändare", "UI & Beteende", "Loggning & drift",
   ui.tab_visibility_changed)
- ✅ BUGG: EventBus-prenumeration med lambdas (GC:as av weakrefs)
    * mail.sent / mail.failed / ui.theme_changed / module.disabled
      nådde ALDRIG fönstret
    * Nu: bundna metoder _on_mail_sent/_on_mail_failed/
      _on_theme_changed/_on_module_disabled
- ✅ BUGG: QClipboard användes men importerades inte
    * _copy_history_recipients kraschade med NameError
- ✅ BUGG: SendWorker skickade bildinställningar till send_email()
    * preserve_image_dimensions/image_jpeg_quality m.fl. – dessa finns
      nu i core/email_sender.py v3.7 (annars TypeError)
- ✅ SNABBARE: debounce av placeholder-omskapning
    * _on_editor_changed triggade _rebuild_ph vid VARJE tangenttryckning
    * Nu: QTimer 220 ms – endast när användaren pausar
- ✅ _save_tpl: .docx-mallar sparas via create_template (ej rå text)
- ✅ _set_theme applicerar temat + publicerar ui.theme_changed

Viktiga regler som uppfylls här:
- Ingen CC i UI eller sändflöde
- Bilagesteget stödjer drag and drop
- Adressboken stängs inte när användaren trycker på "Lägg till"
- Inställningsfliken visar en redigerbar sammanställning av settings
- Historik har högerklick för att visa mottagare
- QThread + pyqtSignal används för sändning
- Förhandsgranskning och skickat mail följer samma ordning
- Fritext ska ligga ovan signaturen (rendering i core.email_sender)
- Kontakter-fliken laddar om adressboken när fliken öppnas

FIL: ui/main_window.py
"""

from __future__ import annotations

# stdlib
import datetime
import inspect
import json
import logging
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


def theme_button_caption(resolved_mode: str) -> Tuple[str, str]:
    """Knapptext + tooltip för tema-knappen (🌙/☀️).

    Visar det läge man byter TILL: mörkt ger ☀️ Ljust, ljust ger 🌙 Mörkt.
    """
    mode = str(resolved_mode or "").strip().lower()
    if mode == "dark":
        return ("☀️ Ljust", "Byt till ljust tema")
    return ("🌙 Mörkt", "Byt till mörkt tema")


def history_selected_row(current_row: int, n_rows: int) -> int:
    """Returnerar giltigt radindex, annars -1."""
    try:
        row = int(current_row)
        total = int(n_rows)
    except (TypeError, ValueError):
        return -1
    if 0 <= row < total:
        return row
    return -1


def history_open_feedback(
    tpl_loaded: bool,
    tpl_name: str,
    missing_attachments: int,
) -> Tuple[str, str]:
    """Statusrad efter öppna-från-historik: (meddelande, stil)."""
    parts: List[str] = []
    name = str(tpl_name or "").strip()
    if not tpl_loaded and name:
        parts.append(f"⚠️ Mallen '{name}' saknas")
    try:
        missing = int(missing_attachments or 0)
    except (TypeError, ValueError):
        missing = 0
    if missing:
        parts.append(f"{missing} bilaga(or) saknas")
    if parts:
        return (" · ".join(parts), "warning")
    return ("✏️ Öppnad från historik – granska och skicka om", "info")


# Lägg projektroten först i importvägen innan lokala imports.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# third-party
from PyQt6.QtCore import QPoint, Qt, QThread, QTimer, QUrl, pyqtSignal, pyqtSlot
from PyQt6.QtGui import (
    QAction,
    QClipboard,
    QDesktopServices,
    QFont,
    QKeySequence,
    QShortcut,
)
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressDialog,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

# local
from core.email_sender import SendResult, send_email, test_smtp_connection
from core.i18n import get_language as i18n_get_language
from core.i18n import normalize_language
from core.i18n import set_language as i18n_set_language
from core.i18n import tr
from core.logger import get_log_file_path
from core.recovery_manager import RecoveryManager
from core.settings_manager import SettingsManager
from core.version import GITHUB_REPO_URL
from core.version import __version__ as APP_VERSION

try:
    from core.event_bus import EventBus
except Exception:  # pragma: no cover
    class EventBus:  # type: ignore[no-redef]
        def publish(self, *args: Any, **kwargs: Any) -> None:
            return None

        def subscribe(self, *args: Any, **kwargs: Any) -> None:
            return None

try:
    from ui.styles import StyleEngine, get_colors
except Exception:  # pragma: no cover
    class StyleEngine:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._theme = "dark"

        def apply(self) -> None:
            return None

        def set_theme(self, theme: str) -> None:
            self._theme = theme

        def get_theme(self) -> str:
            return str(self._theme)

        def toggle(self) -> None:
            self._theme = "light" if self._theme == "dark" else "dark"

        def get_colors(self) -> Dict[str, str]:
            return get_colors(self._theme)

    def get_colors(_theme: str = "dark") -> Dict[str, str]:  # type: ignore[no-redef]
        return {
            "accent": "#5C9EFF",
            "success": "#2ECC71",
            "warning": "#F5A623",
            "error": "#E74C3C",
            "surface": "#2A2A3E",
            "border": "#4A4A6A",
            "text": "#FFFFFF",
            "text_secondary": "#BBBBCC",
            "entry_bg": "#1E1E2E",
            "entry_fg": "#FFFFFF",
            "panel_bg": "#232336",
        }

try:
    from ui.preview import PreviewTab
except Exception:  # pragma: no cover
    PreviewTab = None  # type: ignore[assignment]

try:
    from ui.dialogs import SendConfirmDialog, DeliverabilityGuideDialog
except Exception:  # pragma: no cover
    SendConfirmDialog = None  # type: ignore[assignment]
    DeliverabilityGuideDialog = None  # type: ignore[assignment]

try:
    from script.recipients import (
        _StoreAdapter,
        AddContactDialog,
        AddressBookDialog,
        ContactStore,
        validate_email_address,
    )
except Exception:  # pragma: no cover
    _StoreAdapter = None  # type: ignore[assignment]
    AddContactDialog = None  # type: ignore[assignment]
    AddressBookDialog = None  # type: ignore[assignment]
    ContactStore = None  # type: ignore[assignment]

    def validate_email_address(email: str) -> bool:  # type: ignore[no-redef]
        return bool(
            re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email or "").strip())
        )

try:
    from script.contacts_ui import ContactsTab as ContactsTabUI
    from script.contacts_ui import ContactStore as ContactsStoreUI
except Exception:  # pragma: no cover
    ContactsTabUI = None  # type: ignore[assignment]
    ContactsStoreUI = None  # type: ignore[assignment]

log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# Konstanter och hjälpdata
# ═══════════════════════════════════════════════════════════════════════════

PLACEHOLDER_DROPDOWNS: Dict[str, List[str]] = {
    "ruta": [
        "Vindruta",
        "Bakruta",
        "Höger sidoruta fram",
        "Vänster sidoruta fram",
        "Höger sidoruta bak",
        "Vänster sidoruta bak",
        "Höger ventilationsruta",
        "Vänster ventilationsruta",
        "Höger kvarts-/hörn-ruta",
        "Vänster kvarts-/hörn-ruta",
        "Taklucka / Panoramatak",
        "Vindruteglas (laminerad)",
        "Vindruteglas (härdad)",
    ],
}

_PH_SV: Dict[str, str] = {
    "ruta": "🪟 Glastyp",
    "modell": "🚗 Bilmodell",
    "reg": "🔢 Reg.nummer",
    "vin": "🔢 VIN (obligatoriskt för EN)",
    "kommentar": "💬 Kommentar",
    "name": "👤 Namn",
    "email": "📧 E-post",
    "company": "🏢 Företag",
    "date": "📅 Datum",
    "order_id": "📋 Ordernr",
    "price": "💰 Pris",
    "delivery": "🚚 Leverans",
}

_PH_EN: Dict[str, str] = {
    "ruta": "🪟 Glass type",
    "modell": "🚗 Car model",
    "reg": "🔢 Reg. number",
    "vin": "🔢 VIN (English only)",
    "kommentar": "💬 Comment",
    "name": "👤 Name",
    "email": "📧 Email",
    "company": "🏢 Company",
    "date": "📅 Date",
    "order_id": "📋 Order no.",
    "price": "💰 Price",
    "delivery": "🚚 Delivery",
}

_PH_PATTERN = re.compile(
    r"\(\(([^)]+)\)\)|::([^:]+)::|\{([^}]+)\}", re.IGNORECASE
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# (v5.2) Språktagg på mottagare: "namn@example.se [SV]" / "[EN]"
_LANG_TAG_RE = re.compile(r"\s*\[(SV|EN)\]\s*$", re.IGNORECASE)


def _lang_tag(lang: str) -> str:
    """Språktagg för mottagarlistor: [SV] eller [EN]."""
    return "[EN]" if str(lang or "").lower() == "en" else "[SV]"


def _strip_lang_tag(text: str) -> str:
    """Ta bort språktaggen från en mottagartext (behåller e-posten)."""
    return _LANG_TAG_RE.sub("", str(text or "")).strip()

_IMAGE_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff",
}

_PLACEHOLDER_VALUE_EN: Dict[str, Dict[str, str]] = {
    "ruta": {
        "vindruta": "Windshield",
        "bakruta": "Rear window",
        "höger sidoruta fram": "Front right door glass",
        "vänster sidoruta fram": "Front left door glass",
        "höger sidoruta bak": "Rear right door glass",
        "vänster sidoruta bak": "Rear left door glass",
        "höger ventilationsruta": "Right vent glass",
        "vänster ventilationsruta": "Left vent glass",
        "höger kvarts-/hörn-ruta": "Right quarter glass",
        "vänster kvarts-/hörn-ruta": "Left quarter glass",
        "taklucka / panoramatak": "Sunroof / panoramic roof glass",
        "vindruteglas (laminerad)": "Laminated windshield glass",
        "vindruteglas (härdad)": "Tempered windshield glass",
        "sidoruta höger fram": "Front right door glass",
        "sidoruta vänster fram": "Front left door glass",
        "sidoruta högidoruta vänster bak": "Rear left door glass",
        "höger framruta": "Front right door glass",
        "vänster framruta": "Front left door glass",
        "höger bakruta": "Rear right door glass",
        "vänster bakruta": "Rear left door glass",
        "panoramatak": "Panoramic roof glass",
        "taklucka": "Sunroof glass",
    }
}

# Platshållare som bara hör till [en]-mailet (UI + sändning)
EN_ONLY_PLACEHOLDERS = frozenset({"vin"})

# (v5.4) Flikalias för select_tab(): nyckel + SV/EN-namn ger samma flik
# oavsett UI-språk (tray.py anropar fortfarande med svenskt namn).
_TAB_ALIASES: Dict[str, str] = {
    "send": "send", "skicka": "send",
    "contacts": "contacts", "kontakter": "contacts",
    "templates": "templates", "mallar": "templates",
    "preview": "preview", "förhandsgranskning": "preview",
    "history": "history", "historik": "history",
    "logs": "logs", "loggar": "logs", "logg": "logs",
    "settings": "settings", "inställningar": "settings",
}


def vin_required_missing(
    replacements: Dict[str, str], include_english: bool
) -> bool:
    """True om EN-mottagare finns och VIN är tomt (då får man inte skicka)."""
    if not include_english:
        return False
    vin = ""
    for key, value in (replacements or {}).items():
        if str(key).lower() == "vin":
            vin = str(value or "").strip()
            break
    return not vin

_NO_TRANSLATE_PLACEHOLDERS = {
    "reg",
    "vin",
    "registration",
    "registreringsnummer",
    "email",
    "e-post",
    "order_id",
    "ordernr",
}


# ═══════════════════════════════════════════════════════════════════════════
# Översättningshjälpare
# ═══════════════════════════════════════════════════════════════════════════

def _translate(text: str) -> str:
    """sv→en med fallback-kedja."""
    if not text.strip():
        return text
    for module_name in ("deep_translator", "googletrans"):
        try:
            if module_name == "deep_translator":
                from deep_translator import GoogleTranslator  # type: ignore
                result = GoogleTranslator(
                    source="sv", target="en"
                ).translate(text)
            else:
                from googletrans import Translator  # type: ignore
                result = Translator().translate(
                    text, src="sv", dest="en"
                ).text
            if result:
                return str(result)
        except ImportError:
            continue
        except Exception:
            log.warning(
                "Översättning via %s misslyckades",
                module_name, exc_info=True,
            )
    return text


def _translate_placeholder_value(key: str, value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return text
    key_l = str(key or "").strip().lower()
    if key_l in _NO_TRANSLATE_PLACEHOLDERS:
        return text
    mapped = _PLACEHOLDER_VALUE_EN.get(key_l, {}).get(text.lower())
    if mapped:
        return mapped
    if key_l in {"modell", "model", "name", "namn", "company", "företag"}:
        return text
    return _translate(text)


# ═══════════════════════════════════════════════════════════════════════════
# Övriga småhjälpare
# ═══════════════════════════════════════════════════════════════════════════

def _dedupe(values: Iterable[str]) -> List[str]:
    seen: set = set()
    out: List[str] = []
    for raw in values:
        value = str(raw or "").strip()
        if not value:
            continue
        key = value.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _looks_like_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


def _is_image(path: str) -> bool:
    return Path(path).suffix.lower() in _IMAGE_SUFFIXES


def _clean_email(value: object) -> str:
    text = str(value or "").strip()
    mailto = re.search(r"mailto:([^\)\]\s>]+)", text, re.IGNORECASE)
    if mailto:
        return mailto.group(1).strip()
    angle = re.search(r"<([^<>\s]+@[^<>\s]+)>", text)
    if angle:
        return angle.group(1).strip()
    bracket = re.search(r"\[([^\]\s]+@[^\]\s]+)\]", text)
    if bracket:
        return bracket.group(1).strip()
    plain = re.search(r"[^\s<>\(\)\[\]]+@[^\s<>\(\)\[\]]+", text)
    return plain.group(0).strip() if plain else text


def _attachment_key(path: str) -> str:
    try:
        return str(Path(path).resolve()).lower()
    except Exception:
        return str(path).strip().lower()


# ═══════════════════════════════════════════════════════════════════════════
# Fallback preview om ui.preview saknas
# ═══════════════════════════════════════════════════════════════════════════

class _FallbackPreviewTab(QWidget):
    """Enkel fallback-preview om riktig PreviewTab inte finns tillgänglig."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        self._subject = QLabel("(ingen preview ännu)")
        self._subject.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(self._subject)
        self._body = QPlainTextEdit()
        self._body.setReadOnly(True)
        layout.addWidget(self._body, stretch=1)

    def render(
        self,
        subject: str,
        body_plain: str,
        body_html: Optional[str] = None,
        placeholders: Optional[Dict[str, str]] = None,
    ) -> None:
        del body_html, placeholders
        self._subject.setText(subject or "(utan ämne)")
        self._body.setPlainText(body_plain or "")


# ═══════════════════════════════════════════════════════════════════════════
# Drag & drop-lista för bilagor
# ═══════════════════════════════════════════════════════════════════════════

class AttachmentDropListWidget(QListWidget):
    """QListWidget med drag-and-drop för filer i bilagesteget."""

    filesDropped = pyqtSignal(list)

    def __init__(
        self, colors: Dict[str, str], parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._colors = dict(colors)
        self.setAcceptDrops(True)
        self.setDragEnabled(False)
        self.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.setMinimumHeight(150)
        self._drag_active = False
        self._apply_drop_style()

    def set_theme_colors(self, colors: Dict[str, str]) -> None:
        self._colors = dict(colors)
        self._apply_drop_style()

    def _apply_drop_style(self) -> None:
        border = (
            self._colors.get("accent", "#5C9EFF")
            if self._drag_active
            else self._colors.get("border", "#4A4A6A")
        )
        surface = self._colors.get(
            "panel_bg", self._colors.get("surface", "#232336")
        )
        text = self._colors.get("text", "#FFFFFF")
        self.setStyleSheet(
            f"QListWidget {{"
            f"border: 2px dashed {border}; border-radius: 10px; "
            f"background: {surface}; color: {text}; padding: 6px;"
            f"}}"
        )

    def dragEnterEvent(self, event: Any) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self._drag_active = True
            self._apply_drop_style()
        else:
            event.ignore()

    def dragMoveEvent(self, event: Any) -> None:  # noqa: N802
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event: Any) -> None:  # noqa: N802
        self._drag_active = False
        self._apply_drop_style()
        event.accept()

    def dropEvent(self, event: Any) -> None:  # noqa: N802
        self._drag_active = False
        self._apply_drop_style()
        if not event.mimeData().hasUrls():
            event.ignore()
            return

        paths: List[str] = []
        for url in event.mimeData().urls():
            if url.isLocalFile():
                local_path = url.toLocalFile().strip()
                if local_path:
                    paths.append(local_path)

        if paths:
            self.filesDropped.emit(paths)
            event.acceptProposedAction()
        else:
            event.ignore()


# ═══════════════════════════════════════════════════════════════════════════
# QThread för sändning
# ═══════════════════════════════════════════════════════════════════════════

class SendWorker(QThread):
    """Trådsäker sändning via QThread + pyqtSignal."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(
        self, settings: SettingsManager, params: Dict[str, Any]
    ) -> None:
        super().__init__()
        self.s = settings
        self.p = params

    def _resolve_default_bcc(self) -> List[str]:
        """Standard-Bcc + arkivkopia (deduplicerat, v4.7)."""
        default_bcc = list(
            self.p.get("default_bcc")
            or self.s.get("default_bcc", [])
            or []
        )
        archive = str(self.s.get("archive_copy_email", "") or "").strip()
        if archive:
            lowered = {str(email).lower() for email in default_bcc}
            if archive.lower() not in lowered:
                default_bcc.append(archive)
        return default_bcc

    def run(self) -> None:
        try:
            include_english = bool(self.p.get("include_english", False))
            replacements_sv = dict(self.p.get("replacements", {}))
            replacements_en = {
                key: _translate_placeholder_value(str(key), value)
                for key, value in replacements_sv.items()
            }

            image_settings = {}
            getter = getattr(self.s, "image_compression_settings", None)
            if callable(getter):
                try:
                    image_settings = dict(getter())
                except Exception:
                    image_settings = {}

            kwargs = dict(
                smtp_server=self.s.get("smtp_server"),
                smtp_port=self.s.get("smtp_port"),
                sender_email=self.s.get("sender_email"),
                sender_name=self.s.get("sender_name"),
                username=self.s.get("username"),
                password=self.s.get("password"),
                word_file_path=self.p.get("template_path", ""),
                replacements=replacements_sv,
                include_english=include_english,
                recipients_to=self.p.get("recipients_to", []),
                recipients_bcc=self.p.get("recipients_bcc", []),
                # (v5.2) Språk per mottagare (email_sender v3.9)
                recipients_to_lang=(
                    self.p.get("recipients_to_lang") or None
                ),
                recipients_bcc_lang=(
                    self.p.get("recipients_bcc_lang") or None
                ),
                attachments=self.p.get("attachments", []),
                free_text=self.p.get("free_text", ""),
                validate_recipients=self.s.get(
                    "validate_recipients", False
                ),
                skip_invalid_recipients=self.s.get(
                    "skip_invalid_recipients", True
                ),
                bcc_batch_size=self.s.get("bcc_batch_size", 0) or None,
                delay_between_batches=self.s.get(
                    "delay_between_batches", 0.5
                ),
                max_retries=self.s.get("max_retries", 2),
                timeout=self.s.get("smtp_timeout", 30),
                generate_html_from_plain=self.s.get(
                    "generate_html_from_plain", True
                ),
                own_email=(
                    self.s.get_own_email()
                    if hasattr(self.s, "get_own_email")
                    else self.s.get("own_email", "")
                ),
                reply_to=(
                    self.s.get_reply_to()
                    if hasattr(self.s, "get_reply_to")
                    else self.s.get("reply_to", "")
                ),
                # Standard-Bcc + arkivkopia (v4.7): fast adress som
                # alltid får kopia (dold Bcc) på varje skickat mail.
                default_bcc=self._resolve_default_bcc(),
                translate_placeholders=(
                    self.s.should_translate_placeholders()
                    if hasattr(self.s, "should_translate_placeholders")
                    else self.s.get("translate_placeholders", True)
                ),
                # v5.0 – leverans-/läskvitto (email_sender v3.8)
                request_receipts=bool(
                    self.p.get("request_receipts", False)
                ),
                dry_run=False,
                on_progress=lambda current, total, message: (
                    self.progress.emit(current, total, message)
                ),
            )
            # v3.7: bildinställningar (compress_images m.fl.) – alla
            # nycklar accepteras nu av core.email_sender.send_email()
            kwargs.update(image_settings)

            try:
                signature = inspect.signature(send_email)
                if "replacements_en" in signature.parameters:
                    kwargs["replacements_en"] = replacements_en
                elif "english_replacements" in signature.parameters:
                    kwargs["english_replacements"] = replacements_en
            except Exception:
                pass

            result = send_email(**kwargs)
            self.finished.emit(result)
        except Exception as exc:
            log.exception("SendWorker misslyckades")
            self.error.emit(str(exc))


class UpdateWorker(QThread):
    """(v5.4) GitHub-uppdatering i bakgrunden: "check" eller "install".

    Samma mönster som SendWorker (QThread + pyqtSignal) så att UI:t
    aldrig fryser under nätverk/nedladdning.
    """

    checked = pyqtSignal(object)    # core.github_update.UpdateInfo
    installed = pyqtSignal(object)  # dict från apply_github_update
    failed = pyqtSignal(str)

    def __init__(
        self,
        mode: str,
        info: Any = None,
        base_dir: Optional[Path] = None,
    ) -> None:
        super().__init__()
        self._mode = str(mode or "check")
        self._info = info
        self._base_dir = base_dir

    def run(self) -> None:
        try:
            from core.github_update import apply_github_update, check_for_update

            if self._mode == "install":
                result = apply_github_update(
                    self._info, Path(self._base_dir or _PROJECT_ROOT)
                )
                self.installed.emit(result)
            else:
                self.checked.emit(check_for_update())
        except Exception as exc:
            log.warning(
                "UpdateWorker (%s) misslyckades", self._mode, exc_info=True
            )
            self.failed.emit(str(exc))


# ═══════════════════════════════════════════════════════════════════════════
# MainWindow
# ═══════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """Huvudfönster för EmailApp (PyQt6), enkel 4-stegs wizard utan CC."""

    def __init__(
        self,
        settings: SettingsManager,
        event_bus: EventBus,
        recovery: RecoveryManager,
    ) -> None:
        super().__init__()
        self.settings = settings
        self.bus = event_bus
        self.recovery = recovery

        self._tray_ref: Optional[Any] = None
        self._ph_inputs: Dict[str, QWidget] = {}
        self._ph_row_widgets: Dict[str, Tuple[QWidget, ...]] = {}
        self._attachments: List[str] = []
        self._last_tpl: Optional[Path] = None
        self._worker: Optional[SendWorker] = None
        self._last_send_params: Dict[str, Any] = {}
        self._view_actions: List[QAction] = []
        self._history_rows: List[Dict[str, Any]] = []
        self._settings_widgets: Dict[str, QWidget] = {}
        # (v5.4) Språkoberoende fliknycklar i tab-ordning (se _load_tabs)
        self._tab_keys: List[str] = []
        # (v5.4) GitHub-uppdatering (bakgrundstråd + pending-info)
        self._update_worker: Optional[UpdateWorker] = None
        self._update_check_manual = False
        self._pending_update_info: Any = None
        self._update_progress: Optional[QProgressDialog] = None

        self._style = StyleEngine(settings, event_bus)
        self._style.apply()

        self._contact_store: Optional[Any] = None
        _contact_store_cls = ContactsStoreUI or ContactStore
        if _contact_store_cls is not None:
            try:
                self._contact_store = _contact_store_cls(
                    self._contacts_path(), event_bus=self.bus
                )
            except TypeError:
                try:
                    self._contact_store = _contact_store_cls(
                        self._contacts_path()
                    )
                except Exception:
                    log.warning(
                        "Kunde inte initiera ContactStore", exc_info=True
                          )
                    self._contact_store = None
            except Exception:
                log.warning(
                    "Kunde inte initiera ContactStore", exc_info=True
                )
                self._contact_store = None

        # (v5.4) UI-språket (sv/en) måste sättas INNAN UI:t byggs –
        # alla tr()-anrop under _build_ui använder valt språk.
        try:
            _lang = (
                settings.get_ui_language()
                if hasattr(settings, "get_ui_language")
                else str(settings.get("language", "sv") or "sv")
            )
        except Exception:
            _lang = "sv"
        i18n_set_language(_lang)

        self._build_ui()
        self._install_shortcuts()
        self._bind_events()
        self._restore_geo()

        # (v5.4) Tyst GitHub-uppdateringssökning strax efter start
        # (respekterar auto_update_check + max 1 gång/dygn).
        QTimer.singleShot(4000, self._maybe_auto_check_update)

        # (v5.5) Muskjulsskydd – idempotent (main.pyw installerar normalt)
        try:
            from ui.wheel_guard import install_wheel_guard

            install_wheel_guard()
        except Exception:
            log.debug(
                "wheel_guard ej tillgänglig här", exc_info=True
            )

    # ────────────────────────────────────────────────────────────────
    # Grundläggande hjälpmetoder
    # ────────────────────────────────────────────────────────────────

    def set_tray(self, tray: Any) -> None:
        self._tray_ref = tray

    def _c(self) -> Dict[str, str]:
        return self._style.get_colors()

    def _base_dir(self) -> Path:
        return Path(getattr(self.settings, "base_dir", _PROJECT_ROOT))

    def _contacts_path(self) -> Path:
        return (
            self._base_dir()
            / str(self.settings.get("address_dir", "adresslistor"))
            / "contacts.json"
        )

    # ────────────────────────────────────────────────────────────────
    # UI – skal
    # ────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        self.setWindowTitle(tr("app.window_title"))
        self.setMinimumSize(1080, 760)

        central = QWidget()
        central.setProperty("cssClass", "appRoot")
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self._build_toolbar(layout)

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.tabs.tabBar().customContextMenuRequested.connect(
            self._tab_ctx
        )
        self.tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tabs, stretch=1)

        self._build_menubar()
        self._build_statusbar()
        self._load_tabs()

    def _build_toolbar(self, parent: QVBoxLayout) -> None:
        toolbar_frame = QFrame()
        toolbar_frame.setProperty("cssClass", "hero")
        toolbar = QHBoxLayout(toolbar_frame)
        toolbar.setContentsMargins(16, 12, 16, 12)
        toolbar.setSpacing(10)

        title = QLabel("📧 E-postofferten")
        title.setStyleSheet(
            "font-size: 16pt; font-weight: bold; background: transparent; "
            "color: #FFFFFF;"
        )
        toolbar.addWidget(title)

        subtitle = QLabel(tr("app.tagline_steps"))
        subtitle.setStyleSheet(
            "background: transparent; color: #FFFFFF; font-weight: bold;"
        )
        toolbar.addWidget(subtitle, stretch=1)

        self.btn_send = QPushButton(tr("toolbar.send"))
        self.btn_send.setProperty("cssClass", "send")
        self.btn_send.clicked.connect(self._send)
        toolbar.addWidget(self.btn_send)

        # (v5.4) Mall-wizard + donation direkt i verktygsraden
        btn_wizard = QPushButton(tr("toolbar.new_template"))
        btn_wizard.setProperty("cssClass", "back")
        btn_wizard.clicked.connect(self._open_template_wizard)
        toolbar.addWidget(btn_wizard)

        btn_donate = QPushButton(tr("toolbar.donate"))
        btn_donate.setProperty("cssClass", "back")
        btn_donate.clicked.connect(self._open_donate)
        toolbar.addWidget(btn_donate)

        self.btn_theme = QPushButton()
        self.btn_theme.setProperty("cssClass", "back")
        self.btn_theme.clicked.connect(self._on_theme_button_clicked)
        self._update_theme_button()
        toolbar.addWidget(self.btn_theme)

        btn_settings = QPushButton(tr("toolbar.settings"))
        btn_settings.setProperty("cssClass", "back")
        btn_settings.clicked.connect(self._open_settings)
        toolbar.addWidget(btn_settings)

        parent.addWidget(toolbar_frame)

    def _build_menubar(self) -> None:
        bar = self.menuBar()

        file_menu = bar.addMenu(tr("menu.file"))
        act_send = file_menu.addAction(tr("menu.send_mail"))
        act_send.setShortcut(QKeySequence("Ctrl+Return"))
        act_send.triggered.connect(self._send)
        # (v5.4) Skapa ny mall steg för steg
        file_menu.addAction(
            tr("menu.new_template_wizard")
        ).triggered.connect(self._open_template_wizard)
        file_menu.addAction(tr("menu.save_template")).triggered.connect(self._save_tpl)
        file_menu.addAction(
            tr("menu.backup_lists")
        ).triggered.connect(self._backup_lists_dialog)
        file_menu.addSeparator()
        # (v5.4) Manuell uppdateringssökning mot GitHub Releases
        file_menu.addAction(
            tr("menu.check_updates")
        ).triggered.connect(lambda: self._check_updates(manual=True))
        file_menu.addAction(
            tr("menu.update_from_folder")
        ).triggered.connect(self._update_from_folder_dialog)
        file_menu.addSeparator()
        act_quit = file_menu.addAction(tr("menu.quit"))
        act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        act_quit.triggered.connect(self._quit_app)

        self._view_menu = bar.addMenu(tr("menu.view"))

        theme_menu = bar.addMenu(tr("menu.theme"))
        for label, mode in (
            (tr("menu.theme_dark"), "dark"),
            (tr("menu.theme_light"), "light"),
            (tr("menu.theme_system"), "system"),
        ):
            action = theme_menu.addAction(label)
            action.triggered.connect(
                lambda checked=False, selected=mode: self._set_theme(selected)
            )

        # (v5.4) UI-språk sv/en (omstart erbjuds vid byte)
        language_menu = bar.addMenu(tr("menu.language"))
        for label, code in (
            (tr("language.sv"), "sv"),
            (tr("language.en"), "en"),
        ):
            action = language_menu.addAction(label)
            action.setCheckable(True)
            action.setChecked(i18n_get_language() == code)
            action.triggered.connect(
                lambda checked=False, lang=code: self._set_ui_language(lang)
            )

        help_menu = bar.addMenu(tr("menu.help"))
        help_menu.addAction(tr("menu.deliverability")).triggered.connect(
            self._open_deliverability_guide
        )
        help_menu.addAction(tr("menu.check_updates")).triggered.connect(
            lambda: self._check_updates(manual=True)
        )
        help_menu.addAction(tr("menu.donate")).triggered.connect(self._open_donate)
        help_menu.addSeparator()
        help_menu.addAction(tr("menu.about")).triggered.connect(self._show_about)

    def _build_statusbar(self) -> None:
        self._sb = QStatusBar()
        self.setStatusBar(self._sb)

        self._sb_label = QLabel(tr("app.ready"))
        self._sb_label.setStyleSheet(
            "color: #FFFFFF; font-weight: bold; font-size: 10pt;"
        )
        self._sb.addWidget(self._sb_label, stretch=1)

        self._sb_time = QLabel("")
        self._sb_time.setStyleSheet("color: #FFFFFF; font-size: 9pt;")
        self._sb.addPermanentWidget(self._sb_time)

        self._sb_timer = QTimer(self)
        self._sb_timer.setSingleShot(True)
        self._sb_timer.timeout.connect(self._status_reset)
        self._status_reset()

    def _load_tabs(self) -> None:
        # (v5.4) _tab_keys[i] = språkoberoende nyckel för flik i –
        # används av select_tab/_on_tab_changed i stället för synlig
        # (översatt) fliktext. ORDNINGEN måste matcha addTab nedan.
        self._tab_keys = [
            "send", "contacts", "templates", "preview",
            "history", "logs", "settings",
        ]
        self.tabs.addTab(self._build_send_wizard_tab(), tr("tab.send"))
        self.tabs.addTab(self._build_contacts_tab(), tr("tab.contacts"))
        self.tabs.addTab(self._build_template_tools_tab(), tr("tab.templates"))

        if PreviewTab is not None:
            try:
                self.preview_tab = PreviewTab(
                    event_bus=self.bus, theme_engine=self._style
                )  # type: ignore[misc]
            except Exception:
                log.warning(
                    "PreviewTab kunde inte initieras – använder fallback",
                    exc_info=True,
                )
                self.preview_tab = _FallbackPreviewTab()
        else:
            self.preview_tab = _FallbackPreviewTab()
        self.tabs.addTab(self.preview_tab, tr("tab.preview"))

        self.tabs.addTab(self._build_history_tab(), tr("tab.history"))
        self.tabs.addTab(self._build_log_tab(), tr("tab.logs"))
        self.tabs.addTab(self._build_settings_tab(), tr("tab.settings"))

        self._build_view_menu()

    def _build_view_menu(self) -> None:
        self._view_menu.clear()
        self._view_actions.clear()
        for index in range(self.tabs.count()):
            text = self.tabs.tabText(index)
            action = self._view_menu.addAction(text)
            action.setCheckable(True)
            action.setChecked(self.tabs.isTabVisible(index))
            action.triggered.connect(
                lambda checked, idx=index: self._set_tab_visible(
                    idx, checked
                )
            )
            self._view_actions.append(action)
        self._view_menu.addSeparator()
        self._view_menu.addAction(tr("menu.show_all_tabs")).triggered.connect(
            self._restore_tabs
        )

    def _sync_view_menu(self) -> None:
        for index, action in enumerate(self._view_actions):
            if index < self.tabs.count():
                action.blockSignals(True)
                action.setChecked(self.tabs.isTabVisible(index))
                action.blockSignals(False)

    def _set_tab_visible(self, index: int, visible: bool) -> None:
        visible_count = sum(
            1
            for i in range(self.tabs.count())
            if self.tabs.isTabVisible(i)
        )
        if not visible and visible_count <= 1:
            QMessageBox.warning(
                self, "Minst en tab", "Minst en tab måste vara synlig."
            )
            self._sync_view_menu()
            return
        self.tabs.setTabVisible(index, visible)
        self.bus.publish(
            "ui.tab_visibility_changed",
            {
                "tab_key": self.tabs.tabText(index),
                "visible": visible,
            },
        )
        self._sync_view_menu()

    def _restore_tabs(self) -> None:
        for index in range(self.tabs.count()):
            self.tabs.setTabVisible(index, True)
        self._sync_view_menu()

    def _tab_ctx(self, pos: QPoint) -> None:
        index = self.tabs.tabBar().tabAt(pos)
        if index < 0:
            return
        menu = QMenu(self)
        action = menu.addAction(tr("menu.hide_tab"))
        action.triggered.connect(
            lambda: self._set_tab_visible(index, False)
        )
        menu.exec(self.tabs.tabBar().mapToGlobal(pos))

    def select_tab(self, name: str) -> None:
        """Välj flik via nyckel ("send"), SV-namn eller EN-namn.

        (v5.4) Språkoberoende: fliktexterna är översatta, så matchning
        sker först mot _TAB_ALIASES + _tab_keys och först därefter mot
        synlig text (bakåtkompatibilitet, t.ex. tray.py:s svenska anrop).
        """
        needle = str(name or "").strip().lower()
        key = _TAB_ALIASES.get(needle)
        keys = getattr(self, "_tab_keys", []) or []
        if key is not None and key in keys:
            index = keys.index(key)
            if index < self.tabs.count():
                self.tabs.setCurrentIndex(index)
                return
        for index in range(self.tabs.count()):
            if needle and needle in self.tabs.tabText(index).lower():
                self.tabs.setCurrentIndex(index)
                return

    def _install_shortcuts(self) -> None:
        """Tangentbord: Ctrl+Enter skicka, F5 preview, Ctrl+S, Ctrl+K, Ctrl+1–4, Ctrl+Q."""
        pairs = [
            ("Ctrl+Return", self._send),
            ("Ctrl+Enter", self._send),
            ("F5", lambda: (self.select_tab("preview"), self._refresh_preview())),
            ("Ctrl+S", self._save_tpl),
            ("Ctrl+K", self._focus_contact_search),
            ("Ctrl+1", lambda: self._jump_wizard_step(0)),
            ("Ctrl+2", lambda: self._jump_wizard_step(1)),
            ("Ctrl+3", lambda: self._jump_wizard_step(2)),
            ("Ctrl+4", lambda: self._jump_wizard_step(3)),
            ("Ctrl+Q", self._quit_app),
        ]
        self._shortcuts: List[Any] = []
        for seq, slot in pairs:
            try:
                sc = QShortcut(QKeySequence(seq), self)
                sc.setContext(Qt.ShortcutContext.WindowShortcut)
                sc.activated.connect(slot)
                self._shortcuts.append(sc)
            except Exception:
                log.debug("Kunde inte binda %s", seq, exc_info=True)

    def _jump_wizard_step(self, index: int) -> None:
        self.select_tab("send")
        steps = getattr(self, "_wizard_steps", []) or []
        if index < 0 or index >= len(steps):
            return
        widget = steps[index]
        scroll = getattr(self, "_wizard_scroll", None)
        try:
            if scroll is not None and hasattr(scroll, "ensureWidgetVisible"):
                scroll.ensureWidgetVisible(widget)
        except Exception:
            pass
        try:
            widget.setFocus()
        except Exception:
            pass

    def _focus_contact_search(self) -> None:
        self.select_tab("contacts")
        line = getattr(self, "_contacts_search", None)
        if line is None:
            tab = getattr(self, "_contacts_tab", None)
            if tab is not None:
                line = tab.findChild(QLineEdit)
        if line is not None:
            try:
                line.setFocus()
                line.selectAll()
            except Exception:
                pass

    def _quit_app(self) -> None:
        if self._tray_ref is not None and hasattr(self._tray_ref, "_do_quit"):
            try:
                self._tray_ref._do_quit()
                return
            except Exception:
                log.debug("tray._do_quit misslyckades", exc_info=True)
        self.close()

    def _backup_lists_dialog(self) -> None:
        dest = QFileDialog.getExistingDirectory(
            self, "Välj mapp för säkerhetskopia av adresslistor"
        )
        if not dest:
            return
        try:
            from core.user_backup import backup_address_lists_to

            path = backup_address_lists_to(self._base_dir(), Path(dest))
        except Exception as exc:
            QMessageBox.warning(self, "Säkerhetskopia", str(exc))
            return
        if path is None:
            QMessageBox.information(
                self,
                "Säkerhetskopia",
                "Ingen adresslista att kopiera (mappen adresslistor saknas eller är tom).",
            )
            return
        QMessageBox.information(
            self, "Säkerhetskopia", "Adresslistor kopierade till:\n%s" % path
        )
        self._status("📦 Adresslistor säkerhetskopierade", "success")

    def _update_from_folder_dialog(self) -> None:
        src = QFileDialog.getExistingDirectory(
            self, "Välj mapp med ny app-version (endast kod kopieras)"
        )
        if not src:
            return
        reply = QMessageBox.question(
            self,
            "Uppdatera app",
            "Kopiera kod från:\n%s\n\n"
            "JSON, adresslistor och inställningar rörs inte."
            % src,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            from core.app_update import apply_update_from_dir

            result = apply_update_from_dir(Path(src), self._base_dir())
        except Exception as exc:
            QMessageBox.critical(self, "Uppdatering", str(exc))
            return
        copied = len(result.get("copied") or [])
        skipped = len(result.get("skipped") or [])
        errors = result.get("errors") or []
        msg = "Kopierade %d filer.\nHoppade över %d (JSON/settings/data).\n" % (
            copied,
            skipped,
        )
        if errors:
            msg += "Fel:\n" + "\n".join(str(e) for e in errors[:8])
            QMessageBox.warning(self, "Uppdatering", msg)
        else:
            QMessageBox.information(self, "Uppdatering", msg)
        self._status("⬇️ App-uppdatering klar (%d filer)" % copied, "success")

    # ────────────────────────────────────────────────────────────────
    # (v5.4) Mall-wizard
    # ────────────────────────────────────────────────────────────────

    def _templates_dir(self) -> Path:
        """Mallmappen enligt inställningen template_dir."""
        return self._base_dir() / str(
            self.settings.get("template_dir", "Mallar")
        )

    def _open_template_wizard(self) -> None:
        """Öppna wizarden för att skapa en ny mall (ui/template_wizard)."""
        try:
            from ui.template_wizard import TemplateWizard
        except Exception:
            log.warning("Mall-wizarden kunde inte laddas", exc_info=True)
            QMessageBox.warning(self, tr("wizard.title"), tr("wizard.error.title"))
            return
        wizard = TemplateWizard(
            self,
            templates_dir=self._templates_dir(),
            existing_names=self._template_names(),
            translate_func=_translate,
        )
        if wizard.exec() != QDialog.DialogCode.Accepted or not wizard.created_path:
            return
        created = wizard.created_path
        self._scan_tpls()
        self._refresh_default_template_combo()
        self._refresh_template_tools_list()
        if wizard.set_as_default:
            try:
                if hasattr(self.settings, "set_default_template"):
                    self.settings.set_default_template(created.name)
                else:
                    self.settings.set("default_template", created.name)
                self.settings.save()
                self._refresh_default_template_combo()
            except Exception:
                log.debug(
                    "Kunde inte sätta standardmall efter wizarden", exc_info=True
                )
        if wizard.select_after and hasattr(self, "_tpl_combo"):
            idx = self._tpl_combo.findText(created.name)
            if idx >= 0:
                self._tpl_combo.setCurrentIndex(idx)
                self._on_tpl_sel(created.name)
            self.select_tab("send")
        self._status(tr("wizard.created_status", name=created.name), "success")

    # ────────────────────────────────────────────────────────────────
    # (v5.4) Uppdatering från GitHub Releases (auto + manuellt)
    # ────────────────────────────────────────────────────────────────

    def _maybe_auto_check_update(self) -> None:
        """Tyst autosökning vid start – max 1 gång/dygn, bara om aktiverad."""
        try:
            if not bool(self.settings.get("auto_update_check", True)):
                return
            from core.github_update import should_auto_check

            if not should_auto_check(self.settings.get("last_update_check", "")):
                return
        except Exception:
            log.debug("Autosökning av uppdatering hoppades över", exc_info=True)
            return
        self._check_updates(manual=False)

    def _check_updates(self, manual: bool = True) -> None:
        """Starta uppdateringssökning i bakgrunden (knapp/meny = manual)."""
        if self._update_worker is not None and self._update_worker.isRunning():
            return
        self._update_check_manual = bool(manual)
        self._set_last_update_check_now()
        if manual:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
            self._status(tr("update.checking"), "info")
        worker = UpdateWorker("check")
        worker.checked.connect(self._on_update_checked)
        worker.failed.connect(self._on_update_failed)
        worker.finished.connect(worker.deleteLater)
        self._update_worker = worker
        worker.start()

    def _set_last_update_check_now(self) -> None:
        try:
            from core.github_update import now_iso

            self.settings.set("last_update_check", now_iso())
            self.settings.save()
        except Exception:
            log.debug("Kunde inte spara last_update_check", exc_info=True)
        self._refresh_last_check_label()

    def _refresh_last_check_label(self) -> None:
        label = getattr(self, "_lbl_last_check", None)
        if label is None:
            return
        raw = str(self.settings.get("last_update_check", "") or "").strip()
        if raw:
            label.setText(
                tr("update.last_check", when=raw.replace("T", " ")[:16])
            )
        else:
            label.setText(tr("update.last_check_never"))

    def _restore_update_cursor(self) -> None:
        try:
            while QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
        except Exception:
            pass

    def _on_update_checked(self, info: Any) -> None:
        self._restore_update_cursor()
        self._update_worker = None
        manual = self._update_check_manual
        if getattr(info, "available", False):
            self._pending_update_info = info
            self._status(
                tr("update.status_available", latest=info.latest_version),
                "success",
            )
            if manual or self.isVisible():
                self._prompt_update_install(info)
            else:
                # Appen startade minimerad i trayen: notis nu –
                # installationsfrågan visas när fönstret öppnas (show()).
                self._notify_update_via_tray(info)
            return
        self._status_reset()
        if getattr(info, "no_releases", False):
            if manual:
                QMessageBox.information(
                    self,
                    tr("update.title"),
                    tr("update.no_releases", repo_url=GITHUB_REPO_URL),
                )
        elif getattr(info, "error", ""):
            if manual:
                QMessageBox.warning(
                    self,
                    tr("update.title"),
                    tr("update.check_failed", error=info.error),
                )
            else:
                log.info("Autosökning: %s", info.error)
        elif manual:
            QMessageBox.information(
                self,
                tr("update.title"),
                tr("update.up_to_date", current=APP_VERSION),
            )

    def _prompt_update_install(self, info: Any) -> None:
        """Fråga om en hittad uppdatering ska installeras nu."""
        self._pending_update_info = None
        notes = (info.notes or "").strip() or info.name or info.tag
        if len(notes) > 700:
            notes = notes[:700] + "…"
        box = QMessageBox(self)
        box.setWindowTitle(tr("update.available_title"))
        box.setText(
            tr(
                "update.available_text",
                latest=info.latest_version,
                current=APP_VERSION,
                notes=notes,
            )
        )
        btn_install = box.addButton(
            tr("update.install"), QMessageBox.ButtonRole.AcceptRole
        )
        btn_page = box.addButton(
            tr("update.release_page"), QMessageBox.ButtonRole.ActionRole
        )
        box.addButton(tr("update.later"), QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is btn_install:
            self._install_update(info)
        elif clicked is btn_page:
            self._open_url(info.html_url or f"{GITHUB_REPO_URL}/releases")

    def _notify_update_via_tray(self, info: Any) -> None:
        """Tray-notis om ny version (när fönstret är dolt i trayen)."""
        tray = getattr(self, "_tray_ref", None)
        notify = getattr(tray, "show_notification", None)
        if callable(notify):
            try:
                notify(
                    tr("update.tray_title"),
                    tr(
                        "update.tray_text",
                        latest=getattr(info, "latest_version", ""),
                    ),
                )
                return
            except Exception:
                log.debug("Tray-notis om uppdatering misslyckades", exc_info=True)
        log.info(
            "Ny version %s tillgänglig (visas vid nästa fönsteröppning).",
            getattr(info, "latest_version", "?"),
        )

    def _maybe_prompt_pending_update(self) -> None:
        """Visa uppskjuten installationsfråga när fönstret blivit synligt."""
        info = self._pending_update_info
        if info is not None and self.isVisible():
            self._prompt_update_install(info)

    def _install_update(self, info: Any) -> None:
        """Ladda ner + installerad vald release i bakgrunden."""
        if self._update_worker is not None and self._update_worker.isRunning():
            return
        progress = QProgressDialog(
            tr("update.downloading", latest=getattr(info, "latest_version", "")),
            None, 0, 0, self,
        )
        progress.setWindowTitle(tr("update.title"))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(0)
        progress.setCancelButton(None)
        progress.show()
        self._update_progress = progress
        worker = UpdateWorker("install", info=info, base_dir=self._base_dir())
        worker.installed.connect(self._on_update_installed)
        worker.failed.connect(self._on_update_failed)
        worker.finished.connect(worker.deleteLater)
        self._update_worker = worker
        worker.start()

    def _close_update_progress(self) -> None:
        if self._update_progress is not None:
            try:
                self._update_progress.close()
            except Exception:
                pass
            self._update_progress = None

    def _on_update_installed(self, result: Any) -> None:
        self._close_update_progress()
        self._update_worker = None
        result = result if isinstance(result, dict) else {}
        copied = len(result.get("copied") or [])
        errors = result.get("errors") or []
        if copied == 0 and errors:
            QMessageBox.warning(
                self,
                tr("update.title"),
                tr(
                    "update.install_failed",
                    error="\n".join(str(e) for e in errors[:8]),
                ),
            )
            return
        self._status(tr("update.installed_title"), "success")
        reply = QMessageBox.question(
            self,
            tr("update.installed_title"),
            tr("update.installed", count=copied),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._restart_app()

    def _on_update_failed(self, message: str) -> None:
        was_install = self._update_progress is not None
        self._close_update_progress()
        self._restore_update_cursor()
        self._update_worker = None
        if was_install:
            QMessageBox.warning(
                self, tr("update.title"),
                tr("update.install_failed", error=str(message)),
            )
        elif self._update_check_manual:
            QMessageBox.warning(
                self, tr("update.title"),
                tr("update.check_failed", error=str(message)),
            )
        else:
            log.info("Autosökning misslyckades: %s", message)

    # ────────────────────────────────────────────────────────────────
    # (v5.4) Donation, språkbyte, omstart, Om-dialog
    # ────────────────────────────────────────────────────────────────

    def _open_url(self, url: str) -> bool:
        """Öppna URL i webbläsaren (via ui.donate-hjälparen)."""
        try:
            from ui.donate import open_url_in_browser

            return open_url_in_browser(str(url))
        except Exception:
            try:
                return bool(QDesktopServices.openUrl(QUrl(str(url))))
            except Exception:
                log.warning("Kunde inte öppna URL: %s", url, exc_info=True)
                return False

    def _donation_url_setting(self) -> str:
        if hasattr(self.settings, "get_donation_url"):
            return self.settings.get_donation_url()
        return str(self.settings.get("donation_url", "") or "")

    def _open_donate(self) -> None:
        """❤️ Stöd projektet-sidan (Ko-fi, PayPal, Swish-QR)."""
        try:
            from ui.donate import DonateDialog
        except Exception:
            log.warning("Donationsdialogen kunde inte laddas", exc_info=True)
            return
        DonateDialog(
            self,
            kofi_url=self._donation_url_setting(),
            paypal_url=str(self.settings.get("donation_paypal_url", "") or ""),
            swish_number=str(self.settings.get("donation_swish", "") or ""),
        ).exec()

    def _open_donation_page(self) -> None:
        """Öppna Ko-fi-sidan direkt – fältets aktuella text vinner."""
        raw = self._donation_url_setting()
        widget = self._settings_widgets.get("donation_url")
        if isinstance(widget, QLineEdit) and widget.text().strip():
            raw = widget.text()
        try:
            from core.donate import resolve_donation_links

            url = resolve_donation_links(raw, "")[0]
        except Exception:
            url = ""
        if url:
            self._open_url(url)
        else:
            self._open_donate()

    def _set_ui_language(self, language: str) -> None:
        """Byt UI-språk (sv/en), spara och erbjud omstart."""
        lang = normalize_language(language)
        current_setting = normalize_language(self.settings.get("language", "sv"))
        if lang == i18n_get_language() and lang == current_setting:
            return
        self.settings.set("language", lang)
        try:
            self.settings.save()
        except Exception:
            log.debug("Kunde inte spara språkvalet", exc_info=True)
        i18n_set_language(lang)
        self._prompt_restart_for_language(lang)

    def _prompt_restart_for_language(self, lang: str) -> None:
        name = tr("language.en") if lang == "en" else tr("language.sv")
        reply = QMessageBox.question(
            self,
            tr("language.changed_title"),
            tr("language.changed_text", language=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._restart_app()

    def _restart_app(self) -> None:
        """Be main.pyw starta en ny instans EFTER att denna stängt rent.

        Sätter EMAILAPP_RELAUNCH=1 och avslutar event-loopen; städning
        (settings, tray, single-instance-låset) sker i main.pyw:s
        finally – först därefter spawnas ersättaren, så låset aldrig
        krockar med den nya instansen.
        """
        app = QApplication.instance()
        if app is None:
            QMessageBox.warning(self, tr("app.window_title"), tr("restart.failed"))
            return
        os.environ["EMAILAPP_RELAUNCH"] = "1"
        log.info("Omstart begärd (EMAILAPP_RELAUNCH=1) – avslutar instansen.")
        app.exit(0)

    def _show_about(self) -> None:
        """Om-dialog med version + genvägar till GitHub och donation."""
        box = QMessageBox(self)
        box.setWindowTitle(tr("about.title"))
        box.setText(
            tr("about.text", version=APP_VERSION, repo_url=GITHUB_REPO_URL)
        )
        btn_donate = box.addButton(
            tr("toolbar.donate"), QMessageBox.ButtonRole.ActionRole
        )
        btn_github = box.addButton(
            tr("donate.github_btn"), QMessageBox.ButtonRole.ActionRole
        )
        box.addButton(QMessageBox.StandardButton.Ok)
        box.exec()
        clicked = box.clickedButton()
        if clicked is btn_donate:
            self._open_donate()
        elif clicked is btn_github:
            self._open_url(GITHUB_REPO_URL)

    def _on_tab_changed(self, index: int) -> None:
        self._sync_view_menu()
        # (v5.4) Nyckelbaserat (språkoberoende) i stället för svensk
        # fliktext – med text-fallback om nycklarna saknas.
        keys = getattr(self, "_tab_keys", []) or []
        key = keys[index] if 0 <= index < len(keys) else ""
        if not key:
            text = self.tabs.tabText(index).lower()
            key = _TAB_ALIASES.get(text.split()[-1] if text.split() else "", "")
        if key == "contacts":
            self._reload_contacts_tab()
        elif key == "history":
            self._refresh_history()
        elif key == "logs":
            self._refresh_log()
        elif key == "templates":
            self._refresh_template_tools_list()

    # ────────────────────────────────────────────────────────────────
    # 4-STEGS WIZARD
    # ────────────────────────────────────────────────────────────────

    def _build_send_wizard_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(8, 8, 8, 16)
        layout.setSpacing(12)

        self._wizard_scroll = scroll
        self._wizard_steps: List[QWidget] = []

        self._add_step(
            layout, "①", "📝", tr("step1.title"), tr("step1.hint"),
            "step-blue",
        )
        step1 = self._build_step_mail()
        layout.addWidget(step1)
        self._wizard_steps.append(step1)

        self._add_step(
            layout,
            "②",
            "🖼️",
            tr("step2.title"),
            tr("step2.hint"),
            "step-orange",
        )
        step2 = self._build_step_attachments()
        layout.addWidget(step2)
        self._wizard_steps.append(step2)

        self._add_step(
            layout,
            "③",
            "📬",
            tr("step3.title"),
            tr("step3.hint"),
            "step-green",
        )
        step3 = self._build_step_recipients()
        layout.addWidget(step3)
        self._wizard_steps.append(step3)

        self._add_step(
            layout,
            "④",
            "🚀",
            tr("step4.title"),
            tr("step4.hint"),
            "step-red",
        )
        step4 = self._build_step_send()
        layout.addWidget(step4)
        self._wizard_steps.append(step4)

        layout.addStretch()
        scroll.setWidget(inner)

        self._scan_tpls()
        self._load_default_recipients()
        return scroll

    def _add_step(
        self,
        layout: QVBoxLayout,
        number: str,
        emoji: str,
        title: str,
        hint: str,
        css_class: str,
    ) -> None:
        frame = QFrame()
        frame.setProperty("cssClass", css_class)
        step_layout = QHBoxLayout(frame)
        step_layout.setContentsMargins(18, 12, 18, 12)
        step_layout.setSpacing(12)

        label = QLabel(f"{number}  {emoji}  {title}")
        label.setStyleSheet(
            "color: #FFFFFF; font-size: 14pt; font-weight: bold; "
            "background: transparent;"
        )
        step_layout.addWidget(label)

        hint_label = QLabel(hint)
        hint_label.setStyleSheet(
            "color: #FFFFFF; font-weight: bold; background: transparent;"
        )
        hint_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        hint_label.setWordWrap(True)
        step_layout.addWidget(hint_label, stretch=1)

        layout.addWidget(frame)

    # ── Steg 1: mall ───────────────────────────────────────────────
    def _build_step_mail(self) -> QWidget:
        card = QFrame()
        card.setProperty("cssClass", "card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(10)

        top = QHBoxLayout()
        top.addWidget(QLabel("Mall:"))

        self._tpl_combo = QComboBox()
        self._tpl_combo.setMinimumWidth(360)
        self._tpl_combo.currentTextChanged.connect(self._on_tpl_sel)
        top.addWidget(self._tpl_combo, stretch=1)

        btn_scan = QPushButton("🔄 Sök")
        btn_scan.clicked.connect(self._scan_tpls)
        top.addWidget(btn_scan)

        btn_dir = QPushButton("📂 Öppna mapp")
        btn_dir.clicked.connect(self._open_tpl_dir)
        top.addWidget(btn_dir)

        self._tpl_badge = QLabel("⏳ Ingen mall vald")
        self._tpl_badge.setProperty("cssClass", "pill")
        top.addWidget(self._tpl_badge)
        outer.addLayout(top)

        subject_row = QHBoxLayout()
        subject_row.addWidget(QLabel("Ämne:"))
        self._subject = QLineEdit()
        self._subject.setPlaceholderText("Skriv ämnesrad…")
        self._subject.textChanged.connect(self._refresh_preview)
        subject_row.addWidget(self._subject, stretch=1)
        outer.addLayout(subject_row)

        self._editor = QTextEdit()
        self._editor.setMinimumHeight(170)
        self._editor.setPlaceholderText(
            "Mallinnehåll visas här efter att du valt en mall…"
        )
        self._editor.textChanged.connect(self._on_editor_changed)
        outer.addWidget(self._editor)

        ph_group = QGroupBox("🔑 Uppgifter i mallen")
        ph_layout = QVBoxLayout(ph_group)
        self._ph_area = QVBoxLayout()
        ph_layout.addLayout(self._ph_area)
        self._ph_status = QLabel("⏳ Välj en mall")
        self._ph_status.setProperty("cssClass", "subtext")
        ph_layout.addWidget(self._ph_status)
        outer.addWidget(ph_group)

        bottom = QHBoxLayout()
        # (v5.4) Ingen "Inkludera engelsk version"-knapp – språket styrs
        # per mottagare: EN-mottagare får alltid engelsk version
        lang_info = QLabel(
            "🌐 Språk per mottagare: EN får engelsk version, SV får "
            "svensk – skickas automatiskt"
        )
        lang_info.setProperty("cssClass", "subtext")
        lang_info.setWordWrap(True)
        bottom.addWidget(lang_info, stretch=1)

        btn_save = QPushButton("💾 Spara mall")
        btn_save.clicked.connect(self._save_tpl)
        bottom.addWidget(btn_save)
        outer.addLayout(bottom)

        return card

    # ── Steg 2: bilagor/bilder ─────────────────────────────────────
    def _build_step_attachments(self) -> QWidget:
        card = QFrame()
        card.setProperty("cssClass", "card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(12)

        att_group = QGroupBox("🖼️ Bilder & bifogade filer")
        att_layout = QVBoxLayout(att_group)

        self._drop_hint = QLabel(
            "Dra filer hit eller klicka på “Lägg till bilder/filer”"
        )
        self._drop_hint.setProperty("cssClass", "subtext")
        att_layout.addWidget(self._drop_hint)

        self._att_list = AttachmentDropListWidget(self._c())
        self._att_list.filesDropped.connect(self._handle_dropped_files)
        att_layout.addWidget(self._att_list)

        att_buttons = QHBoxLayout()
        btn_add = QPushButton("➕ Lägg till bilder/filer")
        btn_add.setProperty("cssClass", "accent")
        btn_add.clicked.connect(self._add_att)
        att_buttons.addWidget(btn_add)

        btn_rm = QPushButton("🗑️ Ta bort")
        btn_rm.setProperty("cssClass", "danger")
        btn_rm.clicked.connect(self._rm_att)
        att_buttons.addWidget(btn_rm)

        btn_clear = QPushButton("🧹 Rensa")
        btn_clear.setProperty("cssClass", "danger")
        btn_clear.clicked.connect(self._clr_att)
        att_buttons.addWidget(btn_clear)

        self._att_label = QLabel("0 bilagor")
        self._att_label.setProperty("cssClass", "subtext")
        att_buttons.addWidget(self._att_label)
        att_buttons.addStretch()
        att_layout.addLayout(att_buttons)

        grid.addWidget(att_group, 0, 0)

        free_group = QGroupBox("💬 Fritext")
        free_layout = QVBoxLayout(free_group)

        free_hint = QLabel("Fritext skickas med ovan signaturen i mailet.")
        free_hint.setProperty("cssClass", "subtext")
        free_layout.addWidget(free_hint)

        self._free_edit = QPlainTextEdit()
        self._free_edit.setMaximumHeight(140)
        self._free_edit.setPlaceholderText(
            "Skriv valfri extra text som läggs till i mailet…"
        )
        self._free_edit.textChanged.connect(self._refresh_preview)
        free_layout.addWidget(self._free_edit)

        grid.addWidget(free_group, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)

        outer.addLayout(grid)
        return card

    # ── Steg 3: mottagare ──────────────────────────────────────────
    def _build_step_recipients(self) -> QWidget:
        card = QFrame()
        card.setProperty("cssClass", "card")
        outer = QVBoxLayout(card)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(12)

        top = QHBoxLayout()
        title = QLabel("📒 Välj mottagare")
        title.setProperty("cssClass", "heading")
        top.addWidget(title, stretch=1)

        btn_address_book = QPushButton("📒 Öppna adressbok")
        btn_address_book.setProperty("cssClass", "accent")
        btn_address_book.clicked.connect(self._open_address_book)
        top.addWidget(btn_address_book)
        outer.addLayout(top)

        # (v5.2) Språk för nya mottagare
        lang_row = QHBoxLayout()
        lang_row.addWidget(QLabel("🌐 Språk för nya mottagare:"))
        self._new_lang_combo = QComboBox()
        self._new_lang_combo.addItem("🇸🇪 Svenska (SV)", "sv")
        self._new_lang_combo.addItem("🇬🇧 Engelska (EN)", "en")
        lang_row.addWidget(self._new_lang_combo)
        lang_hint = QLabel(
            "Högerklick på en mottagare → byt språk · Dubbelklick växlar. "
            "SV får endast svensk version, EN endast engelsk."
        )
        lang_hint.setProperty("cssClass", "subtext")
        lang_hint.setWordWrap(True)
        lang_row.addWidget(lang_hint, stretch=1)
        outer.addLayout(lang_row)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.addWidget(self._build_recipient_box("📨 Till", "to"), 0, 0)
        grid.addWidget(self._build_recipient_box("🙈 Bcc", "bcc"), 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        outer.addLayout(grid)

        info = QLabel(
            "Tips: Standard-Bcc fylls i automatiskt från inställningar. "
            "CC används inte."
        )
        info.setProperty("cssClass", "subtext")
        info.setWordWrap(True)
        outer.addWidget(info)
        return card

    def _build_recipient_box(self, title: str, target: str) -> QGroupBox:
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        input_row = QHBoxLayout()
        line = QLineEdit()
        line.setPlaceholderText("namn@example.se")
        input_row.addWidget(line, stretch=1)

        btn_add = QPushButton("➕ Lägg till")
        input_row.addWidget(btn_add)
        layout.addLayout(input_row)

        list_widget = QListWidget()
        list_widget.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        list_widget.setMinimumHeight(130)
        # (v5.2) Språk: högerklick → välj språk, dubbelklick → växla
        list_widget.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        list_widget.customContextMenuRequested.connect(
            lambda pos, w=list_widget, t=target: self._recipient_context_menu(
                w, t, pos
            )
        )
        list_widget.itemDoubleClicked.connect(
            lambda item, w=list_widget: self._toggle_recipient_lang(w, item)
        )
        layout.addWidget(list_widget)

        buttons = QHBoxLayout()
        btn_remove = QPushButton("🗑️ Ta bort")
        btn_remove.setProperty("cssClass", "danger")
        buttons.addWidget(btn_remove)

        btn_clear = QPushButton("🧹 Rensa")
        btn_clear.setProperty("cssClass", "danger")
        buttons.addWidget(btn_clear)
        buttons.addStretch()
        layout.addLayout(buttons)

        if target == "to":
            self._to_input = line
            self._to_list = list_widget
            btn_add.clicked.connect(lambda: self._add_recipient("to"))
            line.returnPressed.connect(lambda: self._add_recipient("to"))
            btn_remove.clicked.connect(
                lambda: self._remove_selected_recipients("to")
            )
            btn_clear.clicked.connect(lambda: self._clear_recipients("to"))
        else:
            self._bcc_input = line
            self._bcc_list = list_widget
            btn_add.clicked.connect(lambda: self._add_recipient("bcc"))
            line.returnPressed.connect(lambda: self._add_recipient("bcc"))
            btn_remove.clicked.connect(
                lambda: self._remove_selected_recipients("bcc")
            )
            btn_clear.clicked.connect(lambda: self._clear_recipients("bcc"))
        return group

    # ── Steg 4: skicka ─────────────────────────────────────────────
    def _build_step_send(self) -> QWidget:
        card = QFrame()
        card.setProperty("cssClass", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        self._send_summary = QLabel(
            "Kontrollera uppgifterna och klicka Skicka mail."
        )
        self._send_summary.setProperty("cssClass", "subtext")
        self._send_summary.setWordWrap(True)
        layout.addWidget(self._send_summary)

        buttons = QHBoxLayout()
        btn_preview = QPushButton("👁️ Visa preview-tab")
        btn_preview.setProperty("cssClass", "purple")
        btn_preview.clicked.connect(lambda: self.select_tab("preview"))
        buttons.addWidget(btn_preview)

        buttons.addStretch()

        btn_send = QPushButton("📤 Skicka mail")
        btn_send.setProperty("cssClass", "send")
        btn_send.setMinimumHeight(42)
        btn_send.clicked.connect(self._send)
        buttons.addWidget(btn_send)
        layout.addLayout(buttons)

        return card

    # ────────────────────────────────────────────────────────────────
    # Mallar / placeholders
    # ────────────────────────────────────────────────────────────────

    def _template_names(self) -> List[str]:
        """Alla mallfiler i Mallar/-mappen (utan ~$, .bak, .tmp)."""
        templates_dir = self._base_dir() / str(
            self.settings.get("template_dir", "Mallar")
        )
        templates: List[str] = []
        if templates_dir.exists():
            for pattern in ("*.docx", "*.html", "*.htm", "*.txt"):
                for path in sorted(templates_dir.glob(pattern)):
                    if path.name.startswith("~$"):
                        continue
                    if path.name.endswith((".bak", ".tmp")):
                        continue
                    templates.append(path.name)
        return templates

    def _apply_default_template(self) -> None:
        """(v5.1) Välj standardmallen om inställningen är satt.

        Anropas vid första mallinläsningen och när inställningarna
        sparas. Manuella val i dropdown-menyn VINNER alltid – standarden
        gäller bara tills användaren byter (eller appen startas om).
        """
        name = self.settings.get_default_template() if hasattr(
            self.settings, "get_default_template"
        ) else str(self.settings.get("default_template", "") or "").strip()
        if not name or not hasattr(self, "_tpl_combo"):
            return
        idx = self._tpl_combo.findText(name)
        if idx >= 0:
            self._tpl_combo.setCurrentIndex(idx)
            self._status(f"📝 Standardmall: {name}", "success")

    def _scan_tpls(self) -> None:
        templates = self._template_names()

        self._tpl_combo.blockSignals(True)
        self._tpl_combo.clear()
        self._tpl_combo.addItems(templates)
        self._tpl_combo.blockSignals(False)

        if templates:
            if self._last_tpl is None:
                # Första inläsningen (v5.1): standardmallen om satt,
                # annars första mallen som förut.
                default = (
                    self.settings.get_default_template()
                    if hasattr(self.settings, "get_default_template")
                    else str(
                        self.settings.get("default_template", "") or ""
                    ).strip()
                )
                idx = self._tpl_combo.findText(default) if default else -1
                if idx >= 0:
                    self._tpl_combo.setCurrentIndex(idx)
                    self._on_tpl_sel(default)
                else:
                    if default:
                        self._status(
                            f"⚠️ Standardmallen '{default}' saknas – "
                            "valde första mallen",
                            "warning",
                        )
                    self._tpl_combo.setCurrentIndex(0)
                    self._on_tpl_sel(templates[0])
            else:
                # Omskanning (t.ex. "🔄 Sök"): behåll användarens val
                # om mallen fortfarande finns – byt inte tillbaka.
                current = self._tpl_combo.currentText()
                if not current or current not in templates:
                    self._tpl_combo.setCurrentIndex(0)
                    self._on_tpl_sel(templates[0])
        else:
            self._tpl_badge.setText("⚠️ Inga mallar hittades")
            self._status("⚠️ Inga mallar hittades", "warning")

    def _on_tpl_sel(self, name: str) -> None:
        if not name:
            return
        path = (
            self._base_dir()
            / str(self.settings.get("template_dir", "Mallar"))
            / name
        )
        if not path.exists():
            self._status(f"❌ Mall saknas: {name}", "error")
            return

        self._last_tpl = path
        try:
            subject, body = self._read_template(path)
            self._subject.setText(subject)
            self._editor.blockSignals(True)
            self._editor.setPlainText(body)
            self._editor.blockSignals(False)
        except Exception as exc:
            log.warning(
                "Ladda mall '%s' misslyckades", name, exc_info=True
            )
            self._editor.setPlainText(f"⚠️ Fel: {exc}")

        self._tpl_badge.setText(f"✅ {name}")
        self._tpl_badge.setProperty("cssClass", "pillGreen")
        if self._tpl_badge.style() is not None:
            self._tpl_badge.style().unpolish(self._tpl_badge)
            self._tpl_badge.style().polish(self._tpl_badge)

        self._rebuild_ph()
        self._refresh_preview()
        self._status(f"📝 Mall vald: {name}", "success")

    def _read_template(self, path: Path) -> Tuple[str, str]:
        suffix = path.suffix.lower()
        if suffix == ".docx":
            from script.templates import parse_subject_and_body

            try:
                return parse_subject_and_body(
                    str(path),
                    replacements={},
                    include_english=False,
                    remove_lines_with_missing=False,
                )
            except TypeError:
                return parse_subject_and_body(str(path))

        raw = path.read_text(encoding="utf-8", errors="replace")
        if suffix in (".html", ".htm"):
            title_match = re.search(
                r"<title>(.*?)</title>", raw, re.I | re.DOTALL
            )
            subject = (
                title_match.group(1).strip()
                if title_match
                else ""
            )
            body_match = re.search(
                r"<body[^>]*>(.*?)</body>", raw, re.I | re.DOTALL
            )
            body_html = body_match.group(1) if body_match else raw
            body = re.sub(r"<br\s*/?>", "\n", body_html, flags=re.I)
            body = re.sub(r"</?p[^>]*>", "\n", body, flags=re.I)
            body = re.sub(r"<[^>]+>", "", body)
            return subject, body.strip()

        lines = raw.splitlines()
        if lines and lines[0].lower().startswith(("ämne:", "subject:")):
            subject = lines[0].split(":", 1)[1].strip()
            body = "\n".join(lines[1:]).strip()
            return subject, body
        return (lines[0].strip() if lines else ""), "\n".join(
            lines[1:]
        ).strip()

    def _extract_placeholder_keys(self) -> List[str]:
        content = f"{self._subject.text()}\n{self._editor.toPlainText()}"
        keys: List[str] = []
        seen: set = set()

        def add_key(raw: object) -> None:
            key = str(raw or "").strip()
            if key and key.lower() not in seen:
                seen.add(key.lower())
                keys.append(key)

        for match in _PH_PATTERN.finditer(content):
            add_key(match.group(1) or match.group(2) or match.group(3))

        if self._last_tpl is not None and self._last_tpl.exists():
            try:
                from script.templates import list_placeholders

                for key in list_placeholders(self._last_tpl):
                    add_key(key)
            except Exception:
                try:
                    from script.templates import find_placeholders_in_file

                    for key in find_placeholders_in_file(self._last_tpl):
                        add_key(key)
                except Exception:
                    log.debug(
                        "Kunde inte läsa placeholders direkt från mallfil",
                        exc_info=True,
                    )
        return keys

    def _rebuild_ph(self) -> None:
        self._clear_layout(self._ph_area)
        self._ph_inputs.clear()
        self._ph_row_widgets.clear()

        keys = self._extract_placeholder_keys()
        if not keys:
            self._ph_status.setText(
                "ℹ️ Inga uppgifter behöver fyllas i för denna mall."
            )
            self._refresh_preview()
            return

        # (v5.4) Labels alltid svenska – mallen fylls i på svenska,
        # engelsk version genereras automatiskt till EN-mottagare
        labels = _PH_SV
        saved = self.settings.get("replacements_values", {}) or {}

        header = QLabel(f"🔑 Fyll i mallens uppgifter här: {', '.join(keys)}")
        header.setWordWrap(True)
        header.setStyleSheet(
            f"color: {self._c().get('accent', '')}; font-weight: bold;"
        )
        self._ph_area.addWidget(header)

        grid = QGridLayout()
        grid.setSpacing(10)
        colors = ["accent", "purple", "success", "warning"]
        palette = self._c()

        for row, key in enumerate(keys):
            key_l = key.lower()
            label_text = labels.get(key_l, key.replace("_", " ").title())
            color = palette.get(
                colors[row % len(colors)], palette.get("accent", "")
            )

            label = QLabel(f"{label_text}:")
            label.setStyleSheet(
                f"color: {color}; font-weight: bold; font-size: 10pt;"
            )
            grid.addWidget(label, row, 0)

            default = str(saved.get(key, saved.get(key_l, "")) or "")
            if key_l in PLACEHOLDER_DROPDOWNS:
                field = QComboBox()
                field.addItems(PLACEHOLDER_DROPDOWNS[key_l])
                field.setEditable(True)
                if default:
                    field.setCurrentText(default)
                field.currentTextChanged.connect(self._on_ph_chg)
            else:
                field = QLineEdit(default)
                field.setPlaceholderText(f"Skriv {label_text.lower()}…")
                field.textChanged.connect(self._on_ph_chg)
            grid.addWidget(field, row, 1)

            indicator = QLabel("✅" if default.strip() else "⬜")
            indicator.setStyleSheet("font-size: 15pt;")
            grid.addWidget(indicator, row, 2)
            self._ph_inputs[key] = field

        grid.setColumnStretch(1, 1)
        self._ph_area.addLayout(grid)
        self._ensure_subject_contains_model_and_reg(update_field=True)
        self._update_en_only_placeholder_visibility()
        self._update_ph_status()
        self._refresh_preview()

    def _clear_layout(self, layout: Any) -> None:
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())

    def _on_ph_chg(self) -> None:
        values = self._get_ph()
        self._ensure_subject_contains_model_and_reg(update_field=True)
        self._update_ph_status()
        self.settings.set("replacements_values", values)
        self.bus.publish(
            "template.placeholder_changed",
            {"key": "", "value": "", "all_values": values},
        )
        self._refresh_preview()

    def _on_editor_changed(self) -> None:
        # Debounce (v4.6): omskapa placeholder-fält endast när
        # användaren pausar – inte vid varje tangenttryckning.
        if not hasattr(self, "_ph_debounce"):
            self._ph_debounce = QTimer(self)
            self._ph_debounce.setSingleShot(True)
            self._ph_debounce.setInterval(220)
            self._ph_debounce.timeout.connect(self._rebuild_ph)
        self._ph_debounce.start()
        self._refresh_preview()

    def _update_ph_status(self) -> None:
        values = self._get_ph()
        show_en_only = self._has_en_recipient()
        counted = {
            key: value
            for key, value in values.items()
            if show_en_only or str(key).lower() not in EN_ONLY_PLACEHOLDERS
        }
        filled = sum(1 for value in counted.values() if value.strip())
        total = len(counted)
        colors = self._c()

        if total == 0:
            self._ph_status.setText("")
            return

        if filled == total:
            text = f"✅ Alla {total} uppgifter ifyllda – redo!"
            style = f"color: {colors.get('success', '')}; font-weight: bold;"
        elif filled > 0:
            text = f"⚠️ {filled}/{total} uppgifter ifyllda"
            style = f"color: {colors.get('warning', '')}; font-weight: bold;"
        else:
            text = f"❌ 0/{total} uppgifter ifyllda"
            style = f"color: {colors.get('error', '')}; font-weight: bold;"

        self._ph_status.setText(text)
        self._ph_status.setStyleSheet(style)

        grid = None
        for index in range(self._ph_area.count()):
            item = self._ph_area.itemAt(index)
            if item and item.layout():
                grid = item.layout()
                break
        if grid is None:
            return

        for row, key in enumerate(self._ph_inputs):
            value = self._widget_text(self._ph_inputs[key])
            item = grid.itemAtPosition(row, 2)
            if item and item.widget():
                item.widget().setText("✅" if value.strip() else "⬜")

    def _get_ph(self) -> Dict[str, str]:
        return {
            key: self._widget_text(widget).strip()
            for key, widget in self._ph_inputs.items()
        }

    @staticmethod
    def _widget_text(widget: QWidget) -> str:
        if isinstance(widget, QComboBox):
            return widget.currentText()
        if isinstance(widget, QLineEdit):
            return widget.text()
        return ""

    @staticmethod
    def _subject_placeholder_keys(subject_text: str) -> set:
        keys: set = set()
        for match in _PH_PATTERN.finditer(subject_text or ""):
            raw = (
                match.group(1)
                or match.group(2)
                or match.group(3)
                or ""
            ).strip().lower()
            if raw:
                keys.add(raw)
        return keys

    def _get_model_and_reg_values(
        self, values: Optional[Dict[str, str]] = None
    ) -> Tuple[str, str]:
        values = values or self._get_ph()
        model = ""
        reg = ""
        for key in ("modell", "model"):
            candidate = str(values.get(key, "") or "").strip()
            if candidate:
                model = candidate
                break
        for key in ("reg", "registration", "registreringsnummer"):
            candidate = str(values.get(key, "") or "").strip()
            if candidate:
                reg = candidate
                break
        return model, reg

    def _ensure_subject_contains_model_and_reg(
        self, *, update_field: bool = False
    ) -> str:
        """Säkerställ att ämnesraden innehåller modell och reg.

        Regler:
        - Om ämnesraden redan innehåller modell/reg-värdet görs inget.
        - Om ämnesraden innehåller en placeholder för modell/reg görs inget.
        - Om värden finns men saknas i ämnet appenderas de som suffix.
        """
        subject_text = self._subject.text().strip()
        placeholder_keys = self._subject_placeholder_keys(subject_text)
        model, reg = self._get_model_and_reg_values()

        parts_to_add: List[str] = []
        if model and model.lower() not in subject_text.lower() and not (
            {"modell", "model"} & placeholder_keys
        ):
            parts_to_add.append(model)
        if reg and reg.lower() not in subject_text.lower() and not (
            {"reg", "registration", "registreringsnummer"} & placeholder_keys
        ):
            parts_to_add.append(reg)

        updated = subject_text
        if parts_to_add:
            separator = " – " if updated else ""
            updated = f"{updated}{separator}{' – '.join(parts_to_add)}"
            if update_field and updated != self._subject.text():
                self._subject.blockSignals(True)
                self._subject.setText(updated)
                self._subject.blockSignals(False)
        return updated

    # ────────────────────────────────────────────────────────────────
    # Bilagor / drag & drop
    # ────────────────────────────────────────────────────────────────

    def _handle_dropped_files(self, paths: List[str]) -> None:
        added = self._add_attachment_paths(paths)
        if added:
            self._status(
                f"🖼️ {added} fil(er) lades till via drag & drop", "success"
            )
        else:
            self._status("ℹ️ Inga nya filer lades till", "info")

    def _add_attachment_paths(self, paths: Sequence[str]) -> int:
        existing = {_attachment_key(path) for path in self._attachments}
        added = 0
        for file_path in paths:
            cleaned = str(file_path).strip()
            if not cleaned:
                continue
            path = Path(cleaned)
            if not path.exists() or not path.is_file():
                continue
            key = _attachment_key(cleaned)
            if key in existing:
                continue
            existing.add(key)
            self._attachments.append(cleaned)
            prefix = "🖼️ " if _is_image(cleaned) else "📎 "
            item = QListWidgetItem(prefix + path.name)
            item.setToolTip(cleaned)
            self._att_list.addItem(item)
            added += 1

        if added:
            self._update_attachment_label()
            self._refresh_preview()
        return added

    def _add_att(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Välj bilder eller bifogade filer",
            "",
            "Alla filer (*);;Bilder (*.png *.jpg *.jpeg *.gif *.bmp "
            "*.webp *.tif *.tiff);;PDF (*.pdf);;Dokument (*.docx *.xlsx *.txt)",
        )
        added = self._add_attachment_paths(files)
        if added:
            self._status(
                f"📎 {added} bilaga/bild(er) tillagda", "success"
            )

    def _rm_att(self) -> None:
        rows = sorted(
            {
                self._att_list.row(item)
                for item in self._att_list.selectedItems()
            },
            reverse=True,
        )
        for row in rows:
            self._att_list.takeItem(row)
            if 0 <= row < len(self._attachments):
                self._attachments.pop(row)
        self._update_attachment_label()
        self._refresh_preview()

    def _clr_att(self) -> None:
        self._attachments.clear()
        self._att_list.clear()
        self._update_attachment_label()
        self._refresh_preview()

    def _update_attachment_label(self) -> None:
        images = sum(1 for path in self._attachments if _is_image(path))
        files = len(self._attachments) - images
        if not self._attachments:
            text = "0 bilagor"
        else:
            text = f"{len(self._attachments)} bilagor"
            if images:
                text += f" · {images} bilder"
            if files:
                text += f" · {files} filer"
        self._att_label.setText(text)

    # ────────────────────────────────────────────────────────────────
    # Mottagare och adressbok
    # ────────────────────────────────────────────────────────────────

    def _load_contacts_for_address_book(self) -> List[Dict[str, Any]]:
        path = self._contacts_path()
        if not path.exists():
            self._status(f"⚠️ contacts.json saknas: {path}", "warning")
            return []

        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            QMessageBox.warning(
                self, "Adressbok", f"Kunde inte läsa contacts.json:\n{exc}"
            )
            return []

        raw_contacts: List[Any]
        if isinstance(data, dict) and isinstance(data.get("contacts"), list):
            raw_contacts = data["contacts"]
        elif isinstance(data, list):
            raw_contacts = data
        elif isinstance(data, dict):
            raw_contacts = []
            for email, value in data.items():
                if isinstance(value, dict):
                    item = dict(value)
                    item.setdefault("email", email)
                    raw_contacts.append(item)
        else:
            raw_contacts = []

        contacts: List[Dict[str, Any]] = []
        seen: set = set()
        for item in raw_contacts:
            if not isinstance(item, dict):
                continue
            email = _clean_email(item.get("email", ""))
            if not _looks_like_email(email):
                continue
            key = email.lower()
            if key in seen:
                continue
            seen.add(key)

            categories = item.get(
                "categories",
                item.get("category", item.get("group", "Okategoriserad")),
            )
            if isinstance(categories, str):
                categories = [categories]
            if not isinstance(categories, list):
                categories = ["Okategoriserad"]

            contacts.append(
                {
                    "email": email,
                    "name": str(item.get("name", "") or email),
                    "company": str(item.get("company", "") or ""),
                    "categories": [
                        str(cat)
                        for cat in categories
                        if str(cat).strip()
                    ]
                    or ["Okategoriserad"],
                }
            )
        return contacts

    def _contact_lang(self, email: str) -> str:
        """(v5.3) Språk för en kontakt från adressboken, annars 'sv'."""
        store = getattr(self, "_contact_store", None)
        if store is not None:
            try:
                contact = store.get(email)
                if contact is not None:
                    lang = str(getattr(contact, "language", "sv") or "sv")
                    return "en" if lang.lower() == "en" else "sv"
            except Exception:
                log.debug("Kunde inte läsa kontaktspråk för %s", email,
                          exc_info=True)
        return "sv"

    def _address_book_add_callback(
        self, emails: List[str], target: str
    ) -> None:
        """Callback från AddressBookDialog – dialogen ska förbli öppen."""
        added = 0
        for email in emails:
            added += self._add_recipient(
                target,
                email=email,
                show_warning=False,
                lang=self._contact_lang(email),
            )
        self._refresh_preview()
        if added:
            self._status(
                f"📒 {added} mottagare tillagda i "
                f"{'To' if target == 'to' else 'Bcc'}",
                "success",
            )
        else:
            self._status("ℹ️ Inga nya mottagare tillagda", "info")

    def _open_address_book(self) -> None:
        if AddressBookDialog is not None and self._contact_store is not None:
            try:
                dialog = AddressBookDialog(
                    self,
                    self._contact_store,
                    self._style,
                    on_add=self._address_book_add_callback,
                )
                dialog.show()
                return
            except TypeError:
                # Om äldre signatur saknar on_add, kör kompatibilitetsväg.
                try:
                    dialog = AddressBookDialog(
                        self, self._contact_store, self._style
                    )
                    result = dialog.show()
                    for email in result.get("to", []):
                        self._add_recipient(
                            "to",
                            email=email,
                            show_warning=False,
                            lang=self._contact_lang(email),
                        )
                    for email in result.get("bcc", []):
                        self._add_recipient(
                            "bcc",
                            email=email,
                            show_warning=False,
                            lang=self._contact_lang(email),
                        )
                    self._refresh_preview()
                    return
                except Exception:
                    log.exception(
                        "Kunde inte öppna AddressBookDialog via "
                        "kompatibilitetsväg"
                    )
            except Exception:
                log.exception("Kunde inte öppna AddressBookDialog")

        # Fallback om script.recipients saknas.
        contacts = self._load_contacts_for_address_book()
        if not contacts:
            QMessageBox.information(
                self,
                "Adressbok",
                "Inga kontakter hittades i adresslistor/contacts.json.",
            )
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("📒 Adressbok – välj mottagare")
        dialog.setModal(True)
        dialog.resize(760, 520)

        layout = QVBoxLayout(dialog)
        info = QLabel(
            "Markera kontakter och välj om de ska läggas i To eller Bcc. "
            "Dialogen stannar öppen."
        )
        info.setProperty("cssClass", "subtext")
        layout.addWidget(info)

        tree = QTreeWidget()
        tree.setColumnCount(4)
        tree.setHeaderLabels(["Namn", "E-post", "Företag", "Kategorier"])
        tree.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        tree.setRootIsDecorated(False)
        tree.setAlternatingRowColors(True)
        for contact in contacts:
            row = QTreeWidgetItem(
                [
                    contact["name"],
                    contact["email"],
                    contact["company"],
                    ", ".join(contact["categories"]),
                ]
            )
            row.setData(0, Qt.ItemDataRole.UserRole, contact["email"])
            tree.addTopLevelItem(row)
        tree.resizeColumnToContents(0)
        tree.resizeColumnToContents(1)
        layout.addWidget(tree, stretch=1)

        feedback = QLabel(
            "Välj kontakter och klicka på Lägg till som To/Bcc."
        )
        feedback.setProperty("cssClass", "subtext")
        feedback.setWordWrap(True)
        layout.addWidget(feedback)

        buttons = QHBoxLayout()
        btn_all = QPushButton("Markera alla")
        btn_all.clicked.connect(lambda: tree.selectAll())
        buttons.addWidget(btn_all)

        btn_none = QPushButton("Avmarkera")
        btn_none.clicked.connect(lambda: tree.clearSelection())
        buttons.addWidget(btn_none)

        buttons.addStretch()

        btn_to = QPushButton("➕ Lägg i To")
        btn_to.setProperty("cssClass", "accent")
        buttons.addWidget(btn_to)

        btn_bcc = QPushButton("➕ Lägg i Bcc")
        btn_bcc.setProperty("cssClass", "purple")
        buttons.addWidget(btn_bcc)

        # (v5.5) Lägg till ALLA visade kontakter direkt i To/Bcc
        btn_all_to = QPushButton("➕ Alla visade → To")
        btn_all_to.setProperty("cssClass", "accent")
        btn_all_to.clicked.connect(lambda: add_all("to"))
        buttons.addWidget(btn_all_to)

        btn_all_bcc = QPushButton("➕ Alla visade → Bcc")
        btn_all_bcc.setProperty("cssClass", "purple")
        btn_all_bcc.clicked.connect(lambda: add_all("bcc"))
        buttons.addWidget(btn_all_bcc)

        btn_done = QPushButton("✅ Klar")
        btn_done.clicked.connect(dialog.accept)
        buttons.addWidget(btn_done)

        btn_cancel = QPushButton("Stäng")
        btn_cancel.clicked.connect(dialog.reject)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

        def selected_emails() -> List[str]:
            return _dedupe(
                [
                    str(item.data(0, Qt.ItemDataRole.UserRole) or "")
                    for item in tree.selectedItems()
                ]
            )

        def add_selected(target: str) -> None:
            emails = selected_emails()
            if not emails:
                QMessageBox.information(
                    dialog, "Adressbok", "Markera minst en kontakt först."
                )
                return
            added = 0
            for email in emails:
                added += self._add_recipient(
                    target,
                    email=email,
                    show_warning=False,
                    lang=self._contact_lang(email),
                )
            self._refresh_preview()
            feedback.setText(
                f"✅ {added} adress(er) lades till i "
                f"{'To' if target == 'to' else 'Bcc'}."
            )

        def all_emails() -> List[str]:
            """Alla e-postadresser i trädet (alla visade kontakter)."""
            emails: List[str] = []
            for index in range(tree.topLevelItemCount()):
                item = tree.topLevelItem(index)
                raw = item.data(0, Qt.ItemDataRole.UserRole)
                if raw:
                    emails.append(str(raw))
            return _dedupe(emails)

        def add_all(target: str) -> None:
            """(v5.5) Lägg till ALLA visade kontakter direkt i To/Bcc."""
            emails = all_emails()
            if not emails:
                QMessageBox.information(
                    dialog,
                    "Adressbok",
                    "Inga kontakter att lägga till.",
                )
                return
            added = 0
            for email in emails:
                added += self._add_recipient(
                    target,
                    email=email,
                    show_warning=False,
                    lang=self._contact_lang(email),
                )
            self._refresh_preview()
            feedback.setText(
                f"✅ {added} adress(er) lades till i "
                f"{'To' if target == 'to' else 'Bcc'} "
                f"(alla visade)."
            )

        btn_to.clicked.connect(lambda: add_selected("to"))
        btn_bcc.clicked.connect(lambda: add_selected("bcc"))
        tree.itemDoubleClicked.connect(lambda *_args: add_selected("to"))
        dialog.exec()

    def _add_recipient(
        self,
        target: str,
        email: Optional[str] = None,
        show_warning: bool = True,
        lang: Optional[str] = None,
    ) -> int:
        line = self._to_input if target == "to" else self._bcc_input
        list_widget = self._to_list if target == "to" else self._bcc_list

        value = (email if email is not None else line.text()).strip()
        if not value:
            return 0
        if not _looks_like_email(value):
            if show_warning:
                QMessageBox.warning(
                    self,
                    "Ogiltig e-post",
                    f"'{value}' ser inte ut som en e-postadress.",
                )
            return 0

        current = self._list_items(list_widget)
        if value.lower() in {item.lower() for item in current}:
            if email is None:
                line.clear()
            return 0

        # (v5.2) Språk för mottagaren: explicit → dropdown → SV
        if lang is None:
            lang = "sv"
            combo = getattr(self, "_new_lang_combo", None)
            if combo is not None:
                try:
                    lang = str(combo.currentData() or "sv")
                except Exception:
                    lang = "sv"

        item = QListWidgetItem(f"{value} {_lang_tag(lang)}")
        item.setData(Qt.ItemDataRole.UserRole, "en" if str(lang).lower() == "en" else "sv")
        list_widget.addItem(item)
        if email is None:
            line.clear()
        self._update_en_only_placeholder_visibility()
        self._refresh_preview()
        return 1

    def _remove_selected_recipients(self, target: str) -> None:
        list_widget = self._to_list if target == "to" else self._bcc_list
        for item in reversed(list_widget.selectedItems()):
            list_widget.takeItem(list_widget.row(item))
        self._update_en_only_placeholder_visibility()
        self._refresh_preview()

    def _clear_recipients(self, target: str) -> None:
        list_widget = self._to_list if target == "to" else self._bcc_list
        list_widget.clear()
        self._update_en_only_placeholder_visibility()
        self._refresh_preview()

    def _list_items(self, widget: QListWidget) -> List[str]:
        """Alla e-postadresser i listan (språktaggen tas bort, v5.2)."""
        return [
            _strip_lang_tag(widget.item(index).text()).strip()
            for index in range(widget.count())
            if _strip_lang_tag(widget.item(index).text()).strip()
        ]

    def _list_langs(self, widget: QListWidget) -> Dict[str, str]:
        """(v5.2) Språk per mottagare: {e-post: "sv"/"en"} (fallback sv)."""
        langs: Dict[str, str] = {}
        for index in range(widget.count()):
            item = widget.item(index)
            email = _strip_lang_tag(item.text()).strip()
            if not email:
                continue
            raw = str(item.data(Qt.ItemDataRole.UserRole) or "sv")
            langs[email] = "en" if raw.lower() == "en" else "sv"
        return langs

    def _has_en_recipient(self) -> bool:
        """True om minst en To/Bcc-mottagare är märkt [EN]."""
        try:
            to_lang = self._list_langs(self._to_list) if hasattr(self, "_to_list") else {}
            bcc_lang = (
                self._list_langs(self._bcc_list) if hasattr(self, "_bcc_list") else {}
            )
        except Exception:
            return False
        return any(v == "en" for v in to_lang.values()) or any(
            v == "en" for v in bcc_lang.values()
        )

    def _update_en_only_placeholder_visibility(self) -> None:
        """Visa VIN-fältet bara när det finns EN-mottagare."""
        show = self._has_en_recipient()
        rows = getattr(self, "_ph_row_widgets", {}) or {}
        for key, widgets in rows.items():
            if str(key).lower() not in EN_ONLY_PLACEHOLDERS:
                continue
            for widget in widgets:
                try:
                    widget.setVisible(show)
                except Exception:
                    pass
        self._update_ph_status()

    def _toggle_recipient_lang(
        self, widget: QListWidget, item: Any
    ) -> None:
        """(v5.2) Dubbelklick: växla språk SV↔EN för en mottagare."""
        email = _strip_lang_tag(item.text()).strip()
        if not email:
            return
        current = str(item.data(Qt.ItemDataRole.UserRole) or "sv")
        new_lang = "sv" if current.lower() == "en" else "en"
        item.setText(f"{email} {_lang_tag(new_lang)}")
        item.setData(Qt.ItemDataRole.UserRole, new_lang)
        self._update_en_only_placeholder_visibility()
        self._refresh_preview()
        self._status(f"🌐 {email}: {_lang_tag(new_lang)}", "info")

    def _recipient_context_menu(
        self, widget: QListWidget, target: str, pos: QPoint
    ) -> None:
        """(v5.2) Högerklick: sätt språk SV/EN på markerade mottagare."""
        del target
        item = widget.itemAt(pos)
        if item is not None and not item.isSelected():
            widget.setCurrentItem(item)
            item.setSelected(True)
        selected = widget.selectedItems()
        if not selected:
            return

        menu = QMenu(self)
        act_sv = menu.addAction("🇸🇪 Sätt svenska (SV)")
        act_en = menu.addAction("🇬🇧 Sätt engelska (EN)")
        chosen = menu.exec(widget.viewport().mapToGlobal(pos))
        if chosen is None:
            return
        new_lang = "en" if chosen == act_en else "sv"
        for it in selected:
            email = _strip_lang_tag(it.text()).strip()
            if not email:
                continue
            it.setText(f"{email} {_lang_tag(new_lang)}")
            it.setData(Qt.ItemDataRole.UserRole, new_lang)
        self._refresh_preview()
        self._status(
            f"🌐 {len(selected)} mottagare: {_lang_tag(new_lang)}", "info"
        )

    def _load_default_recipients(self) -> None:
        """Ladda standard-To + standard-Bcc + arkivkopia (v4.9).

        Körs vid start OCH efter formulärrensning – så standardadresserna
        kommer alltid tillbaka efter att mailet skickats.
        """
        # Standard-To (v4.9) – slipper lägga till varje gång
        for email in self.settings.get("default_to", []) or []:
            if isinstance(email, str) and _looks_like_email(email):
                self._add_recipient("to", email=email, show_warning=False)

        # Standard-Bcc
        for email in self.settings.get("default_bcc", []) or []:
            if isinstance(email, str) and _looks_like_email(email):
                self._add_recipient("bcc", email=email, show_warning=False)

        # Arkivkopia: fast adress som alltid får kopia (dold Bcc)
        archive = str(
            self.settings.get("archive_copy_email", "") or ""
        ).strip()
        if archive and _looks_like_email(archive):
            self._add_recipient("bcc", email=archive, show_warning=False)

        bcc_count = self._bcc_list.count()
        if bcc_count and self.bus is not None:
            try:
                self.bus.publish(
                    "recipients.default_loaded", {"bcc_count": bcc_count}
                )
            except Exception:
                log.debug(
                    "recipients.default_loaded publish misslyckades",
                    exc_info=True,
                )

    # Bakåtkompatibelt alias
    _load_default_bcc = _load_default_recipients

    # ────────────────────────────────────────────────────────────────
    # Preview och sändsammanfattning
    # ────────────────────────────────────────────────────────────────

    def _refresh_preview(self) -> None:
        preview = getattr(self, "preview_tab", None)
        if preview is None or not hasattr(preview, "render"):
            return
        try:
            body = self._editor.toPlainText()
            free_text = (
                self._free_edit.toPlainText().strip()
                if hasattr(self, "_free_edit")
                else ""
            )
            if free_text:
                body = (
                    f"{body}\n\n{free_text}\n\n"
                    f"(Signaturen placeras efter detta vid sändning.)"
                )
            subject_for_preview = self._ensure_subject_contains_model_and_reg(
                update_field=False
            )
            preview.render(
                subject_for_preview, body, placeholders=self._get_ph()
            )
            self._update_send_summary()
        except Exception:
            log.debug("Kunde inte uppdatera preview", exc_info=True)

    def _update_send_summary(self) -> None:
        if not hasattr(self, "_send_summary"):
            return
        to_n = self._to_list.count() if hasattr(self, "_to_list") else 0
        bcc_n = self._bcc_list.count() if hasattr(self, "_bcc_list") else 0
        img_n = sum(1 for path in self._attachments if _is_image(path))
        file_n = len(self._attachments) - img_n
        subject_text = (
            self._ensure_subject_contains_model_and_reg(update_field=False)
            or "(tomt)"
        )
        # (v5.2) Språkfördelning i sammanfattningen
        lang_text = ""
        if hasattr(self, "_to_list") and hasattr(self, "_bcc_list"):
            en_n = sum(
                1 for v in self._list_langs(self._to_list).values() if v == "en"
            ) + sum(
                1 for v in self._list_langs(self._bcc_list).values() if v == "en"
            )
            total_n = to_n + bcc_n
            if total_n > 0:
                lang_text = f" · 🌐 SV {total_n - en_n} · EN {en_n}"
        self._send_summary.setText(
            f"Till: {to_n} · Bcc: {bcc_n} · Bilagor: {len(self._attachments)} "
            f"({img_n} bilder, {file_n} övriga filer){lang_text} · "
            f"Ämne: {subject_text}"
        )

    # ────────────────────────────────────────────────────────────────
    # Kontakter-flik
    # ────────────────────────────────────────────────────────────────

    def _build_contacts_tab(self) -> QWidget:
        # Primär modern implementation via separat ContactsTab-modul.
        if ContactsTabUI is not None and self._contact_store is not None:
            try:
                self._contacts_tab = ContactsTabUI(
                    parent=self,
                    store=self._contact_store,
                    event_bus=self.bus,
                    on_add_to=self._contacts_tab_add_to,
                    theme_engine=self._style,
                )
                return self._contacts_tab
            except Exception:
                log.warning(
                    "Kunde inte initiera ContactsTabUI – fallback används",
                    exc_info=True,
                )

        # Fallback om extern kontaktflik inte är tillgänglig.
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        top = QHBoxLayout()
        self._contacts_search = QLineEdit()
        self._contacts_search.setPlaceholderText(
            "Sök namn, e-post, företag eller kategori…"
        )
        self._contacts_search.textChanged.connect(
            self._populate_contacts_table
        )
        top.addWidget(self._contacts_search, stretch=1)

        btn_reload = QPushButton("🔄 Ladda om")
        btn_reload.clicked.connect(self._reload_contacts_tab)
        top.addWidget(btn_reload)

        btn_add = QPushButton("➕ Ny kontakt")
        btn_add.setProperty("cssClass", "success")
        btn_add.clicked.connect(self._add_contact)
        top.addWidget(btn_add)

        btn_edit = QPushButton("✏️ Redigera")
        btn_edit.clicked.connect(self._edit_contact)
        top.addWidget(btn_edit)

        btn_delete = QPushButton("🗑️ Ta bort")
        btn_delete.setProperty("cssClass", "danger")
        btn_delete.clicked.connect(self._delete_contact)
        top.addWidget(btn_delete)
        layout.addLayout(top)

        self._contacts_info = QLabel("Kontakter laddas när fliken öppnas.")
        self._contacts_info.setProperty("cssClass", "subtext")
        layout.addWidget(self._contacts_info)

        self._contacts_table = QTableWidget(0, 4)
        self._contacts_table.setHorizontalHeaderLabels(
            ["Namn", "E-post", "Företag", "Kategorier"]
        )
        self._contacts_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._contacts_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._contacts_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._contacts_table.setAlternatingRowColors(True)
        self._contacts_table.itemDoubleClicked.connect(
            lambda *_args: self._edit_contact()
        )
        layout.addWidget(self._contacts_table, stretch=1)
        return widget

    def _contacts_tab_add_to(self, emails: List[str], target: str) -> None:
        """Callback från ContactsTab för att lägga markerade i To/Bcc."""
        added = 0
        for email in emails:
            added += self._add_recipient(
                target,
                email=email,
                show_warning=False,
                lang=self._contact_lang(email),
            )
        self._refresh_preview()
        if added:
            self._status(
                f"👥 {added} kontakt(er) lades till i "
                f"{'To' if target == 'to' else 'Bcc'}",
                "success",
            )
        else:
            self._status("ℹ️ Inga nya mottagare tillagda", "info")

    def _reload_contacts_tab(self) -> None:
        if hasattr(self, "_contacts_tab") and self._contacts_tab is not None:
            try:
                if hasattr(self._contacts_tab, "reload"):
                    self._contacts_tab.reload()
                elif hasattr(self._contacts_tab, "refresh_list"):
                    self._contacts_tab.refresh_list()
                return
            except Exception:
                log.warning(
                    "Kunde inte ladda om ContactsTabUI", exc_info=True
                )

        if self._contact_store is None:
            if hasattr(self, "_contacts_info"):
                self._contacts_info.setText(
                    "⚠️ Kontaktlagring är inte tillgänglig."
                )
            return

        try:
            self._contact_store.reload()
        except Exception:
            log.warning("Kunde inte ladda om ContactStore", exc_info=True)
        self._populate_contacts_table()

    def _populate_contacts_table(self) -> None:
        if self._contact_store is None:
            return
        query = (
            self._contacts_search.text().strip().lower()
            if hasattr(self, "_contacts_search")
            else ""
        )
        contacts = self._contact_store.all()
        if query:
            filtered = []
            for contact in contacts:
                categories = ", ".join(getattr(contact, "categories", []))
                haystack = " | ".join(
                    [
                        str(getattr(contact, "name", "")),
                        str(getattr(contact, "email", "")),
                        str(getattr(contact, "company", "")),
                        categories,
                    ]
                ).lower()
                if query in haystack:
                    filtered.append(contact)
            contacts = filtered

        contacts.sort(
            key=lambda contact: (
                getattr(contact, "name", "")
                or getattr(contact, "email", "")
            ).lower()
        )

        table = self._contacts_table
        table.setRowCount(len(contacts))
        for row, contact in enumerate(contacts):
            name = str(getattr(contact, "name", ""))
            email = str(getattr(contact, "email", ""))
            company = str(getattr(contact, "company", ""))
            categories = ", ".join(getattr(contact, "categories", []))
            values = [name, email, company, categories]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column == 1:
                    item.setData(Qt.ItemDataRole.UserRole, email)
                table.setItem(row, column, item)
        table.resizeColumnsToContents()
        self._contacts_info.setText(f"📒 {len(contacts)} kontakt(er) visas")

    def _selected_contact_email(self) -> Optional[str]:
        items = self._contacts_table.selectedItems()
        if not items:
            return None
        row = items[0].row()
        item = self._contacts_table.item(row, 1)
        return item.text().strip() if item else None

    def _add_contact(self) -> None:
        if (
            self._contact_store is None
            or AddContactDialog is None
            or _StoreAdapter is None
        ):
            QMessageBox.warning(
                self, "Kontakter", "Kontaktredigering är inte tillgänglig just nu."
            )
            return
        adapter = _StoreAdapter(self._contact_store)
        dialog = AddContactDialog(self, adapter, self._style)
        result = dialog.show()
        if result:
            self._reload_contacts_tab()
            self._status(
                f"✅ Kontakt sparad: {result.display_name()}", "success"
            )

    def _edit_contact(self) -> None:
        email = self._selected_contact_email()
        if not email:
            QMessageBox.information(
                self, "Kontakter", "Markera en kontakt först."
            )
            return
        if (
            self._contact_store is None
            or AddContactDialog is None
            or _StoreAdapter is None
        ):
            QMessageBox.warning(
                self, "Kontakter", "Kontaktredigering är inte tillgänglig just nu."
            )
            return
        contact = self._contact_store.get(email)
        if contact is None:
            return
        adapter = _StoreAdapter(self._contact_store)
        dialog = AddContactDialog(
            self, adapter, self._style, edit_contact=contact
        )
        result = dialog.show()
        if result:
            self._reload_contacts_tab()
            self._status(
                f"✅ Kontakt uppdaterad: {result.display_name()}", "success"
            )

    def _delete_contact(self) -> None:
        email = self._selected_contact_email()
        if not email:
            QMessageBox.information(
                self, "Kontakter", "Markera en kontakt först."
            )
            return
        if self._contact_store is None:
            return

        reply = QMessageBox.question(
            self,
            "Ta bort kontakt",
            f"Vill du ta bort {email}?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        try:
            if self._contact_store.delete(email):
                self._contact_store.save()
                self._reload_contacts_tab()
                self._status(f"🗑️ Kontakt borttagen: {email}", "success")
        except Exception:
            log.exception("Kunde inte ta bort kontakt")
            QMessageBox.critical(
                self, "Kontakter", "Kunde inte ta bort kontakt."
            )

    # ────────────────────────────────────────────────────────────────
    # Historik-flik
    # ────────────────────────────────────────────────────────────────

    def _build_history_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        header = QFrame()
        header.setProperty("cssClass", "step-green")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 10, 16, 10)
        title = QLabel("📨 Historik över skickade mail")
        title.setStyleSheet(
            "color: #FFFFFF; font-size: 13pt; font-weight: bold; "
            "background: transparent;"
        )
        header_layout.addWidget(title, stretch=1)
        layout.addWidget(header)

        self._history_table = QTableWidget(0, 7)
        self._history_table.setHorizontalHeaderLabels(
            ["Tid", "Ämne", "Mall", "To", "Bcc", "Bilagor", "Status"]
        )
        self._history_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self._history_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self._history_table.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        self._history_table.setAlternatingRowColors(True)
        self._history_table.setToolTip(
            "Dubbelklicka en rad för att öppna mailet i Skicka-fliken."
        )
        self._history_table.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self._history_table.customContextMenuRequested.connect(
            self._history_context_menu
        )
        # Dubbelklick på rad → öppna för redigering/återsändning (v4.9)
        self._history_table.itemDoubleClicked.connect(
            self._on_history_double_clicked
        )
        self._history_table.itemSelectionChanged.connect(
            self._update_history_open_button
        )
        layout.addWidget(self._history_table, stretch=1)

        hint = QLabel(
            "💡 Markera ett mail och klicka ✏️ Öppna / skicka om "
            "(eller dubbelklicka raden). Högerklick ger samma meny."
        )
        hint.setWordWrap(True)
        hint.setProperty("cssClass", "subtext")
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        self._btn_open_history_mail = QPushButton("✏️ Öppna / skicka om")
        self._btn_open_history_mail.setProperty("cssClass", "send")
        self._btn_open_history_mail.setToolTip(
            "Öppna valt mail i Skicka-fliken för redigering eller återsändning."
        )
        self._btn_open_history_mail.clicked.connect(self._open_selected_history)
        self._btn_open_history_mail.setEnabled(False)
        buttons.addWidget(self._btn_open_history_mail)

        btn_refresh = QPushButton("🔄 Uppdatera")
        btn_refresh.setProperty("cssClass", "accent")
        btn_refresh.clicked.connect(self._refresh_history)
        buttons.addWidget(btn_refresh)

        btn_open = QPushButton("📂 Öppna historikfil")
        btn_open.clicked.connect(self._open_history_file)
        buttons.addWidget(btn_open)

        btn_clear = QPushButton("🧹 Rensa historik")
        btn_clear.setProperty("cssClass", "danger")
        btn_clear.clicked.connect(self._clear_history)
        buttons.addWidget(btn_clear)

        buttons.addStretch()
        layout.addLayout(buttons)

        self._refresh_history()
        return widget

    def _history_path(self) -> Path:
        path = self._base_dir() / ".data" / "sent_history.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _load_history(self) -> List[Dict[str, Any]]:
        path = self._history_path()
        if not path.exists():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
            return data if isinstance(data, list) else []
        except Exception:
            log.warning("Kunde inte läsa sändhistorik", exc_info=True)
            return []

    def _save_history(self, rows: List[Dict[str, Any]]) -> None:
        path = self._history_path()
        path.write_text(
            json.dumps(rows[-500:], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _append_send_history(self, result: SendResult) -> None:
        params = dict(self._last_send_params or {})
        row = {
            "timestamp": datetime.datetime.now().isoformat(
                timespec="seconds"
            ),
            "subject": getattr(result, "subject", "")
            or params.get("subject", ""),
            "template": params.get(
                "template_name",
                self._tpl_combo.currentText()
                if hasattr(self, "_tpl_combo")
                else "",
            ),
            "to": list(params.get("recipients_to", [])),
            "bcc": list(params.get("recipients_bcc", [])),
            # (v5.2) Språk per mottagare sparas för återsändning
            "to_lang": dict(params.get("recipients_to_lang", {}) or {}),
            "bcc_lang": dict(params.get("recipients_bcc_lang", {}) or {}),
            "attachments": [
                Path(path).name for path in params.get("attachments", [])
            ],
            "attachments_count": len(params.get("attachments", [])),
            "success": bool(getattr(result, "success", False)),
            "elapsed_seconds": float(
                getattr(result, "elapsed_seconds", 0) or 0
            ),
            # (v4.8) Extra data för "Öppna för redigering / Skicka om"
            "template_name": params.get("template_name", ""),
            "body": str(params.get("body_plain", "") or ""),
            "free_text": str(params.get("free_text", "") or ""),
            "replacements": dict(params.get("replacements", {}) or {}),
            "include_english": bool(params.get("include_english", False)),
            "attachment_paths": [
                str(path) for path in params.get("attachments", [])
            ],
        }
        rows = self._load_history()
        rows.append(row)
        self._save_history(rows)
        self._refresh_history()

    def _refresh_history(self) -> None:
        table = getattr(self, "_history_table", None)
        if table is None:
            return
        self._history_rows = list(reversed(self._load_history()))
        table.setRowCount(len(self._history_rows))
        for row_idx, item in enumerate(self._history_rows):
            values = [
                str(item.get("timestamp", "")).replace("T", " "),
                str(item.get("subject", "")),
                str(item.get("template", "")),
                str(len(item.get("to", []) or [])),
                str(len(item.get("bcc", []) or [])),
                str(
                    item.get(
                        "attachments_count",
                        len(item.get("attachments", []) or []),
                    )
                ),
                "✅ Skickat" if item.get("success", False) else "❌ Fel",
            ]
            for col, value in enumerate(values):
                table.setItem(row_idx, col, QTableWidgetItem(value))
        table.resizeColumnsToContents()
        self._update_history_open_button()

    def _history_current_row(self) -> int:
        table = getattr(self, "_history_table", None)
        if table is None:
            return -1
        return history_selected_row(
            table.currentRow(), len(getattr(self, "_history_rows", []) or [])
        )

    def _update_history_open_button(self) -> None:
        btn = getattr(self, "_btn_open_history_mail", None)
        if btn is None:
            return
        btn.setEnabled(self._history_current_row() >= 0)

    def _on_history_double_clicked(self, item: QTableWidgetItem) -> None:
        if item is None:
            return
        self._open_history_for_edit(item.row())

    def _open_selected_history(self) -> None:
        row = self._history_current_row()
        if row < 0:
            QMessageBox.information(
                self,
                "Historik",
                "Markera ett mail i listan och klicka ✏️ Öppna / skicka om.\n\n"
                "Tips: dubbelklicka på raden.",
            )
            return
        self._open_history_for_edit(row)

    def _history_context_menu(self, pos: QPoint) -> None:
        row = self._history_table.rowAt(pos.y())
        if row < 0 or row >= len(self._history_rows):
            return
        self._history_table.selectRow(row)

        menu = QMenu(self)
        menu.addAction(
            "✏️ Öppna för redigering / Skicka om",
            lambda: self._open_history_for_edit(row),
        )
        menu.addSeparator()
        menu.addAction(
            "👁️ Visa mottagare",
            lambda: self._show_history_recipients(row),
        )
        menu.addAction(
            "📋 Kopiera mottagare",
            lambda: self._copy_history_recipients(row),
        )
        menu.exec(self._history_table.viewport().mapToGlobal(pos))

    def _show_history_recipients(self, row: int) -> None:
        if row < 0 or row >= len(self._history_rows):
            return
        item = self._history_rows[row]
        to_list = list(item.get("to", []) or [])
        bcc_list = list(item.get("bcc", []) or [])
        total = len(to_list) + len(bcc_list)

        text = (
            f"Ämne: {item.get('subject', '')}\n"
            f"Mall: {item.get('template', '')}\n\n"
            f"To ({len(to_list)}):\n"
            + ("\n".join(to_list) if to_list else "(inga)")
            + "\n\n"
            f"Bcc ({len(bcc_list)}):\n"
            + ("\n".join(bcc_list) if bcc_list else "(inga)")
            + "\n\n"
            f"Totalt: {total} mottagare"
        )
        QMessageBox.information(self, "Mottagare för vald historikpost", text)

    def _copy_history_recipients(self, row: int) -> None:
        if row < 0 or row >= len(self._history_rows):
            return
        item = self._history_rows[row]
        recipients = _dedupe(
            list(item.get("to", []) or []) + list(item.get("bcc", []) or [])
        )
        if recipients:
            QApplication.clipboard().setText(
                "\n".join(recipients), QClipboard.Mode.Clipboard
            )
            self._status("📋 Mottagare kopierade från historiken", "success")

    def _open_history_for_edit(self, row: int) -> None:
        """Öppna en historikpost i formuläret för redigering/återsändning (v4.8).

        Återställer mall, ämne, brödtext, platshållarvärden, mottagare,
        fritext, engelska och bilagor (om sökvägarna finns sparade).
        Äldre historikposter utan extra-data återställer det som finns.
        """
        if row < 0 or row >= len(self._history_rows):
            return
        item = self._history_rows[row]

        tpl_name = str(
            item.get("template_name", "")
            or item.get("template", "")
            or ""
        ).strip()
        history_subject = str(item.get("subject", "") or "").strip()
        history_body = str(item.get("body", "") or "").strip()
        history_free = str(item.get("free_text", "") or "").strip()
        history_to = list(item.get("to", []) or [])
        history_bcc = list(item.get("bcc", []) or [])
        # (v5.2) Språktaggar från historiken återställs
        history_to_lang = dict(item.get("to_lang", {}) or {})
        history_bcc_lang = dict(item.get("bcc_lang", {}) or {})
        history_repl = dict(item.get("replacements", {}) or {})
        history_paths = list(item.get("attachment_paths", []) or [])

        # 1. Välj mall (om den fortfarande finns)
        tpl_loaded = False
        if tpl_name:
            idx = self._tpl_combo.findText(tpl_name)
            if idx >= 0:
                self._tpl_combo.setCurrentIndex(idx)
                self._on_tpl_sel(tpl_name)
                tpl_loaded = True
            else:
                log.warning(
                    "Historik: mallen '%s' saknas – återställer utan mall.",
                    tpl_name,
                )

        # 2. Ämne + brödtext (från historiken – kan skilja sig från mallfilen)
        self._subject.blockSignals(True)
        self._subject.setText(history_subject)
        self._subject.blockSignals(False)
        if history_body:
            self._editor.blockSignals(True)
            self._editor.setPlainText(history_body)
            self._editor.blockSignals(False)

        # 3. (v5.4) Ingen engelsk-knapp – mottagarnas språktaggar styr
        #    (återställs i steg 5 → engelska skickas automatiskt)

        # 4. Platshållarvärden (återuppbyggs med sparade värden)
        self.settings.set("replacements_values", history_repl)
        self._rebuild_ph()

        # 5. Mottagare (v5.2: språktaggar återställs)
        self._to_list.clear()
        self._bcc_list.clear()
        for email in history_to:
            self._add_recipient(
                "to",
                email=email,
                show_warning=False,
                lang=history_to_lang.get(email, "sv"),
            )
        for email in history_bcc:
            self._add_recipient(
                "bcc",
                email=email,
                show_warning=False,
                lang=history_bcc_lang.get(email, "sv"),
            )

        # 6. Fritext
        if history_free:
            self._free_edit.setPlainText(history_free)

        # 7. Bilagor – endast om fullständiga sökvägar finns kvar
        missing_attachments = 0
        if history_paths:
            existing = [p for p in history_paths if Path(p).exists()]
            self._add_attachment_paths(existing)
            missing_attachments = len(history_paths) - len(existing)
        else:
            missing_attachments = len(item.get("attachments", []) or [])

        # 8. Visa Skicka-fliken + uppdatera
        self.select_tab("send")
        self._refresh_preview()
        self._update_send_summary()

        # Status: tydlig återkoppling om något inte kunde återställas
        msg, style = history_open_feedback(
            tpl_loaded, tpl_name, missing_attachments
        )
        self._status(msg, style)

    def _open_history_file(self) -> None:
        self._explorer(self._history_path())

    def _clear_history(self) -> None:
        reply = QMessageBox.question(
            self,
            "Rensa historik",
            "Vill du rensa historiken över skickade mail?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self._save_history([])
        self._refresh_history()
        self._status("🧹 Historik rensad", "success")

    # ────────────────────────────────────────────────────────────────
    # Loggar-flik
    # ────────────────────────────────────────────────────────────────

    def _build_log_tab(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._log_edit = QPlainTextEdit()
        self._log_edit.setReadOnly(True)
        self._log_edit.setFont(QFont("Consolas", 9))
        layout.addWidget(self._log_edit, stretch=1)

        buttons = QHBoxLayout()
        btn_refresh = QPushButton("🔄 Uppdatera")
        btn_refresh.setProperty("cssClass", "accent")
        btn_refresh.clicked.connect(self._refresh_log)
        buttons.addWidget(btn_refresh)

        btn_open = QPushButton("📂 Öppna")
        btn_open.clicked.connect(self._open_log)
        buttons.addWidget(btn_open)

        btn_clear = QPushButton("🧹 Rensa")
        btn_clear.setProperty("cssClass", "danger")
        btn_clear.clicked.connect(self._log_edit.clear)
        buttons.addWidget(btn_clear)

        buttons.addStretch()
        layout.addLayout(buttons)
        return widget

    def _refresh_log(self) -> None:
        log_path = self._log_path()
        if not log_path or not log_path.exists():
            self._status("⚠️ Loggfil saknas", "warning")
            return
        self._log_edit.setPlainText(
            log_path.read_text(encoding="utf-8", errors="replace")
        )
        cursor = self._log_edit.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self._log_edit.setTextCursor(cursor)

    def _open_log(self) -> None:
        path = self._log_path()
        if path:
            self._explorer(path)

    def _log_path(self) -> Optional[Path]:
        log_dir = self._base_dir() / "logs"
        try:
            return get_log_file_path(log_dir)
        except Exception:
            path = log_dir / "email_app.log"
            return path if path.exists() else None

    # ────────────────────────────────────────────────────────────────
    # Inställningar-flik (sammanställning + redigerbar)
    # ────────────────────────────────────────────────────────────────

    def _build_settings_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        intro = QLabel(
            "⚙️ Här visas en sammanställning av centrala inställningar. "
            "Du kan redigera och spara dem direkt här."
        )
        intro.setWordWrap(True)
        intro.setProperty("cssClass", "subtext")
        layout.addWidget(intro)

        self._settings_widgets = {}
        layout.addWidget(self._build_settings_group_smtp())
        layout.addWidget(self._build_settings_group_paths())
        layout.addWidget(self._build_settings_group_templates())
        layout.addWidget(self._build_settings_group_ui())
        layout.addWidget(self._build_settings_group_sending())
        layout.addWidget(self._build_settings_group_images())
        layout.addWidget(self._build_settings_group_deliverability())
        layout.addWidget(self._build_settings_group_logging())
        layout.addWidget(self._build_settings_group_updates())
        layout.addWidget(self._build_settings_group_support())

        buttons = QHBoxLayout()
        btn_reload = QPushButton("🔄 Läs om")
        btn_reload.clicked.connect(self._reload_settings_form)
        buttons.addWidget(btn_reload)

        btn_test = QPushButton("🔌 Testa SMTP")
        btn_test.setProperty("cssClass", "purple")
        btn_test.clicked.connect(self._test_smtp_from_settings)
        buttons.addWidget(btn_test)

        buttons.addStretch()

        btn_save = QPushButton("💾 Spara inställningar")
        btn_save.setProperty("cssClass", "success")
        btn_save.clicked.connect(self._save_settings_form)
        buttons.addWidget(btn_save)
        layout.addLayout(buttons)

        layout.addStretch()
        scroll.setWidget(inner)

        self._reload_settings_form()
        return scroll

    def _make_settings_line(
        self, key: str, label_text: str, password: bool = False
    ) -> QLineEdit:
        del label_text
        line = QLineEdit()
        if password:
            line.setEchoMode(QLineEdit.EchoMode.Password)
        self._settings_widgets[key] = line
        return line

    def _make_settings_checkbox(self, key: str, label_text: str) -> QCheckBox:
        checkbox = QCheckBox(label_text)
        self._settings_widgets[key] = checkbox
        return checkbox

    def _make_settings_combo(self, key: str, items: Sequence[str]) -> QComboBox:
        combo = QComboBox()
        combo.addItems(list(items))
        self._settings_widgets[key] = combo
        return combo

    def _build_settings_group_smtp(self) -> QGroupBox:
        group = QGroupBox("📡 SMTP & Avsändare")
        form = QFormLayout(group)
        form.addRow("SMTP-server", self._make_settings_line("smtp_server", "SMTP-server"))
        form.addRow("SMTP-port", self._make_settings_line("smtp_port", "SMTP-port"))
        form.addRow("Avsändaradress", self._make_settings_line("sender_email", "Avsändaradress"))
        form.addRow("Avsändarnamn", self._make_settings_line("sender_name", "Avsändarnamn"))
        form.addRow("Användarnamn", self._make_settings_line("username", "Användarnamn"))
        form.addRow("Lösenord", self._make_settings_line("password", "Lösenord", password=True))
        form.addRow("Reply-To", self._make_settings_line("reply_to", "Reply-To"))
        form.addRow("Own email (To)", self._make_settings_line("own_email", "Own email"))
        form.addRow(
            "Arkivkopia (alltid kopia)",
            self._make_settings_line("archive_copy_email", "Arkivkopia"),
        )
        form.addRow("SSL", self._make_settings_checkbox("use_ssl", "Använd SSL"))
        return group

    def _build_settings_group_paths(self) -> QGroupBox:
        group = QGroupBox("📂 Sökvägar")
        form = QFormLayout(group)
        form.addRow("Mallmapp", self._make_settings_line("template_dir", "Mallmapp"))
        form.addRow("Adressmapp", self._make_settings_line("address_dir", "Adressmapp"))
        form.addRow("Word-filväg", self._make_settings_line("word_file_path", "Word-filväg"))
        form.addRow(
            "Standard-To (kommaseparerat)",
            self._make_settings_line("default_to", "default_to"),
        )
        form.addRow(
            "Standard-Bcc (kommaseparerat)",
            self._make_settings_line("default_bcc", "default_bcc"),
        )
        btn_backup = QPushButton("📦 Säkerhetskopiera adresslistor…")
        btn_backup.setProperty("cssClass", "accent")
        btn_backup.clicked.connect(self._backup_lists_dialog)
        form.addRow("", btn_backup)
        return group

    def _build_settings_group_templates(self) -> QGroupBox:
        """(v5.1) Standardmall – väljs automatiskt vid start."""
        group = QGroupBox("📝 Standardmall")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        row = QHBoxLayout()
        row.addWidget(QLabel("<b>Mall vid start:</b>"))

        self._default_tpl_combo = self._make_settings_combo(
            "default_template", []
        )
        self._default_tpl_combo.setMinimumWidth(320)
        self._refresh_default_template_combo()
        row.addWidget(self._default_tpl_combo, stretch=1)

        btn_refresh = QPushButton("🔄 Uppdatera mallista")
        btn_refresh.clicked.connect(self._refresh_default_template_combo)
        row.addWidget(btn_refresh)
        layout.addLayout(row)

        info = QLabel(
            "Standardmallen väljs automatiskt när appen startar. "
            "Du kan alltid byta i dropdown-menyn på fliken Skicka – "
            "ditt manuella val gäller tills appen startas om."
        )
        info.setProperty("cssClass", "muted")
        info.setWordWrap(True)
        layout.addWidget(info)
        return group

    def _refresh_default_template_combo(self) -> None:
        """(v5.1) Fyll dropdownen med mallarna + sätt aktuellt värde."""
        if not hasattr(self, "_default_tpl_combo"):
            return
        combo = self._default_tpl_combo
        value = (
            self.settings.get_default_template()
            if hasattr(self.settings, "get_default_template")
            else str(self.settings.get("default_template", "") or "").strip()
        )
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("(ingen – senast valda)")
        combo.addItems(self._template_names())
        if value:
            idx = combo.findText(value)
            combo.setCurrentIndex(idx if idx >= 0 else 0)
        else:
            combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def _build_settings_group_ui(self) -> QGroupBox:
        group = QGroupBox(tr("settings.ui_group"))
        form = QFormLayout(group)
        form.addRow("Tema", self._make_settings_combo("theme", ["system", "dark", "light"]))
        form.addRow(tr("settings.language_row"), self._make_settings_combo("language", ["sv", "en"]))
        form.addRow("Start minimerat", self._make_settings_checkbox("start_minimized", "Start minimerat"))
        form.addRow("Close to tray", self._make_settings_checkbox("close_to_tray", "Stäng till tray"))
        form.addRow("Autostart", self._make_settings_checkbox("autostart", "Starta med systemet"))
        # (v5.4) Ingen "Inkludera engelsk del" – språk styrs per mottagare
        return group

    def _build_settings_group_sending(self) -> QGroupBox:
        group = QGroupBox("📤 Sändning")
        form = QFormLayout(group)
        form.addRow("Validera mottagare", self._make_settings_checkbox("validate_recipients", "Validera mottagare"))
        form.addRow("Hoppa över ogiltiga", self._make_settings_checkbox("skip_invalid_recipients", "Hoppa över ogiltiga"))
        form.addRow("Clear form after send", self._make_settings_checkbox("clear_form_after_send", "Rensa formulär efter skickat"))
        form.addRow("Save last recipients", self._make_settings_checkbox("save_last_recipients", "Spara senaste mottagare"))
        form.addRow("Översätt placeholders", self._make_settings_checkbox("translate_placeholders", "Översätt placeholder-värden"))
        form.addRow("BCC batch size", self._make_settings_line("bcc_batch_size", "BCC batch size"))
        form.addRow("Delay between batches", self._make_settings_line("delay_between_batches", "Delay between batches"))
        form.addRow("Max retries", self._make_settings_line("max_retries", "Max retries"))
        form.addRow("SMTP timeout", self._make_settings_line("smtp_timeout", "SMTP timeout"))
        return group

    def _build_settings_group_images(self) -> QGroupBox:
        group = QGroupBox("🖼️ Bildhantering")
        form = QFormLayout(group)
        form.addRow("Komprimera bilder", self._make_settings_checkbox("compress_images", "Komprimera bifogade bilder"))
        form.addRow("Behåll dimensioner", self._make_settings_checkbox("preserve_image_dimensions", "Bevara pixelstorlek"))
        form.addRow("Behåll skärpa", self._make_settings_checkbox("preserve_image_sharpness", "Bevara skärpa så långt möjligt"))
        form.addRow("JPEG-kvalitet", self._make_settings_line("image_jpeg_quality", "JPEG-kvalitet"))
        form.addRow("PNG compress level", self._make_settings_line("image_png_compress_level", "PNG compress level"))
        return group

    def _build_settings_group_deliverability(self) -> QGroupBox:
        """(v5.0) Leveransbarhet: kvitton + guide mot skräppost."""
        group = QGroupBox("📨 Leveransbarhet (mot skräppost)")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        layout.addWidget(
            self._make_settings_checkbox(
                "request_receipts",
                "Begär leverans- och läskvitto (standard för sänddialogen)",
            )
        )
        info = QLabel(
            "Kvitto läggs till per mail – checkboxen i sänddialogen "
            "kan ändras varje gång. Läskvitto via "
            "Disposition-Notification-To, leveranskvitto via SMTP-DSN "
            "när servern stödjer det."
        )
        info.setProperty("cssClass", "muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        btn_guide = QPushButton("📖 Öppna leveransbarhets-guide")
        btn_guide.setProperty("cssClass", "purple")
        btn_guide.clicked.connect(self._open_deliverability_guide)
        layout.addWidget(btn_guide, alignment=Qt.AlignmentFlag.AlignLeft)

        tip = QLabel(
            "Guiden innehåller SPF/DKIM/DMARC-poster för WebSupport, "
            "SMTP-tips och innehållsråd – kopiera DNS-posterna direkt "
            "därifrån."
        )
        tip.setProperty("cssClass", "muted")
        tip.setWordWrap(True)
        layout.addWidget(tip)
        return group

    def _open_deliverability_guide(self) -> None:
        """(v5.0) Öppna leveransbarhets-guiden (dialogs v4.7)."""
        if DeliverabilityGuideDialog is not None:
            try:
                dialog = DeliverabilityGuideDialog(
                    self, theme_engine=self._style
                )
                dialog.exec()
                return
            except Exception:
                log.warning(
                    "Kunde inte öppna DeliverabilityGuideDialog",
                    exc_info=True,
                )
        QMessageBox.information(
            self,
            "Leveransbarhets-guide",
            "Guiden är inte tillgänglig just nu.\n\n"
            "Kontrollera SPF (v=spf1 include:_spf.websupport.se ~all), "
            "DKIM och DMARC hos WebSupport – se tidigare instruktioner.",
        )

    def _build_settings_group_logging(self) -> QGroupBox:
        group = QGroupBox("🧾 Loggning & drift")
        form = QFormLayout(group)
        form.addRow("Debug logging", self._make_settings_checkbox("debug_logging", "Aktivera debug logging"))
        form.addRow("Loggnivå", self._make_settings_combo("log_level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]))
        form.addRow("Mode", self._make_settings_combo("mode", ["prod", "dev"]))
        form.addRow("Smart cache", self._make_settings_checkbox("smart_cache", "Smart cache"))
        return group

    def _build_settings_group_updates(self) -> QGroupBox:
        """(v5.4) GitHub-uppdateringar: autosökning + manuell knapp."""
        group = QGroupBox(tr("update.group"))
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        version_label = QLabel(
            f"<b>{tr('update.current_version', version=APP_VERSION)}</b>"
        )
        layout.addWidget(version_label)

        layout.addWidget(
            self._make_settings_checkbox("auto_update_check", tr("update.auto_check"))
        )

        self._lbl_last_check = QLabel("")
        self._lbl_last_check.setProperty("cssClass", "muted")
        layout.addWidget(self._lbl_last_check)
        self._refresh_last_check_label()

        row = QHBoxLayout()
        btn_check = QPushButton(tr("update.check_now_btn"))
        btn_check.setProperty("cssClass", "accent")
        btn_check.clicked.connect(lambda: self._check_updates(manual=True))
        row.addWidget(btn_check)
        btn_folder = QPushButton(tr("update.from_folder_btn"))
        btn_folder.clicked.connect(self._update_from_folder_dialog)
        row.addWidget(btn_folder)
        row.addStretch()
        layout.addLayout(row)

        hint = QLabel(tr("update.folder_hint"))
        hint.setWordWrap(True)
        hint.setProperty("cssClass", "muted")
        layout.addWidget(hint)
        return group

    def _build_settings_group_support(self) -> QGroupBox:
        """(v5.4) Donation (Ko-fi/PayPal/Swish) + projektlänkar."""
        group = QGroupBox(tr("donate.group"))
        form = QFormLayout(group)

        donation_line = self._make_settings_line("donation_url", "donation_url")
        donation_line.setPlaceholderText(tr("donate.url_placeholder"))
        form.addRow(tr("donate.url_label"), donation_line)

        paypal_line = self._make_settings_line(
            "donation_paypal_url", "donation_paypal_url"
        )
        paypal_line.setPlaceholderText(tr("donate.paypal_placeholder"))
        form.addRow(tr("donate.paypal_label"), paypal_line)

        swish_line = self._make_settings_line("donation_swish", "donation_swish")
        swish_line.setPlaceholderText(tr("donate.swish_placeholder"))
        form.addRow(tr("donate.swish_label"), swish_line)

        defaults_hint = QLabel(tr("donate.defaults_hint"))
        defaults_hint.setProperty("cssClass", "muted")
        defaults_hint.setWordWrap(True)
        form.addRow("", defaults_hint)

        row_widget = QWidget()
        row = QHBoxLayout(row_widget)
        row.setContentsMargins(0, 0, 0, 0)
        btn_donate = QPushButton(tr("donate.open_settings_btn"))
        btn_donate.clicked.connect(self._open_donation_page)
        row.addWidget(btn_donate)
        btn_github = QPushButton(tr("donate.github_btn"))
        btn_github.clicked.connect(lambda: self._open_url(GITHUB_REPO_URL))
        row.addWidget(btn_github)
        row.addStretch()
        form.addRow("", row_widget)
        return group

    def _reload_settings_form(self) -> None:
        data = (
            self.settings.get_all(redact_secrets=False)
            if hasattr(self.settings, "get_all")
            else {}
        )
        for key, widget in self._settings_widgets.items():
            value = data.get(key)
            if isinstance(widget, QLineEdit):
                if key in ("default_bcc", "default_to"):
                    widget.setText(
                        ", ".join(value or [])
                        if isinstance(value, list)
                        else str(value or "")
                    )
                else:
                    widget.setText("" if value is None else str(value))
            elif isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QComboBox):
                if key == "default_template":
                    # (v5.1) Standardmall-kombon uppdateras med
                    # aktuella mallar + valt värde
                    self._refresh_default_template_combo()
                else:
                    widget.setCurrentText(str(value or ""))

    def _collect_settings_form(self) -> Dict[str, Any]:
        values: Dict[str, Any] = {}
        for key, widget in self._settings_widgets.items():
            if isinstance(widget, QLineEdit):
                raw = widget.text().strip()
                if key in ("default_bcc", "default_to"):
                    values[key] = [
                        part.strip() for part in raw.split(",") if part.strip()
                    ]
                elif key in {
                    "smtp_port",
                    "bcc_batch_size",
                    "max_retries",
                    "smtp_timeout",
                    "image_jpeg_quality",
                    "image_png_compress_level",
                }:
                    values[key] = raw
                elif key == "delay_between_batches":
                    values[key] = raw
                else:
                    values[key] = raw
            elif isinstance(widget, QCheckBox):
                values[key] = widget.isChecked()
            elif isinstance(widget, QComboBox):
                if key == "default_template":
                    # (v5.1) "(ingen – senast valda)" → tom sträng
                    text = widget.currentText().strip()
                    values[key] = (
                        "" if text == "(ingen – senast valda)" else text
                    )
                else:
                    values[key] = widget.currentText().strip()
        return values

    def _save_settings_form(self) -> None:
        values = self._collect_settings_form()
        # (v5.4) "ko-fi.com/namn" eller bara "namn" → fullständig URL;
        # Swish-numret normaliseras till nationellt sifferformat.
        try:
            from core.donate import (
                normalize_donation_url,
                normalize_swish_number,
            )

            if "donation_url" in values:
                values["donation_url"] = normalize_donation_url(
                    values.get("donation_url"), "ko-fi"
                )
            if "donation_paypal_url" in values:
                values["donation_paypal_url"] = normalize_donation_url(
                    values.get("donation_paypal_url"), "paypal"
                )
            if "donation_swish" in values:
                values["donation_swish"] = normalize_swish_number(
                    values.get("donation_swish")
                )
        except Exception:
            log.debug("Kunde inte normalisera donationsfält", exc_info=True)
        if hasattr(self.settings, "update_from_dict"):
            self.settings.update_from_dict(values)
        else:
            for key, value in values.items():
                self.settings.set(key, value)

        if self.settings.save():
            try:
                self.settings.sync_autostart()
            except Exception:
                log.debug(
                    "sync_autostart misslyckades efter settings save",
                    exc_info=True,
                )
            self._status("💾 Inställningar sparade", "success")
            # (v5.1) Applicera standardmallen direkt om den ändrades
            if "default_template" in values:
                self._apply_default_template()
            # (v5.4) Språkbyte via formuläret → erbjud omstart
            if values.get("language"):
                new_lang = normalize_language(values.get("language"))
                if new_lang != i18n_get_language():
                    i18n_set_language(new_lang)
                    self._prompt_restart_for_language(new_lang)
            self._refresh_last_check_label()
            self._refresh_preview()
        else:
            QMessageBox.critical(
                self, "Inställningar", "Kunde inte spara inställningarna."
            )

    def _test_smtp_from_settings(self) -> None:
        values = self._collect_settings_form()
        try:
            port = int(
                str(
                    values.get(
                        "smtp_port", self.settings.get("smtp_port", 587)
                    )
                    or 587
                )
            )
        except Exception:
            port = 587

        ok, message = test_smtp_connection(
            smtp_server=str(
                values.get(
                    "smtp_server", self.settings.get("smtp_server", "")
                )
            ),
            smtp_port=port,
            username=str(
                values.get("username", self.settings.get("username", ""))
            ),
            password=str(
                values.get("password", self.settings.get("password", ""))
            ),
            use_ssl=bool(
                values.get("use_ssl", self.settings.get("use_ssl", False))
            ),
            timeout=int(self.settings.get("smtp_timeout", 15) or 15),
        )
        if ok:
            QMessageBox.information(self, "SMTP-test", message)
            self._status("🔌 SMTP-test lyckades", "success")
        else:
            QMessageBox.warning(self, "SMTP-test", message)
            self._status("⚠️ SMTP-test misslyckades", "warning")

    def _open_settings(self) -> None:
        self.select_tab("settings")

    # ────────────────────────────────────────────────────────────────
    # Mallverktyg
    # ────────────────────────────────────────────────────────────────

    def _build_template_tools_tab(self) -> QWidget:
        """(v5.4) Mall-fliken: wizard-start + klickbar mallista."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        icon = QLabel("📝")
        icon.setStyleSheet("font-size: 40pt;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon)

        heading = QLabel(tr("templates_tab.heading"))
        heading.setStyleSheet("font-size: 16pt; font-weight: bold;")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)

        text = QLabel(tr("templates_tab.text"))
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setWordWrap(True)
        layout.addWidget(text)

        btn_wizard = QPushButton(tr("templates_tab.wizard_btn"))
        btn_wizard.setProperty("cssClass", "accent")
        btn_wizard.clicked.connect(self._open_template_wizard)
        layout.addWidget(btn_wizard, alignment=Qt.AlignmentFlag.AlignCenter)

        row = QHBoxLayout()
        btn_open_dir = QPushButton(tr("templates_tab.open_folder"))
        btn_open_dir.clicked.connect(self._open_tpl_dir)
        row.addWidget(btn_open_dir)
        btn_refresh = QPushButton(tr("templates_tab.refresh"))
        btn_refresh.clicked.connect(self._refresh_template_tools_list)
        row.addWidget(btn_refresh)
        row.addStretch()
        self._tpl_tools_count = QLabel("")
        self._tpl_tools_count.setProperty("cssClass", "subtext")
        row.addWidget(self._tpl_tools_count)
        layout.addLayout(row)

        self._tpl_tools_list = QListWidget()
        self._tpl_tools_list.itemDoubleClicked.connect(
            self._on_template_tool_activated
        )
        layout.addWidget(self._tpl_tools_list, stretch=1)

        hint = QLabel(tr("templates_tab.use_hint"))
        hint.setProperty("cssClass", "subtext")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        self._refresh_template_tools_list()
        return widget

    def _refresh_template_tools_list(self) -> None:
        """Uppdatera mallistan på Mall-fliken (tål att anropas tidigt)."""
        lst = getattr(self, "_tpl_tools_list", None)
        if lst is None:
            return
        names = self._template_names()
        lst.clear()
        lst.addItems(names)
        label = getattr(self, "_tpl_tools_count", None)
        if label is not None:
            if names:
                label.setText(
                    tr(
                        "templates_tab.count",
                        count=len(names),
                        folder=str(self._templates_dir()),
                    )
                )
            else:
                label.setText(tr("templates_tab.empty"))
        if self._last_tpl is not None:
            matches = lst.findItems(
                self._last_tpl.name, Qt.MatchFlag.MatchExactly
            )
            if matches:
                lst.setCurrentItem(matches[0])

    def _on_template_tool_activated(self, item: Any) -> None:
        """Dubbelklick i mallistan → använd mallen i Skicka-fliken."""
        name = item.text() if item is not None else ""
        if not name:
            return
        self._scan_tpls()
        if hasattr(self, "_tpl_combo"):
            idx = self._tpl_combo.findText(name)
            if idx >= 0:
                self._tpl_combo.setCurrentIndex(idx)
        self._on_tpl_sel(name)
        self.select_tab("send")

    # ────────────────────────────────────────────────────────────────
    # Event / tema / status
    # ────────────────────────────────────────────────────────────────

    def _bind_events(self) -> None:
        # Bundna metoder (v4.6) – lambdas GC:as av weakref-bussen
        try:
            self.bus.subscribe("mail.sent", self._on_mail_sent)
            self.bus.subscribe("mail.failed", self._on_mail_failed)
            self.bus.subscribe("ui.theme_changed", self._on_theme_changed)
            self.bus.subscribe("module.disabled", self._on_module_disabled)
        except Exception:
            log.debug("Kunde inte binda EventBus-events", exc_info=True)

    def _on_mail_sent(self, data: Optional[Dict[str, Any]] = None) -> None:
        data = data or {}
        QTimer.singleShot(
            0,
            lambda: self._status(
                f"✅ '{data.get('subject', '')}' skickad!", "success"
            ),
        )

    def _on_mail_failed(self, data: Optional[Dict[str, Any]] = None) -> None:
        data = data or {}
        QTimer.singleShot(
            0,
            lambda: self._status(f"❌ {data.get('error', '')}", "error"),
        )

    def _on_theme_changed(self, data: Optional[Dict[str, Any]] = None) -> None:
        del data
        QTimer.singleShot(0, self._apply_theme)

    def _on_module_disabled(
        self, data: Optional[Dict[str, Any]] = None
    ) -> None:
        data = data or {}
        QTimer.singleShot(
            0,
            lambda: QMessageBox.warning(
                self,
                "⚠️ Modul inaktiverad",
                f"{data.get('module', '?')} inaktiverades.\n"
                f"{data.get('reason', '')}",
            ),
        )

    def _apply_theme(self) -> None:
        self._style.apply()
        if isinstance(self._att_list, AttachmentDropListWidget):
            self._att_list.set_theme_colors(self._c())
        self._update_theme_button()
        self._status_reset()
        self._update_ph_status()
        self._refresh_preview()

    def _update_theme_button(self) -> None:
        btn = getattr(self, "btn_theme", None)
        if btn is None:
            return
        mode = "dark"
        try:
            mode = str(self._style.get_theme())
        except Exception:
            mode = str(
                getattr(self._style, "_mode", getattr(self._style, "_theme", "dark"))
            )
        text, tip = theme_button_caption(mode)
        btn.setText(text)
        btn.setToolTip(tip)

    def _on_theme_button_clicked(self) -> None:
        """Ett klick: växla ljust ↔ mörkt (StyleEngine.toggle)."""
        try:
            self._style.toggle()
        except Exception:
            current = "dark"
            try:
                current = str(self._style.get_theme())
            except Exception:
                pass
            self._set_theme("light" if current == "dark" else "dark")
            self._update_theme_button()
            return
        self._update_theme_button()
        mode = "dark"
        try:
            mode = str(self._style.get_theme())
        except Exception:
            pass
        label = "Mörkt" if str(mode).lower() == "dark" else "Ljust"
        self._status(f"🎨 {label} tema", "success")

    def _set_theme(self, mode: str) -> None:
        self._style.set_theme(mode)
        self.settings.set("theme", mode)
        try:
            self._style.apply()
        except Exception:
            log.debug("style.apply() misslyckades", exc_info=True)
        self.bus.publish(
            "ui.theme_changed", {"theme": mode, "was": ""}
        )
        label = {"dark": "Mörkt", "light": "Ljust", "system": "System"}.get(
            mode, mode
        )
        self._status(f"🎨 {label} tema", "success")

    def _status(self, message: str, style: str = "info") -> None:
        now = datetime.datetime.now().strftime("%H:%M:%S")
        colors = self._c()
        bg_map = {
            "info": colors.get("accent", ""),
            "success": colors.get("success", ""),
            "warning": colors.get("warning", ""),
            "error": colors.get("error", ""),
        }
        bg = bg_map.get(style, bg_map["info"])
        self._sb.setStyleSheet(f"QStatusBar {{ background: {bg}; }}")
        self._sb_label.setText(message)
        self._sb_time.setText(now)
        if style != "info":
            self._sb_timer.start(5000)

    def _status_reset(self) -> None:
        self._sb.setStyleSheet(
            f"QStatusBar {{ background: {self._c().get('accent', '')}; }}"
        )

    # ────────────────────────────────────────────────────────────────
    # Sändning
    # ────────────────────────────────────────────────────────────────

    def _default_bcc_with_archive(self) -> List[str]:
        """Standard-Bcc + arkivkopia (deduplicerat, v4.7)."""
        default_bcc = list(self.settings.get("default_bcc", []) or [])
        archive = str(
            self.settings.get("archive_copy_email", "") or ""
        ).strip()
        if archive and _looks_like_email(archive):
            lowered = {str(email).lower() for email in default_bcc}
            if archive.lower() not in lowered:
                default_bcc.append(archive)
        return default_bcc

    def _gather_send_params(self) -> Dict[str, Any]:
        recipients_to = _dedupe(self._list_items(self._to_list))
        recipients_bcc = _dedupe(self._list_items(self._bcc_list))
        replacements = self._get_ph()
        subject_text = self._ensure_subject_contains_model_and_reg(
            update_field=True
        )

        # (v5.4) Engelska skickas ALLTID automatiskt om någon mottagare
        # (To ELLER Bcc) är märkt EN – ingen global knapp längre
        to_lang = self._list_langs(self._to_list)
        bcc_lang = self._list_langs(self._bcc_list)
        has_en_recipient = (
            any(value == "en" for value in to_lang.values())
            or any(value == "en" for value in bcc_lang.values())
        )
        include_english = has_en_recipient

        # VIN är EN-only: skickas inte alls utan EN-mottagare
        if not has_en_recipient:
            replacements = {
                key: value
                for key, value in replacements.items()
                if str(key).lower() not in EN_ONLY_PLACEHOLDERS
            }

        return {
            "recipients_to": recipients_to,
            "recipients_bcc": recipients_bcc,
            # (v5.2) Språk per mottagare – SV får svensk, EN får engelsk
            "recipients_to_lang": to_lang,
            "recipients_bcc_lang": bcc_lang,
            "subject": subject_text,
            "body_plain": self._editor.toPlainText(),
            "template_path": str(self._last_tpl) if self._last_tpl else "",
            "template_name": self._tpl_combo.currentText() or "ingen",
            "replacements": replacements,
            "include_english": include_english,
            "language": "both" if include_english else "sv",
            "free_text": self._free_edit.toPlainText().strip(),
            "attachments": list(self._attachments),
            "default_bcc": self._default_bcc_with_archive(),
            # v5.0 – standardvärde för kvittocheckboxen i sänddialogen
            "request_receipts": bool(
                self.settings.get("request_receipts", False)
            ),
            "placeholders_missing": [
                key
                for key, value in replacements.items()
                if not value.strip()
            ],
            "warnings": [],
        }

    def _send(self) -> None:
        params = self._gather_send_params()
        recipients_to = params["recipients_to"]
        recipients_bcc = params["recipients_bcc"]
        total = len(recipients_to) + len(recipients_bcc)

        if total == 0:
            QMessageBox.warning(
                self,
                "Inga mottagare",
                "Lägg till minst en mottagare i steg ③.",
            )
            self.select_tab("send")
            return

        invalid = [
            email
            for email in recipients_to + recipients_bcc
            if not _looks_like_email(email)
        ]
        if invalid:
            QMessageBox.warning(
                self,
                "Ogiltiga mottagare",
                "Kontrollera:\n" + "\n".join(invalid[:10]),
            )
            return

        if vin_required_missing(
            params.get("replacements") or {},
            bool(params.get("include_english")),
        ):
            QMessageBox.warning(
                self,
                "VIN saknas",
                "VIN-nummer är obligatoriskt när det finns en "
                "engelsk mottagare [EN].\n\n"
                "Fyll i fältet 🔢 VIN (obligatoriskt för EN) i steg ①.",
            )
            self.select_tab("send")
            return

        if not self._confirm_send(params, total):
            self._status("❌ Sändning avbruten")
            return

        self._last_send_params = dict(params)
        self.btn_send.setEnabled(False)
        self._status("⏳ Skickar…", "warning")

        if self._tray_ref is not None and hasattr(
            self._tray_ref, "update_icon"
        ):
            self._tray_ref.update_icon("sending")

        self._worker = SendWorker(self.settings, params)
        self._worker.progress.connect(
            lambda cur, tot, msg: self._status(
                f"📤 {msg} ({cur}/{tot})", "warning"
            )
        )
        self._worker.finished.connect(self._send_done)
        self._worker.error.connect(self._send_err)
        self._worker.start()

    def _confirm_send(self, params: Dict[str, Any], total: int) -> bool:
        if SendConfirmDialog is not None:
            try:
                dialog = SendConfirmDialog(
                    self, params, self._style
                )  # type: ignore[misc]
                action = dialog.show()
                if action == "preview":
                    self.select_tab("preview")
                    return False
                if action == "send":
                    # v5.0 – hämta dialogens val (kvittocheckboxen)
                    try:
                        params.update(dialog.result_params())
                    except Exception:
                        log.debug(
                            "result_params() saknas – behåller standard",
                            exc_info=True,
                        )
                    return True
                return False
            except Exception:
                log.warning(
                    "SendConfirmDialog kunde inte användas, "
                    "fallback till QMessageBox",
                    exc_info=True,
                )

        image_count = sum(1 for path in self._attachments if _is_image(path))
        file_count = len(self._attachments) - image_count
        reply = QMessageBox.question(
            self,
            "📤 Bekräfta sändning",
            f"Skicka e-post nu?\n\n"
            f"Till: {len(params['recipients_to'])}\n"
            f"Bcc: {len(params['recipients_bcc'])}\n"
            f"Totalt: {total}\n\n"
            f"Ämne: {params['subject'] or '(tomt)'}\n"
            f"Mall: {params['template_name']}\n"
            f"Bilagor: {len(self._attachments)} st"
            + (
                f" ({image_count} bilder, {file_count} övriga filer)"
                if self._attachments
                else ""
            )
            + (
                "\nFritext: Ja (placeras ovan signaturen)"
                if params.get("free_text")
                else "\nFritext: Nej"
            ),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    @pyqtSlot(object)
    def _send_done(self, result: SendResult) -> None:
        self.btn_send.setEnabled(True)
        success = bool(getattr(result, "success", False))

        if self._tray_ref is not None and hasattr(
            self._tray_ref, "update_icon"
        ):
            self._tray_ref.update_icon(
                "success" if success else "error"
            )

        if success:
            total = int(getattr(result, "total_recipients", 0) or 0)
            self._status(f"✅ Skickat till {total} mottagare!", "success")
            self.bus.publish(
                "mail.sent",
                {
                    "subject": getattr(result, "subject", ""),
                    "count": total,
                },
            )
            self._append_send_history(result)
            self._save_recent_recipients()
            # Rensa ALLA fält INNAN dialogen visas (v4.9) – när
            # användaren stänger "✅ Klart" är formuläret redan tomt.
            if self.settings.get("clear_form_after_send", True):
                self._reset_form_after_send()
                self.bus.publish("ui.form_reset", {"source": "send_success"})
            QMessageBox.information(
                self,
                "✅ Klart",
                f"E-post skickad!\nMottagare: {total}\n"
                f"Tid: {getattr(result, 'elapsed_seconds', 0):.1f}s",
            )
        else:
            errors = list(getattr(result, "errors", []) or [])
            message = errors[0] if errors else "Okänt fel"
            self._status("❌ Misslyckades", "error")
            self.bus.publish("mail.failed", {"error": message})
            QMessageBox.critical(
                self,
                "Sändningsfel",
                "\n".join(errors) if errors else "Okänt fel",
            )

    @pyqtSlot(str)
    def _send_err(self, message: str) -> None:
        self.btn_send.setEnabled(True)
        if self._tray_ref is not None and hasattr(
            self._tray_ref, "update_icon"
        ):
            self._tray_ref.update_icon("error")
        self._status("❌ Kritiskt fel", "error")
        self.bus.publish("mail.failed", {"error": message})
        QMessageBox.critical(self, "Kritiskt fel", message)

    def _save_recent_recipients(self) -> None:
        if not self.settings.get("save_last_recipients", True):
            return
        add_recent = getattr(self.settings, "add_recent_recipient", None)
        if not callable(add_recent):
            return
        for email in (
            self._list_items(self._to_list) + self._list_items(self._bcc_list)
        ):
            try:
                add_recent(email, "")
            except Exception:
                log.debug(
                    "Kunde inte spara senaste mottagare: %s",
                    email, exc_info=True,
                )

    def _reset_form_after_send(self) -> None:
        """Rensa ALLA fält efter lyckad sändning (formulärrensning).

        v4.7: tömmer även ämnesraden och visar tydlig status i fönstret.
        Mallval + malltext behålls (spec) – allt inmatat töms.
        """
        self.settings.set("replacements_values", {})

        # Platshållarfält (v4.7: duck-typad – fungerar för alla widgettyper;
        # QComboBox måste tömmas via setCurrentText, ALDRIG clear() som
        # raderar dropdown-alternativen)
        for widget in self._ph_inputs.values():
            try:
                widget.blockSignals(True)
                if hasattr(widget, "setCurrentText"):
                    widget.setCurrentText("")
                elif hasattr(widget, "clear"):
                    widget.clear()
            except Exception:
                log.debug("Kunde inte rensa fält %r", widget, exc_info=True)
            finally:
                try:
                    widget.blockSignals(False)
                except Exception:
                    pass

        # (v5.6) Dropdown-placeholders återställs till första alternativet
        # – glastyp (::ruta::) ska vara FÖRINSTÄLLD på "Vindruta" efter
        # rensning, men användaren kan alltid välja i dropdown-menyn.
        default_values: Dict[str, str] = {}
        for key, widget in self._ph_inputs.items():
            options = PLACEHOLDER_DROPDOWNS.get(key.lower())
            if not options:
                continue
            try:
                widget.blockSignals(True)
                if hasattr(widget, "setCurrentText"):
                    widget.setCurrentText(options[0])
                default_values[key] = options[0]
            except Exception:
                log.debug(
                    "Kunde inte förinställa dropdown '%s'", key,
                    exc_info=True,
                )
            finally:
                try:
                    widget.blockSignals(False)
                except Exception:
                    pass
        if default_values:
            self.settings.set("replacements_values", default_values)

        # Ämnesrad (v4.7 – inget från förra mailet får ligga kvar)
        self._subject.blockSignals(True)
        self._subject.clear()
        self._subject.blockSignals(False)

        # Fritext, bilagor, mottagare
        self._free_edit.clear()
        self._clr_att()
        self._to_list.clear()
        self._bcc_list.clear()

        # Standard-Bcc + arkivkopia laddas in igen (ska alltid finnas)
        self._load_default_recipients()

        self._update_ph_status()
        self._refresh_preview()
        self._status("🧹 Formuläret rensades efter sändning", "info")

    # ────────────────────────────────────────────────────────────────
    # Hjälpmetoder
    # ────────────────────────────────────────────────────────────────

    def _save_tpl(self) -> None:
        if not self._last_tpl:
            QMessageBox.warning(self, "Ingen mall", "Välj en mall först.")
            return
        try:
            suffix = self._last_tpl.suffix.lower()
            if suffix == ".docx":
                # DOCX-mallar sparas via create_template (v4.6) –
                # aldrig som rå text (skulle korrumpera filen).
                from script.templates import create_template

                create_template(
                    self._last_tpl,
                    self._subject.text(),
                    self._editor.toPlainText(),
                    overwrite=True,
                )
            else:
                self._last_tpl.write_text(
                    f"ÄMNE: {self._subject.text()}\n\n"
                    f"INNEHÅLL:\n{self._editor.toPlainText()}",
                    encoding="utf-8",
                )
            self._status(f"💾 Sparad: {self._last_tpl.name}", "success")
        except Exception as exc:
            log.error("Spara mall misslyckades", exc_info=True)
            self._status(f"❌ {exc}", "error")

    def _open_tpl_dir(self) -> None:
        self._explorer(
            self._base_dir() / str(self.settings.get("template_dir", "Mallar"))
        )

    def _restore_geo(self) -> None:
        geometry = str(self.settings.get("window_geometry", "") or "")
        if geometry:
            try:
                parts = geometry.split("+")
                size = parts[0].split("x")
                self.resize(int(size[0]), int(size[1]))
                if len(parts) >= 3:
                    self.move(int(parts[1]), int(parts[2]))
                return
            except Exception:
                log.debug(
                    "Kunde inte återställa geometri: %s",
                    geometry, exc_info=True,
                )
        self.resize(1200, 820)

    def _explorer(self, path: Any) -> None:
        resolved = str(Path(path).resolve())
        try:
            if platform.system() == "Windows":
                os.startfile(resolved)  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.run(["open", resolved], check=False)
            else:
                subprocess.run(["xdg-open", resolved], check=False)
        except Exception:
            log.warning("Kunde inte öppna: %s", resolved, exc_info=True)

    def show(self) -> None:  # type: ignore[override]
        super().show()
        self.raise_()
        self.activateWindow()
        self.bus.publish("ui.window_shown", {})
        # (v5.4) Uppdatering funnen medan appen låg i trayen? Fråga nu.
        if self._pending_update_info is not None:
            QTimer.singleShot(400, self._maybe_prompt_pending_update)

    def hide(self) -> None:  # type: ignore[override]
        super().hide()
        self.bus.publish("ui.window_hidden", {})

    def closeEvent(self, event: Any) -> None:  # noqa: N802
        if self.settings.get("close_to_tray", True):
            event.ignore()
            self.hide()
            return

        if self._tray_ref is not None and hasattr(
            self._tray_ref, "_do_quit"
        ):
            try:
                event.ignore()
                self._tray_ref._do_quit()
                return
            except Exception:
                log.warning("tray._do_quit() misslyckades", exc_info=True)

        geo = self.geometry()
        self.settings.set(
            "window_geometry",
            f"{geo.width()}x{geo.height()}+{geo.x()}+{geo.y()}",
        )
        self.bus.publish("app.shutdown", {"reason": "close"})
        event.accept()


__all__ = [
    "MainWindow",
    "SendWorker",
    "PLACEHOLDER_DROPDOWNS",
    "AttachmentDropListWidget",
    "EN_ONLY_PLACEHOLDERS",
    "vin_required_missing",
]
