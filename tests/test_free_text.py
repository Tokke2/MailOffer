import unittest
import importlib.util
from core.free_text import insert_free_text
from core.email_sender import append_free_text


class FreeTextTests(unittest.TestCase):
    def test_requested_signoff_position(self):
        body = 'Hej,\nVi önskar en offert.\n\nTack på förhand!\nkontakt@example.com\nFöretaget'
        result = append_free_text(body, '<Listen som åtgår eftersöks>', False)
        self.assertLess(result.index('<Listen'), result.index('Tack på förhand!'))
        self.assertEqual(result.count('<Listen'), 1)
        self.assertIn('kontakt@example.com\nFöretaget', result)

    def test_english_and_other_signoffs(self):
        for signoff in ('Best regards,', 'Kind regards', 'Med vänliga hälsningar', 'Mvh', '-- '):
            result = insert_free_text('Body\n\n' + signoff + '\nName', 'Extra')
            self.assertLess(result.index('Extra'), result.index(signoff.strip()))

    def test_do_not_match_sentence_in_body(self):
        body = 'Hej\nTack på förhand för att ni läser detta.\nBody'
        self.assertEqual(insert_free_text(body, 'Extra'), body + '\n\nExtra')

    def test_empty_free_text_preserves_body(self):
        self.assertEqual(insert_free_text('Body\r\n', '  '), 'Body\r\n')

    @unittest.skipUnless(importlib.util.find_spec("bs4"), "beautifulsoup4 saknas")
    def test_html_literal_text_before_signature(self):
        from bs4 import BeautifulSoup
        result = insert_free_text('<html><body><p>Hej</p><p>Tack på förhand!<br>Företag</p></body></html>', '<Listen>\nNy rad', True)
        soup = BeautifulSoup(result, 'html.parser')
        self.assertIsNone(soup.find('listen'))
        self.assertLess(soup.get_text().index('<Listen>'), soup.get_text().index('Tack på förhand'))
        self.assertIn('Ny rad', soup.get_text())

    @unittest.skipUnless(importlib.util.find_spec("bs4"), "beautifulsoup4 saknas")
    def test_html_without_signature_stays_inside_body(self):
        result = insert_free_text('<html><body><p>Body</p></body></html>', 'Extra', True)
        self.assertLess(result.index('Extra'), result.index('</body>'))
