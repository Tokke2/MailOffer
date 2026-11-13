from email import message_from_string
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from core.email_sender import send_email
from core.send_diagnostics import audit_message, check_hidden_overlap
from core.support_report import build_support_report


class PrivateBccTests(unittest.TestCase):
    def test_separate_envelopes_sender_only_to_and_unique_message_ids(self):
        with tempfile.TemporaryDirectory() as folder:
            template = Path(folder) / 'test.txt'
            template.write_text('Subject: Test\n\nTest body', encoding='utf-8')
            calls = []
            def send(**kwargs):
                calls.append(kwargs)
                return kwargs['server']
            with mock.patch('core.email_sender.connect_smtp') as connect, mock.patch('core.email_sender.send_with_retry', side_effect=send):
                send_email(smtp_server='example.com', smtp_port=465,
                    sender_email='sender@example.com', sender_name='Sender', username='user', password='secret',
                    word_file_path=str(template), replacements={}, include_english=False,
                    recipients_to=[], recipients_bcc=['one@example.com', 'two@example.com'], attachments=[],
                    delay_between_batches=0, translate_placeholders=False, bcc_batch_size=100)
            self.assertEqual([x['rcpt_to'] for x in calls], [['one@example.com'], ['two@example.com']])
            ids = []
            for call in calls:
                msg = message_from_string(call['message_str'])
                self.assertEqual(msg['To'], 'sender@example.com')
                self.assertIsNone(msg['Cc'])
                self.assertIsNone(msg['Bcc'])
                ids.append(msg['Message-ID'])
                self.assertNotIn('one@example.com', call['message_str'])
                self.assertNotIn('two@example.com', call['message_str'])
            self.assertEqual(len(set(ids)), 2)

    def test_overlap_not_silently_promoted_to_to(self):
        with self.assertRaises(ValueError):
            check_hidden_overlap(['A@example.com'], ['a@example.com'], [], None, 'sender@example.com')
        with self.assertRaises(ValueError):
            check_hidden_overlap([], [], ['sender@example.com'], None, 'sender@example.com')
        msg = message_from_string('From: sender@example.com\nTo: sender@example.com\nBcc:\n\nBody')
        with self.assertRaises(ValueError):
            audit_message(msg)

    def test_report_whitelist_does_not_export_secrets_or_body(self):
        with tempfile.TemporaryDirectory() as folder:
            logs = Path(folder) / 'logs'
            logs.mkdir()
            (logs / 'app.log').write_text(
                '2026-01-01 01:00:00 | PROCESS START Python=3.14.2 executable=private/path\n'
                '2026-01-01 01:00:01 | Förbereder sändning – ämne: SECRET SUBJECT one@example.com\n'
                '2026-01-01 01:00:02 | ERROR | password=VerySecret custom body\n'
                '2026-01-01 01:00:03 | Sändning klar. Batchar: 1, Ämne: PRIVATE\n', encoding='utf-8')
            (logs / 'startup.log').write_text('2026-01-01 01:00:00 | Launcher started; folder=private/path\n'
                '2026-01-01 01:00:02 | Process ended; exit code=0\n', encoding='utf-16')
            report = build_support_report(folder)
            for forbidden in ('SECRET', 'VerySecret', 'one@example.com', 'PRIVATE', 'private/path', 'custom body'):
                self.assertNotIn(forbidden, report)
            self.assertIn('Python=3.14.2', report)
            self.assertIn('kod=0', report)
            self.assertIn('Sändning avslutad', report)
