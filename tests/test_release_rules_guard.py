#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Säkerställ att projektets permanenta regler och Latest-release-synk alltid finns på plats."""

from __future__ import annotations

from pathlib import Path
import unittest

from tools.sync_latest_release import (
    build_release_patch_payload,
    sync_release,
    update_release_body_build_marker,
)

ROOT = Path(__file__).resolve().parents[1]


class ReleaseAndPersistentRulesTests(unittest.TestCase):
    def test_persistent_agent_instruction_files_exist_and_cover_hard_rules(self) -> None:
        for rel in ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md", "docs/forslagslogg.md"):
            path = ROOT / rel
            self.assertTrue(path.is_file(), f"Saknar permanent regelfil: {rel}")

        agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for required_phrase in (
            "make_latest",
            "/releases/latest",
            "compare_release_files",
            "sync_latest_release.py",
            "cleanup_pre_update_backups",
            "RETENTION_DAYS = 7",
            "docs/forslagslogg.md",
            "10 helt nya förbättringsförslag",
        ):
            self.assertIn(required_phrase, agents_text)

    def test_ci_workflow_automatically_syncs_and_marks_latest_release_on_push(self) -> None:
        wf = (ROOT / ".github/workflows/tests.yml").read_text(encoding="utf-8")
        self.assertIn("sync-latest-release:", wf)
        self.assertIn("needs: [unittest, windows-startup-syntax, desktop-portability]", wf)
        self.assertIn("contents: write", wf)
        self.assertIn("python tools/sync_latest_release.py", wf)

    def test_sync_release_moves_tag_sets_make_latest_true_and_rejects_main(self) -> None:
        calls = []
        fake_sha = "a" * 40

        def fake_api(method: str, endpoint: str, payload=None):
            calls.append((method, endpoint, payload))
            if method == "GET" and "releases?per_page=" in endpoint:
                return [
                    {
                        "id": 425123647,
                        "tag_name": "v1.0.0",
                        "name": "E-postofferten 1.0.0",
                        "body": "<!-- build: 2026102365 -->\nBefintlig text",
                    }
                ]
            if method == "PATCH" and endpoint.endswith("/releases/425123647"):
                return {"id": 425123647, "tag_name": "v1.0.0"}
            if method == "GET" and endpoint.endswith("/releases/latest"):
                return {
                    "id": 425123647,
                    "tag_name": "v1.0.0",
                    "draft": False,
                    "prerelease": False,
                }
            return {}

        tag, rel_id = sync_release(
            repo="Tokke2/MailOffer",
            commit_sha=fake_sha,
            branch="arena/447b9635-mailoffer",
            version="1.0.0",
            build_id="2026102366",
            note="- Synkar alltid release + Latest",
            api=fake_api,
        )
        self.assertEqual(tag, "v1.0.0")
        self.assertEqual(rel_id, 425123647)

        # Verify tag ref moved to exact SHA
        self.assertEqual(calls[0][0], "PATCH")
        self.assertEqual(calls[0][1], "repos/Tokke2/MailOffer/git/refs/tags/v1.0.0")
        self.assertEqual(calls[0][2], {"sha": fake_sha, "force": True})

        # Verify release PATCH explicitly sets make_latest="true", draft=False, prerelease=False
        patch_calls = [c for c in calls if c[0] == "PATCH" and "/releases/425123647" in c[1]]
        self.assertEqual(len(patch_calls), 1)
        patch_payload = patch_calls[0][2]
        self.assertEqual(patch_payload["make_latest"], "true")
        self.assertFalse(patch_payload["draft"])
        self.assertFalse(patch_payload["prerelease"])
        self.assertIn("<!-- build: 2026102366 -->", patch_payload["body"])
        self.assertIn("## BUILD2026102366", patch_payload["body"])

        # Main and master must always be rejected
        for forbidden in ("main", "master", "MAIN"):
            with self.assertRaises(ValueError):
                build_release_patch_payload(
                    tag="v1.0.0",
                    target_commitish=forbidden,
                    name="E-postofferten 1.0.0",
                    body=update_release_body_build_marker("", "2026102366"),
                )


if __name__ == "__main__":
    unittest.main()
