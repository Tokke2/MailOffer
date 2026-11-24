#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för ui/wheel_guard.py v2.0:
Alla textfält och rullmenyer ignoreras vid skrollning om de ej är specifikt markerade.
"""

from __future__ import annotations

import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from ui.wheel_guard import (
    _WHEEL_STEP_PX,
    _WheelGuard,
    install_wheel_guard,
    reset_wheel_guard,
    wheel_guard_installed,
)

try:
    from PyQt6.QtCore import QEvent, QPoint, QPointF, Qt
    from PyQt6.QtGui import QWheelEvent
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QFrame,
        QLabel,
        QLineEdit,
        QPlainTextEdit,
        QScrollArea,
        QSpinBox,
        QTextBrowser,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
    from ui.clickable_combo import ClickableComboBox

    HAS_QT = True
except Exception:
    HAS_QT = False


# ── Lättviktsstubbar som körs även i miljöer utan libGL ──────────────────


class _StubBar:
    def __init__(self, value: int = 0, minimum: int = 0, maximum: int = 500) -> None:
        self._val = value
        self._min = minimum
        self._max = maximum

    def value(self) -> int:
        return self._val

    def minimum(self) -> int:
        return self._min

    def maximum(self) -> int:
        return self._max

    def setValue(self, v: int) -> None:
        self._val = max(self._min, min(self._max, int(v)))


class _StubDelta:
    def __init__(self, x: int = 0, y: int = 0) -> None:
        self._x = x
        self._y = y

    def x(self) -> int:
        return self._x

    def y(self) -> int:
        return self._y


class _StubWheelEvent:
    def __init__(self, dy: int = -120, dx: int = 0) -> None:
        self._angle = _StubDelta(dx, dy)
        self._pixel = _StubDelta(0, 0)

    def type(self):
        return QEvent.Type.Wheel if HAS_QT else 31

    def angleDelta(self) -> _StubDelta:
        return self._angle

    def pixelDelta(self) -> _StubDelta:
        return self._pixel


class _StubNode:
    def __init__(self, parent=None, *, focused: bool = False, enabled: bool = True) -> None:
        self._parent = parent
        self._focused = focused
        self._enabled = enabled

    def parent(self):
        return self._parent

    def hasFocus(self) -> bool:
        return self._focused

    def isEnabled(self) -> bool:
        return self._enabled


def _typed_stub(cls_name: str, parent=None, **kwargs):
    cls = type(cls_name, (_StubNode,), {})
    return cls(parent=parent, **kwargs)


class DummyScrollArea(_StubNode):
    def __init__(self, parent=None, *, value: int = 0, maximum: int = 500) -> None:
        super().__init__(parent=parent)
        self._vbar = _StubBar(value=value, maximum=maximum)
        self._hbar = _StubBar(value=0, maximum=200)

    def verticalScrollBar(self) -> _StubBar:
        return self._vbar

    def horizontalScrollBar(self) -> _StubBar:
        return self._hbar


class WheelGuardPureLogicTests(unittest.TestCase):
    def test_all_unmarked_text_fields_and_dropdowns_are_ignored_and_scroll_page(self) -> None:
        guard = _WheelGuard()
        for cls_name in (
            "QComboBox",
            "ClickableComboBox",
            "QLineEdit",
            "QTextEdit",
            "QPlainTextEdit",
            "QTextBrowser",
            "QSpinBox",
        ):
            with self.subTest(widget=cls_name):
                scroll = DummyScrollArea(value=100, maximum=600)
                card = _typed_stub("QFrame", parent=scroll)
                ctrl = _typed_stub(cls_name, parent=card, focused=False)
                viewport = _typed_stub("QWidget", parent=ctrl, focused=False)

                # Både direkt på kontrollen och på dess inre viewport/barn
                consumed_direct = guard._handle_wheel(ctrl, _StubWheelEvent(dy=-120))
                self.assertTrue(consumed_direct)
                self.assertEqual(scroll.verticalScrollBar().value(), 100 + _WHEEL_STEP_PX)

                consumed_child = guard._handle_wheel(viewport, _StubWheelEvent(dy=-120))
                self.assertTrue(consumed_child)
                self.assertEqual(scroll.verticalScrollBar().value(), 100 + 2 * _WHEEL_STEP_PX)

    def test_specifically_marked_text_fields_and_dropdowns_allow_native_scroll(self) -> None:
        guard = _WheelGuard()
        for cls_name in (
            "QComboBox",
            "ClickableComboBox",
            "QLineEdit",
            "QTextEdit",
            "QPlainTextEdit",
            "QTextBrowser",
            "QSpinBox",
        ):
            with self.subTest(widget=cls_name):
                scroll = DummyScrollArea(value=100, maximum=600)
                ctrl = _typed_stub(cls_name, parent=scroll, focused=True)
                consumed = guard._handle_wheel(ctrl, _StubWheelEvent(dy=-120))
                self.assertFalse(consumed, f"{cls_name} med fokus ska inte blockeras")
                self.assertEqual(scroll.verticalScrollBar().value(), 100)

    def test_clickable_combo_with_focused_inner_line_edit_or_open_popup_is_marked(self) -> None:
        guard = _WheelGuard()
        scroll = DummyScrollArea(value=50, maximum=400)
        combo = _typed_stub("ClickableComboBox", parent=scroll, focused=False)
        inner_le = _typed_stub("QLineEdit", parent=combo, focused=True)
        combo.lineEdit = lambda: inner_le  # type: ignore[attr-defined]
        combo.view = lambda: None  # type: ignore[attr-defined]

        # Inre lineEdit har fokus → rullmenyn räknas som specifikt markerad
        self.assertFalse(guard._handle_wheel(inner_le, _StubWheelEvent(dy=-120)))
        self.assertEqual(scroll.verticalScrollBar().value(), 50)

        # Utan fokus men med öppen popup-lista → specifikt markerad
        inner_le._focused = False
        popup = type("Popup", (), {"isVisible": lambda self: True})()
        combo.view = lambda: popup  # type: ignore[attr-defined]
        self.assertFalse(guard._handle_wheel(combo, _StubWheelEvent(dy=-120)))

        # Stängd popup och inget fokus → ignoreras, skrollar sidan
        popup_closed = type("Popup", (), {"isVisible": lambda self: False})()
        combo.view = lambda: popup_closed  # type: ignore[attr-defined]
        self.assertTrue(guard._handle_wheel(inner_le, _StubWheelEvent(dy=-120)))
        self.assertEqual(scroll.verticalScrollBar().value(), 50 + _WHEEL_STEP_PX)

    def test_nested_scroll_area_skips_non_scrollable_inner_container(self) -> None:
        guard = _WheelGuard()
        outer = DummyScrollArea(value=80, maximum=500)
        inner = DummyScrollArea(parent=outer, value=0, maximum=0)
        field = _typed_stub("QTextEdit", parent=inner, focused=False)

        self.assertTrue(guard._handle_wheel(field, _StubWheelEvent(dy=-120)))
        self.assertEqual(inner.verticalScrollBar().value(), 0)
        self.assertEqual(outer.verticalScrollBar().value(), 80 + _WHEEL_STEP_PX)

    def test_fractional_high_res_wheel_deltas_scroll_symmetrically(self) -> None:
        guard = _WheelGuard()
        scroll = DummyScrollArea(value=200, maximum=500)
        field = _typed_stub("QPlainTextEdit", parent=scroll, focused=False)

        guard._handle_wheel(field, _StubWheelEvent(dy=-30))
        after_down = scroll.verticalScrollBar().value()
        self.assertGreater(after_down, 200)

        guard._handle_wheel(field, _StubWheelEvent(dy=+30))
        after_up = scroll.verticalScrollBar().value()
        self.assertEqual(after_up, 200)


# ── Verkliga PyQt6-widgettester (körs i Windows CI 3.12 & 3.14) ──────────


@unittest.skipUnless(HAS_QT, "PyQt6.QtWidgets krävs för UI-hjulstester")
class WheelGuardQtUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        reset_wheel_guard()
        self.assertTrue(install_wheel_guard(self.app))
        self.assertTrue(wheel_guard_installed())

    def tearDown(self) -> None:
        reset_wheel_guard()

    @staticmethod
    def _send_wheel(target: QWidget, delta_y: int = -120) -> bool:
        center = target.rect().center()
        ev = QWheelEvent(
            QPointF(center),
            QPointF(target.mapToGlobal(center)),
            QPoint(0, 0),
            QPoint(0, delta_y),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.NoModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False,
        )
        return QApplication.sendEvent(target, ev)

    @staticmethod
    def _send_left_click(target: QWidget) -> None:
        QTest.mouseClick(target, Qt.MouseButton.LeftButton)

    def _build_scrollable_form(self):
        win = QWidget()
        win.resize(520, 320)
        root = QVBoxLayout(win)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        root.addWidget(scroll)

        page = QFrame()
        page_layout = QVBoxLayout(page)
        heading = QLabel("Formulärrubrik")
        page_layout.addWidget(heading)

        combo = QComboBox()
        combo.addItems(["Alternativ A", "Alternativ B", "Alternativ C"])
        page_layout.addWidget(combo)

        clickable = ClickableComboBox()
        clickable.addItems(["Vindruta", "Bakruta", "Sidoruta"])
        clickable.setEditable(True)
        page_layout.addWidget(clickable)

        line_edit = QLineEdit("JKH649")
        page_layout.addWidget(line_edit)

        text_edit = QTextEdit()
        text_edit.setFixedHeight(90)
        text_edit.setPlainText("\n".join(f"Rad {i}" for i in range(40)))
        page_layout.addWidget(text_edit)

        plain_edit = QPlainTextEdit()
        plain_edit.setFixedHeight(90)
        plain_edit.setPlainText("\n".join(f"Fritext {i}" for i in range(40)))
        page_layout.addWidget(plain_edit)

        browser = QTextBrowser()
        browser.setFixedHeight(90)
        browser.setPlainText("\n".join(f"Förhandsvisning {i}" for i in range(40)))
        page_layout.addWidget(browser)

        spin = QSpinBox()
        spin.setRange(0, 100)
        spin.setValue(25)
        page_layout.addWidget(spin)

        # Extra höjd så att sidans QScrollArea har ordentlig skrollmån
        spacer = QWidget()
        spacer.setMinimumHeight(900)
        page_layout.addWidget(spacer)

        scroll.setWidget(page)
        win.show()
        win.activateWindow()
        self.app.processEvents()
        # Säkerställ att ingenting är fokuserat från start
        fw = self.app.focusWidget()
        if fw is not None:
            fw.clearFocus()
        self.app.processEvents()
        return win, scroll, page, heading, combo, clickable, line_edit, text_edit, plain_edit, browser, spin

    def test_unmarked_dropdowns_and_text_fields_are_ignored_and_scroll_page(self) -> None:
        (
            win,
            scroll,
            _page,
            _heading,
            combo,
            clickable,
            line_edit,
            text_edit,
            plain_edit,
            browser,
            spin,
        ) = self._build_scrollable_form()
        try:
            vbar = scroll.verticalScrollBar()
            self.assertGreater(vbar.maximum(), 200)
            self.assertEqual(vbar.value(), 0)

            # 1. Omarkerad QComboBox → ändrar ej val, skrollar sidan
            self._send_wheel(combo, -120)
            self.assertEqual(combo.currentIndex(), 0)
            self.assertFalse(combo.hasFocus())
            self.assertEqual(vbar.value(), _WHEEL_STEP_PX)

            # 2. Omarkerad ClickableComboBox (både ramen och dess inre QLineEdit)
            self._send_wheel(clickable, -120)
            self._send_wheel(clickable.lineEdit(), -120)
            self.assertEqual(clickable.currentText(), "Vindruta")
            self.assertFalse(clickable.hasFocus())
            self.assertFalse(clickable.lineEdit().hasFocus())
            self.assertEqual(vbar.value(), 3 * _WHEEL_STEP_PX)

            # 3. Omarkerad QLineEdit → skrollar sidan
            self._send_wheel(line_edit, -120)
            self.assertEqual(line_edit.text(), "JKH649")
            self.assertEqual(vbar.value(), 4 * _WHEEL_STEP_PX)

            # 4. Omarkerade flerradiga textfält (QTextEdit, QPlainTextEdit, QTextBrowser)
            #    → fältets egen skrollbar rör sig EJ, sidan skrollar!
            for tf in (text_edit, plain_edit, browser):
                before = vbar.value()
                self._send_wheel(tf.viewport(), -120)
                self.assertEqual(tf.verticalScrollBar().value(), 0)
                self.assertFalse(tf.hasFocus())
                self.assertEqual(vbar.value(), before + _WHEEL_STEP_PX)

            # 5. Omarkerad QSpinBox → värdet 25 oförändrat, sidan skrollar
            before = vbar.value()
            self._send_wheel(spin, -120)
            self.assertEqual(spin.value(), 25)
            self.assertEqual(vbar.value(), before + _WHEEL_STEP_PX)
        finally:
            win.close()

    def test_marked_text_field_and_dropdown_respond_until_unmarked_by_outside_click(self) -> None:
        (
            win,
            scroll,
            page,
            heading,
            combo,
            clickable,
            _line_edit,
            text_edit,
            plain_edit,
            _browser,
            _spin,
        ) = self._build_scrollable_form()
        try:
            vbar = scroll.verticalScrollBar()
            vbar.setValue(0)

            # Markera QTextEdit explicit → nu skrollar textfältet sitt eget innehåll
            text_edit.setFocus()
            self.app.processEvents()
            self.assertTrue(text_edit.hasFocus())
            self._send_wheel(text_edit.viewport(), -120)
            self.assertGreater(text_edit.verticalScrollBar().value(), 0)
            self.assertEqual(vbar.value(), 0)

            # Klicka utanför på passiv rubrik/kort → avmarkerar QTextEdit
            self._send_left_click(heading)
            self.app.processEvents()
            self.assertFalse(text_edit.hasFocus())

            # Nästa skroll över QTextEdit ignorerar textfältet och skrollar sidan
            saved_tf_pos = text_edit.verticalScrollBar().value()
            self._send_wheel(text_edit.viewport(), -120)
            self.assertEqual(text_edit.verticalScrollBar().value(), saved_tf_pos)
            self.assertEqual(vbar.value(), _WHEEL_STEP_PX)

            # Markera QPlainTextEdit → skrollar sitt eget innehåll
            plain_edit.setFocus()
            self.app.processEvents()
            self.assertTrue(plain_edit.hasFocus())
            self._send_wheel(plain_edit.viewport(), -120)
            self.assertGreater(plain_edit.verticalScrollBar().value(), 0)

            # Klicka på kortbakgrunden (page) → avmarkerar QPlainTextEdit
            self._send_left_click(page)
            self.app.processEvents()
            self.assertFalse(plain_edit.hasFocus())

            # Markera QComboBox explicit → mushjulet får nu ändra val i rullmenyn
            combo.setFocus()
            self.app.processEvents()
            self.assertTrue(combo.hasFocus())
            self._send_wheel(combo, -120)
            self.assertGreater(combo.currentIndex(), 0)

            # Klicka på passiv bakgrund → avmarkerar QComboBox, skroll ändrar ej längre val
            chosen_idx = combo.currentIndex()
            self._send_left_click(heading)
            self.app.processEvents()
            self.assertFalse(combo.hasFocus())
            before_page = vbar.value()
            self._send_wheel(combo, -120)
            self.assertEqual(combo.currentIndex(), chosen_idx)
            self.assertEqual(vbar.value(), before_page + _WHEEL_STEP_PX)

            # Markera ClickableComboBox via inre lineEdit → räknas som markerad
            clickable.lineEdit().setFocus()
            self.app.processEvents()
            self.assertTrue(clickable.lineEdit().hasFocus())
            self._send_wheel(clickable, -120)
            self.assertNotEqual(clickable.currentIndex(), 0)
        finally:
            win.close()

    def test_standalone_unmarked_text_field_ignores_scroll_until_marked(self) -> None:
        win = QWidget()
        win.resize(340, 160)
        lay = QVBoxLayout(win)
        editor = QPlainTextEdit()
        editor.setPlainText("\n".join(f"Loggrad {i}" for i in range(60)))
        lay.addWidget(editor)
        win.show()
        win.activateWindow()
        self.app.processEvents()
        editor.clearFocus()
        self.app.processEvents()
        try:
            self.assertFalse(editor.hasFocus())
            self._send_wheel(editor.viewport(), -120)
            self.assertEqual(editor.verticalScrollBar().value(), 0)

            editor.setFocus()
            self.app.processEvents()
            self.assertTrue(editor.hasFocus())
            self._send_wheel(editor.viewport(), -120)
            self.assertGreater(editor.verticalScrollBar().value(), 0)
        finally:
            win.close()


if __name__ == "__main__":
    unittest.main()
