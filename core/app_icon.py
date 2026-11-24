#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/app_icon.py – Central app-ikon för EmailApp (används ÖVERALLT)

Version: 1.1 – MailOffer-kuvert med turkos offertbricka

Ikonen används på:
  - Huvudfönstret (taskbar + titelrad) – via QApplication.setWindowIcon
  - Alla dialoger (SendConfirmDialog, inställningar, meddelanden) –
    ärver automatiskt app-ikonen på Windows
  - Systemfältet (tray) – via ui/tray.py (idle-läget = app-ikonen,
    statuslägen = app-ikonen + liten status-badge)
  - Startup-feldialoger (main.pyw _safe_show_critical)

Fil: icons/app_icon.png (1024x1024 RGBA) + .ico (16–256px, Windows).
Samma ICO kan användas för manuella Windows-genvägar till VBS-startfilen.

Fallback-säkerhet:
  - Saknas PNG-filen ritas en snygg kuvertikon programmatiskt
    (QPainter) – appen får ALLTID en ikon, även utan filer.
  - Ikonen laddas EN gång och cachas (snabb uppstart).

FIL: core/app_icon.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

ICON_FILE_NAME = "app_icon.png"
ICON_ICO_NAME = "app_icon.ico"
WINDOWS_APP_ID = "RickardLangkvist.MailOffer"

# Ikon-cache (laddas en gång)
_icon_cache: Optional[object] = None  # QIcon


# ═══════════════════════════════════════════════════════════════════════
# Sökvägar
# ═══════════════════════════════════════════════════════════════════════

def project_root() -> Path:
    """Projektroten: förälder till core/-mappen (där main.pyw ligger)."""
    return Path(__file__).resolve().parents[1]


def icon_path() -> Optional[Path]:
    """Sökväg till icons/app_icon.png (None om filen saknas)."""
    candidate = project_root() / "icons" / ICON_FILE_NAME
    return candidate if candidate.is_file() else None


def icon_ico_path() -> Optional[Path]:
    """Sökväg till icons/app_icon.ico (Windows) – None om filen saknas."""
    candidate = project_root() / "icons" / ICON_ICO_NAME
    return candidate if candidate.is_file() else None


# ═══════════════════════════════════════════════════════════════════════
# Ikonladdning
# ═══════════════════════════════════════════════════════════════════════

def get_app_icon() -> object:
    """Returnera app-ikonen (QIcon) – cachad, med fallback.

    Prioritet:
      1. icons/app_icon.png (om filen finns) – QIcon(PNG)
      2. icons/app_icon.ico (Windows-format)
      3. Programmatiskt ritad kuvertikon (QPainter) – fungerar alltid

    Returns:
        QIcon (PyQt6.QtGui.QIcon)
    """
    global _icon_cache
    if _icon_cache is not None:
        return _icon_cache

    icon: Optional[object] = None

    # Vector source stays sharp at fractional DPI and on different monitors.
    svg = project_root() / 'icons' / 'app_icon.svg'
    if svg.is_file():
        try:
            from PyQt6.QtGui import QIcon
            candidate = QIcon(str(svg))
            if not candidate.isNull():
                icon = candidate
        except Exception:
            log.debug('SVG icon unavailable; using raster fallback', exc_info=True)

    # 1. PNG fallback
    png = icon_path()
    if icon is None and png is not None:
        try:
            from PyQt6.QtGui import QIcon

            icon = QIcon(str(png))
            if icon.isNull():
                icon = None
            else:
                log.debug("App-ikon laddad: %s", png)
        except Exception:
            log.debug("Kunde inte ladda PNG-ikon", exc_info=True)

    # 2. ICO (Windows)
    if icon is None:
        ico = icon_ico_path()
        if ico is not None:
            try:
                from PyQt6.QtGui import QIcon

                icon = QIcon(str(ico))
                if icon.isNull():
                    icon = None
                else:
                    log.debug("App-ikon laddad (ICO): %s", ico)
            except Exception:
                log.debug("Kunde inte ladda ICO-ikon", exc_info=True)

    # 3. Fallback: rita kuvertikon programmatiskt
    if icon is None:
        icon = _draw_fallback_icon()
        log.info(
            "Ingen ikonfil hittades i %s – använder ritad fallback-ikon.",
            project_root() / "icons",
        )

    _icon_cache = icon
    return icon


