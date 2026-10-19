#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Säkerhetskopiera adresslistor så GitHub-uppdatering inte raderar dem."""
from __future__ import annotations

import datetime as _dt
import logging
import shutil
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

KEEP = 10


def backup_address_lists(base_dir: Path) -> Optional[Path]:
    """Kopiera adresslistor/ till .data/backups/adresslistor-YYYYMMDD-HHMMSS/.

    Rör aldrig originalet. Returnerar sökväg till kopian eller None.
    """
    src = Path(base_dir) / "adresslistor"
    try:
        if not src.is_dir():
            return None
        has_files = any(src.iterdir())
        if not has_files:
            return None
    except Exception:
        log.debug("Kunde inte läsa adresslistor", exc_info=True)
        return None

    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = Path(base_dir) / ".data" / "backups" / ("adresslistor-" + stamp)
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest)
        log.info("Adresslistor säkerhetskopierade: %s", dest)
        _prune(dest.parent)
        return dest
    except Exception:
        log.warning("Kunde inte säkerhetskopiera adresslistor", exc_info=True)
        return None


def _prune(backup_root: Path) -> None:
    try:
        dirs = sorted(
            [p for p in backup_root.iterdir() if p.is_dir() and p.name.startswith("adresslistor-")],
            key=lambda p: p.name,
        )
        extra = dirs[:-KEEP] if len(dirs) > KEEP else []
        for old in extra:
            shutil.rmtree(old, ignore_errors=True)
    except Exception:
        log.debug("Kunde inte rensa gamla adressboks-backuper", exc_info=True)


def backup_settings(base_dir: Path) -> Optional[Path]:
    """Kopiera inställnings-JSON till .data/backups/settings-...json."""
    candidates = [
        Path(base_dir) / ".data" / "email_settings.json",
        Path(base_dir) / "email_settings.json",
    ]
    src = next((p for p in candidates if p.is_file()), None)
    if src is None:
        return None
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest_dir = Path(base_dir) / ".data" / "backups"
    dest = dest_dir / ("settings-" + stamp + ".json")
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        log.info("Inställningar säkerhetskopierade: %s", dest)
        return dest
    except Exception:
        log.warning("Kunde inte säkerhetskopiera inställningar", exc_info=True)
        return None


def backup_address_lists_to(base_dir: Path, dest_parent: Path) -> Optional[Path]:
    """Kopiera adresslistor/ till en mapp användaren valt."""
    src = Path(base_dir) / "adresslistor"
    try:
        if not src.is_dir() or not any(src.iterdir()):
            return None
    except Exception:
        return None
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = Path(dest_parent) / ("adresslistor-" + stamp)
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dest)
        log.info("Adresslistor kopierade till: %s", dest)
        return dest
    except Exception:
        log.warning("Manuell backup av adresslistor misslyckades", exc_info=True)
        return None


__all__ = [
    "backup_address_lists",
    "backup_settings",
    "backup_address_lists_to",
]
