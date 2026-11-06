"""Build the small Windows GUI launcher with embedded app icon.

python -m pip install ziglang==0.17.0
python tools/build_launcher.py
No runtime is bundled: the host loads the installed shared CPython DLL in-process.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def build():
    with tempfile.TemporaryDirectory() as temp:
        resource = str(Path(temp) / 'mailoffer.res')
        subprocess.run([sys.executable, '-m', 'ziglang', 'rc', '/c65001', '/fo', resource, 'mailoffer.rc'], cwd=ROOT / 'launcher', check=True)
        subprocess.run([sys.executable, '-m', 'ziglang', 'cc', '-target', 'x86_64-windows-gnu', '-municode', '-Wl,--subsystem,windows', '-Wl,--stack,8388608', '-Os', '-s', 'mailoffer.c', resource, '-lshell32', '-o', str(ROOT / 'MailOffer.exe')], cwd=ROOT / 'launcher', check=True)


if __name__ == '__main__':
    build()
