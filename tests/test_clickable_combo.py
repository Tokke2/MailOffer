import os
import unittest
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest
    from PyQt6.QtWidgets import QApplication
    from ui.clickable_combo import ClickableComboBox
    QT = True
except ImportError:
    QT = False


@unittest.skipUnless(QT, 'Qt unavailable')
class ClickableComboTests(unittest.TestCase):
    def test_text_area_opens_without_changing_value(self):
        app = QApplication.instance() or QApplication([])
        combo = ClickableComboBox()
        combo.addItems(['Vindruta', 'Bakruta'])
        combo.setEditable(True)
        combo.resize(300, 40)
        combo.show()
        app.processEvents()
        try:
            QTest.mouseClick(combo.lineEdit(), Qt.MouseButton.LeftButton)
            self.assertTrue(combo.view().isVisible())
            self.assertEqual(combo.currentText(), 'Vindruta')
            combo.hidePopup()
            combo.lineEdit().selectAll()
            QTest.keyClicks(combo.lineEdit(), 'Eget val')
            self.assertEqual(combo.currentText(), 'Eget val')
            combo.setEnabled(False)
            QTest.mouseClick(combo.lineEdit(), Qt.MouseButton.LeftButton)
            self.assertFalse(combo.view().isVisible())
        finally:
            combo.close()
