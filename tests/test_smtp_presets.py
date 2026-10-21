#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för SMTP-leverantörsförval (ren logik)."""

from __future__ import annotations

import unittest

from core.smtp_presets import (
    all_presets,
    domain_from_email,
    preset_by_id,
    preset_for_email,
    preset_for_server,
)


class TestSmtpPresets(unittest.TestCase):
    def test_preset_values_sane(self):
        for preset in all_presets():
            self.assertTrue(preset.server)
            self.assertIn(preset.port, (465, 587))
            # 465 = implicit SSL, 587 = STARTTLS
            self.assertEqual(preset.use_ssl, preset.port == 465)

    def test_preset_for_email_domains(self):
        self.assertEqual(preset_for_email("anna@gmail.com").preset_id, "gmail")
        self.assertEqual(
            preset_for_email("anna@hotmail.com").preset_id, "outlook"
        )
        self.assertEqual(
            preset_for_email("anna@foretag.onmicrosoft.com").preset_id,
            "office365",
        )
        self.assertEqual(preset_for_email("anna@yahoo.se").preset_id, "yahoo")
        self.assertEqual(preset_for_email("anna@icloud.com").preset_id, "icloud")
        self.assertIsNone(preset_for_email("anna@exempel.se"))
        self.assertIsNone(preset_for_email("inte-en-adress"))

    def test_preset_for_server_and_id(self):
        self.assertEqual(
            preset_for_server("smtp.gmail.com").preset_id, "gmail"
        )
        self.assertIsNone(preset_for_server("mail.exempel.se"))
        self.assertEqual(preset_by_id("yahoo").port, 465)
        self.assertIsNone(preset_by_id("okand"))

    def test_domain_from_email(self):
        self.assertEqual(domain_from_email("Anna@Example.SE"), "example.se")
        self.assertEqual(domain_from_email(""), "")
        self.assertEqual(domain_from_email("a@b@c.se"), "")


if __name__ == "__main__":
    unittest.main()
