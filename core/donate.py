#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Donationshjälpare (Ko-fi) för E-postofferten.

Ren logik utan Qt: normalisering/validering av donationslänken som
sparas i inställningen ``donation_url``. Själva dialogen och
webbläsaröppningen bor i ``ui/donate.py``.

Användaren valde Ko-fi (2026-10-19) men angav ingen personlig länk,
så standardvärdet är tomt – länken klistras in i
Inställningar → ❤️ Stöd & om och börjar gälla direkt.

FIL: core/donate.py
"""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlparse

KOFI_BASE = "https://ko-fi.com/"

_SCHEME_RE = re.compile(r"^https?://", re.IGNORECASE)


def normalize_donation_url(raw: object) -> str:
    """Normalisera en inmatad donationslänk.

    - Trimmas; "ko-fi.com/namn" → "https://ko-fi.com/namn"
    - Bara användarnamnet ("namn") → "https://ko-fi.com/namn"
      (Ko-fi är vald tjänst, så det är den servicevänliga tolkningen)
    - Tom inmatning → "" (donation ej konfigurerad)
    """
    text = str(raw or "").strip()
    if not text:
        return ""
    if _SCHEME_RE.match(text):
        return text
    lowered = text.lower()
    if lowered.startswith("ko-fi.com/") or lowered.startswith("www.ko-fi.com/"):
        return "https://" + text
    if "/" not in text and "." not in text and " " not in text:
        # Enda ordet = Ko-fi-användarnamn
        return KOFI_BASE + text.lstrip("@")
    if " " not in text and "." in text:
        return "https://" + text
    return text


def is_valid_donation_url(url: object) -> bool:
    """True om länken är en rimlig http(s)-URL med domän + sökvägstump."""
    text = normalize_donation_url(url)
    if not text:
        return False
    try:
        parsed = urlparse(text)
    except Exception:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if not parsed.netloc or "." not in parsed.netloc:
        return False
    # En ren domän (ko-fi.com/) är ingen personlig donationssida
    return bool(parsed.path and parsed.path.strip("/"))


def configured_donation_url(raw: object) -> Optional[str]:
    """Returnera normaliserad giltig länk – eller None om ej konfigurerad."""
    text = normalize_donation_url(raw)
    return text if is_valid_donation_url(text) else None


__all__ = [
    "KOFI_BASE",
    "configured_donation_url",
    "is_valid_donation_url",
    "normalize_donation_url",
]
