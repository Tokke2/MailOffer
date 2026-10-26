#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Autouppdatering från GitHub Releases för E-postofferten.

Flöde:
1. ``check_for_update()`` frågar GitHub-API:t efter senaste *release*
   (``/repos/{repo}/releases/latest``) och jämför ``tag_name`` med den
   installerade versionen (``core/version.py``). Om versionsnumret är
   SAMMA jämförs även byggstämpel (``BUILD_ID`` mot releasens
   "build:"-markering) och ett release-fingeravtryck av releasens
   metadata, så att uppdaterade filer i t.ex. v1.0.0 ändå erbjuds som
   uppdatering (ägarbeslut 2026-10-21).
2. ``apply_github_update()`` laddar ner release-zip:en (bifogad
   ``.zip``-asset om den finns, annars ``zipball_url``), packar upp
   den säkert (zip-slip-skydd) och delegerar kopieringen till
   ``core/app_update.apply_update_from_dir`` – som ALDRIG rör JSON,
   inställningar, adresslistor eller mallmappen (``update_protect``).

Beslut (användaren 2026-10-19): ENDAST Releases – appen följer alltså
inte ``main``-branchen. Finns ingen publicerad release rapporteras
``no_releases=True`` (inget fel, bara inget att hämta än).

All nätverkslogik går via en injicerbar ``fetcher`` så hela modulen
kan enhetstestas utan internet:

    fetcher(url: str, timeout: float) -> tuple[int, bytes]

FIL: core/github_update.py
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import logging
import re
import shutil
import tempfile
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from core.version import (
    BUILD_ID as CURRENT_BUILD_ID,
    GITHUB_REPO,
    __version__ as CURRENT_VERSION,
)

log = logging.getLogger(__name__)

API_BASE = "https://api.github.com"
MAX_ZIP_BYTES = 200 * 1024 * 1024  # 200 MB – skydd mot trasiga svar
AUTO_CHECK_INTERVAL_HOURS = 12

Fetcher = Callable[[str, float], Tuple[int, bytes]]


# ───────────────────────────────────────────────────────────────────────
# Versionsjämförelse (ren logik – testbar)
# ───────────────────────────────────────────────────────────────────────

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")


def parse_version(value: object) -> Tuple[int, ...]:
    """Tolka versionssträng till jämförelsetupel.

    "v5.4.0" → (5, 4, 0); "5.4" → (5, 4); "v5.4.0-beta1" → (5, 4, 0);
    ogiltigt/tomt → (). Suffix efter siffrorna ignoreras medvetet –
    releaser i detta projekt taggas med ren SemVer.
    """
    match = _VERSION_RE.search(str(value or ""))
    if not match:
        return ()
    try:
        return tuple(int(part) for part in match.group(1).split("."))
    except ValueError:
        return ()


def _padded(version: Tuple[int, ...], length: int) -> Tuple[int, ...]:
    return version + (0,) * max(0, length - len(version))


def compare_versions(a: object, b: object) -> int:
    """-1 om a < b, 0 om lika, 1 om a > b. "5.4" == "5.4.0"."""
    pa, pb = parse_version(a), parse_version(b)
    size = max(len(pa), len(pb))
    pa, pb = _padded(pa, size), _padded(pb, size)
    if pa < pb:
        return -1
    if pa > pb:
        return 1
    return 0


def is_newer_version(latest: object, current: object) -> bool:
    """True om ``latest`` är strikt nyare än ``current``."""
    if not parse_version(latest):
        return False
    return compare_versions(latest, current) > 0


def normalize_tag(tag: object) -> str:
    """Versionssträng ur en release-tagg: "v5.4.0" → "5.4.0"."""
    match = _VERSION_RE.search(str(tag or ""))
    return match.group(1) if match else ""


_BUILD_MARKER_RE = re.compile("(?i)build *: *([A-Za-z0-9._+-]+)")


def parse_build_id(value: object) -> str:
    """Byggstämpel ur release-text: "build: 2026102102" → "2026102102".

    Accepterar antingen en release-payload (dict – namn + text söks
    igenom) eller en ren sträng. Saknas markering returneras "".
    """
    if isinstance(value, dict):
        text = f"{value.get('name') or ''} {value.get('body') or ''}"
    else:
        text = str(value or "")
    match = _BUILD_MARKER_RE.search(text)
    return match.group(1).strip() if match else ""


