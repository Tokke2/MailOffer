#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/wheel_guard.py – Muskjulsskydd för EmailApp (PyQt6)

Version: 1.0 – MUSHJULET SKROLLAR SIDAN, ÄNDRAR ALDRIG FÄLTVÄRDEN

Problem:
  - Muspekaren över en QComboBox → mushjulet byter val i dropdownen
  - Muspekaren över en QSpinBox/QSlider/QDial → mushjulet ändrar värdet
  - Muspekaren över en QLineEdit → mushjulet gör ingenting (sidan
    bakom skrollar inte heller)

Lösning (globalt event-filter på QApplication):
  - När mushjulet används över ett "värdekänsligt" fält konsumeras
    händelsen och skrollningen skickas i stället till närmaste
    skrollbara område (QScrollArea) – sidan skrollar alltid
  - Fältets värde ändras ALDRIG av mushjulet
  - Undantag: om en QComboBox-lista är öppen (popup) får mushjulet
    skrolla listan som vanligt
  - QScrollBar undantas (skrollar sig själv när musen är över den)
  - Textfält (QTextEdit/QPlainTextEdit), listor och träd skrollar sitt
    eget innehåll som vanligt

Installeras av main.pyw (steg 9.6) och MainWindow (idempotent).

FIL: ui/wheel_guard.py
"""

from __future__ import annotations

import logging
from typing import Optional

from PyQt6.QtCore import QEvent, QObject
from PyQt6.QtWidgets import (
    QAbstractScrollArea,
    QAbstractSlider,
    QAbstractSpinBox,
    QApplication,
    QComboBox,
    QDial,
    QLineEdit,
    QScrollBar,
)

log = logging.getLogger(__name__)

# Antal pixlar som skrollas per mussteg (40 px ≈ 3 rader text)
_WHEEL_STEP_PX = 40

_guard_instance: Optional[QObject] = None


class _WheelGuard(QObject):
    """Event-filter: musjul över värdekänsliga fält → skrolla sidan."""

    def eventFilter(self, obj: object, event: object) -> bool:  # noqa: N802 - Qt API
        if event.type() != QEvent.Type.Wheel:
            return False
        try:
            return self._handle_wheel(event)
        except Exception:
            log.debug("wheel_guard: fel vid hantering", exc_info=True)
            return False

    def _handle_wheel(self, event: object) -> bool:
        """Hantera musjulshändelse. True = konsumera (fältet ändras ej)."""
        widget = self._widget_under_cursor(event)
        if widget is None:
            return False

        # Öppen QComboBox-popup → låt Qt skrolla listan som vanligt
        if isinstance(widget, QComboBox):
            try:
                view = widget.view()
                if view is not None and view.isVisible():
                    return False
            except Exception:
                pass

        if not self._is_sensitive(widget):
            return False

        scroll_area = self._find_scroll_area(widget)
        if scroll_area is None:
            # Inget skrollbart område – konsumera ändå så att
            # fältvärdet ALDRIG ändras av mushjulet
            return True

        self._scroll_area(scroll_area, event)
        return True

    @staticmethod
    def _widget_under_cursor(event: object) -> Optional[object]:
        try:
            point = event.globalPosition().toPoint()
        except Exception:
            return None
        try:
            return QApplication.widgetAt(point)
        except Exception:
            return None

    @staticmethod
    def _is_sensitive(widget: object) -> bool:
        """Värdekänsliga fält – mushjul får aldrig ändra deras värde.

        Primärt klassnamnsbaserat (fungerar även om arv saknas i
        teststubbar) med isinstance som säkerhetsnät för riktig Qt.
        """
        name = type(widget).__name__
        if name in (
            "QComboBox",
            "QLineEdit",
            "QDial",
            "QSpinBox",
            "QDoubleSpinBox",
            "QDateTimeEdit",
            "QTimeEdit",
            "QDateEdit",
            "QSlider",
        ):
            return True
        try:
            # Fallback för riktig Qt (arvsbaserat)
            if isinstance(widget, QAbstractSpinBox):
                return True
            if isinstance(widget, QAbstractSlider) and not isinstance(
                widget, QScrollBar
            ):
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def _find_scroll_area(widget: object) -> Optional[QAbstractScrollArea]:
        """Närmaste QAbstractScrollArea bland föräldrarna (max 40 nivåer)."""
        current = widget
        for _ in range(40):
            try:
                current = current.parent()
            except Exception:
                return None
            if current is None:
                return None
            if isinstance(current, QAbstractScrollArea):
                return current
        return None

    @staticmethod
    def _scroll_area(scroll_area: QAbstractScrollArea, event: object) -> None:
        """Skrolla skrollområdet med samma riktning som mushjulet."""
        try:
            delta = event.angleDelta()
            delta_y = delta.y()
            delta_x = delta.x()
        except Exception:
            return

        if delta_y:
            vbar = scroll_area.verticalScrollBar()
            if vbar is not None:
                steps = delta_y // 120
                vbar.setValue(vbar.value() - steps * _WHEEL_STEP_PX)
                return
        if delta_x:
            hbar = scroll_area.horizontalScrollBar()
            if hbar is not None:
                steps = delta_x // 120
                hbar.setValue(hbar.value() - steps * _WHEEL_STEP_PX)


def install_wheel_guard(app: Optional[QApplication] = None) -> bool:
    """Installera muskjulsskyddet på applikationen (idempotent).

    Args:
        app: QApplication-instans (default: QApplication.instance())

    Returns:
        True om skyddet är installerat.
    """
    global _guard_instance
    if _guard_instance is not None:
        return True
    app = app or QApplication.instance()
    if app is None:
        return False
    _guard_instance = _WheelGuard(app)
    app.installEventFilter(_guard_instance)
    log.debug("Muskjulsskydd installerat (wheel guard v1.0).")
    return True


def wheel_guard_installed() -> bool:
    """True om skyddet redan är installerat."""
    return _guard_instance is not None


def reset_wheel_guard() -> None:
    """Rensa instansen (används i tester)."""
    global _guard_instance
    _guard_instance = None


__all__ = [
    "install_wheel_guard",
    "wheel_guard_installed",
    "reset_wheel_guard",
    "_WheelGuard",
    "_WHEEL_STEP_PX",
]
