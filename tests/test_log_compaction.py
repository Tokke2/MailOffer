from datetime import date
import logging
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile
from core.log_archive import archive_logs
from core.error_log import ErrorLogCollector
from core.open_errors import open_issues, resolve_issues, record_error, import_history

TODAY = date(2026, 11, 4)
OLD = '2026-11-03 10:00:00 | ERROR | failure-code-535\nTraceback (most recent call last):\n  stack.py:12\n'
NEW = '2026-11-04 10:00:00 | INFO | healthy today\n'


class DailyCompactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.logs = self.base / 'logs'
        self.logs.mkdir()
        self.source = self.logs / 'email_app.log'

    def test_collect_before_move_keeps_open_error_and_does_not_reingest_today(self):
        self.source.write_text(OLD + NEW + NEW.replace('INFO', 'ERROR'))
        collector = ErrorLogCollector(self.base)
        self.assertEqual(collector.collect(), 2)
        keys = [row[0] for row in open_issues(self.logs)]
        collector.archive_completed_logs(TODAY)
        self.assertEqual(self.source.read_text(), NEW + NEW.replace('INFO', 'ERROR'))
        self.assertIn('failure-code-535', (self.logs / 'errors.log').read_text())
        self.assertFalse((self.logs / 'unresolved-errors.log').exists())
        self.assertEqual(collector.collect(), 0)
        resolve_issues(self.logs, keys)
        collector.archive_completed_logs(TODAY)
        self.assertEqual(open_issues(self.logs), [])
        self.assertEqual(collector.collect(), 0)
        self.assertTrue(list((self.logs / 'archive/2026-11-03').glob('*.zip')))

    def test_running_file_handler_reopens_new_file_and_preserves_today(self):
        handler = logging.FileHandler(self.source, encoding='utf-8')
        self.addCleanup(handler.close)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.Logger('archive-writer', logging.INFO)
        logger.addHandler(handler)
        logger.info(OLD.rstrip())
        logger.info(NEW.rstrip())
        archive_logs(self.logs, TODAY)
        logger.info('2026-11-04 12:00:00 | INFO | still writable')
        handler.flush()
        self.assertNotIn('failure-code', self.source.read_text())
        self.assertIn('healthy today', self.source.read_text())
        self.assertIn('still writable', self.source.read_text())

    def test_rename_failure_leaves_original_and_verified_archive_then_retries(self):
        self.source.write_text(OLD + NEW)
        replace = os.replace
        def fail_final(source, target):
            if Path(target) == self.source:
                raise PermissionError('busy writer')
            return replace(source, target)
        with mock.patch('core.log_archive.os.replace', side_effect=fail_final):
            archive_logs(self.logs, TODAY)
        self.assertEqual(self.source.read_text(), OLD + NEW)
        paths = list((self.logs / 'archive/2026-11-03').glob('*.zip'))
        self.assertEqual(len(paths), 1)
        with zipfile.ZipFile(paths[0]) as archive:
            self.assertEqual(archive.read(self.source.name).decode().splitlines(), OLD.splitlines())
        archive_logs(self.logs, TODAY)
        self.assertEqual(self.source.read_text(), NEW)

    def test_archive_failure_never_rewrites_source(self):
        self.source.write_text(OLD + NEW)
        with mock.patch('core.log_archive.snapshot', side_effect=OSError('disk full')), self.assertRaises(OSError):
            archive_logs(self.logs, TODAY)
        self.assertEqual(self.source.read_text(), OLD + NEW)

    def test_partial_collector_cursor_does_not_allow_deleting_uncollected_errors(self):
        self.source.write_text(OLD * 30 + NEW)
        collector = ErrorLogCollector(self.base)
        with mock.patch('core.error_log.MAX_READ', len(OLD.encode())):
            collector.collect()
            collector.archive_completed_logs(TODAY)
        self.assertIn('failure-code', self.source.read_text())
        collector.collect(final=True)
        collector.archive_completed_logs(TODAY)
        self.assertEqual(self.source.read_text(), NEW)

    def test_utf16_source_remains_utf16_and_future_records_are_not_deleted(self):
        future = '2026-11-05 10:00:00 | INFO | clock ahead\n'
        self.source.write_text(OLD + NEW + future, encoding='utf-16')
        archive_logs(self.logs, TODAY)
        self.assertTrue(self.source.read_bytes().startswith(b'\xff\xfe'))
        self.assertEqual(self.source.read_text(encoding='utf-16'), NEW + future)

    def test_invalid_encoding_is_left_untouched(self):
        raw = b'2026-11-03 10:00:00 | ERROR | bad \xff\n'
        self.source.write_bytes(raw)
        archive_logs(self.logs, TODAY)
        self.assertEqual(self.source.read_bytes(), raw)

    @unittest.skipUnless(os.name == 'nt', 'Windows exclusive sharing')
    def test_external_open_writer_is_not_truncated(self):
        self.source.write_text(OLD + NEW)
        with self.source.open('ab') as writer:
            self.assertEqual(archive_logs(self.logs, TODAY), [])
            writer.write(b'2026-11-04 12:00:00 | INFO | external write\n')
            writer.flush()
            self.assertIn('failure-code', self.source.read_text())
        archive_logs(self.logs, TODAY)
        self.assertNotIn('failure-code', self.source.read_text())
        self.assertIn('external write', self.source.read_text())

    def test_missing_canonical_file_regenerates_without_losing_registry(self):
        record_error(self.logs, 'email_app.log', 'ERROR SMTP 535')
        (self.logs / 'errors.log').unlink()
        import_history(self.logs)
        self.assertIn('SMTP 535', (self.logs / 'errors.log').read_text())

    def test_old_history_and_old_generated_view_migrate_without_reopening_resolved(self):
        self.source.write_text(OLD)
        collector = ErrorLogCollector(self.base)
        collector.collect()
        key = open_issues(self.logs)[0][0]
        resolve_issues(self.logs, [key])
        import sqlite3
        db = sqlite3.connect(self.logs / 'error-issues.sqlite3')
        db.execute("DELETE FROM metadata WHERE key='canonical-error-log-v2'")
        db.commit()
        db.close()
        (self.logs / 'errors.log').write_text('=== Collected 2026-11-03T12:00:00 | source=email_app.log ===\n' + OLD)
        (self.logs / 'unresolved-errors.log').write_text('OPEN ERRORS — mark resolved in the app; do not edit this generated file.\n', encoding='utf-8')
        import_history(self.logs)
        self.assertEqual(open_issues(self.logs), [])
        self.assertFalse((self.logs / 'unresolved-errors.log').exists())
        self.assertTrue(list((self.logs / 'archive').rglob('*.zip')))

    def test_interrupted_index_update_recovers_without_reopening_resolved_errors(self):
        current_error = NEW.replace('INFO', 'ERROR')
        self.source.write_text(OLD + current_error)
        collector = ErrorLogCollector(self.base)
        collector.collect()
        resolve_issues(self.logs, [row[0] for row in open_issues(self.logs)])
        with mock.patch.object(collector, '_save_index', side_effect=OSError('simulated interruption')), self.assertRaises(OSError):
            collector.archive_completed_logs(TODAY)
        self.assertEqual(self.source.read_text(), current_error)
        self.assertTrue(list(self.logs.glob('.archive-cursor-*.json')))
        self.assertEqual(ErrorLogCollector(self.base).collect(), 0)
        self.assertEqual(open_issues(self.logs), [])
        self.assertFalse(list(self.logs.glob('.archive-cursor-*.json')))

    def test_writer_waits_for_compaction_and_appends_to_replacement(self):
        import threading
        import time
        import core.log_archive as module
        self.source.write_text(OLD + NEW)
        handler = logging.FileHandler(self.source, encoding='utf-8')
        self.addCleanup(handler.close)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger = logging.Logger('concurrent-archive', logging.INFO)
        logger.addHandler(handler)
        done = threading.Event()
        def write():
            logger.info('2026-11-04 12:00:00 | INFO | concurrent-write')
            done.set()
        thread = threading.Thread(target=write)
        snapshot = module.snapshot
        def during_snapshot(*args):
            thread.start()
            time.sleep(0.05)
            self.assertFalse(done.is_set())
            return snapshot(*args)
        with mock.patch('core.log_archive.snapshot', side_effect=during_snapshot):
            archive_logs(self.logs, TODAY)
        thread.join(timeout=5)
        self.assertTrue(done.is_set())
        self.assertIn('concurrent-write', self.source.read_text())
        self.assertNotIn('failure-code', self.source.read_text())

    def test_unknown_legacy_content_is_not_deleted(self):
        legacy = self.logs / 'unresolved-errors.log'
        legacy.write_text('OPEN ERRORS\nunknown content that must not disappear\n', encoding='utf-8')
        original = legacy.read_bytes()
        with self.assertRaises(ValueError):
            import_history(self.logs)
        self.assertEqual(legacy.read_bytes(), original)
