#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/dialogs.py – Kritiska UI-dialoger för EmailApp (PyQt6)

Version: 4.9 – SPRÅKFÖRDELNING UTAN VARNING (engelska alltid automatiskt)

ÄNDRINGAR mot v4.8:
- ✅ Språkvarningen "Engelska är av…" borttagen – engelska skickas
    alltid automatiskt till EN-mottagare (main_window v5.4); dialogen
    visar bara "🌐 Språk: SV n · EN n"

ÄNDRINGAR mot v4.7:
- ✅ SendConfirmDialog visar "🌐 Språk: 🇸🇪 SV n · 🇬🇧 EN n" (antal
    mottagare per språk från params recipients_to_lang/bcc_lang,
    v5.2 i main_window)
- ✅ Varning om EN-markerade mottagare finns men "Inkludera engelsk
    version" är av: de får då svensk version (regel: SV får aldrig
    engelsk; engelska av → alla svensk)

ÄNDRINGAR mot v4.6:
- ✅ SendConfirmDialog: ny checkbox "📨 Begär leverans- och läskvitto"
    * Standardvärde från params["request_receipts"] (settings v24.4)
    * result_params() → {"request_receipts": bool} hämtas av
      MainWindow efter bekräftelse (sändningen anropar aldrig direkt)
- ✅ Ny dialog: DeliverabilityGuideDialog ("📖 Leveransbarhets-guide")
    * HTML-guide: SPF, DKIM, DMARC (WebSupport-värden), SMTP-tips,
      innehållstips mot skräppost, Thunderbird-träning, kvitton
    * Knapp "📋 Kopiera DNS-poster" → kopierar färdiga TXT-poster
    * Öppnas från Inställningsfliken (main_window v5.0)

Fixar mot v4.4:
- ✅ Standard-To-fält i SettingsDialog (default_to, kommaseparerat)
- ✅ _collect_values() inkluderar default_to

Fixar mot v4.3:
- ✅ Korrupt markdown/inklistringssyntax borttagen
  (__future__, __all__, log.info, _PROJECT_ROOT, _csv_to_list,
   _is_image_path, _SMTP_PLACEHOLDERS, _build_ui, _on_send,
   _on_preview, _on_cancel, _build_smtp_tab, _build_send_tab,
   _build_ui_tab_widget, _build_adv_tab, _mark_clear_recent,
   _run_test, _collect_values, _save_and_close,
   smtp.gmail.com, arkiv@firma.se, chef@firma.se, <b>, >,
   "Bekräfta & skicka", "[ErrorDialog.info]")
- ✅ ProgressDialog.update() gjord robust
    * QWidget.update() är en riktig Qt-metod som kan anropas utan
      argument internt – överskuggningen hade kunnat krascha med
      TypeError. Nu: defensiva defaults (current=0, total=1) +
      guards (total<=0 → 1, isVisible-koll) – fungerar alltid.
- ✅ _collect_values() skriver ALDRIG tillbaka default_cc (pop)
- ✅ Ingen CC någonstans i UI: endast To/Bcc, standardmottagare = Bcc
- ✅ SendConfirmDialog visar bild-/fil-räkning separat
- ✅ Färgglada step-headers + knappklasser (send/back/danger/accent)

Klasser:
- SendConfirmDialog: obligatorisk bekräftelse före sändning
- ProgressDialog: progressdialog med QProgressBar
- ErrorDialog: statiska QMessageBox-hjälpare
- SettingsDialog: SMTP, Sändning, Utseende, Avancerat

Regler:
- Ingen Tkinter-kod
- Endast To och Bcc, ingen CC
- default_bcc behålls
- default_cc ignoreras och exponeras inte
- QDialog.exec() för modal visning
- QTimer.singleShot() kan användas för trådsäkra uppdateringar

