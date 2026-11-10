"""Explicitly added To recipients associated with an exact template filename."""
from core.template_bcc import normalize_template_bcc


def normalize_template_recipients(rules):
    return normalize_template_bcc(rules)


def template_recipients(name, rules):
    return normalize_template_recipients(rules).get(name, [])
