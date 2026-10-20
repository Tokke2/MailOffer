#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Förhandskontroll (preflight) före e-postsändning.

Ren logik utan Qt: räknar slutliga mottagare (inklusive egen To och
standard-Bcc/arkivkopia), språkfördelning, dubbletter mellan To/Bcc,
ogiltiga adresser, bilagor och stoppande konfigurationsfel.

Blockerare/varningar returneras som ``(kod, värden)`` så att UI:t kan
översätta dem via ``core.i18n``.

FIL: core/send_preflight.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

_EMAIL_RE = re.compile(r"^[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+$")
Issue = Tuple[str, Dict[str, Any]]


def _looks_like_email(value: object) -> bool:
    text = str(value or "").strip()
    if not _EMAIL_RE.match(text) or ".." in text:
        return False
    local, _, domain = text.partition("@")
    return bool(local and domain and not domain.startswith(".") and not domain.endswith("."))


def _clean_list(values: Iterable[object] | None) -> List[str]:
    return [str(value).strip() for value in (values or []) if str(value or "").strip()]


def _dedupe(values: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for value in values:
        key = value.lower()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


@dataclass
class PreflightReport:
    """Sammanställning av en förhandskontroll."""

    profile_name: str = ""
    sender_email: str = ""
    smtp_server: str = ""
    smtp_port: int = 587
    to_final: List[str] = field(default_factory=list)
    bcc_final: List[str] = field(default_factory=list)
    overlap: List[str] = field(default_factory=list)
    invalid: List[str] = field(default_factory=list)
    sv_count: int = 0
    en_count: int = 0
    attachment_count: int = 0
    attachment_bytes: int = 0
    missing_attachments: List[str] = field(default_factory=list)
    blockers: List[Issue] = field(default_factory=list)
    warnings: List[Issue] = field(default_factory=list)
    test_mode: bool = False

    @property
    def total(self) -> int:
        return len(self.to_final) + len(self.bcc_final)

    @property
    def ok(self) -> bool:
        return not self.blockers

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_name": self.profile_name,
            "sender_email": self.sender_email,
            "smtp_server": self.smtp_server,
            "smtp_port": self.smtp_port,
            "to_final": list(self.to_final),
            "bcc_final": list(self.bcc_final),
            "total": self.total,
            "overlap": list(self.overlap),
            "invalid": list(self.invalid),
            "sv_count": self.sv_count,
            "en_count": self.en_count,
            "attachment_count": self.attachment_count,
            "attachment_bytes": self.attachment_bytes,
            "missing_attachments": list(self.missing_attachments),
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "test_mode": self.test_mode,
            "ok": self.ok,
        }


