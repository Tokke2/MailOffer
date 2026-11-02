"""Exercise actual tray action methods without requiring a system tray/Qt."""
import ast
import logging
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def method(name):
    tree = ast.parse((ROOT / 'ui/tray.py').read_text(encoding='utf-8'))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'SystemTray')
    node = next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == name)
    namespace = {'log': logging.getLogger('tray-test'), 'tr': lambda key: key}
    exec(compile(ast.Module(body=[node], type_ignores=[]), 'tray-action', 'exec'), namespace)
    return namespace[name]


class TrayUpdatesTests(unittest.TestCase):
    def test_shows_window_then_performs_manual_check(self):
        events = []
        window = mock.Mock()
        window._check_updates.side_effect = lambda **kwargs: events.append(('check', kwargs))
        tray = SimpleNamespace(_main_window=window, _do_show=lambda: events.append(('show', {})))
        method('_do_check_updates')(tray)
        self.assertEqual(events, [('show', {}), ('check', {'manual': True})])

    def test_menu_wires_update_action_to_manual_callback(self):
        actions = {}
        menu = mock.Mock()
        def add_action(text):
            actions[text] = mock.Mock()
            return actions[text]
        menu.addAction.side_effect = add_action
        tray = SimpleNamespace(_menu=menu, **{name: mock.Mock() for name in (
            '_do_show', '_do_hide', '_do_open_settings', '_do_check_updates', '_do_test_smtp', '_do_quit')})
        method('_build_menu')(tray)
        actions['menu.check_updates'].triggered.connect.assert_called_once_with(tray._do_check_updates)

    def test_action_failure_is_logged_not_propagated(self):
        tray = SimpleNamespace(_main_window=mock.Mock(), _do_show=mock.Mock(side_effect=RuntimeError('window failure')))
        with self.assertLogs('tray-test', level='ERROR'):
            method('_do_check_updates')(tray)
        tray._main_window._check_updates.assert_not_called()
