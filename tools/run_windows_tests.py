"""Expose Windows script-test failures as CI annotations as well as console output."""
from pathlib import Path
import subprocess
import sys
import unittest

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
except Exception:
    pass

root = Path(__file__).resolve().parents[1]

if len(sys.argv) >= 2 and sys.argv[1] == '--inner':
    pattern = sys.argv[2] if len(sys.argv) > 2 else 'test_windows_launcher.py'
    sys.path.insert(0, str(root))
    suite = unittest.defaultTestLoader.discover(str(root / 'tests'), pattern=pattern)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    for _, text in result.errors + result.failures:
        escaped = text.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print('::error::' + escaped, flush=True)
    raise SystemExit(0 if result.wasSuccessful() else 1)

pattern = sys.argv[1] if len(sys.argv) > 1 else 'test_windows_launcher.py'
proc = subprocess.run(
    [sys.executable, str(Path(__file__).resolve()), '--inner', pattern],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding='utf-8',
    errors='backslashreplace',
)
output = proc.stdout or ''
sys.stdout.write(output)
sys.stdout.flush()
if proc.returncode != 0 and '::error::' not in output:
    tail = output[-3500:].replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    hex_code = hex(proc.returncode & 0xFFFFFFFF)
    print(f'::error::{pattern} exited with code {proc.returncode} ({hex_code}):%0A{tail}', flush=True)
raise SystemExit(proc.returncode)