FIL: ui/dialogs.py
"""

from __future__ import annotations

# stdlib
import logging
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Gör lokala paket importbara även om filen körs direkt från ui/-mappen.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# third-party
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

# local
from ui.styles import StyleEngine, get_colors
from ui.responsive import WrapLayout

log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _preview(values: List[str], limit: int = 3) -> str:
    if not values:
        return "(inga)"
    text = ", ".join(str(value) for value in values[:limit])
    if len(values) > limit:
        text += f" … +{len(values) - limit} till"
    return text


def _csv_to_list(text: str) -> List[str]:
    return [
        part.strip()
        for part in text.replace("\n", ",").split(",")
        if part.strip()
    ]


def _is_image_path(path: str) -> bool:
    return Path(path).suffix.lower() in {
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tif", ".tiff",
    }


# ═══════════════════════════════════════════════════════════════════════════
# SendConfirmDialog
# ═══════════════════════════════════════════════════════════════════════════

class SendConfirmDialog(QDialog):
    """Obligatorisk bekräftelsedialog innan e-post skickas.

    Returnerar via show() / result_action():
    - send
    - preview
    - cancel
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        send_params: Optional[Dict[str, Any]] = None,
        theme_engine: Optional[StyleEngine] = None,
    ) -> None:
        super().__init__(parent)
        self._style = theme_engine
        self._params = send_params or {}
        self._action = "cancel"

        params = self._params
        self._to = list(params.get("recipients_to", []) or [])
        self._bcc = list(params.get("recipients_bcc", []) or [])
        self._def_bcc = list(params.get("default_bcc", []) or [])
        self._subj = str(params.get("subject", "") or "")
        self._tpl = str(params.get("template_name", "Okänd") or "Okänd")
        self._lang = str(params.get("language", "sv") or "sv")
        self._miss = list(params.get("placeholders_missing", []) or [])
        self._att = list(params.get("attachments", []) or [])
        self._warns = list(params.get("warnings", []) or [])
        self._has_free_text = bool(
            str(params.get("free_text", "") or "").strip()
        )
        # v4.7 – leverans-/läskvitto (standardvärde från settings v24.4)
        self._receipts = bool(params.get("request_receipts", False))
        # v4.8 – språk per mottagare (från main_window v5.2)
        self._to_lang = dict(params.get("recipients_to_lang", {}) or {})
        self._bcc_lang = dict(params.get("recipients_bcc_lang", {}) or {})
        self._sender_profile_name = str(
            params.get("sender_profile_name", "") or ""
        )
        self._sender_email = str(params.get("sender_email", "") or "")
        self._test_mode = bool(params.get("test_mode", False))
        self._test_recipient = str(params.get("test_recipient", "") or "")
        self._preflight_text = str(params.get("preflight_text", "") or "")

        # Ingen CC: total = To + Bcc. Eventuell legacy recipients_cc ignoreras.
        self._total = len(self._to) + len(self._bcc)

        self.setWindowTitle(
            "🧪 Bekräfta testmail" if self._test_mode else "📤 Bekräfta e-postsändning"
        )
        self.setModal(True)
        self.setMinimumSize(360, 260)
        screen = self.screen()
        available = screen.availableGeometry() if screen else None
        self.resize(min(760, max(360, available.width() - 60)) if available else 760,
                    min(680, max(260, available.height() - 80)) if available else 680)
        self._build_ui()

    def _c(self) -> Dict[str, str]:
        if self._style:
            return self._style.get_colors()
        return get_colors("dark")

    def _build_ui(self) -> None:
        colors = self._c()
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        self._content_scroll = QScrollArea()
        self._content_scroll.setWidgetResizable(True)
        self._content_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        layout = QVBoxLayout(content)
        self._content_scroll.setWidget(content)
        root.addWidget(self._content_scroll, stretch=1)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Färgglad wizard-header
        hero = QFrame()
        hero.setProperty("cssClass", "step-orange")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(18, 14, 18, 14)
        hero_layout.setSpacing(4)

        title = QLabel(
            "④ 🧪 Bekräfta testmail" if self._test_mode else "④ 📤 Bekräfta & skicka"
        )
        title.setWordWrap(True)
        title.setStyleSheet(
            "color: #FFFFFF; font-size: 15pt; font-weight: bold; "
            "background: transparent;"
        )
        hero_layout.addWidget(title)

        subtitle = QLabel(
            "Testläge: bara testadressen får mailet – vanliga "
            "mottagare, standard-Bcc och arkivkopia används inte."
            if self._test_mode
            else "Kontrollera To/Bcc, ämne, bilagor och fritext. "
            "E-post skickas bara när du bekräftar."
        )
        subtitle.setStyleSheet(
            "color: #FFFFFF; font-weight: bold; background: transparent;"
        )
        subtitle.setWordWrap(True)
        hero_layout.addWidget(subtitle)
        layout.addWidget(hero)

        # Sammanfattning
        info = QFrame()
        info.setProperty("cssClass", "card")
        grid = QGridLayout(info)
        grid.setContentsMargins(14, 12, 14, 12)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(8)
        self._grid_row = 0

        def row(label: str, value: str, color: str = "") -> None:
            label_widget = QLabel(label)
            label_widget.setWordWrap(True)
            label_widget.setStyleSheet("font-weight: bold;")
            value_widget = QLabel(value)
            value_widget.setTextFormat(Qt.TextFormat.PlainText)
            value_widget.setMinimumWidth(0)
            value_widget.setWordWrap(True)
            if color:
                value_widget.setStyleSheet(f"color: {color}; font-weight: bold;")
            grid.addWidget(
                label_widget, self._grid_row, 0, Qt.AlignmentFlag.AlignTop
            )
            grid.addWidget(value_widget, self._grid_row, 1)
            self._grid_row += 1

        row(
            "📨 Till:",
            f"{len(self._to)} st – {_preview(self._to)}",
            colors.get("error", "") if not self._to else "",
        )
        row("🙈 Bcc:", f"{len(self._bcc)} st – {_preview(self._bcc, 2)}")
        # (v4.8) Språkfördelning: SV får svensk, EN får engelsk
        def _en_count(emails: List[str], lang_map: Dict[str, Any]) -> int:
            return sum(
                1
                for email in emails
                if str(lang_map.get(email, "sv")).lower() == "en"
            )

        en_total = _en_count(self._to, self._to_lang) + _en_count(
            self._bcc, self._bcc_lang
        )
        if en_total > 0:
            row(
                "🌐 Språk:",
                f"🇸🇪 SV {max(0, self._total - en_total)} · "
                f"🇬🇧 EN {en_total}",
                colors.get("accent", ""),
            )
            # (v4.9) Ingen varning – engelska skickas alltid automatiskt
            # till EN-mottagare (To eller Bcc)
        if self._def_bcc:
            row(
                "📌 Standard-Bcc:",
                f"{len(self._def_bcc)} st alltid inkluderade",
                colors.get("accent", ""),
            )
        row(
            "👥 Totalt:",
            f"{self._total} mottagare",
            colors.get("error", "")
            if self._total == 0
            else colors.get("success", ""),
        )
        if self._sender_email or self._sender_profile_name:
            sender_text = self._sender_profile_name or self._sender_email
            if self._sender_email and self._sender_email != sender_text:
                sender_text = f"{sender_text} <{self._sender_email}>"
            row("👤 Avsändare:", sender_text)
            from core.sender_profiles import normalize_profile_color
            color = normalize_profile_color((self._params.get("sender_profile") or {}).get("profile_color"))
            value_widget = grid.itemAtPosition(self._grid_row - 1, 1).widget()
            value_widget.setStyleSheet("border-left: 8px solid " + color + "; padding: 6px;")
        if self._test_mode:
            row(
                "🧪 Testläge:",
                f"Bara {self._test_recipient or 'testadressen'} får mailet",
                colors.get("warning", ""),
            )
        row(
            "✉️ Ämne:",
            self._subj or "(tomt)",
            colors.get("warning", "") if not self._subj.strip() else "",
        )
        row("📝 Mall:", self._tpl)
        lang_map = {"sv": "Svenska", "en": "Engelska", "both": "Svenska + Engelska"}
        row("🌐 Språk:", lang_map.get(self._lang, self._lang))

        if self._att:
            names = ", ".join(Path(path).name for path in self._att[:3])
            if len(self._att) > 3:
                names += f" … +{len(self._att) - 3} till"
            image_count = sum(
                1 for path in self._att if _is_image_path(path)
            )
            file_count = len(self._att) - image_count
            row("📎 Bilagor:", f"{len(self._att)} fil(er): {names}")
            row("🖼️ Bilder/Filer:", f"{image_count} bilder · {file_count} övriga filer")
        else:
            row("📎 Bilagor:", "Inga bilagor")

        row(
            "💬 Fritext:",
            "Ja – placeras ovan signaturen" if self._has_free_text else "Nej",
            colors.get("accent", "") if self._has_free_text else "",
        )
        layout.addWidget(info)

        if self._preflight_text:
            preflight_box = QFrame()
            preflight_box.setProperty("cssClass", "card")
            preflight_layout = QVBoxLayout(preflight_box)
            preflight_layout.setContentsMargins(14, 10, 14, 10)
            preflight_title = QLabel("🔎 Förhandskontroll")
            preflight_title.setStyleSheet("font-weight: bold;")
            preflight_layout.addWidget(preflight_title)
            preflight_label = QLabel(self._preflight_text)
            preflight_label.setWordWrap(True)
            preflight_layout.addWidget(preflight_label)
            layout.addWidget(preflight_box)

        # Platshållare
        ph_box = QFrame()
        ph_box.setProperty(
            "cssClass", "warningPanel" if self._miss else "successPanel"
        )
        ph_layout = QVBoxLayout(ph_box)
        ph_layout.setContentsMargins(14, 10, 14, 10)
        if self._miss:
            shown = [str(value) for value in self._miss[:6]]
            text = ", ".join(shown)
            if len(self._miss) > 6:
                text += f" … +{len(self._miss) - 6} till"
            label = QLabel(f"⚠️ {len(self._miss)} uppgifter saknar värde: {text}")
            label.setStyleSheet(
                f"color: {colors.get('warning', '')}; font-weight: bold;"
            )
        else:
            label = QLabel("✅ Alla uppgifter är ifyllda")
            label.setStyleSheet(
                f"color: {colors.get('success', '')}; font-weight: bold;"
            )
        label.setWordWrap(True)
        ph_layout.addWidget(label)
        layout.addWidget(ph_box)

        # Varningar
        if self._warns:
            warn_box = QFrame()
            warn_box.setProperty("cssClass", "warningPanel")
            warn_layout = QVBoxLayout(warn_box)
            warn_layout.setContentsMargins(14, 10, 14, 10)
            for warning in self._warns[:6]:
                warning_label = QLabel(f"• {warning}")
                warning_label.setWordWrap(True)
                warning_label.setStyleSheet(
                    f"color: {colors.get('warning', '')};"
                )
                warn_layout.addWidget(warning_label)
            layout.addWidget(warn_box)

        if self._total == 0:
            no_recipient = QLabel("❌ Inga mottagare – sändning är ej möjlig.")
            no_recipient.setStyleSheet(
                f"color: {colors.get('error', '')}; font-weight: bold; "
                f"font-size: 11pt;"
            )
            layout.addWidget(no_recipient)

        # v4.7 – checkbox för leverans-/läskvitto
        self._receipt_check = QCheckBox(
            "📨 Begär leverans-/läskvitto"
        )
        self._receipt_check.setChecked(self._receipts)
        self._receipt_check.setToolTip(
            "Lägger till Disposition-Notification-To / Return-Receipt-To "
            "samt SMTP-DSN (NOTIFY) när servern stödjer det. "
            "Mottagarens e-postklient kan neka läskvitto."
        )
        layout.addWidget(self._receipt_check)

        question = QLabel(
            f"Vill du skicka testmail till {self._test_recipient}?"
            if self._test_mode and self._total > 0
            else f"Vill du skicka e-post till {self._total} mottagare?"
            if self._total > 0
            else "Inga mottagare har lagts till."
        )
        question.setStyleSheet("font-size: 11pt; font-weight: bold;")
        question.setWordWrap(True)
        layout.addWidget(question)

        # Knappar
        buttons = WrapLayout()
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
        root.addLayout(buttons)

    def keyPressEvent(self, event: Any) -> None:  # noqa: N802 - Qt API
        if event.key() == Qt.Key.Key_F5:
            self._on_preview()
            return
        super().keyPressEvent(event)

    def _on_send(self) -> None:
        log.info(
            "SendConfirmDialog: bekräftad → %d mottagare, ämne='%s'",
            self._total, self._subj,
        )
        self._action = "send"
        self.accept()

    def _on_preview(self) -> None:
        log.debug("SendConfirmDialog: förhandsgranskning.")
        self._action = "preview"
        self.reject()

    def _on_cancel(self) -> None:
        log.debug("SendConfirmDialog: avbruten.")
        self._action = "cancel"
        self.reject()

    def result_action(self) -> str:
        return self._action

    def result_params(self) -> Dict[str, Any]:
        """Extra värden från dialogen som ska följa med i sändningen.

        (v4.7) Hämtas av MainWindow när användaren bekräftar sändning –
        dialogen anropar aldrig sändning direkt.
        """
        return {
            "request_receipts": bool(
                getattr(self, "_receipt_check", None)
                and self._receipt_check.isChecked()
            )
        }

    def show(self) -> str:  # type: ignore[override]
        """
        Visa dialog modalt och returnera vald åtgärd ("send"/"preview"/"cancel").

        (API-kompatibilitet: kör exec() och returnerar _action.
        Anropas enbart från applikationskod – Qt:s interna show-anrop
        påverkas inte, då QWidget.show() inte är en virtuell metod.)
        """
        self.exec()
        return self._action


