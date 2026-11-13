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


def repair_requested_autostart(settings):
    """One-time activation requested in build 2343; later explicit opt-outs survive.

    Mark complete only after OS registration and settings persistence succeed.
    StartupApproved/policy blocks are reported, never modified or bypassed.
    """
    marker = 'autostart_request_2343_applied'
    pending = not settings.get(marker, False)
    if pending:
        if not settings.set_autostart(True):
            return False
        settings.set('start_minimized', True)
    elif not settings.sync_autostart():
        return False
    info = settings.get_autostart_info()
    wanted = bool(settings.get('autostart', False))
    if wanted and (info.get('os_blocked') or not info.get('os_enabled') or
                   info.get('classification') != 'correct'):
        return False
    if pending:
        settings.set(marker, True)
        if not settings.save():
            settings.set(marker, False)
            return False
    return True
