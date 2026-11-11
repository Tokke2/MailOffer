"""Layout-ordered focus, visible focused controls and keyboard context menus."""
from PyQt6.QtCore import QObject, QEvent, Qt
from PyQt6.QtWidgets import (QApplication, QWidget, QDialog, QLabel, QScrollArea,
    QAbstractItemView, QComboBox, QAbstractSpinBox, QLineEdit, QTextEdit, QPlainTextEdit)


def layout_controls(root):
    """Treat compound controls as one tab stop, not their private child widgets."""
    controls = []
    def visit(widget):
        if isinstance(widget, (QTextEdit, QPlainTextEdit)):
            widget.setTabChangesFocus(True)
        if widget.focusPolicy() & Qt.FocusPolicy.TabFocus and not isinstance(widget, QScrollArea):
            controls.append(widget)
            if isinstance(widget, (QAbstractItemView, QComboBox, QAbstractSpinBox, QLineEdit, QTextEdit, QPlainTextEdit)):
                return
        if isinstance(widget, QScrollArea):
            if widget.widget() is not None:
                visit(widget.widget())
        elif widget.layout() is not None:
            visit_layout(widget.layout())
    def visit_layout(layout):
        label = None
        for index in range(layout.count()):
            item = layout.itemAt(index)
            widget = item.widget()
            if widget is not None:
                if isinstance(widget, QLabel):
                    label = widget
                    continue
                before = len(controls)
                visit(widget)
                if label is not None and len(controls) > before:
                    target = controls[before]
                    if label.buddy() is None:
                        label.setBuddy(target)
                    if not target.accessibleName():
                        target.setAccessibleName(label.text().replace('&', '').rstrip(':'))
                label = None
            elif item.layout() is not None:
                visit_layout(item.layout())
                label = None
    visit(root)
    return list(dict.fromkeys(controls))


def configure_tab_flow(roots):
    controls = []
    for root in roots:
        controls.extend(layout_controls(root))
    controls = list(dict.fromkeys(controls))
    for before, after in zip(controls, controls[1:]):
        QWidget.setTabOrder(before, after)
    return controls


class KeyboardNavigation(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show and isinstance(obj, QDialog):
            configure_tab_flow([obj])
        elif event.type() == QEvent.Type.FocusIn and isinstance(obj, QWidget):
            ancestor = obj.parentWidget()
            while ancestor is not None:
                if isinstance(ancestor, QScrollArea):
                    ancestor.ensureWidgetVisible(obj, 20, 20)
                ancestor = ancestor.parentWidget()
        elif event.type() == QEvent.Type.KeyPress and isinstance(obj, QAbstractItemView):
            context_key = event.key() == Qt.Key.Key_Menu or (
                event.key() == Qt.Key.Key_F10 and event.modifiers() == Qt.KeyboardModifier.ShiftModifier)
            if context_key and obj.contextMenuPolicy() == Qt.ContextMenuPolicy.CustomContextMenu:
                index = obj.currentIndex()
                position = obj.visualRect(index).center() if index.isValid() else obj.viewport().rect().center()
                obj.customContextMenuRequested.emit(position)
                return True
        return False


def install_keyboard_navigation():
    app = QApplication.instance()
    if app is None:
        return
    if not hasattr(app, '_mailoffer_keyboard_navigation'):
        guard = KeyboardNavigation(app)
        app.installEventFilter(guard)
        app._mailoffer_keyboard_navigation = guard
