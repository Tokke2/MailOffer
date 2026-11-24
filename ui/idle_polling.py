"""Reduce idle wakeups without stopping draft protection or background services."""
from PyQt6.QtCore import QObject, QEvent, Qt


def update_polling(window):
    active = window.isVisible() and not window.isMinimized()
    # Draft autosave and backup/update timers are deliberately not changed.
    for name in ('_contacts_poll', '_mail_images_timer'):
        timer = getattr(window, name, None)
        if timer is None:
            continue
        interval = 2000 if active else 15000
        timer.setTimerType(
            Qt.TimerType.CoarseTimer if active else Qt.TimerType.VeryCoarseTimer
        )
        if timer.interval() != interval:
            timer.setInterval(interval)


class IdlePollingController(QObject):
    def eventFilter(self, watched, event):
        if event.type() in (QEvent.Type.Show, QEvent.Type.Hide, QEvent.Type.WindowStateChange):
            if watched is self.parent():
                update_polling(watched)
        return False


def install_idle_polling(window):
    controller = IdlePollingController(window)
    window.installEventFilter(controller)
    window._idle_polling_controller = controller
    update_polling(window)
    return controller
