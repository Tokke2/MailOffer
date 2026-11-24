"""Windows focus signals & Win32 window presentation helpers (no native EXE host)."""
from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger(__name__)

_SW_HIDE = 0
_SW_SHOWNORMAL = 1
_SW_SHOWMAXIMIZED = 3
_SW_SHOW = 5
_SW_RESTORE = 9

_HWND_TOPMOST = -1
_HWND_NOTOPMOST = -2
_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_SHOWWINDOW = 0x0040


def _is_native_windows_qpa() -> bool:
    if os.name != "nt":
        return False
    try:
        from PyQt6.QtGui import QGuiApplication
        return (QGuiApplication.platformName() or "").strip().lower() == "windows"
    except Exception:
        return False


def _win32_apis():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.restype = wintypes.BOOL

    user32.IsWindowVisible.argtypes = [wintypes.HWND]
    user32.IsWindowVisible.restype = wintypes.BOOL

    user32.IsIconic.argtypes = [wintypes.HWND]
    user32.IsIconic.restype = wintypes.BOOL

    user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.ShowWindow.restype = wintypes.BOOL

    user32.SetWindowPos.argtypes = [
        wintypes.HWND,
        ctypes.c_ssize_t,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        wintypes.UINT,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL

    user32.GetForegroundWindow.argtypes = []
    user32.GetForegroundWindow.restype = wintypes.HWND

    user32.GetWindowThreadProcessId.argtypes = [
        wintypes.HWND,
        ctypes.POINTER(wintypes.DWORD),
    ]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD

    user32.AttachThreadInput.argtypes = [
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.BOOL,
    ]
    user32.AttachThreadInput.restype = wintypes.BOOL

    user32.BringWindowToTop.argtypes = [wintypes.HWND]
    user32.BringWindowToTop.restype = wintypes.BOOL

    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL

    user32.SetActiveWindow.argtypes = [wintypes.HWND]
    user32.SetActiveWindow.restype = wintypes.HWND

    kernel32.GetCurrentThreadId.argtypes = []
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD

    return user32, kernel32, wintypes


def win32_is_window_visible(hwnd: int) -> bool:
    """Return True if Win32 reports *hwnd* as genuinely visible on screen."""
    if os.name != "nt" or not hwnd:
        return False
    try:
        user32, _, wintypes = _win32_apis()
        handle = wintypes.HWND(int(hwnd))
        return bool(user32.IsWindow(handle) and user32.IsWindowVisible(handle))
    except Exception:
        return False


def _force_win32_show_and_focus(
    hwnd: int,
    *,
    maximize: bool = False,
    keep_topmost: bool = False,
) -> None:
    """Explicitly unhide & foreground *hwnd* on Windows.

    When pythonw.exe is launched via ``WScript.Shell.Run(..., 0, True)``,
    Windows sets ``STARTUPINFO.wShowWindow = SW_HIDE (0)``. On the very first
    ``QWidget.show()``, Qt6 calls ``ShowWindow(hwnd, SW_SHOWDEFAULT)`` which
    applies ``SW_HIDE`` — leaving the native ``HWND`` invisible while Qt marks
    ``isVisible() == True``. Calling ``ShowWindow`` explicitly with
    ``SW_RESTORE`` / ``SW_SHOWNORMAL`` overrides ``SW_SHOWDEFAULT``.
    """
    if os.name != "nt" or not hwnd:
        return
    try:
        user32, kernel32, wintypes = _win32_apis()
        handle = wintypes.HWND(int(hwnd))
        if not user32.IsWindow(handle):
            return

        if user32.IsIconic(handle):
            cmd = _SW_RESTORE
        elif maximize:
            cmd = _SW_SHOWMAXIMIZED
        elif not user32.IsWindowVisible(handle):
            cmd = _SW_SHOWNORMAL
        else:
            cmd = _SW_SHOW
        user32.ShowWindow(handle, cmd)

        fg_hwnd = user32.GetForegroundWindow()
        fg_tid = user32.GetWindowThreadProcessId(fg_hwnd, None) if fg_hwnd else 0
        cur_tid = kernel32.GetCurrentThreadId()
        attached = False
        if fg_tid and cur_tid and fg_tid != cur_tid:
            attached = bool(user32.AttachThreadInput(fg_tid, cur_tid, True))
        try:
            flags = _SWP_NOMOVE | _SWP_NOSIZE | _SWP_SHOWWINDOW
            user32.SetWindowPos(handle, _HWND_TOPMOST, 0, 0, 0, 0, flags)
            if not keep_topmost:
                user32.SetWindowPos(handle, _HWND_NOTOPMOST, 0, 0, 0, 0, flags)
            user32.BringWindowToTop(handle)
            user32.SetForegroundWindow(handle)
            user32.SetActiveWindow(handle)
        finally:
            if attached:
                user32.AttachThreadInput(fg_tid, cur_tid, False)
    except Exception:
        log.debug("Win32 show/foreground-hjälpare misslyckades", exc_info=True)


def _repair_offscreen_or_iconic_geometry(window: Any) -> None:
    """Ensure *window* never restores to Windows' -32000,-32000 iconic slot."""
    try:
        from PyQt6.QtCore import QRect
        from PyQt6.QtGui import QGuiApplication
        from ui.screen_fit import bounded_geometry

        geo = window.geometry()
        bad_geo = (
            geo.width() < 320
            or geo.height() < 220
            or abs(geo.x()) >= 16000
            or abs(geo.y()) >= 16000
        )
        screen = (
            (None if bad_geo else QGuiApplication.screenAt(geo.center()))
            or window.screen()
            or QGuiApplication.primaryScreen()
        )
        if screen is None:
            return
        avail = screen.availableGeometry()
        if not bad_geo and avail.intersects(geo):
            return

        normal = window.normalGeometry()
        if (
            normal.width() >= 320
            and normal.height() >= 220
            and abs(normal.x()) < 16000
            and abs(normal.y()) < 16000
        ):
            candidate = normal
        else:
            w = min(1280, max(640, int(avail.width() * 0.88)))
            h = min(880, max(480, int(avail.height() * 0.85)))
            candidate = QRect(
                avail.x() + max(0, (avail.width() - w) // 2),
                avail.y() + max(0, (avail.height() - h) // 2),
                w,
                h,
            )
        fixed = bounded_geometry(candidate, avail)
        window.resize(fixed.width(), fixed.height())
        window.move(fixed.topLeft())
    except Exception:
        log.debug("Geometrireparation vid fönstervisning misslyckades", exc_info=True)


def ensure_qwidget_shown(window: Any) -> None:
    """Synchronize Qt + native Win32 visibility, unminimize, and focus *window*."""
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QWidget

    try:
        setattr(window, "_restoring_from_tray", True)
    except Exception:
        pass
    try:
        state = window.windowState()
        was_maximized = bool(state & Qt.WindowState.WindowMaximized)
        was_minimized = bool(state & Qt.WindowState.WindowMinimized) or window.isMinimized()
        keep_topmost = bool(window.windowFlags() & Qt.WindowType.WindowStaysOnTopHint)

        if not was_maximized:
            _repair_offscreen_or_iconic_geometry(window)

        native_win32 = _is_native_windows_qpa()
        hwnd = int(window.winId()) if native_win32 else 0

        # If Qt already thinks the widget is visible while Win32 left the HWND hidden
        # (caused by STARTUPINFO SW_HIDE + Qt6 SW_SHOWDEFAULT), reset Qt state first
        # so QShowEvent, backing-store expose, and layout all run cleanly.
        if native_win32 and hwnd and window.isVisible() and not win32_is_window_visible(hwnd):
            QWidget.hide(window)

        new_state = (state & ~Qt.WindowState.WindowMinimized) | Qt.WindowState.WindowActive
        if was_maximized:
            new_state |= Qt.WindowState.WindowMaximized
        window.setWindowState(new_state)

        if was_maximized:
            QWidget.showMaximized(window)
        elif was_minimized:
            QWidget.showNormal(window)
        else:
            QWidget.show(window)

        if native_win32:
            hwnd = int(window.winId())
            # På första QWidget.show() i en process startad med STARTUPINFO SW_HIDE
            # anropar Qt6 ShowWindow(SW_SHOWDEFAULT) -> SW_HIDE (firstShow=true).
            # En omedelbar hide()+show()-cykel förbrukar firstShow så att Qt6:s egen
            # QWindowsWindow hamnar i synk med Win32 innan vi sätter förgrundsfokus.
            if hwnd and not win32_is_window_visible(hwnd):
                QWidget.hide(window)
                if was_maximized:
                    QWidget.showMaximized(window)
                else:
                    QWidget.showNormal(window)
                hwnd = int(window.winId())
            _force_win32_show_and_focus(
                hwnd, maximize=was_maximized, keep_topmost=keep_topmost
            )

        window.raise_()
        window.activateWindow()
        window.update()
    finally:
        try:
            setattr(window, "_restoring_from_tray", False)
        except Exception:
            pass


def ensure_qwidget_hidden(window: Any) -> None:
    """Hide *window* in both Qt and native Win32 (even after SW_HIDE startup)."""
    from PyQt6.QtWidgets import QWidget

    native_win32 = _is_native_windows_qpa()
    hwnd = int(window.winId()) if native_win32 and window.testAttribute(
        __import__("PyQt6.QtCore", fromlist=["Qt"]).Qt.WidgetAttribute.WA_WState_Created
    ) else 0
    QWidget.hide(window)
    if native_win32 and hwnd and win32_is_window_visible(hwnd):
        try:
            user32, _, wintypes = _win32_apis()
            user32.ShowWindow(wintypes.HWND(hwnd), _SW_HIDE)
        except Exception:
            log.debug("Win32 ShowWindow(SW_HIDE) misslyckades", exc_info=True)


def present_window(window: Any) -> None:
    """Show, restore, raise, and focus *window* (supports MainWindow, QWidget, or mocks)."""
    if window is None:
        return
    try:
        from PyQt6.QtWidgets import QWidget
        is_qwidget = isinstance(window, QWidget)
    except Exception:
        is_qwidget = False

    if is_qwidget:
        from PyQt6.QtWidgets import QWidget
        # Subclasses overriding show() (such as MainWindow) invoke
        # ensure_qwidget_shown(self) inside show() and emit UI events.
        if type(window).show is not QWidget.show:
            window.show()
        else:
            ensure_qwidget_shown(window)
        return

    window.show()
    if hasattr(window, "raise_"):
        window.raise_()
    if hasattr(window, "activateWindow"):
        window.activateWindow()


def install_focus_handler(window):
    if os.name != 'nt':
        return
    import ctypes
    from ctypes import wintypes
    from PyQt6.QtCore import QTimer
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateEventW.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.CreateEventW(None, False, False, 'Local\\RickardLangkvist.MailOffer.Focus')
    if not handle:
        raise OSError('Kunde inte öppna enkelinstansens fokussignal')
    def poll():
        if kernel.WaitForSingleObject(handle, 0) == 0:
            present_window(window)
    timer = QTimer(window)
    timer.timeout.connect(poll)
    timer.start(100)
    window._focus_signal_timer = timer
    closed = False
    def cleanup(*_):
        nonlocal closed
        if closed:
            return
        closed = True
        timer.stop()
        kernel.CloseHandle(handle)
    window._cleanup_focus_signal = cleanup
    window.destroyed.connect(cleanup)


def request_focus():
    if os.name != 'nt':
        return False
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.OpenEventW.restype = wintypes.HANDLE
    kernel.SetEvent.argtypes = [wintypes.HANDLE]
    kernel.SetEvent.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenEventW(0x0002, False, 'Local\\RickardLangkvist.MailOffer.Focus')
    if not handle:
        return False
    try:
        return bool(kernel.SetEvent(handle))
    finally:
        kernel.CloseHandle(handle)
