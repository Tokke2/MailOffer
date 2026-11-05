from pathlib import Path
import subprocess
import unittest
from unittest import mock
from tools import update_python_packages as updater

ROOT = Path(__file__).resolve().parents[1]


class PythonStartupTests(unittest.TestCase):
    def test_updates_only_app_packages_with_same_interpreter_then_checks(self):
        run = mock.Mock(return_value=subprocess.CompletedProcess([], 0))
        with mock.patch.object(updater.sys, 'prefix', updater.sys.base_prefix):
            self.assertEqual(updater.update_packages(run), 0)
        calls = [c.args[0] for c in run.call_args_list]
        self.assertEqual(calls[0][:3], [updater.sys.executable, '-m', 'pip'])
        self.assertIn('PyQt6>=6.7.0', calls[1])
        self.assertIn('--upgrade', calls[1])
        self.assertNotIn('--user', calls[1])
        self.assertEqual(calls[-1][-2:], ['pip', 'check'])
        self.assertTrue(all(c.kwargs['timeout'] == 900 for c in run.call_args_list))

    def test_no_updates_inside_virtual_environment(self):
        run = mock.Mock()
        with mock.patch.object(updater.sys, 'prefix', '/different'), self.assertRaises(RuntimeError):
            updater.update_packages(run)
        run.assert_not_called()

    def test_failed_update_is_not_success_or_separate_install(self):
        run = mock.Mock(side_effect=[subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 1)])
        with mock.patch.object(updater.sys, 'prefix', updater.sys.base_prefix):
            self.assertEqual(updater.update_packages(run), 1)
        self.assertEqual(run.call_count, 2)

    def test_failed_bootstrap_does_not_install_packages(self):
        run = mock.Mock(return_value=subprocess.CompletedProcess([], 1))
        with mock.patch.object(updater.sys, 'prefix', updater.sys.base_prefix):
            self.assertEqual(updater.update_packages(run), 1)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args.args[0][-2:], ['ensurepip', '--upgrade'])

    def test_direct_launch_checked_before_qt_and_parallel_updates_locked(self):
        source = (ROOT / 'main.pyw').read_text()
        self.assertLess(source.index('MAILOFFER_STARTUP_READY'), source.index('from PyQt6'))
        helper = (ROOT / 'tools/ensure_python.ps1').read_text()
        self.assertIn('[IO.FileShare]::None', helper)
        self.assertIn('$startupLock.Dispose()', helper)
        self.assertIn('sys.prefix == sys.base_prefix', helper)
        self.assertIn('update_python_packages.py', helper)

    def test_weekly_gate_skips_network_before_candidate_probes(self):
        helper = (ROOT / 'tools/ensure_python.ps1').read_text()
        gate = helper.index('Test-PythonMaintenanceDue $statePath')
        self.assertLess(gate, helper.index('$candidates = @()'))
        self.assertIn('exit 0', helper[gate:helper.index('$candidates = @()')])
        self.assertLess(helper.index('update_python_packages.py'), helper.index('$temporaryState ='))
        self.assertIn('completed=(Get-Date)', helper)

    def test_monday_task_is_hidden_and_has_no_saved_credentials(self):
        schedule = (ROOT / 'tools/weekly_python.ps1').read_text()
        self.assertIn("-DaysOfWeek Monday -At '08:00'", schedule)
        self.assertIn('-StartWhenAvailable', schedule)
        self.assertIn('-LogonType Interactive -RunLevel Limited', schedule)
        self.assertNotIn('-Password', schedule)
        script = (ROOT / 'tools/weekly_python.vbs').read_text()
        self.assertIn(', 0, True)', script)
        self.assertNotIn('main.pyw', script)
