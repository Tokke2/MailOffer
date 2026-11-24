"""Expose Windows script-test failures as CI annotations as well as console output."""
import faulthandler
import json
import mmap
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
    sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    faulthandler.enable()
except Exception:
    pass

root = Path(__file__).resolve().parents[1]


def _ascii_workflow_arg(text: str, limit: int = 800) -> str:
    safe = text.encode('ascii', 'backslashreplace').decode('ascii')
    safe = safe[-limit:] if len(safe) > limit else safe
    return safe.replace('%', '%25').replace('\r', '').replace('\n', '%0A')


if len(sys.argv) >= 4 and sys.argv[1] == '--inner':
    report_path = Path(sys.argv[2])
    crumb_path = Path(sys.argv[3])
    pattern = sys.argv[4] if len(sys.argv) > 4 else 'test_windows_launcher.py'
    sys.path.insert(0, str(root))

    crumb_file = crumb_path.open('wb+')
    crumb_file.write(b' ' * 4096)
    crumb_file.flush()
    crumb_map = mmap.mmap(crumb_file.fileno(), 4096)
    ring = [''] * 12
    idx = 0

    def _profiler(frame, event, _arg):
        global idx
        if event not in ('call', 'c_call'):
            return
        code = frame.f_code
        fn = code.co_filename
        if 'MailOffer' not in fn and event != 'c_call':
            return
        entry = f"{event}:{Path(fn).name}:{frame.f_lineno}:{code.co_name}"
        if event == 'c_call' and _arg is not None:
            entry += f"->{getattr(_arg, '__name__', repr(_arg))}"
        ring[idx % 12] = entry
        idx += 1
        ordered = ' | '.join(ring[(idx + i) % 12] for i in range(12) if ring[(idx + i) % 12])
        raw = ordered.encode('ascii', 'backslashreplace')[:4090]
        crumb_map.seek(0)
        crumb_map.write(raw.ljust(4096, b' '))

    sys.setprofile(_profiler)
    try:
        suite = unittest.defaultTestLoader.discover(str(root / 'tests'), pattern=pattern)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
    finally:
        sys.setprofile(None)
        crumb_map.close()
        crumb_file.close()

    items = [
        {'test': str(case), 'traceback': text}
        for case, text in (result.errors + result.failures)
    ]
    report_path.write_text(json.dumps(items), encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)

pattern = sys.argv[1] if len(sys.argv) > 1 else 'test_windows_launcher.py'
with tempfile.TemporaryDirectory() as tmp:
    report_file = Path(tmp) / 'report.json'
    crumb_file = Path(tmp) / 'crumb.mmap'
    proc = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            '--inner',
            str(report_file),
            str(crumb_file),
            pattern,
        ],
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
        crumbs = ''
        if crumb_file.is_file():
            try:
                crumbs = crumb_file.read_bytes().decode('ascii', 'replace').strip()
            except Exception:
                crumbs = ''
        body = _ascii_workflow_arg(f"{output}\nCRUMBS: {crumbs}", 880)
        print(
            f'::error title=EXIT {pattern} ({proc.returncode} / {hex_code})::{body}',
            flush=True,
        )

raise SystemExit(proc.returncode)
