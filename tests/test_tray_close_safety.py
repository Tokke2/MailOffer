import ast
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]

class TrayCloseSafetyTests(unittest.TestCase):
    def handler(self):
        tree = ast.parse((ROOT / 'ui/main_window.py').read_text(encoding='utf-8'))
        node = next(n for c in tree.body if isinstance(c, ast.ClassDef) for n in c.body
                    if isinstance(n, ast.FunctionDef) and n.name == 'closeEvent')
        scope = {'Any': object}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'close-handler', 'exec'), scope)
        return scope['closeEvent']

    def test_close_hides_only_with_recoverable_tray(self):
        for available in (True, False):
            window = mock.Mock()
            window.settings = {'close_to_tray': True}
            window._can_hide_to_tray.return_value = available
            event = mock.Mock()
            self.handler()(window, event)
            event.ignore.assert_called_once()
            if available:
                window.hide.assert_called_once()
                window.showMinimized.assert_not_called()
            else:
                window.hide.assert_not_called()
                window.showMinimized.assert_called_once()
