#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enhetstester för v5.8: tema-knapp + öppna från historik (utan PyQt6-körning)."""
from __future__ import annotations

import ast
import py_compile
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "ui" / "main_window.py"

HELPER_NAMES = {
    "theme_button_caption",
    "history_selected_row",
    "history_open_feedback",
}


def load_helpers():
    src = MAIN.read_text(encoding="utf-8")
    tree = ast.parse(src)
    keep = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in HELPER_NAMES
    ]
    module = ast.Module(body=keep, type_ignores=[])
    ast.fix_missing_locations(module)
    ns: dict = {}
    exec(compile(module, str(MAIN), "exec"), ns)
    return ns


class TestThemeHistoryHelpers(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.h = load_helpers()

    def test_helpers_loaded(self) -> None:
        for name in HELPER_NAMES:
            self.assertIn(name, self.h)

    def test_theme_button_dark_shows_light(self) -> None:
        text, tip = self.h["theme_button_caption"]("dark")
        self.assertIn("Ljust", text)
        self.assertIn("☀️", text)
        self.assertIn("ljust", tip.lower())

    def test_theme_button_light_shows_dark(self) -> None:
        text, tip = self.h["theme_button_caption"]("light")
        self.assertIn("Mörkt", text)
        self.assertIn("🌙", text)
        self.assertIn("mörkt", tip.lower())

    def test_theme_button_empty_and_case(self) -> None:
        text, _tip = self.h["theme_button_caption"]("")
        self.assertIn("Mörkt", text)
        text2, _ = self.h["theme_button_caption"]("DARK")
        self.assertIn("Ljust", text2)

    def test_history_selected_row(self) -> None:
        fn = self.h["history_selected_row"]
        self.assertEqual(fn(0, 3), 0)
        self.assertEqual(fn(2, 3), 2)
        self.assertEqual(fn(-1, 3), -1)
        self.assertEqual(fn(3, 3), -1)
        self.assertEqual(fn(0, 0), -1)
        self.assertEqual(fn("1", 4), 1)
        self.assertEqual(fn("x", 4), -1)
        self.assertEqual(fn(None, 4), -1)

    def test_history_open_feedback_ok(self) -> None:
        msg, style = self.h["history_open_feedback"](True, "Mall", 0)
        self.assertEqual(style, "info")
        self.assertIn("Öppnad från historik", msg)

    def test_history_open_feedback_missing_template(self) -> None:
        msg, style = self.h["history_open_feedback"](False, "Saknas.txt", 0)
        self.assertEqual(style, "warning")
        self.assertIn("Saknas.txt", msg)

    def test_history_open_feedback_missing_attachments(self) -> None:
        msg, style = self.h["history_open_feedback"](True, "Mall", 2)
        self.assertEqual(style, "warning")
        self.assertIn("2", msg)

    def test_history_open_feedback_both(self) -> None:
        msg, style = self.h["history_open_feedback"](False, "X", 1)
        self.assertEqual(style, "warning")
        self.assertIn("X", msg)
        self.assertIn("1", msg)

    def test_source_has_theme_button_and_open(self) -> None:
        src = MAIN.read_text(encoding="utf-8")
        self.assertIn("btn_theme", src)
        self.assertIn("_on_theme_button_clicked", src)
        self.assertIn("StyleEngine.toggle", src)
        self.assertIn("✏️ Öppna / skicka om", src)
        self.assertIn("_open_selected_history", src)
        self.assertIn("_on_history_double_clicked", src)
        self.assertNotIn(
            "lambda item, column: self._open_history_for_edit(item.row())",
            src,
        )


class TestPyCompile(unittest.TestCase):
    def test_main_window_compiles(self) -> None:
        py_compile.compile(str(MAIN), doraise=True)

    def test_compile_in_temp(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            py_compile.compile(
                str(MAIN),
                cfile=str(Path(tmp) / "mw.pyc"),
                doraise=True,
            )


if __name__ == "__main__":
    unittest.main()
