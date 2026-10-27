#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/dep_check.py
=================
Kontrollera och installera Python-tillägg (pinnade versioner).

Version: 1.0 – AUTO-INSTALL + PROGRESS

Körs vid appstart. Saknade/för gamla paket installeras med pip.
Ingen VBS. Progress via callback (UI visar progressbar).

FIL: core/dep_check.py
"""

from __future__ import annotations

import importlib
import logging
import os
import subprocess
from core.process_utils import quiet_process_options, python_cli_executable
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

VERSION = "1.0"
AUTHOR = "Rickard Längkvist"

# pip-namn, import-namn, pinnad version
REQUIRED: List[Tuple[str, str, str]] = [
    ("PyQt6", "PyQt6", "6.7.0"),
    ("python-docx", "docx", "1.1.2"),
    ("darkdetect", "darkdetect", "0.8.0"),
    ("email-validator", "email_validator", "2.2.0"),
    ("deep-translator", "deep_translator", "1.11.4"),
]

OPTIONAL: List[Tuple[str, str, str]] = [
    ("Pillow", "PIL", "10.4.0"),
    ("beautifulsoup4", "bs4", "4.12.3"),
    # Swish-QR i donationsdialogen (fail-soft: numret visas ändå)
    ("qrcode", "qrcode", "7.4.2"),
]

ProgressCb = Callable[[int, int, str], None]


def _pkg_version(import_name: str) -> Optional[str]:
    try:
        from importlib import metadata
    except ImportError:
        import importlib_metadata as metadata  # type: ignore
    candidates = [import_name, import_name.replace("_", "-")]
    for name in candidates:
        try:
            return str(metadata.version(name))
        except Exception:
            continue
    try:
        mod = importlib.import_module(import_name)
        ver = getattr(mod, "__version__", None)
        return str(ver) if ver else None
    except Exception:
        return None


def _parse_ver(text: str) -> Tuple[int, ...]:
    parts: List[int] = []
    for bit in str(text or "").split("."):
        digits = "".join(ch for ch in bit if ch.isdigit())
        if digits:
            parts.append(int(digits))
        else:
            break
    return tuple(parts) if parts else (0,)


def inspect_packages(
    include_optional: bool = True,
) -> List[Dict[str, Any]]:
    """Returnera status per paket: ok | install | upgrade."""
    rows: List[Dict[str, Any]] = []
    items = list(REQUIRED)
    if include_optional:
        items.extend(OPTIONAL)
    for pip_name, import_name, required in items:
        installed = _pkg_version(import_name)
        if installed is None:
            # extra: PyQt6.QtWidgets som proxy
            try:
                importlib.import_module(import_name)
                installed = required
            except Exception:
                installed = None
        action = "ok"
        if installed is None:
            action = "install"
        elif _parse_ver(installed) < _parse_ver(required):
            action = "upgrade"
        rows.append(
            {
                "pip": pip_name,
                "import": import_name,
                "required": required,
                "installed": installed,
                "action": action,
                "spec": f"{pip_name}=={required}",
            }
        )
    return rows


def needed_packages(include_optional: bool = True) -> List[Dict[str, Any]]:
    return [row for row in inspect_packages(include_optional) if row["action"] != "ok"]


def pyqt6_available() -> bool:
    try:
        importlib.import_module("PyQt6.QtWidgets")
        return True
    except Exception:
        return False


def _pip_cmd() -> List[str]:
    return [python_cli_executable(), "-m", "pip"]


def ensure_pip() -> bool:
    try:
        r = subprocess.run(
            _pip_cmd() + ["--version"],
            capture_output=True,
            text=True,
            timeout=60,
            **quiet_process_options(),
        )
        if r.returncode == 0:
            return True
    except Exception:
        log.debug("pip --version misslyckades", exc_info=True)
    try:
        subprocess.run(
            [python_cli_executable(), "-m", "ensurepip", "--upgrade"],
            capture_output=True,
            timeout=120,
            **quiet_process_options(),
        )
        return True
    except Exception:
        log.exception("ensurepip misslyckades")
        return False


def install_spec(
    spec: str,
    on_progress: Optional[ProgressCb] = None,
    index: int = 1,
    total: int = 1,
) -> bool:
    """pip install --upgrade <paket==version>."""
    if on_progress:
        on_progress(index, total, "Installerar %s…" % spec)
    log.info("pip install %s", spec)
    kwargs: Dict[str, Any] = {
        "capture_output": True,
        "text": True,
        "timeout": 600,
    }
    kwargs.update(quiet_process_options())
    try:
        result = subprocess.run(
            _pip_cmd() + ["install", "--upgrade", spec],
            **kwargs,
        )
    except Exception:
        log.exception("pip install kraschade: %s", spec)
        return False
    if result.returncode != 0:
        err = (result.stderr or result.stdout or "")[-800:]
        log.warning("pip install misslyckades (%s): %s", spec, err)
        return False
    return True


def install_needed(
    include_optional: bool = True,
    on_progress: Optional[ProgressCb] = None,
) -> Dict[str, Any]:
    """Installera/uppdatera saknade paket. Returnerar sammanfattning."""
    todo = needed_packages(include_optional)
    summary: Dict[str, Any] = {
        "needed": [row["spec"] for row in todo],
        "ok": [],
        "failed": [],
    }
    if not todo:
        if on_progress:
            on_progress(1, 1, "Alla tillägg är installerade")
        return summary
    if not ensure_pip():
        summary["failed"] = [row["spec"] for row in todo]
        return summary
    total = len(todo)
    for i, row in enumerate(todo, start=1):
        spec = row["spec"]
        if install_spec(spec, on_progress, i, total):
            summary["ok"].append(spec)
        else:
            summary["failed"].append(spec)
    if on_progress:
        on_progress(total, total, "Klart")
    return summary


__all__ = [
    "REQUIRED",
    "OPTIONAL",
    "inspect_packages",
    "needed_packages",
    "pyqt6_available",
    "ensure_pip",
    "install_spec",
    "install_needed",
    "VERSION",
]
