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
   I appen verifieras dessutom release-taggens verkliga commit (även
   annoterade taggar), officiell asset-SHA-256 (``digest``) och SHA-256
   för nedladdade appfiler mot installationen.
2. ``apply_github_update()`` återanvänder verifierad release-zip från
   ``.data/update_cache/`` (eller laddar ner över krypterad HTTPS),
   packar upp den säkert (zip-slip-, symlänk-, krypterings- och
   zip-bomb-skydd) och delegerar kopieringen till
   ``core/app_update.apply_update_from_dir`` – som validerar
   Python-syntax, skriver atomärt med automatisk rollback och ALDRIG rör
   JSON, inställningar, adresslistor eller mallmappen (``update_protect``).

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
import os
import posixpath
import re
import shutil
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from urllib.parse import quote
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.version import (
    BUILD_ID as CURRENT_BUILD_ID,
    GITHUB_REPO,
    __version__ as CURRENT_VERSION,
)

log = logging.getLogger(__name__)

API_BASE = "https://api.github.com"
MAX_ZIP_BYTES = 200 * 1024 * 1024  # 200 MB – skydd mot trasiga svar
MAX_JSON_BYTES = 8 * 1024 * 1024   # 8 MB – skydd för JSON-metadata
MAX_EXTRACT_FILES = 20_000
MAX_EXTRACT_BYTES = 400 * 1024 * 1024
AUTO_CHECK_INTERVAL_HOURS = 12
_STREAM_CHUNK_BYTES = 64 * 1024
_TRANSIENT_HTTP_CODES = frozenset({408, 429, 500, 502, 503, 504})
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_BUILD_SECTION_RE = re.compile(r"(?m)^##\s+BUILD([0-9A-Za-z_.-]+)\b[^\n]*$")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_WINDOWS_RESERVED_NAMES = frozenset(
    {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        *(f"COM{i}" for i in range(1, 10)),
        *(f"LPT{i}" for i in range(1, 10)),
    }
)

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
    matches = _BUILD_MARKER_RE.findall(text)
    if not matches:
        return ""
    if all(m.strip().isdigit() for m in matches):
        return max((m.strip() for m in matches), key=int)
    return matches[-1].strip()


def extract_latest_release_notes(
    notes: str, build_id: str = "", *, max_chars: int = 900
) -> str:
    """Plocka ut det senaste/matchande versionsavsnittet ur release-texten.

    När en release har kumulativa ``## BUILD...``-avsnitt ligger de nyaste
    ändringarna längst ned; tidigare kapades ``notes[:700]`` från toppen
    vilket dolde nyheterna i själva bygget.
    """
    cleaned = _HTML_COMMENT_RE.sub("", str(notes or "")).strip()
    if not cleaned:
        return ""
    sections = list(_BUILD_SECTION_RE.finditer(cleaned))
    if sections:
        chosen_idx = len(sections) - 1
        wanted = str(build_id or "").strip()
        if wanted:
            for idx, m in enumerate(sections):
                if m.group(1).strip() == wanted:
                    chosen_idx = idx
                    break
        start = sections[chosen_idx].start()
        end = (
            sections[chosen_idx + 1].start()
            if chosen_idx + 1 < len(sections)
            else len(cleaned)
        )
        block = cleaned[start:end].strip()
    else:
        block = cleaned
    if len(block) > max_chars:
        block = block[: max_chars - 1].rstrip() + "…"
    return block


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
    if payload.get("resolved_commit_sha"):
        data["resolved_commit_sha"] = payload["resolved_commit_sha"]
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


def should_midnight_auto_update(
    last_midnight_date: object,
    now: Optional[_dt.datetime] = None,
) -> bool:
    """True om dagens 00:00-autouppdatering ännu inte körts.

    Jämför sparat datum (``YYYY-MM-DD``, lokal tid) mot dagens datum:
    annat datum, tomt eller ogiltigt värde → True (kör nu). Samma datum
    → False (redan kört i natt). Ren logik – testbar utan nät/Qt.
    """
    moment = now or _dt.datetime.now()
    today = moment.date().isoformat()
    text = str(last_midnight_date or "").strip()[:10]
    if not text:
        return True
    try:
        _dt.date.fromisoformat(text)
    except ValueError:
        return True
    return text != today


