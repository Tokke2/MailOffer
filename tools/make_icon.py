#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generera E-postoffertens app-ikon (samma ikon ÖVERALLT).

Ritar ikonen programmatiskt med Pillow i 2048px och skalar ner:
  - icons/app_icon.png    (1024px master, RGBA med transparenta hörn)
  - icons/app_icon.ico    (16-256px, Windows)
  - thunderbird/icon.png  (256px, samma motiv)

Design: blå→lila rundad kvadrat, vitt kuvert och guldbricka med
offertdokument – samma varumärke som tidigare ikoner, men vektor-
skarpt och med äkta transparens (den gamla PNG:n hade svart
bakgrund inbakad runt hörnen).

Kör:  python tools/make_icon.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
S = 2048  # ritstorlek (supersampling)

TOP = (31, 111, 229)      # blå
BOTTOM = (75, 44, 201)    # lila
GOLD = (238, 177, 17)
GOLD_DARK = (214, 148, 8)
WHITE = (255, 255, 255, 255)
FLAP = (205, 212, 238, 255)


def _lerp(a: tuple, b: tuple, t: float) -> tuple:
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _rounded_mask(size: int, box: tuple, radius: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(box, radius=radius, fill=255)
    return mask


def _gradient_tile() -> Image.Image:
    """Hela bakgrunds-tilen med diagonal blå→lila gradient."""
    tile = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tile)
    box = (112, 112, S - 112, S - 112)
    for y in range(box[1], box[3]):
        t = (y - box[1]) / (box[3] - box[1])
        draw.line([(box[0], y), (box[2], y)], fill=_lerp(TOP, BOTTOM, t) + (255,))
    tile.putalpha(_rounded_mask(S, box, 430))
    # Diskret ljuskant upptill för djup
    gloss = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(gloss).rounded_rectangle(
        (112, 112, S - 112, 700), radius=430, fill=(255, 255, 255, 26)
    )
    gloss.putalpha(
        Image.composite(gloss.getchannel("A"), Image.new("L", (S, S), 0),
                        _rounded_mask(S, box, 430))
    )
    return Image.alpha_composite(tile, gloss)


def _draw_envelope(canvas: Image.Image) -> None:
    # Mjuk skugga under kuvertet
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(
        (300, 640, 1748, 1460), radius=56, fill=(10, 10, 40, 90)
    )
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(28)))

    draw = ImageDraw.Draw(canvas)
    box = (284, 604, 1764, 1428)
    draw.rounded_rectangle(box, radius=52, fill=WHITE)
    cx, cy = (box[0] + box[2]) // 2, 1052
    # Flik (V) + sidoveck
    draw.line([(box[0] + 30, box[1] + 26), (cx, cy)], fill=FLAP, width=38)
    draw.line([(box[2] - 30, box[1] + 26), (cx, cy)], fill=FLAP, width=38)
    draw.line([(box[0] + 30, box[3] - 26), (cx - 110, cy + 128)], fill=FLAP, width=30)
    draw.line([(box[2] - 30, box[3] - 26), (cx + 110, cy + 128)], fill=FLAP, width=30)


def _draw_badge(canvas: Image.Image) -> None:
    draw = ImageDraw.Draw(canvas)
    outer = (1242, 1122, 1876, 1756)
    inner = (1296, 1176, 1822, 1702)
    # Skugga + separationsring i bakgrundslila, sedan guldytan
    shadow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle(outer, radius=150, fill=(10, 10, 40, 100))
    canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(22)))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(outer, radius=150, fill=(58, 47, 176, 255))
    gold_w, gold_h = inner[2] - inner[0], inner[3] - inner[1]
    gold = Image.new("RGBA", (gold_w, gold_h), (0, 0, 0, 0))
    gold_draw = ImageDraw.Draw(gold)
    for y in range(gold_h):
        t = y / max(1, gold_h - 1)
        gold_draw.line([(0, y), (gold_w, y)], fill=_lerp(GOLD, GOLD_DARK, t) + (255,))
    gold_mask = Image.new("L", (gold_w, gold_h), 0)
    ImageDraw.Draw(gold_mask).rounded_rectangle(
        (0, 0, gold_w, gold_h), radius=120, fill=255
    )
    gold.putalpha(gold_mask)
    canvas.alpha_composite(gold, (inner[0], inner[1]))

    draw = ImageDraw.Draw(canvas)
    # Dokumentglyf (vit kontur + rader + vikt hörn)
    doc = (1484, 1310, 1748, 1608)
    draw.rounded_rectangle(doc, radius=26, outline=WHITE, width=36)
    draw.polygon(
        [(doc[2] - 108, doc[1] + 6), (doc[2] - 6, doc[1] + 108),
         (doc[2] - 108, doc[1] + 108)],
        fill=WHITE,
    )
    for i, y in enumerate((1436, 1508, 1580 - 28)):
        draw.line([(doc[0] + 52, y), (doc[2] - (52 if i < 2 else 118), y)],
                  fill=WHITE, width=30)
    # Citattecken uppe till vänster om dokumentet
    for x in (1332, 1424):
        draw.ellipse((x, 1276, x + 72, 1348), fill=WHITE)
        draw.polygon([(x + 2, 1316), (x + 70, 1316), (x + 8, 1404)], fill=WHITE)


def build_master() -> Image.Image:
    canvas = _gradient_tile()
    _draw_envelope(canvas)
    _draw_badge(canvas)
    return canvas.resize((1024, 1024), Image.LANCZOS)


def main() -> None:
    master = build_master()
    icons = ROOT / "icons"
    icons.mkdir(exist_ok=True)
    master.save(icons / "app_icon.png")
    master.save(
        icons / "app_icon.ico",
        sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (40, 40),
               (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    master.resize((256, 256), Image.LANCZOS).save(
        ROOT / "thunderbird" / "icon.png"
    )
    print("Ikoner skrivna: icons/app_icon.png, icons/app_icon.ico, thunderbird/icon.png")


if __name__ == "__main__":
    main()
