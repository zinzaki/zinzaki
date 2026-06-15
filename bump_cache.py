#!/usr/bin/env python3
"""Refresh ?v= cache-busting tokens on this repo's self-hosted README images.

GitHub proxies README images through its camo cache, keyed by the image URL.
With a constant URL, camo keeps serving a stale image after the SVG is
regenerated — which is why the profile looked frozen. This derives each
token from the SVG's *content* hash, so the URL changes exactly when the
image changes: the cache busts on real updates, with zero churn when nothing
changed and nothing to bump by hand.

Run after generate.py (locally or in CI) and commit README.md with the SVGs.
"""

import hashlib
import re
from pathlib import Path

README = Path("README.md")
# README image filename -> local file whose content drives its token
TRACKED = {"profile.svg": "profile.svg"}


def token(path):
    p = Path(path)
    return hashlib.sha1(p.read_bytes()).hexdigest()[:8] if p.exists() else None


def main():
    tokens = {name: token(src) for name, src in TRACKED.items()}
    text = README.read_text(encoding="utf-8")

    def fix(m):
        url = m.group(0)
        name = next((n for n in tokens if f"/{n}" in url and tokens[n]), None)
        if not name:                          # not tracked (e.g. the snake) — leave as-is
            return url
        base = re.sub(r"\?v=[0-9a-fA-F]+", "", url)
        sep = "&" if "?" in base else "?"
        return f"{base}{sep}v={tokens[name]}"

    text = re.sub(r"https://raw\.githubusercontent\.com/\S+?\.svg(\?v=[0-9a-fA-F]+)?", fix, text)
    README.write_text(text, encoding="utf-8")
    print("cache tokens:", {k: v for k, v in tokens.items() if v})


if __name__ == "__main__":
    main()