def _is_newer_build(latest: object, current: object) -> bool:
    """True om releasens byggstämpel är nyare än den installerade.

    Numeriska stämplar (t.ex. datum + löpnummer) jämförs numeriskt;
    övriga stämplar räknas som nyare om de skiljer sig åt.
    """
    latest_s = str(latest or "").strip()
    current_s = str(current or "").strip()
    if not latest_s or not current_s:
        return False
    if latest_s.isdigit() and current_s.isdigit():
        return int(latest_s) > int(current_s)
    return latest_s != current_s


def release_fingerprint(payload: Dict[str, Any]) -> str:
    """Stabilt fingeravtryck av en releases nedladdningsbara innehåll.

    Bygger på fält som ändras när releasens FILER ändras (ny commit för
    taggen, ompublicerad release, utbytt zip-asset) men INTE när bara
    release-texten redigeras. Returnerar "" för ogiltig payload.
    """
    if not isinstance(payload, dict):
        return ""
    assets: list = []
    raw_assets = payload.get("assets")
    if isinstance(raw_assets, list):
        for asset in raw_assets:
            if not isinstance(asset, dict):
                continue
            assets.append({
                "id": asset.get("id"),
                "name": str(asset.get("name") or ""),
                "size": asset.get("size"),
                "created_at": str(asset.get("created_at") or ""),
                "updated_at": str(asset.get("updated_at") or ""),
                "digest": str(asset.get("digest") or ""),
                "browser_download_url": str(
                    asset.get("browser_download_url") or ""
                ),
            })
    assets.sort(key=lambda item: (item["name"], str(item["id"])))
    data = {
        "id": payload.get("id"),
        "tag_name": str(payload.get("tag_name") or ""),
        "target_commitish": str(payload.get("target_commitish") or ""),
        "created_at": str(payload.get("created_at") or ""),
        "published_at": str(payload.get("published_at") or ""),
        "zipball_url": str(payload.get("zipball_url") or ""),
        "tarball_url": str(payload.get("tarball_url") or ""),
        "assets": assets,
    }
    encoded = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


# ───────────────────────────────────────────────────────────────────────
# Auto-check-planering (ren logik – testbar)
# ───────────────────────────────────────────────────────────────────────

def now_iso(now: Optional[_dt.datetime] = None) -> str:
    """Aktuell tid som ISO-sträng (sekundprecision, lokal tid)."""
    moment = now or _dt.datetime.now()
    return moment.replace(microsecond=0).isoformat()


def should_auto_check(
    last_check_iso: object,
    now: Optional[_dt.datetime] = None,
    interval_hours: float = AUTO_CHECK_INTERVAL_HOURS,
) -> bool:
    """True om det är dags för automatisk uppdateringssökning.

    Tom/ogiltig tidsstämpel → True (aldrig sökt). Framtida tidsstämpel
    (klockan flyttad) → True hellre än att fastna för evigt.
    """
    text = str(last_check_iso or "").strip()
    if not text:
        return True
    try:
        last = _dt.datetime.fromisoformat(text)
    except ValueError:
        return True
    moment = now or _dt.datetime.now()
    try:
        age = moment - last
    except TypeError:  # aware/naive-blandning
        return True
    if age.total_seconds() < 0:
        return True
    return age >= _dt.timedelta(hours=float(interval_hours))


# ───────────────────────────────────────────────────────────────────────
# GitHub API
# ───────────────────────────────────────────────────────────────────────

@dataclass
class UpdateInfo:
    """Resultat av en uppdateringssökning."""

    available: bool = False
    latest_version: str = ""
    tag: str = ""
    name: str = ""
    notes: str = ""
    download_url: str = ""
    html_url: str = ""
    build_id: str = ""
    fingerprint: str = ""
    same_version_files_changed: bool = False
    error: str = ""
    no_releases: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)


def _default_fetcher(url: str, timeout: float) -> Tuple[int, bytes]:
    """GET via urllib. Returnerar (status, body); HTTP-fel → status."""
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"E-postofferten/{CURRENT_VERSION} (+https://github.com/{GITHUB_REPO})",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(getattr(response, "status", 200) or 200), response.read()
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read()
        except Exception:
            body = b""
        return int(exc.code or 0), body


