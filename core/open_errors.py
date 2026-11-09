"""Persistent unresolved errors: only explicit resolution closes an issue."""
from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import tempfile

NAME = 'errors.log'


def _connect(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(directory / 'error-issues.sqlite3', timeout=10)
    db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)')
    db.execute('CREATE TABLE IF NOT EXISTS issues (id TEXT PRIMARY KEY, source TEXT, message TEXT, first_seen TEXT, last_seen TEXT, count INTEGER, resolved INTEGER)')
    return db


def _render(db, directory):
    fd, temporary = tempfile.mkstemp(prefix='.open-errors-', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            rows = db.execute('SELECT id, source, message, first_seen, last_seen, count FROM issues WHERE resolved=0 ORDER BY last_seen DESC').fetchall()
            if rows:
                stream.write('OPEN ERRORS — mark resolved in the app; do not edit this generated file.\n')
            for row in rows:
                key, source, message, first, last, count = row
                stream.write(f'\n=== ID {key} | source={source} | first={first} | last={last} | count={count} ===\n{message.rstrip()}\n')
        os.replace(temporary, Path(directory) / NAME)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _identity(source, message):
    family = re.sub(r'\.\d+$', '', Path(source).name)
    normalized = re.sub(r'^\d{4}-\d\d-\d\d[ T]\d\d:\d\d:\d\d(?:[,.]\d+)?\s*\|?\s*', '', message, flags=re.M)
    normalized = re.sub(r'pid=\d+', 'pid=*', normalized)
    key = hashlib.sha256((family + '\n' + normalized.strip()).encode()).hexdigest()[:24]
    return family, key


def record_error(directory, source, message):
    from core.error_log import redact
    import_history(directory)
    message = redact(message)
    family, key = _identity(source, message)
    now = datetime.now().isoformat(timespec='seconds')
    db = _connect(directory)
    try:
        with db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('INSERT INTO issues VALUES (?, ?, ?, ?, ?, 1, 0) ON CONFLICT(id) DO UPDATE SET message=excluded.message, last_seen=excluded.last_seen, count=issues.count+1, resolved=0', (key, family, message, now, now))
            _render(db, directory)
    finally:
        db.close()
    return key


def import_history(directory):
    """Migrate retained history and the old generated view without reopening fixes."""
    from core.error_log import redact, is_error
    directory = Path(directory)
    legacy = directory / 'unresolved-errors.log'
    db = _connect(directory)
    try:
        with db:
            db.execute('BEGIN IMMEDIATE')
            migrated = db.execute("SELECT 1 FROM metadata WHERE key='canonical-error-log-v2'").fetchone()
            if not migrated:
                header = re.compile(r'^=== Collected ([^|]+) \| source=(.+) ===$', re.M)
                for path in sorted(directory.glob('errors.log*')):
                    if not re.fullmatch(r'errors\.log(?:\.\d+)?', path.name) or path.is_symlink():
                        continue
                    text = path.read_text(encoding='utf-8-sig', errors='replace')
                    matches = list(header.finditer(text))
                    if matches:
                        from core.log_archive import snapshot
                        snapshot(directory, path.name, datetime.fromtimestamp(path.stat().st_mtime).date(), path.read_bytes())
                    for i, match in enumerate(matches):
                        message = redact(text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)].strip())
                        if not is_error(message, match[2]):
                            continue
                        family, key = _identity(match[2], message)
                        stamp = match[1].strip()
                        db.execute('INSERT OR IGNORE INTO issues VALUES (?, ?, ?, ?, ?, 1, 0)', (key, family, message, stamp, stamp))
            has_legacy = legacy.exists() and not legacy.is_symlink()
            if has_legacy:
                text = legacy.read_text(encoding='utf-8-sig')
                pattern = re.compile(r'^=== ID ([0-9a-f]+) \| source=(.+) \| first=(.+) \| last=(.+) \| count=(\d+) ===$', re.M)
                matches = list(pattern.finditer(text))
                if text.strip() and not matches and (not text.startswith('OPEN ERRORS') or len(text.strip().splitlines()) > 1):
                    raise ValueError('Okänd gammal fellogg; filen lämnas orörd')
                for i, match in enumerate(matches):
                    message = redact(text[match.end():matches[i + 1].start() if i + 1 < len(matches) else len(text)].strip())
                    db.execute('INSERT OR IGNORE INTO issues VALUES (?, ?, ?, ?, ?, ?, 0)', (match[1], match[2], message, match[3], match[4], int(match[5])))
            if not migrated or has_legacy or not (directory / NAME).exists():
                _render(db, directory)
            if not migrated:
                db.execute("INSERT INTO metadata VALUES ('canonical-error-log-v2', '1')")
    finally:
        db.close()
    if legacy.exists() and not legacy.is_symlink():
        legacy.unlink()


def open_issues(directory):
    import_history(directory)
    db = _connect(directory)
    try:
        return db.execute('SELECT id, source, message, first_seen, last_seen, count FROM issues WHERE resolved=0 ORDER BY last_seen DESC').fetchall()
    finally:
        db.close()


def resolve_issues(directory, keys):
    db = _connect(directory)
    try:
        with db:
            db.execute('BEGIN IMMEDIATE')
            db.executemany('UPDATE issues SET resolved=1 WHERE id=?', [(key,) for key in keys])
            _render(db, directory)
    finally:
        db.close()
