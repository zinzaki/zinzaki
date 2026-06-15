#!/usr/bin/env python3
"""Smoke test for the profile generator.

Run before committing a build (locally or in CI) so a broken or invalid SVG
never lands in the repo. Checks: config parses, the SVG is well-formed XML,
the key zones/elements are present, and config text containing & < > stays
valid (regression guard for the css_str escaping).

Usage: python3 test_generate.py   (exits non-zero on failure)
"""

import xml.dom.minidom as minidom

import generate


def check(svg, needles):
    minidom.parseString(svg)                       # well-formed XML, or raises
    missing = [n for n in needles if n not in svg]
    assert not missing, f"missing from SVG: {missing}"


def main():
    cfg = generate.load()
    svg = generate.build_profile(cfg, cfg["palette"])
    check(svg, [
        'class="frame"', 'class="crystal"', 'class="lily"', 'class="nick"',
        'class="tw"', 'STACK · INSTRUMENTS', 'METRICS · LIVE', 'PROJECTS · TOP',
        generate.esc(cfg["identity"]["role"]),
    ])

    # regression guard: a config value carrying & < > must not break the XML
    cfg["vision"] = {"waves": [["echo hazard", "a & b < c > d"]]}
    minidom.parseString(generate.build_profile(cfg, cfg["palette"]))

    print("✓ smoke test passed")


if __name__ == "__main__":
    main()
