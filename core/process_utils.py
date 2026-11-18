"""Windows-safe subprocess options for background helpers (not GUI windows)."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def quiet_process_options() -> dict:
    if os.name != "nt":
        return {}
    options = {"creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)}
    if hasattr(subprocess, 'STARTUPINFO'):
        startup = subprocess.STARTUPINFO()
        startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startup.wShowWindow = subprocess.SW_HIDE
        options['startupinfo'] = startup
    return options


def python_cli_executable() -> str:
    """Use console Python with redirected pipes and NO_WINDOW for helper output."""
    executable = Path(sys.executable)
    if executable.name.lower() == "pythonw.exe":
        sibling = executable.with_name("python.exe")
        if sibling.is_file():
            return str(sibling)
    return sys.executable
