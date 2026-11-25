#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate sharp, editable SVG masters (digital + print) and crisp raster exports.

All SVG masters contain pure closed vector outlines (<path>), zero <text>,
zero <image>, zero strokes on print masters, and semantic named <g id="...">
layers so every element and letter can be edited directly in Illustrator,
Affinity Designer, Inkscape, or CorelDRAW.
"""
from __future__ import annotations

import io
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

# DejaVu Sans Bold glyph outlines in font units (license in docs/branding-font-license.txt),
# transformed into clean 1:1 upright SVG viewBox coordinates with optical kerning.
_RAW_GLYPHS: List[Tuple[str, float, str]] = [
    ("01-E", 0, "M188 1493H1227V1202H573V924H1188V633H573V291H1249V0H188Z"),
    ("02-hyphen", 1415, "M111 735H739V444H111Z"),
    (
        "03-p",
        2275,
        "M530 162V-426H172V1120H530V956Q604 1054 694 1100.5Q784 1147 901 1147Q1108 1147 1241 982.5Q1374 818 1374 559Q1374 300 1241 135.5Q1108 -29 901 -29Q784 -29 694 17.5Q604 64 530 162ZM768 887Q653 887 591.5 802.5Q530 718 530 559Q530 400 591.5 315.5Q653 231 768 231Q883 231 943.5 315Q1004 399 1004 559Q1004 719 943.5 803Q883 887 768 887Z",
    ),
    (
        "04-o",
        3760,
        "M705 891Q586 891 523.5 805.5Q461 720 461 559Q461 398 523.5 312.5Q586 227 705 227Q822 227 884 312.5Q946 398 946 559Q946 720 884 805.5Q822 891 705 891ZM705 1147Q994 1147 1156.5 991Q1319 835 1319 559Q1319 283 1156.5 127Q994 -29 705 -29Q415 -29 251.5 127Q88 283 88 559Q88 835 251.5 991Q415 1147 705 1147Z",
    ),
    (
        "05-s",
        5185,
        "M1047 1085V813Q932 861 825 885Q718 909 623 909Q521 909 471.5 883.5Q422 858 422 805Q422 762 459.5 739Q497 716 594 705L657 696Q932 661 1027 581Q1122 501 1122 330Q1122 151 990 61Q858 -29 596 -29Q485 -29 366.5 -11.5Q248 6 123 41V313Q230 261 342.5 235Q455 209 571 209Q676 209 729 238Q782 267 782 324Q782 372 745.5 395.5Q709 419 600 432L537 440Q298 470 202 551Q106 632 106 797Q106 975 228 1061Q350 1147 602 1147Q701 1147 810 1132Q919 1117 1047 1085Z",
    ),
    (
        "06-t",
        6420,
        "M563 1438V1120H932V864H563V389Q563 311 594 283.5Q625 256 717 256H901V0H594Q382 0 293.5 88.5Q205 177 205 389V864H27V1120H205V1438Z",
    ),
    (
        "07-o",
        7415,
        "M705 891Q586 891 523.5 805.5Q461 720 461 559Q461 398 523.5 312.5Q586 227 705 227Q822 227 884 312.5Q946 398 946 559Q946 720 884 805.5Q822 891 705 891ZM705 1147Q994 1147 1156.5 991Q1319 835 1319 559Q1319 283 1156.5 127Q994 -29 705 -29Q415 -29 251.5 127Q88 283 88 559Q88 835 251.5 991Q415 1147 705 1147Z",
    ),
    (
        "08-f",
        8840,
        "M909 1556V1321H711Q635 1321 605 1293.5Q575 1266 575 1198V1120H881V864H575V0H217V864H39V1120H217V1198Q217 1381 319 1468.5Q421 1556 635 1556Z",
    ),
    (
        "09-f",
        9750,
        "M909 1556V1321H711Q635 1321 605 1293.5Q575 1266 575 1198V1120H881V864H575V0H217V864H39V1120H217V1198Q217 1381 319 1468.5Q421 1556 635 1556Z",
    ),
    (
        "10-e",
        10660,
        "M1290 563V461H453Q466 335 544 272Q622 209 762 209Q875 209 993.5 242.5Q1112 276 1237 344V68Q1110 20 983 -4.5Q856 -29 729 -29Q425 -29 256.5 125.5Q88 280 88 559Q88 833 253.5 990Q419 1147 709 1147Q973 1147 1131.5 988Q1290 829 1290 563ZM922 682Q922 784 862.5 846.5Q803 909 707 909Q603 909 538 850.5Q473 792 457 682Z",
    ),
    (
        "11-r",
        12070,
        "M1004 815Q957 837 910.5 847.5Q864 858 817 858Q679 858 604.5 769.5Q530 681 530 516V0H172V1120H530V936Q599 1046 688.5 1096.5Q778 1147 903 1147Q921 1147 942 1145.5Q963 1144 1003 1139Z",
    ),
    (
        "12-t",
        13095,
        "M563 1438V1120H932V864H563V389Q563 311 594 283.5Q625 256 717 256H901V0H594Q382 0 293.5 88.5Q205 177 205 389V864H27V1120H205V1438Z",
    ),
    (
        "13-e",
        14090,
        "M1290 563V461H453Q466 335 544 272Q622 209 762 209Q875 209 993.5 242.5Q1112 276 1237 344V68Q1110 20 983 -4.5Q856 -29 729 -29Q425 -29 256.5 125.5Q88 280 88 559Q88 833 253.5 990Q419 1147 709 1147Q973 1147 1131.5 988Q1290 829 1290 563ZM922 682Q922 784 862.5 846.5Q803 909 707 909Q603 909 538 850.5Q473 792 457 682Z",
    ),
    (
        "14-n",
        15500,
        "M1298 682V0H938V111V522Q938 667 931.5 722Q925 777 909 803Q888 838 852 857.5Q816 877 770 877Q658 877 594 790.5Q530 704 530 551V0H172V1120H530V956Q611 1054 702 1100.5Q793 1147 903 1147Q1097 1147 1197.5 1028Q1298 909 1298 682Z",
    ),
]

_TOKEN_RE = re.compile(r"[MLHVQZ]|-?\d+(?:\.\d+)?")


def _fmt(val: float) -> str:
    rounded = round(val, 2)
    if abs(rounded - round(rounded)) < 1e-6:
        return str(int(round(rounded)))
    return f"{rounded:.2f}".rstrip("0").rstrip(".")


def _transform_svg_path(
    d: str, *, tx: float = 0.0, ty: float = 0.0, sx: float = 1.0, sy: float = 1.0
) -> str:
    """Transform an absolute-command SVG path (M, L, H, V, Q, Z) into 1:1 coordinates."""
    tokens = _TOKEN_RE.findall(d)
    out: List[str] = []
    i = 0
    cmd = ""
    while i < len(tokens):
        tok = tokens[i]
        if tok.isalpha():
            cmd = tok
            out.append(cmd)
            i += 1
            continue
        if cmd in ("M", "L"):
            x = tx + float(tokens[i]) * sx
            y = ty + float(tokens[i + 1]) * sy
            out.append(f"{_fmt(x)} {_fmt(y)}")
            i += 2
        elif cmd == "H":
            x = tx + float(tokens[i]) * sx
            out.append(_fmt(x))
            i += 1
        elif cmd == "V":
            y = ty + float(tokens[i]) * sy
            out.append(_fmt(y))
            i += 1
        elif cmd == "Q":
            cx = tx + float(tokens[i]) * sx
            cy = ty + float(tokens[i + 1]) * sy
            x = tx + float(tokens[i + 2]) * sx
            y = ty + float(tokens[i + 3]) * sy
            out.append(f"{_fmt(cx)} {_fmt(cy)} {_fmt(x)} {_fmt(y)}")
            i += 4
        else:
            raise ValueError(f"Unsupported command {cmd!r}")
    return " ".join(out).replace(" Z", "Z")


def _rounded_rect_path(x: float, y: float, w: float, h: float, r: float) -> str:
    r = min(r, w / 2.0, h / 2.0)
    k = 0.5522847498 * r
    x0, y0, x1, y1 = x, y, x + w, y + h
    return (
        f"M{_fmt(x0 + r)} {_fmt(y0)}"
        f"H{_fmt(x1 - r)}"
        f"C{_fmt(x1 - r + k)} {_fmt(y0)} {_fmt(x1)} {_fmt(y0 + r - k)} {_fmt(x1)} {_fmt(y0 + r)}"
        f"V{_fmt(y1 - r)}"
        f"C{_fmt(x1)} {_fmt(y1 - r + k)} {_fmt(x1 - r + k)} {_fmt(y1)} {_fmt(x1 - r)} {_fmt(y1)}"
        f"H{_fmt(x0 + r)}"
        f"C{_fmt(x0 + r - k)} {_fmt(y1)} {_fmt(x0)} {_fmt(y1 - r + k)} {_fmt(x0)} {_fmt(y1 - r)}"
        f"V{_fmt(y0 + r)}"
        f"C{_fmt(x0)} {_fmt(y0 + r - k)} {_fmt(x0 + r - k)} {_fmt(y0)} {_fmt(x0 + r)} {_fmt(y0)}Z"
    )


def _top_rounded_rect_path(x: float, y: float, w: float, h: float, r: float) -> str:
    r = min(r, w / 2.0, h)
    k = 0.5522847498 * r
    x0, y0, x1, y1 = x, y, x + w, y + h
    return (
        f"M{_fmt(x0 + r)} {_fmt(y0)}"
        f"H{_fmt(x1 - r)}"
        f"C{_fmt(x1 - r + k)} {_fmt(y0)} {_fmt(x1)} {_fmt(y0 + r - k)} {_fmt(x1)} {_fmt(y0 + r)}"
        f"V{_fmt(y1)}H{_fmt(x0)}V{_fmt(y0 + r)}"
        f"C{_fmt(x0)} {_fmt(y0 + r - k)} {_fmt(x0 + r - k)} {_fmt(y0)} {_fmt(x0 + r)} {_fmt(y0)}Z"
    )


def _bottom_rounded_rect_path(x: float, y: float, w: float, h: float, r: float) -> str:
    r = min(r, w / 2.0, h)
    k = 0.5522847498 * r
    x0, y0, x1, y1 = x, y, x + w, y + h
    return (
        f"M{_fmt(x0)} {_fmt(y0)}H{_fmt(x1)}V{_fmt(y1 - r)}"
        f"C{_fmt(x1)} {_fmt(y1 - r + k)} {_fmt(x1 - r + k)} {_fmt(y1)} {_fmt(x1 - r)} {_fmt(y1)}"
        f"H{_fmt(x0 + r)}"
        f"C{_fmt(x0 + r - k)} {_fmt(y1)} {_fmt(x0)} {_fmt(y1 - r + k)} {_fmt(x0)} {_fmt(y1 - r)}Z"
    )


def _circle_path(cx: float, cy: float, r: float) -> str:
    k = 0.5522847498 * r
    return (
        f"M{_fmt(cx)} {_fmt(cy - r)}"
        f"C{_fmt(cx + k)} {_fmt(cy - r)} {_fmt(cx + r)} {_fmt(cy - k)} {_fmt(cx + r)} {_fmt(cy)}"
        f"C{_fmt(cx + r)} {_fmt(cy + k)} {_fmt(cx + k)} {_fmt(cy + r)} {_fmt(cx)} {_fmt(cy + r)}"
        f"C{_fmt(cx - k)} {_fmt(cy + r)} {_fmt(cx - r)} {_fmt(cy + k)} {_fmt(cx - r)} {_fmt(cy)}"
        f"C{_fmt(cx - r)} {_fmt(cy - k)} {_fmt(cx - k)} {_fmt(cy - r)} {_fmt(cx)} {_fmt(cy - r)}Z"
    )


def _thick_polyline_outline(
    pts: List[Tuple[float, float]], half_w: float
) -> str:
    """Build a crisp closed mitred/beveled polygon around a 3-point checkmark."""
    (x0, y0), (x1, y1), (x2, y2) = pts
    # Segment 1 unit normal
    dx1, dy1 = x1 - x0, y1 - y0
    l1 = math.hypot(dx1, dy1)
    ux1, uy1 = dx1 / l1, dy1 / l1
    nx1, ny1 = -uy1, ux1

    # Segment 2 unit normal
    dx2, dy2 = x2 - x1, y2 - y1
    l2 = math.hypot(dx2, dy2)
    ux2, uy2 = dx2 / l2, dy2 / l2
    nx2, ny2 = -uy2, ux2

    # Extend square end-caps slightly for crisp visual weight
    sx0, sy0 = x0 - ux1 * (half_w * 0.35), y0 - uy1 * (half_w * 0.35)
    ex2, ey2 = x2 + ux2 * (half_w * 0.35), y2 + uy2 * (half_w * 0.35)

    def _intersect(p1, d1, p2, d2):
        det = d1[0] * d2[1] - d1[1] * d2[0]
        t = ((p2[0] - p1[0]) * d2[1] - (p2[1] - p1[1]) * d2[0]) / det
        return (p1[0] + t * d1[0], p1[1] + t * d1[1])

    p0_top = (sx0 + nx1 * half_w, sy0 + ny1 * half_w)
    p0_bot = (sx0 - nx1 * half_w, sy0 - ny1 * half_w)
    p2_top = (ex2 + nx2 * half_w, ey2 + ny2 * half_w)
    p2_bot = (ex2 - nx2 * half_w, ey2 - ny2 * half_w)

    inner_join = _intersect(p0_top, (ux1, uy1), p2_top, (ux2, uy2))
    outer_join = _intersect(p0_bot, (ux1, uy1), p2_bot, (ux2, uy2))

    poly = [p0_top, inner_join, p2_top, p2_bot, outer_join, p0_bot]
    head = f"M{_fmt(poly[0][0])} {_fmt(poly[0][1])}"
    rest = "".join(f"L{_fmt(px)} {_fmt(py)}" for px, py in poly[1:])
    return head + rest + "Z"


def _scale_any_path(d: str, ox: float, oy: float, scale: float) -> str:
    """Scale a path composed of M, L, H, V, C, Z from 512x512 space to target space."""
    tokens = re.findall(r"[MLHVCZ]|-?\d+(?:\.\d+)?", d)
    out: List[str] = []
    i = 0
    cmd = ""
    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t
            out.append(cmd)
            i += 1
            continue
        if cmd in ("M", "L"):
            out.append(f"{_fmt(ox + float(tokens[i]) * scale)} {_fmt(oy + float(tokens[i + 1]) * scale)}")
            i += 2
        elif cmd == "H":
            out.append(_fmt(ox + float(tokens[i]) * scale))
            i += 1
        elif cmd == "V":
            out.append(_fmt(oy + float(tokens[i]) * scale))
            i += 1
        elif cmd == "C":
            pts = []
            for k in range(0, 6, 2):
                pts.append(f"{_fmt(ox + float(tokens[i + k]) * scale)} {_fmt(oy + float(tokens[i + k + 1]) * scale)}")
            out.append(" ".join(pts))
            i += 6
        else:
            raise ValueError(f"Unexpected cmd {cmd}")
    return " ".join(out).replace(" Z", "Z")


def _symbol_layers(mode: str, *, ox: float = 0.0, oy: float = 0.0, scale: float = 1.0) -> Tuple[str, str]:
    """Return (defs_xml, layers_xml) for the MailOffer symbol.

    mode:
      - 'digital': rich crisp gradients (ZERO transparency/filters Issues, pure closed paths)
      - 'flat': 100% solid spot-ready colors (zero gradients, zero opacity, zero strokes)
      - 'mono': 1-color black (#000000 + #FFFFFF knockouts) for B/W print, stamps & engraving
    """
    def S(path_512: str) -> str:
        if ox == 0.0 and oy == 0.0 and abs(scale - 1.0) < 1e-9:
            return path_512
        return _scale_any_path(path_512, ox, oy, scale)

    # 1. Squircle plate & crisp inner ring (evenodd closed path — zero stroke!)
    plate = S(_rounded_rect_path(24, 24, 464, 464, 108))
    rim_outer = S(_rounded_rect_path(38, 38, 436, 436, 95))
    rim_inner = S(_rounded_rect_path(46, 46, 420, 420, 87))

    # 2. Open envelope back triangle + interior pocket
    env_back = S("M84 214L256 92L428 214V372H84Z")

    # 3. Rising offer specification card + bold spec bars (legible down to 16-24px!)
    offer_card = S(_top_rounded_rect_path(140, 114, 232, 196, 22))
    spec_bar_1 = S(_rounded_rect_path(172, 148, 120, 20, 10))
    spec_pill_1 = S(_rounded_rect_path(306, 148, 34, 20, 10))
    spec_bar_2 = S(_rounded_rect_path(172, 184, 168, 18, 9))

    # 4. Crisp architectural envelope front wings & lower pocket (pure closed polygons!)
    env_base = S(_bottom_rounded_rect_path(84, 214, 344, 182, 30))
    # V-channel fold shadow separating top opening cleanly (zero jutting strokes!)
    env_v_groove = S("M84 214L256 322L428 214V234L256 342L84 234Z")
    # Lower geometric front flap
    env_lower_flap = S(
        "M94 388L232 296C247 286 265 286 280 296L418 388"
        "C412 393 405 396 398 396H114C107 396 100 393 94 388Z"
    )

    # 5. Golden Offer Approval Seal (bottom-right, cleanly inside the inner rim!)
    seal_halo = S(_circle_path(366, 342, 78))
    seal_disc = S(_circle_path(366, 342, 65))
    seal_check = S(_thick_polyline_outline([(335, 342), (357, 364), (400, 319)], 11.0))

    defs = ""
    if mode == "digital":
        defs = (
            "<defs>"
            '<linearGradient id="mo-plate" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#1E40AF"/>'
            '<stop offset="0.52" stop-color="#1D4ED8"/>'
            '<stop offset="1" stop-color="#0B1942"/>'
            "</linearGradient>"
            '<linearGradient id="mo-rim" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#7DD3FC"/>'
            '<stop offset="0.5" stop-color="#38BDF8"/>'
            '<stop offset="1" stop-color="#60A5FA"/>'
            "</linearGradient>"
            '<linearGradient id="mo-flap" x1="0" y1="0" x2="0" y2="1">'
            '<stop offset="0" stop-color="#38BDF8"/>'
            '<stop offset="1" stop-color="#0284C7"/>'
            "</linearGradient>"
            '<linearGradient id="mo-seal" x1="0" y1="0" x2="1" y2="1">'
            '<stop offset="0" stop-color="#FDE047"/>'
            '<stop offset="0.45" stop-color="#FBBF24"/>'
            '<stop offset="1" stop-color="#D97706"/>'
            "</linearGradient>"
            "</defs>"
        )
        c: Dict[str, str] = {
            "plate": "url(#mo-plate)",
            "rim": "url(#mo-rim)",
            "env_back": "url(#mo-flap)",
            "card": "#FFFFFF",
            "bar1": "#1E3A8A",
            "pill1": "#0EA5E9",
            "bar2": "#60A5FA",
            "env_base": "#EFF6FF",
            "v_groove": "#1E3A8A",
            "lower_flap": "#FFFFFF",
            "seal_halo": "#0B1942",
            "seal_disc": "url(#mo-seal)",
            "seal_check": "#0B1942",
        }
    elif mode == "flat":
        c = {
            "plate": "#18368C",
            "rim": "#38BDF8",
            "env_back": "#0EA5E9",
            "card": "#FFFFFF",
            "bar1": "#18368C",
            "pill1": "#F59E0B",
            "bar2": "#38BDF8",
            "env_base": "#DBEAFE",
            "v_groove": "#18368C",
            "lower_flap": "#FFFFFF",
            "seal_halo": "#0F1E54",
            "seal_disc": "#FBBF24",
            "seal_check": "#0F1E54",
        }
    elif mode == "mono":
        c = {
            "plate": "#000000",
            "rim": "#FFFFFF",
            "env_back": "#000000",
            "card": "#FFFFFF",
            "bar1": "#000000",
            "pill1": "#000000",
            "bar2": "#000000",
            "env_base": "#FFFFFF",
            "v_groove": "#000000",
            "lower_flap": "#FFFFFF",
            "seal_halo": "#FFFFFF",
            "seal_disc": "#000000",
            "seal_check": "#FFFFFF",
        }
    else:
        raise ValueError(mode)

    layers = (
        f'<g id="lager-symbolplatta">'
        f'<path id="symbol-basplatta" fill="{c["plate"]}" d="{plate}"/>'
        f'<path id="symbol-innerkant" fill="{c["rim"]}" fill-rule="evenodd" d="{rim_outer} {rim_inner}"/>'
        f"</g>"
        f'<g id="lager-kuvert-bak">'
        f'<path id="kuvert-bakflik" fill="{c["env_back"]}" d="{env_back}"/>'
        f"</g>"
        f'<g id="lager-offertblad">'
        f'<path id="offertblad-ark" fill="{c["card"]}" d="{offer_card}"/>'
        f'<path id="offertblad-rad-1" fill="{c["bar1"]}" d="{spec_bar_1}"/>'
        f'<path id="offertblad-prisbricka" fill="{c["pill1"]}" d="{spec_pill_1}"/>'
        f'<path id="offertblad-rad-2" fill="{c["bar2"]}" d="{spec_bar_2}"/>'
        f"</g>"
        f'<g id="lager-kuvert-fram">'
        f'<path id="kuvert-sidovingar" fill="{c["env_base"]}" d="{env_base}"/>'
        f'<path id="kuvert-bottenflik" fill="{c["lower_flap"]}" d="{env_lower_flap}"/>'
        f'<path id="kuvert-v-fals" fill="{c["v_groove"]}" d="{env_v_groove}"/>'
        f"</g>"
        f'<g id="lager-offertsigill">'
        f'<path id="sigill-kontur" fill="{c["seal_halo"]}" d="{seal_halo}"/>'
        f'<path id="sigill-guldbricka" fill="{c["seal_disc"]}" d="{seal_disc}"/>'
        f'<path id="sigill-bock" fill="{c["seal_check"]}" d="{seal_check}"/>'
        f"</g>"
    )
    return defs, layers


def _wordmark_layers(*, text_fill: str, accent_primary: str, accent_gold: str) -> str:
    scale = 0.053
    origin_x = 336.0
    baseline_y = 196.0
    glyph_paths: List[str] = []
    for gid, adv_x, raw_d in _RAW_GLYPHS:
        baked_d = _transform_svg_path(
            raw_d,
            tx=origin_x + adv_x * scale,
            ty=baseline_y,
            sx=scale,
            sy=-scale,
        )
        glyph_paths.append(
            f'<path id="bokstav-{gid}" fill="{text_fill}" d="{baked_d}"/>'
        )
    # Clean two-tone accent bar beneath "offerten" (clears the "p" descender completely)
    bar_blue = _rounded_rect_path(732, 222, 366, 10, 5)
    bar_gold = _rounded_rect_path(1112, 222, 114, 10, 5)
    return (
        '<g id="lager-ordbild">'
        + "".join(glyph_paths)
        + "</g>"
        + '<g id="lager-accentlinje">'
        + f'<path id="accent-primar" fill="{accent_primary}" d="{bar_blue}"/>'
        + f'<path id="accent-guld" fill="{accent_gold}" d="{bar_gold}"/>'
        + "</g>"
    )


from xml.sax.saxutils import escape as _xml_escape


def _wrap_svg(
    *,
    width_mm: int,
    height_mm: int,
    vb_w: int,
    vb_h: int,
    title: str,
    desc: str,
    defs: str,
    body: str,
) -> str:
    return (
        "<?xml version='1.0' encoding='utf-8'?>\n"
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_mm}mm" height="{height_mm}mm" '
        f'viewBox="0 0 {vb_w} {vb_h}" role="img">'
        f"<title>{_xml_escape(title)}</title>"
        f"<desc>{_xml_escape(desc)}</desc>"
        f"{defs}"
        f"{body}"
        "</svg>\n"
    )


def generate_all() -> None:
    desc_std = (
        "Redigerbart vektororiginal med namngivna lager och rena konturbanor (utan typsnittsberoende eller rasterbilder). "
        "© 2026 Rickard Längkvist."
    )

    # 1. Square App Icon SVG (512x512, 128x128 mm)
    defs_dig, sym_dig = _symbol_layers("digital")
    (ROOT / "icons" / "app_icon.svg").write_text(
        _wrap_svg(
            width_mm=128,
            height_mm=128,
            vb_w=512,
            vb_h=512,
            title="E-postofferten – Appikon (vektororiginal)",
            desc=desc_std,
            defs=defs_dig,
            body=sym_dig,
        ),
        encoding="utf-8",
    )

    # 2. Print Symbol SVGs (gradient + flat solid spot-ready)
    (ROOT / "tryck" / "E-postofferten-symbol.svg").write_text(
        _wrap_svg(
            width_mm=128,
            height_mm=128,
            vb_w=512,
            vb_h=512,
            title="E-postofferten – Symbol för tryck & digitalt (lagerindelad vektor)",
            desc=desc_std,
            defs=defs_dig,
            body=sym_dig,
        ),
        encoding="utf-8",
    )
    _, sym_flat_512 = _symbol_layers("flat")
    (ROOT / "tryck" / "E-postofferten-symbol-farg-plan.svg").write_text(
        _wrap_svg(
            width_mm=128,
            height_mm=128,
            vb_w=512,
            vb_h=512,
            title="E-postofferten – Plan trycksymbol utan gradienter",
            desc=desc_std,
            defs="",
            body=sym_flat_512,
        ),
        encoding="utf-8",
    )

    # 3. Horizontal Digital Logo (color symbol + dark navy wordmark for light surfaces)
    defs_h_dig, sym_h_dig = _symbol_layers("digital", ox=18.0, oy=14.0, scale=0.57)
    wm_navy = _wordmark_layers(
        text_fill="#0F265C", accent_primary="#0EA5E9", accent_gold="#F59E0B"
    )
    (ROOT / "icons" / "mailoffer-logo.svg").write_text(
        _wrap_svg(
            width_mm=180,
            height_mm=45,
            vb_w=1280,
            vb_h=320,
            title="E-postofferten – Horisontell logotyp (färg)",
            desc=desc_std,
            defs=defs_h_dig,
            body=f'<g id="lager-symbol">{sym_h_dig}</g>{wm_navy}',
        ),
        encoding="utf-8",
    )

    # 4. Horizontal Light-Text Logo (color symbol + crisp white wordmark for dark/hero surfaces)
    wm_white = _wordmark_layers(
        text_fill="#FFFFFF", accent_primary="#38BDF8", accent_gold="#FBBF24"
    )
    (ROOT / "icons" / "mailoffer-logo-light.svg").write_text(
        _wrap_svg(
            width_mm=180,
            height_mm=45,
            vb_w=1280,
            vb_h=320,
            title="E-postofferten – Horisontell logotyp för mörk bakgrund",
            desc=desc_std,
            defs=defs_h_dig,
            body=f'<g id="lager-symbol">{sym_h_dig}</g>{wm_white}',
        ),
        encoding="utf-8",
    )

    # 5. Editable Flat Print Master (Color — zero gradients, zero opacity, zero strokes, zero transforms!)
    _, sym_h_flat = _symbol_layers("flat", ox=18.0, oy=14.0, scale=0.57)
    wm_flat = _wordmark_layers(
        text_fill="#0F1E54", accent_primary="#0EA5E9", accent_gold="#F59E0B"
    )
    (ROOT / "tryck" / "E-postofferten-farg.svg").write_text(
        _wrap_svg(
            width_mm=180,
            height_mm=45,
            vb_w=1280,
            vb_h=320,
            title="E-postofferten – Redigerbart tryckoriginal (plana färger)",
            desc=desc_std,
            defs="",
            body=f'<g id="lager-symbol">{sym_h_flat}</g>{wm_flat}',
        ),
        encoding="utf-8",
    )

    # 6. Monochrome Black Print Master (1-color black + white knockouts)
    _, sym_h_mono = _symbol_layers("mono", ox=18.0, oy=14.0, scale=0.57)
    wm_mono = _wordmark_layers(
        text_fill="#000000", accent_primary="#000000", accent_gold="#000000"
    )
    mono_svg = _wrap_svg(
        width_mm=180,
        height_mm=45,
        vb_w=1280,
        vb_h=320,
        title="E-postofferten – Redigerbart tryckoriginal (svart/vit)",
        desc=desc_std,
        defs="",
        body=f'<g id="lager-symbol">{sym_h_mono}</g>{wm_mono}',
    )
    (ROOT / "tryck" / "E-postofferten-svart.svg").write_text(mono_svg, encoding="utf-8")
    (ROOT / "icons" / "mailoffer-logo-black.svg").write_text(mono_svg, encoding="utf-8")


def render_rasters() -> None:
    import xml.etree.ElementTree as ET
    import resvg_py
    from PIL import Image

    def render_svg(svg_path: Path, width: int) -> bytes:
        root = ET.parse(svg_path).getroot()
        _, _, w, h = root.attrib["viewBox"].split()
        root.set("width", w)
        root.set("height", h)
        return resvg_py.svg_to_bytes(
            svg_string=ET.tostring(root, encoding="unicode"),
            width=width,
            skip_system_fonts=True,
        )

    icon_svg = ROOT / "icons" / "app_icon.svg"
    master_1024 = Image.open(io.BytesIO(render_svg(icon_svg, 1024))).convert("RGBA")
    master_1024.save(ROOT / "icons" / "app_icon.png", optimize=True)
    master_1024.save(ROOT / "icons" / "app_icon.icns")

    # Render each ICO frame directly from vector at exact target size for razor-sharp 16–256px taskbar/tray!
    ico_sizes = (16, 24, 32, 48, 64, 128, 256)
    ico_frames = [
        Image.open(io.BytesIO(render_svg(icon_svg, s))).convert("RGBA")
        for s in ico_sizes
    ]
    ico_frames[-1].save(
        ROOT / "icons" / "app_icon.ico",
        format="ICO",
        append_images=ico_frames[:-1],
        sizes=[(s, s) for s in ico_sizes],
    )

    # Render Thunderbird 256x256 icon directly from vector!
    tb_256 = Image.open(io.BytesIO(render_svg(icon_svg, 256))).convert("RGBA")
    tb_256.save(ROOT / "thunderbird" / "icon.png", optimize=True)

    # Render horizontal logos (2560px wide = crisp up to 4K/300% DPI!)
    (ROOT / "icons" / "mailoffer-logo.png").write_bytes(
        render_svg(ROOT / "icons" / "mailoffer-logo.svg", 2560)
    )
    (ROOT / "icons" / "mailoffer-logo-light.png").write_bytes(
        render_svg(ROOT / "icons" / "mailoffer-logo-light.svg", 2560)
    )


if __name__ == "__main__":
    generate_all()
    render_rasters()
