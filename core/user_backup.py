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


# ─────────────────────────────────────────────────────────────────────
# Komplett säkerhetskopia (ZIP) – skapa/inspektera/återställ
# ─────────────────────────────────────────────────────────────────────
# Innehåll i ZIP:en:
#   manifest.json                  format/version/datum/sektioner
#   settings/email_settings.json   inställningar UTAN lösenord
#   adresslistor/...               kontakter/kategorier
#   Mallar/...                     mallfiler
#   data/sent_history.json         sändhistorik
# Lösenord tas ALLTID bort ur inställningarna i säkerhetskopian –
# de måste fyllas i igen efter återställning.

import json as _json
import zipfile as _zipfile
from typing import Any as _Any, Dict as _Dict, List as _List

BACKUP_FORMAT = 1
_SETTINGS_ARC = "settings/email_settings.json"
_HISTORY_ARC = "data/sent_history.json"
_DIR_SECTIONS = ("adresslistor", "Mallar")


def _redact_settings_data(data: _Any) -> _Any:
    """Kopia av inställningsdata med alla 'password'-värden tömda."""
    if isinstance(data, dict):
        return {
            key: ("" if key == "password" else _redact_settings_data(value))
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [_redact_settings_data(item) for item in data]
    return data


def create_full_backup(
    base_dir: Path,
    settings_path: Optional[Path],
    dest_zip: Path,
    *,
    app_version: str = "",
    dir_sources: Optional[_Dict[str, Path]] = None,
) -> _Dict[str, _Any]:
    """Skapa en komplett säkerhetskopia som ZIP. Returnerar sammanfattning."""
    base = Path(base_dir)
    dest = Path(dest_zip)
    dest.parent.mkdir(parents=True, exist_ok=True)

    sections: _Dict[str, int] = {}

    # Läs + rensa inställningar i minnet (originalfilen rörs aldrig)
    settings_bytes: Optional[bytes] = None
    if settings_path is not None and Path(settings_path).is_file():
        try:
            raw = _json.loads(Path(settings_path).read_text(encoding="utf-8"))
            settings_bytes = _json.dumps(
                _redact_settings_data(raw), ensure_ascii=False, indent=2
            ).encode("utf-8")
        except Exception:
            log.warning(
                "Kunde inte läsa inställningar för säkerhetskopian",
                exc_info=True,
            )

    with _zipfile.ZipFile(dest, "w", _zipfile.ZIP_DEFLATED) as archive:
        file_count = 0
        if settings_bytes is not None:
            archive.writestr(_SETTINGS_ARC, settings_bytes)
            sections["settings"] = 1
            file_count += 1

        for dirname in _DIR_SECTIONS:
            src = Path((dir_sources or {}).get(dirname) or (base / dirname))
            if not src.is_dir():
                continue
            count = 0
            for path in sorted(src.rglob("*")):
                if path.is_file():
                    archive.write(
                        path, f"{dirname}/" + path.relative_to(src).as_posix()
                    )
                    count += 1
            if count:
                sections[dirname] = count
                file_count += count

        history = base / ".data" / "sent_history.json"
        if history.is_file():
            archive.write(history, _HISTORY_ARC)
            sections["history"] = 1
            file_count += 1

        manifest = {
            "format": BACKUP_FORMAT,
            "app": "E-postofferten",
            "app_version": str(app_version or ""),
            "created": _dt.datetime.now().isoformat(timespec="seconds"),
            "passwords_included": False,
            "sections": sections,
            "files": file_count,
        }
        archive.writestr(
            "manifest.json",
            _json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8"),
        )

    log.info("Säkerhetskopia skapad: %s (%d filer)", dest, file_count)
    return {"path": dest, "files": file_count, "sections": sections,
            "manifest": manifest}


def inspect_backup(zip_path: Path) -> _Dict[str, _Any]:
    """Läs och validera en säkerhetskopias manifest. ValueError vid fel."""
    path = Path(zip_path)
    if not path.is_file():
        raise ValueError("Filen finns inte.")
    try:
        with _zipfile.ZipFile(path, "r") as archive:
            names = archive.namelist()
            if "manifest.json" not in names:
                raise ValueError("Ingen manifest.json – inte en säkerhetskopia.")
            manifest = _json.loads(
                archive.read("manifest.json").decode("utf-8", errors="replace")
            )
    except _zipfile.BadZipFile as exc:
        raise ValueError("Filen är ingen giltig ZIP-fil.") from exc
    if not isinstance(manifest, dict):
        raise ValueError("Manifestet i säkerhetskopian är ogiltigt.")
    if int(manifest.get("format") or 0) != BACKUP_FORMAT:
        raise ValueError(
            f"Okänt backupformat: {manifest.get('format')!r} "
            f"(förväntade {BACKUP_FORMAT})."
        )
    return manifest


def _safe_target(root: Path, arcname: str) -> Optional[Path]:
    """Målväg för en ZIP-post, eller None om posten är ogiltig/farlig."""
    parts = [p for p in arcname.replace("\\", "/").split("/") if p]
    if not parts or any(p in (".", "..") for p in parts):
        return None
    target = root.joinpath(*parts)
    try:
        target.resolve().relative_to(root.resolve())
    except Exception:
        return None
    return target


def restore_full_backup(
    zip_path: Path,
    base_dir: Path,
    settings_path: Optional[Path],
    *,
    app_version: str = "",
    dir_targets: Optional[_Dict[str, Path]] = None,
) -> _Dict[str, _Any]:
    """Återställ en säkerhetskopia.

    Skapar först en automatisk säkerhetskopia av nuvarande data i
    ``.data/backups/``. Avbryter (ValueError) om ZIP:en är ogiltig
    eller innehåller osäkra sökvägar.
    """
    manifest = inspect_backup(zip_path)
    base = Path(base_dir)

    # 1) Säkerhetskopia av läget FÖRE återställning
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    safety = base / ".data" / "backups" / f"fore-aterstallning-{stamp}.zip"
    try:
        create_full_backup(base, settings_path, safety, app_version=app_version,
                           dir_sources=dir_targets)
    except Exception as exc:
        raise ValueError(
            "Kunde inte skapa säkerhetskopia av nuvarande data – "
            "återställningen avbröts."
        ) from exc

    restored: _List[str] = []
    with _zipfile.ZipFile(Path(zip_path), "r") as archive:
        for info in archive.infolist():
            name = info.filename
            if name.endswith("/") or name == "manifest.json":
                continue
            data = archive.read(name)
            if name == _SETTINGS_ARC:
                if settings_path is None:
                    continue
                target = Path(settings_path)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                restored.append("settings")
                continue
            if name == _HISTORY_ARC:
                target = base / ".data" / "sent_history.json"
            elif name.split("/")[0] in _DIR_SECTIONS:
                section_root = Path(
                    (dir_targets or {}).get(name.split("/")[0])
                    or (base / name.split("/")[0])
                )
                target = _safe_target(section_root, "/".join(name.split("/")[1:]))
                if target is None:
                    raise ValueError(f"Osäker sökväg i säkerhetskopian: {name}")
            else:
                continue  # okända poster ignoreras
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            section = name.split("/")[0]
            if section not in restored:
                restored.append(section)

    log.info("Säkerhetskopia återställd från %s (sektioner: %s)",
             zip_path, ", ".join(restored))
    return {
        "manifest": manifest,
        "restored_sections": restored,
        "safety_backup": safety,
    }


__all__ += [
    "BACKUP_FORMAT",
    "create_full_backup",
    "inspect_backup",
    "restore_full_backup",
]
