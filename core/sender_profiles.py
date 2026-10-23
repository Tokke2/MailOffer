#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Avsändarprofiler för E-postofferten.

En profil samlar allt som behövs för att skicka från ett visst
konto/företag: SMTP-server och port, avsändaradress/-namn,
inloggning, Reply-To, egen To-adress, arkivkopia och SSL-val.

Modulen är ren logik utan Qt. ``SettingsManager`` använder hjälparna
för att normalisera profiler som sparas i inställningsfilen, och
UI:t använder samma fältlista. De gamla platta SMTP-nycklarna i
inställningarna behålls som spegel av den aktiva profilen för
bakåtkompatibilitet med äldre kod (tray, Thunderbird-brygga m.m.).

FIL: core/sender_profiles.py
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

SENDER_PROFILE_FIELDS: Tuple[str, ...] = (
    "profile_color",
    "signature_text",
    "signature_contact",
    "signature_logo",
    "smtp_server",
    "smtp_port",
    "sender_email",
    "sender_name",
    "username",
    "password",
    "reply_to",
    "own_email",
    "archive_copy_email",
    "use_ssl",
)

_STRING_FIELDS = (
    "profile_color",
    "signature_text",
    "signature_contact",
    "signature_logo",
    "smtp_server",
    "sender_email",
    "sender_name",
    "username",
    "password",
    "reply_to",
    "own_email",
    "archive_copy_email",
)

_TRUE_VALUES = {"1", "true", "yes", "on", "ja"}


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in _TRUE_VALUES
    return bool(value)


def _as_port(value: Any, default: int = 587) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        return default
    return port if 1 <= port <= 65535 else default


def slugify_profile_id(value: object, default: str = "profil") -> str:
    """Gör ett stabilt profil-id av namn/e-post (ASCII, bindestreck)."""
    text = str(value or "").strip().lower()
    decomposed = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return slug or default


def unique_profile_id(base: object, existing_ids: Iterable[str]) -> str:
    """Returnera ett ledigt profil-id baserat på ``base``."""
    existing = {str(value or "").strip().lower() for value in existing_ids}
    candidate = slugify_profile_id(base)
    if candidate not in existing:
        return candidate
    suffix = 2
    while f"{candidate}-{suffix}" in existing:
        suffix += 1
    return f"{candidate}-{suffix}"


def _default_profile_name(data: Mapping[str, Any]) -> str:
    for key in ("name", "sender_name", "sender_email", "username"):
        value = str(data.get(key) or "").strip()
        if value:
            return value
    return "Standard"


def normalize_sender_profile(
    raw: Optional[Mapping[str, Any]],
    *,
    fallback: Optional[Mapping[str, Any]] = None,
    existing_ids: Iterable[str] = (),
) -> Dict[str, Any]:
    """Normalisera en profil till exakt kända fält med rätt typer."""
    source: Dict[str, Any] = dict(fallback or {})
    if raw:
        source.update(dict(raw))

    name = str(source.get("name") or "").strip() or _default_profile_name(source)
    raw_id = str(source.get("id") or "").strip()
    profile_id = (
        slugify_profile_id(raw_id)
        if raw_id
        else unique_profile_id(name or source.get("sender_email"), existing_ids)
    )

    profile: Dict[str, Any] = {"id": profile_id, "name": name}
    for field in _STRING_FIELDS:
        profile[field] = str(source.get(field) or "").strip()
    profile["profile_color"] = normalize_profile_color(source.get("profile_color"))
    profile["smtp_port"] = _as_port(source.get("smtp_port", 587))
    profile["use_ssl"] = _as_bool(source.get("use_ssl", False))

    # Håll ordningen stabil och lättläst i inställningsfilen.
    ordered: Dict[str, Any] = {"id": profile_id, "name": name}
    for field in SENDER_PROFILE_FIELDS:
        ordered[field] = profile[field]
    return ordered


def profile_from_settings(
    data: Mapping[str, Any],
    *,
    profile_id: str = "",
    name: str = "",
) -> Dict[str, Any]:
    """Bygg en profil av de platta SMTP-nycklarna i inställningarna."""
    raw: Dict[str, Any] = {
        field: data.get(field, "" if field != "smtp_port" else 587)
        for field in SENDER_PROFILE_FIELDS
    }
    raw["id"] = profile_id or data.get("active_sender_profile_id") or ""
    raw["name"] = name or _default_profile_name(data)
    return normalize_sender_profile(raw)


def normalize_sender_profiles(
    raw_profiles: Any,
    flat_settings: Optional[Mapping[str, Any]] = None,
    active_id: object = "",
    *,
    sync_active_from_flat: bool = False,
) -> Tuple[List[Dict[str, Any]], str]:
    """Normalisera sparade profiler och välj en giltig aktiv profil.

    Saknas profiler skapas en ``Standard``-profil av de gamla platta
    SMTP-fälten. Med ``sync_active_from_flat=True`` speglas de platta
    fälten tillbaka in i den aktiva profilen (används av
    inställningsvalideringen så gamla formulär/dialoger som bara
    känner till platta nycklar ändå uppdaterar rätt profil).
    """
    flat = dict(flat_settings or {})
    profiles: List[Dict[str, Any]] = []
    seen: List[str] = []

    if isinstance(raw_profiles, list):
        for raw in raw_profiles:
            if not isinstance(raw, Mapping):
                continue
            profile = normalize_sender_profile(raw, existing_ids=seen)
            if profile["id"] in seen:
                profile["id"] = unique_profile_id(profile["id"], seen)
            seen.append(str(profile["id"]))
            profiles.append(profile)

    if not profiles:
        profiles = [profile_from_settings(flat)]

    wanted = slugify_profile_id(active_id) if str(active_id or "").strip() else ""
    active = next(
        (profile for profile in profiles if profile["id"] == wanted),
        profiles[0],
    )

    if sync_active_from_flat and flat:
        synced = profile_from_settings(
            flat, profile_id=str(active["id"]), name=str(active["name"])
        )
        profiles = [
            synced if profile["id"] == active["id"] else profile
            for profile in profiles
        ]
        active = synced

    return profiles, str(active["id"])


def apply_profile_to_settings(
    data: Mapping[str, Any], profile: Mapping[str, Any]
) -> Dict[str, Any]:
    """Kopiera profilens fält till de platta SMTP-nycklarna."""
    result = dict(data)
    normalized = normalize_sender_profile(profile)
    for field in SENDER_PROFILE_FIELDS:
        result[field] = normalized[field]
    result["active_sender_profile_id"] = normalized["id"]
    return result


__all__ = [
    "SENDER_PROFILE_FIELDS",
    "apply_profile_to_settings",
    "normalize_sender_profile",
    "normalize_sender_profiles",
    "profile_from_settings",
    "slugify_profile_id",
    "unique_profile_id",
]


def normalize_profile_color(value):
    text = str(value or "").strip()
    return text.lower() if re.fullmatch(r"#[0-9a-fA-F]{6}", text) else "#4f78b8"
