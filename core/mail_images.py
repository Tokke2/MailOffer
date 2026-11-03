"""Local, bounded image-attachment inbox for the Thunderbird bridge."""
import base64
import hashlib
import json
from pathlib import Path
import re
import shutil
import uuid

MAX_FILE = 10 * 1024 * 1024
MAX_TOTAL = 20 * 1024 * 1024
MAX_FILES = 10


def image_extension(data):
    if data.startswith(b'\x89PNG\r\n\x1a\n'): return '.png'
    if data.startswith(b'\xff\xd8\xff'): return '.jpg'
    if data.startswith((b'GIF87a', b'GIF89a')): return '.gif'
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP': return '.webp'
    if data.startswith(b'BM'): return '.bmp'
    if data.startswith((b'II*\x00', b'MM\x00*')): return '.tiff'
    raise ValueError('Bilagan har inte ett tillåtet bildformat (PNG/JPEG/GIF/WebP/BMP/TIFF).')


def queue_images(base, images, subject=''):
    if not isinstance(images, list) or not 1 <= len(images) <= MAX_FILES:
        raise ValueError('Välj 1–10 bildbilagor per import.')
    validated, total = [], 0
    for item in images:
        if not isinstance(item, dict) or not isinstance(item.get('data'), str):
            raise ValueError('Ogiltig bildbilaga.')
        if len(item['data']) > ((MAX_FILE + 2) // 3) * 4:
            raise ValueError('En bild får vara högst 10 MB.')
        data = base64.b64decode(item['data'], validate=True)
        if not data or len(data) > MAX_FILE:
            raise ValueError('Tom eller för stor bildbilaga.')
        extension = image_extension(data)
        total += len(data)
        if total > MAX_TOTAL:
            raise ValueError('Bildbilagorna får vara högst 20 MB tillsammans.')
        stem = re.sub(r'[^\w .-]', '_', str(item.get('name') or 'bild'))[:100].strip(' .')
        stem = Path(stem).stem or 'bild'
        validated.append((stem, extension, data))
    root = Path(base).resolve() / '.data' / 'mail-images'
    if root.is_symlink() or root.resolve() != root:
        raise ValueError('Osäker importmapp.')
    root.mkdir(parents=True, exist_ok=True)
    job = root / uuid.uuid4().hex
    job.mkdir(mode=0o700)
    try:
        manifest = {'subject': str(subject)[:300], 'images': []}
        for index, (stem, extension, data) in enumerate(validated, 1):
            name = f'{index:02d}-{stem}{extension}'
            (job / name).write_bytes(data)
            manifest['images'].append({'name': name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        temporary = job / 'request.tmp'
        temporary.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        temporary.replace(job / 'request.json')
        return {'count': len(validated), 'bytes': total}
    except Exception:
        shutil.rmtree(job)
        raise


def pending_requests(base):
    root = Path(base).resolve() / '.data' / 'mail-images'
    if not root.exists() or root.resolve() != root:
        return []
    return sorted(p for p in root.glob('*/request.json')
                  if not p.is_symlink() and not p.parent.is_symlink() and p.parent.resolve().parent == root)


def read_request(path):
    path = Path(path)
    if path.is_symlink() or path.parent.is_symlink() or path.stat().st_size > 65536:
        raise ValueError('Osäker eller för stor importbegäran.')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    images = manifest.get('images')
    if not isinstance(images, list) or not 1 <= len(images) <= MAX_FILES:
        raise ValueError('Ogiltigt antal bilder i importen.')
    paths, total = [], 0
    for item in images:
        name = item['name']
        if not isinstance(name, str) or '/' in name or '\\' in name or name in ('', '.', '..'):
            raise ValueError('Ogiltigt filnamn i bildimporten.')
        image = path.parent / name
        if image.is_symlink() or not image.is_file() or image.stat().st_size > MAX_FILE:
            raise ValueError('Bildfilen saknas eller är osäker.')
        data = image.read_bytes()
        total += len(data)
        if total > MAX_TOTAL or hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Bildimporten har ändrats eller är för stor.')
        if image.suffix.lower() != image_extension(data):
            raise ValueError("Bildens filändelse matchar inte filinnehållet.")
        paths.append(str(image))
    return str(manifest.get('subject', ''))[:300], paths


def finish_request(path, status):
    if status not in ('imported', 'dismissed', 'failed'):
        raise ValueError('Ogiltig importstatus.')
    path = Path(path)
    path.replace(path.with_name(status + '.json'))
