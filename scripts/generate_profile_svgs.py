#!/usr/bin/env python3
"""Generate every profile SVG (dark + light) and README.md from
data/profile.toml and data/github-stats.json.

Deterministic: same inputs → byte-identical outputs. Standard library only.

Usage: python3 scripts/generate_profile_svgs.py [--check]
  --check   exit 1 if regenerating would change any file (used in CI/tests)
"""
from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svgkit import (WIDTH, THEMES, chip, document, esc, fit, icon, led, pixel_text,  # noqa: E402
                    rect, section_header, text_w, txt, window)

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "data" / "profile.toml"
STATS = ROOT / "data" / "github-stats.json"
GEN = ROOT / "assets" / "generated"
README = ROOT / "README.md"

ANIM_CSS = """
.blink{animation:blink 1.2s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.pulse{animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
"""


# ═════════════════════════════════════════════════════════════════════════════
#  Components
# ═════════════════════════════════════════════════════════════════════════════
def hero(cfg, t, slug):
    w, h = WIDTH, 330
    idn = cfg["identity"]
    b = []
    # corner brackets
    for (x, y, dx, dy) in ((24, 24, 1, 1), (w - 24, 24, -1, 1), (24, h - 24, 1, -1), (w - 24, h - 24, -1, -1)):
        b.append(f'<path d="M{x} {y+18*dy}V{y}H{x+18*dx}" fill="none" stroke="{t["amber"]}" stroke-width="2"/>')
    # boot line
    b.append(led(58, 56, t, "green", blink=True))
    b.append(txt(72, 61, "NAWSHER/OS v5.0  ·  backend systems workstation  ·  tty1", t, size=13, fill="muted", spacing=0.5))
    # pixel wordmark
    mark, mw = pixel_text(idn["name"], 52, 84, 8, t["green"], cls="boot")
    b.append(mark)
    # wordmark underline + cursor
    b.append(rect(52, 154, mw, 3, t["green_soft"]))
    b.append(rect(52 + mw + 14, 128, 16, 26, t["amber"], extra=' class="blink"'))
    # designation
    b.append(txt(52, 192, idn["title"].upper(), t, size=24, fill="amber", weight=700, spacing=1))
    b.append(txt(52, 222, fit(idn["subtitle"], 15, 625), t, size=15, fill="text"))
    b.append(txt(52, 248, "multi-tenant SaaS  ·  REST APIs  ·  AI integration & automation", t, size=14, fill="muted"))

    # server rack illustration (right)
    rx, ry, rw = 690, 52, 268
    b.append(rect(rx, ry, rw, 206, t["panel"], t["border"], rx=6))
    b.append(txt(rx + 14, ry + 22, "RACK-01 // services", t, size=12, fill="muted"))
    units = [("laravel.api", "green"), ("fastapi.svc", "green"), ("redis.queue", "cyan"), ("ai.agents", "amber")]
    for i, (name, col) in enumerate(units):
        uy = ry + 36 + i * 40
        b.append(rect(rx + 12, uy, rw - 24, 32, t["panel2"], t["border"], rx=4))
        for k in range(3):
            anim = f' class="pulse" style="animation-delay:{i*0.6:.1f}s"' if k == 0 else ""
            fill = t[col] if k == 0 else t["dim"]
            b.append(f'<circle cx="{rx + 28 + k*12}" cy="{uy+16}" r="3.5" fill="{fill}"{anim}/>')
        b.append(txt(rx + 70, uy + 21, name, t, size=13, fill="text"))
        # activity bars
        for k in range(6):
            bh = 4 + ((i * 7 + k * 5) % 13)
            b.append(rect(rx + rw - 96 + k * 12, uy + 26 - bh, 7, bh, t[col], extra=
                          f' opacity="0.8" class="pulse" style="animation-delay:{(k*0.25 + i*0.4):.2f}s"'))
    # status bar
    sy = 292
    b.append(f'<line x1="40" y1="{sy-22}" x2="{w-40}" y2="{sy-22}" stroke="{t["border"]}"/>')
    items = [("● ONLINE", "green"), (f"LOC {idn['location'].upper()} (UTC+5)", "muted"),
             ("MODE REMOTE / RELOCATION", "muted"), (f"EXP {idn['experience'].upper()}", "muted")]
    x = 52
    for label, col in items:
        b.append(txt(x, sy, label, t, size=12, fill=col, spacing=1))
        x += text_w(label, 12) + 12 * 0.6 * 1 + 34
    css = ANIM_CSS + """
.boot{animation:boot 1.6s steps(8) both}
@keyframes boot{0%{opacity:0}40%{opacity:.4}60%{opacity:.1}100%{opacity:1}}
.sweep{animation:sweep 6s linear infinite}
@keyframes sweep{0%{transform:translateY(-40px)}100%{transform:translateY(360px)}}
"""
    b.append(rect(1, 0, w - 2, 30, t["green"], extra=' opacity="0.05" class="sweep"'))
    return document(w, h, f"{idn['name']} — {idn['title']}",
                    f"Retro terminal banner: {idn['name']}, {idn['title']}. {idn['subtitle']}. "
                    f"Based in {idn['location']}, {idn['experience'].lower()} of experience.",
                    "".join(b), t, css, slug=slug)


