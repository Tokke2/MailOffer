"""Early, independent diagnostics; safe before Qt and normal logging setup."""
import atexit
import faulthandler
import logging
import logging.handlers
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
import warnings

_logger = None
_fault_file = None


class RedactingFormatter(logging.Formatter):
    def format(self, record):
        text = super().format(record)
        text = re.sub(r'(?i)((?:password|passwd|token|authorization|secret)\s*[=:]\s*)[^\s,;]+', r'\1[REDACTED]', text)
        return re.sub(r'(?i)(AUTH\s+(?:PLAIN|LOGIN)\s+)\S+', r'\1[REDACTED]', text)


class ErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.WARNING or bool(record.exc_info)


def install(base):
    global _logger, _fault_file
    if _logger is not None:
        return _logger
    for directory in (Path(base) / 'logs', Path(tempfile.gettempdir()) / 'MailOffer-logs'):
        try:
            directory.mkdir(parents=True, exist_ok=True)
            handler = logging.handlers.RotatingFileHandler(directory / 'diagnostics.log', maxBytes=5*1024*1024, backupCount=5, encoding='utf-8')
            break
        except OSError:
            continue
    else:
        return logging.getLogger('mailoffer.diagnostics.unavailable')
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
        fault_path = directory / ('native-crash-%s.log' % os.getpid())
        for old in sorted(directory.glob('native-crash-*.log'), key=lambda p: p.stat().st_mtime, reverse=True)[9:]:
            try:
                old.unlink()
            except OSError:
                pass
        _fault_file = fault_path.open('a', encoding='utf-8')
        faulthandler.enable(file=_fault_file, all_threads=True)
    except (OSError, RuntimeError):
        _logger.exception('Could not enable native crash diagnostics')
    atexit.register(lambda: _logger.info('PROCESS EXIT (Python atexit reached)'))
    return _logger


class ErrorStream:
    encoding = 'utf-8'
    def __init__(self, logger):
        self.logger = logger
    def write(self, text):
        if text.strip():
            self.logger.error('stderr: %s', text.rstrip())
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
    forward.addFilter(ErrorFilter())
    root.addHandler(forward)


def install_qt():
    from PyQt6.QtCore import qInstallMessageHandler, QtMsgType
    def message(kind, context, text):
        level = logging.DEBUG if kind == QtMsgType.QtDebugMsg else logging.WARNING
        if kind in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            level = logging.CRITICAL
        _logger.log(level, 'Qt %s: %s (%s:%s)', kind.name, text, context.file, context.line)
    qInstallMessageHandler(message)
