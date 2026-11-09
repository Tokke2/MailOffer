"""Windows focus signals for the shared Python process; no native EXE host."""
import os


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
            window.showNormal()
            window.raise_()
            window.activateWindow()
    timer = QTimer(window)
    timer.timeout.connect(poll)
    timer.start(100)
    window._focus_signal_timer = timer
    window.destroyed.connect(lambda: kernel.CloseHandle(handle))


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
