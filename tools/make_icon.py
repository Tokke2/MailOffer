"""Render committed vector artwork. Build-only dependencies: Pillow, resvg-py.

No generated imagery or fonts are needed at runtime. Print masters stay SVG.
"""
from pathlib import Path
import io
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def build():
    import resvg_py
    from PIL import Image
    def render(name, width):
        root = ET.parse(ROOT / 'icons' / name).getroot()
        _, _, w, h = root.attrib['viewBox'].split()
        root.set('width', w)
        root.set('height', h)
        return resvg_py.svg_to_bytes(svg_string=ET.tostring(root, encoding='unicode'), width=width, skip_system_fonts=True)
    image = Image.open(io.BytesIO(render('app_icon.svg', 1024))).convert('RGBA')
    image.save(ROOT / 'icons/app_icon.png')
    image.save(ROOT / 'icons/app_icon.ico', sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
    image.save(ROOT / 'icons/app_icon.icns')
    image.resize((256, 256), Image.Resampling.LANCZOS).save(ROOT / 'thunderbird/icon.png')
    (ROOT / 'icons/mailoffer-logo.png').write_bytes(render('mailoffer-logo.svg', 2560))


if __name__ == '__main__':
    build()
