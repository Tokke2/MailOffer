"""One local autosaved draft; explicit field allowlist, never SMTP credentials."""
import json
from pathlib import Path
from core.update_session import FIELDS, save_session

MAX_BYTES = 4 * 1024 * 1024


def validate(state):
    if not isinstance(state, dict):
        raise ValueError('Ogiltigt utkast')
    result = {key: value for key, value in state.items() if key in FIELDS and key != 'tab'}
    for key, value in result.items():
        if key in ('to', 'bcc', 'attachment_paths'):
            valid = isinstance(value, list) and all(isinstance(item, str) for item in value)
        elif key in ('to_lang', 'bcc_lang', 'replacements'):
            valid = isinstance(value, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in value.items())
        else:
            valid = isinstance(value, str)
        if not valid:
            raise ValueError('Ogiltigt utkastfält: ' + key)
    if len(json.dumps(result, ensure_ascii=False).encode('utf-8')) > MAX_BYTES:
        raise ValueError('Utkastet är för stort för autosparning')
    return result


def save_draft(path, state):
    save_session(path, validate(state))


def read_draft(path):
    path = Path(path)
    if not path.exists():
        return None
    if path.stat().st_size > MAX_BYTES:
        raise ValueError('Utkastfilen är för stor')
    return validate(json.loads(path.read_text(encoding='utf-8')))
