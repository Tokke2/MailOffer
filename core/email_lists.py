#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tolka e-postlistor från text, CSV/TSV och inklistrade Excel-rader.

Modulen är medvetet fri från Qt så att den kan användas av både
kontaktlagret och mottagar-UI:t samt testas utan grafisk miljö.

Format som stöds:
- en e-postadress per rad
- adresser avgränsade med komma, semikolon, tabb eller radbrytning
- Outlook-format: ``Namn <namn@example.se>; annan@example.se``
- CSV/TSV med svenska eller engelska rubriker, t.ex.
  ``E-post;Namn;Företag;Språk;Kategori``
- rubriklösa rader/kopierade Excel-celler där en kolumn innehåller
  e-postadressen och övriga kolumner tolkas försiktigt som metadata

Dubletter slås ihop. Metadata från senare rader fyller bara i fält
som saknas, medan kategorier slås samman.

FIL: core/email_lists.py
"""

from __future__ import annotations

import csv
import io
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

_EMAIL_CANDIDATE_RE = re.compile(
    r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@"
    r"[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+"
)
_ANGLE_ADDRESS_RE = re.compile(
    r"^\s*\"?([^\"<\n;]{1,140}?)\"?\s*<\s*([^<>\s]+@[^<>\s]+)\s*>"
)
_TRAILING_PUNCTUATION = ".,;:!?)]}>\"'"

_FIELD_ALIASES: Dict[str, set] = {
    "email": {
        "email",
        "e mail",
        "email address",
        "e mail address",
        "epost",
        "e post",
        "epostadress",
        "e postadress",
        "mejl",
        "mejladress",
        "mail",
        "mail address",
        "primary email",
    },
    "name": {
        "name",
        "namn",
        "full name",
        "fullname",
        "display name",
        "kontakt",
        "kontaktperson",
        "person",
    },
    "company": {
        "company",
        "foretag",
        "firma",
        "bolag",
        "organisation",
        "organization",
    },
    "language": {
        "language",
        "lang",
        "locale",
        "sprak",
        "sprakkod",
    },
    "categories": {
        "categories",
        "category",
        "kategori",
        "kategorier",
        "group",
        "groups",
        "grupp",
        "grupper",
        "lista",
        "list",
        "listnamn",
        "list name",
        "tags",
        "taggar",
        "etikett",
        "etiketter",
    },
}
_ALIAS_TO_FIELD = {
    alias: field_name
    for field_name, aliases in _FIELD_ALIASES.items()
    for alias in aliases
}
_LANGUAGE_EN = {"en", "eng", "english", "engelska", "gb", "uk", "us", "en gb", "en us"}
_LANGUAGE_SV = {"sv", "swe", "swedish", "svenska", "se", "sv se"}


@dataclass
class ParsedContact:
    """En kontakt funnen i en e-postlista."""

    email: str
    name: str = ""
    company: str = ""
    # Tom sträng betyder att listan inte angav språk. Anropande kod
    # väljer då standard eller bevarar kontaktens befintliga språk.
    language: str = ""
    categories: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "email": self.email,
            "name": self.name,
            "company": self.company,
            "language": self.language,
            "categories": list(self.categories),
        }


@dataclass
class ParsedEmailList:
    """Resultatet av en tolkning, inklusive enkel importstatistik."""

    contacts: List[ParsedContact] = field(default_factory=list)
    invalid: int = 0
    duplicates: int = 0

    @property
    def emails(self) -> List[str]:
        return [contact.email for contact in self.contacts]


def _is_plausible_email(value: str) -> bool:
    candidate = str(value or "").strip().strip("<>\"'").rstrip(_TRAILING_PUNCTUATION)
    if candidate.count("@") != 1 or len(candidate) > 254:
        return False
    local, domain = candidate.split("@", 1)
    if not local or local.startswith(".") or local.endswith(".") or ".." in local:
        return False
    labels = domain.split(".")
    if len(labels) < 2 or len(labels[-1]) < 2 or not labels[-1].isalpha():
        return False
    return all(
        label and not label.startswith("-") and not label.endswith("-")
        for label in labels
    )


def _clean_email(value: object) -> str:
    return str(value or "").strip().strip("<>\"'").rstrip(_TRAILING_PUNCTUATION).lower()


def extract_email_addresses(text: object) -> List[str]:
    """Extrahera unika giltiga e-postadresser ur fri text, i ordning."""
    result: List[str] = []
    seen = set()
    for match in _EMAIL_CANDIDATE_RE.finditer(str(text or "")):
        email = _clean_email(match.group(0))
        if not _is_plausible_email(email) or email in seen:
            continue
        seen.add(email)
        result.append(email)
    return result


def _normalize_header(value: object) -> str:
    text = str(value or "").lstrip("\ufeff").strip().lower()
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return " ".join(re.findall(r"[a-z0-9]+", ascii_text))


def _normalize_language(value: object) -> str:
    text = _normalize_header(value)
    if text in _LANGUAGE_EN or text.startswith("en "):
        return "en"
    if text in _LANGUAGE_SV or text.startswith("sv "):
        return "sv"
    return ""


def _split_categories(value: object) -> List[str]:
    categories: List[str] = []
    for part in re.split(r"[;,|/]", str(value or "")):
        category = part.strip()
        if category and category not in categories:
            categories.append(category)
    return categories


def _detect_delimiter(text: str) -> str:
    sample_lines = [line for line in text.splitlines()[:20] if line.strip()]
    if not sample_lines:
        return ","
    sample = "\n".join(sample_lines[:10])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
        return str(dialect.delimiter)
    except csv.Error:
        pass
    first = sample_lines[0]
    counts = {delimiter: first.count(delimiter) for delimiter in (";", "\t", "|", ",")}
    best = max(counts, key=counts.get)
    return best if counts[best] else ","


def _header_map(row: Sequence[object]) -> Dict[str, int]:
    mapping: Dict[str, int] = {}
    for index, cell in enumerate(row):
        field_name = _ALIAS_TO_FIELD.get(_normalize_header(cell))
        if field_name and field_name not in mapping:
            mapping[field_name] = index
    return mapping


def _cell(row: Sequence[str], mapping: Dict[str, int], field_name: str) -> str:
    index = mapping.get(field_name)
    if index is None or index >= len(row):
        return ""
    return str(row[index] or "").strip()


def _name_from_token(token: str, email: str) -> str:
    angle = _ANGLE_ADDRESS_RE.match(token)
    if angle and _clean_email(angle.group(2)) == email:
        return angle.group(1).strip()
    # Vanligt kopieringsformat: "Anna Andersson anna@example.se".
    # Acceptera bara korta, människolika prefix utan kolon.
    match = re.match(r"^\s*([A-Za-zÅÄÖåäöÉé'’ .-]{2,80}?)\s+(?:" + re.escape(email) + r")\s*$", token)
    if match:
        return match.group(1).strip()
    return ""


def _add_or_merge(
    result: ParsedEmailList,
    by_email: Dict[str, ParsedContact],
    contact: ParsedContact,
) -> None:
    email = _clean_email(contact.email)
    if not _is_plausible_email(email):
        result.invalid += 1
        return
    contact.email = email
    contact.name = str(contact.name or "").strip()
    contact.company = str(contact.company or "").strip()
    contact.language = _normalize_language(contact.language)
    contact.categories = _split_categories(";".join(contact.categories))

    existing = by_email.get(email)
    if existing is None:
        by_email[email] = contact
        result.contacts.append(contact)
        return
    result.duplicates += 1
    if not existing.name and contact.name:
        existing.name = contact.name
    if not existing.company and contact.company:
        existing.company = contact.company
    if not existing.language and contact.language:
        existing.language = contact.language
    for category in contact.categories:
        if category not in existing.categories:
            existing.categories.append(category)


def _parse_freeform_token(
    result: ParsedEmailList,
    by_email: Dict[str, ParsedContact],
    token: str,
) -> None:
    emails = extract_email_addresses(token)
    if not emails:
        if token.strip():
            result.invalid += 1
        return
    for email in emails:
        _add_or_merge(
            result,
            by_email,
            ParsedContact(email=email, name=_name_from_token(token, email)),
        )


def _parse_headerless_row(
    result: ParsedEmailList,
    by_email: Dict[str, ParsedContact],
    row: Sequence[str],
) -> None:
    cells = [str(cell or "").strip() for cell in row]
    if not any(cells):
        return
    if len(cells) == 1:
        # En rad kan innehålla flera adresser separerade med ; , eller mellanslag.
        segments = [part.strip() for part in re.split(r"[;\n]+", cells[0]) if part.strip()]
        if len(segments) > 1:
            for segment in segments:
                _parse_freeform_token(result, by_email, segment)
        else:
            _parse_freeform_token(result, by_email, cells[0])
        return

    row_emails: List[str] = []
    email_cells: List[tuple[int, str, List[str]]] = []
    for index, cell in enumerate(cells):
        found = extract_email_addresses(cell)
        if found:
            email_cells.append((index, cell, found))
            row_emails.extend(found)

    if not row_emails:
        if any("@" in cell for cell in cells):
            result.invalid += 1
        return

    # Flera e-postceller på samma rad är separata mottagare (typiskt
    # semikolonseparerad lista). Dela inte namn/metadata mellan dem.
    if len(email_cells) > 1:
        for _index, cell, _found in email_cells:
            _parse_freeform_token(result, by_email, cell)
        return

    email_index, email_cell, found_in_cell = email_cells[0]
    metadata = [
        cell for index, cell in enumerate(cells)
        if index != email_index and cell
    ]
    language = ""
    remaining: List[str] = []
    for value in metadata:
        normalized_language = _normalize_language(value)
        if normalized_language and _normalize_header(value) in (_LANGUAGE_EN | _LANGUAGE_SV):
            language = normalized_language
        else:
            remaining.append(value)

    shared_name = remaining[0] if remaining and len(found_in_cell) == 1 else ""
    company = ""
    if remaining:
        company = remaining[1] if shared_name and len(remaining) > 1 else remaining[0]
        if shared_name and len(found_in_cell) == 1 and len(remaining) == 1:
            company = ""
    for email in found_in_cell:
        _add_or_merge(
            result,
            by_email,
            ParsedContact(
                email=email,
                name=_name_from_token(email_cell, email) or shared_name,
                company=company,
                language=language,
            ),
        )


def parse_email_list_text(text: object) -> ParsedEmailList:
    """Tolka text/CSV/TSV till kontakter med e-post och metadata."""
    source = str(text or "").lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    result = ParsedEmailList()
    if not source.strip():
        return result

    delimiter = _detect_delimiter(source)
    try:
        rows = list(
            csv.reader(
                io.StringIO(source),
                delimiter=delimiter,
                skipinitialspace=True,
            )
        )
    except csv.Error:
        rows = [[line] for line in source.splitlines()]
    rows = [row for row in rows if any(str(cell or "").strip() for cell in row)]
    if not rows:
        return result

    by_email: Dict[str, ParsedContact] = {}
    mapping = _header_map(rows[0])
    has_header = "email" in mapping or len(mapping) >= 2
    data_rows: Iterable[Sequence[str]] = rows[1:] if has_header else rows

    if not has_header:
        for row in data_rows:
            _parse_headerless_row(result, by_email, row)
        return result

    for row in data_rows:
        cells = [str(cell or "").strip() for cell in row]
        if not any(cells):
            continue
        email_value = _cell(cells, mapping, "email")
        emails = extract_email_addresses(email_value)
        if not emails and "email" not in mapping:
            emails = extract_email_addresses(" ".join(cells))
        if not emails:
            if email_value or any("@" in cell for cell in cells):
                result.invalid += 1
            continue

        name = _cell(cells, mapping, "name")
        company = _cell(cells, mapping, "company")
        language = _normalize_language(_cell(cells, mapping, "language"))
        categories = _split_categories(_cell(cells, mapping, "categories"))
        for email in emails:
            _add_or_merge(
                result,
                by_email,
                ParsedContact(
                    email=email,
                    name=name or _name_from_token(email_value, email),
                    company=company,
                    language=language,
                    categories=list(categories),
                ),
            )
    return result


def read_email_list_file(path: str | Path) -> ParsedEmailList:
    """Läs och tolka en .txt/.csv/.tsv-fil med rimlig teckenfallback."""
    file_path = Path(path)
    data = file_path.read_bytes()
    if data.startswith(b"PK\x03\x04"):
        raise ValueError(
            "Excel-filer (.xlsx) kan inte läsas direkt. "
            "Spara som CSV eller kopiera cellerna och klistra in listan."
        )
    text: Optional[str] = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = data.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    if text is None:  # latin-1 ska alltid lyckas, men behåll en säker fallback.
        text = data.decode("utf-8", errors="replace")
    return parse_email_list_text(text)


__all__ = [
    "ParsedContact",
    "ParsedEmailList",
    "extract_email_addresses",
    "parse_email_list_text",
    "read_email_list_file",
]
