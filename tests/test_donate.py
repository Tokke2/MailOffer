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


class TestPaypalAndResolve(unittest.TestCase):
    def test_bare_paypal_name(self):
        from core.donate import normalize_donation_url
        self.assertEqual(
            normalize_donation_url("Rickard3dPrint", "paypal"),
            "https://paypal.me/Rickard3dPrint",
        )
        self.assertEqual(
            normalize_donation_url("paypal.me/Rickard3dPrint", "paypal"),
            "https://paypal.me/Rickard3dPrint",
        )

    def test_invalid_input_falls_back_to_defaults(self):
        # Giltigheten är tjänsteagnostisk (http(s) + domän + profilstump)
        # så ägaren kan länka en egen donationssida – men en ren domän
        # utan profilstump är ogiltig och ger standardlänkarna.
        from core.donate import is_valid_donation_url, resolve_donation_links
        self.assertFalse(is_valid_donation_url("https://ko-fi.com/", "ko-fi"))
        self.assertFalse(is_valid_donation_url("", "paypal"))
        self.assertTrue(
            is_valid_donation_url("https://paypal.me/Rickard3dPrint", "paypal")
        )
        self.assertEqual(
            resolve_donation_links("ko-fi.com/", "paypal.me/"),
            ("https://ko-fi.com/tokke2", "https://paypal.me/Rickard3dPrint"),
        )

    def test_defaults_when_unconfigured(self):
        from core.donate import resolve_donation_links
        self.assertEqual(
            resolve_donation_links("", ""),
            ("https://ko-fi.com/tokke2", "https://paypal.me/Rickard3dPrint"),
        )

    def test_saved_value_wins_over_default(self):
        from core.donate import resolve_donation_links
        kofi, paypal = resolve_donation_links("mittnamn", "")
        self.assertEqual(kofi, "https://ko-fi.com/mittnamn")
        self.assertEqual(paypal, "https://paypal.me/Rickard3dPrint")


class TestSwish(unittest.TestCase):
    def test_normalize_variants(self):
        from core.donate import normalize_swish_number
        self.assertEqual(normalize_swish_number("+46 70 123 45 67"), "0701234567")
        self.assertEqual(normalize_swish_number("070-123 45 67"), "0701234567")
        self.assertEqual(normalize_swish_number("701234567"), "0701234567")
        self.assertEqual(normalize_swish_number("0046701234567"), "0701234567")
        self.assertEqual(normalize_swish_number("123 456 78 90"), "1234567890")
        self.assertEqual(normalize_swish_number(""), "")

    def test_validity(self):
        from core.donate import is_valid_swish_number
        self.assertTrue(is_valid_swish_number("0701234567"))
        self.assertTrue(is_valid_swish_number("0736123456"))
        self.assertTrue(is_valid_swish_number("1234567890"))
        self.assertFalse(is_valid_swish_number("08123456"))
        self.assertFalse(is_valid_swish_number("12345"))
        self.assertFalse(is_valid_swish_number(""))

    def test_format(self):
        from core.donate import format_swish_number
        self.assertEqual(format_swish_number("0701234567"), "070-123 45 67")
        self.assertEqual(format_swish_number("1234567890"), "123 456 78 90")

    def test_payload_defaults_open_amount(self):
        from core.donate import build_swish_payload
        self.assertEqual(
            build_swish_payload("070-123 45 67"),
            "C0701234567;;E-postofferten;6",
        )

    def test_payload_amount_decimal_comma(self):
        from core.donate import build_swish_payload
        self.assertEqual(
            build_swish_payload("1234567890", amount="49.5", message="Stöd"),
            "C1234567890;49,50;Stöd;6",
        )

    def test_payload_sanitizes_message_and_truncates(self):
        from core.donate import build_swish_payload
        payload = build_swish_payload(
            "0701234567", message="Hej;med\nseparator" + "x" * 60
        )
        parts = payload[1:].split(";")
        self.assertEqual(len(parts), 4)
        self.assertLessEqual(len(parts[2]), 50)
        self.assertNotIn("\n", payload)

    def test_payload_invalid_raises(self):
        from core.donate import build_swish_payload
        with self.assertRaises(ValueError):
            build_swish_payload("123")
        with self.assertRaises(ValueError):
            build_swish_payload("0701234567", amount="billigt")


if __name__ == "__main__":
    unittest.main()
