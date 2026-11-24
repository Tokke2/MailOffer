"""Persistent unresolved errors with verified archiving & automatic post-fix cleanup."""
from __future__ import annotations

from datetime import datetime
import hashlib
import os
from pathlib import Path
import re
import sqlite3
import tempfile
from typing import Iterable, List, Optional, Sequence

NAME = 'errors.log'


def _current_build_id() -> str:
    try:
        from core.version import BUILD_ID
        return str(BUILD_ID or '').strip()
    except Exception:
        return ''


def classify_issue_category(source: str, message: str) -> str:
    """Classify an error record so verified runtime recovery can auto-clean it."""
    family = re.sub(r'\.\d+$', '', Path(str(source or '')).name).lower()
    low = (message or '').lower()
    if (
        'kunde inte översätta placeholder' in low
        or 'deep_translator' in low
        or 'googletranslator' in low
        or 'translate_batch' in low
    ):
        return 'placeholder_translation'
    if '_do_show misslyckades' in low or 'window_focus' in low:
        return 'tray_window'
    if 'github_update' in low or 'updateworker' in low or 'uppdateringskontroll' in low:
        return 'github_update'
    if (
        'core.email_sender' in low
        or 'smtp' in low
        or 'sendworker' in low
        or 'sändning misslyckades' in low
    ):
        return 'smtp_send'
    if (
        family in ('startup.log', 'launcher.log', 'startup_crash.log')
        or 'python startup check' in low
        or 'launch error=' in low
    ):
        return 'startup'
    return 'general'


