#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enhetstester för core/i18n.py (sv/en-UI) – ren Python, ingen Qt."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.i18n import (  # noqa: E402
    STRINGS,
    get_language,
    missing_keys,
    normalize_language,
    set_language,
    tr,
)


class TestNormalizeLanguage(unittest.TestCase):
    def test_english_variants(self) -> None:
        for value in ("en", "EN", "en_GB", "en-US", "english", " English "):
            self.assertEqual(normalize_language(value), "en", value)

    def test_swedish_variants(self) -> None:
        for value in ("sv", "SV", "sv_SE", "svenska", "swedish"):
            self.assertEqual(normalize_language(value), "sv", value)

    def test_unknown_falls_back_to_swedish(self) -> None:
        for value in ("", None, "de", "fr", 123):
            self.assertEqual(normalize_language(value), "sv", repr(value))


class TestTranslate(unittest.TestCase):
    def tearDown(self) -> None:
        set_language("sv")

    def test_swedish_default(self) -> None:
        set_language("sv")
        self.assertEqual(tr("menu.file"), "Arkiv")
        self.assertEqual(get_language(), "sv")

    def test_english(self) -> None:
        set_language("en")
        self.assertEqual(tr("menu.file"), "File")
        self.assertEqual(tr("tab.templates"), "📝 Templates")
        self.assertEqual(get_language(), "en")

    def test_format_parameters(self) -> None:
        set_language("sv")
        self.assertEqual(
            tr("update.current_version", version="5.4.0"),
            "Installerad version: 5.4.0",
        )
        set_language("en")
        self.assertEqual(
            tr("wizard.filename.preview", filename="Bilglas.txt"),
            "File name: Bilglas.txt",
        )

    def test_missing_format_param_never_crashes(self) -> None:
        set_language("en")
        # {version} saknas -> råtexten tillbaka, inget undantag
        self.assertIn("{version}", tr("update.current_version"))

    def test_missing_key_returns_key(self) -> None:
        set_language("en")
        self.assertEqual(tr("finns.inte"), "finns.inte")

    def test_english_table_is_complete(self) -> None:
        self.assertEqual(missing_keys("en"), [])

    def test_no_extra_keys_in_english(self) -> None:
        self.assertEqual(set(STRINGS["en"]) - set(STRINGS["sv"]), set())

    def test_all_values_are_nonempty_strings(self) -> None:
        for lang, table in STRINGS.items():
            for key, value in table.items():
                self.assertIsInstance(value, str, f"{lang}:{key}")
                self.assertTrue(value.strip(), f"{lang}:{key} är tom")


if __name__ == "__main__":
    unittest.main()
