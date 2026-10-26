#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enhetstester för core/github_update.py – injicerad fetcher, inget nät."""
from __future__ import annotations

import datetime as dt
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.github_update import (  # noqa: E402
    UpdateInfo,
    apply_github_update,
    check_for_update,
    compare_versions,
    download_update_zip,
    extract_update_zip,
    find_app_root,
    is_newer_version,
    normalize_tag,
    now_iso,
    parse_build_id,
    parse_version,
    release_fingerprint,
    should_auto_check,
)


def _release_payload(**overrides):
    payload = {
        "id": 12345,
        "tag_name": "v5.4.0",
        "target_commitish": "abc123",
        "created_at": "2026-10-21T08:00:00Z",
        "published_at": "2026-10-21T08:05:00Z",
        "name": "E-postofferten 5.4.0",
        "body": "Ny mall-wizard!",
        "html_url": "https://github.com/Tokke2/MailOffer/releases/tag/v5.4.0",
        "zipball_url": "https://api.github.com/repos/Tokke2/MailOffer/zipball/v5.4.0",
        "tarball_url": "https://api.github.com/repos/Tokke2/MailOffer/tarball/v5.4.0",
        "assets": [],
    }
    payload.update(overrides)
    return payload


def _fetcher(status, payload=None, raw=None):
    body = raw if raw is not None else json.dumps(payload).encode("utf-8")

    def fetch(url, timeout):
        return status, body

    return fetch


