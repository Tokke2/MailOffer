#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
script/templates.py – Mallhantering för EmailApp

Version: 3.6 – SCAN-CACHE + EARLY-RETURN + FLERSPRÅK

Stöd:
- DOCX (python-docx – lazy/valfri import), HTML (auto via filändelse),
  TXT (ÄMNE:/INNEHÅLL:-format)
- Placeholder-system (tre format): {NAME} · ((NAME)) · ::NAME::
- Språkblock: [sv]...[/sv] · [en]...[/en] · [comment]...[/comment]
- keep_unknown, remove_lines_with_missing, strip_comments
- scan-cache (v3.6: filantal + mtime – skannar endast om något ändrats)
- apply_placeholders early-return (v3.6 – ingen placeholder-grammatik →
  direkt return, ingen onödig regex-körning)

FIL: script/templates.py
"""

from __future__ import annotations

import html as _html
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

log = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = (".docx", ".html", ".htm", ".txt")

# ── Placeholder-grammatik (hittar alla tre format) ───────────────────
_ALL_PH = re.compile(
    r"\{\{([^}]+?)\}\}|\(\(([^)]+?)\)\)|::([^:]+?)::",
    re.IGNORECASE,
)

# ── Språk-/kommentarsblock ───────────────────────────────────────────
_EN_BLOCK = re.compile(r"\[\s*en\s*\](.*?)\[\s*/\s*en\s*\]", re.I | re.S)
_SV_BLOCK = re.compile(r"\[\s*sv\s*\](.*?)\[\s*/\s*sv\s*\]", re.I | re.S)
_COMMENT_BLOCK = re.compile(
    r"\[\s*comment\s*\](.*?)\[\s*/\s*comment\s*\]", re.I | re.S
)

# ── 13 glastyper (dropdown i UI) ─────────────────────────────────────
PLACEHOLDER_DROPDOWNS: Dict[str, List[str]] = {
    "ruta": [
        "Vindruta",
        "Bakruta",
        "Höger sidoruta fram",
        "Vänster sidoruta fram",
        "Höger sidoruta bak",
        "Vänster sidoruta bak",
        "Höger ventilationsruta",
        "Vänster ventilationsruta",
        "Höger kvarts-/hörn-ruta",
        "Vänster kvarts-/hörn-ruta",
        "Taklucka / Panoramatak",
        "Vindruteglas (laminerad)",
        "Vindruteglas (härdad)",
    ],
}

# ── Scan-cache (v3.6): dir → (signatur, lista) ───────────────────────
_scan_cache: Dict[str, Tuple[tuple, List[str]]] = {}

_SKIP_PREFIXES = ("~$",)
_SKIP_SUFFIXES = (".bak", ".tmp")


# ═══════════════════════════════════════════════════════════════════════
# Hjälpfunktioner
# ═══════════════════════════════════════════════════════════════════════

def _iter_placeholder_matches(text: str) -> List[str]:
    """Returnera alla placeholder-nycklar i texten (i ordning)."""
    keys: List[str] = []
    for match in _ALL_PH.finditer(text or ""):
        raw = (
            match.group(1) or match.group(2) or match.group(3) or ""
        ).strip()
        if raw:
            keys.append(raw)
    return keys


def _build_key_regex(key: str) -> re.Pattern:
    """Bygg regex för EN placeholder-nyckel i alla tre format."""
    escaped = re.escape(key.strip())
    # Tillåt valfritt mellanrum innanför markeringarna
    ws = r"\s*"
    return re.compile(
        r"\{" + ws + escaped + ws + r"\}"
        + r"|\(\(" + ws + escaped + ws + r"\)\)"
        + r"|::" + ws + escaped + ws + r"::",
        re.IGNORECASE,
    )


def apply_placeholders(
    text: str,
    replacements: Optional[Dict[str, str]] = None,
    *,
    keep_unknown: bool = True,
    remove_lines_with_missing: bool = False,
) -> str:
    """
    Ersätt placeholders i texten.

    - (v3.6) Early-return: ingen placeholder-grammatik → texten
      returneras direkt utan regex-loopar.
    - Okända placeholders ersätts med tom sträng (keep_unknown=False)
      eller behålls (keep_unknown=True, default).
    - remove_lines_with_missing=True → rader med kvarvarande
      placeholders tas bort helt.
    """
    if not text:
        return text

    # Early-return (v3.6): ingen placeholder-grammatik alls
    if not _ALL_PH.search(text):
        return text

    result = text
    for key, value in (replacements or {}).items():
        if value is None:
            value = ""
        result = _build_key_regex(str(key)).sub(str(value), result)

    # Kvarvarande markeringar (okända nycklar)
    if not keep_unknown or remove_lines_with_missing:
        remaining = _ALL_PH.findall(result)
        if remaining:
            if remove_lines_with_missing:
                lines = result.split("\n")
                kept: List[str] = []
                for line in lines:
                    if not _ALL_PH.search(line):
                        kept.append(line)
                result = "\n".join(kept)
            else:
                result = _ALL_PH.sub("", result)

    return result


def _read_raw(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _strip_language_blocks(body: str, include_english: bool) -> str:
    """Hantera [sv]/[en]-block (split-modell).

    Mallstruktur (samma som användarens mallsystem):
        <svensk del>
        [en]
        <engelsk del>
        [/en]
        <gemensam del – t.ex. signatur>

    - include_english=False → svensk del + gemensam del
    - include_english=True  → engelsk del + gemensam del
    - Inget [en]-block → texten oförändrad (ingen språkväxling)
    - [sv]-taggar tas alltid bort (innehållet behålls)
    """
    body = _SV_BLOCK.sub(lambda m: m.group(1), body)
    en_match = _EN_BLOCK.search(body)
    if not en_match:
        return body.strip()

    before = body[:en_match.start()].rstrip()
    inside = en_match.group(1).strip()
    after = body[en_match.end():].strip()

    if include_english:
        parts = [part for part in (inside, after) if part]
    else:
        parts = [part for part in (before, after) if part]
    return "\n\n".join(parts)


def _parse_txt(path: Path) -> Tuple[str, str]:
    raw = _read_raw(path)
    lines = raw.splitlines()
    subject = ""
    if lines and lines[0].lower().startswith(("ämne:", "subject:")):
        subject = lines[0].split(":", 1)[1].strip()
        lines = lines[1:]
    body_lines: List[str] = []
    for line in lines:
        stripped = line.strip().lower()
        if stripped == "innehåll:" or stripped == "content:":
            continue
        body_lines.append(line)
    return subject, "\n".join(body_lines).strip()


def _parse_html(path: Path) -> Tuple[str, str]:
    raw = _read_raw(path)
    title_match = re.search(
        r"<title>(.*?)</title>", raw, re.I | re.DOTALL
    )
    subject = _html.unescape(title_match.group(1).strip()) if title_match else ""
    body_match = re.search(
        r"<body[^>]*>(.*?)</body>", raw, re.I | re.DOTALL
    )
    body_html = body_match.group(1) if body_match else raw
    body = re.sub(r"<br\s*/?>", "\n", body_html, flags=re.I)
    body = re.sub(r"</?p[^>]*>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]+>", "", body)
    return subject, _html.unescape(body).strip()


def _parse_docx(path: Path) -> Tuple[str, str]:
    try:
        import docx  # type: ignore
    except ImportError as exc:
        raise ValueError(
            f"python-docx krävs för att läsa '{path.name}'. "
            "Installera med: pip install python-docx"
        ) from exc

    document = docx.Document(str(path))
    paragraphs = [p.text for p in document.paragraphs if p.text.strip()]
    if not paragraphs:
        return "", ""

    subject = ""
    lines = list(paragraphs)
    if lines[0].lower().startswith(("ämne:", "subject:")):
        subject = lines[0].split(":", 1)[1].strip()
        lines = lines[1:]
    body_lines: List[str] = []
    for line in lines:
        if line.strip().lower() in ("innehåll:", "content:"):
            continue
        body_lines.append(line)
    return subject, "\n".join(body_lines).strip()


def _read_template_file(path: Path) -> Tuple[str, str]:
    """Läs (subject, body) från fil – filtyp via ändelse."""
    suffix = path.suffix.lower()
    if suffix == ".docx":
        return _parse_docx(path)
    if suffix in (".html", ".htm"):
        return _parse_html(path)
    if suffix == ".txt":
        return _parse_txt(path)
    raise ValueError(
        f"Ej stödd malltyp '{suffix}'. Stödda: "
        + ", ".join(SUPPORTED_EXTENSIONS)
    )


# ═══════════════════════════════════════════════════════════════════════
# Publikt API
# ═══════════════════════════════════════════════════════════════════════

def parse_subject_and_body(
    path: Any,
    replacements: Optional[Dict[str, str]] = None,
    include_english: bool = False,
    remove_lines_with_missing: bool = False,
    keep_unknown: bool = False,
    strip_comments: bool = True,
) -> Tuple[str, str]:
    """
    Parsa en mallfil → (subject, body) med placeholders ersatta.

    - TXT/HTML/DOCX stöds (via filändelse)
    - [comment]-block tas bort (strip_comments=True, default)
    - [sv]/[en]-block: se _strip_language_blocks
    - Placeholders ersätts med replacements (alla tre format,
      case-insensitivt)
    - Saknade platshållare → tom sträng (spec §9.2); rader tas ENBART
      bort om remove_lines_with_missing=True (opt-in)

    Raises:
        FileNotFoundError: filen finns inte
        ValueError: fel malltyp eller otolkbar mall
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(str(file_path))

    subject, body = _read_template_file(file_path)

    if strip_comments:
        body = _COMMENT_BLOCK.sub("", body)
        subject = _COMMENT_BLOCK.sub("", subject)

    body = _strip_language_blocks(body, include_english)

    subject = apply_placeholders(
        subject,
        replacements,
        keep_unknown=keep_unknown,
        remove_lines_with_missing=False,
    )
    body = apply_placeholders(
        body,
        replacements,
        keep_unknown=keep_unknown,
        remove_lines_with_missing=remove_lines_with_missing,
    )
    return subject, body.strip()


