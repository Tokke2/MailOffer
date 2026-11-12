"""Early, independent diagnostics; safe before Qt and normal logging setup."""
import atexit
import faulthandler
import logging
import logging.handlers
from core.daily_log_handler import DiagnosticFileHandler
import os
from pathlib import Path
import re
import sys
import threading
import warnings

_logger = None
_fault_file = None
_error_collector = None


class RedactingFormatter(logging.Formatter):
    def format(self, record):
        from core.error_log import redact
        return redact(super().format(record))


class ErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.WARNING or bool(record.exc_info)


def install(base):
    global _logger, _fault_file, _error_collector
    if _logger is not None:
        return _logger
    directory = Path(base).resolve() / 'logs'
    try:
        directory.mkdir(parents=True, exist_ok=True)
        handler = DiagnosticFileHandler(directory / 'app.log', encoding='utf-8')
    except OSError:
        # Normal logging setup will report the unwritable app log directory.
        # Do not create log files elsewhere or a console on pythonw startup.
        unavailable = logging.getLogger('mailoffer.diagnostics.unavailable')
        unavailable.propagate = False
        if not unavailable.handlers:
            unavailable.addHandler(logging.NullHandler())
        return unavailable
    handler.setFormatter(RedactingFormatter('%(asctime)s | %(levelname)s | pid=%(process)d | %(threadName)s | %(name)s | %(message)s | %(pathname)s:%(lineno)d'))
    _logger = logging.getLogger('mailoffer.diagnostics')
    _logger.setLevel(logging.DEBUG)
    _logger.propagate = False
    _logger.addHandler(handler)
    _logger.info('PROCESS START Python=%s executable=%s cwd=%s base=%s background=%s', sys.version.replace('\n', ' '), sys.executable, os.getcwd(), base, '--background' in sys.argv)
    original = sys.excepthook
    def uncaught(kind, value, tb):
        _logger.critical('Unhandled main-thread exception', exc_info=(kind, value, tb))
        if sys.stderr is not None:
            original(kind, value, tb)
    sys.excepthook = uncaught
    def thread_error(args):
        _logger.critical('Unhandled thread exception: %s', getattr(args.thread, 'name', '?'), exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    threading.excepthook = thread_error
    def unraisable(args):
        _logger.error('Unraisable exception: %s', args.err_msg, exc_info=(args.exc_type, args.exc_value, args.exc_traceback))
    sys.unraisablehook = unraisable
    def warning(message, category, filename, lineno, file=None, line=None):
        _logger.warning('Python warning %s at %s:%s: %s', category.__name__, filename, lineno, message)
    warnings.showwarning = warning
    # pythonw has no stderr; save explicit writes and import tracebacks too.
    if sys.stderr is None:
        sys.stderr = ErrorStream(_logger)
    try:
        handler.native_capture = True
        handler.resume_fault()
        _fault_file = handler
    except (OSError, RuntimeError):
        _logger.exception('Could not enable native crash diagnostics')
    atexit.register(lambda: _logger.info('PROCESS EXIT (Python atexit reached)'))
    try:
        from core.error_log import ErrorLogCollector
        _error_collector = ErrorLogCollector(base, canonical_layout=True)
        _error_collector.start()
    except Exception:
        _logger.exception('Could not start combined error log')
    return _logger


class ErrorStream:
    encoding = 'utf-8'
    def __init__(self, logger):
        self.logger = logger
    def write(self, text):
        if text.strip():
            # Structured console records can arrive here under pythonw. Preserve
            # their severity; stderr alone does not turn a successful INFO into ERROR.
            match = re.match(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[,.]\d+)?\s*\|\s*(DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\|', text)
            level = getattr(logging, match[1]) if match else logging.ERROR
            self.logger.log(level, 'stderr: %s', text.rstrip())
        return len(text)
    def flush(self):
        pass


def attach_root():
    """Reattach after every normal logger reset; include caught DEBUG exceptions."""
    if _logger is None:
        return
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    class Forward(logging.Handler):
        def emit(self, record):
            _logger.handle(record)
    forward = Forward()
    forward.addFilter(lambda record: bool(record.exc_info) and record.levelno < logging.WARNING)
    root.addHandler(forward)


def install_qt():
    if _logger is None:
        return
    from PyQt6.QtCore import qInstallMessageHandler, QtMsgType
    def message(kind, context, text):
        level = logging.DEBUG if kind == QtMsgType.QtDebugMsg else logging.WARNING
        if kind in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            level = logging.CRITICAL
        _logger.log(level, 'Qt %s: %s (%s:%s)', kind.name, text, context.file, context.line)
    qInstallMessageHandler(message)


def collect_errors(base):
    """Refresh the combined log on demand; do not reconfigure logging/hooks."""
    from core.error_log import ErrorLogCollector
    collector = _error_collector
    if collector is None or Path(base).resolve() != collector.base.resolve():
        collector = ErrorLogCollector(base)
    collector.collect(final=True)
    return collector.path
