"""Script-only updates must never install or compare binary/installer executables."""
from pathlib import Path
import tempfile
import unittest
from core.app_update import BLOCKED_BINARY_SUFFIXES, apply_update_from_dir
from core.github_update import compare_release_files


class ExecutableUpdateTests(unittest.TestCase):
    def test_executables_and_native_binaries_are_not_copied_or_diffed(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source'
            dest = Path(folder) / 'dest'
            source.mkdir()
            for suffix in sorted(BLOCKED_BINARY_SUFFIXES):
                (source / f'unexpected{suffix.upper()}').write_bytes(b'MZ')
            (source / 'main.pyw').write_text('# script\n', encoding='utf-8')
            result = apply_update_from_dir(source, dest)
            for suffix in sorted(BLOCKED_BINARY_SUFFIXES):
                name = f'unexpected{suffix.upper()}'
                self.assertFalse((dest / name).exists())
                self.assertIn(name, result['skipped'])
            self.assertTrue((dest / 'main.pyw').exists())
            # Post-install hash comparison must agree and report zero mismatches
            self.assertEqual(compare_release_files(source, dest), [])
