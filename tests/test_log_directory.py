"""All app log writers must stay in the application's logs/ subfolder."""
import logging
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from core.logger import _ensure_log_dir, _add_file_handler, get_log_file_path
from core.error_log import ErrorLogCollector

ROOT = Path(__file__).resolve().parents[1]


class LogDirectoryTests(unittest.TestCase):
    def test_normal_log_and_combined_state_stay_under_app(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            directory = _ensure_log_dir(base / 'logs')
            handler = _add_file_handler(get_log_file_path(directory), logging.INFO, logging.Formatter('%(levelname)s %(message)s'))
            try:
                handler.handle(logging.LogRecord('test', logging.ERROR, 'test.py', 1, 'directory-marker', (), None))
            finally:
                handler.close()
            collector = ErrorLogCollector(base)
            collector.collect()
            self.assertEqual(collector.path, base / 'logs/errors.log')
            self.assertEqual({p.name for p in base.iterdir()}, {'logs'})
            self.assertIn('directory-marker', collector.path.read_text())
            self.assertTrue((directory / 'errors.state.json').exists())
            self.assertTrue((directory / 'errors.lock').exists())

    def test_directory_failure_is_reported_without_temp_fallback(self):
        with mock.patch.object(Path, 'mkdir', side_effect=PermissionError('denied')) as mkdir, mock.patch('tempfile.gettempdir', side_effect=AssertionError('No TEMP logs')):
            with self.assertRaisesRegex(OSError, 'skrivbar appmapp'):
                _ensure_log_dir(Path('/app/logs'))
            self.assertEqual(mkdir.call_count, 1)

    def test_file_open_failure_is_reported_without_temp_fallback(self):
        with mock.patch('core.logger.RotatingFileHandler', side_effect=PermissionError('denied')) as handler, mock.patch('tempfile.gettempdir', side_effect=AssertionError('No TEMP logs')):
            with self.assertRaisesRegex(OSError, 'skrivbehörighet'):
                _add_file_handler(Path('/app/logs/email_app.log'), logging.INFO, logging.Formatter())
            handler.assert_called_once()
            self.assertFalse(handler.call_args.kwargs['delay'])

    def test_early_diagnostics_does_not_try_another_folder_when_denied(self):
        from core import diagnostics
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(diagnostics, '_logger', None), mock.patch('core.diagnostics.logging.handlers.RotatingFileHandler', side_effect=PermissionError('denied')) as handler, mock.patch('tempfile.gettempdir', side_effect=AssertionError('No TEMP logs')):
            logger = diagnostics.install(Path(tmp))
            self.assertEqual(logger.name, 'mailoffer.diagnostics.unavailable')
            handler.assert_called_once()
            self.assertEqual(handler.call_args.args[0], Path(tmp) / 'logs/diagnostics.log')

    def test_launcher_uses_app_log_folder_and_reports_write_failure(self):
        source = (ROOT / 'Starta EmailApp.vbs').read_text()
        log_function = source.split('Sub LogStage(message)', 1)[1]
        self.assertIn('scriptDir & "\\logs"', log_function)
        self.assertNotIn('%TEMP%', log_function)
        self.assertIn('logWarningShown', log_function)
        self.assertIn('Exit Sub', log_function)


    def test_log_write_failure_has_visible_startup_error(self):
        import ast
        tree = ast.parse((ROOT / 'main.pyw').read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == '_setup_app_logging')
        show = mock.Mock()
        setup = mock.Mock(side_effect=PermissionError('logs is read only'))
        namespace = {'Path': Path, 'setup_logging': setup, '_safe_show_critical': show}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'log-startup', 'exec'), namespace)
        self.assertFalse(namespace['_setup_app_logging'](Path('/app/logs')))
        show.assert_called_once()
        self.assertIn('logs is read only', show.call_args.args[1])

    def test_qt_logging_is_not_installed_when_diagnostics_is_unavailable(self):
        from core import diagnostics
        with mock.patch.object(diagnostics, '_logger', None):
            self.assertIsNone(diagnostics.install_qt())
