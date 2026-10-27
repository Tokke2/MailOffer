"""Validated, filename-scoped BCC defaults, independent of the recipient lists."""
from core.send_preflight import _looks_like_email


def normalize_template_bcc(rules):
    if not isinstance(rules, dict):
        return {}
    cleaned = {}
    for name, values in rules.items():
        if not isinstance(name, str) or not name or '/' in name or '\\' in name:
            continue
        if not isinstance(values, list):
            continue
        emails = []
        seen = set()
        for value in values:
            if not isinstance(value, str):
                continue
            email = value.strip()
            if _looks_like_email(email) and email.lower() not in seen:
                emails.append(email)
                seen.add(email.lower())
        if emails:
            cleaned[name] = emails
    return cleaned


def template_bcc(name, rules):
    return normalize_template_bcc(rules).get(name, [])
