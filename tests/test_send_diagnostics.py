from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from types import SimpleNamespace
import unittest
from core.send_diagnostics import audit_message, audit_dns
from core.signatures import append_signature


class SendDiagnosticsTests(unittest.TestCase):
    def message(self, signature='Test signature'):
        msg = MIMEMultipart('alternative')
        msg['From'] = 'sender@example.com'
        msg['To'] = 'Undisclosed recipients:;'
        msg['Subject'] = 'Test'
        msg['Date'] = 'Wed, 01 Jan 2025 10:00:00 +0000'
        msg['Message-ID'] = '<test@example.com>'
        plain, html = append_signature('Body', '<p>Body</p>', signature)
        msg.attach(MIMEText(plain, 'plain', 'utf-8'))
        msg.attach(MIMEText(html, 'html', 'utf-8'))
        return msg

    def test_signature_checked_and_content_not_logged(self):
        with self.assertLogs('core.send_diagnostics', level='INFO') as logs:
            self.assertEqual(audit_message(self.message(), signature_text='Test signature'), [])
        text = '\n'.join(logs.output)
        self.assertIn('signature_text=True', text)
        self.assertNotIn('Test signature', text)
        self.assertNotIn('sender@example.com', text)
        self.assertIn('not verified locally', text)

    def test_missing_signature_and_logo_reported(self):
        warnings = audit_message(self.message(''), signature_text='Missing', signature_logo='logo.png')
        self.assertIn('signature_missing_in_plain', warnings)
        self.assertIn('signature_logo_missing', warnings)

    def test_remote_images_placeholder_and_empty_subject(self):
        msg = self.message('')
        msg.replace_header('Subject', '')
        msg.attach(MIMEText('<img src="https://example.com/x"><b>{{missing}}</b>', 'html'))
        warnings = audit_message(msg)
        for code in ('signature_not_configured', 'remote_images', 'unresolved_placeholder', 'empty_subject'):
            self.assertIn(code, warnings)

    def test_hidden_recipients_never_exposed(self):
        msg = self.message()
        msg['Bcc'] = 'hidden@example.com'
        with self.assertRaises(ValueError):
            audit_message(msg)
        del msg['Bcc']
        msg.replace_header('To', 'hidden@example.com')
        with self.assertRaises(ValueError):
            audit_message(msg, bcc_batch=True, hidden_recipients=['HIDDEN@example.com'])
        # Independent, explicitly visible To recipient is valid.
        msg.replace_header('To', 'visible@example.com')
        audit_message(msg, bcc_batch=True, hidden_recipients=['hidden@example.com'])

    def test_dns_record_presence_never_claims_authentication_pass(self):
        def checker(domain, timeout):
            self.assertEqual(domain, 'example.com')
            self.assertEqual(timeout, .7)
            return SimpleNamespace(spf_status='ok', dmarc_status='ok', dkim_selectors=[], dmarc_policy='none', error='')
        with self.assertLogs('core.send_diagnostics', level='INFO') as logs:
            audit_dns('sender@example.com', checker=checker)
        text = '\n'.join(logs.output)
        self.assertIn('DKIM_common_selector=unknown', text)
        self.assertIn('Authentication-Results required', text)

    def test_dns_failure_does_not_block_sending(self):
        def checker(*args, **kwargs):
            raise OSError('offline')
        self.assertIsNone(audit_dns('sender@example.com', checker=checker))
