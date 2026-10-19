#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uppdatera appen från en mapp – rör ALDRIG JSON och inställningar."""
from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List

from core.update_protect import is_protected

log = logging.getLogger(__name__)

SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".data",
    "adresslistor",
    "logs",
}


def apply_update_from_dir(src: Path, dest: Path) -> Dict[str, Any]:
    """Kopiera kod från src → dest. JSON/settings hoppas över.

    Returns: {copied, skipped, errors}
    """
    src = Path(src).resolve()
    dest = Path(dest).resolve()
    copied: List[str] = []
    skipped: List[str] = []
    errors: List[str] = []
    if not src.is_dir():
        return {
            "copied": copied,
            "skipped": skipped,
            "errors": ["Källmappen finns inte"],
        }
    for path in src.rglob("*"):
        try:
            rel = path.relative_to(src)
        except Exception:
            continue
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            skipped.append(str(rel))
            continue
        target = dest / rel
        if is_protected(target, dest) or is_protected(path, src):
            skipped.append(str(rel))
            continue
        try:
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not path.is_file():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied.append(str(rel))
        except Exception as exc:
            errors.append("%s: %s" % (rel, exc))
            log.warning("Uppdatering misslyckades för %s", rel, exc_info=True)
    log.info(
        "App-uppdatering: %d kopierade, %d hoppade över, %d fel",
        len(copied),
        len(skipped),
        len(errors),
    )
    return {"copied": copied, "skipped": skipped, "errors": errors}


__all__ = ["apply_update_from_dir"]
