#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SingleInstance – förhindra flera samtidiga instanser av EmailApp.

Version: 3.3 – UPPDATERAD (spec §12 uppfylld fullt ut)

Fixar mot v3.2:
- ✅ Korrupt markdown/inklistringssyntax borttagen
  (__init__, __all__, __enter__, __exit__, __repr__, __future__,
   log.info, self.app_name, os.open, _sanitize_name,
   _register_cleanup_handlers, _handle_signal, _acquire_windows_mutex,
   _acquire_flock, _acquire_lockfile_fallback, _remove_stale_lockfile,
   _pid_is_running, _cleanup_lockfile, lock_path.read_text, pid <= 0)
- ✅ Windows-ctypes-mutex-fallback (ny):
    * När pywin32 saknas skapas en named mutex via kernel32
      CreateMutexW (med korrekt restype/argtypes för 64-bit)
    * Lockfile används först därefter som sista utväg
- ✅ POSIX-fokus via Unix-socket (spec §12 – NY):
    * Första instansen startar en daemon-tråd som lyssnar på
      /tmp/<App>.sock
    * Andra instansen skickar "focus" via socket i focus_existing()
    * set_focus_callback() låter appen visa fönstret (eller vad som önskas)
    * Sockeln stängs + tas bort vid release()
- ✅ PID-koll korrigerad:
    * os.kill(pid, 0) + PermissionError → processen LEVER (returnerar True)
      – tidigare returnerades False och en levande instans kunde
      felaktigt stämplas som kraschad (stale-lockfile togs bort)
- ✅ Typning: List/Dict/Tuple från typing (konsistent med övriga core)
- ✅ Lås-fria property-läsningar (acquired) – bool-läsning är atomär
- ✅ Sanitized-namn och sökvägar prekompilerade i __init__

Funktioner:
- Plattformsberoende låsmekanism (Windows/Linux/macOS)
- Windows mutex via pywin32 när tillgängligt
- Windows named mutex via ctypes när pywin32 saknas (v3.3)
- flock-baserad fillåsning på Unix när fcntl finns
- Lockfile/PID-fallback om plattformsspecifik metod saknas
- Automatisk cleanup via atexit och signaler
- focus_existing() för Windows (EnumWindows) och POSIX (socket-signal)
- Context manager-stöd (__enter__/__exit__)
- Thread-safe acquire/release

