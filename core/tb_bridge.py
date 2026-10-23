#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registrera Thunderbird native messaging (högerklick → E-postofferten)."""
from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

HOST_NAME = "e_postofferten"
EXTENSION_ID = "kontakter@e-postofferten.local"


def _host_cmd(base_dir: Path) -> Path:
    return base_dir / "thunderbird" / "e_postofferten_host.cmd"


def _host_py(base_dir: Path) -> Path:
    return base_dir / "thunderbird" / "native_host.py"


def build_manifest(base_dir: Path) -> dict:
    if sys.platform.startswith("win"):
        host = str(_host_cmd(base_dir).resolve())
    else:
        host = str(_host_py(base_dir).resolve())
    return {
        "name": HOST_NAME,
        "description": "Spara Thunderbird-avsändare i E-postofferten",
        "path": host,
        "type": "stdio",
        "allowed_extensions": [EXTENSION_ID],
    }


def register_thunderbird_host(base_dir: Path) -> Optional[Path]:
    """Skriv native-messaging-manifest så Thunderbird hittar hosten."""
    base_dir = Path(base_dir).resolve()
    if not _host_py(base_dir).is_file():
        log.debug("Thunderbird-host saknas: %s", _host_py(base_dir))
        return None
    manifest = build_manifest(base_dir)
    text = json.dumps(manifest, indent=2, ensure_ascii=False)
    written: Optional[Path] = None
    try:
        if sys.platform.startswith("win"):
            appdata = os.getenv("APPDATA") or str(
                Path.home() / "AppData" / "Roaming"
            )
            for rel in (
                Path(appdata) / "Thunderbird" / "NativeMessagingHosts",
                Path(appdata) / "Mozilla" / "NativeMessagingHosts",
            ):
                rel.mkdir(parents=True, exist_ok=True)
                dest = rel / f"{HOST_NAME}.json"
                dest.write_text(text, encoding="utf-8")
                written = dest
            try:
                import winreg  # type: ignore

                for root_path in (
                    r"Software\Thunderbird\NativeMessagingHosts",
                    r"Software\Mozilla\NativeMessagingHosts",
                ):
                    key = winreg.CreateKey(
                        winreg.HKEY_CURRENT_USER,
                        root_path + "\\" + HOST_NAME,
                    )
                    winreg.SetValueEx(
                        key, "", 0, winreg.REG_SZ, str(written)
                    )
                    winreg.CloseKey(key)
            except Exception:
                log.debug("Kunde inte skriva native-host i registret", exc_info=True)
        else:
            dest_dir = Path.home() / ".thunderbird" / "native-messaging-hosts"
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / f"{HOST_NAME}.json"
            dest.write_text(text, encoding="utf-8")
            written = dest
            try:
                os.chmod(_host_py(base_dir), 0o755)
            except OSError:
                pass
        log.info("Thunderbird native host registrerad: %s", written)
    except Exception:
        log.debug("Kunde inte registrera Thunderbird-host", exc_info=True)
        return None
    return written


__all__ = ["register_thunderbird_host", "HOST_NAME", "EXTENSION_ID"]


def test_native_host(base_dir: Path) -> dict:
    """Exercise real native-message framing without modifying contacts.

    This tests the local Python host, NOT whether Thunderbird has loaded the XPI.
    """
    import struct
    import subprocess
    payload = json.dumps({"action": "ping"}).encode("utf-8")
    completed = subprocess.run(
        [sys.executable, str(_host_py(Path(base_dir)))],
        input=struct.pack("<I", len(payload)) + payload,
        capture_output=True, timeout=5,
    )
    if completed.returncode or len(completed.stdout) < 4:
        raise RuntimeError("Native host svarade inte")
    length = struct.unpack("<I", completed.stdout[:4])[0]
    if length > 1024 * 1024 or len(completed.stdout[4:]) != length:
        raise ValueError("Ogiltigt native-messaging-svar")
    result = json.loads(completed.stdout[4:].decode("utf-8"))
    if not result.get("ok"):
        raise RuntimeError(result.get("error", "Native host misslyckades"))
    return result
