"""Profile/template access and recent successful-send detection (no network)."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def template_allowed(name, profile_id, rules):
    if not name or name not in rules:
        return True
    allowed = rules[name]
    return isinstance(allowed, list) and profile_id in allowed


def content_fingerprint(params):
    """Independent of recipient/profile ID; include actual file contents."""
    values = {key: params.get(key) for key in (
        'subject', 'body_plain', 'free_text', 'replacements', 'include_english')}
    if params.get('template_path'):
        values.pop('body_plain', None)  # sending parses the file, not the editor
    profile = params.get('sender_profile') or {}
    values['signature'] = {k: profile.get(k, '') for k in ('signature_text', 'signature_contact')}
    files = [params.get('template_path'), profile.get('signature_logo')] + list(params.get('attachments') or [])
    values['files'] = []
    for filename in files:
        if not filename:
            continue
        path = Path(filename)
        try:
            hasher = hashlib.sha256()
            with path.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    hasher.update(chunk)
            digest = hasher.hexdigest()
        except OSError:
            digest = 'missing:' + str(path)
        values['files'].append(digest)
    return hashlib.sha256(json.dumps(values, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def recent_duplicates(fingerprint, recipients, rows, now=None, hours=24):
    now = now or datetime.now(timezone.utc)
    matches = set()
    requested = {str(x).strip().lower() for x in recipients}
    for row in rows:
        if not row.get('success') or row.get('content_fingerprint') != fingerprint:
            continue
        try:
            date = datetime.fromisoformat(row['timestamp'])
            if date.tzinfo is None:
                date = date.astimezone()
            if not 0 <= (now - date).total_seconds() <= hours * 3600:
                continue
        except (ValueError, TypeError, KeyError):
            continue
        matches.update(requested.intersection(str(x).strip().lower() for x in row.get('delivered_recipients', [])))
    return sorted(matches)
