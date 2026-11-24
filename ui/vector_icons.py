#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Skarpa vektorikoner och minnessnåla HiDPI-miniatyrer (1x–3x DPR).

Alla ikoner ritas direkt i fysiska enhetspixlar för 1.0x, 1.25x, 1.5x,
2.0x och 3.0x skalning med begränsade LRU-cachar, så att ikoner, färgbrickor
och bilageminiatyrer aldrig blir grumliga eller skapar obegränsad minnestillväxt.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Tuple

DPR_LEVELS: Tuple[float, ...] = (1.0, 1.25, 1.5, 2.0, 3.0)
IMAGE_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff",
})


def _pixel_dim(size: int, ratio: float) -> int:
    return max(1, int(round(size * ratio)))


@lru_cache(maxsize=96)
def _cached_vector_icon(kind: str, color_hex: str, size: int) -> object:
    from PyQt6.QtCore import QPointF, QRectF, Qt
    from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

    icon = QIcon()
    stroke_color = QColor(color_hex or "#334155")
    if not stroke_color.isValid():
        stroke_color = QColor("#334155")

    for ratio in DPR_LEVELS:
        px = _pixel_dim(size, ratio)
        pixmap = QPixmap(px, px)
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            s = float(size)
            pen = QPen(stroke_color, max(1.5, s * 0.095))
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            if kind == "send":
                path = QPainterPath()
                path.moveTo(s * 0.14, s * 0.48)
                path.lineTo(s * 0.86, s * 0.16)
                path.lineTo(s * 0.60, s * 0.86)
                path.lineTo(s * 0.44, s * 0.56)
                path.closeSubpath()
                painter.drawPath(path)
                painter.drawLine(QPointF(s * 0.44, s * 0.56), QPointF(s * 0.86, s * 0.16))
            elif kind == "contacts":
                painter.drawEllipse(QRectF(s * 0.30, s * 0.16, s * 0.40, s * 0.34))
                arc = QPainterPath()
                arc.moveTo(s * 0.16, s * 0.84)
                arc.cubicTo(
                    QPointF(s * 0.18, s * 0.58),
                    QPointF(s * 0.82, s * 0.58),
                    QPointF(s * 0.84, s * 0.84),
                )
                painter.drawPath(arc)
            elif kind == "templates":
                doc = QPainterPath()
                doc.moveTo(s * 0.22, s * 0.14)
                doc.lineTo(s * 0.60, s * 0.14)
                doc.lineTo(s * 0.78, s * 0.32)
                doc.lineTo(s * 0.78, s * 0.86)
                doc.lineTo(s * 0.22, s * 0.86)
                doc.closeSubpath()
                painter.drawPath(doc)
                painter.drawLine(QPointF(s * 0.58, s * 0.14), QPointF(s * 0.58, s * 0.33))
                painter.drawLine(QPointF(s * 0.58, s * 0.33), QPointF(s * 0.78, s * 0.33))
                painter.drawLine(QPointF(s * 0.34, s * 0.52), QPointF(s * 0.66, s * 0.52))
                painter.drawLine(QPointF(s * 0.34, s * 0.68), QPointF(s * 0.60, s * 0.68))
            elif kind == "preview":
                eye = QPainterPath()
                eye.moveTo(s * 0.10, s * 0.50)
                eye.quadTo(QPointF(s * 0.50, s * 0.16), QPointF(s * 0.90, s * 0.50))
                eye.quadTo(QPointF(s * 0.50, s * 0.84), QPointF(s * 0.10, s * 0.50))
                painter.drawPath(eye)
                painter.drawEllipse(QRectF(s * 0.38, s * 0.38, s * 0.24, s * 0.24))
            elif kind == "history":
                painter.drawEllipse(QRectF(s * 0.16, s * 0.16, s * 0.68, s * 0.68))
                painter.drawLine(QPointF(s * 0.50, s * 0.32), QPointF(s * 0.50, s * 0.52))
                painter.drawLine(QPointF(s * 0.50, s * 0.52), QPointF(s * 0.66, s * 0.60))
            elif kind == "logs":
                painter.drawRoundedRect(QRectF(s * 0.14, s * 0.18, s * 0.72, s * 0.64), s * 0.10, s * 0.10)
                pulse = QPainterPath()
                pulse.moveTo(s * 0.24, s * 0.54)
                pulse.lineTo(s * 0.38, s * 0.54)
                pulse.lineTo(s * 0.45, s * 0.34)
                pulse.lineTo(s * 0.55, s * 0.68)
                pulse.lineTo(s * 0.63, s * 0.48)
                pulse.lineTo(s * 0.76, s * 0.48)
                painter.drawPath(pulse)
            elif kind == "settings":
                for idx, knob_x in enumerate((0.36, 0.64, 0.44)):
                    y = s * (0.26 + idx * 0.24)
                    painter.drawLine(QPointF(s * 0.16, y), QPointF(s * 0.84, y))
                    painter.setBrush(stroke_color)
                    painter.drawEllipse(QPointF(s * knob_x, y), s * 0.08, s * 0.08)
                    painter.setBrush(Qt.BrushStyle.NoBrush)
            elif kind == "wizard":
                star = QPainterPath()
                star.moveTo(s * 0.50, s * 0.12)
                star.lineTo(s * 0.60, s * 0.40)
                star.lineTo(s * 0.88, s * 0.50)
                star.lineTo(s * 0.60, s * 0.60)
                star.lineTo(s * 0.50, s * 0.88)
                star.lineTo(s * 0.40, s * 0.60)
                star.lineTo(s * 0.12, s * 0.50)
                star.lineTo(s * 0.40, s * 0.40)
                star.closeSubpath()
                painter.drawPath(star)
            elif kind == "donate":
                heart = QPainterPath()
                heart.moveTo(s * 0.50, s * 0.82)
                heart.cubicTo(
                    QPointF(s * 0.12, s * 0.58),
                    QPointF(s * 0.14, s * 0.22),
                    QPointF(s * 0.36, s * 0.22),
                )
                heart.cubicTo(
                    QPointF(s * 0.45, s * 0.22),
                    QPointF(s * 0.50, s * 0.30),
                    QPointF(s * 0.50, s * 0.34),
                )
                heart.cubicTo(
                    QPointF(s * 0.50, s * 0.30),
                    QPointF(s * 0.55, s * 0.22),
                    QPointF(s * 0.64, s * 0.22),
                )
                heart.cubicTo(
                    QPointF(s * 0.86, s * 0.22),
                    QPointF(s * 0.88, s * 0.58),
                    QPointF(s * 0.50, s * 0.82),
                )
                painter.drawPath(heart)
            else:
                painter.drawRoundedRect(QRectF(s * 0.18, s * 0.24, s * 0.64, s * 0.52), s * 0.08, s * 0.08)
                painter.drawLine(QPointF(s * 0.22, s * 0.28), QPointF(s * 0.50, s * 0.52))
                painter.drawLine(QPointF(s * 0.78, s * 0.28), QPointF(s * 0.50, s * 0.52))
        finally:
            painter.end()
        icon.addPixmap(pixmap)
    return icon


