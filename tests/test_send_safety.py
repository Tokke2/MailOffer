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


class RegistrationHistoryTests(unittest.TestCase):
    def test_normalization_and_aliases(self):
        from core.send_safety import registration_number
        for key in ("reg", "registration", "registreringsnummer", "REG"):
            self.assertEqual(registration_number({"replacements": {key: " abc- 12d "}}), "ABC12D")
        self.assertEqual(registration_number({"replacements": {"modell": "ABC123"}}), "")

    def test_match_all_ages_profiles_recipients_and_contents(self):
        from core.send_safety import registration_history_matches
        row = {"timestamp": "2010-01-01", "replacements": {"reg": "ABC 123"}, "success": True, "subject": "Other content"}
        params = {"replacements": {"registration": "abc-123"}}
        self.assertEqual(registration_history_matches(params, [row]), [row])

    def test_empty_different_and_malformed_rows_do_not_match(self):
        from core.send_safety import registration_history_matches
        rows = [None, "bad", {}, {"replacements": []}, {"replacements": {"reg": "DEF456"}}, {"subject": "ABC123"}]
        self.assertEqual(registration_history_matches({"replacements": {"reg": "ABC123"}}, rows), [])
        self.assertEqual(registration_history_matches({}, [{"replacements": {"reg": ""}}]), [])

    def test_legacy_and_explicit_registration_fields(self):
        from core.send_safety import registration_history_matches
        rows = [{"replacements": {"reg": "ABC123"}}, {"registration_number": "abc-123"}]
        self.assertEqual(registration_history_matches({"replacements": {"reg": "ABC123"}}, rows), rows)

    def test_test_mail_does_not_trigger_vehicle_warning(self):
        from core.send_safety import registration_history_matches
        params = {"replacements": {"reg": "ABC123"}}
        self.assertEqual(registration_history_matches(dict(params, test_mode=True), [params]), [])
        self.assertEqual(registration_history_matches(params, [dict(params, test_mode=True)]), [])
