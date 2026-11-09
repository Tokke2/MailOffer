from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import venv

ROOT = Path(__file__).resolve().parents[1]


class SystemPythonProbeTests(unittest.TestCase):
    def test_probe_from_path_with_spaces_without_inline_code(self):
        with tempfile.TemporaryDirectory(prefix='MailOffer probe ') as folder:
            script = Path(folder) / 'Python probe.py'
            shutil.copyfile(ROOT / 'tools/probe_system_python.py', script)
            result = subprocess.run([sys.executable, '-I', str(script)], capture_output=True, text=True, check=True)
            expected = '%d.%d' % sys.version_info[:2] if sys.prefix == sys.base_prefix else 'virtual'
            self.assertEqual(result.stdout.strip(), expected)
            self.assertEqual(result.stderr, '')

    def test_virtual_environment_is_not_system_python(self):
        # A temporary test fixture only; the app never creates environments.
        with tempfile.TemporaryDirectory(prefix='MailOffer test ') as folder:
            venv.EnvBuilder(with_pip=False).create(folder)
            python = Path(folder) / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
            result = subprocess.run([str(python), '-I', str(ROOT / 'tools/probe_system_python.py')], capture_output=True, text=True, check=True)
            self.assertEqual(result.stdout.strip(), 'virtual')

    def test_startup_uses_probe_file_not_quoted_inline_python(self):
        source = (ROOT / 'tools/ensure_python.ps1').read_text()
        self.assertIn("Invoke-PythonCheck $exe (Join-Path $PSScriptRoot 'probe_system_python.py')", source)
        self.assertNotIn(' -c ', source)
