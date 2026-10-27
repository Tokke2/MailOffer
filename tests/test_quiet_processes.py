import subprocess
import unittest
from unittest import mock
from core.process_utils import quiet_process_options
from core.dep_check import ensure_pip


class QuietProcessesTests(unittest.TestCase):
    def test_windows_no_console_flag(self):
        with mock.patch('core.process_utils.os.name', 'nt'):
            self.assertEqual(quiet_process_options()['creationflags'], getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000))

    def test_other_platform_no_windows_flag(self):
        with mock.patch('core.process_utils.os.name', 'posix'):
            self.assertEqual(quiet_process_options(), {})

    def test_both_pip_checks_are_quiet(self):
        with mock.patch('core.dep_check.quiet_process_options', return_value={'creationflags': 0x08000000}), mock.patch('core.dep_check.subprocess.run') as run:
            run.side_effect = [mock.Mock(returncode=1), mock.Mock(returncode=0)]
            self.assertTrue(ensure_pip())
            self.assertEqual(run.call_count, 2)
            for call in run.call_args_list:
                self.assertEqual(call.kwargs['creationflags'], 0x08000000)
