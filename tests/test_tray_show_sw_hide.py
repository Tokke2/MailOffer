#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regressionstester för 'Visa fönster' i systemfältet (inkl. Win32 SW_HIDE / STARTUPINFO)."""

from __future__ import annotations

import ast
import logging
import os
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.window_focus import present_window


def _tray_method(name: str):
    tree = ast.parse((ROOT / "ui" / "tray.py").read_text(encoding="utf-8"))
    cls = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "SystemTray"
    )
    node = next(
        node
        for node in cls.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    )
    namespace = {"log": logging.getLogger("tray-sw-hide-test"), "tr": lambda key: key}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "tray-action", "exec"), namespace)
    return namespace[name]


def _load_save_window_geometry():
    tree = ast.parse((ROOT / "main.pyw").read_text(encoding="utf-8"))
    node = next(
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "save_window_geometry"
    )
    namespace = {"Any": object, "logging": logging}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "main-geo", "exec"), namespace)
    return namespace["save_window_geometry"]


class _RectStub:
    def __init__(self, x: int, y: int, w: int, h: int) -> None:
        self._x, self._y, self._w, self._h = x, y, w, h

    def x(self) -> int:
        return self._x

    def y(self) -> int:
        return self._y

    def width(self) -> int:
        return self._w

    def height(self) -> int:
        return self._h


