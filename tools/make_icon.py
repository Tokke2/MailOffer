"""Export the selected MailOffer artwork to all app and extension icon formats.

Requires Pillow. Source: icons/mailoffer-source.png (selected generated artwork).
The connected light backdrop is removed; white envelope pixels are retained.
"""
from collections import deque
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def build():
    image = Image.open(ROOT / 'icons/mailoffer-source.png').convert('RGBA')
    width, height = image.size
    pixels = image.load()
    visited = bytearray(width * height)
    queue = deque([(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1)])
    while queue:
        x, y = queue.popleft()
        index = y * width + x
        if visited[index]:
            continue
        visited[index] = 1
        r, g, b, a = pixels[x, y]
        if min(r, g, b) <= 105 or max(r, g, b) - min(r, g, b) >= 55:
            continue
        pixels[x, y] = (r, g, b, 0)
        if x: queue.append((x - 1, y))
        if y: queue.append((x, y - 1))
        if x + 1 < width: queue.append((x + 1, y))
        if y + 1 < height: queue.append((x, y + 1))
    image = image.crop(image.getbbox())
    scale = 936 / max(image.size)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    master = Image.new('RGBA', (1024, 1024))
    master.alpha_composite(image, ((1024 - image.width) // 2, (1024 - image.height) // 2))
    master.save(ROOT / 'icons/app_icon.png')
    master.save(ROOT / 'icons/app_icon.ico', sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    master.resize((256, 256), Image.Resampling.LANCZOS).save(ROOT / 'thunderbird/icon.png')


if __name__ == '__main__':
    build()
