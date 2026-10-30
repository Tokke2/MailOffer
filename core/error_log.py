"""Incremental, local-only collection of errors from the app's log files."""
from __future__ import annotations

import atexit
from contextlib import contextmanager
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
import threading

NAME = 'errors.log'
MAX_SIZE = 5 * 1024 * 1024
MAX_READ = 1024 * 1024
_HEADER = re.compile(r'^(?:\d{4}-\d\d-\d\d[ T]\d\d:\d\d:\d\d|[^|\n]{8,40}\s\|)')
_RAW_HEADER = re.compile(r'^\[?(?:ERROR|CRITICAL|FATAL|WARNING|INFO|DEBUG|TRACE)\b', re.I)
_LEVEL = re.compile(r'\|\s*(ERROR|CRITICAL|FATAL|WARNING)\s*\|', re.I)
_TRACE = re.compile(r'Traceback \(most recent call last\)|Fatal Python error|\b\w*(?:Error|Exception):|Unhandled .*exception', re.I)


def redact(text):
    # Keep output readable, but never intentionally copy credential values.
    text = re.sub(r'''(?ix)((?:password|passwd|token|authorization|secret)["']?\s*[=:]\s*)(?:(?:Bearer|Basic)\s+\S+|"[^"\n]*"|'[^'\n]*'|[^\s,;]+)''', r'\1[REDACTED]', text)
    return re.sub(r'(?i)(AUTH\s+(?:PLAIN|LOGIN)\s+)\S+', r'\1[REDACTED]', text)


def is_error(text, source):
    if source.startswith(('native-crash-', 'startup_crash', 'low_level_crash')):
        return bool(text.strip())
    if _LEVEL.search(text) or _TRACE.search(text):
        return True
    if 'launcher' in source.lower():
        # Successful "exit code=0; script error=0" must not become an error.
        for value in re.findall(r'(?:exit code|script error|error)\s*=\s*(-?\d+)', text, re.I):
            if int(value):
                return True
        value = re.search(r'Launch error=(.*)', text, re.I)
        return bool(value and value.group(1).strip() not in ('', '0'))
    return bool(re.search(r'(?:^\s*|\[)(?:ERROR|CRITICAL|FATAL|WARNING)\b', text, re.I))


@contextmanager
def _locked(directory):
    """OS releases this lock even if the process crashes."""
    with (directory / 'errors.lock').open('a+b') as stream:
        if os.name == 'nt':
            import msvcrt
            if stream.seek(0, 2) == 0:
                stream.write(b'0')
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            if os.name == 'nt':
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