def list_placeholders(path: Any) -> List[str]:
    """Unika placeholder-nycklar i en mallfil (subject + body)."""
    return _unique_keys_in_file(Path(path))


def find_placeholders_in_file(path: Any) -> List[str]:
    """Alias för list_placeholders (bakåtkompatibilitet)."""
    return list_placeholders(path)


def _unique_keys_in_file(path: Path) -> List[str]:
    if not path.exists():
        return []
    try:
        subject, body = _read_template_file(path)
    except Exception:
        log.debug(
            "Kunde inte läsa placeholders ur %s", path.name, exc_info=True
        )
        return []
    keys: List[str] = []
    seen: set = set()
    for key in _iter_placeholder_matches(f"{subject}\n{body}"):
        low = key.lower()
        if low not in seen:
            seen.add(low)
            keys.append(key)
    return keys


def validate_template(path: Any) -> Tuple[bool, List[str]]:
    """Validera en mallfil. Returns (ok, felmeddelanden)."""
    file_path = Path(path)
    errors: List[str] = []
    if not file_path.exists():
        return False, [f"Filen finns inte: {file_path.name}"]
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return False, [
            f"Ej stödd malltyp: {file_path.suffix} "
            f"(stödda: {', '.join(SUPPORTED_EXTENSIONS)})"
        ]
    try:
        subject, body = _read_template_file(file_path)
        if not body.strip():
            errors.append("Mallen saknar innehåll (tom brödtext).")
        _ = subject
    except Exception as exc:
        errors.append(f"Kunde inte läsa mallen: {exc}")
    return not errors, errors