# ───────────────────────────────────────────────────────────────────────
# GitHub API & transportskydd
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
    commit_sha: str = ""
    archive_sha256: str = ""
    changed_files: list[str] = field(default_factory=list)
    files_compared: bool = False
    error: str = ""
    no_releases: bool = False
    raw: Dict[str, Any] = field(default_factory=dict)
    expected_asset_sha256: str = ""


_FORBIDDEN_BRANCH_NAMES = frozenset({"main", "master", "head"})
_FORBIDDEN_MAIN_URL_RE = re.compile(
    r"(?i)(?:"
    r"/(?:zipball|tarball)/(?:refs/heads/)?(?:main|master)(?:[/?#]|$)"
    r"|/archive/(?:refs/heads/)?(?:main|master)\.(?:zip|tar\.gz)(?:[?#]|$)"
    r"|/git/refs?/heads/(?:main|master)(?:[/?#]|$)"
    r"|/(?:branches|commits)/(?:main|master)(?:[/?#]|$)"
    r"|raw\.githubusercontent\.com/[^/]+/[^/]+/(?:refs/heads/)?(?:main|master)(?:/|$)"
    r")"
)


def is_forbidden_main_ref(ref: object) -> bool:
    """Hård regel: appuppdateringar får aldrig arbeta mot main-branchen."""
    cleaned = str(ref or "").strip().strip("/").lower()
    if not cleaned:
        return False
    if cleaned in _FORBIDDEN_BRANCH_NAMES:
        return True
    for prefix in ("refs/heads/", "refs/remotes/origin/", "remotes/origin/", "heads/", "origin/"):
        if cleaned.startswith(prefix) and cleaned[len(prefix):] in _FORBIDDEN_BRANCH_NAMES:
            return True
    return False


def is_forbidden_main_url(url: object) -> bool:
    """True om en URL pekar mot main/master-branch i stället för release-tagg/commit."""
    text = str(url or "").strip()
    if not text:
        return False
    if _FORBIDDEN_MAIN_URL_RE.search(text):
        return True
    try:
        parsed = urllib.parse.urlsplit(text)
        for key, values in urllib.parse.parse_qs(parsed.query).items():
            if key.lower() in {"ref", "branch", "sha", "commitish", "target_commitish"}:
                if any(is_forbidden_main_ref(val) for val in values):
                    return True
    except Exception:
        pass
    return False


def validate_update_url(url: object) -> str:
    """Validera att ``url`` använder krypterad ``https://`` och aldrig pekar mot ``main``."""
    text = str(url or "").strip()
    if is_forbidden_main_url(text):
        raise ValueError("Uppdatering mot main-branchen är blockerad (hård regel).")
    parsed = urllib.parse.urlsplit(text)
    if (parsed.scheme or "").lower() != "https" or not parsed.hostname:
        raise ValueError("Endast krypterade HTTPS-länkar tillåts vid uppdatering.")
    return text


class _SafeHttpsRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Verifiera att varje HTTP-omdirigering stannar på ``https://`` och ej ``main``."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        resolved = urllib.parse.urljoin(req.full_url, newurl)
        validate_update_url(resolved)
        return super().redirect_request(req, fp, code, msg, headers, resolved)


def _read_bounded_response(response: Any, max_bytes: int) -> bytes:
    headers = getattr(response, "headers", None)
    content_length = headers.get("Content-Length") if headers is not None else None
    if content_length:
        try:
            if int(content_length) > max_bytes:
                raise RuntimeError("Nedladdningen är oväntat stor – avbryter.")
        except ValueError:
            pass
    chunks: List[bytes] = []
    total = 0
    while True:
        chunk = response.read(_STREAM_CHUNK_BYTES)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise RuntimeError("Nedladdningen är oväntat stor – avbryter.")
        chunks.append(chunk)
    return b"".join(chunks)


