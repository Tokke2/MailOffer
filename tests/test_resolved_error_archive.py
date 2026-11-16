from datetime import date
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from zipfile import ZipFile
from core.open_errors import record_error, open_issues, resolve_issues


class ResolvedArchiveTests(unittest.TestCase):
    def test_selected_archived_removed_and_recurrence_reopens(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record_error(root, 'app.log', 'ERROR first problem')
            record_error(root, 'startup.log', 'ERROR second problem')
            key = next(row[0] for row in open_issues(root) if 'first problem' in row[2])
            resolve_issues(root, [key])
            self.assertEqual(len(open_issues(root)), 1)
            self.assertNotIn('first problem', (root / 'errors.log').read_text())
            files = list((root / 'archive' / date.today().isoformat()).glob('resolved-errors.log-*.zip'))
            self.assertEqual(len(files), 1)
            with ZipFile(files[0]) as z:
                text = z.read('resolved-errors.log').decode()
                self.assertIn('first problem', text)
                self.assertNotIn('second problem', text)
            record_error(root, 'app.log', 'ERROR first problem')
            self.assertEqual(len(open_issues(root)), 2)

    def test_archive_failure_keeps_issue_open(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            record_error(root, 'app.log', 'ERROR preserve me')
            key = open_issues(root)[0][0]
            with mock.patch('core.log_archive.snapshot', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    resolve_issues(root, [key])
            self.assertEqual(len(open_issues(root)), 1)
            self.assertIn('preserve me', (root / 'errors.log').read_text())
