from datetime import date
from pathlib import Path
import tempfile
import unittest
import zipfile

from core.log_archive import archive_logs
from core.open_errors import record_error, open_issues, resolve_issues, import_history


class LogArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.logs = Path(self.temp.name)

    def test_archive_past_days_not_today_or_open_errors(self):
        original = '2026-11-02 10:00:00 | INFO | old\n  context\n2026-11-03 10:00:00 | ERROR | yesterday\n2026-11-04 10:00:00 | INFO | today\n'
        source = self.logs / 'email_app.log'
        source.write_text(original)
        (self.logs / 'unresolved-errors.log').write_text('2026-11-01 10:00:00 | ERROR | open issue\n')
        paths = archive_logs(self.logs, date(2026, 11, 4))
        self.assertEqual(len(paths), 2)
        self.assertEqual({p.parent.name for p in paths}, {'2026-11-02', '2026-11-03'})
        for path in paths:
            with zipfile.ZipFile(path) as archive:
                text = archive.read('email_app.log').decode()
                self.assertNotIn('today', text)
                self.assertNotIn('open issue', text)
        self.assertEqual(source.read_text(), original)
        self.assertEqual(archive_logs(self.logs, date(2026, 11, 4)), [])

    def test_utf16_launcher_archive(self):
        (self.logs / 'launcher.log').write_text('2026-11-03 12:00:00 | Process ended; exit code=3\n2026-11-04 12:00:00 | Started\n', encoding='utf-16')
        paths = archive_logs(self.logs, date(2026, 11, 4))
        self.assertEqual(len(paths), 1)
        with zipfile.ZipFile(paths[0]) as archive:
            self.assertIn('exit code=3', archive.read('launcher.log').decode())

    def test_archive_write_failure_does_not_remove_source(self):
        from unittest import mock
        source = self.logs / 'email_app.log'
        source.write_text('2026-11-03 12:00:00 | INFO | original\n')
        with mock.patch('core.log_archive.zipfile.ZipFile', side_effect=OSError('disk full')), self.assertRaises(OSError):
            archive_logs(self.logs, date(2026, 11, 4))
        self.assertTrue(source.exists())
        self.assertIn('original', source.read_text())

    def test_errors_remain_open_until_manual_resolution_and_reopen(self):
        key = record_error(self.logs, 'email_app.log', '2026-11-03 10:00:00 | ERROR | SMTP 535 password=private')
        record_error(self.logs, 'email_app.log.1', '2026-11-04 10:00:00 | ERROR | SMTP 535 password=private')
        self.assertEqual(len(open_issues(self.logs)), 1)
        self.assertEqual(open_issues(self.logs)[0][-1], 2)
        text = (self.logs / 'unresolved-errors.log').read_text()
        self.assertIn('SMTP 535', text)
        self.assertNotIn('private', text)
        archive_logs(self.logs, date(2026, 11, 5))
        self.assertEqual(len(open_issues(self.logs)), 1)
        resolve_issues(self.logs, [key])
        self.assertEqual(open_issues(self.logs), [])
        self.assertNotIn('SMTP 535', (self.logs / 'unresolved-errors.log').read_text())
        record_error(self.logs, 'email_app.log', '2026-11-05 10:00:00 | ERROR | SMTP 535 password=private')
        self.assertEqual(open_issues(self.logs)[0][0], key)

    def test_old_retained_error_summary_imports_once(self):
        (self.logs / 'errors.log').write_text('\n=== Collected 2026-11-03T10:00:00 | source=C:/App/logs/email_app.log ===\n2026-11-03 10:00:00 | ERROR | existing-error\n')
        import_history(self.logs)
        self.assertEqual(len(open_issues(self.logs)), 1)
        key = open_issues(self.logs)[0][0]
        resolve_issues(self.logs, [key])
        import_history(self.logs)
        self.assertEqual(open_issues(self.logs), [])
