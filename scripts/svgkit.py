"""svgkit — the NAWSHER/OS SVG design system.

Pure-Python, standard library only. Every function returns SVG markup as a
string. Output is deterministic: no random numbers, no clocks, stable ordering.

GitHub serves README images through its camo proxy as <img>, so these SVGs:
  * contain no <script>, no external hrefs, no web fonts;
  * use CSS/SMIL animations that always end in (or default to) the readable state;
  * honour prefers-reduced-motion.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICON_DIR = ROOT / "assets" / "icons" / "brands"

# ── Design tokens ────────────────────────────────────────────────────────────
WIDTH = 1000                     # every full-width asset uses a 1000-unit viewBox
MONO = ("'JetBrains Mono','Fira Code','SFMono-Regular',Consolas,"
        "'Liberation Mono',Menlo,monospace")
CHAR_W = 0.605                   # monospace advance in em (DejaVu/Menlo 0.602, Consolas 0.55)

THEMES = {
    "dark": {
        "bg": "#0A0D0B", "panel": "#0F1512", "panel2": "#131B17",
        "border": "#22302A", "grid": "#16211C",
        "text": "#D5DED8", "muted": "#8A988F", "dim": "#6A786F",
        "green": "#3DDC84", "green_soft": "#1F6F45",
        "amber": "#F2A541", "orange": "#E9783A", "cyan": "#57D3E0",
        "red": "#E5534B", "scan": "#000000", "scan_op": "0.18",
        "heat": ["#141C18", "#123A27", "#18603C", "#24924F", "#3DDC84"],
    },
    "light": {
        "bg": "#F7F8F4", "panel": "#FFFFFF", "panel2": "#F1F4EE",
        "border": "#CBD5CD", "grid": "#E6ECE5",
        "text": "#1C2420", "muted": "#55625A", "dim": "#6E7A73",
        "green": "#137A43", "green_soft": "#B9E3C9",
        "amber": "#9A5B00", "orange": "#B24A12", "cyan": "#0B7285",
        "red": "#B42318", "scan": "#000000", "scan_op": "0.025",
        "heat": ["#EBEFEA", "#B9E3C9", "#74C493", "#2F9E5E", "#137A43"],
    },
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def text_w(s: str, size: float) -> float:
    """Conservative width estimate for monospace text."""
    return len(s) * size * CHAR_W


def fit(s: str, size: float, max_w: float) -> str:
    """Truncate text with an ellipsis so it never overflows max_w."""
    max_chars = int(max_w // (size * CHAR_W))
    return s if len(s) <= max_chars else s[: max(1, max_chars - 1)] + "…"


# ── Document wrapper ─────────────────────────────────────────────────────────
BASE_CSS = """
text{font-family:%(mono)s}
@media (prefers-reduced-motion: reduce){*{animation:none!important}}
"""


def document(w: int, h: int, title: str, desc: str, body: str, t: dict, css: str = "",
             frame: bool = True, slug: str = "x") -> str:
    """Wrap body in an accessible SVG document with background, grid and scanlines."""
    tid, did = f"{slug}-title", f"{slug}-desc"
    defs = (
        f'<pattern id="{slug}-grid" width="20" height="20" patternUnits="userSpaceOnUse">'
        f'<path d="M20 0H0V20" fill="none" stroke="{t["grid"]}" stroke-width="1"/></pattern>'
        f'<pattern id="{slug}-scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        f'<rect width="4" height="1" fill="{t["scan"]}" opacity="{t["scan_op"]}"/></pattern>'
    )
    bg = ""
    if frame:
        bg = (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{t["bg"]}" '
              f'stroke="{t["border"]}"/>'
              f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="url(#{slug}-grid)" opacity="0.55"/>')
    overlay = (f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="url(#{slug}-scan)"/>'
               if frame else "")
    style = (BASE_CSS % {"mono": MONO}) + css
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="{tid} {did}">'
        f'<title id="{tid}">{esc(title)}</title><desc id="{did}">{esc(desc)}</desc>'
        f'<defs>{defs}</defs><style>{style}</style>{bg}{body}{overlay}</svg>\n'
    )


# ── Primitives ───────────────────────────────────────────────────────────────
def txt(x, y, s, t, size=14, fill="text", weight=400, anchor="start", extra="", cls="",
        spacing=None):
    color = t.get(fill, fill)
    ls = f' letter-spacing="{spacing}"' if spacing is not None else ""
    c = f' class="{cls}"' if cls else ""
    return (f'<text x="{x:g}" y="{y:g}" font-size="{size}" fill="{color}" font-weight="{weight}" '
            f'text-anchor="{anchor}"{ls}{c}{extra}>{esc(s)}</text>')


def rect(x, y, w, h, fill, stroke=None, rx=0, extra=""):
    s = f' stroke="{stroke}"' if stroke else ""
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{rx}" fill="{fill}"{s}{extra}/>'


def window(x, y, w, h, t, label, accent="green"):
    """Retro terminal window: square 'LEDs', label, thin title bar."""
    leds = "".join(rect(x + 14 + i * 14, y + 11, 8, 8, t[c]) for i, c in
                   enumerate(("orange", "amber", accent)))
    return (
        rect(x + 0.5, y + 0.5, w - 1, h - 1, t["panel"], t["border"], rx=8)
        + rect(x + 0.5, y + 0.5, w - 1, 30, t["panel2"], None, rx=8)
        + rect(x + 0.5, y + 22, w - 1, 9, t["panel2"])
        + f'<line x1="{x+1}" y1="{y+30.5}" x2="{x+w-1}" y2="{y+30.5}" stroke="{t["border"]}"/>'
        + leds
        + txt(x + 64, y + 20, label, t, size=12, fill="muted", spacing=0.5)
    )


def led(x, y, t, color="green", blink=False, r=4):
    cls = ' class="blink"' if blink else ""
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{t[color]}"{cls}/>'


def chip(x, y, label, t, size=13, color="text", border="border", icon_svg=""):
    """Rounded-rect tag with optional 16px icon. Returns (markup, width)."""
    pad = 10
    iw = 22 if icon_svg else 0
    w = pad * 2 + iw + text_w(label, size)
    h = size + 14
    m = rect(x, y, w, h, t["panel2"], t[border], rx=5)
    if icon_svg:
        m += icon_svg
    m += txt(x + pad + iw, y + h / 2 + size * 0.36, label, t, size=size, fill=color)
    return m, w


# ── Brand icons (CC0 simple-icons paths, recoloured to theme) ────────────────
_ICON_CACHE: dict[str, str] = {}


def icon_path(slug: str) -> str:
    if slug not in _ICON_CACHE:
        p = ICON_DIR / f"{slug}.svg"
        if not p.exists():
            _ICON_CACHE[slug] = ""
        else:
            m = re.search(r'<path d="([^"]+)"', p.read_text(encoding="utf-8"))
            _ICON_CACHE[slug] = m.group(1) if m else ""
    return _ICON_CACHE[slug]


def icon(slug: str, x, y, size, fill) -> str:
    """Brand icon from assets/icons/brands, or a pixel glyph fallback."""
    d = icon_path(slug)
    if d:
        s = size / 24
        return (f'<path transform="translate({x:g} {y:g}) scale({s:g})" d="{d}" fill="{fill}"/>')
    if slug == "aws":       # own pixel-cloud glyph (no official mark embedded)
        return pixel_glyph(CLOUD, x, y + size * 0.15, size / 12, fill)
    if slug == "linkedin":
        return pixel_glyph(IN_GLYPH, x, y, size / 8, fill)
    if slug == "mail":
        return pixel_glyph(MAIL, x, y + size * 0.2, size / 11, fill)
    return ""


# ── Pixel art ────────────────────────────────────────────────────────────────
def pixel_glyph(rows: list[str], x, y, px, fill, cls="") -> str:
    c = f' class="{cls}"' if cls else ""
    out = []
    for r, row in enumerate(rows):
        for col, ch in enumerate(row):
            if ch == "#":
                out.append(f'<rect x="{x + col*px:g}" y="{y + r*px:g}" width="{px:g}" height="{px:g}"/>')
    return f'<g fill="{fill}"{c}>' + "".join(out) + "</g>"


CLOUD = ["....####....", "..##....##..", ".#........##", "#..........#", "#..........#", ".##########."]
IN_GLYPH = ["########", "#......#", "#.#.##.#", "#...#..#", "#.#.#.##", "#.#.#.##", "#......#", "########"]
MAIL = ["###########", "##.......##", "#.#.....#.#", "#..#...#..#", "#...###...#", "#.........#", "###########"]

# 5×7 pixel font (uppercase + a few symbols) — original, used for the hero wordmark.
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "N": ["#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "/": ["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}


def pixel_text(s: str, x, y, px, fill, gap=1, cls="") -> tuple[str, float]:
    """Render uppercase text in the 5×7 pixel font. Returns (markup, width)."""
    out, cx = [], x
    for ch in s.upper():
        rows = FONT.get(ch, FONT[" "])
        out.append(pixel_glyph(rows, cx, y, px, fill))
        cx += (5 + gap) * px
    c = f' class="{cls}"' if cls else ""
    return f'<g{c}>' + "".join(out) + "</g>", cx - x - gap * px


def section_header(num: str, label: str, t: dict, slug: str) -> str:
    """Thin section divider: ▌02 // TELEMETRY ───── [module]."""
    w, h = WIDTH, 56
    head = f"{num} // {label}"
    body = (
        rect(0, 18, 6, 22, t["green"])
        + txt(18, 36, head, t, size=20, fill="text", weight=700, spacing=1.5)
    )
    start = 18 + text_w(head, 20) + 26
    body += f'<line x1="{start:g}" y1="29.5" x2="{w-140}" y2="29.5" stroke="{t["border"]}" stroke-dasharray="2 6"/>'
    tag = f"[{label.lower().replace(' ', '_')}.mod]"
    body += txt(w - 4, 34, tag, t, size=12, fill="muted", anchor="end")
    return document(w, h, f"Section {num}: {label}", f"Section divider for {label}", body, t,
                    frame=False, slug=slug)
