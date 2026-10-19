#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/app_icon.py – Central app-ikon för EmailApp (används ÖVERALLT)

Version: 1.0 – EN IKON, ALLA YTOR

Ikonen används på:
  - Huvudfönstret (taskbar + titelrad) – via QApplication.setWindowIcon
  - Alla dialoger (SendConfirmDialog, inställningar, meddelanden) –
    ärver automatiskt app-ikonen på Windows
  - Systemfältet (tray) – via ui/tray.py (idle-läget = app-ikonen,
    statuslägen = app-ikonen + liten status-badge)
  - Startup-feldialoger (main.pyw _safe_show_critical)

Fil: icons/app_icon.png (512x512 RGBA, rundade hörn) + .ico (Windows)

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

    # 1. PNG
    png = icon_path()
    if png is not None:
        try:
            from PyQt6.QtGui import QIcon

            icon = QIcon(str(png))
            if not icon.isNull():
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
                if not icon.isNull():
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
    """Rita en ren kuvertikon med QPainter (blå rund botten + vitt kuvert)."""
    from PyQt6.QtCore import QPoint, QRectF, Qt
    from PyQt6.QtGui import (
        QColor,
        QIcon,
        QPainter,
        QPen,
        QPixmap,
    )

    size = _FALLBACK_SIZE
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    try:
        base = QColor("#2563EB")
        outer = QRectF(10, 10, size - 20, size - 20)
        painter.setPen(QPen(QColor(255, 255, 255, 210), 8))
        painter.setBrush(base)
        painter.drawEllipse(outer)

        env_x, env_y, env_w, env_h = 62, 88, 132, 90
        env = QRectF(env_x, env_y, env_w, env_h)
        painter.setPen(QPen(QColor(255, 255, 255, 245), 6))
        painter.setBrush(QColor(255, 255, 255, 245))
        painter.drawRoundedRect(env, 14, 14)

        fold_pen = QPen(base.darker(125), 6)
        fold_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(fold_pen)
        mid = QPoint(env_x + env_w // 2, env_y + env_h // 2 + 8)
        painter.drawLine(QPoint(env_x + 5, env_y + 12), mid)
        painter.drawLine(QPoint(env_x + env_w - 5, env_y + 12), mid)
    finally:
        painter.end()

    return QIcon(pixmap)


__all__ = [
    "get_app_icon",
    "set_app_icon",
    "icon_path",
    "icon_ico_path",
    "project_root",
    "clear_icon_cache",
]
