"""Daily immutable snapshots of previous dated log entries; never truncate writers."""
from collections import defaultdict
from datetime import date, datetime, timedelta
import hashlib
from pathlib import Path
import re
import os
import tempfile
import zipfile

RETENTION_DAYS = 7
_ARCHIVE_NAME = re.compile(r'.+\.log(?:\.\d+)?-[0-9a-f]{16}\.zip')

_DATE = re.compile(r'^(?:=== Collected )?(\d{4}-\d{2}-\d{2})(?:[ T]|$)')


def archive_logs(directory, today=None):
    directory = Path(directory)
    today = today or date.today()
    cutoff = today - timedelta(days=RETENTION_DAYS)
    root = directory / 'archive'
    if root.is_symlink():
        raise OSError("Loggarkivet får inte vara en symbolisk länk")
    archived = []
    for source in sorted(directory.glob('*.log*')):
        if source.name.startswith(('unresolved-errors.log', 'resolved-errors.log')):
            continue
        if not re.fullmatch(r'.+\.log(?:\.\d+)?', source.name) or source.is_symlink() or not source.is_file():
            continue
        info = source.stat()
        if info.st_size > 50 * 1024 * 1024:
            continue
        raw = source.read_bytes()
        text = raw.decode('utf-16' if raw.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig', errors='replace')
        current = datetime.fromtimestamp(info.st_mtime).date()
        groups = defaultdict(list)
        for line in text.splitlines(keepends=True):
            match = _DATE.match(line)
            if match:
                try:
                    current = date.fromisoformat(match[1])
                except ValueError:
                    pass
            if cutoff <= current < today:
                groups[current].append(line)
        for day, lines in groups.items():
            data = ''.join(lines).encode('utf-8')
            digest = hashlib.sha256(data).hexdigest()
            folder = directory / 'archive' / day.isoformat()
            if folder.is_symlink():
                raise OSError("Arkivets datumkatalog får inte vara en symbolisk länk")
            folder.mkdir(parents=True, exist_ok=True)
            target = folder / (source.name + '-' + digest[:16] + '.zip')
            if target.exists():
                with zipfile.ZipFile(target) as previous:
                    if previous.read(source.name) != data:
                        raise ValueError('Arkivkontrollen misslyckades: ' + str(target))
                continue
            fd, name = tempfile.mkstemp(prefix='.archive-', suffix='.tmp', dir=folder)
            os.close(fd)
            temporary = Path(name)
            try:
                with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr(source.name, data)
                with zipfile.ZipFile(temporary) as archive:
                    if archive.read(source.name) != data:
                        raise ValueError('Arkivet kunde inte verifieras')
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
            archived.append(target)
    _prune_archives(root, cutoff)
    return archived


def _prune_archives(root, cutoff):
    """Delete only generated ZIPs in expired ISO-date folders, never source logs."""
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