FIL: core/single_instance.py
"""

from __future__ import annotations

import atexit
import logging
import os
import signal
import socket
import sys
import tempfile
import threading
from pathlib import Path
from types import FrameType
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

IS_WINDOWS = sys.platform.startswith("win")
IS_MACOS = sys.platform == "darwin"
IS_LINUX = sys.platform.startswith("linux")
IS_POSIX = IS_MACOS or IS_LINUX

HAS_WIN32 = False
HAS_FCNTL = False

if IS_WINDOWS:
    try:
        import win32api  # type: ignore
        import win32con  # type: ignore
        import win32event  # type: ignore
        import win32gui  # type: ignore
        import winerror  # type: ignore

        HAS_WIN32 = True
    except ImportError:
        HAS_WIN32 = False
else:
    try:
        import fcntl  # type: ignore

        HAS_FCNTL = True
    except ImportError:
        HAS_FCNTL = False

SignalHandler = Callable[[int, Optional[FrameType]], None]

# Windows-konstanter (används av ctypes-fallback)
_ERROR_ALREADY_EXISTS = 183
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


class SingleInstance:
    """Hanterar enkel-instans-beteende för applikationen."""

    def __init__(self, app_name: str) -> None:
        self.app_name = app_name.strip() or "EmailApp"
        self._safe_name = self._sanitize_name(self.app_name)
        self._lock = threading.RLock()
        self._acquired = False
        self._atexit_registered = False
        self._signal_handlers_installed = False
        self._previous_handlers: Dict[int, Any] = {}
        # v3.3: POSIX-fokus
        self._focus_callback: Optional[Callable[[], None]] = None
        self._shutdown_flag = False

        self._lock_path = Path(tempfile.gettempdir()) / f"{self._safe_name}.lock"
        self._socket_path = Path(tempfile.gettempdir()) / f"{self._safe_name}.sock"
        self._mutex_handle = None
        self._lock_fd: Optional[int] = None
        self._lock_mode: Optional[str] = None  # mutex | flock | lockfile
        self._server_socket: Optional[socket.socket] = None
        self._socket_thread: Optional[threading.Thread] = None

        log.debug(
            "SingleInstance initierad: app=%r, lock_path=%s",
            self.app_name,
            self._lock_path,
        )

    @staticmethod
    def _sanitize_name(value: str) -> str:
        sanitized = "".join(
            ch if ch.isalnum() or ch in "-_." else "_" for ch in value
        )
        return sanitized or "EmailApp"

    @property
    def acquired(self) -> bool:
        # Lås-fri: bool-läsning är atomär i CPython
        return self._acquired

    def set_focus_callback(self, callback: Callable[[], None]) -> None:
        """Registrera en callback som anropas när en andra instans
        begär fokus (t.ex. visa och aktivera huvudfönstret)."""
        self._focus_callback = callback

    # ------------------------------------------------------------------
    # Acquire
    # ------------------------------------------------------------------

    def acquire(self) -> bool:
        """Försök att förvärva exklusiv åtkomst."""
        with self._lock:
            if self._acquired:
                return True

            try:
                if IS_WINDOWS and HAS_WIN32:
                    acquired = self._acquire_windows_mutex()
                elif IS_WINDOWS:
                    acquired = self._acquire_windows_ctypes_mutex()
                elif IS_POSIX and HAS_FCNTL:
                    acquired = self._acquire_flock()
                else:
                    acquired = self._acquire_lockfile_fallback()
            except Exception:
                log.exception("Fel vid acquire av single instance")
                acquired = False

            if not acquired:
                return False

            self._acquired = True
            self._start_socket_server()
            self._register_cleanup_handlers()
            log.info(
                "Single instance acquired: app=%s, mode=%s",
                self.app_name, self._lock_mode,
            )
            return True

    def _register_cleanup_handlers(self) -> None:
        if not self._atexit_registered:
            atexit.register(self.release)
            self._atexit_registered = True

        if (
            self._signal_handlers_installed
            or threading.current_thread() is not threading.main_thread()
        ):
            return

        for sig_name in ("SIGTERM", "SIGINT"):
            sig = getattr(signal, sig_name, None)
            if sig is None:
                continue
            try:
                previous = signal.getsignal(sig)
                self._previous_handlers[sig] = previous
                signal.signal(sig, self._handle_signal)
            except Exception:
                log.debug(
                    "Kunde inte registrera signalhanterare för %s",
                    sig_name, exc_info=True,
                )

        self._signal_handlers_installed = True

    def _handle_signal(self, signum: int, frame: Optional[FrameType]) -> None:
        log.info("Signal mottagen för single instance cleanup: %s", signum)
        try:
            self.release()
        except Exception:
            log.exception("Fel under cleanup i signalhanterare")

        previous = self._previous_handlers.get(signum)
        if previous in (None, signal.SIG_DFL):
            raise SystemExit(0)
        if previous == signal.SIG_IGN:
            return
        if callable(previous):
            previous(signum, frame)

    # ------------------------------------------------------------------
    # Plattforms-specifika acquire-metoder
    # ------------------------------------------------------------------

    def _acquire_windows_mutex(self) -> bool:
        mutex_name = f"{self._safe_name}-EmailApp-Mutex"
        try:
            self._mutex_handle = win32event.CreateMutex(
                None, False, mutex_name
            )
            last_error = win32api.GetLastError()
            if last_error == winerror.ERROR_ALREADY_EXISTS:
                log.info(
                    "En annan instans kör redan (Windows mutex): %s",
                    mutex_name,
                )
                if self._mutex_handle is not None:
                    win32api.CloseHandle(self._mutex_handle)
                    self._mutex_handle = None
                return False

            self._lock_mode = "mutex"
            return True
        except Exception:
            log.warning(
                "Mutex-acquire misslyckades, försöker lockfile-fallback",
                exc_info=True,
            )
            return self._acquire_lockfile_fallback()

    def _acquire_windows_ctypes_mutex(self) -> bool:
        """Named mutex via ctypes (v3.3) – när pywin32 saknas."""
        try:
            import ctypes
            from ctypes import wintypes

            kernel32 = ctypes.windll.kernel32
            kernel32.CreateMutexW.restype = wintypes.HANDLE
            kernel32.CreateMutexW.argtypes = [
                wintypes.LPVOID,
                wintypes.BOOL,
                wintypes.LPCWSTR,
            ]
            kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
            kernel32.GetLastError.restype = wintypes.DWORD

            mutex_name = f"{self._safe_name}-EmailApp-Mutex"
            handle = kernel32.CreateMutexW(None, False, mutex_name)
            if not handle:
                log.warning(
                    "ctypes-mutex skapades inte – faller tillbaka till lockfile"
                )
                return self._acquire_lockfile_fallback()

            if kernel32.GetLastError() == _ERROR_ALREADY_EXISTS:
                log.info(
                    "En annan instans kör redan (ctypes mutex): %s",
                    mutex_name,
                )
                kernel32.CloseHandle(handle)
                return False

            self._mutex_handle = handle
            self._lock_mode = "mutex"
            return True
        except Exception:
            log.warning(
                "ctypes-mutex misslyckades, försöker lockfile-fallback",
                exc_info=True,
            )
            return self._acquire_lockfile_fallback()

    def _acquire_flock(self) -> bool:
        fd: Optional[int] = None
        try:
            flags = os.O_RDWR | os.O_CREAT
            if hasattr(os, "O_CLOEXEC"):
                flags |= os.O_CLOEXEC
            fd = os.open(str(self._lock_path), flags, 0o600)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.ftruncate(fd, 0)
            os.write(fd, str(os.getpid()).encode("utf-8"))
            os.fsync(fd)
            self._lock_fd = fd
            self._lock_mode = "flock"
            return True
        except BlockingIOError:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            log.info("En annan instans kör redan (flock): %s", self._lock_path)
            return False
        except Exception:
            if fd is not None:
                try:
                    os.close(fd)
                except OSError:
                    pass
            log.warning(
                "flock-acquire misslyckades, försöker lockfile-fallback",
                exc_info=True,
            )
            return self._acquire_lockfile_fallback()

    def _acquire_lockfile_fallback(self) -> bool:
        for _ in range(2):
            try:
                flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
                if hasattr(os, "O_CLOEXEC"):
                    flags |= os.O_CLOEXEC
                fd = os.open(str(self._lock_path), flags, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(str(os.getpid()))
                self._lock_mode = "lockfile"
                return True
            except FileExistsError:
                if self._remove_stale_lockfile():
                    continue
                log.info(
                    "En annan instans kör redan (lockfile): %s",
                    self._lock_path,
                )
                return False
            except OSError:
                log.exception("OS-fel vid lockfile-acquire")
                return False
        return False

    def _remove_stale_lockfile(self) -> bool:
        try:
            pid_text = self._lock_path.read_text(encoding="utf-8").strip()
            pid = int(pid_text)
        except Exception:
            pid = None  # type: ignore[assignment]

        if pid and self._pid_is_running(pid):
            return False

        try:
            self._lock_path.unlink(missing_ok=True)
            log.warning("Tog bort stale lockfile: %s", self._lock_path)
            return True
        except Exception:
            log.debug("Kunde inte ta bort stale lockfile", exc_info=True)
            return False

    @staticmethod
    def _pid_is_running(pid: int) -> bool:
        if pid <= 0:
            return False
        try:
            if IS_WINDOWS:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                kernel32.OpenProcess.restype = ctypes.c_void_p
                kernel32.OpenProcess.argtypes = [
                    ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32,
                ]
                process = kernel32.OpenProcess(
                    _PROCESS_QUERY_LIMITED_INFORMATION, 0, pid
                )
                if process:
                    kernel32.CloseHandle(process)
                    return True
                return False
            os.kill(pid, 0)
            return True
        except PermissionError:
            # Processen finns men ägs av annan användare – den lever.
            return True
        except ProcessLookupError:
            return False
        except OSError:
            return False
        except Exception:
            return False

    # ------------------------------------------------------------------
    # POSIX-fokus (spec §12 – v3.3)
    # ------------------------------------------------------------------

    def _start_socket_server(self) -> None:
        """Starta Unix-socket-lyssnare för att ta emot fokus-begäran."""
        if not IS_POSIX:
            return
        try:
            self._socket_path.unlink(missing_ok=True)
            srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            srv.bind(str(self._socket_path))
            srv.listen(1)
            srv.settimeout(1.0)  # periodisk timeout → koll av shutdown-flagga
            self._server_socket = srv
            self._socket_thread = threading.Thread(
                target=self._socket_loop,
                args=(srv,),
                daemon=True,
                name="SingleInstanceFocus",
            )
            self._socket_thread.start()
            log.debug("POSIX-fokus-socket aktiv: %s", self._socket_path)
        except Exception:
            log.debug(
                "Kunde inte starta socket-server för fokus",
                exc_info=True,
            )
            self._server_socket = None

    def _socket_loop(self, srv: socket.socket) -> None:
        while not self._shutdown_flag:
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                with conn:
                    data = conn.recv(64)
                    if data and b"focus" in data:
                        callback = self._focus_callback
                        if callback is not None:
                            try:
                                callback()
                            except Exception:
                                log.exception(
                                    "Fel i focus-callback"
                                )
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Release
    # ------------------------------------------------------------------

    def release(self) -> None:
        """Släpp låset och rensa resurser."""
        with self._lock:
            if not self._acquired:
                return

            # Stoppa socket-servern (v3.3)
            self._shutdown_flag = True
            if self._server_socket is not None:
                try:
                    self._server_socket.close()
                except Exception:
                    pass
                self._server_socket = None
            if self._socket_thread is not None:
                try:
                    self._socket_thread.join(timeout=1.5)
                except Exception:
                    pass
                self._socket_thread = None
            try:
                self._socket_path.unlink(missing_ok=True)
            except Exception:
                pass

            try:
                if (
                    self._lock_mode == "mutex"
                    and IS_WINDOWS
                    and self._mutex_handle is not None
                ):
                    if HAS_WIN32:
                        win32api.CloseHandle(self._mutex_handle)
                    else:
                        import ctypes
                        from ctypes import wintypes

                        kernel32 = ctypes.windll.kernel32
                        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
                        kernel32.CloseHandle(self._mutex_handle)
                    self._mutex_handle = None

                elif self._lock_mode == "flock" and self._lock_fd is not None:
                    try:
                        fcntl.flock(self._lock_fd, fcntl.LOCK_UN)
                    finally:
                        os.close(self._lock_fd)
                        self._lock_fd = None
                    # Vid flock låter vi gärna lockfilen ligga kvar
                    # för att undvika race.

                elif self._lock_mode == "lockfile":
                    self._cleanup_lockfile()

            except Exception:
                log.exception("Fel vid release av single instance")
            finally:
                self._acquired = False
                self._lock_mode = None
                log.debug("Single instance released: %s", self.app_name)

    def _cleanup_lockfile(self) -> None:
        try:
            if self._lock_path.exists():
                self._lock_path.unlink(missing_ok=True)
        except Exception:
            log.debug(
                "Kunde inte rensa lockfil: %s",
                self._lock_path, exc_info=True,
            )

    # ------------------------------------------------------------------
    # Fokusera befintlig instans
    # ------------------------------------------------------------------

    def focus_existing(self) -> bool:
        """Försök fokusera befintlig instans.

        - Windows: EnumWindows (fönstertitel matchar app-namn)
        - POSIX: skickar "focus" via Unix-socket till första instansen
        """
        if IS_WINDOWS and HAS_WIN32:
            return self._focus_existing_windows()
        if IS_POSIX:
            return self._focus_existing_socket()
        return False

    def _focus_existing_windows(self) -> bool:
        try:
            windows: List[int] = []

            def enum_callback(hwnd: int, results: List[int]) -> None:
                try:
                    if not win32gui.IsWindowVisible(hwnd):
                        return
                    title = win32gui.GetWindowText(hwnd) or ""
                    if self.app_name.lower() in title.lower():
                        results.append(hwnd)
                except Exception:
                    log.debug(
                        "Fel under EnumWindows-callback", exc_info=True
                    )

            win32gui.EnumWindows(enum_callback, windows)
            if not windows:
                return False

            hwnd = windows[0]
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            log.info("Fokuserade befintlig instans: hwnd=%d", hwnd)
            return True
        except Exception:
            log.exception("Fel vid focus_existing")
            return False

    def _focus_existing_socket(self) -> bool:
        """Skicka fokus-signal till första instansen via Unix-socket."""
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                client.settimeout(2.0)
                client.connect(str(self._socket_path))
                client.sendall(b"focus")
            log.info("Fokus-signal skickad till befintlig instans (socket).")
            return True
        except Exception:
            log.debug("Kunde inte nå befintlig instans via socket")
            return False

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "SingleInstance":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()

    def __repr__(self) -> str:
        status = "acquired" if self._acquired else "released"
        return (
            f"SingleInstance(app_name={self.app_name!r}, "
            f"status={status}, mode={self._lock_mode!r})"
        )


def ensure_single_instance(
    app_name: str,
) -> Tuple[bool, Optional[SingleInstance]]:
    """Enkel helper för att säkerställa single instance.

    Returns:
        (acquired, instance)
        – instance returneras även när acquired=False så att anroparen
          kan anropa focus_existing().
    """
    instance = SingleInstance(app_name)
    acquired = instance.acquire()
    return acquired, instance


__all__ = ["SingleInstance", "ensure_single_instance"]