def terminal(cfg, t, slug):
    lines = cfg["terminal"]["lines"]
    p = cfg["identity"]
    prompt = f"{p['prompt_user']}@{p['prompt_host']}"
    w = WIDTH
    h = 70 + len(lines) * 56 + 44
    b = [window(0, 0, w, h, t, f"{prompt}: ~ — zsh")]
    css = ANIM_CSS
    y = 64
    delay = 0.4
    for i, (cmd, out) in enumerate(lines):
        b.append(txt(24, y, prompt, t, size=16, fill="green", weight=700))
        px = 24 + text_w(prompt, 16)
        b.append(txt(px, y, ":~$", t, size=16, fill="muted"))
        cx = px + text_w(":~$ ", 16)
        b.append(txt(cx, y, cmd, t, size=16, fill="text"))
        cw = text_w(cmd, 16) + 6
        n = max(1, len(cmd))
        # typing cover: shrinks right-to-left; static state = invisible (scaleX 0)
        b.append(rect(cx - 1, y - 16, cw, 22, t["panel"],
                      extra=f' class="type{i}" transform="scale(0 1)" style="transform-origin:{cx+cw:g}px {y}px"'))
        # steps(n+1, jump-none) lands exactly on 0 at the end (plain steps() can stop one step short)
        css += (f".type{i}{{animation:type{i} {0.06*n:.2f}s steps({n + 1},jump-none) {delay:.2f}s both}}"
                f"@keyframes type{i}{{from{{transform:scaleX(1)}}to{{transform:scaleX(0)}}}}")
        delay += 0.06 * n + 0.25
        b.append(txt(24, y + 26, f"→ {out}", t, size=15, fill="amber" if i == 0 else "text",
                     extra=f' class="out{i}"'))
        css += f".out{i}{{animation:fadein .3s ease {delay:.2f}s both}}"
        delay += 0.55
        y += 56
    css += "@keyframes fadein{from{opacity:0}to{opacity:1}}"
    b.append(txt(24, y, prompt, t, size=16, fill="green", weight=700))
    px = 24 + text_w(prompt + ":~$ ", 16)
    b.append(txt(24 + text_w(prompt, 16), y, ":~$", t, size=16, fill="muted"))
    b.append(rect(px, y - 15, 10, 19, t["green"], extra=' class="blink"'))
    desc = " ".join(f"$ {c} → {o}." for c, o in lines)
    return document(w, h, "Terminal introduction", desc, "".join(b), t, css, frame=False, slug=slug)


