import os
from pathlib import Path
import unittest
from unittest import mock
from core.donate import resolve_donation_links, paypal_donation_url

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt6.QtWidgets import QApplication
    from ui.donate import DonateDialog
    QT = True
except ImportError:
    QT = False


class DonationLockTests(unittest.TestCase):
    def test_settings_cannot_redirect_funds(self):
        self.assertEqual(resolve_donation_links('https://example.com/steal', 'other'),
                         ('https://ko-fi.com/tokke2', 'https://paypal.me/Rickard3dPrint'))
        self.assertEqual(paypal_donation_url(50), 'https://paypal.me/Rickard3dPrint/50SEK')
        self.assertEqual(paypal_donation_url(), 'https://paypal.me/Rickard3dPrint')
        for amount in (-1, 100000, 'https://example.com', True, 1.5):
            with self.assertRaises(ValueError):
                paypal_donation_url(amount)

    def test_usage_license_is_explicit_not_an_open_source_grant(self):
        text = (Path(__file__).resolve().parents[1] / 'LICENSE').read_text(encoding='utf-8')
        self.assertIn('privata och kommersiella', text)
        self.assertIn('Rickard Längkvist', text)
        self.assertIn('inte en standardlicens för öppen källkod', text)

    @unittest.skipUnless(QT, 'Qt unavailable')
    def test_dialog_fixed_recipients_and_chosen_amount(self):
        app = QApplication.instance() or QApplication([])
        dialog = DonateDialog(kofi_url='https://example.com/steal', paypal_url='other', swish_number='0701234567')
        try:
            self.assertEqual(dialog._swish_number, '')
            self.assertEqual(dialog._kofi_url, 'https://ko-fi.com/tokke2')
            with mock.patch('ui.donate.open_url_in_browser', return_value=True) as opened:
                dialog._amount.setValue(100)
                dialog._open_paypal()
                opened.assert_called_once_with('https://paypal.me/Rickard3dPrint/100SEK')
        finally:
            dialog.close()
