"""Portable desktop-entry paths and escaping (no shell commands are executed)."""
import os
from pathlib import Path


def linux_autostart_dir():
    configured = os.environ.get('XDG_CONFIG_HOME', '')
    root = Path(configured) if configured and Path(configured).is_absolute() else Path.home() / '.config'
    return root / 'autostart'


def desktop_exec(arguments):
    def quote(value):
        value = str(value)
        if any(ch in value for ch in '\r\n\0'):
            raise ValueError('Radbrytning/NUL tillåts inte i autostartkommandot')
        # Desktop Entry escaping is not shell quoting; literal % must be %%.
        value = value.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$').replace('%', '%%')
        return '"' + value + '"'
    return ' '.join(quote(arg) for arg in arguments)