# ── Mall-wizardhjälpare (v3.7 – används av ui/template_wizard.py) ────

_ILLEGAL_FILENAME_CHARS = '<>:"/\\|?*'
_WINDOWS_RESERVED_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)


def find_placeholders_in_text(text: str) -> List[str]:
    """Unika placeholder-nycklar i en textsträng (ordningen behålls).

    Samma grammatik och avdubblettering (case-insensitiv) som
    ``list_placeholders`` för filer – men för text i minnet, så att
    wizarden kan förhandsgranska innan mallen sparats.
    """
    keys: List[str] = []
    seen: set = set()
    for key in _iter_placeholder_matches(text or ""):
        low = key.lower()
        if low not in seen:
            seen.add(low)
            keys.append(key)
    return keys


def build_template_body(swedish_body: str, english_body: str = "") -> str:
    """Bygg mallbrödtext med valfritt [en]-block av SV- och EN-text.

    Resultatet följer samma split-modell som ``_strip_language_blocks``
    läser: svensk del först, sedan ``[en]…[/en]``. Tom engelska →
    bara den svenska texten.
    """
    sv_text = str(swedish_body or "").strip()
    en_text = str(english_body or "").strip()
    if not en_text:
        return sv_text
    if not sv_text:
        return f"[en]\n{en_text}\n[/en]"
    return f"{sv_text}\n\n[en]\n{en_text}\n[/en]"


