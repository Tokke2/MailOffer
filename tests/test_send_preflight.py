#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för förhandskontrollen före sändning (ren logik)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.send_preflight import build_send_preflight


def _profile(**overrides):
    profile = {
        "id": "standard",
        "name": "Standard",
        "smtp_server": "smtp.example.se",
        "smtp_port": 587,
        "sender_email": "anna@example.se",
        "sender_name": "Anna",
        "username": "anna@example.se",
        "password": "hemligt",
        "reply_to": "",
        "own_email": "egen@example.se",
        "archive_copy_email": "",
        "use_ssl": False,
    }
    profile.update(overrides)
    return profile


class TestBuildSendPreflight(unittest.TestCase):
    def test_final_recipients_overlap_languages_and_size(self):
        with tempfile.TemporaryDirectory() as td:
            attachment = Path(td) / "fil.txt"
            attachment.write_bytes(b"12345")
            report = build_send_preflight(
                {
                    "sender_profile": _profile(),
                    "recipients_to": ["a@example.se"],
                    "recipients_bcc": [
                        "a@example.se",
                        "b@example.com",
                        "ogiltig",
                    ],
                    "recipients_to_lang": {"a@example.se": "en"},
                    "recipients_bcc_lang": {"b@example.com": "sv"},
                    "default_bcc": ["arkiv@example.se"],
                    "attachments": [str(attachment)],
                    "subject": "Hej",
                    "template_path": "",
                }
            )
        self.assertTrue(report.ok)
        self.assertEqual(report.to_final, ["egen@example.se", "a@example.se"])
        self.assertEqual(
            report.bcc_final,
            ["b@example.com", "ogiltig", "arkiv@example.se"],
        )
        self.assertEqual(report.overlap, ["a@example.se"])
        self.assertEqual(report.invalid, ["ogiltig"])
        self.assertEqual(report.en_count, 1)
        self.assertEqual(report.attachment_bytes, 5)
        codes = [code for code, _values in report.warnings]
        self.assertIn("overlap", codes)
        self.assertIn("invalid_recipients_skipped", codes)

    def test_blockers_for_missing_smtp_sender_and_template(self):
        report = build_send_preflight(
            {
                "sender_profile": _profile(
                    smtp_server="",
                    smtp_port=70000,
                    sender_email="inte-epost",
                    own_email="",
                ),
                "recipients_to": [],
                "recipients_bcc": [],
                "template_path": "/finns/inte/mall.txt",
                "attachments": ["/finns/inte/bilaga.pdf"],
                "subject": "",
            },
            skip_invalid_recipients=False,
        )
        codes = [code for code, _values in report.blockers]
        self.assertFalse(report.ok)
        self.assertIn("no_recipients", codes)
        self.assertIn("missing_smtp_server", codes)
        self.assertIn("invalid_smtp_port", codes)
        self.assertIn("invalid_sender", codes)
        self.assertIn("missing_template", codes)
        self.assertIn("missing_attachments", codes)

    def test_test_mode_excludes_own_and_default_bcc(self):
        report = build_send_preflight(
            {
                "sender_profile": _profile(),
                "recipients_to": ["test@example.se"],
                "recipients_bcc": [],
                "default_bcc": ["arkiv@example.se"],
                "subject": "Test",
                "test_mode": True,
            }
        )
        self.assertEqual(report.to_final, ["test@example.se"])
        self.assertEqual(report.bcc_final, [])
        self.assertEqual(report.total, 1)


if __name__ == "__main__":
    unittest.main()
