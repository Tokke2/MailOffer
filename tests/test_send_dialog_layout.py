import os
import unittest
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QPushButton
    from PyQt6.QtGui import QFont
    HAS_QT = True
except ImportError:
    HAS_QT = False


@unittest.skipUnless(HAS_QT, 'PyQt6 saknas')
class SendDialogLayoutTests(unittest.TestCase):
    def test_long_summary_scrolls_but_footer_stays_visible(self):
        from ui.dialogs import SendConfirmDialog
        app = QApplication.instance() or QApplication([])
        dialog = SendConfirmDialog(send_params={
            'recipients_to': ['customer@example.com'],
            'subject': 'Ett långt ämne ' * 20,
            'warnings': ['En lång varning ' * 20] * 8,
            'preflight_text': '\n'.join('Kontrollrad ' + str(i) for i in range(70)),
        })
        dialog.setFont(QFont('Sans', 14))
        dialog.resize(640, 480)
        QWidget.show(dialog)  # public show() on this dialog is modal
        app.processEvents()
        try:
            self.assertGreater(dialog._content_scroll.verticalScrollBar().maximum(), 0)
            footer = [b for b in dialog.findChildren(QPushButton) if not dialog._content_scroll.isAncestorOf(b)]
            self.assertEqual(len(footer), 3)
            for button in footer:
                self.assertTrue(button.isVisible())
                point = button.mapTo(dialog, button.rect().bottomRight())
                self.assertTrue(dialog.rect().contains(point), (button.text(), point))
                self.assertGreaterEqual(button.width(), button.minimumSizeHint().width())
        finally:
            dialog.close()
