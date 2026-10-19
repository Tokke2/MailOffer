#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Donationshjälpare (Ko-fi, PayPal, Swish) för E-postofferten.

Ren logik utan Qt: normalisering/validering av donationslänkar och
Swish-nummer samt bygge av Swish-QR-payload. Dialogen (med QR-bild)
bor i ``ui/donate.py``.

Standardslänkarna nedan är projektets egna (angivna av ägaren).
Inställningarna ``donation_url`` (Ko-fi), ``donation_paypal_url`` och
``donation_swish`` kan skriva över dem i *Inställningar → ❤️ Stöd & om*;
tom inställning = använd standardlänken.

Swish-QR använder C-formatet::

    C<mottagare>;<belopp>;<meddelande>;<redigerbar-mask>

Masken är bitfält: 1=mottagare, 2=belopp, 4=meddelande kan ändras av
betalaren. För donationer används 6 (belopp + meddelande öppna,
mottagaren låst) och tomt belopp så givaren väljer summa själv.

FIL: core/donate.py
"""

from __future__ import annotations

import re
from typing import Optional, Tuple
from urllib.parse import urlparse

KOFI_BASE = "https://ko-fi.com/"
PAYPAL_BASE = "https://paypal.me/"

# Projektets donationslänkar (ägarangivna 2026-10-19).
DEFAULT_KOFI_URL = "https://ko-fi.com/tokke2"
DEFAULT_PAYPAL_URL = "https://paypal.me/Rickard3dPrint"

_SCHEME_RE = re.compile(r"^https?://", re.IGNORECASE)
_SWISH_RE = re.compile(r"^(07\d{8}|123\d{7})$")
_SWISH_MSG_ALLOWED = re.compile(r"[^0-9A-Za-zÅÄÖåäö \!\?\(\)\,\.\-\:]")

SWISH_EDIT_AMOUNT_AND_MESSAGE = 6


def normalize_donation_url(raw: object, provider: str = "ko-fi") -> str:
    """Normalisera en inmatad donationslänk för vald tjänst.

    - Trimmas; "ko-fi.com/namn" → "https://ko-fi.com/namn"
    - Bara användarnamnet ("namn") → tjänstens profil-URL
      (ko-fi: ``ko-fi.com/namn``, paypal: ``paypal.me/namn``)
    - Tom inmatning → "" (betyder: använd standardlänken)
    """
    text = str(raw or "").strip()
    if not text:
        return ""
    if _SCHEME_RE.match(text):
        return text
    is_paypal = str(provider or "").strip().lower().startswith("paypal")
    base = PAYPAL_BASE if is_paypal else KOFI_BASE
    hosts = ("paypal.me/", "www.paypal.me/") if is_paypal else (
        "ko-fi.com/", "www.ko-fi.com/"
    )
    lowered = text.lower()
    if lowered.startswith(hosts):
        return "https://" + text
    if "/" not in text and "." not in text and " " not in text:
        return base + text.lstrip("@")
    if " " not in text and "." in text:
        return "https://" + text
    return text


def is_valid_donation_url(url: object, provider: str = "ko-fi") -> bool:
    """True om länken är en rimlig http(s)-URL med domän + profilstump."""
    text = normalize_donation_url(url, provider)
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
    """Ko-fi-länken uttryckligen sparad i inställningarna – annars None."""
    text = normalize_donation_url(raw, "ko-fi")
    return text if is_valid_donation_url(text, "ko-fi") else None


def resolve_donation_links(
    kofi_setting: object = "", paypal_setting: object = ""
) -> Tuple[str, str]:
    """(Ko-fi-URL, PayPal-URL) med projektets standarder som fallback.

    Sparat (giltigt) värde i inställningarna vinner; annars används
    ``DEFAULT_KOFI_URL`` / ``DEFAULT_PAYPAL_URL`` så att appen alltid
    har fungerande donationsknappar.
    """
    kofi = normalize_donation_url(kofi_setting, "ko-fi")
    if not is_valid_donation_url(kofi, "ko-fi"):
        kofi = DEFAULT_KOFI_URL
    paypal = normalize_donation_url(paypal_setting, "paypal")
    if not is_valid_donation_url(paypal, "paypal"):
        paypal = DEFAULT_PAYPAL_URL
    return kofi, paypal


# ───────────────────────────────────────────────────────────────────────
# Swish
# ───────────────────────────────────────────────────────────────────────

def normalize_swish_number(raw: object) -> str:
    """Normalisera ett Swish-nummer till nationellt sifferformat.

    "070-123 45 67", "+46 70 123 45 67" och "46701234567" blir alla
    "0701234567". Företagsnummer "123 456 78 90" → "1234567890".
    Ogiltiga tecken skalas bort; tomt → "".
    """
    digits = re.sub(r"\D", "", str(raw or ""))
    if digits.startswith("0046"):
        digits = digits[4:]
    elif digits.startswith("46") and len(digits) == 11:
        digits = digits[2:]
    if len(digits) == 9 and digits.startswith("7"):
        digits = "0" + digits
    return digits


def is_valid_swish_number(value: object) -> bool:
    """True för mobilnummer 07xxxxxxxx eller företagsnummer 123xxxxxxx."""
    return bool(_SWISH_RE.match(normalize_swish_number(value)))


def format_swish_number(value: object) -> str:
    """Visningsformat: 070-123 45 67 / 123 456 78 90 (annars orört)."""
    digits = normalize_swish_number(value)
    if len(digits) == 10 and digits.startswith("07"):
        return f"{digits[:3]}-{digits[3:6]} {digits[6:8]} {digits[8:]}"
    if len(digits) == 10 and digits.startswith("123"):
        return f"{digits[:3]} {digits[3:6]} {digits[6:8]} {digits[8:]}"
    return str(value or "").strip()


def build_swish_payload(
    number: object,
    message: str = "E-postofferten",
    amount: str = "",
) -> str:
    """Bygg Swish-QR-payload i C-format.

    ``C<mottagare>;<belopp>;<meddelande>;6`` – belopp och meddelande
    kan ändras av betalaren, mottagaren är låst. Tomt belopp (default)
    betyder att givaren väljer summa i Swish-appen.

    Raises:
        ValueError: om numret inte är ett giltigt Swish-nummer.
    """
    digits = normalize_swish_number(number)
    if not _SWISH_RE.match(digits):
        raise ValueError(f"Ogiltigt Swish-nummer: {number!r}")
    # Meddelande: max 50 tecken, inga ";" (fältavgränsare) eller otillåtna tecken
    msg = _SWISH_MSG_ALLOWED.sub("", str(message or "")).strip()[:50]
    amt = str(amount or "").strip().replace(".", ",")
    if amt:
        if not re.fullmatch(r"\d+(,\d{1,2})?", amt):
            raise ValueError(f"Ogiltigt belopp: {amount!r}")
        if "," in amt:  # kanoniskt öresformat: 49,5 -> 49,50
            whole, frac = amt.split(",", 1)
            amt = f"{whole},{frac.ljust(2, '0')}"
    return f"C{digits};{amt};{msg};{SWISH_EDIT_AMOUNT_AND_MESSAGE}"


__all__ = [
    "DEFAULT_KOFI_URL",
    "DEFAULT_PAYPAL_URL",
    "KOFI_BASE",
    "PAYPAL_BASE",
    "build_swish_payload",
    "configured_donation_url",
    "format_swish_number",
    "is_valid_donation_url",
    "is_valid_swish_number",
    "normalize_donation_url",
    "normalize_swish_number",
    "resolve_donation_links",
]
