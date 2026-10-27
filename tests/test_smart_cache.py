from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from core.smart_cache import clean_smart_cache, run_due_cleanup


class Settings:
    def __init__(self, data=None):
        self.data = dict(data or {})

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value

    def save(self):
        return True


class SmartCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.now = datetime(2026, 10, 27, 12, tzinfo=timezone.utc)

    def file(self, name, age=48 * 3600):
        path = self.base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"cache")
        stamp = self.now.timestamp() - age
        os.utime(path, (stamp, stamp))
        return path

    def test_only_old_regular_bytecode_in_known_cache_dirs(self):
        old = self.file("core/__pycache__/old.cpython-312.pyc")
        boundary = self.file("ui/__pycache__/boundary.pyc", 24 * 3600)
        keep = [self.file("script/__pycache__/fresh.pyc", 23 * 3600),
                self.file("__pycache__/future.pyc", -3600),
                self.file("core/__pycache__/document.txt"),
                self.file("core/source.pyc"), self.file("core/example.py"),
                self.file("other/__pycache__/old.pyc")]
        result = clean_smart_cache(self.base, now=self.now)
        self.assertEqual(result, {"removed": 2, "bytes": 10, "errors": 0})
        self.assertFalse(old.exists())
        self.assertFalse(boundary.exists())
        self.assertTrue(all(p.exists() for p in keep))

    def test_user_data_and_repository_are_not_scanned(self):
        names = ["Mallar", ".data", "logs", "adresslistor", "plugins", ".git", ".venv", "attachments", "backups"]
        protected = [self.file(f"{name}/__pycache__/old.pyc") for name in names]
        clean_smart_cache(self.base, now=self.now)
        self.assertTrue(all(p.exists() for p in protected))

    def test_symbolic_link_file_and_directory_are_skipped(self):
        original = self.file("documents/keep.pyc")
        folder = self.base / "core/__pycache__"
        folder.mkdir(parents=True)
        try:
            (folder / "linked.pyc").symlink_to(original)
            (self.base / "ui").symlink_to(original.parent, target_is_directory=True)
        except OSError:
            self.skipTest("Symbolic links unavailable")
        result = clean_smart_cache(self.base, now=self.now)
        self.assertTrue(original.exists())
        self.assertTrue((folder / "linked.pyc").is_symlink())
        self.assertEqual(result["removed"], 0)

    def test_symlinked_parent_does_not_lead_outside_app(self):
        with tempfile.TemporaryDirectory() as external:
            cache = Path(external) / "__pycache__"
            cache.mkdir()
            keep = cache / "old.pyc"
            keep.write_bytes(b"cache")
            os.utime(keep, (0, 0))
            try:
                (self.base / "core").symlink_to(external, target_is_directory=True)
            except OSError:
                self.skipTest("Symbolic links unavailable")
            self.assertEqual(clean_smart_cache(self.base, now=self.now)["removed"], 0)
            self.assertTrue(keep.exists())

    def test_locked_file_is_preserved_and_reported(self):
        old = self.file("__pycache__/locked.pyc")
        with mock.patch.object(Path, "unlink", side_effect=PermissionError("locked")), self.assertLogs("core.smart_cache", level="WARNING"):
            result = clean_smart_cache(self.base, now=self.now)
        self.assertTrue(old.exists())
        self.assertEqual(result["errors"], 1)
        self.assertEqual(result["removed"], 0)

    def test_once_per_day_including_exact_boundary(self):
        settings = Settings()
        self.assertIsNotNone(run_due_cleanup(self.base, settings, now=self.now))
        with mock.patch("core.smart_cache.clean_smart_cache") as clean:
            self.assertIsNone(run_due_cleanup(self.base, settings, now=self.now + timedelta(hours=23, minutes=59)))
            clean.assert_not_called()
        self.assertIsNotNone(run_due_cleanup(self.base, settings, now=self.now + timedelta(days=1)))

    def test_disabled_auto_and_safe_manual_override(self):
        settings = Settings({"auto_cache_cleanup": False})
        old = self.file("__pycache__/old.pyc")
        fresh = self.file("__pycache__/fresh.pyc", 1)
        self.assertIsNone(run_due_cleanup(self.base, settings, now=self.now))
        self.assertTrue(old.exists())
        self.assertIsNotNone(run_due_cleanup(self.base, settings, now=self.now, force=True))
        self.assertFalse(old.exists())
        self.assertTrue(fresh.exists())

    def test_invalid_or_future_timestamp_recovers(self):
        for timestamp in ("invalid", None, (self.now + timedelta(days=10)).isoformat()):
            settings = Settings({"cache_cleanup_last": timestamp})
            self.assertIsNotNone(run_due_cleanup(self.base, settings, now=self.now))

    def test_timestamp_survives_new_session(self):
        settings = Settings()
        run_due_cleanup(self.base, settings, now=self.now)
        restored = Settings(settings.data)
        self.assertIsNone(run_due_cleanup(self.base, restored, now=self.now + timedelta(hours=1)))

    def test_save_failure_restores_timestamp(self):
        settings = Settings({"cache_cleanup_last": "previous"})
        with mock.patch.object(settings, "save", return_value=False), self.assertRaises(OSError):
            run_due_cleanup(self.base, settings, now=self.now)
        self.assertEqual(settings.get("cache_cleanup_last"), "previous")
