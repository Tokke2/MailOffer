import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from core.error_log import ErrorLogCollector, is_error, redact


class ErrorLogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.collector = self.make_collector()
        self.logs = self.base / 'logs'

    def make_collector(self):
        return ErrorLogCollector(self.base, fallback_dir=self.base / 'fallback',
                                 launcher_fallback=self.base / 'fallback-launcher.log')

    def text(self):
        return self.collector.path.read_text(encoding='utf-8')

    def test_error_and_full_traceback_without_normal_information(self):
        (self.logs / 'email_app.log').write_text(
            '2026-10-30 10:00:00 | INFO | module | normal start\n'
            '2026-10-30 10:01:00 | ERROR | module | send failed\n'
            'Traceback (most recent call last):\n'
            '  File "send.py", line 10\n'
            'ValueError: failure-marker\n'
            '2026-10-30 10:02:00 | INFO | module | normal end\n', encoding='utf-8')
        self.assertEqual(self.collector.collect(), 1)
        self.assertIn('failure-marker', self.text())
        self.assertIn('send.py', self.text())
        self.assertIn('source=', self.text())
        self.assertNotIn('normal start', self.text())
        self.assertNotIn('normal end', self.text())

    def test_utf16_launcher_only_nonzero_errors(self):
        (self.logs / 'launcher.log').write_text(
            '30/10/2026 10:00:00 | Process ended; exit code=0\n'
            '30/10/2026 10:00:01 | Installer ended; exit code=0; script error=0 \n'
            '30/10/2026 10:00:02 | Process ended; exit code=3\n'
            '30/10/2026 10:00:03 | Launch error=Access denied\n', encoding='utf-16')
        self.assertEqual(self.collector.collect(), 2)
        self.assertNotIn('exit code=0', self.text())
        self.assertIn('exit code=3', self.text())
        self.assertIn('Access denied', self.text())

    def test_repeated_scan_and_restart_do_not_reimport(self):
        source = self.logs / 'module.log'
        source.write_text('ERROR first\n', encoding='utf-8')
        self.assertEqual(self.collector.collect(), 1)
        self.assertEqual(self.collector.collect(), 0)
        self.assertEqual(self.make_collector().collect(), 0)
        with source.open('a', encoding='utf-8') as stream:
            stream.write('ERROR second\n')
        self.assertEqual(self.collector.collect(), 1)
        self.assertEqual(self.text().count('ERROR first'), 1)
        self.assertIn('ERROR second', self.text())

    def test_source_rotation_and_truncation(self):
        source = self.logs / 'module.log'
        source.write_text('ERROR original\n', encoding='utf-8')
        self.collector.collect()
        source.rename(self.logs / 'module.log.1')
        source.write_text('ERROR after rotation\n', encoding='utf-8')
        self.collector.collect()
        source.write_text('ERROR cut\n', encoding='utf-8')
        self.collector.collect()
        self.assertEqual(self.text().count('ERROR original'), 1)
        self.assertIn('ERROR after rotation', self.text())
        self.assertIn('ERROR cut', self.text())

    def test_collector_never_reads_itself_or_modifies_sources(self):
        source = self.logs / 'module.log'
        original = b'ERROR original\n'
        source.write_bytes(original)
        self.collector.collect()
        for _ in range(3):
            self.assertEqual(self.collector.collect(), 0)
        self.assertEqual(source.read_bytes(), original)
        self.assertEqual(self.text().count('ERROR original'), 1)

    def test_native_crash_and_startup_crash_include_all_stack_lines(self):
        (self.logs / 'native-crash-123.log').write_text('Fatal Python error: access violation\nThread 123:\n  native.py line 5\n')
        (self.logs / 'startup_crash.log').write_text('ImportError: missing library\n  startup.py line 1\n')
        self.collector.collect()
        self.assertIn('native.py line 5', self.text())
        self.assertIn('startup.py line 1', self.text())

    def test_debug_caught_exception_and_warning_are_collected(self):
        (self.logs / 'diagnostics.log').write_text('2026-10-30 10:00:00 | DEBUG | module | caught\nTraceback (most recent call last):\nRuntimeError: caught-marker\n2026-10-30 10:00:01 | WARNING | module | warning-marker\n')
        self.assertEqual(self.collector.collect(), 2)
        self.assertIn('caught-marker', self.text())
        self.assertIn('warning-marker', self.text())

    def test_app_fallback_directory_and_single_launcher_fallback(self):
        fallback = self.base / 'fallback'
        fallback.mkdir()
        (fallback / 'diagnostics.log').write_text('ERROR fallback-marker\n')
        (self.base / 'fallback-launcher.log').write_text('30/10/2026 10:00:00 | Process ended; exit code=4\n', encoding='utf-16')
        (self.base / 'unrelated.log').write_text('ERROR must-not-read\n')
        self.assertEqual(self.collector.collect(), 2)
        self.assertIn('fallback-marker', self.text())
        self.assertIn('exit code=4', self.text())
        self.assertNotIn('must-not-read', self.text())

    def test_password_redaction_and_no_message_content_in_index(self):
        (self.logs / 'module.log').write_text('ERROR password="long secret value" token=hidden Authorization: Bearer private AUTH PLAIN base64value\n')
        self.collector.collect()
        for secret in ('long secret value', 'hidden', 'private', 'base64value'):
            self.assertNotIn(secret, self.text())
            self.assertNotIn(secret, self.collector.state_path.read_text())
        self.assertIn('[REDACTED]', self.text())
        self.assertNotIn('json-secret', redact('ERROR {"password": "json-secret"}'))

    def test_incomplete_line_waits_and_final_flush_collects_it(self):
        source = self.logs / 'module.log'
        source.write_bytes(b'ERROR incomplete')
        self.assertEqual(self.collector.collect(), 0)
        self.assertEqual(self.collector.collect(final=True), 1)
        self.assertIn('incomplete', self.text())

    def test_following_traceback_fragment_is_preserved(self):
        source = self.logs / 'module.log'
        source.write_text('2026-10-30 10:00:00 | ERROR | module | fail\n')
        self.collector.collect()
        with source.open('a') as stream:
            stream.write('  File "late-stack.py", line 10\n')
        self.collector.collect()
        self.assertIn('late-stack.py', self.text())

    def test_rotates_output_and_does_not_collect_output_backups(self):
        (self.logs / 'module.log').write_text('ERROR first\n')
        self.collector.collect()
        with mock.patch('core.error_log.MAX_SIZE', 100):
            with (self.logs / 'module.log').open('a') as stream:
                stream.write('ERROR second\n')
            self.collector.collect()
        self.assertTrue((self.logs / 'errors.log.1').exists())
        self.assertEqual(self.collector.collect(), 0)

    def test_corrupt_index_recovers_without_touching_original(self):
        (self.logs / 'module.log').write_text('ERROR recovery\n')
        self.collector.state_path.write_text('not json')
        self.assertEqual(self.collector.collect(), 1)
        self.assertIsInstance(json.loads(self.collector.state_path.read_text()), dict)

    def test_empty_file_then_first_error(self):
        source = self.logs / 'module.log'
        source.touch()
        self.collector.collect()
        source.write_text('ERROR first after empty\n')
        self.assertEqual(self.collector.collect(), 1)

    def test_healthy_launcher_messages_are_not_errors(self):
        self.assertFalse(is_error('Process ended; exit code=0', 'launcher.log'))
        self.assertFalse(is_error('Fallback process ended; exit code=0; error=0 ', 'launcher.log'))


    def test_output_failure_retries_without_advancing_cursor(self):
        (self.logs / 'module.log').write_text('ERROR retry-marker\n')
        with mock.patch.object(self.collector, '_append', side_effect=OSError('disk full')):
            self.assertEqual(self.collector.collect(), 0)
        self.assertEqual(self.collector.collect(), 1)
        self.assertIn('retry-marker', self.text())

    def test_stop_drains_recent_errors_and_incomplete_last_line(self):
        self.collector.start()
        (self.logs / 'module.log').write_text('ERROR shutdown-marker')
        self.collector.stop()
        self.assertIn('shutdown-marker', self.text())


    def test_plain_severity_records_exclude_normal_info(self):
        (self.logs / 'plain.log').write_text('INFO healthy-before\nERROR plain-failure\n  stack-context\nINFO healthy-after\n')
        self.assertEqual(self.collector.collect(), 1)
        self.assertIn('plain-failure', self.text())
        self.assertIn('stack-context', self.text())
        self.assertNotIn('healthy-before', self.text())
        self.assertNotIn('healthy-after', self.text())
