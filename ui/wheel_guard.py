#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ui/wheel_guard.py – Mushjulsskydd för EmailApp (PyQt6)

Version: 2.0 – IGNORERA ALLA TEXTFÄLT OCH RULLMENYER VID SKROLLNING
               OM DE EJ ÄR SPECIFIKT MARKERADE

Beteende:
  - Alla rullmenyer (QComboBox, ClickableComboBox m.fl.), alla textfält
    (QLineEdit, QTextEdit, QPlainTextEdit, QTextBrowser) samt övriga
    värdekänsliga inmatningsfält (QSpinBox, QDoubleSpinBox, QDateEdit,
    QTimeEdit, QDateTimeEdit, QSlider, QDial) ignoreras vid mushjulsskroll
    så länge de INTE är specifikt markerade (har fokus eller öppen popup).
  - När ett sådant omarkerat fält skrollas över skickas skrollningen vidare
    till närmaste skrollbara sidbehållare (QScrollArea) så att sidan rullar
    vidare utan att fastna i textfält eller råka ändra rullmenyval.
  - När användaren specifikt markerar ett textfält eller en rullmeny
    (genom klick/fokus eller genom att öppna rullmenyns lista) fungerar
    skrollning i det markerade fältet/listan som vanligt.
  - Vänsterklick på passiv sidbakgrund (kort, etikett utan länk/buddy,
    skrollyta) avmarkerar fokuserat textfält/rullmeny, och pågående
    sidskroll utanför ett markerat fält hindrar fältet från att kapa
    skrollningen när det glider in under muspekaren.

Installeras av main.pyw (steg 9.6) och MainWindow (idempotent).

