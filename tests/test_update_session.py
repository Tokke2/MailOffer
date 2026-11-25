import tempfile
import unittest
from pathlib import Path
from core.update_session import save_session, read_session


class UpdateSessionTests(unittest.TestCase):
    def test_allowlist_and_atomic_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'update-session.json'
            save_session(path, {'subject': 'Hello', 'body': 'Draft', 'password': 'secret', 'sender_profile': {'password': 'secret'}})
            self.assertEqual(read_session(path), {'subject': 'Hello', 'body': 'Draft'})
            self.assertNotIn('secret', path.read_text())
            self.assertFalse(list(Path(tmp).glob('*.tmp')))

    def test_missing_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(read_session(Path(tmp) / 'absent.json'))

    def test_expired_session_is_discarded_and_cleaned_up(self):
        import json as _json
        import time as _time

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'update-session.json'
            save_session(path, {'subject': 'Old', 'no_vin': True})
            data = _json.loads(path.read_text(encoding='utf-8'))
            data['_saved_at'] = _time.time() - 90_000
            path.write_text(_json.dumps(data), encoding='utf-8')
            self.assertIsNone(read_session(path))
            self.assertFalse(path.exists())
