"""Keep application windows reachable in Qt logical pixels (DPI-aware)."""
import weakref

from PyQt6.QtCore import QObject, QEvent, QTimer, QRect, Qt
from PyQt6.QtGui import QGuiApplication, QCursor
from PyQt6.QtWidgets import (
    QAbstractItemView, QComboBox, QWidget, QDialog, QMainWindow, QWizard,
    QMessageBox, QScrollArea, QVBoxLayout, QLayout, QFormLayout, QLabel,
    QTableView, QTreeView,
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


def adapt_form_rows(window):
    """Labels go above fields when necessary instead of forcing window width."""
    for form in window.findChildren(QFormLayout):
        if form.property("mailofferAdaptive"):
            continue
        form.setProperty("mailofferAdaptive", True)
        form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        for row in range(form.rowCount()):
            item = form.itemAt(row, QFormLayout.ItemRole.LabelRole)
            if item is not None and isinstance(item.widget(), QLabel):
                item.widget().setWordWrap(True)


def adapt_tables(window):
    """Bound auto-measure work, enable column reorder/sort indicators, recalculate metrics on DPI/font changes."""
    for table in window.findChildren(QTableView):
        if not table.property('mailofferReadableTable'):
            table.setProperty('mailofferReadableTable', True)
            table.setAlternatingRowColors(True)
            table.setWordWrap(False)
            table.setTextElideMode(Qt.TextElideMode.ElideRight)
            table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            header = table.horizontalHeader()
            header.setResizeContentsPrecision(200)
            if header.count() > 1:
                header.setSectionsMovable(True)
                header.setSectionsClickable(True)
                header.setSortIndicatorShown(True)
        fm = table.fontMetrics()
        font_h = fm.height()
        if table.property('mailofferFontHeight') != font_h:
            table.setProperty('mailofferFontHeight', font_h)
            header = table.horizontalHeader()
            header.setMinimumSectionSize(max(72, fm.horizontalAdvance('MMMMMM')))
            rows = table.verticalHeader()
            rows.setMinimumSectionSize(28)
            rows.setDefaultSectionSize(max(32, font_h + 14))


def adapt_trees(window):
    """Uniform row heights, movable/clickable multi-column headers and smooth HiDPI scrolling."""
    for tree in window.findChildren(QTreeView):
        if not tree.property('mailofferReadableTree'):
            tree.setProperty('mailofferReadableTree', True)
            tree.setAlternatingRowColors(True)
            tree.setUniformRowHeights(True)
            tree.setWordWrap(False)
            tree.setTextElideMode(Qt.TextElideMode.ElideRight)
            tree.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            tree.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
            header = tree.header()
            header.setResizeContentsPrecision(200)
            if header.count() > 1:
                header.setSectionsMovable(True)
                header.setSectionsClickable(True)
                header.setSortIndicatorShown(True)
        fm = tree.fontMetrics()
        font_h = fm.height()
        if tree.property('mailofferTreeFontHeight') != font_h:
            tree.setProperty('mailofferTreeFontHeight', font_h)
            tree.header().setMinimumSectionSize(max(72, fm.horizontalAdvance('MMMMMM')))


def adapt_combos(window):
    """Prevent long dropdown entries from forcing window overflow on compact screens."""
    for combo in window.findChildren(QComboBox):
        if combo.property('mailofferAdaptiveCombo'):
            continue
        combo.setProperty('mailofferAdaptiveCombo', True)
        if combo.sizeAdjustPolicy() == QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow:
            combo.setSizeAdjustPolicy(
                QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon
            )
            if combo.minimumContentsLength() <= 0:
                combo.setMinimumContentsLength(12)
        view = combo.view()
        if view is not None:
            view.setTextElideMode(Qt.TextElideMode.ElideNone)


def fit_window(window, available=None):
    if not isinstance(window, (QDialog, QMainWindow)) or not window.isWindow():
        return
    refresh_dpi = getattr(window, '_refresh_dpi_assets', None)
    if callable(refresh_dpi):
        try:
            refresh_dpi()
        except Exception:
            pass
    adapt_form_rows(window)
    adapt_tables(window)
    adapt_trees(window)
    adapt_combos(window)
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
        self._pending = {}
        app.installEventFilter(self)
        app.screenAdded.connect(self._screen_added)
        app.screenRemoved.connect(lambda screen: self.refit_all())
        for screen in app.screens():
            self._screen_added(screen)

    def _cleanup_pending(self, wid):
        timer = self._pending.pop(wid, None)
        if timer is not None:
            try:
                timer.stop()
                timer.deleteLater()
            except RuntimeError:
                pass

    def _connect_window_screen(self, window):
        try:
            handle = window.windowHandle()
            if handle is not None and not getattr(window, '_screen_fit_connected', False):
                ref = weakref.ref(window)
                handle.screenChanged.connect(
                    lambda _screen, r=ref: self.schedule(r()) if r() is not None and r().isVisible() else None
                )
                window._screen_fit_connected = True
        except RuntimeError:
            pass

    def _screen_added(self, screen):
        screen.availableGeometryChanged.connect(lambda rect: self.refit_all())
        screen.logicalDotsPerInchChanged.connect(lambda dpi: self.refit_all())
        if hasattr(screen, 'physicalDotsPerInchChanged'):
            screen.physicalDotsPerInchChanged.connect(lambda dpi: self.refit_all())
        self.refit_all()

    def refit_all(self):
        for widget in self.app.topLevelWidgets():
            if widget.isVisible():
                self.schedule(widget)

    def schedule(self, window):
        if window is None or not isinstance(window, (QDialog, QMainWindow)):
            return
        try:
            if not window.isWindow() or not window.isVisible():
                return
        except RuntimeError:
            return
        wid = id(window)
        existing = self._pending.get(wid)
        if existing is not None:
            try:
                existing.start(60)
                return
            except RuntimeError:
                self._pending.pop(wid, None)
        try:
            reference = weakref.ref(window, lambda _r, key=wid: self._cleanup_pending(key))
        except TypeError:
            return
        timer = QTimer(self)
        timer.setSingleShot(True)
        self._pending[wid] = timer

        def run():
            self._pending.pop(wid, None)
            try:
                timer.deleteLater()
            except RuntimeError:
                pass
            target = reference()
            if target is None:
                return
            try:
                if not target.isVisible():
                    return
                fit_window(target)
                self._connect_window_screen(target)
            except RuntimeError:
                pass  # transient dialog was deleted before the queued callback

        timer.timeout.connect(run)
        timer.start(60)

    def eventFilter(self, watched, event):
        if event is None or not isinstance(watched, (QDialog, QMainWindow)):
            return False
        etype = event.type()
        if etype == QEvent.Type.Show:
            try:
                if watched.isWindow():
                    self._connect_window_screen(watched)
                    self.schedule(watched)
            except RuntimeError:
                pass
        elif etype in (
            QEvent.Type.Resize,
            QEvent.Type.FontChange,
            QEvent.Type.StyleChange,
        ):
            try:
                if watched.isVisible() and watched.isWindow():
                    self.schedule(watched)
            except RuntimeError:
                pass
        return False


def install_screen_fit(app):
    controller = getattr(app, '_mailoffer_screen_fit', None)
    if controller is None:
        controller = ScreenFitController(app)
        app._mailoffer_screen_fit = controller
    return controller