def sanitize_template_filename(name: str, extension: str = ".txt") -> str:
    """Gör ett användarnamn till ett säkert mallfilnamn.

    - Filändelsen tvingas till ``extension`` (stödda: .txt/.html/.htm/
      .docx – annat faller tillbaka på .txt).
    - Ogiltiga Windows-tecken (``<>:"/\\|?*`` + kontrolltecken) tas
      bort, dubbla mellanslag slås ihop, avslutande punkter/mellanslag
      trimmas (Windows-krav) och reserverade namn (CON, PRN, …) får
      prefixet "_".
    - ÅÄÖ och mellanslag behålls – mallnamn ska vara läsbara.
    - Tomt/osanerbart namn → "" (anroparen validerar).
    """
    ext = str(extension or ".txt").strip().lower()
    if not ext.startswith("."):
        ext = "." + ext
    if ext not in SUPPORTED_EXTENSIONS:
        ext = ".txt"

    base = str(name or "").strip()
    lowered = base.lower()
    for known in SUPPORTED_EXTENSIONS:
        if lowered.endswith(known):
            base = base[: -len(known)]
            break

    cleaned = "".join(
        ch
        for ch in base
        if ch not in _ILLEGAL_FILENAME_CHARS and ord(ch) >= 32
    )
    cleaned = re.sub(r"\s+", " ", cleaned).strip().rstrip(". ")
    if not cleaned:
        return ""
    if cleaned.upper() in _WINDOWS_RESERVED_NAMES:
        cleaned = "_" + cleaned
    cleaned = cleaned[:100].rstrip(". ")
    if not cleaned:
        return ""
    return f"{cleaned}{ext}"


@dataclass
class TemplateVersion:
    """Versionsinfo för en mallfil."""

    name: str
    path: str
    size: int = 0
    mtime: float = 0.0


def scan_templates_dir(
    templates_dir: Any, use_cache: bool = True
) -> List[str]:
    """
    Skanna mallmappen för .docx/.html/.htm/.txt.

    Hoppar över ~$-, .bak och .tmp (alltid).
    (v3.6) Scan-cache: signatur = (antal, max-mtime, namn, storlekar) –
    skannar endast om något ändrats sedan förra anropet.
    """
    directory = Path(templates_dir)
    if not directory.is_dir():
        return []

    cache_key = str(directory.resolve())
    if use_cache and cache_key in _scan_cache:
        cached_sig, cached_names = _scan_cache[cache_key]
        try:
            current_sig = _build_signature(directory)
        except Exception:
            current_sig = None
        if current_sig is not None and current_sig == cached_sig:
            return list(cached_names)

    names: List[str] = []
    try:
        for entry in os.scandir(directory):
            if not entry.is_file():
                continue
            name = entry.name
            if name.startswith(_SKIP_PREFIXES):
                continue
            if name.lower().endswith(_SKIP_SUFFIXES):
                continue
            if name.lower().endswith(SUPPORTED_EXTENSIONS):
                names.append(name)
    except OSError:
        log.warning(
            "Kunde inte skanna mallmapp: %s", directory, exc_info=True
        )
        return []

    names.sort()
    if use_cache:
        _scan_cache[cache_key] = (_build_signature(directory), names)
    return names


