"""Expose native smoke-test failures as CI annotations as well as console output."""
from pathlib import Path
import sys
import unittest
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))
suite = unittest.defaultTestLoader.discover(str(root / 'tests'), pattern='test_native_host.py')
result = unittest.TextTestRunner(verbosity=2).run(suite)
for _, text in result.errors + result.failures:
    print('::error::' + text.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A'))
raise SystemExit(0 if result.wasSuccessful() else 1)
