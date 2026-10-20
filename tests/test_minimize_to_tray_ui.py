#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offscreen-tester: minimering till tray + återställning via show()."""

from __future__ import annotations

import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication

    HAS_QT = True
except Exception:  # pragma: no cover
    HAS_QT = False


def _fake_tray(visible: bool = True):
    icon = types.SimpleNamespace(isVisible=lambda: visible)
    return types.SimpleNamespace(_tray=icon)


@unittest.skipUnless(HAS_QT, "PyQt6 saknas – hoppar UI-tester")
class TestMinimizeToTray(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication(sys.argv[:1])
        try:
            from ui.main_window import MainWindow  # noqa: F401
        except Exception as exc:
            raise unittest.SkipTest(f"MainWindow otillgänglig: {exc}")

    def _make_window(self, **overrides):
        from core.event_bus import EventBus
        from core.recovery_manager import RecoveryManager
        from core.settings_manager import SettingsManager
        from ui.main_window import MainWindow

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        with mock.patch.dict(os.environ, {"EMAILAPP_PORTABLE": "1"}):
            settings = SettingsManager(Path(tmp.name))
        values = {
            "auto_update_check": False,
            "language": "sv",
            "close_to_tray": False,
            "minimize_to_tray": True,
        }
        values.update(overrides)
        settings.update_from_dict(values)
        bus = EventBus()
        win = MainWindow(settings, bus, RecoveryManager(bus))
        self.addCleanup(win.close)
        win.show()
        QTest.qWait(20)
        return win, settings

    def _minimize(self, win) -> None:
        win.showMinimized()
        QTest.qWait(60)  # låt WindowStateChange + singleShot(0) köra

    def test_minimize_hides_to_tray_when_enabled(self):
        win, _settings = self._make_window(minimize_to_tray=True)
        win._tray_ref = _fake_tray(True)
        self._minimize(win)
        self.assertFalse(win.isVisible(), "fönstret ska döljas till trayen")

        # Återställning via tray använder show() – ska avminimera
        win.show()
        QTest.qWait(20)
        self.assertTrue(win.isVisible())
        self.assertFalse(win.isMinimized())

    def test_minimize_stays_in_taskbar_when_disabled(self):
        win, _settings = self._make_window(minimize_to_tray=False)
        win._tray_ref = _fake_tray(True)
        self._minimize(win)
        self.assertTrue(win.isVisible())
        self.assertTrue(win.isMinimized())

    def test_minimize_without_tray_icon_stays_visible(self):
        win, _settings = self._make_window(minimize_to_tray=True)
        win._tray_ref = None
        self._minimize(win)
        self.assertTrue(win.isVisible())
        self.assertTrue(win.isMinimized())

        win2, _s2 = self._make_window(minimize_to_tray=True)
        win2._tray_ref = _fake_tray(False)  # ikonen finns men syns inte
        self._minimize(win2)
        self.assertTrue(win2.isVisible())
        self.assertTrue(win2.isMinimized())

    def test_settings_checkbox_exists_and_saves(self):
        win, settings = self._make_window(minimize_to_tray=False)
        settings.sync_autostart = lambda: True  # type: ignore[method-assign]
        checkbox = win._settings_widgets.get("minimize_to_tray")
        self.assertIsNotNone(checkbox)
        checkbox.setChecked(True)
        win._save_settings_form()
        self.assertTrue(bool(settings.get("minimize_to_tray")))


if __name__ == "__main__":
    unittest.main()