def tab_icon(kind: str, color_hex: str = "#334155", size: int = 20) -> object:
    """Returnera skarp, temafärgad vektorikon för flik eller knapp."""
    from PyQt6.QtGui import QIcon

    return QIcon(_cached_vector_icon(str(kind or ""), str(color_hex or "#334155").lower(), max(12, int(size))))


@lru_cache(maxsize=64)
def _cached_color_swatch(color_hex: str, border_hex: str, size: int) -> object:
    from PyQt6.QtCore import QRectF
    from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

    icon = QIcon()
    fill = QColor(color_hex or "#2563EB")
    if not fill.isValid():
        fill = QColor("#2563EB")
    border = QColor(border_hex or "#64748B")
    if not border.isValid():
        border = QColor("#64748B")

    for ratio in (1.0, 1.5, 2.0, 3.0):
        px = _pixel_dim(size, ratio)
        pixmap = QPixmap(px, px)
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            s = float(size)
            painter.setPen(QPen(border, 1.0))
            painter.setBrush(fill)
            painter.drawRoundedRect(QRectF(1.0, 1.0, s - 2.0, s - 2.0), s * 0.25, s * 0.25)
        finally:
            painter.end()
        icon.addPixmap(pixmap)
    return icon


def color_swatch_icon(color_hex: str, border_hex: str = "#64748B", size: int = 16) -> object:
    """Skarp HiDPI-färgbricka för profildropdowns (begränsad LRU-cache)."""
    from PyQt6.QtGui import QIcon

    return QIcon(
        _cached_color_swatch(
            str(color_hex or "#2563EB").lower(),
            str(border_hex or "#64748B").lower(),
            max(12, int(size)),
        )
    )