def latest_release_url(repo: str = GITHUB_REPO) -> str:
    return f"{API_BASE}/repos/{repo}/releases/latest"


def _pick_download_url(payload: Dict[str, Any]) -> str:
    """Bifogad .zip-asset först, annars GitHubs zipball för taggen."""
    assets = payload.get("assets")
    if isinstance(assets, list):
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name") or "").lower()
            url = str(asset.get("browser_download_url") or "")
            if url and name.endswith(".zip"):
                return url
    return str(payload.get("zipball_url") or "")


def check_for_update(
    current_version: str = CURRENT_VERSION,
    repo: str = GITHUB_REPO,
    timeout: float = 15.0,
    fetcher: Optional[Fetcher] = None,
    current_build_id: str = CURRENT_BUILD_ID,
    installed_fingerprint: str = "",
) -> UpdateInfo:
    """Fråga GitHub om senaste release och jämför med installerad version.

    Kastar aldrig – fel hamnar i ``UpdateInfo.error`` så att UI:t kan
    visa dem snällt (och autosökningen kan vara tyst).
    """
    info = UpdateInfo()
    fetch = fetcher or _default_fetcher
    url = latest_release_url(repo)
    try:
        status, body = fetch(url, float(timeout))
    except Exception as exc:  # nätverk nere, DNS, timeout …
        info.error = str(exc) or exc.__class__.__name__
        log.debug("Uppdateringssökning misslyckades (%s)", url, exc_info=True)
        return info

    if status == 404:
        info.no_releases = True
        log.info("GitHub-release ej tillgänglig (HTTP 404): saknad release eller privat repo utan autentisering (%s).", repo)
        return info
    if status != 200:
        info.error = f"GitHub svarade HTTP {status}"
        return info

    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except Exception as exc:
        info.error = f"Kunde inte tolka GitHub-svaret: {exc}"
        return info
    if not isinstance(payload, dict):
        info.error = "Oväntat svar från GitHub (inte ett JSON-objekt)."
        return info

    info.raw = payload
    info.tag = str(payload.get("tag_name") or "")
    info.latest_version = normalize_tag(info.tag)
    info.name = str(payload.get("name") or info.tag)
    info.notes = str(payload.get("body") or "").strip()
    info.html_url = str(payload.get("html_url") or "")
    info.download_url = _pick_download_url(payload)
    info.build_id = parse_build_id(payload)
    info.fingerprint = release_fingerprint(payload)
    newer = is_newer_version(info.latest_version, current_version)
    same_version = bool(
        info.latest_version
        and compare_versions(info.latest_version, current_version) == 0
    )
    stored_fingerprint = str(installed_fingerprint or "").strip()
    build_changed = _is_newer_build(info.build_id, current_build_id)
    fingerprint_changed = bool(
        stored_fingerprint
        and info.fingerprint
        and stored_fingerprint != info.fingerprint
    )
    # Samma versionsnummer, men releasens filer har uppdaterats
    # (nyare byggstämpel eller annat release-fingeravtryck).
    info.same_version_files_changed = bool(
        same_version
        and info.download_url
        and (build_changed or fingerprint_changed)
    )
    info.available = bool(
        info.latest_version
        and info.download_url
        and (newer or info.same_version_files_changed)
    )
    if info.latest_version and not info.download_url and (
        newer or (same_version and (build_changed or fingerprint_changed))
    ):
        info.error = "Releasen saknar nedladdningsbar zip (asset/zipball)."
    log.info(
        "Uppdateringssökning: installerad=%s senaste=%s tillgänglig=%s "
        "bygg=%s uppdaterade_filer=%s",
        current_version, info.latest_version or "?", info.available,
        info.build_id or "-", info.same_version_files_changed,
    )
    return info


# ───────────────────────────────────────────────────────────────────────
# Nedladdning + uppackning + applicering
# ───────────────────────────────────────────────────────────────────────

