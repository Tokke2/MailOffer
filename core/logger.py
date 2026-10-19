#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/logger.py – Avancerad central logghantering för EmailApp

Version: 3.5 – QUEUE-BASERAD (snabba upp appen) + PUTSAD OCH KÖRBAR

Fixar mot v3.4:
- Korrupt markdown/inklistringssyntax borttagen
  (__future__, __all__, __init__, __enter__, __exit__, log.info,
   root_logger.info, _dev_mode, _ui_error_callback, _ensure_log_dir,
   _add_file_handler, _add_console_handler, _install_excepthook,
   core.events, logging.INFO, >=, 5 * 1024 * 1024)
- SNABBARE: Queue-baserad loggning
    * Alla loggposter skickas till en bakgrundstråd via
      QueueHandler + QueueListener – UI-tråden blockerar ALDRIG
      på disk-IO (tidigare: flush() per post i anropstråden)
    * Automatiskt fallback till direkt loggning om queue-loggning
      av någon anledning misslyckas
    * shutdown_logging() tömer kön + stänger bakgrundstråden
      (anropas via atexit – inget tappas vid avslut)
    * flush_logging() för synkron tömning (t.ex. i excepthook)
- SNABBARE: cachade loggers per kategori (core.loader, core.deps,
  core.startup, core.shutdown, core.perf, core.events, core.recovery)
  – ingen getLogger()-lookup per anrop
- SNABBARE: log_event()/log_perf() guardade med isEnabledFor()
- Idempotent setup_logging(): stoppa gammal listener + rensa
  befintliga handlers vid om-init (inga dubletter)
- Oanvänd intern loggvariabel borttagen
- Imports samlade överst
- List[Path] istället för list[Path] för konsekvent typning
- Mer robust fallback i _ensure_log_dir()
- Korrekt __all__ (inkl. shutdown_logging/flush_logging)