def profile(cfg, t, slug):
    pr = cfg["profile"]
    w, h = WIDTH, 300
    b = []
    cols = [("build.list", "WHAT I BUILD", pr["build"], "green"),
            ("solve.list", "PROBLEMS I SOLVE", pr["solve"], "amber")]
    pw = 318
    for i, (label, head, items, col) in enumerate(cols):
        x = i * (pw + 23)
        b.append(window(x, 0, pw, h, t, label, accent=col))
        b.append(txt(x + 20, 62, head, t, size=14, fill=col, weight=700, spacing=1.5))
        for k, it in enumerate(items):
            y = 100 + k * 44
            b.append(txt(x + 20, y, "▸", t, size=15, fill=col))
            b.append(txt(x + 42, y, fit(it, 15, pw - 60), t, size=15, fill="text"))
    # career timeline
    x = 2 * (pw + 23)
    tw = w - x
    b.append(window(x, 0, tw, h, t, "career.log", accent="cyan"))
    b.append(txt(x + 20, 62, "CAREER TIMELINE", t, size=14, fill="cyan", weight=700, spacing=1.5))
    tl = pr["timeline"]
    b.append(f'<line x1="{x+30}" y1="88" x2="{x+30}" y2="{88 + (len(tl)-1)*50}" stroke="{t["border"]}" stroke-width="2"/>')
    for k, (org, yrs, note) in enumerate(tl):
        y = 88 + k * 50
        last = k == len(tl) - 1
        fill = t["green"] if last else t["panel2"]
        anim = ' class="pulse"' if last else ""
        b.append(f'<rect x="{x+25}" y="{y-5}" width="10" height="10" fill="{fill}" stroke="{t["green"]}"{anim}/>')
        b.append(txt(x + 50, y + 5, org, t, size=15, fill="text", weight=700))
        b.append(txt(x + tw - 18, y + 5, yrs, t, size=13, fill="amber", anchor="end"))
        b.append(txt(x + 50, y + 25, fit(note, 13, tw - 70), t, size=13, fill="muted"))
    desc = ("What I build: " + "; ".join(pr["build"]) + ". Problems I solve: " + "; ".join(pr["solve"])
            + ". Career: " + "; ".join(f"{o} {y} ({n})" for o, y, n in tl) + ".")
    return document(w, h, "Engineering profile", desc, "".join(b), t, ANIM_CSS, frame=False, slug=slug)


def _tile(x, y, w, h, label, value, t, col="green", note=""):
    m = rect(x, y, w, h, t["panel2"], t["border"], rx=6)
    m += txt(x + 16, y + 24, label, t, size=11, fill="muted", spacing=1.2)
    vs = 30 if len(str(value)) <= 6 else 21
    m += txt(x + 16, y + 62, fit(str(value), vs, w - 28), t, size=vs, fill=col, weight=700)
    if note:
        m += txt(x + 16, y + h - 12, fit(note, 11, w - 28), t, size=11, fill="dim")
    return m


LANG_COLORS = ["green", "amber", "cyan", "orange", "muted"]


