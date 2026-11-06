"""Real Windows smoke test: shared CPython runs inside branded EXE, no Qt required."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(os.name == 'nt', 'Windows native host')
class NativeHostTests(unittest.TestCase):
    def test_host_image_duplicate_signal_and_only_one_bootstrap(self):
        with tempfile.TemporaryDirectory(prefix='MailOffer host ') as directory:
            root = Path(directory)
            (root / 'tools').mkdir()
            (root / 'logs').mkdir()
            shutil.copy2(ROOT / 'MailOffer.exe', root / 'MailOffer.exe')
            runtime = str(Path(sys.executable).with_name('pythonw.exe'))
            self.assertTrue(Path(runtime).is_file())
            # Only substitute bootstrap in a temporary test folder; never upgrade CI Python.
            (root / 'tools/python_bootstrap.vbs').write_text('''Option Explicit
Dim fso, root, stream
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
Set stream = fso.CreateTextFile(root & "\\logs\\python-runtime.txt", True, True)
stream.Write "''' + runtime.replace('"', '""') + '''"
stream.Close
Set stream = fso.OpenTextFile(root & "\\bootstrap.log", 8, True)
stream.WriteLine "bootstrap"
stream.Close
''', encoding='ascii')
            (root / 'main.pyw').write_text('''import ctypes, json, os, sys, time
from pathlib import Path
from ctypes import wintypes
root = Path(__file__).parent
kernel = ctypes.WinDLL('kernel32')
path = ctypes.create_unicode_buffer(32768)
kernel.GetModuleFileNameW(None, path, len(path))
kernel.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
kernel.OpenEventW.restype = wintypes.HANDLE
kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
handle = kernel.OpenEventW(0x00100000, False, 'Local\\\\RickardLangkvist.MailOffer.Focus')
(root / 'ready.json').write_text(json.dumps({'image': path.value, 'args': sys.argv, 'host': os.environ.get('MAILOFFER_NATIVE_HOST')}))
end = time.monotonic() + 20
while time.monotonic() < end and not (root / 'finish').exists():
    if kernel.WaitForSingleObject(handle, 100) == 0:
        (root / 'focused').touch()
''', encoding='utf-8')
            first = subprocess.Popen([str(root / 'MailOffer.exe'), '--background'])
            try:
                def wait_file(path):
                    deadline = time.monotonic() + 12
                    while not path.exists() and time.monotonic() < deadline and first.poll() is None:
                        time.sleep(0.05)
                    self.assertTrue(path.exists(), 'Native host did not initialize: ' + str(first.poll()))
                wait_file(root / 'ready.json')
                import json
                proof = json.loads((root / 'ready.json').read_text())
                self.assertEqual(Path(proof['image']).name.lower(), 'mailoffer.exe')
                self.assertEqual(proof['args'][1:], ['--background'])
                self.assertEqual(proof['host'], '1')
                second = subprocess.run([str(root / 'MailOffer.exe')], timeout=10)
                self.assertEqual(second.returncode, 0)
                wait_file(root / 'focused')
                self.assertEqual((root / 'bootstrap.log').read_text().splitlines(), ['bootstrap'])
                (root / 'finish').touch()
                self.assertEqual(first.wait(timeout=10), 0)
            finally:
                if first.poll() is None:
                    first.terminate()
                    first.wait(timeout=10)


class NativeHostWiringTests(unittest.TestCase):
    def test_mutex_and_focus_precede_updates_and_python_is_in_process(self):
        source = (ROOT / 'launcher/mailoffer.c').read_text()
        self.assertLess(source.index('ERROR_ALREADY_EXISTS'), source.index('CreateProcessW('))
        self.assertIn('SetEvent(focus)', source)
        self.assertIn('AllowSetForegroundWindow(*pid)', source)
        self.assertIn('python_main(count + 1, python_args)', source)
        self.assertIn('LoadLibraryExW', source)
        focus = (ROOT / 'core/native_host.py').read_text()
        for method in ('showNormal()', 'raise_()', 'activateWindow()'):
            self.assertIn(method, focus)
