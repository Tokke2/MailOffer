import logging
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from core.diagnostics import RedactingFormatter

ROOT = Path(__file__).resolve().parents[1]


class DiagnosticsTests(unittest.TestCase):
    def test_redacts_common_credentials(self):
        record = logging.LogRecord('test', logging.ERROR, 'test.py', 1,
                                   'password=hunter2 token=private AUTH PLAIN abcdef', (), None)
        text = RedactingFormatter('%(message)s').format(record)
        for secret in ('hunter2', 'private', 'abcdef'):
            self.assertNotIn(secret, text)

    def test_lifecycle_threads_warnings_and_caught_exceptions(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = r'''
import sys, threading, warnings, logging
from core.diagnostics import install, attach_root
log = install(sys.argv[1])
attach_root()
warnings.warn('diagnostic warning')
def failed():
    raise RuntimeError('thread-failure-marker')
t = threading.Thread(target=failed); t.start(); t.join()
try:
    raise ValueError('caught-failure-marker')
except ValueError:
    logging.getLogger('module').debug('caught at DEBUG', exc_info=True)
log.info('normal shutdown marker')
'''
            result = subprocess.run([sys.executable, '-c', script, tmp], cwd=ROOT, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            text = (Path(tmp) / 'logs' / 'diagnostics.log').read_text()
            for marker in ('PROCESS START', 'diagnostic warning', 'thread-failure-marker', 'caught-failure-marker', 'Traceback', 'normal shutdown marker', 'PROCESS EXIT'):
                self.assertIn(marker, text)
            combined = (Path(tmp) / 'logs' / 'errors.log').read_text()
            for marker in ('thread-failure-marker', 'caught-failure-marker', 'diagnostic warning', 'Traceback'):
                self.assertIn(marker, combined)

    def test_early_import_failure_logged_without_qt(self):
        with tempfile.TemporaryDirectory() as tmp:
            script = 'from core.diagnostics import install; install(%r); import definitely_missing_mailoffer_module' % tmp
            result = subprocess.run([sys.executable, '-c', script], cwd=ROOT, capture_output=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('ModuleNotFoundError', (Path(tmp) / 'logs' / 'diagnostics.log').read_text())
            self.assertIn('ModuleNotFoundError', (Path(tmp) / 'logs' / 'errors.log').read_text())
