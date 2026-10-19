#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Skyddade sökvägar vid uppdatering från GitHub.

JSON och inställningar ska ALDRIG skrivas över, raderas eller
ersättas av en uppdatering.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

# Relativa mappar/filer under projektroten som uppdatering FÅR INTE röra
# "Mallar" (v5.4): användarens egna mallar – inkl. wizard-skapade – är
# användardata och får aldrig skrivas över av en GitHub-release.
# Nackdel: nya exempelmallar i en release når inte befintliga
# installationer automatiskt (medvetet val – dataskydd går först).
PROTECTED_DIRS = (
    "adresslistor",
    ".data",
    "logs",
    "Mallar",
)
PROTECTED_NAMES = (
    "email_settings.json",
    "sent_history.json",
    "contacts.json",
)
PROTECTED_SUFFIXES = (
    ".json",
    ".json.bak",
)

# Undantag: källkods-JSON som FÅR uppdateras med appen
CODE_JSON_OK = {
    "thunderbird/manifest.json",
}


def _norm(path: Path) -> str:
    return str(path).replace("\\", "/").lstrip("./").lower()


def is_protected(path: Path, base_dir: Path) -> bool:
    """True om sökvägen är användardata och inte får röras vid uppdatering."""
    try:
        rel = Path(path).resolve().relative_to(Path(base_dir).resolve())
    except Exception:
        name = Path(path).name.lower()
        if name in {n.lower() for n in PROTECTED_NAMES}:
            return True
        if Path(path).suffix.lower() in {".json", ".bak"} and name.endswith(".json"):
            return True
        return False
    rel_s = _norm(rel)
    if rel_s in CODE_JSON_OK:
        return False
    parts = rel.parts
    if parts and parts[0].lower() in {d.lower() for d in PROTECTED_DIRS}:
        return True
    if rel.name.lower() in {n.lower() for n in PROTECTED_NAMES}:
        return True
    if rel.suffix.lower() == ".json":
        return True
    if rel.name.lower().endswith(".json.bak"):
        return True
    return False


def protected_roots(base_dir: Path) -> Iterable[Path]:
    root = Path(base_dir)
    for name in PROTECTED_DIRS:
        yield root / name


__all__ = [
    "PROTECTED_DIRS",
    "PROTECTED_NAMES",
    "is_protected",
    "protected_roots",
]
