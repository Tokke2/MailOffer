#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för färdiga mallpaket."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from script.template_packs import (
    all_template_packs,
    install_template_items,
    install_template_pack,
    iter_template_pack_items,
    template_pack_item_by_id,
)
from script.templates import parse_subject_and_body, scan_templates_dir


class TestTemplatePacks(unittest.TestCase):
    def test_pack_catalog_covers_requested_kinds(self):
        ids = {item.item_id for item in iter_template_pack_items()}
        self.assertIn("reminder_quote", ids)
        self.assertIn("thanks_inquiry", ids)
        self.assertIn("seasonal_campaign", ids)
        self.assertIn("trades_quote", ids)
        self.assertGreaterEqual(len(all_template_packs()), 4)
        self.assertGreaterEqual(len(ids), 10)
        for item in iter_template_pack_items():
            self.assertTrue(item.subject.strip())
            self.assertTrue(item.body_sv.strip())
            self.assertTrue(item.body_en.strip())
            self.assertTrue(item.filename.endswith(".txt"))

    def test_install_selected_items_never_overwrites(self):
        with tempfile.TemporaryDirectory() as td:
            mallar = Path(td) / "Mallar"
            result = install_template_items(mallar, ["reminder_quote"])
            self.assertEqual(len(result.created), 1)
            created = result.created[0]
            created.write_text("användarändring", encoding="utf-8")

            second = install_template_items(mallar, ["reminder_quote"])
            self.assertEqual(second.created, [])
            self.assertEqual(second.skipped, [created.name])
            self.assertEqual(
                created.read_text(encoding="utf-8"), "användarändring"
            )

    def test_installed_template_has_swedish_and_english_versions(self):
        with tempfile.TemporaryDirectory() as td:
            mallar = Path(td) / "Mallar"
            result = install_template_pack(mallar, "cars_workshops")
            self.assertEqual(len(result.created), 3)
            item = template_pack_item_by_id("car_service_quote")
            path = mallar / item.filename
            _subject, sv_body = parse_subject_and_body(
                path,
                {"modell": "Volvo XC60"},
                include_english=False,
                keep_unknown=True,
            )
            _subject_en, en_body = parse_subject_and_body(
                path,
                {"modell": "Volvo XC60"},
                include_english=True,
                keep_unknown=True,
            )
            self.assertIn("Bilmodell", sv_body)
            self.assertIn("Car model", en_body)
            self.assertEqual(len(scan_templates_dir(mallar)), 3)


if __name__ == "__main__":
    unittest.main()
