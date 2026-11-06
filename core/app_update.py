#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Uppdatera appen från en mapp – rör ALDRIG JSON och inställningar."""
from __future__ import annotations

import logging
import shutil
import os
import uuid
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


def _same_contents(source, target):
    if source.stat().st_size != target.stat().st_size:
        return False
    with source.open('rb') as left, target.open('rb') as right:
        while True:
            chunk = left.read(1024 * 1024)
            if chunk != right.read(1024 * 1024):
                return False
            if not chunk:
                return True


def _copy_executable(source, target, base):
    """Swap the file name, never write into a mapped Windows image."""
    if target.exists() and _same_contents(source, target):
        return
    staged = target.with_name('.' + target.name + '-' + uuid.uuid4().hex + '.tmp')
    backup = None
    try:
        shutil.copy2(source, staged)
        if target.exists():
            backups = base / '.data' / 'executable-backups'
            backups.mkdir(parents=True, exist_ok=True)
            backup = backups / (target.stem + '-' + uuid.uuid4().hex + '.exe')
            os.replace(target, backup)
        try:
            os.replace(staged, target)
        except Exception:
            if backup is not None:
                os.replace(backup, target)
            raise
    finally:
        staged.unlink(missing_ok=True)


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
            if target.suffix.lower() == ".exe":
                _copy_executable(path, target, dest)
            else:
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