def telemetry(cfg, stats, t, slug):
    w, h = WIDTH, 340
    tele = cfg["telemetry"]
    b = []
    # left: career facts (static, CV)
    lw = 400
    b.append(window(0, 0, lw, h, t, "career.facts  —  source: CV", accent="amber"))
    facts = cfg["career_facts"][:4]
    tw_, th_ = (lw - 52) / 2, 112
    for i, f in enumerate(facts):
        x = 20 + (i % 2) * (tw_ + 12)
        y = 50 + (i // 2) * (th_ + 14)
        b.append(_tile(x, y, tw_, th_, f["label"], f["value"], t, col="amber"))
    b.append(txt(20, h - 18, "career facts are static and come from the CV", t, size=11, fill="dim"))

    # right: live GitHub
    x0, rw = lw + 20, w - lw - 20
    status = (stats or {}).get("status", "pending")
    b.append(window(x0, 0, rw, h, t, "github.live  —  source: GitHub API", accent="green"))
    if status == "pending" or not stats.get("metrics"):
        b.append(txt(x0 + 24, 90, "AWAITING FIRST SYNC", t, size=22, fill="amber", weight=700, spacing=1))
        b.append(txt(x0 + 24, 124, "Live metrics appear after the first run of", t, size=14, fill="text"))
        b.append(txt(x0 + 24, 146, ".github/workflows/update-profile.yml", t, size=14, fill="green"))
        b.append(txt(x0 + 24, 180, "No numbers are shown until they come from the API.", t, size=13, fill="muted"))
        for k, line in enumerate(["▸ public repos · account age · last public push",
                                  "▸ languages and recently updated featured repos",
                                  "▸ stars, followers and contributions once they pass",
                                  "  the thresholds set in data/profile.toml"]):
            b.append(txt(x0 + 24, 222 + k * 22, line, t, size=13, fill="dim" if k == 3 else "text"))
        b.append(led(x0 + rw - 30, 90, t, "amber", blink=True))
        return document(w, h, "Telemetry", "Career facts from the CV, and live GitHub metrics awaiting first sync.",
                        "".join(b), t, ANIM_CSS, frame=False, slug=slug)

    m = stats["metrics"]
    tiles = []
    if m["public_repos"] >= tele.get("show_repos_min", 0):
        tiles.append(("PUBLIC REPOS", m["public_repos"], ""))
    c = m.get("contributions")
    if c and c["total"] >= tele["show_contributions_min"]:
        tiles.append(("CONTRIBUTIONS · 52W", c["total"], ""))
    if m["total_stars"] >= tele["show_stars_min"]:
        tiles.append(("STARS EARNED", m["total_stars"], ""))
    if m["followers"] >= tele["show_followers_min"]:
        tiles.append(("FOLLOWERS", m["followers"], ""))
    if m.get("created"):
        tiles.append(("ON GITHUB SINCE", m["created"][:4], ""))
    if m.get("last_push"):
        tiles.append(("LAST PUBLIC PUSH", m["last_push"], ""))
    tiles = tiles[:3]
    tw2 = (rw - 40 - 12 * (len(tiles) - 1)) / len(tiles)
    for i, (label, val, note) in enumerate(tiles):
        b.append(_tile(x0 + 20 + i * (tw2 + 12), 50, tw2, 96, label, val, t))
    # languages
    ly = 176
    b.append(txt(x0 + 20, ly, "LANGUAGES IN FEATURED PUBLIC CODE", t, size=11, fill="muted", spacing=1.2))
    langs = list(m.get("languages", {}).items())[:5]
    total = sum(v for _, v in langs)
    bx, bw = x0 + 20, rw - 40
    if total:
        cx = bx
        for i, (name, v) in enumerate(langs):
            seg = bw * v / total
            b.append(rect(cx, ly + 12, max(seg - 2, 2), 12, t[LANG_COLORS[i]], rx=2))
            cx += seg
        lx = bx
        for i, (name, v) in enumerate(langs):
            label = f"{name} {100*v/total:.0f}%"
            b.append(rect(lx, ly + 40, 9, 9, t[LANG_COLORS[i]]))
            b.append(txt(lx + 15, ly + 49, label, t, size=12, fill="text"))
            lx += text_w(label, 12) + 34
    else:
        b.append(rect(bx, ly + 12, bw, 12, t["panel2"], t["border"], rx=2))
        b.append(txt(bx, ly + 49, "awaiting featured public repositories — see the build queue below", t, size=12, fill="dim"))
    # recent repos
    ry = 252
    b.append(txt(x0 + 20, ry, "RECENTLY UPDATED (FEATURED)", t, size=11, fill="muted", spacing=1.2))
    recent = sorted([r for r in m["repos"] if not r["excluded"] and not r["archived"] and r["pushed"]],
                    key=lambda r: (r["pushed"], r["name"]), reverse=True)[:2]
    if recent:
        for i, r in enumerate(recent):
            yy = ry + 24 + i * 22
            b.append(txt(x0 + 20, yy, "▸ " + fit(r["name"], 13, 220), t, size=13, fill="green"))
            b.append(txt(x0 + rw - 20, yy, f"{r['language'] or '—'} · {r['pushed']}", t, size=12, fill="muted", anchor="end"))
    else:
        b.append(txt(x0 + 20, ry + 24, "▸ none yet — flagship repos are in the build queue", t, size=13, fill="dim"))
    # sync footer
    col = "amber" if status == "stale" else "green"
    b.append(led(x0 + 26, h - 22, t, col, blink=status == "stale"))
    b.append(txt(x0 + 38, h - 18, f"{status.upper()} · data as of {stats['as_of']} · @{m['login']}", t, size=11, fill="muted"))
    desc = (f"Live GitHub data for @{m['login']} as of {stats['as_of']}: "
            + ", ".join(f"{l.lower()} {v}" for l, v, _ in tiles) + ". Career facts: "
            + ", ".join(f"{f['label'].lower()} {f['value']}" for f in facts) + ".")
    return document(w, h, "Telemetry", desc, "".join(b), t, ANIM_CSS, frame=False, slug=slug)


def stack(cfg, t, slug):
    groups = cfg["stack"]
    w = WIDTH
    colw, gap = (w - 20) / 2, 20
    # lay out chips per group to compute heights
    layouts = []
    for g in groups:
        x, y, rows = 20, 52, 1
        placed = []
        for slug_i, label in g["items"]:
            ic = 22 if slug_i else 0
            cw = 20 + ic + text_w(label, 14)
            if x + cw > colw - 20:
                x, y, rows = 20, y + 44, rows + 1
            placed.append((x, y, slug_i, label))
            x += cw + 10
        layouts.append((g["group"], placed, 52 + rows * 44 + 8))
    # two columns, rows of paired groups
    b, y = [], 0
    for r in range(0, len(layouts), 2):
        pair = layouts[r:r + 2]
        rh = max(p[2] for p in pair)
        for c, (name, placed, _) in enumerate(pair):
            x0 = c * (colw + gap)
            b.append(window(x0, y, colw, rh, t, f"stack/{name.lower().replace(' & ', '_').replace(' ', '_')}",
                            accent=["green", "amber", "cyan"][(r // 2) % 3]))
            b.append(txt(x0 + colw - 20, y + 20, name, t, size=12, fill="amber", weight=700, anchor="end", spacing=1.2))
            for (cx, cy, s, label) in placed:
                ico = icon(s, x0 + cx + 10, y + cy + 7, 16, t["green"]) if s else ""
                m, _ = chip(x0 + cx, y + cy, label, t, size=14, icon_svg=ico)
                b.append(m)
        y += rh + 16
    h = y - 16
    desc = "Technology stack. " + " ".join(f"{g['group']}: " + ", ".join(l for _, l in g["items"]) + "." for g in groups)
    return document(w, h, "Technology stack", desc, "".join(b), t, frame=False, slug=slug)


def work_card(wk, t, slug):
    w, h = 490, 390
    b = [window(0, 0, w, h, t, f"deploy/{wk['id']}", accent="amber")]
    b.append(txt(22, 66, wk["name"], t, size=22, fill="amber", weight=700, spacing=1.5))
    b.append(txt(22, 90, fit(wk["org"], 13, w - 44), t, size=13, fill="muted"))
    b.append(txt(22, 120, fit(wk["summary"], 14, w - 44), t, size=14, fill="text"))
    for i, f in enumerate(wk["facts"]):
        y = 156 + i * 30
        b.append(txt(22, y, "▸", t, size=14, fill="green"))
        b.append(txt(42, y, fit(f, 14, w - 64), t, size=14, fill="text"))
    b.append(f'<line x1="22" y1="{h-62}" x2="{w-22}" y2="{h-62}" stroke="{t["border"]}" stroke-dasharray="2 5"/>')
    b.append(txt(22, h - 38, fit(wk["stack"], 13, w - 44), t, size=13, fill="cyan"))
    b.append(txt(22, h - 16, "PRIVATE EMPLOYER SYSTEM · NO PUBLIC CODE", t, size=10, fill="dim", spacing=1))
    desc = f"{wk['name']} ({wk['org']}): {wk['summary']}. " + "; ".join(wk["facts"]) + f". Stack: {wk['stack']}."
    return document(w, h, wk["name"], desc, "".join(b), t, frame=False, slug=slug)


def lab(cfg, t, slug):
    items = cfg.get("lab", [])
    w, h = WIDTH, 70 + len(items) * 52
    b = [window(0, 0, w, h, t, "build.queue  —  open-source work in progress", accent="cyan")]
    for i, it in enumerate(items):
        y = 62 + i * 52
        col = {"PLANNED": "muted", "BUILDING": "amber", "SHIPPED": "green"}.get(it["status"], "muted")
        m, cw = chip(20, y - 18, it["status"], t, size=12, color=col, border="border")
        b.append(m)
        b.append(txt(20 + cw + 16, y + 1, it["repo"], t, size=15, fill="green", weight=700))
        b.append(txt(20 + cw + 16, y + 22, fit(it["desc"], 13, w - cw - 60), t, size=13, fill="muted"))
    desc = "Build queue: " + "; ".join(f"{i['repo']} ({i['status'].lower()}): {i['desc']}" for i in items)
    return document(w, h, "Open-source build queue", desc, "".join(b), t, frame=False, slug=slug)


def activity(stats, t, slug):
    c = stats["metrics"]["contributions"]
    weeks = c["weeks"]
    cell, gap = 14, 3
    w, h = WIDTH, 60 + 7 * (cell + gap) + 40
    b = [window(0, 0, w, h, t, f"activity.log  —  {c['total']} contributions · {c['start']} → {c['end']}")]
    mx = max([v for wk in weeks for v in wk] + [1])
    ox = (w - len(weeks) * (cell + gap)) / 2
    for i, wk in enumerate(weeks):
        for d, v in enumerate(wk):
            lvl = 0 if v == 0 else min(4, 1 + int(3 * v / mx))
            b.append(rect(ox + i * (cell + gap), 48 + d * (cell + gap), cell, cell, t["heat"][lvl], rx=2))
    b.append(txt(ox, h - 14, "less", t, size=11, fill="muted"))
    for k in range(5):
        b.append(rect(ox + 36 + k * 16, h - 24, 12, 12, t["heat"][k], rx=2))
    b.append(txt(ox + 120, h - 14, "more  ·  source: GitHub GraphQL contributionCalendar", t, size=11, fill="muted"))
    return document(w, h, "Contribution activity", f"{c['total']} contributions between {c['start']} and {c['end']}.",
                    "".join(b), t, frame=False, slug=slug)


def interests(cfg, t, slug):
    items = cfg["interests"]["items"]
    w, h = WIDTH, 84 + len(items) * 30
    b = [window(0, 0, w, h, t, "htop — research.queue", accent="cyan")]
    b.append(rect(1, 38, w - 2, 26, t["green_soft"]))
    for x, lab_ in ((20, "PID"), (90, "PROCESS"), (420, "STATUS"), (560, "FOCUS")):
        b.append(txt(x, 56, lab_, t, size=12, fill="text", weight=700, spacing=1))
    css = ANIM_CSS + "@keyframes bar{0%,100%{transform:scaleX(1)}50%{transform:scaleX(.55)}}"
    for i, (proc, status) in enumerate(items):
        y = 90 + i * 30
        col = {"ACTIVE": "green", "EXPLORING": "amber", "LEARNING": "cyan"}.get(status, "muted")
        b.append(txt(20, y, str(1001 + i * 7), t, size=13, fill="dim"))
        b.append(txt(90, y, proc, t, size=14, fill="text"))
        b.append(txt(420, y, status, t, size=12, fill=col, weight=700, spacing=1))
        bw = 240 + (i * 53) % 150
        b.append(rect(560, y - 11, 380, 12, t["panel2"], t["border"], rx=2))
        b.append(rect(561, y - 10, bw, 10, t[col], rx=1,
                      extra=f' opacity="0.75" style="transform-origin:561px {y}px;animation:bar {3 + (i % 3)}s ease-in-out {i*0.3:.1f}s infinite"'))
    desc = "Engineering interests: " + ", ".join(f"{p} ({s.lower()})" for p, s in items) + "."
    return document(w, h, "Engineering interests", desc, "".join(b), t, css, frame=False, slug=slug)


def button(label, sub, ico, t, slug):
    w, h = 320, 64
    b = [rect(0.5, 0.5, w - 1, h - 1, t["panel"], t["border"], rx=8),
         rect(0.5, 0.5, 6, h - 1, t["green"], rx=2),
         icon(ico, 24, 20, 24, t["green"]),
         txt(64, 30, label, t, size=16, fill="text", weight=700, spacing=1.5),
         txt(64, 50, fit(sub, 12, w - 90), t, size=12, fill="muted"),
         txt(w - 18, 38, "↗", t, size=18, fill="amber", anchor="end")]
    return document(w, h, label, f"{label}: {sub}", "".join(b), t, frame=False, slug=slug)


def footer(cfg, t, slug):
    w, h = WIDTH, 96
    p = cfg["identity"]
    prompt = f"{p['prompt_user']}@{p['prompt_host']}"
    b = [f'<line x1="0" y1="10.5" x2="{w}" y2="10.5" stroke="{t["border"]}" stroke-dasharray="2 6"/>',
         txt(0, 44, prompt, t, size=15, fill="green", weight=700),
         txt(text_w(prompt, 15), 44, ":~$ exit", t, size=15, fill="muted"),
         txt(0, 72, cfg["footer"]["message"], t, size=14, fill="text"),
         rect(text_w(cfg["footer"]["message"], 14) + 8, 59, 9, 16, t["amber"], extra=' class="blink"'),
         txt(w, 72, "generated by python + github actions · no trackers", t, size=11, fill="dim", anchor="end")]
    return document(w, h, "Footer", cfg["footer"]["message"], "".join(b), t, ANIM_CSS, frame=False, slug=slug)


# ═════════════════════════════════════════════════════════════════════════════
#  Build
# ═════════════════════════════════════════════════════════════════════════════
SECTIONS = [("profile", "01", "SYSTEM PROFILE"), ("telemetry", "02", "TELEMETRY"),
            ("stack", "03", "STACK MODULES"), ("work", "04", "DEPLOYMENTS"),
            ("lab", "05", "BUILD QUEUE"), ("activity", "06", "ACTIVITY LOG"),
            ("interests", "07", "RESEARCH QUEUE"), ("contact", "08", "UPLINK")]


def active_sections(cfg, stats):
    """Sections actually rendered, numbered consecutively."""
    keys = [k for k, _, _ in SECTIONS
            if (k != "activity" or show_activity(cfg, stats)) and (k != "lab" or cfg.get("lab"))
            and (k != "work" or cfg.get("work"))]
    labels = {k: l for k, _, l in SECTIONS}
    return [(k, f"{i:02d}", labels[k]) for i, k in enumerate(keys, 1)]


def show_activity(cfg, stats) -> bool:
    c = ((stats or {}).get("metrics") or {}).get("contributions")
    return bool(c and c["total"] >= cfg["telemetry"]["show_contributions_min"])


def build_assets(cfg, stats) -> dict[str, str]:
    """Return {relative_path: svg_text} for both themes."""
    out = {}
    act = show_activity(cfg, stats)
    for theme, t in THEMES.items():
        def put(name, svg):
            out[f"assets/generated/{theme}/{name}.svg"] = svg
        s = lambda n: f"{n}-{theme}"  # unique ids per file
        put("hero", hero(cfg, t, s("hero")))
        put("terminal", terminal(cfg, t, s("term")))
        put("profile", profile(cfg, t, s("prof")))
        put("telemetry", telemetry(cfg, stats, t, s("tele")))
        put("stack", stack(cfg, t, s("stack")))
        for wk in cfg.get("work", []):
            put(f"work-{wk['id']}", work_card(wk, t, s(f"work-{wk['id']}")))
        if cfg.get("lab"):
            put("lab", lab(cfg, t, s("lab")))
        if act:
            put("activity", activity(stats, t, s("act")))
        put("interests", interests(cfg, t, s("int")))
        put("footer", footer(cfg, t, s("foot")))
        for key, num, label in active_sections(cfg, stats):
            put(f"h-{key}", section_header(num, label, t, s(f"h-{key}")))
        L = cfg["links"]
        put("btn-linkedin", button("LINKEDIN", "/in/nawsher-ali-saas-architect", "linkedin", t, s("bl")))
        put("btn-email", button("EMAIL", L["email"], "mail", t, s("be")))
        put("btn-github", button("GITHUB", f"@{cfg['identity']['handle']}", "github", t, s("bg")))
        if L.get("website"):
            put("btn-website", button("WEBSITE", L["website"].split("//")[-1].strip("/"), "", t, s("bw")))
    return out


def pic(name: str, alt: str, width: str | None = None) -> str:
    wa = f' width="{width}"' if width else ""
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/generated/dark/{name}.svg">'
            f'<source media="(prefers-color-scheme: light)" srcset="assets/generated/light/{name}.svg">'
            f'<img src="assets/generated/dark/{name}.svg" alt="{esc(alt)}"{wa}></picture>')


def build_readme(cfg, stats) -> str:
    idn, L = cfg["identity"], cfg["links"]
    act = show_activity(cfg, stats)
    secs = active_sections(cfg, stats)
    nav = [(k, label.split()[0]) for k, _, label in secs]
    navline = " ".join(f'<a href="#{k}"><kbd>{label}</kbd></a>' for k, label in nav)
    alt_hero = f"{idn['name']} — {idn['title']}: {idn['subtitle']}"
    o = []
    o.append("<!-- GENERATED FILE — edit data/profile.toml, then run scripts/generate_profile_svgs.py -->")
    o.append('<a name="top"></a>')
    o.append(f'<p align="center">{pic("hero", alt_hero)}</p>')
    o.append(f'<p align="center">{navline}</p>')
    o.append(f'<p align="center">{pic("terminal", "Terminal introduction: " + "; ".join(f"{c} → {r}" for c, r in cfg["terminal"]["lines"]))}</p>')

    def head(key):
        num, label = next((n, l) for k, n, l in secs if k == key)
        return f'<a name="{key}"></a>\n<p>{pic("h-" + key, f"{num} // {label}")}</p>'

    o.append(head("profile"))
    o.append(f'<p align="center">{pic("profile", "Engineering profile: what I build, problems I solve, career timeline")}</p>')
    o.append(f"> **{idn['title']}** with {idn['experience'].lower()} of production experience. I build the backend of "
             "multi-tenant SaaS platforms: the APIs, data model, access control and automation that keep large systems "
             "fast and safe to change. I have worked in Pakistan and remotely for an Australian startup.")
    o.append(head("telemetry"))
    o.append(f'<p align="center">{pic("telemetry", "Telemetry: career facts and live GitHub metrics")}</p>')
    o.append(head("stack"))
    o.append(f'<p align="center">{pic("stack", "Technology stack grouped by backend, frontend, data and infra, architecture, AI and automation, quality and ops")}</p>')
    if cfg.get("work"):
        o.append(head("work"))
        cards = " ".join(pic(f"work-{w['id']}", f"{w['name']}: {w['summary']}", width="49%") for w in cfg["work"])
        o.append(f'<p align="center">{cards}</p>')
        o.append("<sub>Employer systems are private. These cards summarise public CV facts only; no proprietary "
                 "code, architecture or data is published.</sub>")
    if cfg.get("lab"):
        o.append(head("lab"))
        o.append(f'<p align="center">{pic("lab", "Open-source build queue")}</p>')
    if act:
        o.append(head("activity"))
        o.append(f'<p align="center">{pic("activity", "Contribution activity heatmap")}</p>')
    o.append(head("interests"))
    o.append(f'<p align="center">{pic("interests", "Engineering interests")}</p>')
    o.append(head("contact"))
    btns = [(L["linkedin"], "btn-linkedin", "LinkedIn profile"),
            (f"mailto:{L['email']}", "btn-email", f"Email {L['email']}"),
            (L["github"], "btn-github", "GitHub profile")]
    if L.get("website"):
        btns.append((L["website"], "btn-website", "Website"))
    o.append('<p align="center">' + " ".join(f'<a href="{esc(u)}">{pic(n, a, width="32%")}</a>' for u, n, a in btns) + "</p>")
    o.append(f'<p align="center"><sub>{esc(idn["availability"])}</sub></p>')
    o.append(f'<p align="center">{pic("footer", cfg["footer"]["message"])}</p>')
    o.append('<p align="right"><a href="#top"><kbd>↑ TOP</kbd></a></p>')
    return "\n\n".join(o) + "\n"


def load():
    cfg = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    stats = json.loads(STATS.read_text(encoding="utf-8")) if STATS.exists() else {"status": "pending"}
    return cfg, stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    cfg, stats = load()
    files = build_assets(cfg, stats)
    files["README.md"] = build_readme(cfg, stats)

    changed = []
    for rel, content in sorted(files.items()):
        p = ROOT / rel
        if not p.exists() or p.read_text(encoding="utf-8") != content:
            changed.append(rel)
            if not args.check:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content, encoding="utf-8")
    # remove generated files that are no longer produced (e.g. activity below threshold)
    for p in sorted(GEN.rglob("*.svg")):
        rel = p.relative_to(ROOT).as_posix()
        if rel not in files:
            changed.append(rel + " (removed)")
            if not args.check:
                p.unlink()
    print(f"[generate] {len(files)} files, {len(changed)} changed")
    for c in changed:
        print(f"  ~ {c}")
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