def _default_fetcher(url: str, timeout: float) -> Tuple[int, bytes]:
    """GET via urllib med HTTPS-kontroll, strömbegränsning och 1 automatiskt omförsök."""
    cleaned = validate_update_url(url)
    is_api = "api.github.com/" in cleaned and "/zipball/" not in cleaned and "/tarball/" not in cleaned
    max_bytes = MAX_JSON_BYTES if is_api else MAX_ZIP_BYTES
    accept = "application/vnd.github+json" if is_api else "application/octet-stream,*/*"
    opener = urllib.request.build_opener(_SafeHttpsRedirectHandler())

    last_exc: Optional[BaseException] = None
    for attempt in range(2):
        request = urllib.request.Request(
            cleaned,
            headers={
                "Accept": accept,
                "User-Agent": f"E-postofferten/{CURRENT_VERSION} (+https://github.com/{GITHUB_REPO})",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with opener.open(request, timeout=timeout) as response:
                final_url = getattr(response, "geturl", lambda: cleaned)() or cleaned
                validate_update_url(final_url)
                status = int(getattr(response, "status", 200) or 200)
                data = _read_bounded_response(response, max_bytes)
                return status, data
        except urllib.error.HTTPError as exc:
            code = int(exc.code or 0)
            if code in _TRANSIENT_HTTP_CODES and attempt == 0:
                time.sleep(0.5)
                continue
            try:
                body = exc.read(MAX_JSON_BYTES)
            except Exception:
                body = b""
            return code, body
        except (urllib.error.URLError, TimeoutError) as exc:
            last_exc = exc
            if attempt == 0:
                time.sleep(0.5)
                continue
            raise
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("Nätverksanropet avbröts utan svar.")


def _guard_fetcher(fetch: Fetcher) -> Fetcher:
    """Förhindra att uppdateraren någonsin anropar main-branch eller okrypterad URL."""
    def guarded(url: str, timeout: float) -> Tuple[int, bytes]:
        cleaned = validate_update_url(url)
        return fetch(cleaned, timeout)

    return guarded


def latest_release_url(repo: str = GITHUB_REPO) -> str:
    return f"{API_BASE}/repos/{repo}/releases/latest"


def _parse_asset_sha256(raw_digest: Any) -> str:
    if not isinstance(raw_digest, str):
        return ""
    text = raw_digest.strip()
    if text.lower().startswith("sha256:"):
        text = text[7:].strip()
    return text.lower() if _SHA256_RE.fullmatch(text) else ""


def _pick_download_asset(payload: Dict[str, Any]) -> Tuple[str, str]:
    """Returnera ``(url, expected_sha256)`` för bästa ``.zip``-asset eller zipball."""
    assets = payload.get("assets")
    if isinstance(assets, list):
        for asset in assets:
            if not isinstance(asset, dict):
                continue
            name = str(asset.get("name") or "").lower()
            url = str(asset.get("browser_download_url") or "").strip()
            if (
                url
                and name.endswith(".zip")
                and not is_forbidden_main_url(url)
                and url.lower().startswith("https://")
            ):
                return url, _parse_asset_sha256(asset.get("digest"))
    zipball = str(payload.get("zipball_url") or "").strip()
    if is_forbidden_main_url(zipball) or (zipball and not zipball.lower().startswith("https://")):
        return "", ""
    return zipball, ""


def _pick_download_url(payload: Dict[str, Any]) -> str:
    """Bifogad .zip-asset först, annars GitHubs zipball för taggen (aldrig main)."""
    url, _ = _pick_download_asset(payload)
    return url


def resolve_release_commit(tag: str, repo: str, fetch: Fetcher, timeout: float) -> str:
    """Resolve the release tag itself, never target_commitish (which may be main)."""
    if is_forbidden_main_ref(tag):
        raise ValueError("Uppdatering mot main-branchen är blockerad (hård regel).")
    guarded = _guard_fetcher(fetch)
    url = f"{API_BASE}/repos/{repo}/git/ref/tags/{quote(tag, safe='')}"
    for _ in range(8):
        status, body = guarded(url, timeout)
        if status != 200:
            raise RuntimeError(f"Kunde inte läsa release-taggens commit (HTTP {status}).")
        payload = json.loads(body.decode("utf-8"))
        obj = payload.get("object", {})
        sha = str(obj.get("sha", ""))
        if not re.fullmatch(r"[0-9a-fA-F]{40}", sha):
            raise ValueError("Ogiltig commit i release-taggen.")
        if obj.get("type") == "commit":
            return sha.lower()
        if obj.get("type") != "tag":
            raise ValueError("Release-taggen pekar inte på en commit.")
        url = f"{API_BASE}/repos/{repo}/git/tags/{sha}"
    raise ValueError("För många nästlade release-taggar.")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_release_files(source: Path, installed: Path) -> list[str]:
    """Hash only files the updater may replace; never treat user data as a diff.

    Local-only files are retained, just as during installation. Unsafe local
    symlinks are refused instead of comparing/writing outside the app folder.
    """
    from core.app_update import BLOCKED_BINARY_SUFFIXES, SKIP_DIR_NAMES
    from core.update_protect import is_protected
    source, installed = Path(source).resolve(), Path(installed).resolve()
    changed = []
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        if any(part in SKIP_DIR_NAMES for part in rel.parts):
            continue
        if path.suffix.lower() in BLOCKED_BINARY_SUFFIXES:
            continue
        target = installed / rel
        if is_protected(path, source):
            continue
        if path.is_symlink():
            raise ValueError(f"Symbolisk länk i release: {rel}")
        if not path.is_file():
            continue
        if target.is_symlink() or any(p.is_symlink() or getattr(p, "is_junction", lambda: False)()
                                      for p in target.parents if p != installed and installed in p.parents):
            raise ValueError(f"Osäker lokal länk: {rel}")
        if is_protected(target, installed):
            continue
        if not target.is_file() or _file_sha256(path) != _file_sha256(target):
            changed.append(rel.as_posix())
    return changed


def _update_cache_dir(base_dir: Path) -> Path:
    return Path(base_dir).resolve() / ".data" / "update_cache"


def _store_verified_zip_in_cache(
    base_dir: Path, zip_path: Path, archive_sha256: str
) -> Optional[Path]:
    if not _SHA256_RE.fullmatch(archive_sha256 or ""):
        return None
    cache_dir = _update_cache_dir(base_dir)
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        target = cache_dir / f"{archive_sha256.lower()}.zip"
        if not target.is_file() or _file_sha256(target) != archive_sha256.lower():
            fd, tmp_name = tempfile.mkstemp(
                dir=str(cache_dir), prefix=".upd-cache-", suffix=".tmp"
            )
            os.close(fd)
            tmp_path = Path(tmp_name)
            try:
                shutil.copy2(zip_path, tmp_path)
                os.replace(tmp_path, target)
            finally:
                tmp_path.unlink(missing_ok=True)
        for other in cache_dir.glob("*.zip"):
            if other != target:
                other.unlink(missing_ok=True)
        return target
    except Exception:
        log.debug("Kunde inte spara verifierad uppdateringscache", exc_info=True)
        return None


def _load_verified_zip_from_cache(
    base_dir: Path, expected_sha256: str
) -> Optional[Path]:
    if not _SHA256_RE.fullmatch(expected_sha256 or ""):
        return None
    candidate = _update_cache_dir(base_dir) / f"{expected_sha256.lower()}.zip"
    if not candidate.is_file() or candidate.is_symlink():
        return None
    try:
        if _file_sha256(candidate) == expected_sha256.lower():
            return candidate
        candidate.unlink(missing_ok=True)
    except OSError:
        pass
    return None


def check_for_update(
    current_version: str = CURRENT_VERSION,
    repo: str = GITHUB_REPO,
    timeout: float = 15.0,
    fetcher: Optional[Fetcher] = None,
    current_build_id: str = CURRENT_BUILD_ID,
    installed_fingerprint: str = "",
    base_dir: Optional[Path] = None,
    installed_commit: str = "",
    on_progress: Optional[Callable[[str], None]] = None,
) -> UpdateInfo:
    """Fråga GitHub om senaste release och jämför med installerad version.

    Kastar aldrig – fel hamnar i ``UpdateInfo.error`` så att UI:t kan
    visa dem snällt (och autosökningen kan vara tyst).
    """
    info = UpdateInfo()
    fetch = _guard_fetcher(fetcher or _default_fetcher)
    url = latest_release_url(repo)
    if on_progress:
        on_progress("Kontrollerar senaste release på GitHub…")
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

    if payload.get("draft") or payload.get("prerelease"):
        return info

    info.raw = payload
    info.tag = str(payload.get("tag_name") or "")
    if is_forbidden_main_ref(info.tag):
        info.error = "Uppdatering mot main-branchen är blockerad (hård regel)."
        return info
    raw_zipball = str(payload.get("zipball_url") or "")
    raw_assets = payload.get("assets") if isinstance(payload.get("assets"), list) else []
    had_main_url = is_forbidden_main_url(raw_zipball) or any(
        isinstance(a, dict) and is_forbidden_main_url(a.get("browser_download_url"))
        for a in raw_assets
    )
    info.latest_version = normalize_tag(info.tag)
    info.name = str(payload.get("name") or info.tag)
    info.notes = str(payload.get("body") or "").strip()
    info.html_url = str(payload.get("html_url") or "")
    dl_url, expected_asset_sha = _pick_download_asset(payload)
    info.download_url = dl_url
    info.expected_asset_sha256 = expected_asset_sha
    if not info.download_url and had_main_url:
        info.error = "Uppdatering mot main-branchen är blockerad (hård regel)."
        return info
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
    if base_dir is not None and (same_version or newer) and not info.download_url:
        info.error = "Releasen saknar nedladdningsbar zip (asset/zipball)."
    if base_dir is not None and not info.latest_version:
        info.error = "Releasen saknar en giltig versionstagg."
    # In-app checks verify real release contents, including fresh/manual
    # installs with no saved fingerprint. Metadata-only callers remain supported.
    if base_dir is not None and info.download_url and (same_version or newer):
        try:
            if on_progress:
                on_progress("Verifierar release-taggens commit och kontrollsumma…")
            info.commit_sha = resolve_release_commit(info.tag, repo, fetch, float(timeout))
            payload["resolved_commit_sha"] = info.commit_sha
            info.fingerprint = release_fingerprint(payload)
            if not any(isinstance(a, dict) and str(a.get("name", "")).lower().endswith(".zip")
                       and a.get("browser_download_url") for a in payload.get("assets", []) or []):
                info.download_url = f"{API_BASE}/repos/{repo}/zipball/{info.commit_sha}"
                info.expected_asset_sha256 = ""
            with tempfile.TemporaryDirectory(prefix="mailoffer-check-") as temp:
                root = Path(temp)
                if on_progress:
                    on_progress("Hämtar och verifierar release-paket (SHA-256)…")
                archive = download_update_zip(
                    info.download_url,
                    root,
                    timeout=timeout,
                    fetcher=fetch,
                    expected_sha256=info.expected_asset_sha256,
                )
                info.archive_sha256 = _file_sha256(archive)
                content = extract_update_zip(archive, root / "extracted")
                if on_progress:
                    on_progress("Jämför release-filer mot din installation…")
                info.changed_files = compare_release_files(content, Path(base_dir))
                info.files_compared = True
                commit_changed = bool(installed_commit and str(installed_commit).lower() != info.commit_sha)
                info.same_version_files_changed = bool(same_version and (build_changed or commit_changed or info.changed_files))
                info.available = bool(newer or info.same_version_files_changed)
                if (
                    info.available
                    and fetcher is None
                    and Path(base_dir).is_dir()
                    and info.archive_sha256
                ):
                    _store_verified_zip_in_cache(
                        Path(base_dir), archive, info.archive_sha256
                    )
        except Exception as exc:
            # Never claim "up to date" or install unverified/ambiguous contents.
            info.error = f"Kunde inte verifiera releasens commit/filer: {exc}"
            info.available = False
            log.warning("Verifiering av release misslyckades", exc_info=True)
    log.info(
        "Uppdateringssökning: installerad=%s senaste=%s tillgänglig=%s "
        "bygg=%s uppdaterade_filer=%s commit=%s jämförda=%s avvikande=%s",
        current_version, info.latest_version or "?", info.available,
        info.build_id or "-", info.same_version_files_changed,
        info.commit_sha or "-", info.files_compared, len(info.changed_files),
    )
    if not info.error:
        from core.open_errors import notify_subsystem_recovered
        notify_subsystem_recovered(
            base_dir or Path(__file__).resolve().parents[1],
            ("github_update",),
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
    *,
    expected_sha256: str = "",
) -> Path:
    """Ladda ner release-zip atomärt till ``dest_dir/update.zip`` och kontrollera den."""
    if not str(url or "").strip():
        raise ValueError("Ingen nedladdningslänk (download_url är tom).")
    cleaned_url = validate_update_url(url)
    fetch = _guard_fetcher(fetcher or _default_fetcher)
    status, body = fetch(cleaned_url, float(timeout))
    if status != 200:
        raise RuntimeError(f"Nedladdningen misslyckades (HTTP {status}).")
    if not body:
        raise RuntimeError("Nedladdningen gav en tom fil.")
    if len(body) > MAX_ZIP_BYTES:
        raise RuntimeError("Nedladdningen är oväntat stor – avbryter.")
    if expected_sha256:
        actual_sha = hashlib.sha256(body).hexdigest()
        if actual_sha.lower() != expected_sha256.strip().lower():
            raise ValueError(
                "Release-paketets SHA-256 matchar inte GitHubs officiella kontrollsumma."
            )
    dest = Path(dest_dir)
    dest.mkdir(parents=True, exist_ok=True)
    zip_path = dest / "update.zip"
    fd, tmp_name = tempfile.mkstemp(dir=str(dest), prefix=".dl-update-", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(body)
            fh.flush()
            try:
                os.fsync(fh.fileno())
            except OSError:
                pass
        if not zipfile.is_zipfile(tmp_path):
            raise ValueError("Nedladdad fil är inte en giltig .zip-fil.")
        os.replace(tmp_path, zip_path)
    except Exception:
        tmp_path.unlink(missing_ok=True)
        raise
    return zip_path


def _validate_zip_member_parts(raw_name: str) -> List[str]:
    normalized = (raw_name or "").replace("\\", "/")
    if not normalized or normalized.startswith("/") or "\x00" in normalized:
        raise ValueError(f"Ogiltig sökväg i zip-filen: {raw_name}")
    if re.match(r"^[A-Za-z]:", normalized):
        raise ValueError(f"Ogiltig sökväg i zip-filen: {raw_name}")
    norm = posixpath.normpath(normalized)
    if norm in ("", "."):
        return []
    if norm.startswith("/") or norm.startswith("../") or norm == "..":
        raise ValueError(f"Ogiltig sökväg i zip-filen: {raw_name}")
    parts = [p for p in norm.split("/") if p and p != "."]
    for part in parts:
        if part == "..":
            raise ValueError(f"Ogiltig sökväg i zip-filen: {raw_name}")
        stem = part.split(".", 1)[0].upper()
        if stem in _WINDOWS_RESERVED_NAMES:
            raise ValueError(f"Reserverat enhetsnamn i zip-filen: {raw_name}")
    return parts


def _safe_extract(zip_path: Path, dest_dir: Path) -> None:
    """Packa upp zip säkert (skydd mot Zip-Slip, symlänkar, kryptering och zip-bomber)."""
    root = Path(dest_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    total_written = 0
    with zipfile.ZipFile(str(zip_path), "r") as archive:
        members = archive.infolist()
        if len(members) > MAX_EXTRACT_FILES or sum(max(0, m.file_size) for m in members) > MAX_EXTRACT_BYTES:
            raise ValueError("Zip-filen packas upp till för mycket data.")
        for member in members:
            if member.flag_bits & 0x1:
                raise ValueError(f"Krypterade filer tillåts inte i release-zip: {member.filename}")
            if (member.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError("Symboliska länkar tillåts inte i release-zip.")
            parts = _validate_zip_member_parts(member.filename)
            if not parts:
                continue
            target = (root / Path(*parts)).resolve()
            if target != root and root not in target.parents:
                raise ValueError(
                    f"Ogiltig sökväg i zip-filen: {member.filename}"
                )
            if member.is_dir() or member.filename.replace("\\", "/").endswith("/"):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            entry_written = 0
            with archive.open(member, "r") as src, target.open("wb") as dst:
                while True:
                    chunk = src.read(_STREAM_CHUNK_BYTES)
                    if not chunk:
                        break
                    entry_written += len(chunk)
                    total_written += len(chunk)
                    if total_written > MAX_EXTRACT_BYTES or entry_written > MAX_ZIP_BYTES:
                        raise ValueError("Zip-filen packas upp till för mycket data.")
                    dst.write(chunk)


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
    on_progress: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """Ladda ner, packa upp och applicera en GitHub-release atomärt med rollback.

    Delegerar själva kopieringen till ``apply_update_from_dir`` så att
    exakt samma skydd gäller som vid "Uppdatera från mapp": JSON,
    inställningar, adresslistor, loggar och Mallar/ rörs ALDRIG.
    Returns: ``{copied, skipped, errors, version, rolled_back, ...}``.
    """
    from core.app_update import apply_update_from_dir, cleanup_pre_update_backups

    if not info or not info.download_url:
        raise ValueError("Ingen nedladdningslänk – sök efter uppdateringar först.")
    if is_forbidden_main_ref(getattr(info, "tag", "")):
        raise ValueError("Uppdatering mot main-branchen är blockerad (hård regel).")
    validate_update_url(info.download_url)

    base_dir = Path(base_dir)
    tmp_root = Path(tempfile.mkdtemp(prefix="epostofferten-update-"))
    used_cached_archive = False
    cached_zip: Optional[Path] = None
    try:
        expected_asset_sha = str(getattr(info, "expected_asset_sha256", "") or "").strip()
        if fetcher is None and getattr(info, "archive_sha256", ""):
            cached_zip = _load_verified_zip_from_cache(base_dir, info.archive_sha256)

        if cached_zip is not None:
            if on_progress:
                on_progress("Använder redan verifierat release-paket (SHA-256)…")
            zip_path = cached_zip
            used_cached_archive = True
        else:
            if on_progress:
                on_progress("Laddar ner och verifierar release-paket (HTTPS + SHA-256)…")
            zip_path = download_update_zip(
                info.download_url,
                tmp_root,
                timeout=timeout,
                fetcher=fetcher,
                expected_sha256=expected_asset_sha,
            )

        actual_sha = _file_sha256(zip_path)
        if expected_asset_sha and actual_sha.lower() != expected_asset_sha.lower():
            raise ValueError(
                "Release-paketets SHA-256 matchar inte GitHubs officiella kontrollsumma."
            )
        if info.archive_sha256 and actual_sha.lower() != info.archive_sha256.lower():
            raise ValueError(
                "Releasens arkiv har ändrats sedan kontrollen. Sök efter uppdateringar igen."
            )

        if on_progress:
            on_progress("Packar upp och säkerhetskontrollerar uppdateringspaketet…")
        app_root = extract_update_zip(zip_path, tmp_root / "extracted")
        # Refuse unsafe local links before copying any file.
        compare_release_files(app_root, base_dir)
        result = apply_update_from_dir(
            app_root,
            base_dir,
            require_app_root=True,
            backup_user_data=True,
            cleanup_backup_on_success=False,
            on_progress=on_progress,
        )
        result = dict(result)
        if not result.get("errors"):
            if on_progress:
                on_progress("Verifierar installerade kontrollsummor…")
            remaining = compare_release_files(app_root, base_dir)
            if remaining:
                result.setdefault("errors", []).append(
                    "Filkontrollen efter installation misslyckades: "
                    + ", ".join(remaining[:8])
                )
        if not result.get("errors"):
            cleanup_pre_update_backups(base_dir)
            result["backup_path"] = ""
            result["backup_cleaned"] = True
            cache_dir = _update_cache_dir(base_dir)
            if cache_dir.is_dir() and not cache_dir.is_symlink():
                for item in list(cache_dir.glob("*.zip")) + list(cache_dir.glob("*.tmp")):
                    item.unlink(missing_ok=True)
                try:
                    if not any(cache_dir.iterdir()):
                        cache_dir.rmdir()
                except OSError:
                    pass
        result["commit_sha"] = info.commit_sha
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
        result["used_cached_archive"] = used_cached_archive
        if used_cached_archive and cached_zip is not None and not result.get("errors"):
            cached_zip.unlink(missing_ok=True)
        return result
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


__all__ = [
    "AUTO_CHECK_INTERVAL_HOURS",
    "UpdateInfo",
    "apply_github_update",
    "check_for_update",
    "compare_versions",
    "compare_release_files",
    "resolve_release_commit",
    "download_update_zip",
    "extract_latest_release_notes",
    "extract_update_zip",
    "find_app_root",
    "is_forbidden_main_ref",
    "is_forbidden_main_url",
    "is_newer_version",
    "latest_release_url",
    "normalize_tag",
    "now_iso",
    "parse_build_id",
    "parse_version",
    "release_fingerprint",
    "should_auto_check",
    "should_midnight_auto_update",
    "validate_update_url",
]
