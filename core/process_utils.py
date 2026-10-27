"""Windows-safe subprocess options for background helpers (not GUI windows)."""
import os
from pathlib import Path
import subprocess
import sys


def quiet_process_options():
    if os.name != 'nt':
        return {}
    return {'creationflags': getattr(subprocess, 'CREATE_NO_WINDOW', 0x08000000)}


def python_cli_executable():
    """Use console Python with redirected pipes and NO_WINDOW for helper output."""
    executable = Path(sys.executable)
    if executable.name.lower() == 'pythonw.exe':
        sibling = executable.with_name('python.exe')
        if sibling.is_file():
            return str(sibling)
    return sys.executable