def download_update_zip(
    url: str,
    dest_dir: Path,
    timeout: float = 180.0,
    fetcher: Optional[Fetcher] = None,
) -> Path:
    """Ladda ner release-zip till ``dest_dir/update.zip``."""
    if not str(url or "").strip():
        raise ValueError("Ingen nedladdningslänk (download_url är tom).")
    fetch = fetcher or _default_fetcher
    status, body = fetch(str(url), float(timeout))
    if status != 200:
        raise RuntimeError(f"Nedladdningen misslyckades (HTTP {status}).")
    if not body:
        raise RuntimeError("Nedladdningen gav en tom fil.")
    if len(body) > MAX_ZIP_BYTES:
        raise RuntimeError("Nedladdningen är oväntat stor – avbryter.")
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / "update.zip"
    zip_path.write_bytes(body)
    return zip_path


def _safe_extract(zip_path: Path, dest_dir: Path) -> None:
    """Packa upp zip med zip-slip-skydd (avbryter vid ../-poster)."""
    root = Path(dest_dir).resolve()
    with zipfile.ZipFile(str(zip_path)) as archive:
        for member in archive.infolist():
            target = (root / member.filename).resolve()
            if target != root and root not in target.parents:
                raise ValueError(
                    f"Ogiltig sökväg i zip-filen: {member.filename}"
                )
            archive.extract(member, str(root))


def find_app_root(extract_dir: Path) -> Path:
    """Hitta mappen som innehåller main.pyw i en uppackad release.

    GitHub-zipballs bäddar in allt under ``Ägare-Repo-<sha>/`` medan en
    handuppladdad asset kan ha filerna i roten – båda hanteras.
    """
    root = Path(extract_dir)
    if (root / "main.pyw").is_file():
        return root
    try:
        children = sorted(p for p in root.iterdir() if p.is_dir())
    except OSError:
        children = []
    for child in children:
        if (child / "main.pyw").is_file():
            return child
    # Sista utväg: sök på djupet (begränsat till rimligt antal träffar)
    for candidate in root.rglob("main.pyw"):
        return candidate.parent
    raise ValueError(
        "Zip-filen ser inte ut som E-postofferten (main.pyw saknas)."
    )


def extract_update_zip(zip_path: Path, dest_dir: Path) -> Path:
    """Packa upp + returnera app-roten i det uppackade trädet."""
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    _safe_extract(Path(zip_path), dest)
    return find_app_root(dest)


def apply_github_update(
    info: UpdateInfo,
    base_dir: Path,
    timeout: float = 180.0,
    fetcher: Optional[Fetcher] = None,
) -> Dict[str, Any]:
    """Ladda ner, packa upp och applicera en GitHub-release.

    Delegerar själva kopieringen till ``apply_update_from_dir`` så att
    exakt samma skydd gäller som vid "Uppdatera från mapp": JSON,
    inställningar, adresslistor, loggar och Mallar/ rörs ALDRIG.
    Returns: ``{copied, skipped, errors, version}``.
    """
    from core.app_update import apply_update_from_dir

    if not info or not info.download_url:
        raise ValueError("Ingen nedladdningslänk – sök efter uppdateringar först.")
    tmp_root = Path(tempfile.mkdtemp(prefix="epostofferten-update-"))
    try:
        zip_path = download_update_zip(
            info.download_url, tmp_root, timeout=timeout, fetcher=fetcher
        )
        app_root = extract_update_zip(zip_path, tmp_root / "extracted")
        result = apply_update_from_dir(app_root, Path(base_dir))
        result = dict(result)
        result["version"] = info.latest_version
        result["build_id"] = str(
            getattr(info, "build_id", "")
            or parse_build_id(getattr(info, "raw", {}))
        )
        result["fingerprint"] = str(
            getattr(info, "fingerprint", "")
            or release_fingerprint(getattr(info, "raw", {}) or {})
        )
        result["same_version_files_changed"] = bool(
            getattr(info, "same_version_files_changed", False)
        )
        return result
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


__all__ = [
    "AUTO_CHECK_INTERVAL_HOURS",
    "UpdateInfo",
    "apply_github_update",
    "check_for_update",
    "compare_versions",
    "download_update_zip",
    "extract_update_zip",
    "find_app_root",
    "is_newer_version",
    "latest_release_url",
    "normalize_tag",
    "now_iso",
    "parse_build_id",
    "parse_version",
    "release_fingerprint",
    "should_auto_check",
]
