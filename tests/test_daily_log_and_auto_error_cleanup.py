import os
import sqlite3
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from core.diagnostics import collect_errors
from core.error_log import ErrorLogCollector
from core.log_archive import archive_logs, filter_today_log_text
from core.open_errors import (
    NAME as ERRORS_NAME,
    auto_cleanup_fixed_issues,
    notify_subsystem_recovered,
    open_issues,
    record_error,
)


class DailyLogOnlyAndAutoErrorCleanupTests(unittest.TestCase):
    def test_only_today_log_remains_visible_and_all_other_days_archive(self) -> None:
        today = date(2026, 11, 24)
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            logs = base / "logs"
            logs.mkdir(parents=True)

            # Active app.log with yesterday + two days ago + today
            (logs / "app.log").write_text(
                "2026-11-22 09:00:00 [INFO] Gammal post 1\n"
                "2026-11-23 14:15:00 [WARNING] Gårdagens varning\n"
                "  fortsättningsrad från igår\n"
                "2026-11-24 08:30:00 [INFO] Dagens post synlig\n",
                encoding="utf-8",
            )
            # UTF-16 startup.log with European DD/MM/YYYY + ISO YYYY-MM-DD
            (logs / "startup.log").write_text(
                "23/11/2026 07:00:00 | Launcher igår\n"
                "2026-11-24 08:29:55 | Launcher idag; exit code=0\n",
                encoding="utf-16",
            )
            # Rotated log from older day
            old_rot = logs / "app.log.1"
            old_rot.write_text("2026-11-21 12:00:00 [INFO] Roterad logg\n", encoding="utf-8")
            old_ts = 1763726400  # 2025-11-21 < today
            os.utime(old_rot, (old_ts, old_ts))

            collector = ErrorLogCollector(base, canonical_layout=True)
            collector.archive_completed_logs(today=today)

            # Rotated file removed from active logs/ and stored in archive/
            self.assertFalse(old_rot.exists())
            app_visible = (logs / "app.log").read_text(encoding="utf-8")
            self.assertEqual(app_visible, "2026-11-24 08:30:00 [INFO] Dagens post synlig\n")
            self.assertNotIn("2026-11-22", app_visible)
            self.assertNotIn("2026-11-23", app_visible)

            startup_visible = (logs / "startup.log").read_text(encoding="utf-16")
            self.assertIn("2026-11-24 08:29:55", startup_visible)
            self.assertNotIn("23/11/2026", startup_visible)

            # Archive zips exist for 2026-11-22 and 2026-11-23
            self.assertTrue(list((logs / "archive" / "2026-11-22").glob("app.log-*.zip")))
            self.assertTrue(list((logs / "archive" / "2026-11-23").glob("app.log-*.zip")))
            self.assertTrue(list((logs / "archive" / "2026-11-23").glob("startup.log-*.zip")))

    def test_filter_today_log_text_hides_any_uncompacted_older_lines(self) -> None:
        today = date(2026, 11, 24)
        mixed = (
            "2026-11-20 10:00:00 [ERROR] Äldre felrad\n"
            "Traceback (most recent call last):\n"
            "  File 'x.py', line 1\n"
            "23/11/2026 23:59:59 | Igår EU-datum\n"
            "2026-11-24 00:01:02 [INFO] Endast idag ska synas\n"
            "  Detalj för idag\n"
        )
        filtered = filter_today_log_text(mixed, today=today)
        self.assertEqual(
            filtered,
            "2026-11-24 00:01:02 [INFO] Endast idag ska synas\n  Detalj för idag\n",
        )

    def test_build_upgrade_auto_cleans_fixed_errors_and_reopens_if_recurring(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            logs = base / "logs"

            # Record two errors in an older build ("2026102360")
            with mock.patch("core.open_errors._current_build_id", return_value="2026102360"):
                record_error(
                    logs,
                    "app.log",
                    "2026-11-23 11:00:00 | WARNING | core.email_sender | Kunde inte översätta placeholder 'reg'",
                )
                record_error(
                    logs,
                    "app.log",
                    "2026-11-23 11:05:00 | ERROR | ui.tray | _do_show misslyckades",
                )
                self.assertEqual(len(open_issues(logs)), 2)

            # User updates to fixed build "2026102362" and app runs collector
            with mock.patch("core.open_errors._current_build_id", return_value="2026102362"):
                collector = ErrorLogCollector(base, canonical_layout=True)
                collector.collect(final=True)

                # Both old fixed errors were archived & removed from errors.log!
                self.assertEqual(open_issues(logs), [])
                errors_content = (logs / ERRORS_NAME).read_text(encoding="utf-8")
                self.assertEqual(errors_content, "")
                resolved_zips = list((logs / "archive").rglob("resolved-errors.log-*.zip"))
                self.assertGreaterEqual(len(resolved_zips), 1)

                # If an actual unfixed error occurs in the new build, it reopens immediately
                record_error(
                    logs,
                    "app.log",
                    "2026-11-24 09:00:00 | ERROR | ui.tray | _do_show misslyckades",
                )
                issues_now = open_issues(logs)
                self.assertEqual(len(issues_now), 1)
                self.assertIn("_do_show misslyckades", (logs / ERRORS_NAME).read_text(encoding="utf-8"))

    def test_pre_2026102362_sqlite_schema_migrates_and_auto_cleans_on_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            logs = base / "logs"
            logs.mkdir(parents=True)
            db_path = logs / "error-issues.sqlite3"
            db = sqlite3.connect(db_path)
            db.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT)")
            db.execute("INSERT INTO metadata VALUES ('canonical-error-log-v2', '1')")
            db.execute(
                "CREATE TABLE issues (id TEXT PRIMARY KEY, source TEXT, message TEXT, "
                "first_seen TEXT, last_seen TEXT, count INTEGER, resolved INTEGER)"
            )
            db.execute(
                "INSERT INTO issues VALUES ('deadbeef1234567890abcdef', 'app.log', "
                "'ERROR gammalt fel före fix', '2026-11-20T10:00:00', '2026-11-20T10:00:00', 2, 0)"
            )
            db.commit()
            db.close()

            collect_errors(base)
            self.assertEqual(open_issues(logs), [])
            self.assertEqual((logs / ERRORS_NAME).read_text(encoding="utf-8"), "")

    def test_runtime_subsystem_recovery_auto_cleans_corresponding_open_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            logs = base / "logs"

            # Record an SMTP error and an unrelated general error in the current build
            record_error(
                logs,
                "app.log",
                "2026-11-24 10:00:00 | ERROR | core.email_sender | SMTP-fel vid försök 1/3: timeout",
            )
            record_error(
                logs,
                "app.log",
                "2026-11-24 10:01:00 | ERROR | core.other | Annat ofixat fel",
            )
            self.assertEqual(len(open_issues(logs)), 2)

            # Simulate a subsequent successful SMTP operation
            cleaned = notify_subsystem_recovered(base, ("smtp_send",))
            self.assertEqual(len(cleaned), 1)

            remaining = open_issues(logs)
            self.assertEqual(len(remaining), 1)
            self.assertIn("Annat ofixat fel", remaining[0][2])
            errors_txt = (logs / ERRORS_NAME).read_text(encoding="utf-8")
            self.assertNotIn("SMTP-fel", errors_txt)
            self.assertIn("Annat ofixat fel", errors_txt)


if __name__ == "__main__":
    unittest.main()
