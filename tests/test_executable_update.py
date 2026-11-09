"""Script-only updates must never install executable files."""
from pathlib import Path
import tempfile
import unittest
from core.app_update import apply_update_from_dir

class ExecutableUpdateTests(unittest.TestCase):
    def test_executables_are_not_copied(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source'
            dest = Path(folder) / 'dest'
            source.mkdir()
            (source / 'unexpected.EXE').write_bytes(b'MZ')
            (source / 'main.pyw').write_text('# script')
            result = apply_update_from_dir(source, dest)
            self.assertFalse((dest / 'unexpected.EXE').exists())
            self.assertTrue((dest / 'main.pyw').exists())
            self.assertIn('unexpected.EXE', result['skipped'])
