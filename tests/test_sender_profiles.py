#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tester för avsändarprofiler (ren logik + SettingsManager)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.sender_profiles import (
    normalize_sender_profile,
    normalize_sender_profiles,
    profile_from_settings,
    slugify_profile_id,
)


class TestSenderProfileHelpers(unittest.TestCase):
    def test_slug_and_normalize_types(self):
        self.assertEqual(slugify_profile_id("Företag ÅÄÖ AB"), "foretag-aao-ab")
        profile = normalize_sender_profile(
            {
                "name": "Anna",
                "smtp_server": " smtp.example.se ",
                "smtp_port": "465",
                "sender_email": " anna@example.se ",
                "use_ssl": "true",
                "unknown": "ska bort",
            }
        )
        self.assertEqual(profile["id"], "anna")
        self.assertEqual(profile["smtp_port"], 465)
        self.assertTrue(profile["use_ssl"])
        self.assertNotIn("unknown", profile)

    def test_legacy_flat_settings_become_standard_profile(self):
        flat = {
            "smtp_server": "smtp.example.se",
            "smtp_port": 587,
            "sender_email": "anna@example.se",
            "sender_name": "Anna",
            "username": "anna@example.se",
            "password": "hemligt",
        }
        profiles, active = normalize_sender_profiles([], flat)
        self.assertEqual(active, "anna")
        self.assertEqual(profiles[0]["sender_email"], "anna@example.se")
        self.assertEqual(profile_from_settings(flat)["name"], "Anna")

    def test_duplicate_ids_are_made_unique(self):
        profiles, active = normalize_sender_profiles(
            [
                {"id": "samma", "name": "Ett", "sender_email": "a@example.se"},
                {"id": "samma", "name": "Två", "sender_email": "b@example.se"},
            ],
            {},
            "samma",
        )
        self.assertEqual(active, "samma")
        self.assertEqual([p["id"] for p in profiles], ["samma", "samma-2"])


class TestSettingsManagerProfiles(unittest.TestCase):
    def _manager(self, tmp: Path):
        from core.settings_manager import SettingsManager

        with mock.patch.dict(os.environ, {"EMAILAPP_PORTABLE": "1"}):
            return SettingsManager(tmp)

    def test_upsert_activate_delete_and_redaction(self):
        with tempfile.TemporaryDirectory() as td:
            manager = self._manager(Path(td))
            manager.update_from_dict(
                {
                    "smtp_server": "smtp.a.se",
                    "smtp_port": 465,
                    "sender_email": "a@example.se",
                    "sender_name": "Företag A",
                    "username": "a@example.se",
                    "password": "hemligt-a",
                    "use_ssl": True,
                }
            )
            first = manager.get_active_sender_profile()
            self.assertEqual(first["sender_email"], "a@example.se")

            second = manager.upsert_sender_profile(
                {
                    "name": "Företag B",
                    "smtp_server": "smtp.b.se",
                    "smtp_port": 587,
                    "sender_email": "b@example.com",
                    "sender_name": "Företag B",
                    "username": "b@example.com",
                    "password": "hemligt-b",
                    "reply_to": "svar@example.com",
                },
                make_active=True,
                save=True,
            )
            self.assertEqual(manager.get("sender_email"), "b@example.com")
            self.assertEqual(manager.get_active_sender_profile_id(), second["id"])
            self.assertEqual(len(manager.get_sender_profiles()), 2)

            redacted = manager.get_all(redact_secrets=True)
            passwords = {
                profile["password"] for profile in redacted["sender_profiles"]
            }
            self.assertEqual(passwords, {"***"})

            manager.set_active_sender_profile(first["id"], save=True)
            self.assertEqual(manager.get("sender_email"), "a@example.se")
            self.assertTrue(manager.delete_sender_profile(second["id"], save=True))
            self.assertEqual(len(manager.get_sender_profiles()), 1)
            self.assertFalse(manager.delete_sender_profile(first["id"]))

    def test_flat_edit_syncs_active_profile(self):
        with tempfile.TemporaryDirectory() as td:
            manager = self._manager(Path(td))
            manager.update_from_dict(
                {
                    "sender_email": "gammal@example.se",
                    "sender_name": "Gammal",
                    "smtp_server": "smtp.gammal.se",
                }
            )
            manager.update_from_dict({"sender_email": "ny@example.se"})
            active = manager.get_active_sender_profile()
            self.assertEqual(active["sender_email"], "ny@example.se")


if __name__ == "__main__":
    unittest.main()
