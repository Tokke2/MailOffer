"""Build installable Thunderbird extension without native host or private data."""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


def build(root=None):
    root = Path(root or Path(__file__).resolve().parents[1])
    target = root / 'thunderbird' / 'MailOffer.xpi'
    with ZipFile(target, 'w', ZIP_DEFLATED) as archive:
        for name in ('manifest.json', 'protocol.json', 'background.js', 'icon.png', 'popup.html', 'popup.css'):
            info = ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (root / 'thunderbird' / name).read_bytes())
    return target


if __name__ == '__main__':
    print(build())
