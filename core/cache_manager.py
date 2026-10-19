#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/cache_manager.py
=====================

Dev/prod cache cleanup, temporära filer, fail-safe.

Version: 1.2 – OPTIMERAD (snabba upp appen)

Fixar mot v1.1:
  - ✅ Rensning görs med EN enda os.walk (ej flera rglob-svep)
  - ✅ Skyddade kataloger prunade UNDER vandringen
        → cleanup() rör aldrig Mallar/, logs/, .data/, adresslistor/,
          plugins/, contacts.json – och söker inte igenom dem heller
  - ✅ is_protected() utan tunga resolve()-anrop
        (normcase + prefix-jämförelse, snabbt även på Windows)
  - ✅ base_dir i sig är alltid skyddad – kan aldrig raderas
  - ✅ cleanup_pycache()/cleanup_pyc_files() delar samma vandring
  - ✅ Bakåtkompatibla _-alias kvar (v1.0/v1.1 API)

Fixar mot v1.0:
  - Publika metoder enligt spec §13/§20:
    cleanup_pycache(), cleanup_pyc_files(), cleanup_preview_tmp(),
    is_protected(), remove_path()
  - tempfile importerat överst (spec §4)
  - __repr__ inkluderar base_dir

PROD MODE (mode="prod" eller smart_cache=False):
  - Rensar __pycache__/ och *.pyc vid exit
  - Rensar temporära HTML-filer (preview)
  - Rensar runtime temp-kataloger

DEV MODE (mode="dev"):
  - Cache behålls mellan sessioner
  - Endast registrerade temp-filer rensas

RENSAS ALDRIG:
  - user data (contacts.json, adresslistor/)
  - settings (.data/settings.json)
  - plugin data
  - logs/
  - Mallar/
  - själva base_dir (applikationsroten)

FIL: core/cache_manager.py
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import List

log = logging.getLogger(__name__)


