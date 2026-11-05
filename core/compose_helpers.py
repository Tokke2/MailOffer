"""Compose safety helpers, independent of Qt."""
from collections import defaultdict
from email.utils import parseaddr
from pathlib import Path
import unicodedata


def duplicate_recipients(groups):
    seen = defaultdict(list)
    for label, addresses in groups.items():
        for address in addresses:
            email = parseaddr(str(address))[1].strip().casefold()
            if email:
                seen[email].append(label)
    return {email: labels for email, labels in seen.items() if len(labels) > 1}


def contact_duplicate_groups(contacts):
    """Conservative suggestions: nonempty identical name AND company, not email guesses."""
    groups = defaultdict(list)
    def normalize(value):
        return ' '.join(unicodedata.normalize('NFKC', str(value or '')).casefold().split())
    for contact in contacts:
        name, company = normalize(contact.get('name')), normalize(contact.get('company'))
        if name and company:
            groups[(name, company)].append(contact)
    return [rows for rows in groups.values() if len({r['email'].casefold() for r in rows}) > 1]


def merge_contact_rows(primary, rows):
    result = dict(primary)
    categories = []
    for row in [primary, *rows]:
        for category in [*row.get('categories', []), row.get('group', '')]:
            if category and category not in categories:
                categories.append(category)
        for key in ('name', 'company', 'group'):
            if not result.get(key) and row.get(key):
                result[key] = row[key]
    result['categories'] = categories
    return result


def dropped_local_files(urls):
    paths = []
    for url in urls:
        if url.isLocalFile():
            path = Path(url.toLocalFile())
            if path.is_file():
                paths.append(str(path))
    return paths
