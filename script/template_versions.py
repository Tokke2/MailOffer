#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Versionshistorik för mallfiler.

Versionerna sparas som bytexakta kopior under
``<mallmapp>/.versions/<mallfilnamn>/``. Mallistan skannar bara
filer direkt i mallmappen, så historiken syns aldrig som vanliga
mallar. En version skapas innan en befintlig mall skrivs över och
innan en äldre version återställs – även en återställning går
därför att ångra.

FIL: script/template_versions.py
"""

from __future__ import annotations

import hashlib
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

log = logging.getLogger(__name__)

VERSIONS_DIRNAME = ".versions"
DEFAULT_KEEP_VERSIONS = 20
_TIMESTAMP_FORMAT = "%Y%m%d-%H%M%S-%f"


@dataclass(frozen=True)
class TemplateVersionInfo:
    """En sparad version av en mallfil."""

    path: Path
    template_name: str
    created_at: datetime
    size: int

    @property
    def label(self) -> str:
        return self.created_at.strftime("%Y-%m-%d %H:%M:%S")


def _versions_dir(template_path: Path, *, create: bool = False) -> Path:
    directory = template_path.parent / VERSIONS_DIRNAME / template_path.name
    if create:
        directory.mkdir(parents=True, exist_ok=True)
    return directory


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 64), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _created_at(path: Path) -> datetime:
    try:
        return datetime.strptime(path.stem, _TIMESTAMP_FORMAT)
    except ValueError:
        return datetime.fromtimestamp(path.stat().st_mtime)


def list_template_versions(template_path: Path) -> List[TemplateVersionInfo]:
    """Alla sparade versioner för en mall, nyast först."""
    template_path = Path(template_path)
    directory = _versions_dir(template_path)
    if not directory.is_dir():
        return []
    versions: List[TemplateVersionInfo] = []
    for path in directory.iterdir():
        if not path.is_file() or path.name.startswith(".tmp-"):
            continue
        if path.suffix.lower() != template_path.suffix.lower():
            continue
        try:
            versions.append(
                TemplateVersionInfo(
                    path=path,
                    template_name=template_path.name,
                    created_at=_created_at(path),
                    size=path.stat().st_size,
                )
            )
        except OSError:
            log.debug("Kunde inte läsa mallversion %s", path, exc_info=True)
    return sorted(versions, key=lambda item: (item.created_at, item.path.name), reverse=True)


def prune_template_versions(
    template_path: Path, *, keep: int = DEFAULT_KEEP_VERSIONS
) -> int:
    """Behåll de ``keep`` nyaste versionerna och ta bort äldre."""
    keep = max(1, int(keep))
    versions = list_template_versions(template_path)
    removed = 0
    for version in versions[keep:]:
        try:
            version.path.unlink()
            removed += 1
        except OSError:
            log.debug(
                "Kunde inte rensa gammal mallversion %s",
                version.path,
                exc_info=True,
            )
    return removed


def snapshot_template_version(
    template_path: Path,
    *,
    keep: int = DEFAULT_KEEP_VERSIONS,
    now: Optional[datetime] = None,
) -> Optional[Path]:
    """Spara en bytexakt version av den aktuella mallen.

    Returnerar sökvägen till versionen som representerar innehållet.
    Om senaste versionen redan har exakt samma innehåll återanvänds
    den i stället för att skapa en dubblett. Saknas mallen returneras
    ``None``.
    """
    template_path = Path(template_path)
    if not template_path.is_file():
        return None

    current_hash = _sha256(template_path)
    existing = list_template_versions(template_path)
    if existing:
        try:
            if _sha256(existing[0].path) == current_hash:
                return existing[0].path
        except OSError:
            log.debug(
                "Kunde inte jämföra senaste mallversionen", exc_info=True
            )

    directory = _versions_dir(template_path, create=True)
    stamp = (now or datetime.now()).strftime(_TIMESTAMP_FORMAT)
    target = directory / f"{stamp}{template_path.suffix}"
    counter = 1
    while target.exists():
        target = directory / f"{stamp}-{counter}{template_path.suffix}"
        counter += 1

    temp = directory / f".tmp-{target.name}"
    try:
        shutil.copy2(template_path, temp)
        os.replace(temp, target)
    finally:
        try:
            if temp.exists():
                temp.unlink()
        except OSError:
            pass

    prune_template_versions(template_path, keep=keep)
    log.info("Mallversion sparad: %s -> %s", template_path.name, target.name)
    return target


def _validate_version_path(template_path: Path, version_path: Path) -> Path:
    version_path = Path(version_path)
    expected_dir = _versions_dir(template_path).resolve()
    try:
        resolved_parent = version_path.parent.resolve()
    except OSError as exc:
        raise ValueError("Ogiltig sökväg till mallversion.") from exc
    if resolved_parent != expected_dir:
        raise ValueError("Versionen hör inte till den valda mallen.")
    if version_path.suffix.lower() != template_path.suffix.lower():
        raise ValueError("Versionen har fel filtyp för mallen.")
    if not version_path.is_file():
        raise FileNotFoundError(str(version_path))
    return version_path


def restore_template_version(
    template_path: Path,
    version_path: Path,
    *,
    keep: int = DEFAULT_KEEP_VERSIONS,
) -> Path:
    """Återställ en mall till en sparad version.

    Nuvarande innehåll versions sparas först, så återställningen kan
    ångras genom att återställa den versionen.
    """
    template_path = Path(template_path)
    version_path = _validate_version_path(template_path, version_path)

    if template_path.is_file():
        snapshot_template_version(template_path, keep=keep)

    template_path.parent.mkdir(parents=True, exist_ok=True)
    temp = template_path.with_name(f".{template_path.name}.restore-tmp")
    try:
        shutil.copy2(version_path, temp)
        os.replace(temp, template_path)
    finally:
        try:
            if temp.exists():
                temp.unlink()
        except OSError:
            pass
    log.info("Mall återställd: %s <- %s", template_path.name, version_path.name)
    return template_path


def delete_template_version(template_path: Path, version_path: Path) -> bool:
    """Ta bort en sparad mallversion."""
    validated = _validate_version_path(Path(template_path), Path(version_path))
    validated.unlink()
    return True


__all__ = [
    "DEFAULT_KEEP_VERSIONS",
    "TemplateVersionInfo",
    "VERSIONS_DIRNAME",
    "delete_template_version",
    "list_template_versions",
    "prune_template_versions",
    "restore_template_version",
    "snapshot_template_version",
]
