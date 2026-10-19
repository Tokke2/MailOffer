#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för startkedjan + ikonen (5.4-uppföljning).

- Installera_Python.bat: 3.12, /silent-läge, snabbkoll om Python finns,
  den ENDA .bat-filen i projektet.
- Starta EmailApp.vbs: dolt fönster, kör .bat endast vid behov, startar
  main.pyw och skickar vidare argument (t.ex. --background).
- main.pyw:s Python-vakt (_python_supported) laddas via AST så Qt inte
  behövs (samma teknik som tests/test_main_v58_guards.py).
- Ikonerna finns med rätt format + transparenta hörn (Pillow-guardat).
"""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[1]


class TestInstallBat(unittest.TestCase):
    def setUp(self) -> None:
        self.bat = ROOT / "Installera_Python.bat"
        self.src = self.bat.read_text(encoding="utf-8", errors="replace")

    def test_only_one_bat_in_project(self):
        bats = [p.name for p in ROOT.glob("*.bat")]
        self.assertEqual(bats, ["Installera_Python.bat"])

    def test_old_bat_name_gone(self):
        self.assertFalse((ROOT / "Installera senaste Python.bat").exists())

    def test_pinned_python_312_everywhere(self):
        self.assertIn("Python.Python.3.12", self.src)            # winget-id
        self.assertIn(r"3\.12\.\d+", self.src)                   # python.org-regex
        self.assertIn("https://www.python.org/ftp/python/", self.src)
        self.assertIn("py -3.12", self.src)

    def test_silent_mode_and_fast_exit(self):
        self.assertIn("/silent", self.src)
        self.assertIn(":AlreadyOk", self.src)
        # pause får bara finnas i manuellt läge (efter SILENT-kollen)
        pause_at = self.src.rfind("pause")
        guard_at = self.src.rfind("if not defined SILENT")
        self.assertGreater(pause_at, guard_at)

    def test_quiet_installer_flags(self):
        self.assertIn("/quiet", self.src)
        self.assertIn("PrependPath=1", self.src)
        self.assertIn("Include_launcher=1", self.src)


class TestStartVbs(unittest.TestCase):
    def setUp(self) -> None:
        self.vbs = ROOT / "Starta EmailApp.vbs"
        self.src = self.vbs.read_text(encoding="utf-8", errors="replace")

    def test_runs_installer_hidden_and_waits(self):
        self.assertIn("Installera_Python.bat", self.src)
        self.assertIn("/silent", self.src)
        self.assertIn(", 0, True", self.src)  # 0 = dolt fönster, True = vänta

    def test_starts_main_pyw_hidden_with_args(self):
        self.assertIn("main.pyw", self.src)
        self.assertIn("WScript.Arguments", self.src)
        self.assertIn(", 0, False", self.src)

    def test_pythonw_search_prefers_312(self):
        self.assertIn("Python312", self.src)
        self.assertLess(self.src.index("Python312"), self.src.index("Python310"))

    def test_ascii_only_no_mojibake_risk(self):
        self.assertTrue(all(ord(ch) < 128 for ch in self.src))


class TestMainPythonGuard(unittest.TestCase):
    @staticmethod
    def _load() -> Dict[str, Any]:
        src = (ROOT / "main.pyw").read_text(encoding="utf-8")
        tree = ast.parse(src)
        keep = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "MIN_PYTHON_VERSION"
                for t in node.targets
            ):
                keep.append(node)
            elif isinstance(node, ast.FunctionDef) and node.name in (
                "_python_supported",
            ):
                keep.append(node)
        module = ast.Module(body=keep, type_ignores=[])
        ast.fix_missing_locations(module)
        namespace: Dict[str, Any] = {"Any": Any, "sys": sys}
        exec(compile(module, "main.pyw<python-guard>", "exec"), namespace)
        return namespace

    def test_minimum_is_310(self):
        self.assertEqual(self._load()["MIN_PYTHON_VERSION"], (3, 10))

    def test_supported_logic(self):
        ok = self._load()["_python_supported"]
        self.assertTrue(ok((3, 12, 10)))
        self.assertTrue(ok((3, 10, 0)))
        self.assertFalse(ok((3, 9, 7)))
        self.assertFalse(ok((2, 7, 18)))
        self.assertTrue(ok())  # testmiljön själv kör 3.10+

    def test_silent_launcher_uses_no_console(self):
        src = (ROOT / "main.pyw").read_text(encoding="utf-8")
        block = src.split("def _launch_python_installer_silent", 1)[1]
        block = block.split("def _safe_show_critical", 1)[0]
        self.assertIn("PYTHON_INSTALLER_BAT", block)
        self.assertIn('"/silent"', block)
        self.assertIn("CREATE_NO_WINDOW", block)
        self.assertIn("DEVNULL", block)


class TestIcons(unittest.TestCase):
    def test_files_exist_with_magic_bytes(self):
        png = (ROOT / "icons" / "app_icon.png").read_bytes()
        self.assertTrue(png.startswith(b"\x89PNG\r\n\x1a\n"))
        ico = (ROOT / "icons" / "app_icon.ico").read_bytes()
        self.assertTrue(ico.startswith(b"\x00\x00\x01\x00"))  # ICO-header
        tb = (ROOT / "thunderbird" / "icon.png").read_bytes()
        self.assertTrue(tb.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_transparent_corners_and_ico_sizes(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow saknas i testmiljön")
        master = Image.open(ROOT / "icons" / "app_icon.png")
        self.assertEqual(master.mode, "RGBA")
        self.assertEqual(master.getpixel((0, 0))[3], 0)  # genomskinligt hörn
        ico = Image.open(ROOT / "icons" / "app_icon.ico")
        sizes = set(ico.info.get("sizes", set()))
        self.assertTrue({(16, 16), (32, 32), (48, 48), (256, 256)} <= sizes)


if __name__ == "__main__":
    unittest.main()