def _connect(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    db_path = directory / 'error-issues.sqlite3'
    existed_before = db_path.exists() and db_path.stat().st_size > 0
    db = sqlite3.connect(db_path, timeout=10)
    cur_build = _current_build_id()
    db.execute('CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT)')
    db.execute(
        'CREATE TABLE IF NOT EXISTS issues ('
        'id TEXT PRIMARY KEY, source TEXT, message TEXT, '
        'first_seen TEXT, last_seen TEXT, count INTEGER, resolved INTEGER, '
        "build_id TEXT DEFAULT '', category TEXT DEFAULT 'general')"
    )
    cols = {row[1] for row in db.execute('PRAGMA table_info(issues)').fetchall()}
    upgraded_pre_build_tracking = False
    if 'build_id' not in cols:
        db.execute("ALTER TABLE issues ADD COLUMN build_id TEXT DEFAULT 'pre-2026102362'")
        upgraded_pre_build_tracking = True
    if 'category' not in cols:
        db.execute("ALTER TABLE issues ADD COLUMN category TEXT DEFAULT ''")

    missing_cat = db.execute(
        "SELECT id, source, message FROM issues WHERE category IS NULL OR category=''"
    ).fetchall()
    if missing_cat:
        db.executemany(
            'UPDATE issues SET category=? WHERE id=?',
            [(classify_issue_category(src, msg), key) for key, src, msg in missing_cat],
        )

    if upgraded_pre_build_tracking:
        db.execute(
            "INSERT OR IGNORE INTO metadata VALUES ('last_verified_build_id', 'pre-2026102362')"
        )
    elif not existed_before and cur_build:
        db.execute(
            "INSERT OR IGNORE INTO metadata VALUES ('last_verified_build_id', ?)",
            (cur_build,),
        )
    db.commit()
    return db


def _render(db, directory):
    fd, temporary = tempfile.mkstemp(prefix='.open-errors-', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            rows = db.execute(
                'SELECT id, source, message, first_seen, last_seen, count '
                'FROM issues WHERE resolved=0 ORDER BY last_seen DESC'
            ).fetchall()
            if rows:
                stream.write(
                    'OPEN ERRORS — active unfixed errors (automatically cleaned after verified fix; do not edit manually).\n'
                )
            for row in rows:
                key, source, message, first, last, count = row
                stream.write(
                    f'\n=== ID {key} | source={source} | first={first} | last={last} | count={count} ===\n{message.rstrip()}\n'
                )
        os.replace(temporary, Path(directory) / NAME)
    finally:
        Path(temporary).unlink(missing_ok=True)


def _identity(source, message):
    family = re.sub(r'\.\d+$', '', Path(source).name)
    message = message.replace('\r\n', '\n').replace('\r', '\n')
    normalized = re.sub(
        r'^\d{4}-\d\d-\d\d[ T]\d\d:\d\d:\d\d(?:[,.]\d+)?\s*\|?\s*',
        '',
        message,
        flags=re.M,
    )
    normalized = re.sub(r'pid=\d+', 'pid=*', normalized)
    key = hashlib.sha256((family + '\n' + normalized.strip()).encode()).hexdigest()[:24]
    return family, key


def record_error(directory, source, message, *, build_id: Optional[str] = None):
    from core.error_log import redact

    import_history(directory)
    message = redact(message)
    family, key = _identity(source, message)
    now = datetime.now().isoformat(timespec='seconds')
    eff_build = _current_build_id() if build_id is None else str(build_id)
    category = classify_issue_category(family, message)
    db = _connect(directory)
    try:
        with db:
            db.execute('BEGIN IMMEDIATE')
            db.execute(
                'INSERT INTO issues (id, source, message, first_seen, last_seen, count, resolved, build_id, category) '
                'VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?) '
                'ON CONFLICT(id) DO UPDATE SET '
                'message=excluded.message, last_seen=excluded.last_seen, '
                'count=issues.count+1, resolved=0, '
                'build_id=excluded.build_id, category=excluded.category',
                (key, family, message, now, now, eff_build, category),
            )
            _render(db, directory)
    finally:
        db.close()
    return key


def _normalize_legacy_ids(db):
    # Old Windows collectors hashed CRLF, while history reads normalized LF.
    # Re-key stored issues FIRST so importing history cannot reopen fixed issues.
    rows = db.execute(
        'SELECT id, source, message, first_seen, last_seen, count, resolved FROM issues'
    ).fetchall()
    for old, source, message, first, last, count, resolved in rows:
        _, key = _identity(source, message)
        if key == old:
            continue
        prior = db.execute(
            'SELECT first_seen, last_seen, count, resolved FROM issues WHERE id=?',
            (key,),
        ).fetchone()
        if prior:
            db.execute(
                'UPDATE issues SET first_seen=?, last_seen=?, count=?, resolved=? WHERE id=?',
                (
                    min(first, prior[0]),
                    max(last, prior[1]),
                    count + prior[2],
                    min(resolved, prior[3]),
                    key,
                ),
            )
            db.execute('DELETE FROM issues WHERE id=?', (old,))
        else:
            db.execute('UPDATE issues SET id=? WHERE id=?', (key, old))


def _import_generated(db, text):
    from core.error_log import redact

    pattern = re.compile(
        r'^=== ID ([0-9a-f]+) \| source=(.+) \| first=(.+) \| last=(.+) \| count=(\d+) ===$',
        re.M,
    )
    matches = list(pattern.finditer(text))
    if (
        text.strip()
        and not matches
        and (not text.startswith('OPEN ERRORS') or len(text.strip().splitlines()) > 1)
    ):
        raise ValueError('Okänd gammal fellogg; filen lämnas orörd')
    cur_build = _current_build_id()
    for i, match in enumerate(matches):
        message = redact(
            text[
                match.end() : matches[i + 1].start()
                if i + 1 < len(matches)
                else len(text)
            ].strip()
        )
        family, key = _identity(match[2], message)
        category = classify_issue_category(family, message)
        db.execute(
            'INSERT OR IGNORE INTO issues '
            '(id, source, message, first_seen, last_seen, count, resolved, build_id, category) '
            'VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)',
            (key, family, message, match[3], match[4], int(match[5]), cur_build, category),
        )


def import_history(directory):
    """Migrate retained history and the old generated view without reopening fixes."""
    from core.error_log import is_error, redact

    directory = Path(directory)
    legacy = directory / 'unresolved-errors.log'
    db = _connect(directory)
    cur_build = _current_build_id()
    try:
        with db:
            db.execute('BEGIN IMMEDIATE')
            migrated = db.execute(
                "SELECT 1 FROM metadata WHERE key='canonical-error-log-v2'"
            ).fetchone()
            if not migrated:
                _normalize_legacy_ids(db)
                header = re.compile(r'^=== Collected ([^|]+) \| source=(.+) ===$', re.M)
                for path in sorted(directory.glob('errors.log*')):
                    if (
                        not re.fullmatch(r'errors\.log(?:\.\d+)?', path.name)
                        or path.is_symlink()
                    ):
                        continue
                    text = path.read_text(encoding='utf-8-sig', errors='replace')
                    matches = list(header.finditer(text))
                    if not matches and text.startswith('OPEN ERRORS'):
                        _import_generated(db, text)
                    if matches:
                        from core.log_archive import snapshot

                        snapshot(
                            directory,
                            path.name,
                            datetime.fromtimestamp(path.stat().st_mtime).date(),
                            path.read_bytes(),
                        )
                    for i, match in enumerate(matches):
                        message = redact(
                            text[
                                match.end() : matches[i + 1].start()
                                if i + 1 < len(matches)
                                else len(text)
                            ].strip()
                        )
                        if not is_error(message, match[2]):
                            continue
                        family, key = _identity(match[2], message)
                        stamp = match[1].strip()
                        category = classify_issue_category(family, message)
                        db.execute(
                            'INSERT OR IGNORE INTO issues '
                            '(id, source, message, first_seen, last_seen, count, resolved, build_id, category) '
                            'VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?)',
                            (key, family, message, stamp, stamp, cur_build, category),
                        )
            has_legacy = legacy.exists() and not legacy.is_symlink()
            if has_legacy:
                text = legacy.read_text(encoding='utf-8-sig')
                _import_generated(db, text)
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
        return db.execute(
            'SELECT id, source, message, first_seen, last_seen, count '
            'FROM issues WHERE resolved=0 ORDER BY last_seen DESC'
        ).fetchall()
    finally:
        db.close()


def resolve_issues(directory, keys, *, reason: str = 'explicitly marked resolved'):
    db = _connect(directory)
    try:
        with db:
            db.execute('BEGIN IMMEDIATE')
            # Archive exact selected open rows while holding the write transaction.
            # If backup creation/verification fails, no issue is closed.
            rows = []
            for key in dict.fromkeys(keys):
                row = db.execute(
                    'SELECT id, source, message, first_seen, last_seen, count '
                    'FROM issues WHERE id=? AND resolved=0',
                    (key,),
                ).fetchone()
                if row:
                    rows.append(row)
            if rows:
                from core.log_archive import snapshot

                now = datetime.now()
                text = (
                    f'RESOLVED ERRORS — {reason} at '
                    + now.isoformat(timespec='seconds')
                    + '\n'
                )
                for key, source, message, first, last, count in rows:
                    text += (
                        f'\n=== ID {key} | source={source} | first={first} '
                        f'| last={last} | count={count} ===\n{message.rstrip()}\n'
                    )
                snapshot(
                    directory,
                    'resolved-errors.log',
                    now.date(),
                    text.encode('utf-8'),
                )
            db.executemany(
                'UPDATE issues SET resolved=1 WHERE id=?',
                [(row[0],) for row in rows],
            )
            _render(db, directory)
            return [row[0] for row in rows]
    finally:
        db.close()


def auto_cleanup_fixed_issues(
    directory,
    *,
    current_build_id: Optional[str] = None,
    recovered_categories: Sequence[str] = (),
    before_timestamp: Optional[str] = None,
) -> List[str]:
    """Automatically archive and purge resolved errors from errors.log.

    1. Build-fix cleanup: when the app runs on a newer BUILD_ID than
       ``metadata['last_verified_build_id']``, open errors recorded under older
       builds that have not recurred in the current build are archived to
       ``logs/archive/<date>/resolved-errors.log-*.zip`` and removed from
       ``errors.log``. If any issue is still genuinely broken and occurs again,
       ``record_error`` immediately reopens it under the new build.
    2. Subsystem recovery cleanup: when a subsystem completes a healthy real
       operation (e.g. successful email send / SMTP check / window show / update
       check), prior open errors in those ``recovered_categories`` are archived
       and removed from ``errors.log``.
    """
    directory = Path(directory)
    import_history(directory)
    target_build = (
        _current_build_id() if current_build_id is None else str(current_build_id)
    )
    keys_to_resolve: List[str] = []
    should_advance_build = False

    db = _connect(directory)
    try:
        prior_row = db.execute(
            "SELECT value FROM metadata WHERE key='last_verified_build_id'"
        ).fetchone()
        prior_build = prior_row[0] if prior_row else ''

        if target_build and prior_build != target_build:
            should_advance_build = True
            if prior_build:
                stale_rows = db.execute(
                    'SELECT id FROM issues WHERE resolved=0 AND build_id != ?',
                    (target_build,),
                ).fetchall()
                keys_to_resolve.extend(row[0] for row in stale_rows)

        if recovered_categories:
            placeholders = ','.join('?' for _ in recovered_categories)
            params: List[object] = list(recovered_categories)
            sql = (
                f'SELECT id FROM issues WHERE resolved=0 '
                f'AND category IN ({placeholders})'
            )
            if before_timestamp:
                sql += ' AND last_seen <= ?'
                params.append(before_timestamp)
            cat_rows = db.execute(sql, params).fetchall()
            keys_to_resolve.extend(row[0] for row in cat_rows)
    finally:
        db.close()

    resolved_ids: List[str] = []
    if keys_to_resolve:
        reason = (
            f'auto-cleaned after fix (build={target_build})'
            if should_advance_build
            else 'auto-cleaned after verified subsystem recovery'
        )
        resolved_ids = resolve_issues(directory, keys_to_resolve, reason=reason)

    if should_advance_build and target_build:
        db = _connect(directory)
        try:
            with db:
                db.execute(
                    "INSERT OR REPLACE INTO metadata VALUES ('last_verified_build_id', ?)",
                    (target_build,),
                )
        finally:
            db.close()

    return resolved_ids


def notify_subsystem_recovered(
    base_or_logs_dir,
    categories: Iterable[str],
) -> List[str]:
    """Best-effort hook called when a runtime subsystem succeeds cleanly."""
    cats = tuple(str(c) for c in categories if c)
    if not cats:
        return []
    try:
        path = Path(base_or_logs_dir).resolve()
        logs_dir = path if path.name == 'logs' else (path / 'logs')
        if not (logs_dir / 'error-issues.sqlite3').exists():
            return []
        return auto_cleanup_fixed_issues(logs_dir, recovered_categories=cats)
    except Exception:
        return []
