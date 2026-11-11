"""Browser-style tab history, scoped to the active main window only."""
from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtWidgets import QApplication, QWidget


class MouseNavigation(QObject):
    def __init__(self, window, tabs):
        super().__init__(window)
        self.window = window
        self.tabs = tabs
        self.history = []
        self.position = -1
        self.replaying = False
        self.record(tabs.currentIndex())
        tabs.currentChanged.connect(self.record)

    def record(self, index):
        if self.replaying or index < 0:
            return
        page = self.tabs.widget(index)
        if self.position >= 0 and self.history[self.position] is page:
            return
        self.history = self.history[:self.position + 1]
        self.history.append(page)
        # Bound history without keeping an unlimited number of page references.
        self.history = self.history[-100:]
        self.position = len(self.history) - 1

    def navigate(self, direction):
        position = self.position + direction
        while 0 <= position < len(self.history):
            try:
                index = self.tabs.indexOf(self.history[position])
            except RuntimeError:  # A page may have been deleted.
                index = -1
            if index >= 0 and self.tabs.isTabVisible(index) and self.tabs.isTabEnabled(index):
                self.position = position
                self.replaying = True
                try:
                    self.tabs.setCurrentIndex(index)
                finally:
                    self.replaying = False
                return True
            position += direction
        return False

    def eventFilter(self, obj, event):
        if event.type() not in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease,
                                QEvent.Type.MouseButtonDblClick):
            return False
        if event.button() not in (Qt.MouseButton.BackButton, Qt.MouseButton.ForwardButton):
            return False
        if (QApplication.activeWindow() is not self.window or
                QApplication.activeModalWidget() is not None or
                QApplication.activePopupWidget() is not None):
            return False
        if not isinstance(obj, QWidget) or obj.window() is not self.window:
            return False
        if event.type() == QEvent.Type.MouseButtonPress:
            self.navigate(-1 if event.button() == Qt.MouseButton.BackButton else 1)
        # Consume the whole click so embedded controls do not also navigate.
        return True


def install_mouse_navigation(window, tabs):
    guard = MouseNavigation(window, tabs)
    QApplication.instance().installEventFilter(guard)
    window._mouse_navigation = guard
    return guard
