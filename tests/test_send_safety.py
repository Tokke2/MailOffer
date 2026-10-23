import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from core.send_safety import template_allowed, content_fingerprint, recent_duplicates


class SendSafetyTests(unittest.TestCase):
    def test_profile_rules(self):
        rules = {'A.txt': ['profile-a'], 'B.txt': []}
        self.assertTrue(template_allowed('Shared.txt', 'new-profile', rules))
        self.assertTrue(template_allowed('A.txt', 'profile-a', rules))
        self.assertFalse(template_allowed('A.txt', 'profile-b', rules))
        self.assertFalse(template_allowed('B.txt', 'profile-a', rules))
        self.assertFalse(template_allowed('A.txt', '', rules))

    def test_fingerprint_content_not_recipient(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / 'A.txt'
            file.write_text('Original')
            params = dict(subject='Subject', template_path=str(file), replacements={'name': 'A'}, recipients_to=['a@example.com'])
            first = content_fingerprint(params)
            params['recipients_to'] = ['b@example.com']
            self.assertEqual(first, content_fingerprint(params))
            params['replacements']['name'] = 'B'
            self.assertNotEqual(first, content_fingerprint(params))
            params['replacements']['name'] = 'A'
            file.write_text('Changed')
            self.assertNotEqual(first, content_fingerprint(params))

    def test_duplicates_recent_successful_only(self):
        now = datetime.now(timezone.utc)
        row = dict(timestamp=now.isoformat(), success=True, content_fingerprint='abc', delivered_recipients=['A@EXAMPLE.COM'])
        self.assertEqual(recent_duplicates('abc', ['a@example.com', 'b@example.com'], [row], now), ['a@example.com'])
        self.assertEqual(recent_duplicates('different', ['a@example.com'], [row], now), [])
        self.assertEqual(recent_duplicates('abc', ['a@example.com'], [dict(row, success=False)], now), [])
        self.assertEqual(recent_duplicates('abc', ['a@example.com'], [row], now + timedelta(hours=25)), [])
        self.assertEqual(recent_duplicates('abc', ['a@example.com'], [dict(row, timestamp='broken')], now), [])
