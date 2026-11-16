import os
from pathlib import Path
import unittest
from unittest import mock
from core.donate import resolve_donation_links, paypal_donation_url

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt6.QtWidgets import QApplication, QLabel, QLineEdit, QPushButton
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
            self.assertEqual(dialog._swish_number, '0721817177')
            self.assertEqual(dialog._swish_payload, 'C0721817177;50;E-postofferten;6')
            self.assertEqual(dialog._kofi_url, 'https://ko-fi.com/tokke2')
            for widget in dialog.findChildren(QLabel) + dialog.findChildren(QLineEdit):
                self.assertNotIn('0721817177', widget.text())
            dialog._amount.setValue(100)
            self.assertEqual(dialog._swish_payload, 'C0721817177;100;E-postofferten;6')
            for widget in dialog.findChildren(QLabel) + dialog.findChildren(QPushButton):
                self.assertNotIn('PayPal', widget.text())
                self.assertNotIn('Ko-fi', widget.text())
            dialog._amount.setValue(0)
            self.assertEqual(dialog._swish_payload, 'C0721817177;;E-postofferten;6')
        finally:
            dialog.close()

    @unittest.skipUnless(QT, 'Qt unavailable')
    def test_alternative_buttons_open_fixed_urls_directly(self):
        from ui.main_window import MainWindow
        receiver = mock.Mock()
        MainWindow._open_paypal_donation(receiver)
        receiver._open_url.assert_called_once_with('https://paypal.me/Rickard3dPrint')
        receiver._open_url.reset_mock()
        MainWindow._open_kofi_donation(receiver)
        receiver._open_url.assert_called_once_with('https://ko-fi.com/tokke2')
        receiver._open_donate.assert_not_called()
