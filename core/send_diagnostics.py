"""Privacy-conscious outgoing-message checks, not a spam-score guarantee."""
import logging
import re
from email.utils import getaddresses

log = logging.getLogger(__name__)


def audit_message(message, *, signature_text='', signature_contact='', signature_logo='',
                  bcc_batch=False, hidden_recipients=()):
    """Inspect the final MIME without writing recipients, body or signature to logs."""
    plain = []
    html = []
    cids = set()
    attachments = 0
    for part in message.walk():
        if part.get('Content-ID'):
            cids.add(str(part['Content-ID']).strip('<>'))
        if part.get_content_disposition() == 'attachment':
            attachments += 1
            continue
        if part.get_content_type() in ('text/plain', 'text/html'):
            raw = part.get_payload(decode=True) or b''
            text = raw.decode(part.get_content_charset() or 'utf-8', errors='replace')
            (plain if part.get_content_type() == 'text/plain' else html).append(text)
    plain = '\n'.join(plain)
    html = '\n'.join(html)
    warnings = []
    if not str(message.get('Subject', '')).strip():
        warnings.append('empty_subject')
    if not plain.strip():
        warnings.append('empty_plain_body')
    configured = '\n'.join(str(x).strip() for x in (signature_text, signature_contact) if x)
    if not configured and not signature_logo:
        warnings.append('signature_not_configured')
    elif configured and configured not in plain:
        warnings.append('signature_missing_in_plain')
    if signature_logo and ('mailoffer-signature' not in cids or 'cid:mailoffer-signature' not in html):
        warnings.append('signature_logo_missing')
    if re.search(r'<img\b[^>]*\bsrc\s*=\s*[\'"]?https?://', html, re.I):
        warnings.append('remote_images')
    for cid in re.findall(r'cid:([^\s\'"<>]+)', html):
        if cid not in cids:
            warnings.append('missing_inline_image')
            break
    if re.search(r'\{\{[^{}]+\}\}', plain + html):
        warnings.append('unresolved_placeholder')
    for header in ('From', 'To', 'Date', 'Message-ID'):
        if not message.get(header):
            warnings.append('missing_' + header.lower())
    # A Bcc header would expose the hidden recipient list in the transmitted MIME.
    if message.get_all('Bcc') is not None or message.get_all('Resent-Bcc') is not None:
        raise ValueError('Bcc-header får inte finnas i utgående MIME')
    visible = {email.casefold() for _, email in getaddresses(message.get_all('To', []) + message.get_all('Cc', []))}
    if visible.intersection(str(email).casefold() for email in hidden_recipients):
        raise ValueError('Bcc-mottagare skulle exponeras i Till/Kopia')
    log.info('SEND_CHECK MIME plain=%s html=%s signature_text=%s signature_contact=%s '
             'signature_logo=%s attachments=%d bcc_batch=%s warnings=%d',
             bool(plain.strip()), bool(html.strip()), bool(signature_text), bool(signature_contact),
             bool(signature_logo), attachments, bcc_batch, len(warnings))
    for code in warnings:
        log.warning('SEND_CHECK %s', code)
    log.info('SEND_CHECK SPF/DMARC receiver evaluation and actual DKIM signing are not verified locally; '
             'SMTP acceptance does not prove inbox delivery')
    return warnings


def audit_dns(sender_email, *, checker=None):
    """Best-effort automatic DNS hints once per send action, off the GUI thread.

    TXT presence is not SPF authorization, DKIM validity or DMARC alignment.
    Common-selector misses are unknown, not evidence that DKIM is absent.
    """
    from core.dns_checks import check_domain
    domain = str(sender_email).rpartition('@')[2]
    try:
        report = (checker or check_domain)(domain, timeout=0.7)
        log.info('SEND_CHECK DNS SPF_record=%s DMARC_record=%s DKIM_common_selector=%s policy=%s',
                 report.spf_status, report.dmarc_status,
                 'found' if report.dkim_selectors else 'unknown', report.dmarc_policy)
        if report.error or report.spf_status != 'ok' or report.dmarc_status != 'ok':
            log.warning('SEND_CHECK DNS incomplete; use domain diagnostics and provider settings')
        log.info('SEND_CHECK DNS is record discovery only; receiver Authentication-Results required for actual pass/fail')
        return report
    except Exception:
        log.warning('SEND_CHECK DNS unavailable; delivery authentication remains unverified')
        return None


def check_hidden_overlap(visible, hidden, defaults, own_email, sender):
    """Do not silently promote hidden addresses to visible To via deduplication."""
    hidden_set = {str(email).strip().casefold() for email in list(hidden) + list(defaults)}
    visible_set = {str(email).strip().casefold() for email in visible}
    if own_email:
        visible_set.add(str(own_email).strip().casefold())
    if hidden_set.intersection(visible_set) or str(sender).strip().casefold() in hidden_set:
        raise ValueError('En hemlig mottagare överlappar Till/avsändare. Ta bort överlappningen före sändning.')
