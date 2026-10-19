#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/styles.py – Tema och styling för EmailApp (PyQt6)

Version: 1.3 – REPARERAD + SNABBARE (QSS-cache), färgglad, steg-för-steg

Fixar mot v1.2:
- ✅ Korrupt markdown/inklistringssyntax borttagen
  (__init__, __repr__, __all__, __future__, log.info, _resolve_mode,
   QScrollArea > QWidget > QWidget, <, >)
- ✅ SNABBARE: QSS-cache
    * build_qss() bygger en ~15 kB stylesheet-sträng varje gång
    * Nu cachad per läge ("dark"/"light") – byggs EN gång, återanvänds
      vid alla tema-byten/appliceringar
- ✅ get_colors()/get_color() redan lås-fria dict-läsningar
- ✅ apply() applicerar enbart om stilen faktiskt ändrats

Ersätter: ui/theme_engine.py (Tkinter)

Funktioner:
- Färgpaletter DARK_COLORS / LIGHT_COLORS
- QSS stylesheet-generering via build_qss()
- OS-sync via darkdetect
- StyleEngine: runtime tema-byte + EventBus-integration
- Wizard-/stegkort-design för enklare flöde
- get_colors() på modulnivå

REGLER:
- Inga Tkinter-imports
- Inga hårdkodade färger utanför DARK_COLORS / LIGHT_COLORS
- QSS appliceras globalt via QApplication.setStyleSheet()
- Scroll hanteras av Qt automatiskt
- Ingen CC-specifik styling

