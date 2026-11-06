"""Receive duplicate-launch requests on the Qt GUI thread, including hidden windows."""
import os


def install_focus_handler(window):
    if os.name != 'nt' or os.environ.get('MAILOFFER_NATIVE_HOST') != '1':
        return
    import ctypes
    from ctypes import wintypes
    from PyQt6.QtCore import QTimer
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.OpenEventW.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    handle = kernel.OpenEventW(0x00100000, False, 'Local\\RickardLangkvist.MailOffer.Focus')
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
    window._native_focus_timer = timer
    window.destroyed.connect(lambda: kernel.CloseHandle(handle))
