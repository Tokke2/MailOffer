#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för DNS-kontroller (SPF/DKIM/DMARC) med fejkad DoH-fetch."""

from __future__ import annotations

import json
import unittest
import urllib.parse

from core.dns_checks import check_domain, normalize_domain


def _payload(records):
    return json.dumps(
        {"Answer": [{"type": 16, "data": r} for r in records]}
    ).encode("utf-8")


def _fetcher(mapping):
    def fetch(url, timeout):
        name = urllib.parse.parse_qs(
            urllib.parse.urlparse(url).query
        )["name"][0]
        return 200, _payload(mapping.get(name, []))

    return fetch


class TestDnsChecks(unittest.TestCase):
    def test_normalize_domain(self):
        self.assertEqual(normalize_domain("EXEMPEL.se."), "exempel.se")
        self.assertEqual(normalize_domain("anna@Exempel.se"), "exempel.se")
        self.assertEqual(normalize_domain("inte en domän"), "")
        self.assertEqual(normalize_domain(""), "")

    def test_all_ok_and_chunked_txt(self):
        mapping = {
            "exempel.se": ['"v=spf1 include:_spf.google.com" " ~all"'],
            "_dmarc.exempel.se": ["v=DMARC1; p=reject; rua=mailto:d@exempel.se"],
            "google._domainkey.exempel.se": [
                "v=DKIM1; k=rsa; p=MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A"
            ],
        }
        report = check_domain("exempel.se", fetcher=_fetcher(mapping))
        self.assertEqual(report.spf_status, "ok")
        self.assertIn("~all", report.spf_record)
        self.assertEqual(report.dmarc_status, "ok")
        self.assertEqual(report.dmarc_policy, "reject")
        self.assertEqual(report.dkim_status, "ok")
        self.assertIn("google", report.dkim_selectors)
        self.assertEqual(report.ok_count, 3)

    def test_missing_records(self):
        report = check_domain("exempel.se", fetcher=_fetcher({}))
        self.assertEqual(report.spf_status, "missing")
        self.assertEqual(report.dmarc_status, "missing")
        self.assertEqual(report.dkim_status, "missing")

    def test_invalid_domain_and_network_error(self):
        report = check_domain("inte en domän", fetcher=_fetcher({}))
        self.assertEqual(report.spf_status, "error")
        self.assertTrue(report.error)

        def boom(url, timeout):
            raise OSError("nätet nere")

        report2 = check_domain("exempel.se", fetcher=boom)
        self.assertEqual(report2.spf_status, "error")
        self.assertIn("nätet nere", report2.error)


if __name__ == "__main__":
    unittest.main()
