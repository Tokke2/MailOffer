#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SMTP-förval för vanliga e-postleverantörer.

Ren logik (inget Qt): kända leverantörers server/port/säkerhet,
identifiering utifrån avsändaradressens domän eller servernamn samt
länk till leverantörens sida för applösenord. UI:t använder detta
för att fylla i SMTP-fälten i Inställningar/avsändarprofiler.

FIL: core/smtp_presets.py
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class SmtpPreset:
    """Ett leverantörsförval."""

    preset_id: str
    name: str
    server: str
    port: int
    use_ssl: bool  # True = implicit SSL (465), False = STARTTLS (587)
    domains: Tuple[str, ...] = ()
    app_password_url: str = ""
    note_key: str = ""  # i18n-nyckel för hjälptext i UI:t
    server_template: str = ""  # t.ex. "mail.{domain}" för webbhotell


PRESETS: Tuple[SmtpPreset, ...] = (
    SmtpPreset(
        preset_id="gmail",
        name="Gmail / Google Workspace",
        server="smtp.gmail.com",
        port=587,
        use_ssl=False,
        domains=("gmail.com", "googlemail.com"),
        app_password_url="https://myaccount.google.com/apppasswords",
        note_key="smtp.preset_note.gmail",
    ),
    SmtpPreset(
        preset_id="outlook",
        name="Outlook.com / Hotmail",
        server="smtp-mail.outlook.com",
        port=587,
        use_ssl=False,
        domains=("outlook.com", "hotmail.com", "live.com", "msn.com"),
        app_password_url="https://account.live.com/proofs/AppPassword",
        note_key="smtp.preset_note.outlook",
    ),
    SmtpPreset(
        preset_id="office365",
        name="Microsoft 365 (företag)",
        server="smtp.office365.com",
        port=587,
        use_ssl=False,
        domains=("onmicrosoft.com",),
        app_password_url="",
        note_key="smtp.preset_note.office365",
    ),
    SmtpPreset(
        preset_id="yahoo",
        name="Yahoo Mail",
        server="smtp.mail.yahoo.com",
        port=465,
        use_ssl=True,
        domains=("yahoo.com", "yahoo.se", "ymail.com"),
        app_password_url="https://login.yahoo.com/account/security",
        note_key="smtp.preset_note.yahoo",
    ),
    SmtpPreset(
        preset_id="icloud",
        name="iCloud Mail",
        server="smtp.mail.me.com",
        port=587,
        use_ssl=False,
        domains=("icloud.com", "me.com", "mac.com"),
        app_password_url="https://appleid.apple.com/",
        note_key="smtp.preset_note.icloud",
    ),
    SmtpPreset(
        preset_id="websupport",
        name="WebSupport (webbhotell)",
        server="smtp.websupport.se",
        port=465,
        use_ssl=True,
        note_key="smtp.preset_note.websupport",
    ),
    SmtpPreset(
        preset_id="loopia",
        name="Loopia (webbhotell)",
        server="mailcluster.loopia.se",
        port=587,
        use_ssl=False,
        note_key="smtp.preset_note.webhotel",
    ),
    SmtpPreset(
        preset_id="onecom",
        name="one.com (webbhotell)",
        server="send.one.com",
        port=587,
        use_ssl=False,
        note_key="smtp.preset_note.webhotel",
    ),
    SmtpPreset(
        preset_id="webhotel_generic",
        name="Annat webbhotell (egen domän)",
        server="",
        port=465,
        use_ssl=True,
        note_key="smtp.preset_note.webhotel_generic",
        server_template="mail.{domain}",
    ),
)


def all_presets() -> List[SmtpPreset]:
    return list(PRESETS)


def preset_by_id(preset_id: object) -> Optional[SmtpPreset]:
    wanted = str(preset_id or "").strip().lower()
    for preset in PRESETS:
        if preset.preset_id == wanted:
            return preset
    return None


def domain_from_email(email: object) -> str:
    """Domänen ur en e-postadress ('' om ogiltig)."""
    text = str(email or "").strip().lower()
    if text.count("@") != 1:
        return ""
    domain = text.split("@")[1].strip().strip(".")
    if not domain or "." not in domain or " " in domain:
        return ""
    return domain


def preset_for_email(email: object) -> Optional[SmtpPreset]:
    """Gissa leverantör utifrån avsändaradressens domän.

    Matchar exakt domän eller underdomän (t.ex.
    ``foretag.onmicrosoft.com`` → Microsoft 365).
    """
    domain = domain_from_email(email)
    if not domain:
        return None
    for preset in PRESETS:
        for known in preset.domains:
            if domain == known or domain.endswith("." + known):
                return preset
    return None


def preset_for_server(server: object) -> Optional[SmtpPreset]:
    """Leverantör utifrån SMTP-servernamn (för att spegla sparade värden)."""
    host = str(server or "").strip().lower()
    if not host:
        return None
    for preset in PRESETS:
        if preset.server and host == preset.server:
            return preset
    if host.startswith("smtp.") and host.endswith(".websupport.se"):
        return preset_by_id("websupport")
    if host.startswith("mail."):
        return preset_by_id("webhotel_generic")
    return None


def server_for_preset(preset: SmtpPreset, email: object) -> str:
    """Servernamn för ett förval; mallförval fylls med adressens domän."""
    if preset.server:
        return preset.server
    if preset.server_template:
        domain = domain_from_email(email)
        if domain:
            return preset.server_template.replace("{domain}", domain)
        return preset.server_template.replace("{domain}", "dindomän.se")
    return ""


__all__ = [
    "SmtpPreset",
    "PRESETS",
    "all_presets",
    "preset_by_id",
    "preset_for_email",
    "preset_for_server",
    "domain_from_email",
    "server_for_preset",
]
