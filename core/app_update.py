#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Transaktionssäker appuppdatering från mapp – rör ALDRIG användardata.

Säkerhetsgarantier:
1. Alla skyddade sökvägar (JSON, inställningar, adresslistor, loggar,
   Mallar/, .data/) lämnas garanterat orörda.
2. Körbara binärer/installerare (.exe, .dll, .msi, .scr m.fl.) kopieras aldrig.
3. Osäkra symboliska länkar / junctions i källa eller mål avvisas innan
   någon fil ändras.
4. Alla inkommande Python-filer valideras mot NUL-byte-korruption och
   kompileras i minnet (``compile(..., 'exec')``) före installation, så att
   trasig syntax aldrig kan göra appen ostartbar.
5. Varje fil skrivs först till en temporär syskonfil, fsyncas, kontrollräknas
   med SHA-256 och växlas in atomärt med ``os.replace``.
6. Automatisk återställning (rollback): om kopiering eller kontrollsumma
   misslyckas för en enda fil återställs alla redan ersatta filer från en
   temporär återställningskopia och nya delfiler städas bort.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import os
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from core.update_protect import is_protected

log = logging.getLogger(__name__)

SKIP_DIR_NAMES = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".data",
    "adresslistor",
    "logs",
}

BLOCKED_BINARY_SUFFIXES = frozenset(
    {
        ".exe",
        ".dll",
        ".msi",
        ".scr",
        ".com",
        ".pif",
        ".cpl",
        ".hta",
        ".sys",
    }
)

_SENSITIVE_JSON_KEYS = frozenset(
    {
        "smtp_password",
        "password",
        "pass",
        "secret",
        "token",
        "api_key",
    }
)

