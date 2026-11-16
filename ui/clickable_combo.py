"""Editable dropdown whose text field opens its options on a left click."""
from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QComboBox


class ClickableComboBox(QComboBox):
    def setEditable(self, editable):
        super().setEditable(editable)
        if editable and self.lineEdit() is not None:
            self.lineEdit().installEventFilter(self)

    def eventFilter(self, obj, event):
        if (obj is self.lineEdit() and self.isEnabled() and
                event.type() == QEvent.Type.MouseButtonRelease and
                event.button() == Qt.MouseButton.LeftButton and
                self.lineEdit().rect().contains(event.position().toPoint()) and
                not self.view().isVisible()):
            self.showPopup()
            return True
        return super().eventFilter(obj, event)