def _build_signature(directory: Path) -> tuple:
    """Signatur för scan-cache: (antal, max_mtime, (namn, storlek)...)."""
    entries = []
    max_mtime = 0.0
    try:
        for entry in os.scandir(directory):
            if not entry.is_file():
                continue
            name = entry.name
            if name.startswith(_SKIP_PREFIXES):
                continue
            if name.lower().endswith(_SKIP_SUFFIXES):
                continue
            if name.lower().endswith(SUPPORTED_EXTENSIONS):
                try:
                    stat = entry.stat()
                except OSError:
                    continue
                entries.append((name, stat.st_size))
                max_mtime = max(max_mtime, stat.st_mtime)
    except OSError:
        pass
    return (len(entries), max_mtime, tuple(sorted(entries)))


def export_template(path: Any) -> Optional[str]:
    """Exportera/backa upp en mallfil (.bak). Returns bakup-sökväg eller None."""
    file_path = Path(path)
    if not file_path.exists():
        return None
    backup = file_path.with_suffix(file_path.suffix + ".bak")
    try:
        backup.write_bytes(file_path.read_bytes())
        return str(backup)
    except Exception:
        log.warning(
            "Kunde inte backa upp mallen %s", file_path.name, exc_info=True
        )
        return None


def create_template(
    path: Any,
    subject: str,
    body: str,
    overwrite: bool = True,
) -> None:
    """
    Skapa/uppdatera en mallfil.

    - .txt → "ÄMNE: <subject>\n\nINNEHÅLL:\n<body>"
    - .docx → python-docx-dokument med samma struktur (ÄMNE-rad + stycken)
    - .html → komplett HTML med <title> och <body>
    """
    file_path = Path(path)
    if file_path.exists() and not overwrite:
        raise FileExistsError(f"Mallen finns redan: {file_path.name}")

    suffix = file_path.suffix.lower()
    if suffix == ".docx":
        try:
            import docx  # type: ignore
        except ImportError as exc:
            raise ValueError(
                "python-docx krävs för att skapa .docx-mallar. "
                "Installera med: pip install python-docx"
            ) from exc
        document = docx.Document()
        document.add_paragraph(f"ÄMNE: {subject}")
        document.add_paragraph("INNEHÅLL:")
        for line in (body or "").split("\n"):
            document.add_paragraph(line)
        document.save(str(file_path))
    elif suffix in (".html", ".htm"):
        # (v3.8) Escapa både ämne och brödtext – annars bryter <, > och &
        # i användartexten HTML-strukturen (placeholders påverkas inte).
        escaped_subject = _html.escape(str(subject), quote=False)
        html_text = (
            "<!DOCTYPE html>\n<html lang=\"sv\">\n<head>\n"
            f"<meta charset=\"utf-8\">\n<title>{escaped_subject}</title>\n"
            "</head>\n<body>\n"
        )
        for line in (body or "").split("\n"):
            html_text += f"<p>{_html.escape(line, quote=False)}</p>\n"
        html_text += "</body>\n</html>\n"
        file_path.write_text(html_text, encoding="utf-8")
    else:
        file_path.write_text(
            f"ÄMNE: {subject}\n\nINNEHÅLL:\n{body}\n",
            encoding="utf-8",
        )


def clear_scan_cache() -> None:
    """Rensa scan-cachen (anropas t.ex. vid mallsparning)."""
    _scan_cache.clear()


__all__ = [
    "parse_subject_and_body",
    "apply_placeholders",
    "list_placeholders",
    "find_placeholders_in_file",
    "find_placeholders_in_text",
    "build_template_body",
    "sanitize_template_filename",
    "validate_template",
    "scan_templates_dir",
    "clear_scan_cache",
    "create_template",
    "export_template",
    "TemplateVersion",
    "PLACEHOLDER_DROPDOWNS",
]
