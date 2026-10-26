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
