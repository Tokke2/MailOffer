from pathlib import Path
import os
import tempfile
import unittest
from unittest import mock
from core.app_update import _copy_executable


class ExecutableUpdateTests(unittest.TestCase):
    def test_swap_keeps_old_image_and_unchanged_file_needs_no_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, target = base / 'new.exe', base / 'MailOffer.exe'
            source.write_bytes(b'new')
            target.write_bytes(b'old')
            _copy_executable(source, target, base)
            self.assertEqual(target.read_bytes(), b'new')
            backups = list((base / '.data/executable-backups').glob('*.exe'))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_bytes(), b'old')
            _copy_executable(source, target, base)
            self.assertEqual(len(list((base / '.data/executable-backups').glob('*.exe'))), 1)

    def test_failed_final_swap_rolls_back_original(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            source, target = base / 'new.exe', base / 'MailOffer.exe'
            source.write_bytes(b'new')
            target.write_bytes(b'old')
            replace = os.replace
            def fail_staged(src, dst):
                if Path(src).suffix == '.tmp':
                    raise OSError('denied')
                return replace(src, dst)
            with mock.patch('core.app_update.os.replace', side_effect=fail_staged), self.assertRaises(OSError):
                _copy_executable(source, target, base)
            self.assertEqual(target.read_bytes(), b'old')
            self.assertFalse(list(base.glob('*.tmp')))