MAX_PRE_UPDATE_BACKUPS = 3


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_unsafe_link(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junc = getattr(path, "is_junction", None)
        if callable(is_junc) and is_junc():
            return True
    except OSError:
        return True
    return False


def _has_unsafe_ancestor_link(target: Path, root: Path) -> bool:
    if _is_unsafe_link(target):
        return True
    for parent in target.parents:
        if parent == root:
            break
        if root in parent.parents and _is_unsafe_link(parent):
            return True
    return False


def _redact_credentials(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: ("" if str(k).lower() in _SENSITIVE_JSON_KEYS else _redact_credentials(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [_redact_credentials(item) for item in obj]
    return obj


def create_pre_update_user_backup(dest: Path) -> Optional[Path]:
    """Skapa en rullande säkerhetskopia av användardata (utan lösenord) före uppdatering."""
    dest = Path(dest).resolve()
    candidates: List[tuple[Path, str]] = []
    for name in ("email_settings.json", "contacts.json", "sent_history.json"):
        fp = dest / name
        if fp.is_file() and not _is_unsafe_link(fp):
            candidates.append((fp, name))
    for folder_name in ("adresslistor", "Mallar"):
        folder = dest / folder_name
        if folder.is_dir() and not _is_unsafe_link(folder):
            for child in sorted(folder.rglob("*")):
                if child.is_file() and not _is_unsafe_link(child):
                    rel = child.relative_to(dest).as_posix()
                    candidates.append((child, rel))

    if not candidates:
        return None

    backup_dir = dest / ".data" / "pre_update_backups"
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        fd, tmp_name = tempfile.mkstemp(
            dir=str(backup_dir), prefix=f"pre-update-{stamp}-", suffix=".tmp"
        )
        os.close(fd)
        tmp_zip = Path(tmp_name)
        final_zip = backup_dir / f"pre-update-{stamp}.zip"
        try:
            with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
                for src_file, arcname in candidates:
                    if src_file.name.lower() == "email_settings.json":
                        try:
                            parsed = json.loads(
                                src_file.read_text(encoding="utf-8", errors="replace")
                            )
                            safe_bytes = json.dumps(
                                _redact_credentials(parsed),
                                ensure_ascii=False,
                                indent=2,
                            ).encode("utf-8")
                            zf.writestr(arcname, safe_bytes)
                            continue
                        except Exception:
                            continue
                    zf.write(src_file, arcname=arcname)
            os.replace(tmp_zip, final_zip)
        finally:
            tmp_zip.unlink(missing_ok=True)

        existing = sorted(
            backup_dir.glob("pre-update-*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for old in existing[MAX_PRE_UPDATE_BACKUPS:]:
            old.unlink(missing_ok=True)
        return final_zip
    except Exception:
        log.debug("Förhandsbackup före uppdatering hoppades över", exc_info=True)
        return None


def cleanup_pre_update_backups(dest: Path) -> int:
    """Ta bort temporära förhandsbackuper när uppdateringen lyckats."""
    backup_dir = Path(dest).resolve() / ".data" / "pre_update_backups"
    if not backup_dir.exists() or _is_unsafe_link(backup_dir):
        return 0
    removed = 0
    try:
        for item in list(backup_dir.iterdir()):
            if _is_unsafe_link(item) or not item.is_file():
                continue
            if (
                item.name.startswith("pre-update-")
                and item.suffix.lower() in (".zip", ".tmp")
            ):
                try:
                    item.unlink(missing_ok=True)
                    removed += 1
                except OSError:
                    pass
        if not any(backup_dir.iterdir()):
            backup_dir.rmdir()
    except OSError:
        log.debug("Kunde inte städa förhandsbackupmapp helt", exc_info=True)
    return removed


def validate_python_sources(
    src: Path, *, strict_pyw: Optional[bool] = None
) -> List[str]:
    """Kontrollera att inga Python-källfiler i uppdateringen är skadade/ogiltiga."""
    src = Path(src).resolve()
    errors: List[str] = []
    check_pyw = (
        bool(strict_pyw)
        if strict_pyw is not None
        else (src / "core" / "version.py").is_file()
    )
    for path in sorted(src.rglob("*")):
        try:
            rel = path.relative_to(src)
        except Exception:
            continue
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        if _is_unsafe_link(path):
            errors.append(f"Symbolisk länk tillåts inte i uppdatering: {rel.as_posix()}")
            continue
        if not path.is_file():
            continue
        if is_protected(path, src):
            continue
        suffix = path.suffix.lower()
        if suffix not in (".py", ".pyw"):
            continue
        try:
            raw = path.read_bytes()
        except Exception as exc:
            errors.append(f"{rel.as_posix()}: kunde inte läsa källfil ({exc})")
            continue
        if b"\x00" in raw:
            errors.append(f"{rel.as_posix()}: filen innehåller NUL-byte (skadad fil)")
            continue
        if suffix == ".py" or check_pyw:
            try:
                compile(raw, rel.as_posix(), "exec")
            except SyntaxError as exc:
                errors.append(
                    f"{rel.as_posix()}: ogiltig Python-syntax på rad {exc.lineno}: {exc.msg}"
                )
            except Exception as exc:
                errors.append(f"{rel.as_posix()}: källkontroll misslyckades ({exc})")
    return errors


def _validate_paths_relationship(src: Path, dest: Path) -> Optional[str]:
    if src == dest:
        return "Källmappen är samma mapp som den aktiva installationen."
    if src in dest.parents:
        return "Installationsmappen ligger inuti källmappen – avbryter."
    if dest in src.parents:
        rel = src.relative_to(dest)
        if not (rel.parts and rel.parts[0] == ".data"):
            return "Källmappen ligger inuti den aktiva installationsmappen – avbryter."
    return None


def apply_update_from_dir(
    src: Path,
    dest: Path,
    *,
    require_app_root: bool = False,
    strict_syntax: Optional[bool] = None,
    backup_user_data: bool = False,
    cleanup_backup_on_success: bool = True,
    on_progress: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Kopiera kod från ``src`` → ``dest`` atomärt med automatisk återställning.

    JSON/settings/adresslistor/loggar/Mallar hoppas alltid över.

    Returns: ``{copied, skipped, errors, rolled_back, backup_path}``
    """
    copied: List[str] = []
    skipped: List[str] = []
    errors: List[str] = []

    raw_src = Path(src)
    raw_dest = Path(dest)
    if _is_unsafe_link(raw_src) or _is_unsafe_link(raw_dest):
        return {
            "copied": copied,
            "skipped": skipped,
            "errors": ["Osäker symbolisk länk i käll- eller målmapp"],
            "rolled_back": False,
            "backup_path": "",
        }

    src = raw_src.resolve()
    dest = raw_dest.resolve()

    if not src.is_dir():
        return {
            "copied": copied,
            "skipped": skipped,
            "errors": ["Källmappen finns inte"],
            "rolled_back": False,
            "backup_path": "",
        }

    rel_err = _validate_paths_relationship(src, dest)
    if rel_err:
        return {
            "copied": copied,
            "skipped": skipped,
            "errors": [rel_err],
            "rolled_back": False,
            "backup_path": "",
        }

    if require_app_root and not (src / "main.pyw").is_file():
        return {
            "copied": copied,
            "skipped": skipped,
            "errors": ["Mappen saknar main.pyw och ser inte ut som E-postofferten."],
            "rolled_back": False,
            "backup_path": "",
        }

    if on_progress:
        on_progress("Kontrollerar paketsäkerhet och validerar Python-filer…")

    files_to_copy: List[tuple[Path, Path, Path]] = []
    dirs_to_ensure: List[Path] = []
    total_bytes = 0

    for path in sorted(src.rglob("*")):
        try:
            rel = path.relative_to(src)
        except Exception:
            continue
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            skipped.append(str(rel))
            continue
        if _is_unsafe_link(path):
            errors.append(f"Symbolisk länk i uppdatering: {rel.as_posix()}")
            continue
        if path.suffix.lower() in BLOCKED_BINARY_SUFFIXES:
            skipped.append(str(rel))
            continue
        target = dest / rel
        if is_protected(target, dest) or is_protected(path, src):
            skipped.append(str(rel))
            continue
        if dest.exists() and _has_unsafe_ancestor_link(target, dest):
            errors.append(f"Osäker lokal länk: {rel.as_posix()}")
            continue
        if path.is_dir():
            dirs_to_ensure.append(target)
            continue
        if not path.is_file():
            continue
        try:
            total_bytes += path.stat().st_size
        except OSError as exc:
            errors.append(f"{rel}: {exc}")
            continue
        files_to_copy.append((path, target, rel))

    if not errors:
        syntax_errors = validate_python_sources(src, strict_pyw=strict_syntax)
        if syntax_errors:
            errors.extend(syntax_errors)

    if errors:
        return {
            "copied": copied,
            "skipped": skipped,
            "errors": errors,
            "rolled_back": False,
            "backup_path": "",
        }

    try:
        dest.mkdir(parents=True, exist_ok=True)
        free_bytes = shutil.disk_usage(dest).free
        required = total_bytes * 2 + 2 * 1024 * 1024
        if free_bytes < required:
            return {
                "copied": copied,
                "skipped": skipped,
                "errors": [
                    f"För lite ledigt diskutrymme ({free_bytes // (1024 * 1024)} MB ledigt)."
                ],
                "rolled_back": False,
                "backup_path": "",
            }
    except OSError:
        pass

    backup_file: Optional[Path] = None
    if backup_user_data:
        if on_progress:
            on_progress("Skapar lokal säkerhetskopia av användardata…")
        backup_file = create_pre_update_user_backup(dest)

    if on_progress:
        on_progress(f"Installerar {len(files_to_copy)} appfiler atomärt…")

    rollback_root = Path(tempfile.mkdtemp(prefix="mailoffer-rollback-"))
    overwritten: List[tuple[Path, Path]] = []
    created_files: List[Path] = []
    created_dirs: List[Path] = []
    rolled_back = False
    pid = os.getpid()

    try:
        for dpath in dirs_to_ensure:
            if not dpath.exists():
                dpath.mkdir(parents=True, exist_ok=True)
                created_dirs.append(dpath)

        for idx, (src_file, target, rel) in enumerate(files_to_copy):
            staged_tmp = target.parent / f".mailoffer-upd-{pid}-{idx}.tmp"
            try:
                if not target.parent.exists():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    created_dirs.append(target.parent)

                expected_hash = _file_sha256(src_file)
                shutil.copy2(src_file, staged_tmp)
                if not staged_tmp.is_file():
                    raise IOError("Temporär installationsfil skapades inte")
                try:
                    with staged_tmp.open("rb") as fh:
                        os.fsync(fh.fileno())
                except OSError:
                    pass
                actual_hash = _file_sha256(staged_tmp)
                if actual_hash != expected_hash:
                    raise IOError("SHA-256-kontroll misslyckades för temporär fil")

                had_existing = target.is_file()
                if had_existing:
                    backup_copy = rollback_root / rel
                    backup_copy.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(target, backup_copy)
                    os.replace(staged_tmp, target)
                    overwritten.append((backup_copy, target))
                else:
                    os.replace(staged_tmp, target)
                    created_files.append(target)

                copied.append(str(rel))
            except Exception as exc:
                errors.append(f"{rel}: {exc}")
                log.warning("Uppdatering misslyckades för %s – återställer", rel, exc_info=True)
                break
            finally:
                staged_tmp.unlink(missing_ok=True)

        if errors:
            for child in reversed(created_files):
                try:
                    child.unlink(missing_ok=True)
                except OSError:
                    pass
            for backup_copy, target in reversed(overwritten):
                try:
                    rollback_tmp = target.parent / f".mailoffer-rb-{pid}.tmp"
                    shutil.copy2(backup_copy, rollback_tmp)
                    os.replace(rollback_tmp, target)
                except Exception:
                    log.error("Kunde inte återställa %s vid rollback", target, exc_info=True)
            for dpath in reversed(created_dirs):
                try:
                    if dpath.is_dir() and not any(dpath.iterdir()):
                        dpath.rmdir()
                except OSError:
                    pass
            rolled_back = bool(overwritten or created_files)
            copied.clear()
    finally:
        shutil.rmtree(rollback_root, ignore_errors=True)

    backup_cleaned = False
    if not errors and backup_user_data and cleanup_backup_on_success:
        cleanup_pre_update_backups(dest)
        backup_file = None
        backup_cleaned = True

    log.info(
        "App-uppdatering: %d kopierade, %d hoppade över, %d fel, återställd=%s",
        len(copied),
        len(skipped),
        len(errors),
        rolled_back,
    )
    return {
        "copied": copied,
        "skipped": skipped,
        "errors": errors,
        "rolled_back": rolled_back,
        "backup_path": str(backup_file) if backup_file else "",
        "backup_cleaned": backup_cleaned,
    }


__all__ = [
    "BLOCKED_BINARY_SUFFIXES",
    "SKIP_DIR_NAMES",
    "apply_update_from_dir",
    "cleanup_pre_update_backups",
    "create_pre_update_user_backup",
    "validate_python_sources",
]
