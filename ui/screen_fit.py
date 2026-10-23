"""Keep application windows reachable in Qt logical pixels (DPI-aware)."""
import weakref

from PyQt6.QtCore import QObject, QEvent, QTimer, QRect
from PyQt6.QtGui import QGuiApplication, QCursor
from PyQt6.QtWidgets import (
    QWidget, QDialog, QMainWindow, QWizard, QMessageBox,
    QScrollArea, QVBoxLayout, QLayout,
)


def bounded_geometry(rect, available, margin=12):
    margin = min(margin, max(0, min(available.width(), available.height()) // 10))
    area = available.adjusted(margin, margin, -margin, -margin)
    width = min(max(1, rect.width()), max(1, area.width()))
    height = min(max(1, rect.height()), max(1, area.height()))
    x = max(area.left(), min(rect.x(), area.right() - width + 1))
    y = max(area.top(), min(rect.y(), area.bottom() - height + 1))
    return QRect(x, y, width, height)


def _scroll_layout(widget):
    """Preserve the full content when a dialog cannot fit at its natural size."""
    old = widget.layout()
    if old is None or getattr(widget, '_screen_scroll', None) is not None:
        return
    # Existing scrolling dialogs retain their carefully positioned footers.
    if any(old.indexOf(scroll) >= 0 for scroll in widget.findChildren(QScrollArea)):
        return
    content = QWidget()
    natural = old.minimumSize()
    content.setLayout(old)  # Qt transfers ownership from the previous QWidget.
    content.setMinimumSize(natural)
    scroll = QScrollArea(widget)
    scroll.setWidgetResizable(True)
    scroll.setWidget(content)
    root = QVBoxLayout(widget)
    root.setContentsMargins(0, 0, 0, 0)
    root.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
    root.addWidget(scroll)
    widget._screen_scroll = scroll


def fit_window(window, available=None):
    if not isinstance(window, (QDialog, QMainWindow)) or not window.isWindow():
        return
    if window.isMinimized() or window.isMaximized() or window.isFullScreen():
        return
    if available is None:
        screen = QGuiApplication.screenAt(window.frameGeometry().center())
        if screen is None and window.parentWidget() is not None:
            screen = window.parentWidget().screen()
        screen = screen or QGuiApplication.screenAt(QCursor.pos()) or window.screen()
        if screen is None:
            return
        available = screen.availableGeometry()
    frame = window.frameGeometry()
    dx = max(0, frame.width() - window.width())
    dy = max(0, frame.height() - window.height())
    bounds = available.adjusted(12, 12, -12, -12)
    limit_width = max(1, bounds.width() - dx)
    limit_height = max(1, bounds.height() - dy)
    oversized = (window.minimumWidth() > limit_width or window.minimumHeight() > limit_height
                 or window.minimumSizeHint().width() > limit_width
                 or window.minimumSizeHint().height() > limit_height)
    if oversized:
        if isinstance(window, QWizard):
            for page_id in window.pageIds():
                _scroll_layout(window.page(page_id))
        elif isinstance(window, QMainWindow):
            if not getattr(window, '_screen_central_scroll', None):
                content = window.takeCentralWidget()
                if content is not None:
                    scroll = QScrollArea()
                    scroll.setWidgetResizable(True)
                    scroll.setWidget(content)
                    window.setCentralWidget(scroll)
                    window._screen_central_scroll = scroll
        elif not isinstance(window, QMessageBox):
            _scroll_layout(window)
        layout = window.layout()
        if layout is not None and not isinstance(window, QMainWindow):
            layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
    window.setMinimumSize(min(window.minimumWidth(), limit_width), min(window.minimumHeight(), limit_height))
    # Respect smaller/fixed preferred sizes; never enlarge windows automatically.
    window.resize(min(window.width(), limit_width), min(window.height(), limit_height))
    target = bounded_geometry(window.frameGeometry(), available)
    window.move(target.topLeft())


class ScreenFitController(QObject):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self._pending = set()
        app.installEventFilter(self)
        app.screenAdded.connect(self._screen_added)
        app.screenRemoved.connect(lambda screen: self.refit_all())
        for screen in app.screens():
            self._screen_added(screen)

    def _screen_added(self, screen):
        screen.availableGeometryChanged.connect(lambda rect: self.refit_all())
        self.refit_all()

    def refit_all(self):
        for widget in self.app.topLevelWidgets():
            if widget.isVisible():
                self.schedule(widget)

    def schedule(self, window):
        if not isinstance(window, (QDialog, QMainWindow)) or not window.isWindow():
            return
        if window in self._pending:
            return
        self._pending.add(window)
        def run():
            self._pending.discard(window)
            try:
                fit_window(window)
                handle = window.windowHandle()
                if handle is not None and not getattr(window, '_screen_fit_connected', False):
                    handle.screenChanged.connect(lambda screen, ref=weakref.ref(window): self.schedule(ref()) if ref() is not None else None)
                    window._screen_fit_connected = True
            except RuntimeError:
                pass  # transient dialog was deleted before the queued callback
        QTimer.singleShot(0, run)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Show, QEvent.Type.Resize):
            self.schedule(watched)
        return False


def install_screen_fit(app):
    controller = getattr(app, '_mailoffer_screen_fit', None)
    if controller is None:
        controller = ScreenFitController(app)
        app._mailoffer_screen_fit = controller
    return controller