FIL: ui/wheel_guard.py
"""

from __future__ import annotations

import logging
import time
from typing import Optional

try:
    from PyQt6.QtCore import QEvent, QObject, Qt
    from PyQt6.QtGui import QWindow
    from PyQt6.QtWidgets import (
        QAbstractButton,
        QAbstractItemView,
        QAbstractScrollArea,
        QAbstractSlider,
        QAbstractSpinBox,
        QApplication,
        QComboBox,
        QDial,
        QFrame,
        QGroupBox,
        QLabel,
        QLineEdit,
        QMenu,
        QMenuBar,
        QPlainTextEdit,
        QScrollArea,
        QScrollBar,
        QTabBar,
        QTextBrowser,
        QTextEdit,
        QToolBar,
        QWidget,
    )

    HAS_QT = True
except Exception:  # pragma: no cover - miljö utan libGL/QtWidgets
    HAS_QT = False
    QObject = object  # type: ignore[misc,assignment]
    QEvent = None  # type: ignore[assignment]
    Qt = None  # type: ignore[assignment]
    QWindow = ()  # type: ignore[assignment]
    QAbstractScrollArea = ()  # type: ignore[assignment]
    QApplication = None  # type: ignore[assignment]

log = logging.getLogger(__name__)

# Antal pixlar som skrollas per standardsteg (120 angleDelta ≈ 40 px)
_WHEEL_STEP_PX = 40

# Tidsfönster (sekunder) under vilket en aktiv sidskroll som startats utanför
# ett fokuserat fält inte kapas om fältet glider in under muspekaren.
_PAGE_SCROLL_GRACE_S = 0.35

_GUARDED_CLASS_NAMES = frozenset(
    {
        "QComboBox",
        "ClickableComboBox",
        "QLineEdit",
        "QTextEdit",
        "QPlainTextEdit",
        "QTextBrowser",
        "QDial",
        "QSpinBox",
        "QDoubleSpinBox",
        "QDateTimeEdit",
        "QTimeEdit",
        "QDateEdit",
        "QSlider",
    }
)

_TEXT_FIELD_CLASS_NAMES = frozenset(
    {
        "QLineEdit",
        "QTextEdit",
        "QPlainTextEdit",
        "QTextBrowser",
    }
)

_guard_instance: Optional[object] = None


class _WheelGuard(QObject):  # type: ignore[misc]
    """Globalt event-filter: ignorera omarkerade textfält & rullmenyer vid skroll."""

    def __init__(self, parent: Optional[object] = None) -> None:
        if HAS_QT:
            super().__init__(parent)  # type: ignore[arg-type]
        self._page_scroll_until: float = 0.0

    def eventFilter(self, obj: object, event: object) -> bool:  # noqa: N802 - Qt API
        if event is None:
            return False
        try:
            etype = event.type()
        except Exception:
            return False

        if HAS_QT:
            wheel_type = QEvent.Type.Wheel
            press_type = QEvent.Type.MouseButtonPress
        else:
            wheel_type = 31  # QEvent::Wheel
            press_type = 2   # QEvent::MouseButtonPress

        if etype == wheel_type:
            try:
                return self._handle_wheel(obj, event)
            except Exception:
                log.debug("wheel_guard: fel vid mushjulshantering", exc_info=True)
                return False

        if etype == press_type:
            try:
                return self._handle_mouse_press(obj, event)
            except Exception:
                log.debug("wheel_guard: fel vid klickhantering", exc_info=True)
                return False

        return False

    def _handle_wheel(self, obj: object, event: object) -> bool:
        """Hantera mushjulshändelse. True = konsumera (fältet ignoreras)."""
        # Hoppa över QWindow-nivån så att QWidgetWindow levererar till rätt QWidget.
        if HAS_QT and isinstance(obj, QWindow):
            return False

        target = obj if self._is_widget_like(obj) else self._widget_under_cursor(event)
        if target is None:
            return False

        control = self._resolve_guarded_widget(target)
        now = time.monotonic()

        if control is None:
            # Användaren skrollar direkt på sidan/listan utanför textfält/rullmeny.
            # Om ett skyddat fält råkar ha fokus i bakgrunden och pekaren är utanför
            # det fältet, markera att en sidskroll pågår så att fältet inte kapar
            # skrollningen när det rullar in under muspekaren.
            focused = self._focused_guarded_widget()
            if focused is not None and not self._cursor_inside_widget(focused, event):
                self._page_scroll_until = now + _PAGE_SCROLL_GRACE_S
            return False

        self._ensure_no_wheel_focus(control)

        # Är fältet/rullmenyn specifikt markerad (och inte överkörd av pågående sidskroll)?
        if self._is_specifically_selected(control, now=now):
            return False

        # Omarkerat textfält / omarkerad rullmeny (eller pågående sidskroll):
        # ignorera fältet och skrolla omgivande QScrollArea i stället.
        if now < self._page_scroll_until:
            self._page_scroll_until = now + _PAGE_SCROLL_GRACE_S

        scroll_area = self._find_scroll_area(control, event)
        if scroll_area is not None:
            self._scroll_area(scroll_area, event)
        return True

    def _handle_mouse_press(self, obj: object, event: object) -> bool:
        """Avmarkera fokuserat textfält/rullmeny vid vänsterklick på passiv bakgrund."""
        if HAS_QT and isinstance(obj, QWindow):
            return False

        self._page_scroll_until = 0.0

        try:
            button = event.button()
        except Exception:
            return False

        left_btn = Qt.MouseButton.LeftButton if HAS_QT else 1
        if button != left_btn:
            return False

        if not self._is_passive_background(obj):
            return False

        focused = self._focused_guarded_widget()
        if focused is None:
            return False

        try:
            if HAS_QT and isinstance(obj, QWidget) and isinstance(focused, QWidget):
                if obj.window() is not focused.window():
                    return False
            focus_leaf = QApplication.focusWidget() if (HAS_QT and QApplication is not None) else focused
            if focus_leaf is not None:
                focus_leaf.clearFocus()
            focused.clearFocus()
        except Exception:
            pass
        return False

    @staticmethod
    def _is_widget_like(obj: object) -> bool:
        if obj is None:
            return False
        if HAS_QT and isinstance(obj, QWidget):
            return True
        return type(obj).__name__ in _GUARDED_CLASS_NAMES or hasattr(obj, "parent")

    @staticmethod
    def _widget_under_cursor(event: object) -> Optional[object]:
        if QApplication is None:
            return None
        try:
            point = event.globalPosition().toPoint()
        except Exception:
            return None
        try:
            return QApplication.widgetAt(point)
        except Exception:
            return None

    @classmethod
    def _is_sensitive(cls, widget: object) -> bool:
        """True för alla rullmenyer, textfält och värdekänsliga inmatningsfält."""
        if widget is None:
            return False
        name = type(widget).__name__
        if name in _GUARDED_CLASS_NAMES:
            return True
        if not HAS_QT:
            return False
        try:
            if isinstance(
                widget,
                (
                    QComboBox,
                    QLineEdit,
                    QTextEdit,
                    QPlainTextEdit,
                    QTextBrowser,
                    QAbstractSpinBox,
                    QDial,
                ),
            ):
                return True
            if isinstance(widget, QAbstractSlider) and not isinstance(
                widget, QScrollBar
            ):
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def _is_text_scroll_widget(widget: object) -> bool:
        """True om widgeten själv är ett flerradigt textfält (ej sidans QScrollArea)."""
        if widget is None:
            return False
        if type(widget).__name__ in _TEXT_FIELD_CLASS_NAMES:
            return True
        if HAS_QT:
            try:
                return isinstance(widget, (QTextEdit, QPlainTextEdit, QTextBrowser))
            except Exception:
                return False
        return False

    @staticmethod
    def _is_page_scroll_container(widget: object) -> bool:
        """True för en yttre skrollbehållare (QScrollArea) men INTE ett textfält."""
        if widget is None:
            return False
        if type(widget).__name__ in ("QScrollArea", "DummyScrollArea"):
            return True
        if HAS_QT:
            try:
                if isinstance(widget, QScrollArea):
                    return True
                if isinstance(widget, QAbstractScrollArea) and not isinstance(
                    widget, (QTextEdit, QPlainTextEdit, QTextBrowser, QAbstractItemView)
                ):
                    return True
            except Exception:
                return False
        return False

    @classmethod
    def _resolve_guarded_widget(cls, widget: object) -> Optional[object]:
        """Hitta yttersta skyddade kontroll (t.ex. ClickableComboBox eller QTextEdit
        när händelsen träffar dess inre lineEdit() eller viewport()).
        """
        current = widget
        found: Optional[object] = None
        for _ in range(8):
            if current is None:
                break
            if cls._is_page_scroll_container(current):
                break
            if cls._is_sensitive(current):
                found = current
            try:
                parent = current.parent()
            except Exception:
                break
            if parent is current:
                break
            current = parent
        return found

    @staticmethod
    def _is_combo_popup_open(control: object) -> bool:
        is_combo = type(control).__name__ in ("QComboBox", "ClickableComboBox")
        if HAS_QT and not is_combo:
            try:
                is_combo = isinstance(control, QComboBox)
            except Exception:
                is_combo = False
        if not is_combo:
            return False
        try:
            view = control.view()  # type: ignore[attr-defined]
            return bool(view is not None and view.isVisible())
        except Exception:
            return False

    def _is_specifically_selected(
        self, control: object, *, now: Optional[float] = None
    ) -> bool:
        """True endast om fältet/rullmenyn är specifikt markerad av användaren."""
        try:
            if hasattr(control, "isEnabled") and not control.isEnabled():  # type: ignore[attr-defined]
                return False
        except Exception:
            return False

        # Öppen rullmenylista är alltid explicit öppnad av användaren.
        if self._is_combo_popup_open(control):
            return True

        ts = time.monotonic() if now is None else now
        if ts < self._page_scroll_until:
            return False

        try:
            if hasattr(control, "hasFocus") and control.hasFocus():  # type: ignore[attr-defined]
                return True
        except Exception:
            pass

        # Sammansatta kontroller: redigerbar QComboBox/ClickableComboBox, QSpinBox, QTextEdit
        for sub_attr in ("lineEdit", "viewport"):
            try:
                getter = getattr(control, sub_attr, None)
                sub = getter() if callable(getter) else None
                if sub is not None and hasattr(sub, "hasFocus") and sub.hasFocus():
                    return True
            except Exception:
                pass

        return False

    @staticmethod
    def _ensure_no_wheel_focus(control: object) -> None:
        """Förhindra att Qt ger fokus automatiskt enbart av mushjulet (WheelFocus)."""
        if not HAS_QT:
            return
        targets = [control]
        try:
            getter = getattr(control, "lineEdit", None)
            sub = getter() if callable(getter) else None
            if sub is not None:
                targets.append(sub)
        except Exception:
            pass
        for item in targets:
            try:
                if (
                    isinstance(item, QWidget)
                    and item.focusPolicy() == Qt.FocusPolicy.WheelFocus
                ):
                    item.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            except Exception:
                pass

    @classmethod
    def _focused_guarded_widget(cls) -> Optional[object]:
        if not HAS_QT or QApplication is None:
            return None
        try:
            fw = QApplication.focusWidget()
        except Exception:
            return None
        if fw is None:
            return None
        return cls._resolve_guarded_widget(fw)

    @staticmethod
    def _cursor_inside_widget(widget: object, event: object) -> bool:
        if not HAS_QT or not isinstance(widget, QWidget):
            return False
        try:
            gpos = event.globalPosition().toPoint()  # type: ignore[attr-defined]
            local = widget.mapFromGlobal(gpos)
            return bool(widget.rect().contains(local))
        except Exception:
            return False

    @classmethod
    def _is_passive_background(cls, obj: object) -> bool:
        """True om klicket skedde på passiv bakgrund (kort/ram/etikett/skrollyta)."""
        if obj is None:
            return False
        if not HAS_QT:
            return type(obj).__name__ in ("QFrame", "QWidget", "QScrollArea", "DummyBackground")
        if not isinstance(obj, QWidget):
            return False

        current: Optional[QWidget] = obj
        for _ in range(8):
            if current is None:
                break
            if isinstance(current, QScrollArea):
                return True
            if cls._is_sensitive(current):
                return False
            if isinstance(
                current,
                (
                    QAbstractButton,
                    QAbstractItemView,
                    QScrollBar,
                    QTabBar,
                    QMenu,
                    QMenuBar,
                    QToolBar,
                ),
            ):
                return False
            if isinstance(current, QGroupBox) and current.isCheckable():
                return False
            if isinstance(current, QLabel):
                if current.buddy() is not None:
                    return False
                flags = current.textInteractionFlags()
                if flags & Qt.TextInteractionFlag.TextSelectableByMouse:
                    return False
                if "<a " in (current.text() or "").lower():
                    return False
            elif not isinstance(current, (QFrame, QGroupBox)):
                # Vanlig QWidget med aktivt ClickFocus behandlas som interaktiv kontroll
                if current.focusPolicy() & Qt.FocusPolicy.ClickFocus:
                    return False
            if current.isWindow():
                break
            current = current.parentWidget()
        return True

    @classmethod
    def _find_scroll_area(
        cls, widget: object, event: Optional[object] = None
    ) -> Optional[object]:
        """Hitta lämplig föräldra-QScrollArea ovanför `widget` (max 40 nivåer).

        Om nästlade skrollområden finns väljs i första hand det innersta som
        faktiskt kan skrolla vidare i mushjulets riktning, annars det närmaste.
        """
        delta_y, delta_x = cls._extract_deltas(event)
        current = widget
        fallback: Optional[object] = None
        for _ in range(40):
            try:
                current = current.parent()  # type: ignore[attr-defined]
            except Exception:
                break
            if current is None:
                break
            if cls._is_text_scroll_widget(current):
                continue
            if cls._is_page_scroll_container(current) or (
                not HAS_QT and hasattr(current, "verticalScrollBar")
            ):
                if fallback is None:
                    fallback = current
                if cls._can_scroll_in_direction(current, delta_y, delta_x):
                    return current
        return fallback

    @staticmethod
    def _extract_deltas(event: Optional[object]) -> tuple[int, int]:
        if event is None:
            return (0, 0)
        try:
            delta = event.angleDelta()  # type: ignore[attr-defined]
            dy, dx = int(delta.y()), int(delta.x())
            if dy or dx:
                return (dy, dx)
        except Exception:
            pass
        try:
            pdelta = event.pixelDelta()  # type: ignore[attr-defined]
            return (int(pdelta.y()), int(pdelta.x()))
        except Exception:
            return (0, 0)

    @staticmethod
    def _can_scroll_in_direction(
        scroll_area: object, delta_y: int, delta_x: int
    ) -> bool:
        try:
            if delta_y != 0:
                vbar = scroll_area.verticalScrollBar()  # type: ignore[attr-defined]
                if vbar is not None:
                    val = vbar.value()
                    if delta_y < 0 and val < vbar.maximum():
                        return True
                    if delta_y > 0 and val > vbar.minimum():
                        return True
            if delta_x != 0:
                hbar = scroll_area.horizontalScrollBar()  # type: ignore[attr-defined]
                if hbar is not None:
                    val = hbar.value()
                    if delta_x < 0 and val < hbar.maximum():
                        return True
                    if delta_x > 0 and val > hbar.minimum():
                        return True
        except Exception:
            pass
        return False

    @classmethod
    def _scroll_pixels(cls, angle_delta: int) -> int:
        if angle_delta == 0:
            return 0
        px = round((angle_delta / 120.0) * _WHEEL_STEP_PX)
        if px == 0:
            return 1 if angle_delta > 0 else -1
        return px

    @classmethod
    def _scroll_area(cls, scroll_area: object, event: object) -> None:
        """Skrolla skrollområdet symmetriskt i mushjulets riktning."""
        angle_y = angle_x = 0
        pixel_y = pixel_x = 0
        try:
            delta = event.angleDelta()  # type: ignore[attr-defined]
            angle_y = int(delta.y())
            angle_x = int(delta.x())
        except Exception:
            pass
        if not angle_y and not angle_x:
            try:
                pdelta = event.pixelDelta()  # type: ignore[attr-defined]
                pixel_y = int(pdelta.y())
                pixel_x = int(pdelta.x())
            except Exception:
                return

        if angle_y or pixel_y:
            try:
                vbar = scroll_area.verticalScrollBar()  # type: ignore[attr-defined]
            except Exception:
                vbar = None
            if vbar is not None:
                step = cls._scroll_pixels(angle_y) if angle_y else pixel_y
                vbar.setValue(vbar.value() - step)
                return

        if angle_x or pixel_x:
            try:
                hbar = scroll_area.horizontalScrollBar()  # type: ignore[attr-defined]
            except Exception:
                hbar = None
            if hbar is not None:
                step = cls._scroll_pixels(angle_x) if angle_x else pixel_x
                hbar.setValue(hbar.value() - step)


def install_wheel_guard(app: Optional[object] = None) -> bool:
    """Installera mushjulsskyddet på applikationen (idempotent)."""
    global _guard_instance
    if _guard_instance is not None:
        return True
    if app is None and HAS_QT and QApplication is not None:
        app = QApplication.instance()
    if app is None:
        return False
    _guard_instance = _WheelGuard(app)
    app.installEventFilter(_guard_instance)  # type: ignore[attr-defined]
    log.debug("Mushjulsskydd installerat (wheel guard v2.0).")
    return True


def wheel_guard_installed() -> bool:
    """True om skyddet redan är installerat."""
    return _guard_instance is not None


def reset_wheel_guard() -> None:
    """Avregistrera och rensa instansen (används i tester)."""
    global _guard_instance
    if _guard_instance is not None and HAS_QT and QApplication is not None:
        try:
            app = QApplication.instance()
            if app is not None:
                app.removeEventFilter(_guard_instance)  # type: ignore[arg-type]
        except Exception:
            pass
    _guard_instance = None


__all__ = [
    "install_wheel_guard",
    "wheel_guard_installed",
    "reset_wheel_guard",
    "_WheelGuard",
    "_WHEEL_STEP_PX",
]
