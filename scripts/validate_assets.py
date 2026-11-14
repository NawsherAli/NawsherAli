#!/usr/bin/env python3
"""Validate the profile before it is committed.

Checks
  1. Every SVG is well-formed XML, has role="img", <title> and <desc>.
  2. No scripts, event handlers, external resources or embedded rasters in SVGs.
  3. SVG size budget (keeps camo + mobile loading fast).
  4. Every image path referenced by README.md exists, and every generated
     SVG is referenced (no orphans).
  5. Every in-page link (#anchor) has a matching <a name="…">.
  6. No secrets anywhere in tracked text files.
  7. (optional, --online) external links respond.

Exit code 1 on any failure. Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG_NS = "{http://www.w3.org/2000/svg}"
MAX_SVG_BYTES = 60_000
SECRET_PATTERNS = [
    r"ghp_[A-Za-z0-9]{30,}", r"github_pat_[A-Za-z0-9_]{30,}", r"gh[ousr]_[A-Za-z0-9]{30,}",
    r"AKIA[0-9A-Z]{16}", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"xox[baprs]-[A-Za-z0-9-]{10,}",
    r"(?i)(password|passwd|secret|api_key)\s*[:=]\s*['\"][^'\"]{6,}['\"]",
]
TEXT_EXT = {".md", ".py", ".toml", ".json", ".yml", ".yaml", ".svg", ".txt"}


def check_svg(p: Path) -> list[str]:
    errs = []
    raw = p.read_text(encoding="utf-8")
    if len(raw.encode()) > MAX_SVG_BYTES:
        errs.append(f"{p}: {len(raw.encode())} bytes exceeds {MAX_SVG_BYTES}")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        return errs + [f"{p}: invalid XML ({e})"]
    if root.tag != f"{SVG_NS}svg":
        errs.append(f"{p}: root is not <svg>")
    if root.get("role") != "img":
        errs.append(f'{p}: missing role="img"')
    if root.find(f"{SVG_NS}title") is None or not (root.find(f"{SVG_NS}title").text or "").strip():
        errs.append(f"{p}: missing <title>")
    if root.find(f"{SVG_NS}desc") is None:
        errs.append(f"{p}: missing <desc>")
    for el in root.iter():
        tag = el.tag.replace(SVG_NS, "")
        if tag in ("script", "foreignObject", "image", "iframe"):
            errs.append(f"{p}: forbidden element <{tag}>")
        for k, v in el.attrib.items():
            if k.lower().startswith("on"):
                errs.append(f"{p}: event handler {k}")
            if "href" in k.lower() and not v.startswith("#"):
                errs.append(f"{p}: external reference {k}={v}")
    if re.search(r"@import|url\((?!#)", raw):
        errs.append(f"{p}: external CSS resource")
    return errs


def check_readme() -> list[str]:
    errs = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    refs = set(re.findall(r'(?:src|srcset)="([^"]+)"', readme))
    for r in sorted(refs):
        if r.startswith("http"):
            errs.append(f"README: remote image {r} (all images must be local)")
        elif not (ROOT / r).exists():
            errs.append(f"README: missing image {r}")
    for p in sorted((ROOT / "assets" / "generated").rglob("*.svg")):
        rel = p.relative_to(ROOT).as_posix()
        if rel not in refs:
            errs.append(f"orphan generated asset {rel}")
    anchors = set(re.findall(r'<a name="([^"]+)"', readme))
    for target in re.findall(r'href="#([^"]+)"', readme):
        if target not in anchors:
            errs.append(f"README: link to #{target} has no anchor")
    for img in re.findall(r"<img [^>]*>", readme):
        if 'alt="' not in img or 'alt=""' in img:
            errs.append(f"README: image without alt text: {img[:80]}")
    return errs


def check_secrets() -> list[str]:
    errs = []
    for p in ROOT.rglob("*"):
        if ".git" in p.parts or not p.is_file() or p.suffix not in TEXT_EXT:
            continue
        if p.name == "validate_assets.py":
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for pat in SECRET_PATTERNS:
            if re.search(pat, text):
                errs.append(f"possible secret in {p.relative_to(ROOT)} (pattern {pat})")
    return errs


def check_links_online() -> list[str]:
    warns = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for url in sorted(set(re.findall(r'href="(https?://[^"]+)"', readme))):
        try:
            req = urllib.request.Request(url, method="GET", headers={"User-Agent": "Mozilla/5.0 profile-validator"})
            with urllib.request.urlopen(req, timeout=15) as r:
                print(f"  link {r.status} {url}")
        except Exception as e:  # LinkedIn returns 999 to bots; report, don't fail
            warns.append(f"link check: {url} → {e}")
    return warns


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--online", action="store_true", help="also request external links")
    args = ap.parse_args(argv)
    svgs = sorted(ROOT.joinpath("assets").rglob("*.svg"))
    errs = [e for p in svgs if "brands" not in p.parts for e in check_svg(p)]
    errs += check_readme() + check_secrets()
    print(f"[validate] {len(svgs)} SVGs, README, secrets scanned")
    if args.online:
        for w in check_links_online():
            print(f"  WARN {w}")
    for e in errs:
        print(f"  FAIL {e}")
    print("[validate] OK" if not errs else f"[validate] {len(errs)} problem(s)")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
