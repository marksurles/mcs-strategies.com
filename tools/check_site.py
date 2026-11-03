#!/usr/bin/env python3
"""Pre-publish gate for the static site. Run before every commit that touches pages.

Why: there is no build step, so nothing else catches a broken link, a leftover placeholder, a page
whose header drifted from the others, a private address leaking into public copy, or a privacy page
that no longer matches the app's Terms.swift (App Store review compares the two).

Usage: python3 tools/check_site.py   (exit 1 on any problem)
"""
from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
# Never shipped: repo docs and tooling. Only these paths are the public site.
SITE_EXCLUDE = {"docs", "tools", ".git", ".claude"}
BANNED = [r"\bTODO\b", r"\bTBD\b", r"lorem ipsum", r"\[verify", r"\bmark" + "@" + r"mcs-strategies",  # split so this public file holds no harvestable address
          r"MCS Software Strategies", r"XXX"]


class Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[str] = []
        self.ids: set[str] = set()
        self.meta: dict[str, str] = {}
        self.title = ""
        self._in_title = False
        self.imgs_missing_alt = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if a.get(k):
                self.refs.append(a[k])
        if tag == "img" and a.get("alt") is None:
            self.imgs_missing_alt += 1
        if tag == "meta" and a.get("name"):
            self.meta[a["name"]] = a.get("content", "")
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def site_pages(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.html")
                  if not (set(p.relative_to(root).parts) & SITE_EXCLUDE))


def resolve(root: Path, page: Path, ref: str) -> Path | None:
    """Local file a reference points at, or None for external/mailto/anchor-only refs."""
    u = urlparse(ref)
    if u.scheme or ref.startswith(("#", "//")):
        return None
    path = u.path
    target = (root / path.lstrip("/")) if path.startswith("/") else (page.parent / path)
    if path.endswith("/") or target.is_dir():
        target = target / "index.html"
    return target


def chrome(text: str) -> str:
    """Header + footer with the per-page aria-current marker removed, for drift comparison."""
    head = text[text.find('<header class="site-header">'):text.find("</header>")]
    foot = text[text.find('<footer class="site-footer">'):]
    return (head + foot).replace(' aria-current="page"', "")


def check(root: Path = ROOT, privacy_render=None) -> list[str]:
    problems: list[str] = []
    pages = site_pages(root)
    parsed: dict[Path, Page] = {}
    for p in pages:
        pg = Page()
        text = p.read_text()
        pg.feed(text)
        parsed[p] = pg
        rel = p.relative_to(root)
        if not pg.title.strip():
            problems.append(f"{rel}: missing <title>")
        if "description" not in pg.meta:
            problems.append(f"{rel}: missing meta description")
        if "viewport" not in pg.meta:
            problems.append(f"{rel}: missing meta viewport")
        if pg.imgs_missing_alt:
            problems.append(f"{rel}: {pg.imgs_missing_alt} <img> without alt")
        for pat in BANNED:
            if re.search(pat, text, re.I):
                problems.append(f"{rel}: banned text /{pat}/")
    for p, pg in parsed.items():
        for ref in pg.refs:
            target = resolve(root, p, ref)
            if target is None:
                continue
            if not target.exists():
                problems.append(f"{p.relative_to(root)}: broken link {ref}")
                continue
            frag = urlparse(ref).fragment
            if frag and target in parsed and frag not in parsed[target].ids:
                problems.append(f"{p.relative_to(root)}: missing anchor {ref}")
    chromes = {p: chrome(p.read_text()) for p in pages if '<header class="site-header">' in p.read_text()}
    if chromes:
        ref_page = root / "index.html"
        base = chromes.get(ref_page, next(iter(chromes.values())))
        for p, c in chromes.items():
            if c != base:
                problems.append(f"{p.relative_to(root)}: header/footer differs from index.html")
    if privacy_render is not None:
        privacy = root / "pillsheet" / "privacy.html"
        if not privacy.exists() or privacy.read_text() != privacy_render():
            problems.append("pillsheet/privacy.html is out of sync with Terms.swift "
                            "(run tools/build_privacy.py)")
    return problems


def main() -> int:
    sys.path.insert(0, str(Path(__file__).parent))
    import build_privacy
    problems = check(ROOT, build_privacy.render)
    for p in problems:
        print("FAIL", p)
    print(f"{len(site_pages(ROOT))} pages checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
