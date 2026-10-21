#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för mallversioner: spara, lista, återställ och ångra."""

from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

from script.template_versions import (
    delete_template_version,
    list_template_versions,
    prune_template_versions,
    restore_template_version,
    snapshot_template_version,
)
from script.templates import scan_templates_dir


class TestTemplateVersions(unittest.TestCase):
    def _template(self, root: Path) -> Path:
        mallar = root / "Mallar"
        mallar.mkdir()
        template = mallar / "Offert.txt"
        template.write_text("version 1", encoding="utf-8")
        return template

    def test_snapshot_deduplicates_and_restore_can_be_undone(self):
        with tempfile.TemporaryDirectory() as td:
            template = self._template(Path(td))
            t0 = datetime(2026, 10, 21, 12, 0, 0)

            first = snapshot_template_version(template, now=t0)
            duplicate = snapshot_template_version(
                template, now=t0 + timedelta(seconds=1)
            )
            self.assertEqual(first, duplicate)
            self.assertEqual(len(list_template_versions(template)), 1)

            template.write_text("version 2", encoding="utf-8")
            restore_template_version(template, first)
            self.assertEqual(template.read_text(encoding="utf-8"), "version 1")

            versions = list_template_versions(template)
            self.assertGreaterEqual(len(versions), 2)
            undo = next(
                version
                for version in versions
                if version.path.read_text(encoding="utf-8") == "version 2"
            )
            restore_template_version(template, undo.path)
            self.assertEqual(template.read_text(encoding="utf-8"), "version 2")

            # Historiken ligger i en undermapp och syns inte som mallar.
            self.assertEqual(scan_templates_dir(template.parent), ["Offert.txt"])

    def test_restore_rejects_version_for_other_template(self):
        with tempfile.TemporaryDirectory() as td:
            template = self._template(Path(td))
            other = template.parent / "Annan.txt"
            other.write_text("annan", encoding="utf-8")
            version = snapshot_template_version(other)
            with self.assertRaises(ValueError):
                restore_template_version(template, version)

    def test_prune_and_delete(self):
        with tempfile.TemporaryDirectory() as td:
            template = self._template(Path(td))
            start = datetime(2026, 10, 21, 12, 0, 0)
            for index in range(4):
                template.write_text(f"innehåll {index}", encoding="utf-8")
                snapshot_template_version(
                    template, now=start + timedelta(minutes=index), keep=10
                )
            self.assertEqual(len(list_template_versions(template)), 4)
            prune_template_versions(template, keep=2)
            versions = list_template_versions(template)
            self.assertEqual(len(versions), 2)
            delete_template_version(template, versions[0].path)
            self.assertEqual(len(list_template_versions(template)), 1)


if __name__ == "__main__":
    unittest.main()
