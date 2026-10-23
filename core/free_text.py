"""Place literal user text before a template's sign-off, without Qt."""
import re

_SIGNOFF = re.compile(
    r'^(?:tack på förhand|med vänlig(?:a)? hälsning(?:ar)?|vänliga hälsningar|'
    r'mvh|hälsningar|best regards|kind regards|with kind regards|regards|'
    r'sincerely|thanks in advance|thank you in advance)(?:\s*[!,.:]?\s*$)', re.I)


def is_signoff(line):
    stripped = line.strip()
    return stripped in ('--', '-- ') or bool(_SIGNOFF.fullmatch(stripped))


def insert_free_text(body, free_text, is_html=False):
    free = (free_text or '').strip()
    if not free:
        return body
    if is_html:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(body or '', 'html.parser')
        block = soup.new_tag('div')
        block['style'] = 'white-space: pre-wrap;'
        block.string = free  # literal text, never interpret user text as markup
        for tag in soup.find_all(['p', 'div', 'span', 'td']):
            lines = tag.get_text('\n').strip().splitlines()
            if lines and is_signoff(lines[0]):
                tag.insert_before(block)
                return str(soup)
        (soup.body or soup).append(block)
        return str(soup)
    lines = (body or '').splitlines(keepends=True)
    for index, line in enumerate(lines):
        if is_signoff(line):
            before = ''.join(lines[:index]).rstrip()
            after = ''.join(lines[index:]).lstrip('\r\n')
            return '\n\n'.join(part for part in (before, free, after) if part)
    return (body or '').rstrip() + ('\n\n' if body and body.strip() else '') + free
