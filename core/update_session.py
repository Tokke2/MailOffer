"""Short-lived, local compose state for an approved update restart (no credentials)."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
import time

FIELDS = {
    'template_name', 'subject', 'body', 'free_text', 'replacements', 'to', 'bcc',
    'to_lang', 'bcc_lang', 'attachment_paths', 'profile_id', 'tab', 'no_vin',
}

MAX_SESSION_AGE_S = 24 * 60 * 60
MAX_SESSION_BYTES = 4 * 1024 * 1024


def save_session(path, state):
    path = Path(path)
    if path.exists() and path.is_symlink():
        raise ValueError('Symbolic link is not allowed for update session')
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {key: value for key, value in state.items() if key in FIELDS}
    payload['_saved_at'] = time.time()
    encoded = json.dumps(payload, ensure_ascii=False)
    if len(encoded.encode('utf-8')) > MAX_SESSION_BYTES:
        raise ValueError('Update session exceeds maximum allowed size')
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='update-session-', suffix='.tmp')
    try:
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            handle.write(encoded)
            handle.flush()
            try:
                os.fsync(handle.fileno())
            except OSError:
                pass
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def read_session(path, *, max_age_s: float = MAX_SESSION_AGE_S):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        return None
    if path.stat().st_size > MAX_SESSION_BYTES:
        raise ValueError('Update session exceeds maximum allowed size')
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Invalid update session')
    saved_at = data.get('_saved_at')
    if isinstance(saved_at, (int, float)) and max_age_s > 0:
        if (time.time() - float(saved_at)) > max_age_s:
            path.unlink(missing_ok=True)
            return None
    return {key: value for key, value in data.items() if key in FIELDS}