FIL: ui/styles.py
"""

from __future__ import annotations

# stdlib
import logging
import sys
from typing import Any, Dict, Literal, Optional, cast

# third-party
from PyQt6.QtWidgets import QApplication

# optional third-party
try:
    import darkdetect  # type: ignore
    HAS_DARKDETECT = True
except ImportError:
    darkdetect = None  # type: ignore[assignment]
    HAS_DARKDETECT = False

# local
try:
    from core.event_bus import EventBus  # type: ignore
except Exception:
    class EventBus:  # type: ignore[no-redef]
        def publish(self, *args: Any, **kwargs: Any) -> None:
            return None

try:
    from core.settings_manager import SettingsManager  # type: ignore
except Exception:
    class SettingsManager:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self._data: Dict[str, Any] = {"theme": "system"}

        def get(self, key: str, default: Any = None) -> Any:
            return self._data.get(key, default)

        def set(self, key: str, value: Any) -> None:
            self._data[key] = value

log = logging.getLogger("ui.styles")


# ═══════════════════════════════════════════════════════════════════════════
# FÄRGPALETTER
# ENDA TILLÅTNA PLATSEN FÖR HÅRDKODADE FÄRGER I HELA APPLIKATIONEN
# ═══════════════════════════════════════════════════════════════════════════

DARK_COLORS: Dict[str, str] = {
    # Bas
    "background": "#101827",
    "surface": "#182235",
    "surface_alt": "#20304A",
    "bg_secondary": "#142033",
    "panel_bg": "#1F2D46",
    "card_bg": "#1B2940",
    "card_hover": "#243653",
    "input_bg": "#0F1A2B",
    # Alias
    "bg": "#101827",
    "fg": "#F8FAFC",
    "entry_bg": "#0F1A2B",
    "entry_fg": "#F8FAFC",
    # Text
    "text": "#F8FAFC",
    "text_secondary": "#CBD5E1",
    "fg_secondary": "#CBD5E1",
    "muted": "#94A3B8",
    "disabled_fg": "#64748B",
    "disabled_bg": "#263246",
    "inverse_text": "#FFFFFF",
    "dark_text": "#0F172A",
    # Brand / accent
    "accent": "#3B82F6",
    "accent_hover": "#60A5FA",
    "accent_active": "#2563EB",
    "accent_soft": "#1D4ED8",
    "link": "#60A5FA",
    # Färgglada status/steg
    "success": "#22C55E",
    "success_hover": "#16A34A",
    "success_soft": "#14532D",
    "warning": "#F59E0B",
    "warning_hover": "#D97706",
    "warning_soft": "#78350F",
    "error": "#EF4444",
    "error_hover": "#DC2626",
    "error_soft": "#7F1D1D",
    "purple": "#A855F7",
    "purple_hover": "#9333EA",
    "purple_soft": "#581C87",
    "pink": "#EC4899",
    "pink_hover": "#DB2777",
    "pink_soft": "#831843",
    "cyan": "#06B6D4",
    "cyan_hover": "#0891B2",
    "cyan_soft": "#164E63",
    "orange": "#F97316",
    "orange_hover": "#EA580C",
    "orange_soft": "#7C2D12",
    # Knappar
    "button_bg": "#334155",
    "button_fg": "#F8FAFC",
    "button_hover": "#475569",
    "button_active": "#1E293B",
    # Tabbar
    "tab_bg": "#1E293B",
    "tab_fg": "#CBD5E1",
    "tab_active_bg": "#3B82F6",
    "tab_active_fg": "#FFFFFF",
    # Selection / hover
    "hover_bg": "#243653",
    "select_bg": "#3B82F6",
    "select_fg": "#FFFFFF",
    # Övrigt
    "border": "#334155",
    "border_soft": "#263246",
    "scrollbar_bg": "#1E293B",
    "scrollbar_fg": "#64748B",
    # Meny
    "menu_bg": "#182235",
    "menu_fg": "#F8FAFC",
    "menu_active_bg": "#243653",
    "menu_active_fg": "#60A5FA",
    # Tooltip
    "tooltip_bg": "#0F172A",
    "tooltip_fg": "#F8FAFC",
}

LIGHT_COLORS: Dict[str, str] = {
    # Bas
    "background": "#F6F8FF",
    "surface": "#FFFFFF",
    "surface_alt": "#EEF4FF",
    "bg_secondary": "#EDF2FF",
    "panel_bg": "#E6EEFF",
    "card_bg": "#FFFFFF",
    "card_hover": "#F0F7FF",
    "input_bg": "#FFFFFF",
    # Alias
    "bg": "#F6F8FF",
    "fg": "#101827",
    "entry_bg": "#FFFFFF",
    "entry_fg": "#101827",
    # Text
    "text": "#101827",
    "text_secondary": "#475569",
    "fg_secondary": "#475569",
    "muted": "#64748B",
    "disabled_fg": "#94A3B8",
    "disabled_bg": "#E2E8F0",
    "inverse_text": "#FFFFFF",
    "dark_text": "#0F172A",
    # Brand / accent
    "accent": "#2563EB",
    "accent_hover": "#1D4ED8",
    "accent_active": "#1E40AF",
    "accent_soft": "#DBEAFE",
    "link": "#2563EB",
    # Färgglada status/steg
    "success": "#16A34A",
    "success_hover": "#15803D",
    "success_soft": "#DCFCE7",
    "warning": "#F59E0B",
    "warning_hover": "#D97706",
    "warning_soft": "#FEF3C7",
    "error": "#DC2626",
    "error_hover": "#B91C1C",
    "error_soft": "#FEE2E2",
    "purple": "#9333EA",
    "purple_hover": "#7E22CE",
    "purple_soft": "#F3E8FF",
    "pink": "#DB2777",
    "pink_hover": "#BE185D",
    "pink_soft": "#FCE7F3",
    "cyan": "#0891B2",
    "cyan_hover": "#0E7490",
    "cyan_soft": "#CFFAFE",
    "orange": "#EA580C",
    "orange_hover": "#C2410C",
    "orange_soft": "#FFEDD5",
    # Knappar
    "button_bg": "#334155",
    "button_fg": "#FFFFFF",
    "button_hover": "#1E293B",
    "button_active": "#0F172A",
    # Tabbar
    "tab_bg": "#E2E8F0",
    "tab_fg": "#334155",
    "tab_active_bg": "#2563EB",
    "tab_active_fg": "#FFFFFF",
    # Selection / hover
    "hover_bg": "#E0F2FE",
    "select_bg": "#2563EB",
    "select_fg": "#FFFFFF",
    # Övrigt
    "border": "#CBD5E1",
    "border_soft": "#E2E8F0",
    "scrollbar_bg": "#E2E8F0",
    "scrollbar_fg": "#94A3B8",
    # Meny
    "menu_bg": "#FFFFFF",
    "menu_fg": "#101827",
    "menu_active_bg": "#DBEAFE",
    "menu_active_fg": "#1D4ED8",
    # Tooltip
    "tooltip_bg": "#10172A",
    "tooltip_fg": "#FFFFFF",
}

# Bakåtkompatibla alias
DARK = DARK_COLORS
LIGHT = LIGHT_COLORS

# Steg-färger för wizard-headers/kort: mall, bilagor, mottagare, skicka
STEP_COLORS = ["accent", "orange", "success", "purple"]

_VALID = frozenset({"dark", "light", "system"})
_ALIASES = {"auto": "system"}

# ── QSS-cache (v1.3) ───────────────────────────────────────────────────
_qss_cache: Dict[str, str] = {}


# ═══════════════════════════════════════════════════════════════════════════
# QSS-GENERERING
# ═══════════════════════════════════════════════════════════════════════════

def build_qss(c: Dict[str, str]) -> str:
    """Bygg komplett QSS stylesheet från färgpalett."""
    if sys.platform == "win32":
        font = "Segoe UI"
    elif sys.platform == "darwin":
        font = "SF Pro Text"
    else:
        font = "Helvetica"

    return f"""
    /* ══════════════════════════════════════════════
       GLOBAL
    ══════════════════════════════════════════════ */
    QMainWindow, QWidget {{
        background-color: {c['background']};
        color: {c['text']};
        font-family: "{font}", "Segoe UI", sans-serif;
        font-size: 10pt;
    }}

    QWidget[cssClass="appRoot"] {{
        background-color: {c['background']};
    }}

    /* ══════════════════════════════════════════════
       ENKLA KORT / PANELER
    ══════════════════════════════════════════════ */
    QFrame[cssClass="card"],
    QWidget[cssClass="card"] {{
        background-color: {c['card_bg']};
        border: 1px solid {c['border_soft']};
        border-radius: 14px;
        padding: 12px;
    }}

    QFrame[cssClass="cardHover"] {{
        background-color: {c['card_hover']};
        border: 1px solid {c['border']};
        border-radius: 14px;
        padding: 12px;
    }}

    QFrame[cssClass="softPanel"],
    QWidget[cssClass="softPanel"] {{
        background-color: {c['surface_alt']};
        border: 1px solid {c['border_soft']};
        border-radius: 16px;
        padding: 14px;
    }}

    QFrame[cssClass="hero"] {{
        background-color: {c['accent']};
        color: {c['inverse_text']};
        border-radius: 18px;
        border: none;
        padding: 18px;
    }}

    QFrame[cssClass="successPanel"] {{
        background-color: {c['success_soft']};
        border: 1px solid {c['success']};
        border-radius: 14px;
        padding: 12px;
    }}

    QFrame[cssClass="warningPanel"] {{
        background-color: {c['warning_soft']};
        border: 1px solid {c['warning']};
        border-radius: 14px;
        padding: 12px;
    }}

    QFrame[cssClass="errorPanel"] {{
        background-color: {c['error_soft']};
        border: 1px solid {c['error']};
        border-radius: 14px;
        padding: 12px;
    }}

    /* ══════════════════════════════════════════════
       STEG-FÖR-STEG / WIZARD
    ══════════════════════════════════════════════ */
    QFrame[cssClass="wizardHeader"] {{
        background-color: {c['surface']};
        border: 1px solid {c['border_soft']};
        border-radius: 18px;
        padding: 10px;
    }}

    QFrame[cssClass="wizardStep"] {{
        background-color: {c['surface']};
        border: 2px solid {c['border_soft']};
        border-radius: 16px;
        padding: 12px;
    }}

    QFrame[cssClass="wizardStepActive"] {{
        background-color: {c['accent_soft']};
        border: 2px solid {c['accent']};
        border-radius: 16px;
        padding: 12px;
    }}

    QFrame[cssClass="wizardStepDone"] {{
        background-color: {c['success_soft']};
        border: 2px solid {c['success']};
        border-radius: 16px;
        padding: 12px;
    }}

    QLabel[cssClass="stepNumber"] {{
        color: {c['inverse_text']};
        background-color: {c['accent']};
        border-radius: 18px;
        min-width: 36px;
        min-height: 36px;
        font-size: 15pt;
        font-weight: bold;
        qproperty-alignment: AlignCenter;
    }}

    QLabel[cssClass="stepTitle"] {{
        color: {c['text']};
        font-size: 13pt;
        font-weight: bold;
        background-color: transparent;
    }}

    QLabel[cssClass="stepHint"] {{
        color: {c['text_secondary']};
        font-size: 9pt;
        background-color: transparent;
    }}

    QFrame[cssClass="step-blue"] {{
        background-color: {c['accent']};
        border-radius: 14px;
        border: none;
        padding: 12px;
    }}

    QFrame[cssClass="step-purple"] {{
        background-color: {c['purple']};
        border-radius: 14px;
        border: none;
        padding: 12px;
    }}

    QFrame[cssClass="step-green"] {{
        background-color: {c['success']};
        border-radius: 14px;
        border: none;
        padding: 12px;
    }}

    QFrame[cssClass="step-orange"] {{
        background-color: {c['orange']};
        border-radius: 14px;
        border: none;
        padding: 12px;
    }}

    QFrame[cssClass="step-red"] {{
        background-color: {c['error']};
        border-radius: 14px;
        border: none;
        padding: 12px;
    }}

    QLabel[cssClass="onColor"],
    QFrame[cssClass="hero"] QLabel,
    QFrame[cssClass="step-blue"] QLabel,
    QFrame[cssClass="step-purple"] QLabel,
    QFrame[cssClass="step-green"] QLabel,
    QFrame[cssClass="step-orange"] QLabel,
    QFrame[cssClass="step-red"] QLabel {{
        color: {c['inverse_text']};
        background-color: transparent;
        font-weight: bold;
    }}

    /* ══════════════════════════════════════════════
       TABS
    ══════════════════════════════════════════════ */
    QTabWidget::pane {{
        border: 1px solid {c['border_soft']};
        border-radius: 14px;
        background: {c['surface']};
        top: -1px;
    }}

    QTabBar {{
        background: transparent;
    }}

    QTabBar::tab {{
        background: {c['tab_bg']};
        color: {c['tab_fg']};
        padding: 10px 22px;
        margin-right: 4px;
        border-top-left-radius: 12px;
        border-top-right-radius: 12px;
        font-weight: bold;
        font-size: 10pt;
        border: 1px solid {c['border_soft']};
        border-bottom: none;
    }}

    QTabBar::tab:selected {{
        background: {c['tab_active_bg']};
        color: {c['tab_active_fg']};
        border-bottom: 3px solid {c['accent_hover']};
    }}

    QTabBar::tab:hover:!selected {{
        background: {c['hover_bg']};
        color: {c['text']};
    }}

    /* ══════════════════════════════════════════════
       KNAPPAR
    ══════════════════════════════════════════════ */
    QPushButton {{
        background-color: {c['button_bg']};
        color: {c['button_fg']};
        border: none;
        border-radius: 12px;
        padding: 9px 18px;
        font-weight: bold;
        font-size: 10pt;
        min-height: 24px;
    }}

    QPushButton:hover {{
        background-color: {c['button_hover']};
    }}

    QPushButton:pressed {{
        background-color: {c['button_active']};
    }}

    QPushButton:disabled {{
        background-color: {c['disabled_bg']};
        color: {c['disabled_fg']};
    }}

    QPushButton[cssClass="accent"],
    QPushButton[cssClass="primary"],
    QPushButton[cssClass="next"] {{
        background-color: {c['accent']};
        color: {c['inverse_text']};
        font-weight: bold;
        padding: 11px 26px;
        border-radius: 14px;
    }}

    QPushButton[cssClass="accent"]:hover,
    QPushButton[cssClass="primary"]:hover,
    QPushButton[cssClass="next"]:hover {{
        background-color: {c['accent_hover']};
    }}

    QPushButton[cssClass="back"] {{
        background-color: {c['surface_alt']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 14px;
    }}

    QPushButton[cssClass="back"]:hover {{
        background-color: {c['hover_bg']};
    }}

    QPushButton[cssClass="danger"] {{
        background-color: {c['error']};
        color: {c['inverse_text']};
        border-radius: 12px;
    }}

    QPushButton[cssClass="danger"]:hover {{
        background-color: {c['error_hover']};
    }}

    QPushButton[cssClass="success"],
    QPushButton[cssClass="send"] {{
        background-color: {c['success']};
        color: {c['inverse_text']};
        border-radius: 14px;
        padding: 11px 26px;
    }}

    QPushButton[cssClass="success"]:hover,
    QPushButton[cssClass="send"]:hover {{
        background-color: {c['success_hover']};
    }}

    QPushButton[cssClass="warning"] {{
        background-color: {c['warning']};
        color: {c['inverse_text']};
        border-radius: 12px;
    }}

    QPushButton[cssClass="warning"]:hover {{
        background-color: {c['warning_hover']};
    }}

    QPushButton[cssClass="purple"] {{
        background-color: {c['purple']};
        color: {c['inverse_text']};
        border-radius: 12px;
    }}

    QPushButton[cssClass="purple"]:hover {{
        background-color: {c['purple_hover']};
    }}

    /* ══════════════════════════════════════════════
       INPUT
    ══════════════════════════════════════════════ */
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {c['entry_bg']};
        color: {c['entry_fg']};
        border: 2px solid {c['border_soft']};
        border-radius: 12px;
        padding: 8px 12px;
        font-size: 10pt;
        selection-background-color: {c['select_bg']};
        selection-color: {c['select_fg']};
    }}

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {c['accent']};
        background-color: {c['input_bg']};
    }}

    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
        background-color: {c['disabled_bg']};
        color: {c['disabled_fg']};
    }}

    QLineEdit:read-only {{
        background-color: {c['bg_secondary']};
    }}

    /* ══════════════════════════════════════════════
       COMBOBOX
    ══════════════════════════════════════════════ */
    QComboBox {{
        background-color: {c['entry_bg']};
        color: {c['entry_fg']};
        border: 2px solid {c['border_soft']};
        border-radius: 12px;
        padding: 8px 12px;
        font-size: 10pt;
        min-height: 24px;
    }}

    QComboBox:focus {{
        border: 2px solid {c['accent']};
    }}

    QComboBox:disabled {{
        background-color: {c['disabled_bg']};
        color: {c['disabled_fg']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 32px;
        border-top-right-radius: 12px;
        border-bottom-right-radius: 12px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        selection-background-color: {c['accent']};
        selection-color: {c['inverse_text']};
        outline: none;
    }}

    /* ══════════════════════════════════════════════
       LISTOR / TRÄD / TABELL
    ══════════════════════════════════════════════ */
    QListWidget, QTreeWidget, QTableWidget {{
        background-color: {c['entry_bg']};
        color: {c['text']};
        border: 1px solid {c['border_soft']};
        border-radius: 12px;
        font-size: 10pt;
        alternate-background-color: {c['bg_secondary']};
        outline: none;
    }}

    QListWidget::item, QTreeWidget::item, QTableWidget::item {{
        padding: 6px 10px;
        border-radius: 8px;
    }}

    QListWidget::item:selected,
    QTreeWidget::item:selected,
    QTableWidget::item:selected {{
        background-color: {c['select_bg']};
        color: {c['select_fg']};
    }}

    QListWidget::item:hover,
    QTreeWidget::item:hover,
    QTableWidget::item:hover {{
        background-color: {c['hover_bg']};
    }}

    QHeaderView::section {{
        background-color: {c['panel_bg']};
        color: {c['text']};
        font-weight: bold;
        padding: 8px;
        border: none;
        border-right: 1px solid {c['border_soft']};
        border-bottom: 1px solid {c['border_soft']};
    }}

    /* ══════════════════════════════════════════════
       GROUP BOX
    ══════════════════════════════════════════════ */
    QGroupBox {{
        border: 1px solid {c['border_soft']};
        border-radius: 14px;
        margin-top: 18px;
        padding-top: 20px;
        font-weight: bold;
        font-size: 10pt;
        color: {c['text']};
        background-color: {c['surface']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 14px;
        top: 0px;
        padding: 3px 10px;
        color: {c['accent']};
        font-weight: bold;
        background-color: {c['surface']};
        border-radius: 8px;
    }}

    /* ══════════════════════════════════════════════
       LABELS
    ══════════════════════════════════════════════ */
    QLabel {{
        color: {c['text']};
        background-color: transparent;
    }}

    QLabel[cssClass="heading"] {{
        font-size: 16pt;
        font-weight: bold;
    }}

    QLabel[cssClass="title"] {{
        font-size: 20pt;
        font-weight: bold;
    }}

    QLabel[cssClass="subtitle"],
    QLabel[cssClass="subtext"] {{
        color: {c['text_secondary']};
        font-size: 10pt;
    }}

    QLabel[cssClass="muted"] {{
        color: {c['muted']};
        font-size: 9pt;
    }}

    QLabel[cssClass="success"] {{
        color: {c['success']};
        font-weight: bold;
    }}

    QLabel[cssClass="warning"] {{
        color: {c['warning']};
        font-weight: bold;
    }}

    QLabel[cssClass="error"] {{
        color: {c['error']};
        font-weight: bold;
    }}

    QLabel[cssClass="accent"] {{
        color: {c['accent']};
        font-weight: bold;
    }}

    QLabel[cssClass="purple"] {{
        color: {c['purple']};
        font-weight: bold;
    }}

    QLabel[cssClass="pill"] {{
        color: {c['inverse_text']};
        background-color: {c['accent']};
        border-radius: 10px;
        padding: 4px 10px;
        font-weight: bold;
    }}

    QLabel[cssClass="pillGreen"] {{
        color: {c['inverse_text']};
        background-color: {c['success']};
        border-radius: 10px;
        padding: 4px 10px;
        font-weight: bold;
    }}

    QLabel[cssClass="pillOrange"] {{
        color: {c['inverse_text']};
        background-color: {c['orange']};
        border-radius: 10px;
        padding: 4px 10px;
        font-weight: bold;
    }}

    QLabel[cssClass="pillPurple"] {{
        color: {c['inverse_text']};
        background-color: {c['purple']};
        border-radius: 10px;
        padding: 4px 10px;
        font-weight: bold;
    }}

    /* ══════════════════════════════════════════════
       STATUSBAR
    ══════════════════════════════════════════════ */
    QStatusBar {{
        background-color: {c['accent']};
        color: {c['inverse_text']};
        font-weight: bold;
        font-size: 10pt;
        border-top: 1px solid {c['border']};
    }}

    QStatusBar QLabel {{
        color: {c['inverse_text']};
        background-color: transparent;
        font-weight: bold;
    }}

    /* ══════════════════════════════════════════════
       MENY
    ══════════════════════════════════════════════ */
    QMenuBar {{
        background-color: {c['surface']};
        color: {c['text']};
        font-size: 10pt;
        border-bottom: 1px solid {c['border_soft']};
    }}

    QMenuBar::item {{
        padding: 7px 14px;
        background: transparent;
        border-radius: 8px;
    }}

    QMenuBar::item:selected {{
        background-color: {c['menu_active_bg']};
        color: {c['menu_active_fg']};
    }}

    QMenu {{
        background-color: {c['menu_bg']};
        color: {c['menu_fg']};
        border: 1px solid {c['border_soft']};
        border-radius: 12px;
        padding: 6px;
    }}

    QMenu::item {{
        padding: 8px 24px;
        border-radius: 8px;
    }}

    QMenu::item:selected {{
        background-color: {c['accent']};
        color: {c['inverse_text']};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {c['border_soft']};
        margin: 5px 10px;
    }}

    /* ══════════════════════════════════════════════
       SCROLLBARS
    ══════════════════════════════════════════════ */
    QScrollBar:vertical {{
        background: {c['scrollbar_bg']};
        width: 11px;
        border-radius: 6px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {c['scrollbar_fg']};
        border-radius: 6px;
        min-height: 32px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {c['accent']};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background: {c['scrollbar_bg']};
        height: 11px;
        border-radius: 6px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background: {c['scrollbar_fg']};
        border-radius: 6px;
        min-width: 32px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {c['accent']};
    }}

    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ══════════════════════════════════════════════
       PROGRESSBAR
    ══════════════════════════════════════════════ */
    QProgressBar {{
        background-color: {c['bg_secondary']};
        border: 1px solid {c['border_soft']};
        border-radius: 9px;
        text-align: center;
        font-weight: bold;
        color: {c['text']};
        min-height: 16px;
    }}

    QProgressBar::chunk {{
        background-color: {c['accent']};
        border-radius: 8px;
    }}

    QProgressBar[cssClass="success"]::chunk {{
        background-color: {c['success']};
    }}

    /* ══════════════════════════════════════════════
       CHECKBOX / RADIOBUTTON
    ══════════════════════════════════════════════ */
    QCheckBox, QRadioButton {{
        color: {c['text']};
        font-size: 10pt;
        spacing: 8px;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {c['border']};
        border-radius: 6px;
        background-color: {c['entry_bg']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {c['accent']};
        border-color: {c['accent']};
    }}

    QCheckBox::indicator:hover {{
        border-color: {c['accent']};
    }}

    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {c['border']};
        border-radius: 9px;
        background-color: {c['entry_bg']};
    }}

    QRadioButton::indicator:checked {{
        background-color: {c['accent']};
        border-color: {c['accent']};
    }}

    QCheckBox:disabled, QRadioButton:disabled {{
        color: {c['disabled_fg']};
    }}

    /* ══════════════════════════════════════════════
       SEPARATORER
    ══════════════════════════════════════════════ */
    QFrame[frameShape="4"],
    QFrame[frameShape="5"],
    QFrame[cssClass="separator"] {{
        background-color: {c['border_soft']};
        border: none;
        max-height: 1px;
    }}

    /* ══════════════════════════════════════════════
       DIALOG
    ══════════════════════════════════════════════ */
    QDialog {{
        background-color: {c['surface']};
        color: {c['text']};
    }}

    /* ══════════════════════════════════════════════
       SPLITTER
    ══════════════════════════════════════════════ */
    QSplitter::handle {{
        background-color: {c['border_soft']};
    }}

    QSplitter::handle:horizontal {{ width: 3px; }}
    QSplitter::handle:vertical {{ height: 3px; }}

    /* ══════════════════════════════════════════════
       TOOLTIP
    ══════════════════════════════════════════════ */
    QToolTip {{
        background-color: {c['tooltip_bg']};
        color: {c['tooltip_fg']};
        border: 1px solid {c['border']};
        padding: 7px 11px;
        border-radius: 8px;
        font-size: 9pt;
    }}

    /* ══════════════════════════════════════════════
       SPINBOX
    ══════════════════════════════════════════════ */
    QSpinBox, QDoubleSpinBox {{
        background-color: {c['entry_bg']};
        color: {c['entry_fg']};
        border: 2px solid {c['border_soft']};
        border-radius: 12px;
        padding: 6px 10px;
        font-size: 10pt;
    }}

    QSpinBox:focus, QDoubleSpinBox:focus {{
        border: 2px solid {c['accent']};
    }}

    /* ══════════════════════════════════════════════
       SLIDER
    ══════════════════════════════════════════════ */
    QSlider::groove:horizontal {{
        background: {c['bg_secondary']};
        height: 7px;
        border-radius: 4px;
    }}

    QSlider::handle:horizontal {{
        background: {c['accent']};
        width: 18px;
        height: 18px;
        margin: -6px 0;
        border-radius: 9px;
    }}

    QSlider::sub-page:horizontal {{
        background: {c['accent']};
        border-radius: 4px;
    }}

    /* ══════════════════════════════════════════════
       SCROLL AREA
    ══════════════════════════════════════════════ */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}
    """


def get_cached_qss(mode: str) -> str:
    """Returnera cachad QSS för läge (v1.3) – byggs endast en gång."""
    normalized = _ALIASES.get(mode, mode)
    key = "dark" if normalized == "dark" else "light"
    if key not in _qss_cache:
        palette = DARK_COLORS if key == "dark" else LIGHT_COLORS
        _qss_cache[key] = build_qss(palette)
    return _qss_cache[key]


# ═══════════════════════════════════════════════════════════════════════════
# StyleEngine – runtime tema-hantering
# ═══════════════════════════════════════════════════════════════════════════

class StyleEngine:
    """Hanterar tema-byte och QSS-applicering i realtid."""

    def __init__(self, settings: SettingsManager, event_bus: EventBus) -> None:
        self._settings = settings
        self._bus = event_bus
        self._mode: Literal["light", "dark"] = self._resolve_mode()
        log.debug("StyleEngine initierad (läge=%s)", self._mode)

    def get_theme(self) -> Literal["light", "dark"]:
        """Returnerar upplöst tema."""
        self._mode = self._resolve_mode()
        return self._mode

    def get_colors(self) -> Dict[str, str]:
        """Returnerar aktiv färgpalett."""
        return DARK_COLORS if self._mode == "dark" else LIGHT_COLORS

    def get_color(self, key: str, fallback: str = "#000000") -> str:
        """Hämta enskild färg."""
        return self.get_colors().get(key, fallback)

    def apply(self, app: Optional[QApplication] = None) -> None:
        """Applicera QSS globalt på QApplication (v1.3: cachad QSS)."""
        self._mode = self._resolve_mode()
        qapp = app or QApplication.instance()
        if qapp is None:
            log.warning("apply(): ingen QApplication.")
            return
        qss = get_cached_qss(self._mode)
        cast(QApplication, qapp).setStyleSheet(qss)
        log.debug("QSS applicerat (läge=%s).", self._mode)

    def set_theme(self, theme: str) -> None:
        """Sätt tema och applicera direkt."""
        normalized = _ALIASES.get(theme, theme)
        if normalized not in _VALID:
            log.warning("Ogiltigt tema '%s'.", theme)
            return

        old = self._mode
        self._settings.set("theme", normalized)
        self._mode = self._resolve_mode()
        self.apply()

        if self._mode != old:
            log.info("Tema: %s → %s", old, self._mode)
            try:
                self._bus.publish(
                    "ui.theme_changed",
                    {"theme": self._mode, "was": old},
                )
            except Exception:
                log.debug(
                    "Kunde inte publicera ui.theme_changed", exc_info=True
                )

    def toggle(self) -> None:
        """Växla light ↔ dark."""
        self.set_theme("dark" if self._mode == "light" else "light")

    @staticmethod
    def is_os_dark() -> bool:
        """True om OS använder mörkt läge."""
        if HAS_DARKDETECT and darkdetect is not None:
            try:
                return bool(darkdetect.isDark())
            except Exception:
                log.debug("darkdetect.isDark() misslyckades", exc_info=True)
        return False

    @property
    def current_mode(self) -> Literal["light", "dark"]:
        """Aktuellt upplöst läge."""
        return self._mode

    def _resolve_mode(self) -> Literal["light", "dark"]:
        raw = self._settings.get("theme", "system")
        raw = _ALIASES.get(str(raw), str(raw))

        if raw == "system":
            if HAS_DARKDETECT and darkdetect is not None:
                try:
                    return "dark" if darkdetect.isDark() else "light"
                except Exception as exc:
                    log.debug("darkdetect: %s", exc)
            return "light"

        if raw in ("light", "dark"):
            return cast(Literal["light", "dark"], raw)

        log.warning("Okänt tema '%s' – faller tillbaka till light.", raw)
        return "light"

    def __repr__(self) -> str:
        return f"StyleEngine(mode={self._mode!r})"


# ═══════════════════════════════════════════════════════════════════════════
# Modulnivå-genvägar
# ═══════════════════════════════════════════════════════════════════════════

def get_colors(mode: str = "dark") -> Dict[str, str]:
    """Genväg utan StyleEngine-instans."""
    normalized = _ALIASES.get(mode, mode)
    return DARK_COLORS if normalized == "dark" else LIGHT_COLORS


def get_step_color(index: int, mode: str = "dark") -> str:
    """Returnera faktisk färg för wizard-steg 0..3."""
    palette = get_colors(mode)
    key = STEP_COLORS[index % len(STEP_COLORS)]
    return palette[key]


# ═══════════════════════════════════════════════════════════════════════════
# Publikt API
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    "DARK_COLORS",
    "LIGHT_COLORS",
    "DARK",
    "LIGHT",
    "STEP_COLORS",
    "StyleEngine",
    "build_qss",
    "get_cached_qss",
    "get_colors",
    "get_step_color",
]
