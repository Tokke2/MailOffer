"""Short-lived, local compose state for an approved update restart (no credentials)."""
import json
import os
from pathlib import Path
import tempfile

FIELDS = {'template_name', 'subject', 'body', 'free_text', 'replacements', 'to', 'bcc',
          'to_lang', 'bcc_lang', 'attachment_paths', 'profile_id', 'tab'}


def save_session(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='update-session-', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump({key: value for key, value in state.items() if key in FIELDS}, handle, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def read_session(path):
    path = Path(path)
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(data, dict):
        raise ValueError('Invalid update session')
    return {key: value for key, value in data.items() if key in FIELDS}
