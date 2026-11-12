from datetime import date, timedelta
import faulthandler
import logging
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from zipfile import ZipFile
from core.error_log import ErrorLogCollector
from core.open_errors import open_issues
from core.log_archive import archive_logs
from core.daily_log_handler import DiagnosticFileHandler

class ThreeDailyLogsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.collector = ErrorLogCollector(self.base, canonical_layout=True)
        self.logs = self.base / 'logs'
        self.today = date.today()
        self.old = self.today - timedelta(days=1)

    def test_three_files_and_old_open_errors_survive_compaction(self):
        old = f'{self.old} 10:00:00 | ERROR | old-issue\nTraceback (most recent call last):\nValueError: failure\n'
        current = f'{self.today} 10:00:00 | INFO | healthy\n'
        (self.logs / 'app.log').write_text(old + current, encoding='utf-8')
        (self.logs / 'startup.log').write_text(f'{self.old} 10:00:00 | ERROR | startup failed\n' + current, encoding='utf-16')
        self.collector.archive_completed_logs(self.today)
        self.assertEqual({p.name for p in self.logs.glob('*.log')}, {'app.log', 'startup.log', 'errors.log'})
        self.assertEqual((self.logs / 'app.log').read_text(), current)
        self.assertEqual((self.logs / 'startup.log').read_text(encoding='utf-16'), current)
        errors = (self.logs / 'errors.log').read_text()
        self.assertIn('old-issue', errors)
        self.assertIn('startup failed', errors)
        self.assertNotIn('healthy', errors)
        self.assertGreaterEqual(len(open_issues(self.logs)), 2)

    def test_legacy_logs_retired_only_after_error_ingestion_and_verified_backup(self):
        source = self.logs / 'diagnostics.log'
        payload = f'{self.today} 10:00:00 | ERROR | legacy-error\n'
        source.write_text(payload)
        self.collector.archive_completed_logs(self.today)
        self.assertFalse(source.exists())
        backups = list((self.logs / 'archive').rglob('*.zip'))
        self.assertTrue(any(ZipFile(path).read('diagnostics.log').decode().replace('\r\n', '\n') == payload for path in backups))
        self.assertIn('legacy-error', (self.logs / 'errors.log').read_text())

    def test_failed_legacy_backup_leaves_original(self):
        source = self.logs / 'launcher.log'
        payload = f'{self.today} 10:00:00 | ERROR | preserve-me\n'
        source.write_text(payload)
        with mock.patch('core.log_archive.snapshot', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                self.collector.archive_completed_logs(self.today)
        self.assertEqual(source.read_text(), payload)

    def test_archive_retains_seven_completed_days(self):
        source = self.logs / 'app.log'
        source.write_text(''.join(f'{self.today - timedelta(days=n)} 12:00:00 | INFO | day-{n}\n' for n in (8, 7, 1, 0)))
        self.collector.archive_completed_logs(self.today)
        folders = {p.name for p in (self.logs / 'archive').iterdir()}
        self.assertNotIn(str(self.today - timedelta(days=8)), folders)
        self.assertIn(str(self.today - timedelta(days=7)), folders)
        self.assertIn(str(self.old), folders)

    def test_native_handler_is_rebound_after_atomic_compaction(self):
        source = self.logs / 'app.log'
        source.write_text(f'{self.old} 10:00:00 | INFO | old\n')
        handler = DiagnosticFileHandler(source, encoding='utf-8')
        with mock.patch('core.daily_log_handler.faulthandler.disable') as disable, mock.patch('core.daily_log_handler.faulthandler.enable') as enable:
            handler.native_capture = True
            try:
                archive_logs(self.logs, self.today)
                disable.assert_called()
                enable.assert_called()
                self.assertIs(enable.call_args.kwargs['file'], handler.stream)
                handler.emit(logging.LogRecord('test', logging.INFO, 'test.py', 1, 'after-compaction', (), None))
                handler.flush()
                self.assertIn('after-compaction', source.read_text())
            finally:
                handler.close()

    def test_startup_exit_failure_collected_but_success_not(self):
        (self.logs / 'startup.log').write_text('2026-11-01 10:00:00 | startup check ended; exit code=1\n2026-11-01 10:01:00 | startup check ended; exit code=0\n', encoding='utf-16')
        self.collector.collect(final=True)
        errors = (self.logs / 'errors.log').read_text()
        self.assertIn('exit code=1', errors)
        self.assertNotIn('exit code=0', errors)
