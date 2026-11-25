#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/app_icon.py – Central logotyp & app-ikon för E-postofferten (används ÖVERALLT)

Version: 2.0 – Skarp vektorlogotyp (SVG-original + multi-size ICO/PNG + HiDPI-hjälpare)

Ikonen och logotypen används konsekvent på:
  - Huvudfönstret (taskbar + titelrad + hero-huvud med horisontell logotyp)
  - Alla dialoger (SendConfirmDialog, Mall-wizard, Om E-postofferten, Stöd projektet)
  - Systemfältet (tray) – via ui/tray.py (idle-läget + status-badges)
  - Startup-feldialoger (main.pyw _safe_show_critical)

Filer:
  - icons/app_icon.svg + app_icon.png (1024x1024) + app_icon.ico (16–256px)
  - icons/mailoffer-logo.svg / mailoffer-logo.png (för ljust underlag)
  - icons/mailoffer-logo-light.svg / mailoffer-logo-light.png (för mörkt/blått underlag)
  - tryck/E-postofferten-*.svg (redigerbara vektororiginal för tryck)
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

ICON_FILE_NAME = "app_icon.png"
ICON_ICO_NAME = "app_icon.ico"
ICON_SVG_NAME = "app_icon.svg"
LOGO_SVG_NAME = "mailoffer-logo.svg"
LOGO_LIGHT_SVG_NAME = "mailoffer-logo-light.svg"
LOGO_PNG_NAME = "mailoffer-logo.png"
LOGO_LIGHT_PNG_NAME = "mailoffer-logo-light.png"
WINDOWS_APP_ID = "RickardLangkvist.MailOffer"

# Ikon-cache (laddas en gång)
_icon_cache: Optional[object] = None  # QIcon


def project_root() -> Path:
    """Projektroten: förälder till core/-mappen (där main.pyw ligger)."""
    return Path(__file__).resolve().parents[1]


def icon_svg_path() -> Optional[Path]:
    """Sökväg till icons/app_icon.svg (None om filen saknas)."""
    candidate = project_root() / "icons" / ICON_SVG_NAME
    return candidate if candidate.is_file() else None


def icon_path() -> Optional[Path]:
    """Sökväg till icons/app_icon.png (None om filen saknas)."""
    candidate = project_root() / "icons" / ICON_FILE_NAME
    return candidate if candidate.is_file() else None


def icon_ico_path() -> Optional[Path]:
    """Sökväg till icons/app_icon.ico (Windows) – None om filen saknas."""
    candidate = project_root() / "icons" / ICON_ICO_NAME
    return candidate if candidate.is_file() else None


def logo_svg_path(*, light_text: bool = False) -> Optional[Path]:
    """Sökväg till horisontell SVG-logotyp (vit eller mörkblå ordbild)."""
    name = LOGO_LIGHT_SVG_NAME if light_text else LOGO_SVG_NAME
    candidate = project_root() / "icons" / name
    if candidate.is_file():
        return candidate
    fallback = project_root() / "icons" / LOGO_SVG_NAME
    return fallback if fallback.is_file() else None


def logo_png_path(*, light_text: bool = False) -> Optional[Path]:
    """Sökväg till horisontell PNG-logotyp (2560x640 RGBA)."""
    name = LOGO_LIGHT_PNG_NAME if light_text else LOGO_PNG_NAME
    candidate = project_root() / "icons" / name
    if candidate.is_file():
        return candidate
    fallback = project_root() / "icons" / LOGO_PNG_NAME
    return fallback if fallback.is_file() else None