def set_app_icon(app: object) -> bool:
    """Sätt app-ikonen på hela applikationen.

    QApplication.setWindowIcon gör att ALLA fönster och dialoger
    (huvudfönster, SendConfirmDialog, inställningar, QMessageBox)
    får app-ikonen – även taskbar-ikonen på Windows.

    Args:
        app: QApplication-instans

    Returns:
        True om ikonen sattes, annars False (app saknar setWindowIcon)
    """
    try:
        setter = getattr(app, "setWindowIcon", None)
        if setter is None:
            return False
        setter(get_app_icon())
        return True
    except Exception:
        log.debug("set_app_icon misslyckades", exc_info=True)
        return False


def clear_icon_cache() -> None:
    """Rensa ikon-cachen (används i tester)."""
    global _icon_cache
    _icon_cache = None


# ═══════════════════════════════════════════════════════════════════════
# Fallback-ikon (ritas med QPainter – ingen fil krävs)
# ═══════════════════════════════════════════════════════════════════════

_FALLBACK_SIZE = 256


def _draw_fallback_icon() -> object:
    """Rita en ren kuvertikon med QPainter i flera HiDPI-storlekar."""
    from PyQt6.QtCore import QPointF, QRectF, Qt
    from PyQt6.QtGui import (
        QColor,
        QIcon,
        QPainter,
        QPen,
        QPixmap,
    )

    icon = QIcon()
    base = QColor("#2563EB")
    for logical in (16, 24, 32, 48, 64, 128, _FALLBACK_SIZE):
        for ratio in (1.0, 2.0):
            px = max(1, int(round(logical * ratio)))
            pixmap = QPixmap(px, px)
            pixmap.setDevicePixelRatio(ratio)
            pixmap.fill(QColor(0, 0, 0, 0))

            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            try:
                s = float(logical)
                margin = max(1.0, s * 0.04)
                outer = QRectF(margin, margin, s - margin * 2, s - margin * 2)
                painter.setPen(QPen(QColor(255, 255, 255, 210), max(1.0, s * 0.03)))
                painter.setBrush(base)
                painter.drawEllipse(outer)

                env_x, env_y = s * 0.24, s * 0.34
                env_w, env_h = s * 0.52, s * 0.35
                env = QRectF(env_x, env_y, env_w, env_h)
                painter.setPen(QPen(QColor(255, 255, 255, 245), max(1.0, s * 0.024)))
                painter.setBrush(QColor(255, 255, 255, 245))
                painter.drawRoundedRect(env, s * 0.055, s * 0.055)

                fold_pen = QPen(base.darker(125), max(1.2, s * 0.024))
                fold_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(fold_pen)
                mid = QPointF(env_x + env_w / 2.0, env_y + env_h / 2.0 + s * 0.03)
                painter.drawLine(QPointF(env_x + s * 0.02, env_y + s * 0.05), mid)
                painter.drawLine(QPointF(env_x + env_w - s * 0.02, env_y + s * 0.05), mid)
            finally:
                painter.end()
            icon.addPixmap(pixmap)

    return icon


__all__ = [
    "get_app_icon",
    "set_app_icon",
    "icon_path",
    "icon_ico_path",
    "project_root",
    "clear_icon_cache",
]


def set_windows_app_id() -> bool:
    """Stable taskbar identity, set before any Qt window is created.

    Version-independent so upgrades keep the same taskbar grouping.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes
        result = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(WINDOWS_APP_ID)
        return result == 0
    except Exception:
        log.warning("Kunde inte sätta Windows app-ID", exc_info=True)
        return False
