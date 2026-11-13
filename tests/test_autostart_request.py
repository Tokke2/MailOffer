import ast
from pathlib import Path
import unittest
from unittest.mock import Mock
from core.desktop_startup import repair_requested_autostart


class AutostartRequestTests(unittest.TestCase):
    def settings(self, **values):
        data = {'autostart': False, **values}
        obj = Mock()
        obj.get.side_effect = lambda key, default=None: data.get(key, default)
        obj.set.side_effect = lambda key, value: data.__setitem__(key, value)
        def register(enable):
            data['autostart'] = enable
            return True
        obj.set_autostart.side_effect = register
        obj.get_autostart_info.return_value = {'os_enabled': True, 'os_blocked': False, 'classification': 'correct'}
        obj.sync_autostart.return_value = True
        obj.save.return_value = True
        return obj, data

    def test_first_start_enables_and_persists_minimized(self):
        obj, data = self.settings()
        self.assertTrue(repair_requested_autostart(obj))
        obj.set_autostart.assert_called_once_with(True)
        self.assertTrue(data['start_minimized'])
        self.assertTrue(data['autostart_request_2343_applied'])
        obj.save.assert_called_once()

    def test_later_opt_out_is_respected(self):
        obj, _ = self.settings(autostart_request_2343_applied=True)
        self.assertTrue(repair_requested_autostart(obj))
        obj.set_autostart.assert_not_called()
        obj.sync_autostart.assert_called_once()

    def test_blocked_startup_not_reported_as_success(self):
        obj, data = self.settings()
        obj.get_autostart_info.return_value['os_blocked'] = True
        self.assertFalse(repair_requested_autostart(obj))
        self.assertNotIn('autostart_request_2343_applied', data)
        obj.save.assert_not_called()

    def test_registration_and_save_failure_retry_next_start(self):
        obj, data = self.settings()
        obj.set_autostart.side_effect = None
        obj.set_autostart.return_value = False
        self.assertFalse(repair_requested_autostart(obj))
        self.assertNotIn('autostart_request_2343_applied', data)
        obj, data = self.settings()
        obj.save.return_value = False
        self.assertFalse(repair_requested_autostart(obj))
        self.assertFalse(data['autostart_request_2343_applied'])

    def test_background_second_instance_does_not_reveal_window(self):
        tree = ast.parse((Path(__file__).resolve().parents[1] / 'main.pyw').read_text(encoding='utf-8'))
        node = next(n for n in ast.walk(tree) if isinstance(n, ast.If) and
                    ast.dump(n.test) == ast.dump(ast.parse('instance is not None and not background_start', mode='eval').body))
        for background, expected in ((True, 0), (False, 1)):
            instance = Mock()
            exec(compile(ast.Module(body=[node], type_ignores=[]), 'focus-test', 'exec'),
                 {'instance': instance, 'background_start': background})
            self.assertEqual(instance.focus_existing.call_count, expected)
