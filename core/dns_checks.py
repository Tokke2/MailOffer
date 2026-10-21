#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DNS-kontroller för leveransbarhet: SPF, DKIM och DMARC.

Slår upp TXT-poster via DNS-over-HTTPS (Google Public DNS JSON-API)
med urllib – inga extra beroenden och fungerar på alla plattformar.
Nätverksanropet kan injiceras (``fetcher``) för tester.

DKIM kan inte kontrolleras fullständigt utan selektor; vi provar ett
antal vanliga selektorer och rapporterar vilka som hittades.

FIL: core/dns_checks.py
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

DOH_BASE = "https://dns.google/resolve"
DKIM_SELECTORS: Tuple[str, ...] = (
    "default",
    "google",
    "selector1",
    "selector2",
    "mail",
    "dkim",
    "s1",
    "k1",
)

Fetcher = Callable[[str, float], Tuple[int, bytes]]

_DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$"
)


@dataclass
class DnsReport:
    """Resultat av SPF/DKIM/DMARC-kontroll för en domän.

    Statusvärden: ``ok``, ``missing`` eller ``error``.
    """

    domain: str = ""
    spf_status: str = "missing"
    spf_record: str = ""
    dmarc_status: str = "missing"
    dmarc_policy: str = ""
    dmarc_record: str = ""
    dkim_status: str = "missing"
    dkim_selectors: List[str] = field(default_factory=list)
    error: str = ""

    @property
    def ok_count(self) -> int:
        return sum(
            1
            for status in (self.spf_status, self.dmarc_status, self.dkim_status)
            if status == "ok"
        )


def _default_fetcher(url: str, timeout: float) -> Tuple[int, bytes]:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/dns-json",
            "User-Agent": "E-postofferten (DNS-kontroll)",
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


def _join_txt(data: str) -> str:
    """Slå ihop citerade TXT-segment: '"abc" "def"' → 'abcdef'."""
    parts = re.findall(r'"([^"]*)"', data)
    if parts:
        return "".join(parts)
    return data.strip()


def fetch_txt_records(
    name: str,
    *,
    fetcher: Optional[Fetcher] = None,
    timeout: float = 8.0,
) -> List[str]:
    """Hämta TXT-poster för ett namn via DNS-over-HTTPS."""
    fetch = fetcher or _default_fetcher
    query = urllib.parse.urlencode({"name": name, "type": "TXT"})
    status, body = fetch(f"{DOH_BASE}?{query}", float(timeout))
    if status != 200:
        raise OSError(f"DNS-uppslagning svarade HTTP {status}")
    payload = json.loads(body.decode("utf-8", errors="replace"))
    if not isinstance(payload, dict):
        raise ValueError("Oväntat DNS-svar (inte JSON-objekt)")
    answers = payload.get("Answer") or []
    records: List[str] = []
    for answer in answers:
        if not isinstance(answer, dict):
            continue
        if int(answer.get("type") or 0) != 16:  # TXT
            continue
        record = _join_txt(str(answer.get("data") or ""))
        if record:
            records.append(record)
    return records


def normalize_domain(domain: object) -> str:
    """Normalisera/validera en domän ('' om ogiltig). Tar även e-post."""
    text = str(domain or "").strip().lower().rstrip(".")
    if "@" in text:
        text = text.rsplit("@", 1)[-1]
    if not _DOMAIN_RE.match(text):
        return ""
    return text


def _find_record(records: List[str], prefix: str) -> str:
    for record in records:
        if record.strip().lower().startswith(prefix):
            return record.strip()
    return ""


def _dmarc_policy(record: str) -> str:
    match = re.search(r"(?:^|;)\s*p\s*=\s*([a-z]+)", record.lower())
    return match.group(1) if match else ""


def check_domain(
    domain: object,
    *,
    fetcher: Optional[Fetcher] = None,
    timeout: float = 8.0,
) -> DnsReport:
    """Kontrollera SPF, DMARC och vanliga DKIM-selektorer för en domän.

    Kastar aldrig – nätverksfel hamnar i ``report.error``.
    """
    report = DnsReport()
    normalized = normalize_domain(domain)
    if not normalized:
        report.error = "Ogiltig domän."
        report.spf_status = report.dmarc_status = report.dkim_status = "error"
        return report
    report.domain = normalized

    try:
        records = fetch_txt_records(normalized, fetcher=fetcher, timeout=timeout)
    except Exception as exc:
        report.error = str(exc) or exc.__class__.__name__
        report.spf_status = "error"
        records = []

    spf = _find_record(records, "v=spf1")
    if spf:
        report.spf_status = "ok"
        report.spf_record = spf
    elif report.spf_status != "error":
        report.spf_status = "missing"

    try:
        dmarc_records = fetch_txt_records(
            f"_dmarc.{normalized}", fetcher=fetcher, timeout=timeout
        )
        dmarc = _find_record(dmarc_records, "v=dmarc1")
        if dmarc:
            report.dmarc_status = "ok"
            report.dmarc_record = dmarc
            report.dmarc_policy = _dmarc_policy(dmarc)
    except Exception as exc:
        report.dmarc_status = "error"
        if not report.error:
            report.error = str(exc) or exc.__class__.__name__

    found: List[str] = []
    dkim_error = False
    for selector in DKIM_SELECTORS:
        try:
            sel_records = fetch_txt_records(
                f"{selector}._domainkey.{normalized}",
                fetcher=fetcher,
                timeout=timeout,
            )
        except Exception:
            dkim_error = True
            continue
        for record in sel_records:
            lowered = record.lower()
            if "v=dkim1" in lowered or ("p=" in lowered and len(record) > 40):
                found.append(selector)
                break
    report.dkim_selectors = found
    if found:
        report.dkim_status = "ok"
    elif dkim_error and report.error:
        report.dkim_status = "error"

    return report


__all__ = [
    "DnsReport",
    "DKIM_SELECTORS",
    "check_domain",
    "fetch_txt_records",
    "normalize_domain",
]