def _make_zip_bytes(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return buf.getvalue()


class TestVersionLogic(unittest.TestCase):
    def test_parse_version(self) -> None:
        self.assertEqual(parse_version("v5.4.0"), (5, 4, 0))
        self.assertEqual(parse_version("5.4"), (5, 4))
        self.assertEqual(parse_version("v5.4.0-beta1"), (5, 4, 0))
        self.assertEqual(parse_version("release-6"), (6,))
        self.assertEqual(parse_version(""), ())
        self.assertEqual(parse_version(None), ())

    def test_compare_and_is_newer(self) -> None:
        self.assertTrue(is_newer_version("v5.4.0", "5.3.0"))
        self.assertTrue(is_newer_version("5.10.0", "5.9.9"))
        self.assertFalse(is_newer_version("5.4.0", "5.4.0"))
        self.assertFalse(is_newer_version("5.3.9", "5.4.0"))
        self.assertFalse(is_newer_version("", "5.4.0"))
        self.assertEqual(compare_versions("5.4", "5.4.0"), 0)
        self.assertEqual(compare_versions("v6.0.0", "5.4.0"), 1)
        self.assertEqual(compare_versions("5.4.0", "6.0.0"), -1)

    def test_normalize_tag(self) -> None:
        self.assertEqual(normalize_tag("v5.4.0"), "5.4.0")
        self.assertEqual(normalize_tag("5.4.0"), "5.4.0")
        self.assertEqual(normalize_tag(""), "")


class TestShouldAutoCheck(unittest.TestCase):
    NOW = dt.datetime(2026, 10, 19, 12, 0, 0)

    def test_never_checked(self) -> None:
        self.assertTrue(should_auto_check("", now=self.NOW))
        self.assertTrue(should_auto_check(None, now=self.NOW))
        self.assertTrue(should_auto_check("skräp", now=self.NOW))

    def test_recent_check_waits(self) -> None:
        recent = now_iso(self.NOW - dt.timedelta(hours=2))
        self.assertFalse(should_auto_check(recent, now=self.NOW))

    def test_old_check_runs(self) -> None:
        old = now_iso(self.NOW - dt.timedelta(hours=25))
        self.assertTrue(should_auto_check(old, now=self.NOW))

    def test_twelve_hour_boundary(self):
        self.assertFalse(should_auto_check(now_iso(self.NOW - dt.timedelta(hours=11, minutes=59)), now=self.NOW))
        self.assertTrue(should_auto_check(now_iso(self.NOW - dt.timedelta(hours=12)), now=self.NOW))

    def test_future_timestamp_runs(self) -> None:
        future = now_iso(self.NOW + dt.timedelta(days=2))
        self.assertTrue(should_auto_check(future, now=self.NOW))


class TestCheckForUpdate(unittest.TestCase):
    def test_newer_release_available_via_zipball(self) -> None:
        info = check_for_update(
            current_version="5.3.0",
            fetcher=_fetcher(200, _release_payload()),
        )
        self.assertTrue(info.available)
        self.assertEqual(info.latest_version, "5.4.0")
        self.assertEqual(info.tag, "v5.4.0")
        self.assertTrue(info.download_url.endswith("zipball/v5.4.0"))
        self.assertEqual(info.error, "")

    def test_zip_asset_preferred_over_zipball(self) -> None:
        payload = _release_payload(assets=[
            {"name": "notes.txt", "browser_download_url": "https://x/notes.txt"},
            {"name": "E-postofferten.zip",
             "browser_download_url": "https://x/app.zip"},
        ])
        info = check_for_update(current_version="5.3.0", fetcher=_fetcher(200, payload))
        self.assertEqual(info.download_url, "https://x/app.zip")

    def test_same_version_not_available(self) -> None:
        info = check_for_update(
            current_version="5.4.0",
            fetcher=_fetcher(200, _release_payload()),
        )
        self.assertFalse(info.available)
        self.assertEqual(info.latest_version, "5.4.0")

    def test_no_releases_404(self) -> None:
        info = check_for_update(
            current_version="5.3.0",
            fetcher=_fetcher(404, raw=b'{"message":"Not Found"}'),
        )
        self.assertTrue(info.no_releases)
        self.assertFalse(info.available)
        self.assertEqual(info.error, "")

    def test_http_error(self) -> None:
        info = check_for_update(
            current_version="5.3.0", fetcher=_fetcher(500, raw=b"oops")
        )
        self.assertFalse(info.available)
        self.assertIn("500", info.error)

    def test_network_exception_never_raises(self) -> None:
        def boom(url, timeout):
            raise OSError("nät nere")

        info = check_for_update(current_version="5.3.0", fetcher=boom)
        self.assertFalse(info.available)
        self.assertIn("nät nere", info.error)

    def test_malformed_json(self) -> None:
        info = check_for_update(
            current_version="5.3.0", fetcher=_fetcher(200, raw=b"inte json")
        )
        self.assertFalse(info.available)
        self.assertTrue(info.error)


class TestSameVersionFileChanges(unittest.TestCase):
    """Uppdaterade filer i SAMMA versionsnummer ska erbjudas."""

    def test_parse_build_id(self) -> None:
        self.assertEqual(parse_build_id("text build: 2026102102 mer"), "2026102102")
        self.assertEqual(
            parse_build_id({"name": "x", "body": "<!-- build: 7 -->"}), "7"
        )
        self.assertEqual(parse_build_id("ingen markering"), "")
        self.assertEqual(parse_build_id(None), "")

    def test_fingerprint_changes_with_files_not_notes(self) -> None:
        base = _release_payload()
        fp = release_fingerprint(base)
        self.assertTrue(fp)
        # Bara release-texten/namnet ändrat -> samma fingeravtryck
        self.assertEqual(
            fp,
            release_fingerprint(
                _release_payload(body="Annan text", name="Annat namn")
            ),
        )
        # Ny commit för taggen -> annat fingeravtryck
        self.assertNotEqual(
            fp, release_fingerprint(_release_payload(target_commitish="def456"))
        )
        # Utbytt zip-asset (ny storlek) -> annat fingeravtryck
        self.assertNotEqual(
            fp,
            release_fingerprint(_release_payload(assets=[{
                "id": 1, "name": "app.zip", "size": 999,
                "browser_download_url": "https://x/app.zip",
            }])),
        )
        self.assertEqual(release_fingerprint(None), "")
        self.assertEqual(release_fingerprint("skräp"), "")

    def test_same_version_newer_build_available(self) -> None:
        payload = _release_payload(
            tag_name="v1.0.0",
            body="Anteckningar <!-- build: 2026102102 -->",
            zipball_url="https://api.github.com/repos/Tokke2/MailOffer/zipball/v1.0.0",
        )
        info = check_for_update(
            current_version="1.0.0",
            current_build_id="2026102101",
            fetcher=_fetcher(200, payload),
        )
        self.assertTrue(info.available)
        self.assertTrue(info.same_version_files_changed)
        self.assertEqual(info.build_id, "2026102102")
        self.assertTrue(info.fingerprint)

    def test_same_version_same_or_older_build_not_available(self) -> None:
        for build in ("2026102101", "2026102100"):
            payload = _release_payload(
                tag_name="v1.0.0", body=f"build: {build}"
            )
            info = check_for_update(
                current_version="1.0.0",
                current_build_id="2026102101",
                fetcher=_fetcher(200, payload),
            )
            self.assertFalse(info.available, build)
            self.assertFalse(info.same_version_files_changed, build)

    def test_same_version_fingerprint_change_available(self) -> None:
        installed_fp = release_fingerprint(
            _release_payload(tag_name="v1.0.0", target_commitish="old", body="x")
        )
        changed = _release_payload(
            tag_name="v1.0.0", target_commitish="new", body="x"
        )
        info = check_for_update(
            current_version="1.0.0",
            current_build_id="",
            installed_fingerprint=installed_fp,
            fetcher=_fetcher(200, changed),
        )
        self.assertTrue(info.available)
        self.assertTrue(info.same_version_files_changed)

        same = check_for_update(
            current_version="1.0.0",
            current_build_id="",
            installed_fingerprint=release_fingerprint(changed),
            fetcher=_fetcher(200, changed),
        )
        self.assertFalse(same.available)

        unknown = check_for_update(
            current_version="1.0.0",
            current_build_id="",
            installed_fingerprint="",
            fetcher=_fetcher(200, changed),
        )
        self.assertFalse(unknown.available)  # baslinjas av UI:t i stället


class TestDownloadExtractApply(unittest.TestCase):
    def test_download_writes_zip(self) -> None:
        data = _make_zip_bytes({"main.pyw": "# nytt"})
        with tempfile.TemporaryDirectory() as td:
            path = download_update_zip(
                "https://example.invalid/app.zip", Path(td),
                fetcher=lambda url, timeout: (200, data),
            )
            self.assertEqual(path.read_bytes(), data)

    def test_download_rejects_http_error_and_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(RuntimeError):
                download_update_zip(
                    "https://x/a.zip", Path(td),
                    fetcher=lambda url, timeout: (404, b""),
                )
            with self.assertRaises(RuntimeError):
                download_update_zip(
                    "https://x/a.zip", Path(td),
                    fetcher=lambda url, timeout: (200, b""),
                )

    def test_find_app_root_nested_zipball_and_flat(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            nested = root / "Tokke2-MailOffer-abc123"
            nested.mkdir()
            (nested / "main.pyw").write_text("x", encoding="utf-8")
            self.assertEqual(find_app_root(root), nested)
            flat = root / "flat"
            flat.mkdir()
            (flat / "main.pyw").write_text("x", encoding="utf-8")
            self.assertEqual(find_app_root(flat), flat)
            with self.assertRaises(ValueError):
                find_app_root(root / "flat" / ".." / "tom") \
                    if (root / "tom").mkdir() is None else None

    def test_zip_slip_is_blocked(self) -> None:
        evil = _make_zip_bytes({"../evil.py": "pwn", "main.pyw": "x"})
        with tempfile.TemporaryDirectory() as td:
            zip_path = Path(td) / "evil.zip"
            zip_path.write_bytes(evil)
            with self.assertRaises(ValueError):
                extract_update_zip(zip_path, Path(td) / "out")
            self.assertFalse((Path(td) / "evil.py").exists())

    def test_apply_never_touches_user_data(self) -> None:
        zip_bytes = _make_zip_bytes({
            "Tokke2-MailOffer-deadbeef/main.pyw": "# NY VERSION",
            "Tokke2-MailOffer-deadbeef/email_settings.json": '{"hack": true}',
            "Tokke2-MailOffer-deadbeef/contacts.json": '{"hack": true}',
            "Tokke2-MailOffer-deadbeef/Mallar/Min egna mall.txt": "ÖVERSKRIVEN",
            "Tokke2-MailOffer-deadbeef/adresslistor/contacts.json": "{}",
            "Tokke2-MailOffer-deadbeef/thunderbird/manifest.json": '{"ok": 1}',
        })
        with tempfile.TemporaryDirectory() as td:
            app_dir = Path(td)
            (app_dir / "main.pyw").write_text("# GAMMAL", encoding="utf-8")
            (app_dir / "email_settings.json").write_text(
                '{"mina": "inställningar"}', encoding="utf-8"
            )
            (app_dir / "Mallar").mkdir()
            (app_dir / "Mallar" / "Min egna mall.txt").write_text(
                "ORIGINAL", encoding="utf-8"
            )
            (app_dir / "thunderbird").mkdir()
            (app_dir / "thunderbird" / "manifest.json").write_text(
                '{"gammal": 1}', encoding="utf-8"
            )

            info = UpdateInfo(
                available=True, latest_version="9.9.9",
                download_url="https://example.invalid/app.zip",
                build_id="2026102102", fingerprint="fp-123",
                same_version_files_changed=True,
            )
            result = apply_github_update(
                info, app_dir,
                fetcher=lambda url, timeout: (200, zip_bytes),
            )
            self.assertEqual(result["version"], "9.9.9")
            self.assertEqual(result["build_id"], "2026102102")
            self.assertEqual(result["fingerprint"], "fp-123")
            self.assertTrue(result["same_version_files_changed"])
            self.assertEqual(
                (app_dir / "main.pyw").read_text(encoding="utf-8"), "# NY VERSION"
            )
            self.assertIn(
                "mina",
                (app_dir / "email_settings.json").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                (app_dir / "Mallar" / "Min egna mall.txt").read_text(
                    encoding="utf-8"
                ),
                "ORIGINAL",
            )
            # Kod-JSON (manifest) FÅR uppdateras
            self.assertIn(
                '"ok"',
                (app_dir / "thunderbird" / "manifest.json").read_text(
                    encoding="utf-8"
                ),
            )


if __name__ == "__main__":
    unittest.main()
