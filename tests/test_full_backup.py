#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för komplett säkerhetskopiering/återställning (core.user_backup)."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from core.user_backup import (
    create_full_backup,
    inspect_backup,
    restore_full_backup,
)


def _seed(base: Path, config_dir: Path) -> Path:
    (base / "adresslistor").mkdir(parents=True)
    (base / "adresslistor" / "contacts.json").write_text(
        '{"contacts": []}', encoding="utf-8"
    )
    (base / "Mallar").mkdir()
    (base / "Mallar" / "Offert.txt").write_text("Hej ::modell::", encoding="utf-8")
    (base / ".data").mkdir()
    (base / ".data" / "sent_history.json").write_text("[]", encoding="utf-8")
    settings = config_dir / "email_settings.json"
    settings.parent.mkdir(parents=True, exist_ok=True)
    settings.write_text(
        json.dumps(
            {
                "sender_email": "anna@exempel.se",
                "password": "hemligt-1",
                "sender_profiles": [
                    {"id": "a", "password": "hemligt-2", "smtp_server": "x"}
                ],
            }
        ),
        encoding="utf-8",
    )
    return settings


class TestFullBackup(unittest.TestCase):
    def test_create_redacts_passwords_and_roundtrip(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            base, config = root / "app", root / "config"
            base.mkdir()
            settings = _seed(base, config)
            dest = root / "backup.zip"

            summary = create_full_backup(base, settings, dest, app_version="1.1.0")
            self.assertGreaterEqual(summary["files"], 4)
            manifest = inspect_backup(dest)
            self.assertFalse(manifest["passwords_included"])
            self.assertEqual(manifest["app_version"], "1.1.0")

            with zipfile.ZipFile(dest) as archive:
                saved = json.loads(
                    archive.read("settings/email_settings.json").decode("utf-8")
                )
            self.assertEqual(saved["password"], "")
            self.assertEqual(saved["sender_profiles"][0]["password"], "")
            # Originalet ska vara orört
            original = json.loads(settings.read_text(encoding="utf-8"))
            self.assertEqual(original["password"], "hemligt-1")

            # Ändra data och återställ
            (base / "Mallar" / "Offert.txt").write_text(
                "ÄNDRAD", encoding="utf-8"
            )
            result = restore_full_backup(dest, base, settings)
            self.assertEqual(
                (base / "Mallar" / "Offert.txt").read_text(encoding="utf-8"),
                "Hej ::modell::",
            )
            self.assertTrue(result["safety_backup"].is_file())
            self.assertIn("settings", result["restored_sections"])

    def test_inspect_rejects_bad_files(self):
        with tempfile.TemporaryDirectory() as td:
            bogus = Path(td) / "x.zip"
            bogus.write_bytes(b"inte en zip")
            with self.assertRaises(ValueError):
                inspect_backup(bogus)
            with self.assertRaises(ValueError):
                inspect_backup(Path(td) / "saknas.zip")

    def test_restore_rejects_zip_slip_inside_section(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            evil = root / "evil.zip"
            with zipfile.ZipFile(evil, "w") as archive:
                archive.writestr(
                    "manifest.json",
                    json.dumps({"format": 1, "app": "E-postofferten"}),
                )
                archive.writestr("Mallar/../../evil.txt", "farligt")
            base = root / "app"
            base.mkdir()
            with self.assertRaises(ValueError):
                restore_full_backup(evil, base, root / "settings.json")
            self.assertFalse((root / "evil.txt").exists())


if __name__ == "__main__":
    unittest.main()
