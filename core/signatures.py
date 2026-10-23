"""Escaped profile signatures and embedded (not remote) logos."""
from html import escape
from pathlib import Path
from email.mime.image import MIMEImage


def append_signature(plain, html, text='', contact='', has_logo=False):
    signature = '\n'.join(str(x).strip() for x in (text, contact) if x)
    if not signature and not has_logo:
        return plain, html
    plain = (plain or '') + ('\n\n-- \n' + signature if signature else '')
    fragment = '<div class="sender-signature"><br>' + escape(signature).replace('\n', '<br>')
    if has_logo:
        fragment += '<br><img src="cid:mailoffer-signature" alt="Logotyp" style="max-width:240px">'
    fragment += '</div>'
    if html:
        import re
        if re.search(r'</body\s*>', html, re.I):
            html = re.sub(r'</body\s*>', lambda m: fragment + m.group(), html, count=1, flags=re.I)
        else:
            html += fragment
    else:
        html = '<div>' + escape(plain).replace('\n', '<br>') + '</div>'
        if has_logo:
            html += '<img src="cid:mailoffer-signature" alt="Logotyp" width="240">'
    return plain, html


def logo_part(path):
    file = Path(path)
    if file.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.gif'}:
        raise ValueError('Logotyp måste vara PNG, JPG eller GIF')
    if file.stat().st_size > 2 * 1024 * 1024:
        raise ValueError('Logotyp får vara högst 2 MB')
    part = MIMEImage(file.read_bytes())
    part.add_header('Content-ID', '<mailoffer-signature>')
    part.add_header('Content-Disposition', 'inline', filename=file.name)
    return part


def preview_signature(plain, html, profile):
    """Use the sending renderer; resolve the CID image locally for preview."""
    logo = str(profile.get('signature_logo') or '')
    if logo:
        logo_part(logo)  # same validation as actual send
    plain, html = append_signature(
        plain, html, profile.get('signature_text', ''),
        profile.get('signature_contact', ''), bool(logo))
    if logo and html:
        html = html.replace('cid:mailoffer-signature', escape(Path(logo).resolve().as_uri(), quote=True))
    return plain, html