def build_send_preflight(
    params: Mapping[str, Any],
    *,
    bcc_batch_size: Any = 0,
    skip_invalid_recipients: bool = True,
    many_recipients_threshold: int = 100,
    bcc_batch_warning_threshold: int = 50,
) -> PreflightReport:
    """Bygg en förhandskontroll av insamlade sändparametrar."""
    profile_raw = params.get("sender_profile")
    profile: Mapping[str, Any] = profile_raw if isinstance(profile_raw, Mapping) else {}
    test_mode = bool(params.get("test_mode"))

    def profile_value(key: str, fallback: Any = "") -> Any:
        return profile.get(key, fallback) if profile else params.get(key, fallback)

    report = PreflightReport(
        profile_name=str(profile.get("name") or params.get("sender_profile_name") or ""),
        sender_email=str(profile_value("sender_email", "") or "").strip(),
        smtp_server=str(profile_value("smtp_server", "") or "").strip(),
        test_mode=test_mode,
    )
    try:
        report.smtp_port = int(profile_value("smtp_port", 587) or 587)
    except (TypeError, ValueError):
        report.smtp_port = 0

    manual_to = _dedupe(_clean_list(params.get("recipients_to")))  # type: ignore[arg-type]
    manual_bcc = _dedupe(_clean_list(params.get("recipients_bcc")))  # type: ignore[arg-type]

    own_email = str(profile_value("own_email", params.get("own_email", "")) or "").strip()
    if test_mode:
        own_email = ""
    default_bcc = [] if test_mode else _clean_list(params.get("default_bcc"))  # type: ignore[arg-type]

    to_final = _dedupe(([own_email] if own_email else []) + manual_to)
    to_keys = {email.lower() for email in to_final}
    bcc_candidates = _dedupe(manual_bcc + default_bcc)
    report.overlap = [email for email in bcc_candidates if email.lower() in to_keys]
    report.to_final = to_final
    report.bcc_final = [
        email for email in bcc_candidates if email.lower() not in to_keys
    ]

    invalid_seen = set()
    for email in report.to_final + report.bcc_final + report.overlap:
        if not _looks_like_email(email) and email.lower() not in invalid_seen:
            invalid_seen.add(email.lower())
            report.invalid.append(email)

    to_lang_raw = params.get("recipients_to_lang")
    bcc_lang_raw = params.get("recipients_bcc_lang")
    to_lang: Mapping[str, Any] = to_lang_raw if isinstance(to_lang_raw, Mapping) else {}
    bcc_lang: Mapping[str, Any] = (
        bcc_lang_raw if isinstance(bcc_lang_raw, Mapping) else {}
    )
    language_by_email: Dict[str, str] = {}
    for mapping in (to_lang, bcc_lang):
        for email, language in mapping.items():
            language_by_email[str(email).lower()] = (
                "en" if str(language or "").lower() == "en" else "sv"
            )
    for email in report.to_final + report.bcc_final:
        if language_by_email.get(email.lower()) == "en":
            report.en_count += 1
        else:
            report.sv_count += 1

    attachments = _clean_list(params.get("attachments"))  # type: ignore[arg-type]
    report.attachment_count = len(attachments)
    for raw_path in attachments:
        path = Path(raw_path)
        try:
            report.attachment_bytes += int(path.stat().st_size)
        except OSError:
            report.missing_attachments.append(path.name or raw_path)

    # ── Stoppande fel ──────────────────────────────────────────────
    if report.total == 0:
        report.blockers.append(("no_recipients", {}))
    if not report.smtp_server:
        report.blockers.append(("missing_smtp_server", {}))
    if not (1 <= report.smtp_port <= 65535):
        report.blockers.append(("invalid_smtp_port", {"port": report.smtp_port}))
    if not _looks_like_email(report.sender_email):
        report.blockers.append(("invalid_sender", {"email": report.sender_email}))

    template_path = str(params.get("template_path") or "").strip()
    if template_path and not Path(template_path).is_file():
        report.blockers.append(
            ("missing_template", {"template": Path(template_path).name})
        )
    if report.invalid and not skip_invalid_recipients:
        report.blockers.append(
            ("invalid_recipients", {"emails": report.invalid[:10]})
        )
    if report.missing_attachments:
        report.blockers.append(
            ("missing_attachments", {"files": report.missing_attachments[:10]})
        )

    # ── Varningar ──────────────────────────────────────────────────
    if report.overlap:
        report.warnings.append(("overlap", {"emails": report.overlap[:10]}))
    if report.invalid and skip_invalid_recipients:
        report.warnings.append(
            ("invalid_recipients_skipped", {"emails": report.invalid[:10]})
        )
    if not str(params.get("subject") or "").strip():
        report.warnings.append(("missing_subject", {}))

    missing_placeholders = _clean_list(params.get("placeholders_missing"))  # type: ignore[arg-type]
    if missing_placeholders:
        report.warnings.append(
            ("missing_placeholders", {"keys": missing_placeholders[:10]})
        )
    if report.total >= int(many_recipients_threshold):
        report.warnings.append(("many_recipients", {"total": report.total}))

    try:
        batch_size = int(bcc_batch_size or 0)
    except (TypeError, ValueError):
        batch_size = 0
    if batch_size <= 0 and len(report.bcc_final) >= int(bcc_batch_warning_threshold):
        report.warnings.append(
            ("bcc_no_batch", {"count": len(report.bcc_final)})
        )

    username = str(profile_value("username", "") or "").strip()
    password = str(profile_value("password", "") or "")
    if not username:
        report.warnings.append(("missing_username", {}))
    if not password:
        report.warnings.append(("missing_password", {}))
    sender_domain = report.sender_email.rsplit("@", 1)[-1].lower()
    username_domain = username.rsplit("@", 1)[-1].lower() if "@" in username else ""
    if sender_domain and username_domain and sender_domain != username_domain:
        report.warnings.append(
            (
                "sender_username_domain_mismatch",
                {"sender_domain": sender_domain, "username_domain": username_domain},
            )
        )

    return report


__all__ = ["Issue", "PreflightReport", "build_send_preflight"]
