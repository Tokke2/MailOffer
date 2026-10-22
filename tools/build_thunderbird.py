"""Build installable Thunderbird extension without native host or private data."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def build(root=None):
    root = Path(root or Path(__file__).resolve().parents[1])
    target = root / 'thunderbird' / 'MailOffer.xpi'
    with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
        for name in ('manifest.json', 'background.js', 'icon.png', 'popup.html', 'popup.css'):
            archive.write(root / 'thunderbird' / name, name)
    return target


if __name__ == '__main__':
    print(build())