class CacheManager:
    """
    Hanterar cache-rensning vid programavslut.

    Användning::

        cache = CacheManager(base_dir, mode="prod")
        cache.register_temp_file(some_tmp_path)
        # vid exit:
        cache.cleanup()
    """

    # Kataloger och filer som ALDRIG får röras (relativa base_dir)
    _PROTECTED = frozenset({
        "contacts.json",
        "adresslistor",
        ".data",
        "logs",
        "Mallar",
        "plugins",
    })

    def __init__(
        self,
        base_dir:    Path,
        mode:        str  = "prod",
        smart_cache: bool = True,
    ) -> None:
        """
        Args:
            base_dir:    Applikationens rotkatalog
            mode:        "prod" eller "dev"
            smart_cache: Om False: behandla alltid som prod
        """
        self._base_dir    = Path(base_dir).resolve()
        self._mode        = mode.lower().strip()
        self._smart_cache = bool(smart_cache)
        self._temp_files: List[Path] = []

        # Förberäknade skyddade prefix (snabba strängjämförelser,
        # inga resolve()-anrop i is_protected)
        self._base_prefix      = self._build_base_prefix()
        self._protected_prefixes = self._build_protected_prefixes()

        log.debug(
            "CacheManager initierad: base=%s mode=%s smart_cache=%s",
            self._base_dir, self._mode, self._smart_cache,
        )

    # ------------------------------------------------------------------
    # Intern: skyddade prefix
    # ------------------------------------------------------------------

    def _build_base_prefix(self) -> List[str]:
        """Absolut normerad base_dir (exakt matchning = alltid skyddad)."""
        return os.path.normcase(
            os.path.abspath(str(self._base_dir))
        ).split(os.sep)

    def _build_protected_prefixes(self) -> List[List[str]]:
        """Bygg lista över skyddade absoluta sökvägsprefix (normcase)."""
        base = os.path.normcase(os.path.abspath(str(self._base_dir)))
        prefixes: List[List[str]] = []
        for name in self._PROTECTED:
            clean = name.rstrip("/\\")
            if not clean:
                continue
            prefixes.append((base + os.sep + clean).split(os.sep))
        return prefixes

    # ------------------------------------------------------------------
    # Publikt API – temp-filer
    # ------------------------------------------------------------------

    def register_temp_file(self, path: Path) -> None:
        """
        Registrera en temporär fil för rensning vid cleanup().

        Filen rensas oavsett mode (dev eller prod).

        Args:
            path: Sökväg till temporär fil.
        """
        p = Path(path)
        if p not in self._temp_files:
            self._temp_files.append(p)
            log.debug("Registrerade temp-fil: %s", p)

    def clear_temp_files(self) -> None:
        """
        Rensa enbart registrerade temporära filer.

        Kallas t.ex. när en preview stängs.
        """
        removed = 0
        for path in list(self._temp_files):
            removed += self.remove_path(path)
        self._temp_files.clear()
        if removed:
            log.debug("Rensade %d temp-filer.", removed)

    # ------------------------------------------------------------------
    # Publikt API – huvudoperation
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """
        Kör full cache-rensning vid programavslut.

        - Alltid: rensa registrerade temp-filer
        - PROD MODE eller smart_cache=False:
            rensa __pycache__, *.pyc, preview-tmpfiler
        - DEV MODE: rensa bara temp-filer
        """
        log.info(
            "CacheManager.cleanup() – mode=%s smart_cache=%s",
            self._mode, self._smart_cache,
        )

        # Alltid: rensa registrerade temp-filer
        self.clear_temp_files()

        # Prod-rensning – EN enda vandring för __pycache__ + *.pyc
        if self._mode == "prod" or not self._smart_cache:
            removed = self._sweep(remove_pycache=True, remove_pyc=True)
            self.cleanup_preview_tmp()
            if removed:
                log.debug("Rensade %d cache-objekt.", removed)
        else:
            log.debug("DEV MODE – hoppar över cache-rensning.")

        log.info("CacheManager.cleanup() klar.")

    # ------------------------------------------------------------------
    # Publika rensningsmetoder (spec §13/§20)
    # ------------------------------------------------------------------

    def cleanup_pycache(self) -> None:
        """
        Rensa alla __pycache__-kataloger rekursivt under base_dir.

        Skyddade kataloger (logs/, .data/, etc.) lämnas orörda – och
        genomsöks inte ens. Fail-safe: kastar aldrig exception.
        """
        removed = self._sweep(remove_pycache=True, remove_pyc=False)
        if removed:
            log.debug("Rensade %d __pycache__-kataloger.", removed)

    def cleanup_pyc_files(self) -> None:
        """
        Rensa alla *.pyc-filer rekursivt under base_dir.

        Skyddade sökvägar lämnas orörda. Fail-safe: kastar aldrig exception.
        """
        removed = self._sweep(remove_pycache=False, remove_pyc=True)
        if removed:
            log.debug("Rensade %d .pyc-filer.", removed)

    def cleanup_preview_tmp(self) -> None:
        """
        Rensa temporära HTML-filer skapade av preview.py.

        Söker efter emailapp_preview_*.html i systemets tmp-katalog.
        Fail-safe: kastar aldrig exception.
        """
        removed = 0
        try:
            tmp_dir = Path(tempfile.gettempdir())
            for f in tmp_dir.glob("emailapp_preview_*.html"):
                removed += self.remove_path(f)
        except Exception:
            log.exception("cleanup_preview_tmp: oväntat fel")
        if removed:
            log.debug("Rensade %d preview-tmpfiler.", removed)

    # ------------------------------------------------------------------
    # Publika hjälpmetoder (spec §13/§20)
    # ------------------------------------------------------------------

    def is_protected(self, path: Path) -> bool:
        """
        Kontrollera om en sökväg är skyddad mot rensning.

        Skyddade sökvägar:
          - contacts.json
          - adresslistor/
          - .data/
          - logs/
          - Mallar/
          - plugins/
          - själva base_dir

        Args:
            path: Sökväg att kontrollera

        Returns:
            True om sökvägen är skyddad (INTE får rensas).
            Vid osäkerhet returneras True (skydda hellre).
        """
        try:
            parts = os.path.normcase(os.path.abspath(str(path))).split(os.sep)
            # base_dir i sig: EXAKT matchning (alla ättlingar är ej skyddade)
            if len(parts) == len(self._base_prefix) and parts == self._base_prefix:
                return True
            # Skyddade underkataloger/filer: prefix-matchning
            for prefix in self._protected_prefixes:
                if len(parts) >= len(prefix) and parts[:len(prefix)] == prefix:
                    return True
        except Exception:
            # Vid tveksamhet – skydda
            return True
        return False

    def remove_path(self, path: Path) -> int:
        """
        Ta bort fil eller katalog säkert.

        Skyddade sökvägar lämnas orörda (loggas som warning).
        Fail-safe: kastar aldrig exception.

        Args:
            path: Fil eller katalog att ta bort

        Returns:
            1 om sökvägen togs bort, 0 annars.
        """
        try:
            p = Path(path)
            if not p.exists():
                return 0
            if self.is_protected(p):
                log.warning(
                    "remove_path: försökte ta bort skyddad sökväg: %s",
                    p,
                )
                return 0
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)
            log.debug("Tog bort: %s", p)
            return 1
        except Exception as exc:
            # Fail-safe: logga men kasta ALDRIG exception
            log.warning(
                "remove_path: kunde inte ta bort %s: %s",
                path, exc,
            )
            return 0

    # ------------------------------------------------------------------
    # Intern vandring (den snabba delen – v1.2)
    # ------------------------------------------------------------------

    def _sweep(
        self,
        remove_pycache: bool = True,
        remove_pyc:     bool = True,
    ) -> int:
        """
        En enda os.walk-vandring under base_dir.

        - Skyddade kataloger prunas REDAN vid nedstigning
          (de genomsöks aldrig – stora vinster när Mallar/logs är tunga)
        - __pycache__-kataloger raderas på stället utan att gå in i dem
        - Fristående *.pyc-filer raderas

        Fail-safe: kastar aldrig exception.
        """
        removed = 0
        try:
            for root, dirs, files in os.walk(
                self._base_dir,
                topdown=True,
                followlinks=False,
            ):
                if remove_pycache:
                    keep: List[str] = []
                    for d in dirs:
                        full = os.path.join(root, d)
                        if self.is_protected(full):
                            continue
                        if d == "__pycache__":
                            removed += self._rmtree(full)
                            continue
                        keep.append(d)
                    dirs[:] = keep
                else:
                    dirs[:] = [
                        d for d in dirs
                        if not self.is_protected(os.path.join(root, d))
                    ]

                if remove_pyc:
                    for f in files:
                        if f.endswith(".pyc"):
                            removed += self._unlink(os.path.join(root, f))
        except Exception:
            log.exception("_sweep: oväntat fel")
        return removed

    def _rmtree(self, path: str) -> int:
        """Ta bort katalog utan att kasta. Returnerar 1 om borta."""
        try:
            shutil.rmtree(path, ignore_errors=True)
            return 0 if os.path.exists(path) else 1
        except Exception:
            return 0

    def _unlink(self, path: str) -> int:
        """Ta bort fil utan att kasta. Returnerar 1 om borta."""
        try:
            os.remove(path)
            return 1
        except FileNotFoundError:
            return 0
        except Exception as exc:
            log.warning("Kunde inte ta bort %s: %s", path, exc)
            return 0

    # ------------------------------------------------------------------
    # Privata alias (bakåtkompatibilitet med v1.0/v1.1)
    # ------------------------------------------------------------------

    _cleanup_pycache     = cleanup_pycache
    _cleanup_pyc_files   = cleanup_pyc_files
    _cleanup_preview_tmp = cleanup_preview_tmp
    _is_protected        = is_protected
    _remove_path         = remove_path

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"CacheManager("
            f"base_dir={str(self._base_dir)!r}, "
            f"mode={self._mode!r}, "
            f"smart_cache={self._smart_cache}, "
            f"temp_files={len(self._temp_files)})"
        )


__all__ = ["CacheManager"]
