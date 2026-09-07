#!/usr/bin/env python3
"""
ADLC mark — reconstruction from the club's own badge.

Corrects an earlier mistake. The first pass drew a symmetric eight-petal
rosette, taken from a written description ("eight-petal lotus") rather than
from the artwork. The actual badge is not radial: it is a BLOOM — slender
petals fanning upward from a single base across roughly a half-circle, longest
in the middle and shortening toward the edges — with the bilingual
"Abu Dhabi / ابوظبي" pair set at its foot and the club name stacked beneath,
all inside a hairline ring.

This is still a reconstruction traced by eye from a 150px avatar, and it is
still not a shipping asset: the club's vector file supersedes it. What it is
good for is layout, favicons and comps that do not misrepresent the mark.

Run:  python3 brand/make_marks.py
"""
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "static" / "brand"
PLUM, GOLD, IVORY, PLUM_DEEP, INK = "#6E2144", "#9A8B3F", "#FDFCFA", "#3A0F2E", "#4A1A2E"

# Five broad lobes, not seven narrow fronds. Narrow petals fanned wide read as
# a palm; the badge's flower is bushier and rounder, the petals overlapping.
BASE = (50.0, 70.0)          # where every petal springs from
FAN  = [-58, -29, 0, 29, 58]                   # degrees from vertical
LEN  = [33.0, 43.0, 48.0, 43.0, 33.0]
WID  = [15.0, 17.0, 18.0, 17.0, 15.0]

def leaf(L, w):
    """A full rounded lobe from the origin, tip at -L. Control points stay wide
    close to the tip so it ends in a curve rather than a spike."""
    return (f"M0 0 C{w*0.92} {-L*0.28}, {w*0.86} {-L*0.74}, 0 {-L} "
            f"C{-w*0.86} {-L*0.74}, {-w*0.92} {-L*0.28}, 0 0 Z")

def bloom(stroke=PLUM, sw=1.9, fill="none"):
    bx, by = BASE
    parts = []
    for a, L, w in zip(FAN, LEN, WID):
        parts.append(f'<path d="{leaf(L, w)}" '
                     f'transform="translate({bx} {by}) rotate({a})"/>')
    return (f'<g fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
            f'stroke-linejoin="round">{"".join(parts)}</g>')

def bloom_solid(fill=PLUM):
    bx, by = BASE
    parts = [f'<path d="{leaf(L, w*1.06)}" transform="translate({bx} {by}) rotate({a})"/>'
             for a, L, w in zip(FAN, LEN, WID)]
    return f'<g fill="{fill}">{"".join(parts)}</g>'

def stem(colour=GOLD):
    """The gold calligraphic bar the Arabic 'Abu Dhabi' sits on."""
    return (f'<path d="M34 72.5 C41 68.5, 59 68.5, 66 72.5" fill="none" '
            f'stroke="{colour}" stroke-width="2.4" stroke-linecap="round"/>')

def svg(body, w=100, h=100, title=""):
    t = f"<title>{title}</title>" if title else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'width="{w}" height="{h}" role="img">{t}{body}</svg>\n')

def badge():
    """The full circular badge: ring, bloom, gold bar, bilingual name."""
    return (
        f'<circle cx="50" cy="50" r="49" fill="{IVORY}" stroke="{PLUM}" stroke-width="0.9"/>'
        + bloom() + stem() +
        f'<text x="50" y="67.5" text-anchor="middle" font-family="IBM Plex Sans Arabic, sans-serif" '
        f'font-size="7.6" font-weight="700" fill="{GOLD}">ابوظبي</text>'
        f'<text x="50" y="80.5" text-anchor="middle" font-family="IBM Plex Sans Arabic, sans-serif" '
        f'font-size="6.6" font-weight="700" fill="{PLUM}">نادي أبوظبي للسيدات</text>'
        f'<text x="50" y="88.5" text-anchor="middle" font-family="Bodoni Moda, Didot, serif" '
        f'font-size="3.9" letter-spacing="0.3" fill="{INK}">ABU DHABI LADIES CLUB</text>')

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    def w(name, content):
        (OUT / name).write_text(content, encoding="utf-8"); made.append(name)

    w("badge.svg", svg(badge(), title="Abu Dhabi Ladies Club"))
    w("mark-bloom.svg", svg(bloom() + stem(), title="Abu Dhabi Ladies Club"))
    w("mark-bloom-dark.svg", svg(
        f'<rect width="100" height="100" fill="{PLUM_DEEP}"/>'
        + bloom(stroke=GOLD, sw=2.1) + stem(IVORY), title="ADLC, dark"))
    w("mark-solid.svg", svg(bloom_solid(), title="ADLC"))
    w("favicon.svg", svg(bloom_solid(), title="ADLC"))
    w("app-icon.svg", svg(
        f'<rect width="100" height="100" rx="22" fill="{PLUM_DEEP}"/>'
        + bloom_solid(GOLD), title="ADLC app icon"))
    w("petal.svg", svg(f'<g transform="translate(50 74)"><path d="{leaf(49,9.8)}" '
                       f'fill="{PLUM}"/></g>', title="ADLC petal"))

    lock = (f'<g transform="translate(2 6) scale(0.78)">{bloom(sw=2.2)}{stem()}</g>'
            f'<text x="96" y="40" font-family="IBM Plex Sans Arabic, sans-serif" '
            f'font-size="25" font-weight="700" fill="{PLUM}">نادي أبوظبي للسيدات</text>'
            f'<text x="96" y="65" font-family="Bodoni Moda, Didot, serif" font-size="14.5" '
            f'letter-spacing="4.2" fill="{GOLD}">ABU DHABI LADIES CLUB</text>')
    w("lockup-horizontal.svg", svg(lock, w=430, h=92, title="ADLC horizontal lockup"))
    w("lockup-horizontal-dark.svg", svg(
        f'<rect width="430" height="92" fill="{PLUM_DEEP}"/>'
        f'<g transform="translate(2 6) scale(0.78)">{bloom(stroke=GOLD, sw=2.4)}{stem(IVORY)}</g>'
        f'<text x="96" y="40" font-family="IBM Plex Sans Arabic, sans-serif" font-size="25" '
        f'font-weight="700" fill="{IVORY}">نادي أبوظبي للسيدات</text>'
        f'<text x="96" y="65" font-family="Bodoni Moda, Didot, serif" font-size="14.5" '
        f'letter-spacing="4.2" fill="{GOLD}">ABU DHABI LADIES CLUB</text>',
        w=430, h=92, title="ADLC horizontal lockup, dark"))
    return made

if __name__ == "__main__":
    for n in build():
        print("wrote static/brand/" + n)