def get_app_icon() -> object:
    """Returnera app-ikonen (QIcon) – cachad, knivskarp på alla skärm-DPI.

    Prioritet:
      1. icons/app_icon.svg (vektor – skalas exakt för 1.0x–3.0x DPI)
      2. icons/app_icon.ico + icons/app_icon.png (multi-size 16–1024px)
      3. Programmatiskt ritad kuvert+offert-ikon (QPainter) – fungerar alltid
    """
    global _icon_cache
    if _icon_cache is not None:
        return _icon_cache

    icon: Optional[object] = None

    svg = icon_svg_path()
    if svg is not None:
        try:
            from PyQt6.QtCore import QSize
            from PyQt6.QtGui import QIcon

            candidate = QIcon(str(svg))
            if not candidate.isNull() and not candidate.pixmap(QSize(32, 32), 1.0).isNull():
                icon = candidate
        except Exception:
            log.debug("SVG icon unavailable; using raster fallback", exc_info=True)

    png = icon_path()
    if icon is None and png is not None:
        try:
            from PyQt6.QtGui import QIcon

            candidate = QIcon(str(png))
            if not candidate.isNull():
                ico = icon_ico_path()
                if ico is not None:
                    ico_icon = QIcon(str(ico))
                    if not ico_icon.isNull():
                        for sz in (16, 24, 32, 48, 64, 128, 256):
                            px = ico_icon.pixmap(sz, sz)
                            if not px.isNull():
                                candidate.addPixmap(px)
                icon = candidate
        except Exception:
            log.debug("Kunde inte ladda PNG-ikon", exc_info=True)

    if icon is None:
        ico = icon_ico_path()
        if ico is not None:
            try:
                from PyQt6.QtGui import QIcon

                candidate = QIcon(str(ico))
                if not candidate.isNull():
                    icon = candidate
            except Exception:
                log.debug("Kunde inte ladda ICO-ikon", exc_info=True)

    if icon is None:
        icon = _draw_fallback_icon()
        log.info(
            "Ingen ikonfil hittades i %s – använder ritad fallback-ikon.",
            project_root() / "icons",
        )

    _icon_cache = icon
    return icon


