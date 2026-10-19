#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för core/donate.py (Ko-fi-länkens normalisering/validering)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.donate import (  # noqa: E402
    configured_donation_url,
    is_valid_donation_url,
    normalize_donation_url,
)


class TestNormalize(unittest.TestCase):
    def test_full_url_kept(self) -> None:
        self.assertEqual(
            normalize_donation_url("https://ko-fi.com/tokke"),
            "https://ko-fi.com/tokke",
        )

    def test_scheme_added(self) -> None:
        self.assertEqual(
            normalize_donation_url("ko-fi.com/tokke"),
            "https://ko-fi.com/tokke",
        )

    def test_bare_username_becomes_kofi(self) -> None:
        self.assertEqual(
            normalize_donation_url("tokke"), "https://ko-fi.com/tokke"
        )
        self.assertEqual(
            normalize_donation_url(" @tokke ".replace(" ", "")),
            "https://ko-fi.com/tokke",
        )

    def test_empty(self) -> None:
        self.assertEqual(normalize_donation_url(""), "")
        self.assertEqual(normalize_donation_url(None), "")
        self.assertEqual(normalize_donation_url("   "), "")


class TestValidate(unittest.TestCase):
    def test_valid_links(self) -> None:
        for url in ("https://ko-fi.com/tokke", "ko-fi.com/tokke", "tokke"):
            self.assertTrue(is_valid_donation_url(url), url)

    def test_invalid_links(self) -> None:
        for url in ("", "https://ko-fi.com/", "inte en länk alls", "http://x"):
            self.assertFalse(is_valid_donation_url(url), url)

    def test_configured_helper(self) -> None:
        self.assertEqual(
            configured_donation_url("tokke"), "https://ko-fi.com/tokke"
        )
        self.assertIsNone(configured_donation_url(""))
        self.assertIsNone(configured_donation_url("bara text här"))


if __name__ == "__main__":
    unittest.main()
