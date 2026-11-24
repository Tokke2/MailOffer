"""Expose Windows script-test failures as CI annotations as well as console output."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
except Exception:
    pass

root = Path(__file__).resolve().parents[1]


def _ascii_workflow_arg(text: str, limit: int = 800) -> str:
    safe = text.encode('ascii', 'backslashreplace').decode('ascii')
    safe = safe[-limit:] if len(safe) > limit else safe
    return safe.replace('%', '%25').replace('\r', '').replace('\n', '%0A')


if len(sys.argv) >= 3 and sys.argv[1] == '--inner':
    report_path = Path(sys.argv[2])
    pattern = sys.argv[3] if len(sys.argv) > 3 else 'test_windows_launcher.py'
    sys.path.insert(0, str(root))
    suite = unittest.defaultTestLoader.discover(str(root / 'tests'), pattern=pattern)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    items = [
        {'test': str(case), 'traceback': text}
        for case, text in (result.errors + result.failures)
    ]
    report_path.write_text(json.dumps(items), encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)

pattern = sys.argv[1] if len(sys.argv) > 1 else 'test_windows_launcher.py'
with tempfile.TemporaryDirectory() as tmp:
    report_file = Path(tmp) / 'report.json'
    proc = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), '--inner', str(report_file), pattern],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='backslashreplace',
    )
    output = proc.stdout or ''
    sys.stdout.write(output)
    if not output.endswith('\n'):
        sys.stdout.write('\n')
    sys.stdout.flush()

    reported = []
    if report_file.is_file():
        try:
            reported = json.loads(report_file.read_text(encoding='utf-8'))
        except Exception:
            reported = []

    for item in reported:
        title = _ascii_workflow_arg(f"{pattern}: {item.get('test', '')}", 120)
        body = _ascii_workflow_arg(item.get('traceback', ''), 850)
        print(f'::error title={title}::{body}', flush=True)

    if proc.returncode != 0 and not reported:
        hex_code = hex(proc.returncode & 0xFFFFFFFF)
        body = _ascii_workflow_arg(output, 850)
        print(
            f'::error title=EXIT {pattern} ({proc.returncode} / {hex_code})::{body}',
            flush=True,
        )

raise SystemExit(proc.returncode)