def _doc_accent_for_suffix(suffix: str) -> str:
    ext = suffix.lower()
    if ext == ".pdf":
        return "#DC2626"
    if ext in {".doc", ".docx"}:
        return "#2563EB"
    if ext in {".xls", ".xlsx", ".csv", ".tsv"}:
        return "#16A34A"
    if ext in {".zip", ".7z", ".rar"}:
        return "#D97706"
    return "#64748B"


@lru_cache(maxsize=96)
def _cached_attachment_icon(resolved: str, mtime_ns: int, file_size: int, size: int) -> object:
    del mtime_ns, file_size  # del av cachenyckeln för automatisk invalidering vid filändring
    from PyQt6.QtCore import QRectF, QSize, Qt
    from PyQt6.QtGui import QColor, QIcon, QImageReader, QPainter, QPainterPath, QPen, QPixmap

    path = Path(resolved)
    suffix = path.suffix.lower()

    if suffix in IMAGE_SUFFIXES and path.is_file():
        icon = QIcon()
        loaded_any = False
        for ratio in (1.0, 2.0):
            target_px = _pixel_dim(size, ratio)
            reader = QImageReader(str(path))
            reader.setAutoTransform(True)
            orig = reader.size()
            if orig.isValid() and orig.width() > 0 and orig.height() > 0:
                scaled = orig.scaled(
                    QSize(target_px - int(2 * ratio), target_px - int(2 * ratio)),
                    Qt.AspectRatioMode.KeepAspectRatio,
                )
                reader.setScaledSize(QSize(max(1, scaled.width()), max(1, scaled.height())))
            img = reader.read()
            if img.isNull():
                break
            canvas = QPixmap(target_px, target_px)
            canvas.setDevicePixelRatio(ratio)
            canvas.fill(QColor(0, 0, 0, 0))
            painter = QPainter(canvas)
            try:
                painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
                s = float(size)
                clip = QPainterPath()
                clip.addRoundedRect(QRectF(1.0, 1.0, s - 2.0, s - 2.0), 4.0, 4.0)
                painter.fillPath(clip, QColor("#0F172A"))
                painter.save()
                painter.setClipPath(clip)
                logical_w = img.width() / ratio
                logical_h = img.height() / ratio
                x = (s - logical_w) / 2.0
                y = (s - logical_h) / 2.0
                painter.drawImage(QRectF(x, y, logical_w, logical_h), img)
                painter.restore()
                painter.setPen(QPen(QColor("#94A3B8"), 1.0))
                painter.drawRoundedRect(QRectF(0.5, 0.5, s - 1.0, s - 1.0), 4.0, 4.0)
            finally:
                painter.end()
            icon.addPixmap(canvas)
            loaded_any = True
        if loaded_any:
            return icon

    return _cached_vector_icon("templates", _doc_accent_for_suffix(suffix), size)


def attachment_icon(path: object, size: int = 28) -> object:
    """Skarp och minnessnål miniatyrikon för bild- och dokumentbilagor."""
    from PyQt6.QtGui import QIcon

    candidate = Path(str(path or ""))
    try:
        stat = candidate.stat()
        resolved = str(candidate.resolve())
        mtime_ns = int(stat.st_mtime_ns)
        fsize = int(stat.st_size)
    except OSError:
        resolved = str(candidate)
        mtime_ns = 0
        fsize = 0
    return QIcon(_cached_attachment_icon(resolved, mtime_ns, fsize, max(16, int(size))))


def clear_vector_icon_caches() -> None:
    """Töm alla ikoncachar (används i tester eller vid minnesrensning)."""
    _cached_vector_icon.cache_clear()
    _cached_color_swatch.cache_clear()
    _cached_attachment_icon.cache_clear()


__all__ = [
    "DPR_LEVELS",
    "attachment_icon",
    "clear_vector_icon_caches",
    "color_swatch_icon",
    "tab_icon",
]
