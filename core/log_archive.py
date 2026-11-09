"""Verified daily archives, then compact active logs to today's records.

Windows obtains exclusive write access after closing our locked log handlers.
Busy external writers are skipped and retried, never truncated underneath them.
"""
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, datetime, timedelta
import hashlib
import logging
import os
from pathlib import Path
import re
import shutil
import tempfile
import zipfile

RETENTION_DAYS = 7
_ARCHIVE_NAME = re.compile(r'.+\.log(?:\.\d+)?-[0-9a-f]{16}\.zip')
_reported_skips = set()
_DATE = re.compile(r'^(?:=== Collected )?(\d{4}-\d{2}-\d{2})(?:[ T]|$)')


def snapshot(directory, name, day, data):
    folder = Path(directory) / 'archive' / day.isoformat()
    if folder.parent.is_symlink() or folder.is_symlink():
        raise OSError('Arkivet får inte vara en symbolisk länk')
    folder.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()[:16]
    target = folder / (name + '-' + digest + '.zip')
    if target.exists():
        with zipfile.ZipFile(target) as archive:
            if archive.read(name) != data:
                raise ValueError('Arkivkontrollen misslyckades: ' + str(target))
        return None
    fd, temporary = tempfile.mkstemp(prefix='.archive-', suffix='.tmp', dir=folder)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(name, data)
        with zipfile.ZipFile(temporary) as archive:
            if archive.read(name) != data:
                raise ValueError('Arkivet kunde inte verifieras')
        os.replace(temporary, target)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return target


@contextmanager
def _exclusive(source):
    handlers = []
    # FileHandler locks pause emit() and QueueListener writes during compaction.
    for ref in list(logging._handlerList):
        handler = ref()
        if isinstance(handler, logging.FileHandler) and Path(handler.baseFilename).resolve() == source.resolve():
            handlers.append(handler)
    handlers.sort(key=id)
    held = []
    stream = None
    try:
        for handler in handlers:
            handler.acquire()
            held.append(handler)
            if handler.stream is not None:
                handler.flush()
                handler.stream.close()
                handler.stream = None
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            import msvcrt
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
            kernel.CreateFileW.restype = wintypes.HANDLE
            handle = kernel.CreateFileW(str(source), 0xC0000000, 1, None, 3, 0x80, None)
            if handle == ctypes.c_void_p(-1).value:
                code = ctypes.get_last_error()
                if code in (5, 32, 33):
                    yield None  # an external writer/reader is using the file
                    return
                raise ctypes.WinError(code)
            try:
                fd = msvcrt.open_osfhandle(handle, os.O_RDWR | os.O_BINARY)
            except Exception:
                kernel.CloseHandle.argtypes = [wintypes.HANDLE]
                kernel.CloseHandle(handle)
                raise
            stream = os.fdopen(fd, 'r+b')
        else:
            import fcntl
            try:
                stream = source.open('r+b')
            except PermissionError:
                yield None
                return
            try:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield None
                return
        yield stream
    finally:
        if stream is not None:
            stream.close()
        for handler in reversed(held):
            # Lazy reopening on emit avoids keeping unnecessary handles alive.
            handler.release()


def archive_logs(directory, today=None, *, eligible=None, prepared=None, rewritten=None):
    directory = Path(directory)
    today = today or date.today()
    root = directory / 'archive'
    if root.is_symlink():
        raise OSError('Loggarkivet får inte vara en symbolisk länk')
    archived = []
    skipped = set()
    for source in sorted(directory.glob('*.log*')):
        if source.name in ('errors.log', 'unresolved-errors.log', 'resolved-errors.log'):
            continue  # open errors never expire
        if not re.fullmatch(r'.+\.log(?:\.\d+)?', source.name) or source.is_symlink() or not source.is_file():
            continue
        if source.name == f'native-crash-{os.getpid()}.log':
            continue  # faulthandler owns this live descriptor
        if source.stat().st_size > 50 * 1024 * 1024:
            skipped.add((source.name, 'filen är större än 50 MB'))
            continue
        with _exclusive(source) as stream:
            if stream is None:
                skipped.add((source.name, 'filen används eller saknar skrivbehörighet; nytt försök senare'))
                continue
            raw = stream.read(50 * 1024 * 1024 + 1)
            if len(raw) > 50 * 1024 * 1024:
                skipped.add((source.name, 'filen är större än 50 MB'))
                continue
            if eligible is not None and not eligible(source, raw):
                continue  # collector must persist all errors before removing source records
            encoding = 'utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig'
            try:
                text = raw.decode(encoding, errors='strict')
            except UnicodeDecodeError:
                skipped.add((source.name, 'okänd/skadad textkodning; originalet lämnas orört'))
                continue  # never rewrite undecodable bytes or a partial UTF sequence
            current = datetime.fromtimestamp(source.stat().st_mtime).date()
            groups, kept = defaultdict(list), []
            for line in text.splitlines(keepends=True):
                match = _DATE.match(line)
                if match:
                    try:
                        current = date.fromisoformat(match[1])
                    except ValueError:
                        pass
                if current < today:
                    groups[current].append(line)
                else:
                    kept.append(line)  # keep future-dated records too; never silently lose them
            if not groups:
                continue
            for day, lines in groups.items():
                path = snapshot(directory, source.name, day, ''.join(lines).encode('utf-8'))
                if path:
                    archived.append(path)
            content = ''.join(kept)
            if encoding == 'utf-16':
                endian = 'utf-16-le' if raw.startswith(b'\xff\xfe') else 'utf-16-be'
                remaining = raw[:2] + content.encode(endian)
            else:
                remaining = (b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'') + content.encode('utf-8')
            # Stage and fsync the complete retained text before replacing the name.
            # A crash can leave the old OR the new file, not a half-truncated log.
            fd, staged = tempfile.mkstemp(prefix='.daily-log-', suffix='.tmp', dir=directory)
            try:
                with os.fdopen(fd, 'wb') as output:
                    output.write(remaining)
                    output.flush()
                    os.fsync(output.fileno())
                shutil.copystat(source, staged)
                if prepared is not None:
                    prepared(source, Path(staged), remaining)
                stream.close()
                # Windows refuses replacement if an external app writer opened the
                # file meanwhile. Leave the original intact and retry later.
                try:
                    os.replace(staged, source)
                except PermissionError:
                    skipped.add((source.name, 'filen används eller saknar skrivbehörighet; nytt försök senare'))
                    continue
            finally:
                Path(staged).unlink(missing_ok=True)
            if rewritten is not None:
                rewritten(source, remaining)
    _prune_archives(root, today - timedelta(days=RETENTION_DAYS))
    global _reported_skips
    for name, reason in sorted(skipped - _reported_skips):
        report = logging.getLogger(__name__).info if "filen används" in reason else logging.getLogger(__name__).warning
        report("Arkivering uppskjuten för %s: %s", name, reason)
    _reported_skips = skipped
    return [path for path in archived if path.exists()]


def _prune_archives(root, cutoff):
    if not root.exists():
        return
    for folder in root.iterdir():
        if folder.is_symlink() or not folder.is_dir():
            continue
        try:
            day = date.fromisoformat(folder.name)
        except ValueError:
            continue
        if folder.name != day.isoformat() or day >= cutoff:
            continue
        for path in folder.iterdir():
            if _ARCHIVE_NAME.fullmatch(path.name) and not path.is_symlink() and path.is_file():
                path.unlink()
        if not any(folder.iterdir()):
            folder.rmdir()