class ErrorLogCollector:
    def __init__(self, base, output_dir=None, *, fallback_dir=None, launcher_fallback=None):
        self.base = Path(base)
        self.directory = Path(output_dir or self.base / 'logs')
        self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / NAME
        self.state_path = self.directory / 'errors.state.json'
        fallback = Path(fallback_dir or Path(tempfile.gettempdir()) / 'MailOffer-logs')
        self.inputs = list(dict.fromkeys([self.base / 'logs', fallback, self.directory]))
        self.launcher_fallback = Path(launcher_fallback or Path(tempfile.gettempdir()) / 'MailOffer-launcher.log')
        self._stop = threading.Event()
        self._thread = None
        self._mutex = threading.RLock()

    def _sources(self):
        found = set()
        for directory in self.inputs:
            if directory.is_symlink():
                continue
            for path in directory.glob('*.log*'):
                if re.fullmatch(r'.+\.log(?:\.\d+)?', path.name) and not path.name.startswith('errors.log'):
                    if path.is_file() and not path.is_symlink():
                        found.add(path)
        if self.launcher_fallback.is_file() and not self.launcher_fallback.is_symlink():
            found.add(self.launcher_fallback)
        return sorted(found, key=lambda p: (p.stat().st_mtime, str(p)))[-128:]

    def _append(self, source, text):
        if self.path.is_symlink():
            raise OSError('Combined error log must not be a symbolic link')
        text = redact(text)
        if len(text) > 128 * 1024:
            text = text[:64 * 1024] + '\n[TRUNCATED]\n' + text[-64 * 1024:]
        data = (f'\n=== Collected {datetime.now().isoformat(timespec="seconds")} | source={source} ===\n' + text.rstrip() + '\n').encode('utf-8')
        if self.path.exists() and self.path.stat().st_size + len(data) > MAX_SIZE:
            for number in range(5, 0, -1):
                previous = self.path if number == 1 else self.path.with_name(NAME + f'.{number - 1}')
                target = self.path.with_name(NAME + f'.{number}')
                if previous.exists():
                    os.replace(previous, target)
        with self.path.open('ab') as stream:
            stream.write(data)
            stream.flush()

    def collect(self, *, final=False):
        """One bounded pass. Original logs are read only; output is never an input."""
        with self._mutex, _locked(self.directory):
            try:
                state = json.loads(self.state_path.read_text(encoding='utf-8'))
                if not isinstance(state, dict):
                    state = {}
            except (OSError, ValueError):
                state = {}
            original_state = dict(state)
            count = 0
            active = {}
            for source in self._sources():
                key = None
                try:
                    info = source.stat()
                    key = f'{info.st_dev}:{info.st_ino}' if info.st_ino else str(source.resolve())
                    previous = state.get(key, {})
                    if not isinstance(previous, dict):
                        previous = {}
                    if not info.st_size:
                        continue
                    if (not isinstance(previous.get('offset', 0), int) or previous.get('offset', 0) < 0
                            or not isinstance(previous.get('prefix_length', 1), int)
                            or not 1 <= previous.get('prefix_length', 1) <= 64):
                        previous = {}
                    with source.open('rb') as stream:
                        prefix_length = int(previous.get('prefix_length', min(info.st_size, 64)))
                        prefix = hashlib.sha256(stream.read(prefix_length)).hexdigest()
                        offset = int(previous.get('offset', 0))
                        continuation = bool(previous.get('continuation', False))
                        if offset > info.st_size or prefix != previous.get('prefix', prefix):
                            offset, continuation = 0, False
                        stream.seek(0)
                        encoding = 'utf-16-le' if stream.read(2) == b'\xff\xfe' else 'utf-8'
                        stream.seek(offset)
                        raw = stream.read(MAX_READ)
                    newline = b'\n\x00' if encoding == 'utf-16-le' else b'\n'
                    end = raw.rfind(newline)
                    consumed = end + len(newline) if end >= 0 else 0
                    if (final and len(raw) < MAX_READ) or (not consumed and len(raw) == MAX_READ):
                        consumed = len(raw)
                        if encoding == 'utf-16-le':
                            consumed -= consumed % 2
                    # Wait for complete lines (including UTF-16 code units).
                    text = raw[:consumed].decode(encoding, errors='replace').lstrip('\ufeff')
                    blocks, block, has_header = [], [], False
                    for line in text.splitlines(keepends=True):
                        if _HEADER.match(line) or _RAW_HEADER.match(line):
                            if block:
                                blocks.append((''.join(block), has_header))
                            block, has_header = [], True
                        block.append(line)
                    if block:
                        blocks.append((''.join(block), has_header))
                    for text, headed in blocks:
                        error = is_error(text, source.name) or (continuation and not headed)
                        if error:
                            self._append(str(source), text)
                            count += 1
                        continuation = error
                    active[key] = dict(offset=offset + consumed, prefix=prefix, prefix_length=prefix_length, continuation=continuation)
                except (OSError, ValueError):
                    if key in state:
                        active[key] = state[key]
            # Retain cursor identities across renames/rotation; no message text is stored.
            for key, value in active.items():
                state.pop(key, None)
                state[key] = value
            state = dict(list(state.items())[-512:])
            if state != original_state or not self.state_path.exists():
                fd, temporary = tempfile.mkstemp(prefix='.errors-state-', dir=self.directory)
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                        json.dump(state, stream)
                    os.replace(temporary, self.state_path)
                finally:
                    Path(temporary).unlink(missing_ok=True)
            if not self.path.exists():
                self.path.touch()
            return count

    def start(self):
        if self._thread is not None:
            return
        def loop():
            while not self._stop.is_set():
                try:
                    self.collect()
                except (OSError, ValueError):
                    pass  # A locked/full disk must not take down the application.
                self._stop.wait(5)
        self._thread = threading.Thread(target=loop, name='ErrorLogCollector', daemon=True)
        self._thread.start()
        atexit.register(self.stop)

    def stop(self):
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=3)
        try:
            self.collect(final=True)
        except (OSError, ValueError):
            pass


if __name__ == '__main__':
    # Optional troubleshooting without importing Qt or starting the app.
    import argparse
    parser = argparse.ArgumentParser(description='Collect MailOffer log errors locally (no Qt).')
    parser.add_argument('--base-dir', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output-dir', type=Path, default=None)
    args = parser.parse_args()
    collector = ErrorLogCollector(args.base_dir, args.output_dir)
    collector.collect(final=True)
    print(collector.path)