# ═══════════════════════════════════════════════════════════════════════════
# ProgressDialog
# ═══════════════════════════════════════════════════════════════════════════

class ProgressDialog(QDialog):
    """Dialog för realtidsförlopp under sändning."""

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        title: str = "Skickar e-post…",
        theme_engine: Optional[StyleEngine] = None,
    ) -> None:
        super().__init__(parent)
        self._style = theme_engine
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(440, 150)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self._lbl_status = QLabel("Förbereder sändning…")
        self._lbl_status.setStyleSheet("font-size: 10pt; font-weight: bold;")
        layout.addWidget(self._lbl_status)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setProperty("cssClass", "success")
        layout.addWidget(self._bar)

        self._lbl_detail = QLabel("")
        self._lbl_detail.setProperty("cssClass", "muted")
        layout.addWidget(self._lbl_detail)

    def update(  # type: ignore[override]
        self,
        current: int = 0,
        total: int = 1,
        message: str = "",
    ) -> None:
        """
        Uppdatera förloppet.

        (v4.4) Defensiv signatur: QWidget.update() är en riktig
        Qt-metod som kan anropas utan argument – denna överskuggning
        får aldrig krascha med TypeError.
        """
        try:
            if not self.isVisible():
                return
            if total <= 0:
                total = 1
            pct = int((current / total) * 100) if total > 0 else 0
            self._bar.setValue(min(max(pct, 0), 100))
            self._lbl_status.setText(
                message or f"Skickar {current} av {total}…"
            )
            self._lbl_detail.setText(
                f"{current} / {total} skickade ({pct}%)"
            )
        except Exception:
            log.debug("ProgressDialog.update() fel", exc_info=True)

    def close(self) -> None:  # type: ignore[override]
        QTimer.singleShot(0, self.accept)


