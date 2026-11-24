#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för strikt branch-regel (aldrig main), skarp HiDPI (>DPI),
skärmanpassad layout/kolumner, minnesstyrning, hastighet och 25 nya förslag.
"""

from __future__ import annotations

import io
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest import mock
import zipfile

from core.error_log import ErrorLogCollector
from core.github_update import (
    UpdateInfo,
    apply_github_update,
    check_for_update,
    download_update_zip,
    is_forbidden_main_ref,
    is_forbidden_main_url,
    resolve_release_commit,
)
from core.signatures import _validate_logo_cached, preview_signature
from script.templates import _build_key_regex, _scan_cache, scan_templates_dir

ROOT = Path(__file__).resolve().parents[1]

try:
    from PyQt6.QtCore import QSize
    from PyQt6.QtWidgets import (
        QApplication,
        QComboBox,
        QDialog,
        QTableWidget,
        QTreeWidget,
        QVBoxLayout,
    )
    HAS_QT = True
except Exception:
    HAS_QT = False


class TestStrictNoMainBranchRule(unittest.TestCase):
    """Hård regel: appuppdateringar får aldrig hämta eller rikta mot main/master."""

    def test_forbidden_main_refs_detected(self) -> None:
        for forbidden in (
            "main",
            "MAIN",
            "master",
            "refs/heads/main",
            "refs/heads/master",
            "origin/main",
            "remotes/origin/main",
            "heads/main",
        ):
            self.assertTrue(is_forbidden_main_ref(forbidden), forbidden)

        for allowed in (
            "arena/447b9635-mailoffer",
            "release/v1.0.0",
            "f617a0f18acc3615bf1c87751af9aa3f286aa586",
            "v1.0.0",
            "domain-maintenance",
        ):
            self.assertFalse(is_forbidden_main_ref(allowed), allowed)

    def test_forbidden_main_urls_detected(self) -> None:
        bad_urls = (
            "https://api.github.com/repos/Tokke2/MailOffer/zipball/main",
            "https://api.github.com/repos/Tokke2/MailOffer/zipball/refs/heads/main",
            "https://github.com/Tokke2/MailOffer/archive/refs/heads/main.zip",
            "https://github.com/Tokke2/MailOffer/archive/main.zip",
            "https://raw.githubusercontent.com/Tokke2/MailOffer/main/core/version.py",
            "https://api.github.com/repos/Tokke2/MailOffer/contents/core/version.py?ref=main",
            "https://api.github.com/repos/Tokke2/MailOffer/commits/main",
        )
        for url in bad_urls:
            self.assertTrue(is_forbidden_main_url(url), url)

        good_urls = (
            "https://api.github.com/repos/Tokke2/MailOffer/releases/latest",
            "https://api.github.com/repos/Tokke2/MailOffer/git/ref/tags/v1.0.0",
            "https://api.github.com/repos/Tokke2/MailOffer/zipball/f617a0f18acc3615bf1c87751af9aa3f286aa586",
            "https://github.com/Tokke2/MailOffer/releases/download/v1.0.0/MailOffer-branch.zip",
        )
        for url in good_urls:
            self.assertFalse(is_forbidden_main_url(url), url)

    def test_download_and_apply_block_main_urls_and_refs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                download_update_zip(
                    "https://api.github.com/repos/Tokke2/MailOffer/zipball/main",
                    Path(tmp),
                    fetcher=lambda url, timeout: (200, b"PK"),
                )
            bad_info = UpdateInfo(
                available=True,
                latest_version="1.0.0",
                tag="v1.0.0",
                name="Release",
                download_url="https://github.com/Tokke2/MailOffer/archive/refs/heads/main.zip",
                html_url="https://github.com/Tokke2/MailOffer/releases/tag/v1.0.0",
                build_id="2026102399",
                commit_sha="main",
            )
            with self.assertRaises(ValueError):
                apply_github_update(
                    bad_info,
                    Path(tmp),
                    fetcher=lambda url, timeout: (200, b"PK"),
                )

    def test_unpinned_release_targeting_main_without_tag_ref_is_blocked(self) -> None:
        payload = {
            "tag_name": "v1.0.0",
            "target_commitish": "main",
            "zipball_url": "https://api.github.com/repos/Tokke2/MailOffer/zipball/main",
            "assets": [],
        }

        def fetch_failing_tag(url: str, timeout: float):
            if "/releases/latest" in url:
                return 200, json.dumps(payload).encode("utf-8")
            return 404, b"{}"

        with self.assertRaises(ValueError):
            resolve_release_commit("main", "Tokke2/MailOffer", fetch_failing_tag, 5.0)
        outcome = check_for_update(
            current_version="1.0.0",
            current_build_id="2026102300",
            repo="Tokke2/MailOffer",
            fetcher=fetch_failing_tag,
        )
        self.assertFalse(outcome.available)
        self.assertTrue(outcome.error)
        self.assertIn("main", outcome.error.lower())


class TestSharpnessMemoryAndProposals(unittest.TestCase):
    """Verifierar CSS/QSS-skärpa, begränsade cachar, loggeffektivitet och 25 nya förslag."""

    def test_styles_qss_has_single_crisp_header_and_unclipped_cells(self) -> None:
        source = (ROOT / "ui" / "styles.py").read_text(encoding="utf-8")
        self.assertEqual(
            source.count("QHeaderView::section {{"),
            1,
            "QHeaderView::section får inte överskrivas av en andra dubblettregel",
        )
        self.assertIn("border-right: 1px solid {c['border']};", source)
        self.assertIn("QTreeWidget::item, QTableWidget::item {{", source)
        self.assertIn("border-radius: 0px;", source)
        self.assertIn("PreferQuality", source)

    def test_main_window_has_negative_coord_geometry_and_step2_reflow(self) -> None:
        source = (ROOT / "ui" / "main_window.py").read_text(encoding="utf-8")
        self.assertNotIn("#729fff", source)
        self.assertIn("def _reflow_step2_attachments", source)
        self.assertIn("def _schedule_preview_refresh", source)
        m = re.compile(r"(\d+)x(\d+)(?:([+-]\d+)([+-]\d+))?")
        hit = m.fullmatch("1280x820-1920+40")
        self.assertIsNotNone(hit)
        assert hit is not None
        self.assertEqual((hit.group(1), hit.group(2), hit.group(3), hit.group(4)), ("1280", "820", "-1920", "+40"))

    def test_template_regex_and_scan_caches_are_bounded(self) -> None:
        _build_key_regex.cache_clear()
        p1 = _build_key_regex("regnummer")
        p2 = _build_key_regex("regnummer")
        self.assertIs(p1, p2)
        self.assertGreaterEqual(_build_key_regex.cache_info().hits, 1)
        self.assertEqual(_build_key_regex.cache_info().maxsize, 256)

        _scan_cache.clear()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            for idx in range(40):
                sub = base / f"dir_{idx}"
                sub.mkdir()
                (sub / "mall.txt").write_text("ÄMNE: Test\nINNEHÅLL:\nHej", encoding="utf-8")
                self.assertEqual(scan_templates_dir(sub), ["mall.txt"])
            self.assertLessEqual(len(_scan_cache), 32)

    def test_signature_logo_preview_uses_lru_cache_and_invalidates_on_change(self) -> None:
        _validate_logo_cached.cache_clear()
        # Minimal 1x1 PNG
        png_1x1 = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc`\x00\x00"
            b"\x00\x02\x00\x01\xe5'\xde\xfc\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        with tempfile.TemporaryDirectory() as tmp:
            logo = Path(tmp) / "logo.png"
            logo.write_bytes(png_1x1)
            profile = {
                "signature_text": "Med vänlig hälsning",
                "signature_contact": "Verkstad AB",
                "signature_logo": str(logo),
            }
            _, html1 = preview_signature("Hej", "<div>Hej</div>", profile)
            _, html2 = preview_signature("Hej igen", "<div>Hej igen</div>", profile)
            self.assertIn("file://", html1)
            self.assertIn("file://", html2)
            self.assertGreaterEqual(_validate_logo_cached.cache_info().hits, 1)
            self.assertEqual(_validate_logo_cached.cache_info().maxsize, 16)

    def test_error_collector_skips_idle_sqlite_writes_but_catches_new_and_truncated_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            collector = ErrorLogCollector(base, canonical_layout=True)
            app_log = base / "logs" / "app.log"
            app_log.write_text("2026-11-24 10:00:00 [INFO] Startad\n", encoding="utf-8")
            self.assertEqual(collector.collect(), 0)
            self.assertTrue(collector._history_verified)

            with mock.patch("core.open_errors.import_history") as mocked_hist:
                self.assertEqual(collector.collect(), 0)
                mocked_hist.assert_not_called()

            # Append real error -> must still be collected immediately
            with app_log.open("a", encoding="utf-8") as stream:
                stream.write("2026-11-24 10:01:00 [ERROR] SMTP timeout vid test\n")
            self.assertEqual(collector.collect(), 1)

            # Truncate & rewrite with a brand-new error -> prefix check detects truncation
            app_log.write_text("2026-11-24 10:02:00 [ERROR] Nytt fel efter trunkering\n", encoding="utf-8")
            self.assertEqual(collector.collect(), 1)

    def test_25_new_competitor_gap_proposals_documented(self) -> None:
        doc = (ROOT / "docs" / "25-produktforslag.md").read_text(encoding="utf-8")
        self.assertIn("## Omgång 2: 25 nya nischförslag", doc)
        part2 = doc.split("## Omgång 2: 25 nya nischförslag", 1)[1]
        numbered = [
            line for line in part2.splitlines()
            if re.match(r"^\|\s*\d+\s*\|", line)
        ]
        self.assertEqual(len(numbered), 25)


@unittest.skipUnless(HAS_QT, "PyQt6 krävs för HiDPI- och layouttester")
class TestHiDpiIconsQrAndScreenFit(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def test_vector_icons_and_thumbnails_support_multi_dpr(self) -> None:
        from ui.vector_icons import (
            DPR_LEVELS,
            attachment_icon,
            clear_vector_icon_caches,
            color_swatch_icon,
            tab_icon,
        )

        clear_vector_icon_caches()
        self.assertEqual(DPR_LEVELS, (1.0, 1.25, 1.5, 2.0, 3.0))
        icon = tab_icon("send", "#2563EB", size=20)
        px_1x = icon.pixmap(QSize(20, 20), 1.0)
        px_2x = icon.pixmap(QSize(20, 20), 2.0)
        self.assertFalse(px_1x.isNull())
        self.assertFalse(px_2x.isNull())
        self.assertGreaterEqual(px_2x.width(), 36)

        swatch = color_swatch_icon("#16A34A", "#334155", size=16)
        self.assertFalse(swatch.pixmap(QSize(16, 16), 2.0).isNull())

        with tempfile.TemporaryDirectory() as tmp:
            from PIL import Image

            big_img = Path(tmp) / "photo.png"
            Image.new("RGBA", (1600, 1200), (30, 120, 220, 255)).save(big_img)
            att = attachment_icon(big_img, size=28)
            thumb = att.pixmap(QSize(28, 28), 2.0)
            self.assertFalse(thumb.isNull())
            self.assertLessEqual(thumb.width(), 56)

    def test_swish_qr_scales_cleanly_at_high_dpr(self) -> None:
        import qrcode
        from ui.donate import build_swish_payload, swish_qr_pixmap, DEFAULT_SWISH_NUMBER

        payload = build_swish_payload(DEFAULT_SWISH_NUMBER, amount="50")
        qr = qrcode.QRCode(border=4, box_size=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
        qr.add_data(payload)
        qr.make(fit=True)
        modules = qr.modules_count + 8

        for ratio in (1.0, 1.5, 2.0):
            px = swish_qr_pixmap(payload, size=230, dpr=ratio)
            self.assertIsNotNone(px)
            assert px is not None
            self.assertEqual(px.width(), px.height())
            self.assertEqual(px.width() % modules, 0)
            self.assertAlmostEqual(px.devicePixelRatio(), ratio, places=2)

    def test_adapt_tables_trees_and_combos(self) -> None:
        from ui.screen_fit import adapt_combos, adapt_tables, adapt_trees

        dlg = QDialog()
        lay = QVBoxLayout(dlg)
        tbl = QTableWidget(1, 3)
        tree = QTreeWidget()
        tree.setColumnCount(3)
        combo = QComboBox()
        combo.addItem("Mycket långt alternativ som inte får spränga små skärmar")
        lay.addWidget(tbl)
        lay.addWidget(tree)
        lay.addWidget(combo)

        adapt_tables(dlg)
        adapt_trees(dlg)
        adapt_combos(dlg)

        self.assertTrue(tbl.alternatingRowColors())
        self.assertEqual(tbl.horizontalHeader().resizeContentsPrecision(), 200)
        self.assertTrue(tree.uniformRowHeights())
        self.assertTrue(tree.alternatingRowColors())
        self.assertEqual(tree.header().resizeContentsPrecision(), 200)
        self.assertTrue(combo.property("mailofferAdaptiveCombo"))


if __name__ == "__main__":
    unittest.main()