def get_brand_mark_pixmap(size: int = 72, dpr: float = 1.0) -> object:
    """Returnera knivskarp HiDPI-QPixmap av den kvadratiska app-symbolen."""
    from PyQt6.QtCore import QSize, Qt
    from PyQt6.QtGui import QGuiApplication, QPixmap

    if QGuiApplication.instance() is None:
        return None
    ratio = max(1.0, float(dpr or 1.0))
    logical = max(16, int(size))
    svg = icon_svg_path()
    if svg is not None:
        try:
            from PyQt6.QtSvg import QSvgRenderer  # type: ignore
            from PyQt6.QtGui import QColor, QPainter

            renderer = QSvgRenderer(str(svg))
            if renderer.isValid():
                px = max(1, int(round(logical * ratio)))
                canvas = QPixmap(px, px)
                canvas.fill(QColor(0, 0, 0, 0))
                painter = QPainter(canvas)
                try:
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                    renderer.render(painter)
                finally:
                    painter.end()
                canvas.setDevicePixelRatio(ratio)
                return canvas
        except Exception:
            pass

    icon = get_app_icon()
    if icon is not None:
        try:
            px_icon = icon.pixmap(QSize(logical, logical), ratio)
            if not px_icon.isNull():
                return px_icon
        except Exception:
            pass

    png = icon_path()
    if png is not None:
        raw = QPixmap(str(png))
        if not raw.isNull():
            target = max(1, int(round(logical * ratio)))
            scaled = raw.scaled(
                target,
                target,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            scaled.setDevicePixelRatio(ratio)
            return scaled
    return QPixmap()


def get_logo_pixmap(
    height: int = 38, *, light_text: bool = False, dpr: float = 1.0
) -> object:
    """Returnera knivskarp HiDPI-QPixmap av horisontella logotypen (4:1)."""
    from PyQt6.QtCore import QSize, Qt
    from PyQt6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPixmap

    if QGuiApplication.instance() is None:
        return None
    ratio = max(1.0, float(dpr or 1.0))
    logical_h = max(18, int(height))
    logical_w = int(round(logical_h * 4.0))

    svg = logo_svg_path(light_text=light_text)
    if svg is not None:
        try:
            from PyQt6.QtSvg import QSvgRenderer  # type: ignore

            renderer = QSvgRenderer(str(svg))
            if renderer.isValid():
                px_w = max(1, int(round(logical_w * ratio)))
                px_h = max(1, int(round(logical_h * ratio)))
                canvas = QPixmap(px_w, px_h)
                canvas.fill(QColor(0, 0, 0, 0))
                painter = QPainter(canvas)
                try:
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                    renderer.render(painter)
                finally:
                    painter.end()
                canvas.setDevicePixelRatio(ratio)
                return canvas
        except Exception:
            pass
        try:
            svg_icon = QIcon(str(svg))
            if not svg_icon.isNull():
                candidate = svg_icon.pixmap(QSize(logical_w, logical_h), ratio)
                if not candidate.isNull():
                    return candidate
        except Exception:
            pass

    png = logo_png_path(light_text=light_text)
    if png is not None:
        raw = QPixmap(str(png))
        if not raw.isNull():
            px_w = max(1, int(round(logical_w * ratio)))
            px_h = max(1, int(round(logical_h * ratio)))
            scaled = raw.scaled(
                px_w,
                px_h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            scaled.setDevicePixelRatio(ratio)
            return scaled
    return QPixmap()


def set_app_icon(app: object) -> bool:
    """Sätt app-ikonen på hela applikationen."""
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


_FALLBACK_SIZE = 256


def _draw_fallback_icon() -> object:
    """Rita skarp kuvert+offert+guldsigill-ikon i flera HiDPI-storlekar."""
    from PyQt6.QtCore import QPointF, QRectF, Qt
    from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

    icon = QIcon()
    plate = QColor("#1D4ED8")
    rim = QColor("#38BDF8")
    gold = QColor("#FBBF24")
    navy = QColor("#0B1942")

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
                m = max(1.0, s * 0.05)
                outer = QRectF(m, m, s - m * 2, s - m * 2)
                painter.setPen(QPen(rim, max(1.0, s * 0.03)))
                painter.setBrush(plate)
                painter.drawRoundedRect(outer, s * 0.21, s * 0.21)

                # Offer sheet
                card = QRectF(s * 0.27, s * 0.22, s * 0.46, s * 0.36)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor("#FFFFFF"))
                painter.drawRoundedRect(card, s * 0.04, s * 0.04)

                # Envelope front
                env = QRectF(s * 0.17, s * 0.42, s * 0.66, s * 0.35)
                painter.setBrush(QColor("#EFF6FF"))
                painter.drawRoundedRect(env, s * 0.06, s * 0.06)

                fold_pen = QPen(navy, max(1.2, s * 0.04))
                fold_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                fold_pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
                painter.setPen(fold_pen)
                vpath = QPainterPath()
                vpath.moveTo(QPointF(s * 0.19, s * 0.44))
                vpath.lineTo(QPointF(s * 0.50, s * 0.64))
                vpath.lineTo(QPointF(s * 0.81, s * 0.44))
                painter.drawPath(vpath)

                # Gold offer approval seal
                seal_r = s * 0.13
                cx, cy = s * 0.72, s * 0.67
                painter.setPen(QPen(navy, max(1.0, s * 0.03)))
                painter.setBrush(gold)
                painter.drawEllipse(QPointF(cx, cy), seal_r, seal_r)
                chk = QPainterPath()
                chk.moveTo(cx - seal_r * 0.42, cy)
                chk.lineTo(cx - seal_r * 0.10, cy + seal_r * 0.34)
                chk.lineTo(cx + seal_r * 0.46, cy - seal_r * 0.34)
                painter.setPen(QPen(navy, max(1.2, s * 0.042)))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPath(chk)
            finally:
                painter.end()
            icon.addPixmap(pixmap)

    return icon


__all__ = [
    "WINDOWS_APP_ID",
    "clear_icon_cache",
    "get_app_icon",
    "get_brand_mark_pixmap",
    "get_logo_pixmap",
    "icon_ico_path",
    "icon_path",
    "icon_svg_path",
    "logo_png_path",
    "logo_svg_path",
    "project_root",
    "set_app_icon",
    "set_windows_app_id",
]


def set_windows_app_id() -> bool:
    """Stable taskbar identity, set before any Qt window is created."""
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        result = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            WINDOWS_APP_ID
        )
        return result == 0
    except Exception:
        log.warning("Kunde inte sätta Windows app-ID", exc_info=True)
        return False