class TrayShowAndGeometrySafetyTests(unittest.TestCase):
    def test_present_window_activates_non_qt_window_stub(self) -> None:
        calls: list[str] = []
        stub = types.SimpleNamespace(
            show=lambda: calls.append("show"),
            raise_=lambda: calls.append("raise"),
            activateWindow=lambda: calls.append("activate"),
        )
        present_window(stub)
        self.assertEqual(calls, ["show", "raise", "activate"])

    def test_tray_do_show_accepts_qaction_checked_bool_and_presents_window(self) -> None:
        calls: list[str] = []
        bus_events: list[tuple[str, dict]] = []
        win = types.SimpleNamespace(
            show=lambda: calls.append("show"),
            raise_=lambda: calls.append("raise"),
            activateWindow=lambda: calls.append("activate"),
        )
        bus = types.SimpleNamespace(
            publish=lambda evt, data: bus_events.append((evt, data))
        )
        tray = types.SimpleNamespace(_main_window=win, _bus=bus)
        # QAction.triggered emits a bool argument (checked=False)
        _tray_method("_do_show")(tray, False)
        self.assertEqual(calls, ["show", "raise", "activate"])
        self.assertEqual(bus_events, [("ui.window_shown", {})])

    def test_tray_do_show_avoids_duplicate_bus_event_for_main_window(self) -> None:
        bus_events: list[str] = []
        win = types.SimpleNamespace(
            _publishes_window_shown=True,
            show=lambda: bus_events.append("from_window"),
            raise_=lambda: None,
            activateWindow=lambda: None,
        )
        bus = types.SimpleNamespace(
            publish=lambda evt, _data: bus_events.append(f"from_tray:{evt}")
        )
        tray = types.SimpleNamespace(_main_window=win, _bus=bus)
        _tray_method("_do_show")(tray, False)
        self.assertEqual(bus_events, ["from_window"])

    def test_build_menu_keeps_strong_action_references_and_wires_visa_fonster(self) -> None:
        created: dict[str, mock.MagicMock] = {}
        menu = mock.MagicMock()

        def add_action(label: str):
            act = mock.MagicMock()
            created[label] = act
            return act

        menu.addAction.side_effect = add_action
        tray = types.SimpleNamespace(
            _menu=menu,
            _do_show=mock.MagicMock(),
            _do_hide=mock.MagicMock(),
            _do_open_settings=mock.MagicMock(),
            _do_check_updates=mock.MagicMock(),
            _do_test_smtp=mock.MagicMock(),
            _do_quit=mock.MagicMock(),
        )
        _tray_method("_build_menu")(tray)
        self.assertIn("👁️ Visa fönster", created)
        created["👁️ Visa fönster"].triggered.connect.assert_called_once_with(
            tray._do_show
        )
        self.assertEqual(len(tray._menu_actions), 6)

    def test_save_window_geometry_ignores_windows_minimized_minus_32000_and_formats_signs(self) -> None:
        save_geo = _load_save_window_geometry()
        saved: dict[str, str] = {}
        settings = types.SimpleNamespace(set=lambda k, v: saved.__setitem__(k, v))
        logger = logging.getLogger("geo-test")

        # 1. Minimized (-32000,-32000) without valid normalGeometry -> do NOT clobber
        iconic_win = types.SimpleNamespace(
            isMinimized=lambda: True,
            isMaximized=lambda: False,
            geometry=lambda: _RectStub(-32000, -32000, 160, 28),
            normalGeometry=lambda: _RectStub(-32000, -32000, 160, 28),
        )
        save_geo(settings, iconic_win, logger)
        self.assertNotIn("window_geometry", saved)

        # 2. Minimized with valid normalGeometry on left monitor (x = -1920, y = 40)
        left_mon_win = types.SimpleNamespace(
            isMinimized=lambda: True,
            isMaximized=lambda: False,
            geometry=lambda: _RectStub(-32000, -32000, 160, 28),
            normalGeometry=lambda: _RectStub(-1920, 40, 1280, 820),
        )
        save_geo(settings, left_mon_win, logger)
        self.assertEqual(saved.get("window_geometry"), "1280x820-1920+40")
        self.assertNotIn("+-", saved["window_geometry"])

    @unittest.skipUnless(os.name == "nt", "Kräver äkta Win32 STARTUPINFO / HWND")
    def test_win32_sw_hide_startup_tray_visa_fonster_makes_hwnd_visible(self) -> None:
        """Exakt reproduktion av Starta EmailApp.vbs (shell.Run ..., 0, True -> SW_HIDE).

        Utan explicit Win32 ShowWindow(SW_SHOWNORMAL/SW_RESTORE) lämnar Qt6:s första
        SW_SHOWDEFAULT fönstrets HWND osynligt (IsWindowVisible == 0) medan Qt sätter
        isVisible() == True, så att 'Visa fönster' i trayen aldrig visar fönstret.
        """
        script = r"""
import os
import sys
from pathlib import Path
from unittest import mock

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon

from core.event_bus import EventBus
from core.recovery_manager import RecoveryManager
from core.settings_manager import SettingsManager
from core.window_focus import win32_is_window_visible
from ui.main_window import MainWindow
from ui.tray import SystemTray

app = QApplication(sys.argv[:1])
tmp_dir = Path(sys.argv[1])
settings = SettingsManager(tmp_dir)
settings.update_from_dict({
    "auto_update_check": False,
    "language": "sv",
    "close_to_tray": True,
    "minimize_to_tray": True,
    "window_geometry": "1200x820+-32000+-32000",
})
bus = EventBus()
recovery = RecoveryManager(bus)

with mock.patch.object(QSystemTrayIcon, "isSystemTrayAvailable", return_value=True):
    win = MainWindow(settings, bus, recovery)
    # _restore_geo ska ha läkt trasig '+-32000+-32000'-geometri direkt
    assert abs(win.geometry().x()) < 16000, f"bad x: {win.geometry().x()}"
    assert abs(win.geometry().y()) < 16000, f"bad y: {win.geometry().y()}"

    tray = SystemTray(app=app, settings=settings, event_bus=bus, main_window=win)
    tray.setup()
    win.set_tray(tray)

    # Exakt som main.pyw: dölj innan fönstret någonsin visats
    win.hide()
    QTest.qWait(40)
    hwnd = int(win.winId())
    assert not win32_is_window_visible(hwnd), "HWND ska vara dolt före Visa fönster"

    # Trigga det faktiska menyvalet '👁️ Visa fönster' i QMenu
    show_actions = [a for a in tray._menu.actions() if "Visa fönster" in a.text()]
    assert len(show_actions) == 1, f"Hittade inte menyvalet: {[a.text() for a in tray._menu.actions()]}"
    show_actions[0].trigger()
    QTest.qWait(120)

    hwnd = int(win.winId())
    assert win.isVisible(), "Qt win.isVisible() måste vara True"
    assert not win.isMinimized(), "Fönstret får inte vara minimerat"
    assert win32_is_window_visible(hwnd), (
        f"Win32 IsWindowVisible({hwnd:#x}) var False efter 'Visa fönster' under SW_HIDE!"
    )

    # Dölj igen via tray-menyn och visa på nytt via vänsterklick (Trigger)
    hide_actions = [a for a in tray._menu.actions() if "Dölj fönster" in a.text()]
    assert len(hide_actions) == 1
    hide_actions[0].trigger()
    QTest.qWait(60)
    assert not win32_is_window_visible(int(win.winId())), "HWND ska döljas vid Dölj fönster"

    tray._on_activated(QSystemTrayIcon.ActivationReason.Trigger)
    QTest.qWait(120)
    assert win32_is_window_visible(int(win.winId())), (
        "Win32 IsWindowVisible var False vid klick på tray-ikonen!"
    )

    tray.shutdown()
    win.hide()
    win.deleteLater()
    QTest.qWait(20)
print("WIN32_SW_HIDE_TRAY_OK")
"""
        with tempfile.TemporaryDirectory() as tmp:
            env = {
                k: v
                for k, v in os.environ.items()
                if k.upper() != "QT_QPA_PLATFORM"
            }
            env["EMAILAPP_PORTABLE"] = "1"
            env["PYTHONIOENCODING"] = "utf-8"

            si = subprocess.STARTUPINFO()  # type: ignore[attr-defined]
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW  # type: ignore[attr-defined]
            si.wShowWindow = 0  # SW_HIDE – exakt som Starta EmailApp.vbs shell.Run(..., 0, True)

            proc = subprocess.run(
                [sys.executable, "-c", script, tmp],
                cwd=str(ROOT),
                env=env,
                startupinfo=si,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=45,
            )
            self.assertEqual(
                proc.returncode,
                0,
                f"Win32 SW_HIDE tray-test misslyckades:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
            )
            self.assertIn("WIN32_SW_HIDE_TRAY_OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