Funktioner (spec §15):
- RotatingFileHandler: 5 MB per fil, 5 backup-filer
- StreamHandler för konsol (endast i dev/debug-läge)
- Enhetligt format: %(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s
- UTF-8 encoding alltid
- Skapar log-katalog automatiskt om den saknas
- Thread-safe via logging-modulens inbyggda lås
- sys.excepthook fångar ohanterade exceptions → logg + UI-dialog

Avancerad loggning (bonus):
- [LOAD]     modul-laddning (OK / FAILED / SAKNAS)
- [DEP]      dependency-kontroll (OK version / SAKNAS / fallback)
- [STARTUP]  startup-sekvens steg för steg
- [SHUTDOWN] shutdown-sekvens steg för steg
- [PERF]     performance-mätning (ms)
- [EVENT]    EventBus-events (endast dev-läge)
- [MODULE]   RecoveryManager-integration

Användning::

    from core.logger import get_logger

    log = get_logger(__name__)
    log.info("Startar process...")
    log.debug("Debug-info: %r", data)
    log.error("Fel: %s", exc, exc_info=True)

    from core.logger import log_module_load, log_dep_check
    from core.logger import log_startup_step, log_shutdown_step
    from core.logger import log_perf, PerfTimer, log_event

    # Vid avslut (valfritt – sker automatiskt via atexit):
    from core.logger import shutdown_logging
    shutdown_logging()

FIL: core/logger.py
"""

from __future__ import annotations

import atexit
import logging
import os
import platform
import queue
import sys
import tempfile
import time
import traceback
from logging.handlers import (
    QueueHandler,
    QueueListener,
    RotatingFileHandler,
)
from pathlib import Path
from typing import Any, Callable, List, Optional

# ═══════════════════════════════════════════════════════════════════════════
# Konstanter
# ═══════════════════════════════════════════════════════════════════════════

LOG_FILENAME = "email_app.log"
MAX_LOG_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 5

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL = logging.INFO

# Dev-läge: om True loggas [EVENT]-meddelanden
_dev_mode: bool = False

# Optional UI-dialog callback (sätts av main.pyw efter UI är initierat)
# Signatur: (title: str, message: str, detail: str) -> None
_ui_error_callback: Optional[Callable[[str, str, str], None]] = None

# ── Queue-loggning (v3.5) ─────────────────────────────────────────────
_log_queue: Optional[queue.SimpleQueue] = None
_queue_listener: Optional[QueueListener] = None
_atexit_registered: bool = False

# ── Cachade loggers per kategori (v3.5 – ingen lookup per anrop) ──────
_LOADER_LOG   = logging.getLogger("core.loader")
_DEPS_LOG     = logging.getLogger("core.deps")
_STARTUP_LOG  = logging.getLogger("core.startup")
_SHUTDOWN_LOG = logging.getLogger("core.shutdown")
_PERF_LOG     = logging.getLogger("core.perf")
_EVENT_LOG    = logging.getLogger("core.events")
_RECOVERY_LOG = logging.getLogger("core.recovery")


# ═══════════════════════════════════════════════════════════════════════════
# Konfiguration av UI-dialog callback
# ═══════════════════════════════════════════════════════════════════════════

def set_ui_error_callback(callback: Callable[[str, str, str], None]) -> None:
    """Registrera en callback som visas vid CRITICAL-fel.

    Exempel::

        from core.logger import set_ui_error_callback
        set_ui_error_callback(lambda t, m, d: dialog.show_error(t, m, d))
    """
    global _ui_error_callback
    _ui_error_callback = callback


def set_dev_mode(enabled: bool) -> None:
    """Aktivera eller inaktivera dev-läge för [EVENT]-loggning."""
    global _dev_mode
    _dev_mode = bool(enabled)


# ═══════════════════════════════════════════════════════════════════════════
# Setup-funktion
# ═══════════════════════════════════════════════════════════════════════════

def setup_logging(
    log_dir: Path,
    level: str = "INFO",
    debug: bool = False,
) -> logging.Logger:
    """Konfigurera och returnera root logger för applikationen.

    Effekter:
    - Skapar log_dir om den saknas (med fallback till temp)
    - Lägger till RotatingFileHandler (5 MB, 5 backups) via bakgrundskö
    - Lägger till StreamHandler om debug=True
    - Sätter sys.excepthook för ohanterade exceptions
    - Aktiverar dev-läge om debug=True

    Idempotent: kan anropas flera gånger utan dubbelhandler.
    """
    global _dev_mode, _queue_listener, _log_queue

    numeric_level = getattr(logging, str(level).upper(), DEFAULT_LOG_LEVEL)
    if not isinstance(numeric_level, int):
        numeric_level = DEFAULT_LOG_LEVEL

    _dev_mode = bool(debug)

    resolved_log_dir = _ensure_log_dir(Path(log_dir))
    log_file = resolved_log_dir / LOG_FILENAME

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Rensa befintliga handlers för att undvika dubletter vid om-init.
    if root_logger.hasHandlers():
        for handler in list(root_logger.handlers):
            try:
                handler.flush()
                handler.close()
            except Exception:
                pass
            root_logger.removeHandler(handler)

    # Stoppa ev. gammal bakgrundstråd vid om-init.
    if _queue_listener is not None:
        try:
            _queue_listener.stop()
        except Exception:
            pass
        _queue_listener = None
    _log_queue = None

    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    file_handler = _add_file_handler(log_file, numeric_level, formatter)
    console_handler = _add_console_handler(formatter) if debug else None

    _attach_handlers(
        root_logger,
        file_handler,
        console_handler,
        numeric_level,
    )

    _install_excepthook(root_logger)
    _register_atexit()

    root_logger.info(
        "[STARTUP] Logger initierad: fil=%s | nivå=%s | debug=%s | queue=%s",
        log_file,
        logging.getLevelName(numeric_level),
        debug,
        _queue_listener is not None,
    )

    return root_logger


def _attach_handlers(
    root_logger:     logging.Logger,
    file_handler:    Optional[logging.Handler],
    console_handler: Optional[logging.Handler],
    numeric_level:   int,
) -> None:
    """
    Koppla handlers – helst via bakgrundskö (QueueListener).

    Vid fel: fallback till direkt koppling (loggning fungerar alltid).
    """
    global _queue_listener, _log_queue

    targets = [
        h for h in (file_handler, console_handler) if h is not None
    ]
    if not targets:
        return

    try:
        _log_queue = queue.SimpleQueue()
        queue_handler = QueueHandler(_log_queue)
        queue_handler.setLevel(numeric_level)
        root_logger.addHandler(queue_handler)

        _queue_listener = QueueListener(
            _log_queue,
            *targets,
            respect_handler_level=True,
        )
        _queue_listener.start()
    except Exception as exc:
        # Fallback: direkt loggning – appen ska ALDRIG bli utan logg.
        _queue_listener = None
        _log_queue = None
        for handler in list(root_logger.handlers):
            root_logger.removeHandler(handler)
        for handler in targets:
            root_logger.addHandler(handler)
        print(
            f"WARNING: Queue-loggning misslyckades ({exc}) – "
            f"direkt loggning aktiv.",
            file=sys.stderr,
        )


def _register_atexit() -> None:
    """Registrera shutdown_logging en gång (tömmer kön vid avslut)."""
    global _atexit_registered
    if not _atexit_registered:
        atexit.register(shutdown_logging)
        _atexit_registered = True


def cleanup_old_logs(log_dir: Path, days: int = 10) -> int:
    """Ta bort loggfiler äldre än *days* dagar. Fail-safe, returnerar antal."""
    removed = 0
    try:
        folder = Path(log_dir)
        if not folder.is_dir():
            return 0
        cutoff = time.time() - max(1, int(days)) * 86400
        patterns = (
            "email_app.log",
            "email_app.log.*",
            "startup_crash.log",
            "launch_*.log",
            "bootstrap_trace.log",
            "low_level_crash.log",
        )
        seen = set()
        for pattern in patterns:
            for path in folder.glob(pattern):
                try:
                    resolved = path.resolve()
                    if resolved in seen or not path.is_file():
                        continue
                    seen.add(resolved)
                    if path.stat().st_mtime < cutoff:
                        path.unlink()
                        removed += 1
                        logging.getLogger(__name__).info(
                            "Tog bort gammal logg: %s", path.name
                        )
                except Exception:
                    logging.getLogger(__name__).debug(
                        "Kunde inte ta bort logg %s", path, exc_info=True
                    )
    except Exception:
        logging.getLogger(__name__).debug(
            "cleanup_old_logs misslyckades", exc_info=True
        )
    return removed


def shutdown_logging() -> None:
    """
    Stoppa bakgrundstråden och töm logg-kön (anropas vid avslut).

    - Bearbetar kvarvarande poster i kön (inget tappas)
    - Stänger listener-tråden
    - Flushar alla handlers
    - Idempotent och fail-safe
    """
    global _queue_listener
    listener = _queue_listener
    _queue_listener = None
    if listener is not None:
        try:
            listener.stop()
        except Exception:
            pass

    root = logging.getLogger()
    for handler in list(root.handlers):
        try:
            handler.flush()
        except Exception:
            pass


def flush_logging() -> None:
    """
    Töm logg-kön synkront (t.ex. i excepthook före hård avslutning).

    Fail-safe och icke-blockerande (max ett begränsat antal poster).
    """
    listener = _queue_listener
    q = _log_queue
    if listener is not None and q is not None:
        try:
            for _ in range(10000):
                try:
                    record = q.get_nowait()
                except Exception:
                    break
                if isinstance(record, logging.LogRecord):
                    listener.handle(record)
        except Exception:
            pass

    root = logging.getLogger()
    for handler in list(root.handlers):
        try:
            handler.flush()
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# Avancerade logghelpers – [LOAD]
# ═══════════════════════════════════════════════════════════════════════════

def log_module_load(
    module_name: str,
    success: bool,
    elapsed_ms: Optional[float] = None,
    error: Optional[Exception] = None,
    optional: bool = False,
    critical: bool = False,
) -> None:
    """Logga resultatet av att ladda en modul."""
    log = _LOADER_LOG
    time_str = f" ({elapsed_ms:.0f}ms)" if elapsed_ms is not None else ""

    if success:
        log.info("[LOAD] %s → OK%s", module_name, time_str)
        return

    error_msg = str(error) if error else "okänt fel"
    if critical:
        log.critical(
            "[LOAD] %s → CRITICAL FAIL – app kan ej starta: %s",
            module_name,
            error_msg,
            exc_info=error is not None,
        )
    elif optional:
        log.warning(
            "[LOAD] %s → SAKNAS (valfri, fortsätter): %s",
            module_name,
            error_msg,
        )
    else:
        log.error(
            "[LOAD] %s → FAILED: %s",
            module_name,
            error_msg,
            exc_info=error is not None,
        )


def log_module_load_start(module_name: str) -> float:
    """Logga att en modul börjar laddas och returnera starttid."""
    _LOADER_LOG.debug("[LOAD] Laddar modul: %s", module_name)
    return time.monotonic()


# ═══════════════════════════════════════════════════════════════════════════
# Avancerade logghelpers – [DEP]
# ═══════════════════════════════════════════════════════════════════════════

def log_dep_check(
    package_name: str,
    available: bool,
    version: Optional[str] = None,
    fallback_msg: Optional[str] = None,
) -> None:
    """Logga resultatet av en dependency-kontroll."""
    log = _DEPS_LOG

    if available:
        ver_str = f" ({version})" if version else ""
        log.info("[DEP] %s → OK%s", package_name, ver_str)
    else:
        fb_str = f" – {fallback_msg}" if fallback_msg else ""
        log.warning("[DEP] %s → SAKNAS%s", package_name, fb_str)


# ═══════════════════════════════════════════════════════════════════════════
# Avancerade logghelpers – [STARTUP] / [SHUTDOWN]
# ═══════════════════════════════════════════════════════════════════════════

def log_startup_begin(version: str) -> None:
    """Logga startup-banner med version."""
    log = _STARTUP_LOG
    separator = "=" * 50
    log.info("[STARTUP] %s", separator)
    log.info("[STARTUP] Email Manager v%s", version)
    log.info("[STARTUP] %s", separator)
    log.info(
        "[STARTUP] Platform: %s | Python %s | PID: %d",
        platform.platform(),
        sys.version.split()[0],
        os.getpid(),
    )


def log_startup_step(component: str, status: str, detail: Optional[str] = None) -> None:
    """Logga ett steg i startup-sekvensen."""
    log = _STARTUP_LOG
    detail_str = f" ({detail})" if detail else ""

    if status == "OK":
        log.info("[STARTUP] %-25s → %s%s", component, status, detail_str)
    elif status == "FAILED":
        log.error("[STARTUP] %-25s → %s%s", component, status, detail_str)
    elif status == "SKIP":
        log.warning("[STARTUP] %-25s → %s%s", component, status, detail_str)
    else:
        log.info("[STARTUP] %-25s → %s%s", component, status, detail_str)


def log_startup_complete(plugin_found: int = 0, plugin_loaded: int = 0) -> None:
    """Logga att startup är klar."""
    log = _STARTUP_LOG
    if plugin_found > 0:
        log.info(
            "[STARTUP] Plugins: %d hittade, %d laddade, %d misslyckade",
            plugin_found,
            plugin_loaded,
            plugin_found - plugin_loaded,
        )
    log.info("[STARTUP] %s", "=" * 50)
    log.info("[STARTUP] Redo")
    log.info("[STARTUP] %s", "=" * 50)


def log_shutdown_begin(reason: str = "user_exit") -> None:
    """Logga start av shutdown-sekvensen."""
    _SHUTDOWN_LOG.info("[SHUTDOWN] Initierar avslutning (reason: %s)", reason)


def log_shutdown_step(component: str, status: str, detail: Optional[str] = None) -> None:
    """Logga ett steg i shutdown-sekvensen."""
    log = _SHUTDOWN_LOG
    detail_str = f" ({detail})" if detail else ""

    if status == "OK":
        log.info("[SHUTDOWN] %-25s → %s%s", component, status, detail_str)
    elif status == "FAILED":
        log.error("[SHUTDOWN] %-25s → %s%s", component, status, detail_str)
    else:
        log.info("[SHUTDOWN] %-25s → %s%s", component, status, detail_str)


def log_shutdown_complete() -> None:
    """Logga att shutdown är klar."""
    log = _SHUTDOWN_LOG
    log.info("[SHUTDOWN] %s", "=" * 50)
    log.info("[SHUTDOWN] Klar")
    log.info("[SHUTDOWN] %s", "=" * 50)


# ═══════════════════════════════════════════════════════════════════════════
# Avancerade logghelpers – [PERF]
# ═══════════════════════════════════════════════════════════════════════════

def log_perf(operation: str, elapsed_ms: float, detail: Optional[str] = None) -> None:
    """Logga performance för en kritisk operation."""
    if not _PERF_LOG.isEnabledFor(logging.DEBUG):
        return
    detail_str = f" [{detail}]" if detail else ""

    if elapsed_ms >= 1000:
        _PERF_LOG.debug("[PERF] %-35s → %.1fs%s", operation, elapsed_ms / 1000, detail_str)
    else:
        _PERF_LOG.debug("[PERF] %-35s → %.0fms%s", operation, elapsed_ms, detail_str)


class PerfTimer:
    """Kontexthanterare för enkel performance-mätning."""

    def __init__(self, operation: str, detail: Optional[str] = None) -> None:
        self.operation = operation
        self.detail = detail
        self._start: float = 0.0

    def __enter__(self) -> "PerfTimer":
        self._start = time.monotonic()
        return self

    def __exit__(self, *_: Any) -> None:
        elapsed_ms = (time.monotonic() - self._start) * 1000
        log_perf(self.operation, elapsed_ms, self.detail)


# ═══════════════════════════════════════════════════════════════════════════
# Avancerade logghelpers – [EVENT]
# ═══════════════════════════════════════════════════════════════════════════

def log_event(event_name: str, data: dict) -> None:
    """Logga ett EventBus-event (endast i dev-läge)."""
    if not _dev_mode:
        return
    if not _EVENT_LOG.isEnabledFor(logging.DEBUG):
        return
    _EVENT_LOG.debug("[EVENT] %-30s → %s", event_name, data)


# ═══════════════════════════════════════════════════════════════════════════
# Avancerade logghelpers – [MODULE] (RecoveryManager-integration)
# ═══════════════════════════════════════════════════════════════════════════

def log_module_error(
    module_name: str,
    error: Exception,
    strike: int,
    max_strikes: int = 3,
) -> None:
    """Logga ett fel i en modul (RecoveryManager-integration)."""
    log = _RECOVERY_LOG
    remaining = max_strikes - strike

    if strike >= max_strikes:
        log.critical(
            "[CRITICAL] [MODULE] %s – fel #%d/%d – disabled permanent: %s",
            module_name,
            strike,
            max_strikes,
            error,
            exc_info=True,
        )
    else:
        log.error(
            "[ERROR] [MODULE] %s – fel #%d/%d – %s: %s (%d strike kvar)",
            module_name,
            strike,
            max_strikes,
            type(error).__name__,
            error,
            remaining,
            exc_info=True,
        )


def log_module_disabled(module_name: str, reason: str) -> None:
    """Logga att en modul har inaktiverats av RecoveryManager."""
    _RECOVERY_LOG.critical(
        "[CRITICAL] [MODULE] %s → DISABLED: %s", module_name, reason
    )


def log_module_reset(module_name: str) -> None:
    """Logga att en modul har återaktiverats."""
    _RECOVERY_LOG.info("[MODULE] %s → RESET (återaktiverad)", module_name)


# ═══════════════════════════════════════════════════════════════════════════
# Hjälpfunktioner (publika)
# ═══════════════════════════════════════════════════════════════════════════

def get_logger(name: str) -> logging.Logger:
    """Hämta en logger för en specifik modul."""
    return logging.getLogger(name)


def get_log_file_path(log_dir: Path) -> Path:
    """Returnera full sökväg till huvudloggfilen."""
    return Path(log_dir) / LOG_FILENAME


def list_log_files(log_dir: Path) -> List[Path]:
    """Lista alla loggfiler (huvudfil + backups), nyast först."""
    files: List[Path] = []
    log_dir = Path(log_dir)
    base = log_dir / LOG_FILENAME

    if base.exists():
        files.append(base)

    for index in range(1, BACKUP_COUNT + 1):
        backup = log_dir / f"{LOG_FILENAME}.{index}"
        if backup.exists():
            files.append(backup)

    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return files


# ═══════════════════════════════════════════════════════════════════════════
# Interna hjälpfunktioner (privata)
# ═══════════════════════════════════════════════════════════════════════════

def _ensure_log_dir(log_dir: Path) -> Path:
    """Försök skapa log_dir. Vid fel, falla tillbaka till temp-katalog."""
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
    except OSError as exc:
        fallback = Path(tempfile.gettempdir()) / "EmailApp" / "logs"
        print(
            f"WARNING: Kunde inte skapa loggkatalog '{log_dir}': {exc}\n"
            f"         Använder fallback: {fallback}",
            file=sys.stderr,
        )
        try:
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback
        except OSError as fb_exc:
            print(
                f"CRITICAL: Kunde inte skapa fallback-katalog: {fb_exc}",
                file=sys.stderr,
            )
            return fallback


def _add_file_handler(
    log_file: Path,
    level: int,
    formatter: logging.Formatter,
) -> Optional[logging.Handler]:
    """Skapa RotatingFileHandler med fallback. Returnerar handler eller None."""
    try:
        handler = RotatingFileHandler(
            filename=log_file,
            mode="a",
            maxBytes=MAX_LOG_SIZE_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
            delay=True,
        )
        handler.setLevel(level)
        handler.setFormatter(formatter)
        return handler
    except OSError as exc:
        print(
            f"ERROR: Kunde inte skapa loggfil '{log_file}': {exc}",
            file=sys.stderr,
        )
        try:
            fallback_file = (
                Path(tempfile.gettempdir()) / "EmailApp" / "logs" / LOG_FILENAME
            )
            fallback_file.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                filename=fallback_file,
                mode="a",
                maxBytes=MAX_LOG_SIZE_BYTES,
                backupCount=BACKUP_COUNT,
                encoding="utf-8",
                delay=True,
            )
            handler.setLevel(level)
            handler.setFormatter(formatter)
            print(f"INFO: Fallback-logg aktiv: {fallback_file}", file=sys.stderr)
            return handler
        except Exception as fallback_exc:
            print(
                f"CRITICAL: Ingen loggfil tillgänglig: {fallback_exc}",
                file=sys.stderr,
            )
            return None


def _add_console_handler(
    formatter: logging.Formatter,
) -> Optional[logging.Handler]:
    """Skapa StreamHandler för konsol-utmatning (dev/debug-läge)."""
    try:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        return handler
    except Exception as exc:
        print(
            f"WARNING: Kunde inte lägga till konsol-logger: {exc}",
            file=sys.stderr,
        )
        return None


def _install_excepthook(root_logger: logging.Logger) -> None:
    """Installera sys.excepthook för att fånga ohanterade exceptions."""

    def handle_exception(
        exc_type: type,
        exc_value: BaseException,
        exc_traceback: Any,
    ) -> None:
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        root_logger.critical(
            "[CRITICAL] Ohanterad exception – %s: %s",
            exc_type.__name__,
            exc_value,
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        # Töm kön synkront så att kritiska poster hamnar på disk
        # även om processen avslutas direkt efteråt.
        flush_logging()

        if _ui_error_callback is not None:
            try:
                detail = "".join(
                    traceback.format_exception(
                        exc_type, exc_value, exc_traceback
                    )
                )
                _ui_error_callback(
                    "Kritiskt fel",
                    f"Ett oväntat fel uppstod:\n{exc_type.__name__}: {exc_value}",
                    detail,
                )
            except Exception as callback_exc:
                root_logger.error(
                    "Kunde inte visa UI-dialog för kritiskt fel: %s",
                    callback_exc,
                    exc_info=True,
                )

    sys.excepthook = handle_exception


# ═══════════════════════════════════════════════════════════════════════════
# Publikt API
# ═══════════════════════════════════════════════════════════════════════════

__all__ = [
    # Setup
    "setup_logging",
    "shutdown_logging",
    "flush_logging",
    "set_ui_error_callback",
    "set_dev_mode",
    # Grundläggande
    "get_logger",
    "get_log_file_path",
    "list_log_files",
    # [LOAD]
    "log_module_load",
    "log_module_load_start",
    # [DEP]
    "log_dep_check",
    # [STARTUP] / [SHUTDOWN]
    "log_startup_begin",
    "log_startup_step",
    "log_startup_complete",
    "log_shutdown_begin",
    "log_shutdown_step",
    "log_shutdown_complete",
    # [PERF]
    "log_perf",
    "PerfTimer",
    # [EVENT]
    "log_event",
    # [MODULE]
    "log_module_error",
    "log_module_disabled",
    "log_module_reset",
    # Konstanter
    "cleanup_old_logs",
    "LOG_FILENAME",
    "MAX_LOG_SIZE_BYTES",
    "BACKUP_COUNT",
    "LOG_FORMAT",
    "LOG_DATE_FORMAT",
]
