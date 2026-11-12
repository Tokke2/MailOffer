"""Saved BCC recipients associated with an exact template filename."""
from core.template_bcc import normalize_template_bcc


def normalize_template_recipients(rules):
    return normalize_template_bcc(rules)


def template_recipients(name, rules):
    return normalize_template_recipients(rules).get(name, [])


def linked_bcc(name, recipient_rules, bcc_rules):
    """Union both persisted formats without mutating settings (legacy compatible)."""
    values = template_recipients(name, recipient_rules)
    values += normalize_template_bcc(bcc_rules).get(name, [])
    return normalize_template_bcc({name: values}).get(name, [])
