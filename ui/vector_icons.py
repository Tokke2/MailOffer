#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Skarpa vektorikoner och minnessnåla HiDPI-miniatyrer (1x–3x DPR).

Alla ikoner ritas direkt i fysiska enhetspixlar för 1.0x, 1.25x, 1.5x,
2.0x och 3.0x skalning med begränsade LRU-cachar, så att flikar, knappar,
menyer, färgbrickor och bilageminiatyrer alltid är knivskarpa.
"""

from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path
from typing import Tuple

DPR_LEVELS: Tuple[float, ...] = (1.0, 1.25, 1.5, 2.0, 3.0)
IMAGE_SUFFIXES = frozenset({
    ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff",
})

SUPPORTED_ICON_KINDS: Tuple[str, ...] = (
    "send",
    "contacts",
    "templates",
    "preview",
    "history",
    "logs",
    "settings",
    "wizard",
    "donate",
    "plus",
    "edit",
    "trash",
    "refresh",
    "update",
    "upload",
    "import",
    "copy",
    "folder",
    "archive",
    "check",
    "shield",
    "search",
    "filter",
    "attachment",
    "theme_dark",
    "theme_light",
    "theme_system",
    "info",
    "keyboard",
    "backup",
    "clean",
    "quit",
    "mail",
)


def _pixel_dim(size: int, ratio: float) -> int:
    return max(1, int(round(size * ratio)))


@lru_cache(maxsize=192)
def _cached_vector_icon(kind: str, color_hex: str, size: int) -> object:
    from PyQt6.QtCore import QPointF, QRectF, Qt
    from PyQt6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

    icon = QIcon()
    stroke_color = QColor(color_hex or "#334155")
    if not stroke_color.isValid():
        stroke_color = QColor("#334155")

    accent_fill = QColor(stroke_color)
    accent_fill.setAlpha(34)

    for ratio in DPR_LEVELS:
        px = _pixel_dim(size, ratio)
        pixmap = QPixmap(px, px)
        pixmap.setDevicePixelRatio(ratio)
        pixmap.fill(QColor(0, 0, 0, 0))

        painter = QPainter(pixmap)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            s = float(size)
            sw = max(1.45, s * 0.092)
            pen = QPen(stroke_color, sw)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            if kind == "send":
                plane = QPainterPath()
                plane.moveTo(s * 0.12, s * 0.46)
                plane.lineTo(s * 0.88, s * 0.15)
                plane.lineTo(s * 0.62, s * 0.87)
                plane.lineTo(s * 0.44, s * 0.56)
                plane.closeSubpath()
                painter.setBrush(accent_fill)
                painter.drawPath(plane)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.44, s * 0.56), QPointF(s * 0.88, s * 0.15))
                painter.drawLine(QPointF(s * 0.44, s * 0.56), QPointF(s * 0.44, s * 0.76))

            elif kind in ("contacts", "users"):
                painter.setBrush(accent_fill)
                painter.drawEllipse(QRectF(s * 0.22, s * 0.15, s * 0.34, s * 0.32))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                body = QPainterPath()
                body.moveTo(s * 0.12, s * 0.84)
                body.cubicTo(
                    QPointF(s * 0.13, s * 0.58),
                    QPointF(s * 0.65, s * 0.58),
                    QPointF(s * 0.66, s * 0.84),
                )
                painter.drawPath(body)
                # Secondary contact silhouette
                head2 = QPainterPath()
                head2.moveTo(s * 0.63, s * 0.20)
                head2.cubicTo(
                    QPointF(s * 0.79, s * 0.20),
                    QPointF(s * 0.79, s * 0.44),
                    QPointF(s * 0.63, s * 0.45),
                )
                painter.drawPath(head2)
                sh2 = QPainterPath()
                sh2.moveTo(s * 0.68, s * 0.58)
                sh2.cubicTo(
                    QPointF(s * 0.82, s * 0.60),
                    QPointF(s * 0.88, s * 0.70),
                    QPointF(s * 0.89, s * 0.83),
                )
                painter.drawPath(sh2)

            elif kind in ("templates", "template"):
                doc = QPainterPath()
                doc.moveTo(s * 0.22, s * 0.13)
                doc.lineTo(s * 0.59, s * 0.13)
                doc.lineTo(s * 0.79, s * 0.33)
                doc.lineTo(s * 0.79, s * 0.87)
                doc.lineTo(s * 0.22, s * 0.87)
                doc.closeSubpath()
                painter.setBrush(accent_fill)
                painter.drawPath(doc)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                flap = QPainterPath()
                flap.moveTo(s * 0.58, s * 0.13)
                flap.lineTo(s * 0.58, s * 0.33)
                flap.lineTo(s * 0.79, s * 0.33)
                painter.drawPath(flap)
                painter.drawLine(QPointF(s * 0.34, s * 0.50), QPointF(s * 0.66, s * 0.50))
                painter.drawLine(QPointF(s * 0.34, s * 0.65), QPointF(s * 0.66, s * 0.65))
                painter.drawLine(QPointF(s * 0.34, s * 0.77), QPointF(s * 0.52, s * 0.77))

            elif kind in ("preview", "eye"):
                eye = QPainterPath()
                eye.moveTo(s * 0.10, s * 0.50)
                eye.quadTo(QPointF(s * 0.50, s * 0.15), QPointF(s * 0.90, s * 0.50))
                eye.quadTo(QPointF(s * 0.50, s * 0.85), QPointF(s * 0.10, s * 0.50))
                painter.setBrush(accent_fill)
                painter.drawPath(eye)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawEllipse(QRectF(s * 0.37, s * 0.37, s * 0.26, s * 0.26))
                painter.setBrush(stroke_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(s * 0.50, s * 0.50), s * 0.06, s * 0.06)

            elif kind == "history":
                painter.setBrush(accent_fill)
                painter.drawEllipse(QRectF(s * 0.16, s * 0.16, s * 0.68, s * 0.68))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.50, s * 0.31), QPointF(s * 0.50, s * 0.51))
                painter.drawLine(QPointF(s * 0.50, s * 0.51), QPointF(s * 0.66, s * 0.60))

            elif kind in ("logs", "log"):
                painter.setBrush(accent_fill)
                painter.drawRoundedRect(QRectF(s * 0.13, s * 0.17, s * 0.74, s * 0.66), s * 0.11, s * 0.11)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                pulse = QPainterPath()
                pulse.moveTo(s * 0.23, s * 0.54)
                pulse.lineTo(s * 0.36, s * 0.54)
                pulse.lineTo(s * 0.44, s * 0.33)
                pulse.lineTo(s * 0.55, s * 0.68)
                pulse.lineTo(s * 0.63, s * 0.47)
                pulse.lineTo(s * 0.77, s * 0.47)
                painter.drawPath(pulse)

            elif kind == "settings":
                for idx, knob_x in enumerate((0.35, 0.65, 0.43)):
                    y = s * (0.26 + idx * 0.24)
                    painter.drawLine(QPointF(s * 0.15, y), QPointF(s * (knob_x - 0.09), y))
                    painter.drawLine(QPointF(s * (knob_x + 0.09), y), QPointF(s * 0.85, y))
                    painter.setBrush(accent_fill)
                    painter.drawEllipse(QPointF(s * knob_x, y), s * 0.085, s * 0.085)
                    painter.setBrush(Qt.BrushStyle.NoBrush)

            elif kind in ("wizard", "sparkle"):
                star = QPainterPath()
                star.moveTo(s * 0.46, s * 0.12)
                star.quadTo(QPointF(s * 0.48, s * 0.42), QPointF(s * 0.80, s * 0.46))
                star.quadTo(QPointF(s * 0.48, s * 0.50), QPointF(s * 0.46, s * 0.82))
                star.quadTo(QPointF(s * 0.44, s * 0.50), QPointF(s * 0.12, s * 0.46))
                star.quadTo(QPointF(s * 0.44, s * 0.42), QPointF(s * 0.46, s * 0.12))
                painter.setBrush(accent_fill)
                painter.drawPath(star)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                # Secondary mini sparkle
                painter.drawLine(QPointF(s * 0.76, s * 0.16), QPointF(s * 0.76, s * 0.32))
                painter.drawLine(QPointF(s * 0.68, s * 0.24), QPointF(s * 0.84, s * 0.24))

            elif kind in ("donate", "heart"):
                heart = QPainterPath()
                heart.moveTo(s * 0.50, s * 0.83)
                heart.cubicTo(
                    QPointF(s * 0.11, s * 0.58),
                    QPointF(s * 0.13, s * 0.21),
                    QPointF(s * 0.35, s * 0.21),
                )
                heart.cubicTo(
                    QPointF(s * 0.45, s * 0.21),
                    QPointF(s * 0.50, s * 0.29),
                    QPointF(s * 0.50, s * 0.34),
                )
                heart.cubicTo(
                    QPointF(s * 0.50, s * 0.29),
                    QPointF(s * 0.55, s * 0.21),
                    QPointF(s * 0.65, s * 0.21),
                )
                heart.cubicTo(
                    QPointF(s * 0.87, s * 0.21),
                    QPointF(s * 0.89, s * 0.58),
                    QPointF(s * 0.50, s * 0.83),
                )
                painter.setBrush(accent_fill)
                painter.drawPath(heart)

            elif kind in ("plus", "add"):
                painter.setBrush(accent_fill)
                painter.drawEllipse(QRectF(s * 0.15, s * 0.15, s * 0.70, s * 0.70))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.50, s * 0.31), QPointF(s * 0.50, s * 0.69))
                painter.drawLine(QPointF(s * 0.31, s * 0.50), QPointF(s * 0.69, s * 0.50))

            elif kind == "edit":
                pen_path = QPainterPath()
                pen_path.moveTo(s * 0.20, s * 0.80)
                pen_path.lineTo(s * 0.25, s * 0.61)
                pen_path.lineTo(s * 0.66, s * 0.20)
                pen_path.lineTo(s * 0.80, s * 0.34)
                pen_path.lineTo(s * 0.39, s * 0.75)
                pen_path.closeSubpath()
                painter.setBrush(accent_fill)
                painter.drawPath(pen_path)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.57, s * 0.29), QPointF(s * 0.71, s * 0.43))

            elif kind in ("trash", "delete"):
                painter.drawLine(QPointF(s * 0.20, s * 0.27), QPointF(s * 0.80, s * 0.27))
                painter.drawLine(QPointF(s * 0.38, s * 0.17), QPointF(s * 0.62, s * 0.17))
                bin_rect = QRectF(s * 0.26, s * 0.27, s * 0.48, s * 0.57)
                painter.setBrush(accent_fill)
                painter.drawRoundedRect(bin_rect, s * 0.07, s * 0.07)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.42, s * 0.41), QPointF(s * 0.42, s * 0.71))
                painter.drawLine(QPointF(s * 0.58, s * 0.41), QPointF(s * 0.58, s * 0.71))

            elif kind in ("refresh", "sync"):
                arc1 = QPainterPath()
                arc1.arcMoveTo(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64), 35)
                arc1.arcTo(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64), 35, 135)
                painter.drawPath(arc1)
                painter.drawLine(QPointF(s * 0.76, s * 0.19), QPointF(s * 0.77, s * 0.36))
                painter.drawLine(QPointF(s * 0.61, s * 0.34), QPointF(s * 0.77, s * 0.36))
                arc2 = QPainterPath()
                arc2.arcMoveTo(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64), 215)
                arc2.arcTo(QRectF(s * 0.18, s * 0.18, s * 0.64, s * 0.64), 215, 135)
                painter.drawPath(arc2)
                painter.drawLine(QPointF(s * 0.23, s * 0.64), QPointF(s * 0.24, s * 0.81))
                painter.drawLine(QPointF(s * 0.23, s * 0.64), QPointF(s * 0.39, s * 0.66))

            elif kind in ("update", "download"):
                painter.drawLine(QPointF(s * 0.50, s * 0.16), QPointF(s * 0.50, s * 0.63))
                arr = QPainterPath()
                arr.moveTo(s * 0.32, s * 0.47)
                arr.lineTo(s * 0.50, s * 0.65)
                arr.lineTo(s * 0.68, s * 0.47)
                painter.drawPath(arr)
                tray = QPainterPath()
                tray.moveTo(s * 0.17, s * 0.62)
                tray.lineTo(s * 0.17, s * 0.78)
                tray.quadTo(QPointF(s * 0.17, s * 0.84), QPointF(s * 0.25, s * 0.84))
                tray.lineTo(s * 0.75, s * 0.84)
                tray.quadTo(QPointF(s * 0.83, s * 0.84), QPointF(s * 0.83, s * 0.78))
                tray.lineTo(s * 0.83, s * 0.62)
                painter.drawPath(tray)

            elif kind in ("upload", "export"):
                painter.drawLine(QPointF(s * 0.50, s * 0.64), QPointF(s * 0.50, s * 0.18))
                arr = QPainterPath()
                arr.moveTo(s * 0.32, s * 0.35)
                arr.lineTo(s * 0.50, s * 0.17)
                arr.lineTo(s * 0.68, s * 0.35)
                painter.drawPath(arr)
                tray = QPainterPath()
                tray.moveTo(s * 0.17, s * 0.62)
                tray.lineTo(s * 0.17, s * 0.78)
                tray.quadTo(QPointF(s * 0.17, s * 0.84), QPointF(s * 0.25, s * 0.84))
                tray.lineTo(s * 0.75, s * 0.84)
                tray.quadTo(QPointF(s * 0.83, s * 0.84), QPointF(s * 0.83, s * 0.78))
                tray.lineTo(s * 0.83, s * 0.62)
                painter.drawPath(tray)

            elif kind == "import":
                painter.setBrush(accent_fill)
                painter.drawRoundedRect(QRectF(s * 0.34, s * 0.15, s * 0.50, s * 0.70), s * 0.08, s * 0.08)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.13, s * 0.50), QPointF(s * 0.60, s * 0.50))
                arr = QPainterPath()
                arr.moveTo(s * 0.45, s * 0.35)
                arr.lineTo(s * 0.61, s * 0.50)
                arr.lineTo(s * 0.45, s * 0.65)
                painter.drawPath(arr)

            elif kind in ("copy", "duplicate"):
                painter.drawRoundedRect(QRectF(s * 0.16, s * 0.16, s * 0.48, s * 0.52), s * 0.08, s * 0.08)
                painter.setBrush(accent_fill)
                painter.drawRoundedRect(QRectF(s * 0.34, s * 0.32, s * 0.50, s * 0.52), s * 0.08, s * 0.08)

            elif kind == "folder":
                fld = QPainterPath()
                fld.moveTo(s * 0.14, s * 0.26)
                fld.lineTo(s * 0.40, s * 0.26)
                fld.lineTo(s * 0.48, s * 0.36)
                fld.lineTo(s * 0.86, s * 0.36)
                fld.lineTo(s * 0.86, s * 0.80)
                fld.lineTo(s * 0.14, s * 0.80)
                fld.closeSubpath()
                painter.setBrush(accent_fill)
                painter.drawPath(fld)

            elif kind == "archive":
                painter.drawRoundedRect(QRectF(s * 0.14, s * 0.18, s * 0.72, s * 0.18), s * 0.05, s * 0.05)
                painter.setBrush(accent_fill)
                painter.drawRoundedRect(QRectF(s * 0.20, s * 0.36, s * 0.60, s * 0.46), s * 0.07, s * 0.07)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.40, s * 0.53), QPointF(s * 0.60, s * 0.53))

            elif kind in ("check", "verify"):
                painter.setBrush(accent_fill)
                painter.drawEllipse(QRectF(s * 0.15, s * 0.15, s * 0.70, s * 0.70))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                chk = QPainterPath()
                chk.moveTo(s * 0.31, s * 0.51)
                chk.lineTo(s * 0.45, s * 0.65)
                chk.lineTo(s * 0.70, s * 0.37)
                painter.drawPath(chk)

            elif kind == "shield":
                sh = QPainterPath()
                sh.moveTo(s * 0.50, s * 0.13)
                sh.lineTo(s * 0.82, s * 0.26)
                sh.lineTo(s * 0.82, s * 0.52)
                sh.quadTo(QPointF(s * 0.82, s * 0.76), QPointF(s * 0.50, s * 0.88))
                sh.quadTo(QPointF(s * 0.18, s * 0.76), QPointF(s * 0.18, s * 0.52))
                sh.lineTo(s * 0.18, s * 0.26)
                sh.closeSubpath()
                painter.setBrush(accent_fill)
                painter.drawPath(sh)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                chk = QPainterPath()
                chk.moveTo(s * 0.35, s * 0.51)
                chk.lineTo(s * 0.46, s * 0.62)
                chk.lineTo(s * 0.66, s * 0.40)
                painter.drawPath(chk)

            elif kind == "search":
                painter.setBrush(accent_fill)
                painter.drawEllipse(QRectF(s * 0.16, s * 0.16, s * 0.50, s * 0.50))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.59, s * 0.59), QPointF(s * 0.84, s * 0.84))

            elif kind == "filter":
                fn = QPainterPath()
                fn.moveTo(s * 0.15, s * 0.20)
                fn.lineTo(s * 0.85, s * 0.20)
                fn.lineTo(s * 0.58, s * 0.52)
                fn.lineTo(s * 0.58, s * 0.80)
                fn.lineTo(s * 0.42, s * 0.84)
                fn.lineTo(s * 0.42, s * 0.52)
                fn.closeSubpath()
                painter.setBrush(accent_fill)
                painter.drawPath(fn)

            elif kind == "attachment":
                clip = QPainterPath()
                clip.moveTo(s * 0.66, s * 0.34)
                clip.lineTo(s * 0.37, s * 0.63)
                clip.cubicTo(
                    QPointF(s * 0.29, s * 0.71),
                    QPointF(s * 0.41, s * 0.83),
                    QPointF(s * 0.49, s * 0.75),
                )
                clip.lineTo(s * 0.79, s * 0.45)
                clip.cubicTo(
                    QPointF(s * 0.91, s * 0.33),
                    QPointF(s * 0.71, s * 0.13),
                    QPointF(s * 0.59, s * 0.25),
                )
                clip.lineTo(s * 0.25, s * 0.59)
                clip.cubicTo(
                    QPointF(s * 0.09, s * 0.75),
                    QPointF(s * 0.35, s * 0.95),
                    QPointF(s * 0.54, s * 0.79),
                )
                painter.drawPath(clip)

            elif kind == "theme_dark":
                moon = QPainterPath()
                moon.moveTo(s * 0.66, s * 0.18)
                moon.cubicTo(
                    QPointF(s * 0.36, s * 0.20),
                    QPointF(s * 0.20, s * 0.54),
                    QPointF(s * 0.40, s * 0.76),
                )
                moon.cubicTo(
                    QPointF(s * 0.56, s * 0.90),
                    QPointF(s * 0.79, s * 0.81),
                    QPointF(s * 0.84, s * 0.64),
                )
                moon.cubicTo(
                    QPointF(s * 0.62, s * 0.68),
                    QPointF(s * 0.46, s * 0.48),
                    QPointF(s * 0.66, s * 0.18),
                )
                painter.setBrush(accent_fill)
                painter.drawPath(moon)

            elif kind == "theme_light":
                painter.setBrush(accent_fill)
                painter.drawEllipse(QPointF(s * 0.50, s * 0.50), s * 0.19, s * 0.19)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                for deg in range(0, 360, 45):
                    rad = math.radians(deg)
                    painter.drawLine(
                        QPointF(s * 0.50 + math.cos(rad) * s * 0.28, s * 0.50 + math.sin(rad) * s * 0.28),
                        QPointF(s * 0.50 + math.cos(rad) * s * 0.39, s * 0.50 + math.sin(rad) * s * 0.39),
                    )

            elif kind == "theme_system":
                painter.setBrush(accent_fill)
                painter.drawRoundedRect(QRectF(s * 0.14, s * 0.20, s * 0.72, s * 0.48), s * 0.08, s * 0.08)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.50, s * 0.68), QPointF(s * 0.50, s * 0.82))
                painter.drawLine(QPointF(s * 0.34, s * 0.82), QPointF(s * 0.66, s * 0.82))

            elif kind == "info":
                painter.setBrush(accent_fill)
                painter.drawEllipse(QRectF(s * 0.15, s * 0.15, s * 0.70, s * 0.70))
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.50, s * 0.46), QPointF(s * 0.50, s * 0.69))
                painter.setBrush(stroke_color)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawEllipse(QPointF(s * 0.50, s * 0.33), s * 0.05, s * 0.05)

            elif kind == "keyboard":
                painter.setBrush(accent_fill)
                painter.drawRoundedRect(QRectF(s * 0.12, s * 0.26, s * 0.76, s * 0.48), s * 0.08, s * 0.08)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                for kx in (0.28, 0.50, 0.72):
                    painter.drawLine(QPointF(s * (kx - 0.04), s * 0.42), QPointF(s * (kx + 0.04), s * 0.42))
                painter.drawLine(QPointF(s * 0.32, s * 0.58), QPointF(s * 0.68, s * 0.58))

            elif kind in ("backup", "save"):
                fl = QPainterPath()
                fl.moveTo(s * 0.18, s * 0.16)
                fl.lineTo(s * 0.70, s * 0.16)
                fl.lineTo(s * 0.84, s * 0.30)
                fl.lineTo(s * 0.84, s * 0.84)
                fl.lineTo(s * 0.18, s * 0.84)
                fl.closeSubpath()
                painter.setBrush(accent_fill)
                painter.drawPath(fl)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(QRectF(s * 0.31, s * 0.52, s * 0.38, s * 0.32), s * 0.04, s * 0.04)
                painter.drawRect(QRectF(s * 0.31, s * 0.16, s * 0.30, s * 0.20))

            elif kind == "clean":
                painter.drawLine(QPointF(s * 0.78, s * 0.18), QPointF(s * 0.46, s * 0.50))
                head = QPainterPath()
                head.moveTo(s * 0.36, s * 0.44)
                head.lineTo(s * 0.56, s * 0.64)
                head.lineTo(s * 0.34, s * 0.84)
                head.lineTo(s * 0.16, s * 0.66)
                head.closeSubpath()
                painter.setBrush(accent_fill)
                painter.drawPath(head)

            elif kind == "quit":
                painter.drawLine(QPointF(s * 0.50, s * 0.15), QPointF(s * 0.50, s * 0.48))
                arc = QPainterPath()
                arc.arcMoveTo(QRectF(s * 0.20, s * 0.22, s * 0.60, s * 0.60), 130)
                arc.arcTo(QRectF(s * 0.20, s * 0.22, s * 0.60, s * 0.60), 130, 280)
                painter.drawPath(arc)

            else:
                painter.setBrush(accent_fill)
                painter.drawRoundedRect(QRectF(s * 0.16, s * 0.24, s * 0.68, s * 0.52), s * 0.09, s * 0.09)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawLine(QPointF(s * 0.20, s * 0.28), QPointF(s * 0.50, s * 0.53))
                painter.drawLine(QPointF(s * 0.80, s * 0.28), QPointF(s * 0.50, s * 0.53))
        finally:
            painter.end()
        icon.addPixmap(pixmap)
    return icon


def tab_icon(kind: str, color_hex: str = "#334155", size: int = 20) -> object:
    """Returnera skarp, temafärgad vektorikon för flik, meny eller knapp."""
    from PyQt6.QtGui import QIcon

    return QIcon(_cached_vector_icon(str(kind or ""), str(color_hex or "#334155").lower(), max(12, int(size))))


def action_icon(kind: str, color_hex: str = "#334155", size: int = 18) -> object:
    """Returnera skarp vektorikon anpassad för knappar och menyval."""
    return tab_icon(kind, color_hex=color_hex, size=size)


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
    del mtime_ns, file_size
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
    "SUPPORTED_ICON_KINDS",
    "action_icon",
    "attachment_icon",
    "clear_vector_icon_caches",
    "color_swatch_icon",
    "tab_icon",
]
