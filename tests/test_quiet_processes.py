import subprocess
import unittest
from pathlib import Path
from unittest import mock

from core.dep_check import ensure_pip, install_needed, install_spec
from core.process_utils import python_cli_executable, quiet_process_options


def completed(code=0, stderr=""):
    return subprocess.CompletedProcess([], code, stdout="", stderr=stderr)


class QuietProcessesTests(unittest.TestCase):
    def test_windows_no_console_flag(self):
        with mock.patch("core.process_utils.os.name", "nt"):
            self.assertEqual(
                quiet_process_options()["creationflags"],
                getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
            )

    def test_other_platform_no_windows_flag(self):
        with mock.patch("core.process_utils.os.name", "posix"):
            self.assertEqual(quiet_process_options(), {})

    def test_pythonw_uses_existing_cli_sibling(self):
        with mock.patch("core.process_utils.sys.executable", "/python/pythonw.exe"), mock.patch.object(Path, "is_file", return_value=True):
            self.assertEqual(python_cli_executable(), str(Path("/python/python.exe")))

    def test_missing_cli_sibling_keeps_current_python(self):
        with mock.patch("core.process_utils.sys.executable", "/python/pythonw.exe"), mock.patch.object(Path, "is_file", return_value=False):
            self.assertEqual(python_cli_executable(), "/python/pythonw.exe")

    def test_other_interpreter_is_unchanged(self):
        with mock.patch("core.process_utils.sys.executable", "/python/python3"), mock.patch.object(Path, "is_file") as exists:
            self.assertEqual(python_cli_executable(), "/python/python3")
            exists.assert_not_called()

    def test_pip_already_works_without_bootstrap(self):
        with mock.patch("core.dep_check.subprocess.run", return_value=completed()) as run:
            self.assertTrue(ensure_pip())
            run.assert_called_once()
            self.assertEqual(run.call_args.args[0][-3:], ["-m", "pip", "--version"])

    def test_bootstrap_and_verification_are_quiet(self):
        with mock.patch("core.dep_check.quiet_process_options", return_value={"creationflags": 0x08000000}), mock.patch("core.dep_check.subprocess.run") as run:
            run.side_effect = [completed(1), completed(), completed()]
            self.assertTrue(ensure_pip())
            self.assertEqual(run.call_count, 3)
            for call in run.call_args_list:
                self.assertEqual(call.kwargs["creationflags"], 0x08000000)
                self.assertEqual(call.kwargs["stdin"], subprocess.DEVNULL)
                self.assertTrue(call.kwargs["capture_output"])
                self.assertEqual(call.kwargs["errors"], "replace")

    def test_failed_bootstrap_never_reports_success(self):
        with mock.patch("core.dep_check.subprocess.run", side_effect=[completed(1), completed(2, "bootstrap failed")]) as run, self.assertLogs("core.dep_check", level="WARNING"):
            self.assertFalse(ensure_pip())
            self.assertEqual(run.call_count, 2)

    def test_successful_bootstrap_still_requires_working_pip(self):
        with mock.patch("core.dep_check.subprocess.run", side_effect=[completed(1), completed(), completed(1)]), self.assertLogs("core.dep_check", level="WARNING"):
            self.assertFalse(ensure_pip())

    def test_bootstrap_timeout_is_failure(self):
        with mock.patch("core.dep_check.subprocess.run", side_effect=[completed(1), subprocess.TimeoutExpired("ensurepip", 120)]), self.assertLogs("core.dep_check", level="ERROR"):
            self.assertFalse(ensure_pip())

    def test_initial_probe_exception_can_recover(self):
        with mock.patch("core.dep_check.subprocess.run", side_effect=[OSError("probe failed"), completed(), completed()]):
            self.assertTrue(ensure_pip())

    def test_install_preserves_spec_as_single_argument(self):
        with mock.patch("core.dep_check.subprocess.run", return_value=completed()) as run:
            self.assertTrue(install_spec("example-package==1.0"))
            self.assertEqual(run.call_args.args[0][-3:], ["install", "--upgrade", "example-package==1.0"])
            self.assertEqual(run.call_args.kwargs["timeout"], 600)
            self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)

    def test_install_failure_is_reported(self):
        with mock.patch("core.dep_check.subprocess.run", return_value=completed(1, "install failed")), self.assertLogs("core.dep_check", level="WARNING"):
            self.assertFalse(install_spec("example-package==1.0"))

    def test_no_package_install_if_pip_is_unavailable(self):
        with mock.patch("core.dep_check.needed_packages", return_value=[{"spec": "example-package==1.0"}]), mock.patch("core.dep_check.ensure_pip", return_value=False), mock.patch("core.dep_check.install_spec") as install:
            self.assertEqual(install_needed()["failed"], ["example-package==1.0"])
            install.assert_not_called()