# ═══════════════════════════════════════════════════════════════════════════
# ErrorDialog
# ═══════════════════════════════════════════════════════════════════════════

class ErrorDialog:
    """Statisk helper för felmeddelanden via QMessageBox."""

    @staticmethod
    def show(
        parent: Optional[QWidget],
        title: str,
        message: str,
        detail: Optional[str] = None,
    ) -> None:
        full = f"{message}\n\n{detail}" if detail else message
        log.error("[ErrorDialog] %s: %s", title, message)
        QMessageBox.critical(parent, title, full)

    @staticmethod
    def show_warning(parent: Optional[QWidget], title: str, message: str) -> None:
        log.warning("[ErrorDialog.warning] %s: %s", title, message)
        QMessageBox.warning(parent, title, message)

    @staticmethod
    def show_info(parent: Optional[QWidget], title: str, message: str) -> None:
        log.info("[ErrorDialog.info] %s: %s", title, message)
        QMessageBox.information(parent, title, message)


# ═══════════════════════════════════════════════════════════════════════════
# SettingsDialog
# ═══════════════════════════════════════════════════════════════════════════

class SettingsDialog(QDialog):
    """Fullständig konfigurationsdialog utan CC. Standardmottagare = Bcc."""

    _SMTP_PLACEHOLDERS = {
        "smtp_server": "t.ex. smtp.gmail.com",
        "smtp_port": "587 eller 465",
    }

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        initial_values: Optional[Dict[str, Any]] = None,
        test_callback: Optional[Callable[[], None]] = None,
        save_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        theme_engine: Optional[StyleEngine] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("⚙️ Inställningar")
        self.setModal(True)
        self.setMinimumSize(560, 620)
        self.resize(680, 760)

        self._test_cb = test_callback
        self._save_cb = save_callback
        self._style = theme_engine
        self._values = initial_values or {}
        self._fields: Dict[str, QWidget] = {}
        self._checks: Dict[str, QCheckBox] = {}
        self._combos: Dict[str, QComboBox] = {}
        self._clear_recent = False

        self._build_ui()

    def _c(self) -> Dict[str, str]:
        if self._style:
            return self._style.get_colors()
        return get_colors("dark")

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        header = QFrame()
        header.setProperty("cssClass", "step-blue")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)
        title = QLabel("⚙️ Inställningar")
        title.setStyleSheet(
            "color: #FFFFFF; font-size: 15pt; font-weight: bold; "
            "background: transparent;"
        )
        header_layout.addWidget(title)
        subtitle = QLabel(
            "SMTP, sändning, utseende och avancerade val. "
            "Ingen CC – endast To/Bcc."
        )
        subtitle.setStyleSheet(
            "color: #FFFFFF; font-weight: bold; background: transparent;"
        )
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_smtp_tab(), "📧 SMTP")
        self._tabs.addTab(self._build_send_tab(), "📤 Sändning")
        self._tabs.addTab(self._build_ui_tab_widget(), "🎨 Utseende")
        self._tabs.addTab(self._build_adv_tab(), "🔧 Avancerat")
        layout.addWidget(self._tabs, stretch=1)

        buttons = QHBoxLayout()
        btn_test = QPushButton("🔌 Testa SMTP")
        btn_test.clicked.connect(self._run_test)
        buttons.addWidget(btn_test)
        buttons.addStretch()

        btn_cancel = QPushButton("❌ Avbryt")
        btn_cancel.setProperty("cssClass", "back")
        btn_cancel.clicked.connect(self.reject)
        buttons.addWidget(btn_cancel)

        btn_save = QPushButton("💾 Spara")
        btn_save.setProperty("cssClass", "send")
        btn_save.setDefault(True)
        btn_save.clicked.connect(self._save_and_close)
        buttons.addWidget(btn_save)
        layout.addLayout(buttons)

    def _build_smtp_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        fields = [
            ("smtp_server", "SMTP-server:", False, "t.ex. smtp.gmail.com"),
            ("smtp_port", "Port:", False, "587 eller 465"),
            ("sender_email", "Avsändar-e-post:", False, ""),
            ("sender_name", "Avsändarnamn:", False, ""),
            ("username", "Användarnamn:", False, ""),
            ("password", "Lösenord:", True, ""),
            ("own_email", "Egen e-post (To):", False, ""),
            ("reply_to", "Reply-To:", False, "Tomt = sender_email"),
            ("archive_copy_email", "Arkivkopia (alltid kopia):", False, "Tomt = av"),
        ]
        for key, label, is_password, placeholder in fields:
            field = QLineEdit()
            if is_password:
                field.setEchoMode(QLineEdit.EchoMode.Password)
            value = str(self._values.get(key, "") or "")
            field.setText(value)
            if placeholder and not value:
                field.setPlaceholderText(placeholder)
            layout.addRow(f"<b>{label}</b>", field)
            self._fields[key] = field

        ssl_cb = QCheckBox("Använd SSL (port 465)")
        ssl_cb.setChecked(bool(self._values.get("use_ssl", False)))
        layout.addRow("", ssl_cb)
        self._checks["use_ssl"] = ssl_cb
        return widget

    def _build_send_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        send_group = QGroupBox("Sändningsinställningar")
        form = QFormLayout(send_group)
        form.setSpacing(8)

        numeric_fields = [
            ("max_retries", "Max återförsök:", 2),
            ("smtp_timeout", "Timeout (sekunder):", 30),
            ("bcc_batch_size", "Bcc-batchstorlek (0=alla):", 0),
            ("delay_between_batches", "Fördröjning (sek):", 0.5),
            ("image_jpeg_quality", "JPEG-kvalitet:", 92),
            ("image_png_compress_level", "PNG compress level:", 6),
        ]
        for key, label, default in numeric_fields:
            field = QLineEdit(str(self._values.get(key, default)))
            form.addRow(f"<b>{label}</b>", field)
            self._fields[key] = field

        bool_fields = [
            ("validate_recipients", "Validera e-postadresser"),
            ("skip_invalid_recipients", "Hoppa över ogiltiga"),
            ("generate_html_from_plain", "Generera HTML från text"),
            ("include_english", "Inkludera engelska"),
            ("translate_placeholders", "Översätt placeholder-värden"),
            ("clear_form_after_send", "Rensa formulär efter sändning"),
            ("save_last_recipients", "Spara senaste mottagare"),
            ("compress_images", "Komprimera bifogade bilder"),
            ("preserve_image_dimensions", "Bevara bilddimensioner"),
            ("preserve_image_sharpness", "Bevara skärpa så långt möjligt"),
        ]
        for key, label in bool_fields:
            checkbox = QCheckBox(label)
            checkbox.setChecked(bool(self._values.get(key, False)))
            form.addRow("", checkbox)
            self._checks[key] = checkbox
        layout.addWidget(send_group)

        default_to_group = QGroupBox("📌 Standardmottagare To")
        default_to_layout = QVBoxLayout(default_to_group)
        default_to_layout.addWidget(QLabel("<b>To-adresser, kommaseparerade:</b>"))
        info_to = QLabel(
            "Dessa adresser läggs automatiskt till som To vid varje sändning."
        )
        info_to.setProperty("cssClass", "muted")
        info_to.setWordWrap(True)
        default_to_layout.addWidget(info_to)

        self._default_to = QPlainTextEdit()
        self._default_to.setMaximumHeight(76)
        self._default_to.setPlaceholderText(
            "kund@firma.se, partner@firma.se"
        )
        default_to_val = self._values.get("default_to", [])
        if isinstance(default_to_val, list):
            self._default_to.setPlainText(
                ", ".join(str(value) for value in default_to_val)
            )
        default_to_layout.addWidget(self._default_to)
        layout.addWidget(default_to_group)

        default_group = QGroupBox("📌 Standardmottagare Bcc")
        default_layout = QVBoxLayout(default_group)
        default_layout.addWidget(QLabel("<b>Bcc-adresser, kommaseparerade:</b>"))
        info = QLabel(
            "Dessa adresser läggs automatiskt till som Bcc vid varje sändning."
        )
        info.setProperty("cssClass", "muted")
        info.setWordWrap(True)
        default_layout.addWidget(info)

        self._default_bcc = QPlainTextEdit()
        self._default_bcc.setMaximumHeight(76)
        self._default_bcc.setPlaceholderText(
            "arkiv@firma.se, chef@firma.se"
        )
        default_bcc = self._values.get("default_bcc", [])
        if isinstance(default_bcc, list):
            self._default_bcc.setPlainText(
                ", ".join(str(value) for value in default_bcc)
            )
        default_layout.addWidget(self._default_bcc)
        layout.addWidget(default_group)

        recent_group = QGroupBox("🕐 Senaste mottagare")
        recent_layout = QVBoxLayout(recent_group)
        recent = self._values.get("recent_recipients", [])
        count = len(recent) if isinstance(recent, list) else 0
        recent_layout.addWidget(QLabel(f"Antal sparade: {count}"))

        if count > 0:
            self._recent_list = QListWidget()
            self._recent_list.setMaximumHeight(110)
            for item in recent[-10:]:
                if isinstance(item, dict):
                    email = item.get("email", "")
                    name = item.get("name", "")
                    last = str(item.get("last_used", ""))[:10]
                    self._recent_list.addItem(f"{email} ({name}) {last}")
            recent_layout.addWidget(self._recent_list)

        btn_clear = QPushButton("🗑️ Rensa senaste mottagare")
        btn_clear.setProperty("cssClass", "danger")
        btn_clear.clicked.connect(self._mark_clear_recent)
        recent_layout.addWidget(btn_clear, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(recent_group)

        layout.addStretch()
        scroll.setWidget(inner)

        wrapper = QWidget()
        wrapper_layout = QVBoxLayout(wrapper)
        wrapper_layout.setContentsMargins(0, 0, 0, 0)
        wrapper_layout.addWidget(scroll)
        return wrapper

    def _mark_clear_recent(self) -> None:
        self._clear_recent = True
        QMessageBox.information(
            self,
            "Info",
            "Senaste mottagare rensas när du klickar Spara.",
        )
        log.info("Senaste mottagare markerade för rensning.")

    def _build_ui_tab_widget(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        theme_cb = QComboBox()
        theme_cb.addItems(["dark", "light", "system"])
        current_theme = str(self._values.get("theme", "system"))
        idx = theme_cb.findText(current_theme)
        theme_cb.setCurrentIndex(idx if idx >= 0 else 2)
        layout.addRow("<b>Tema:</b>", theme_cb)
        self._combos["theme"] = theme_cb

        lang_cb = QComboBox()
        lang_cb.addItems(["sv", "en"])
        current_language = str(self._values.get("language", "sv"))
        idx = lang_cb.findText(current_language)
        lang_cb.setCurrentIndex(idx if idx >= 0 else 0)
        layout.addRow("<b>Språk:</b>", lang_cb)
        self._combos["language"] = lang_cb

        for key, label in [
            ("start_minimized", "Starta minimerat i systray"),
            ("close_to_tray", "Stäng till systray (ej avsluta)"),
            ("minimize_to_tray", "Minimera till systray"),
            ("autostart", "Starta automatiskt med OS"),
        ]:
            checkbox = QCheckBox(label)
            checkbox.setChecked(bool(self._values.get(key, False)))
            layout.addRow("", checkbox)
            self._checks[key] = checkbox
        return widget

    def _build_adv_tab(self) -> QWidget:
        widget = QWidget()
        layout = QFormLayout(widget)
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        log_cb = QComboBox()
        log_cb.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        current_log = str(self._values.get("log_level", "INFO"))
        idx = log_cb.findText(current_log)
        log_cb.setCurrentIndex(idx if idx >= 0 else 1)
        layout.addRow("<b>Loggningsnivå:</b>", log_cb)
        self._combos["log_level"] = log_cb

        mode_cb = QComboBox()
        mode_cb.addItems(["prod", "dev"])
        current_mode = str(self._values.get("mode", "prod"))
        idx = mode_cb.findText(current_mode)
        mode_cb.setCurrentIndex(idx if idx >= 0 else 0)
        layout.addRow("<b>Körläge:</b>", mode_cb)
        self._combos["mode"] = mode_cb

        cache_cb = QCheckBox("Smart cache (rensa vid avslut i prod)")
        cache_cb.setChecked(bool(self._values.get("smart_cache", True)))
        layout.addRow("", cache_cb)
        self._checks["smart_cache"] = cache_cb

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        layout.addRow(separator)

        info = QLabel(
            "Dev-läge: cache behålls, debug-loggning aktivt.\n"
            "Prod-läge: cache rensas vid avslut."
        )
        info.setProperty("cssClass", "muted")
        info.setWordWrap(True)
        layout.addRow(info)
        return widget

    def _run_test(self) -> None:
        if self._test_cb:
            self._test_cb()
        else:
            QMessageBox.information(self, "Info", "Testfunktion ej kopplad.")

    def _collect_values(self) -> Dict[str, Any]:
        """Samla alla inmatade värden. Exponerar inte default_cc."""
        values: Dict[str, Any] = {}

        for key, widget in self._fields.items():
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
                if (
                    key in self._SMTP_PLACEHOLDERS
                    and value == self._SMTP_PLACEHOLDERS[key]
                ):
                    value = ""
                values[key] = value

        for key, checkbox in self._checks.items():
            values[key] = checkbox.isChecked()

        for key, combo in self._combos.items():
            values[key] = combo.currentText()

        if hasattr(self, "_default_to"):
            values["default_to"] = _csv_to_list(
                self._default_to.toPlainText()
            )

        if hasattr(self, "_default_bcc"):
            values["default_bcc"] = _csv_to_list(
                self._default_bcc.toPlainText()
            )

        # Legacy-städning: skriv aldrig tillbaka default_cc.
        values.pop("default_cc", None)

        if self._clear_recent:
            values["recent_recipients"] = []

        for int_key in (
            "smtp_port",
            "max_retries",
            "smtp_timeout",
            "bcc_batch_size",
            "image_jpeg_quality",
            "image_png_compress_level",
        ):
            if int_key in values:
                try:
                    values[int_key] = int(values[int_key])
                except (ValueError, TypeError):
                    pass

        for float_key in ("delay_between_batches",):
            if float_key in values:
                try:
                    values[float_key] = float(values[float_key])
                except (ValueError, TypeError):
                    pass

        return values

    def _save_and_close(self) -> None:
        values = self._collect_values()
        log.info("SettingsDialog: sparar %d inställningar.", len(values))
        if self._save_cb:
            self._save_cb(values)
        self.accept()


# ═══════════════════════════════════════════════════════════════════════════
# DeliverabilityGuideDialog (v4.7)
# ═══════════════════════════════════════════════════════════════════════════

# DNS-poster att kopiera – WebSupport-värden (samma som i guiden)
_DNS_RECORDS_TO_COPY = """\
=== E-postautentisering – EXEMPEL, verifiera i WebSupports kontrollpanel ===
Skapa inte flera SPF-poster. Ersätt inte befintliga poster utan granskning.
DMARC-rapportadressen måste finnas och tillhöra er.

1) SPF (TXT-post på din domän, t.ex. bilrutan.se):
v=spf1 include:_spf.websupport.se ~all

2) DKIM: aktivera i WebSupports kontrollpanel och lägg till den
TXT-post de visar (t.ex. default._domainkey.bilrutan.se).

3) DMARC (TXT-post på _dmarc.din-domän.se, t.ex. _dmarc.bilrutan.se):
v=DMARC1; p=none; rua=mailto:dmarc@din-domän.se

SMTP-inställningar (WebSupport):
Server: smtp.websupport.se
Port: 587 (STARTTLS) eller 465 (SSL)
Användarnamn: hela e-postadressen (t.ex. rl@bilrutan.se)
"""


class DeliverabilityGuideDialog(QDialog):
    """Leveransbarhets-guide – varför mail hamnar i skräppost och vad man gör.

    (v4.7) Öppnas från Inställningsfliken. Innehåller SPF/DKIM/DMARC
    (WebSupport-värden), SMTP-tips, innehållstips mot skräppost,
    Thunderbird-träning och information om kvitton.
    """

    def __init__(
        self,
        parent: Optional[QWidget] = None,
        theme_engine: Optional[StyleEngine] = None,
    ) -> None:
        super().__init__(parent)
        self._style = theme_engine
        self.setWindowTitle("📖 Leveransbarhets-guide")
        self.setModal(True)
        self.setMinimumSize(680, 560)
        self.resize(780, 640)
        self._build_ui()

    def _c(self) -> Dict[str, str]:
        if self._style:
            return self._style.get_colors()
        return get_colors("dark")

    def _build_ui(self) -> None:
        colors = self._c()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        hero = QFrame()
        hero.setProperty("cssClass", "step-purple")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(16, 12, 16, 12)
        title = QLabel("📖 Leveransbarhets-guide – mot skräppost (SPAM)")
        title.setStyleSheet(
            "color: #FFFFFF; font-size: 14pt; font-weight: bold; "
            "background: transparent;"
        )
        hero_layout.addWidget(title)
        subtitle = QLabel(
            "SPF · DKIM · DMARC · SMTP · innehåll · Thunderbird · kvitton"
        )
        subtitle.setStyleSheet(
            "color: #FFFFFF; font-weight: bold; background: transparent;"
        )
        hero_layout.addWidget(subtitle)
        layout.addWidget(hero)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(self._guide_html(colors))
        layout.addWidget(browser, stretch=1)

        buttons = QHBoxLayout()
        btn_copy = QPushButton("📋 Kopiera DNS-poster")
        btn_copy.setProperty("cssClass", "accent")
        btn_copy.clicked.connect(self._copy_dns_records)
        buttons.addWidget(btn_copy)

        btn_mailtest = QPushButton("🧪 mail-tester.com")
        btn_mailtest.clicked.connect(self._open_mail_tester)
        buttons.addWidget(btn_mailtest)

        buttons.addStretch()

        btn_close = QPushButton("✅ Stäng")
        btn_close.setProperty("cssClass", "send")
        btn_close.setDefault(True)
        btn_close.clicked.connect(self.accept)
        buttons.addWidget(btn_close)
        layout.addLayout(buttons)

    def _copy_dns_records(self) -> None:
        try:
            QApplication.clipboard().setText(_DNS_RECORDS_TO_COPY)
        except Exception:
            log.warning(
                "Kunde inte kopiera DNS-poster till urklipp", exc_info=True
            )
            QMessageBox.warning(
                self, "Kopiera", "Kunde inte komma åt urklipp."
            )
            return
        QMessageBox.information(
            self,
            "Kopierat",
            "SPF/DKIM/DMARC-poster kopierade till urklipp.\n\n"
            "Klistra in dem i din DNS-hanterare "
            "(WebSupport kontrollpanel → Domäner → DNS).",
        )

    def _open_mail_tester(self) -> None:
        try:
            import webbrowser

            webbrowser.open("https://www.mail-tester.com")
        except Exception:
            log.warning(
                "Kunde inte öppna mail-tester.com", exc_info=True
            )

    @staticmethod
    def _guide_html(colors: Dict[str, str]) -> str:
        accent = colors.get("accent", "#5C9EFF")
        success = colors.get("success", "#2ECC71")
        warning = colors.get("warning", "#F5A623")
        text = colors.get("text", "#FFFFFF")
        sub = colors.get("text_secondary", "#BBBBCC")
        return f"""<html><body style="color:{text}; font-family:'Segoe UI',Arial; font-size:11pt;">
<h2 style="color:{accent}; margin-bottom:2px;">Varför hamnar mailen i skräppost?</h2>
<p style="color:{sub}; margin-top:0;">Tre huvudorsaker – i ordning av vikt:</p>
<ol>
<li><b>Avsändarens domän är inte verifierad</b> – SPF/DKIM/DMARC saknas eller är fel.
    Mottagarens server kan då inte bevisa att mailet verkligen kommer från er.</li>
<li><b>Avsändaradressen är inte på er egen domän</b> – t.ex. Gmail som From.</li>
<li><b>Innehåll/mönster som påminner om skräppost</b> – många länkar, tecken
    i ämnesraden, upprepade sändningar till samma mottagare.</li>
</ol>

<h2 style="color:{accent};">1️⃣ SPF – vilka servrar får skicka för er domän</h2>
<p>Lägg till en TXT-post på er domän (t.ex. <code>bilrutan.se</code>):</p>
<pre style="background:#1E1E2E; color:{success}; padding:8px; border-radius:6px;">v=spf1 include:_spf.websupport.se ~all</pre>
<p style="color:{sub};">Detta är ett exempel, inte en verifierad post för er domän.
Hämta exakta värden i WebSupports kontrollpanel. Ha endast en SPF-post
och inkludera alla legitima avsändare.</p>

<h2 style="color:{accent};">2️⃣ DKIM – digital signatur på varje mail</h2>
<p>Aktivera DKIM i WebSupports kontrollpanel (E-post → DKIM) och lägg till
den TXT-post de visar, t.ex.:</p>
<pre style="background:#1E1E2E; color:{success}; padding:8px; border-radius:6px;">default._domainkey.bilrutan.se  →  TXT: k=rsa; p=MIGfMA0... (från kontrollpanelen)</pre>

<h2 style="color:{accent};">3️⃣ DMARC – vad servern ska göra med misstänkta mail</h2>
<p>Lägg till TXT-post på <code>_dmarc.bilrutan.se</code>:</p>
<pre style="background:#1E1E2E; color:{success}; padding:8px; border-radius:6px;">v=DMARC1; p=none; rua=mailto:dmarc@bilrutan.se</pre>
<p>Rapportadressen ovan är ett exempel och måste bytas till en adress ni äger.
Ingen inställning garanterar att mejl aldrig hamnar i skräppost.</p>
<p>Börja med <code>p=none</code> (bara rapportering), kontrollera att
mail-tester.com ger grönt, och skärp sedan till <code>p=quarantine</code>.</p>

<h2 style="color:{accent};">4️⃣ SMTP – rätt inställningar (WebSupport)</h2>
<table style="border-collapse:collapse;">
<tr><td style="padding:2px 10px 2px 0; color:{sub};">Server:</td><td><b>smtp.websupport.se</b></td></tr>
<tr><td style="padding:2px 10px 2px 0; color:{sub};">Port:</td><td><b>587</b> (STARTTLS) eller <b>465</b> (SSL)</td></tr>
<tr><td style="padding:2px 10px 2px 0; color:{sub};">Användarnamn:</td><td>hela e-postadressen, t.ex. <b>rl@bilrutan.se</b></td></tr>
</table>

<h2 style="color:{accent};">5️⃣ Innehåll – minska SPAM-signaler</h2>
<ul>
<li>Ämnesrad: rak och tydlig, <b>inga snedstreck (/) eller konstiga tecken</b>.
    Använd "Offertförfrågan:" i stället för "Offert –".</li>
<li>Signaturen: håll den <b>ren och konsekvent</b> – helst EN avsändare,
    EN adress, EN telefon. Flera företagsnamn/telefonnummer/webbplatser i
    samma signatur ökar spam-poängen.</li>
<li>Inga VERSALER, inga !!!, inga ord som "gratis", "erbjudande",
    "viktigt" i ämnesraden.</li>
<li>Skriv personligt ("Hej! Vi söker…") – inte som en massutskickstext.</li>
<li>Undvik att skicka samma exakta text till många mottagare på en gång –
    batcha Bcc (5–10 st) med fördröjning (inställningar → Sändning).</li>
</ul>

<h2 style="color:{accent};">6️⃣ Thunderbird – träna filtret</h2>
<ul>
<li>Högerklicka på ett felplacerat mail → <b>"Inte skräppost"</b> – filtret
    lär sig och flyttar framtida mail rätt.</li>
<li>Taggen <b>(E)</b> i ämnesraden är ett Thunderbird-filter, inte en
    serverbedömning – kontrollera filterreglerna om den dyker upp.</li>
</ul>

<h2 style="color:{accent};">7️⃣ Leverans-/läskvitto (checkboxen i sänddialogen)</h2>
<ul>
<li><b>Läskvitto:</b> lägger till <code>Disposition-Notification-To</code>
    (RFC 3798). Outlook frågar mottagaren; Thunderbird kan konfigureras att
    svara automatiskt – mottagaren kan alltid neka.</li>
<li><b>Leveranskvitto:</b> SMTP-DSN (<code>NOTIFY=SUCCESS,FAILURE</code>)
    begärs när servern stödjer det. Servern kan välja att inte skicka.</li>
<li>Kvitton är <b>aldrig garanterade</b> – de beror på mottagarens klient
    och server. De påverkar inte spam-bedömningen.</li>
</ul>

<h2 style="color:{success};">✅ Snabbkoll innan större sändning</h2>
<p>Skicka ett testmail till <a href="https://www.mail-tester.com" style="color:{accent};">mail-tester.com</a>
och titta på poängen (sikta på 10/10). Kontrollera också med er egen
webmail att mailet hamnar i Inkorgen, inte i Skräppost.</p>
</body></html>"""


__all__ = [
    "SendConfirmDialog",
    "ProgressDialog",
    "ErrorDialog",
    "SettingsDialog",
    "DeliverabilityGuideDialog",
]
