#!/usr/bin/env python3
"""Tests for the profile generator.

Run before committing a build (locally or in CI) so a broken or wrong-but-valid
SVG never lands in the repo. No test framework on purpose — one `python3
test_generate.py` is the whole contract, and CI needs nothing but pyyaml.

Covers: the real config renders; the SVG is well-formed XML; the key zones are
present; tag statuses map to the right classes; the measured-language strip
appears only when it says something; layout heights react to content; text
carrying & < > stays valid (the css_str escaping); and validate.py actually
catches the mistakes it claims to.

Usage: python3 test_generate.py   (exits non-zero on failure)
"""

import copy
import sys
import xml.dom.minidom as minidom
from pathlib import Path

import generate
import validate

FAILS = []


def case(fn):
    """Run one test, record the failure, keep going — one broken case should
    still report the others."""
    try:
        fn()
        print(f"  ✓ {fn.__name__}")
    except AssertionError as e:
        FAILS.append(f"{fn.__name__}: {e}")
        print(f"  ✗ {fn.__name__}: {e}")
    return fn


def parse(svg):
    minidom.parseString(svg)          # well-formed XML, or raises
    return svg


CFG = generate.load()


def render(cfg=None):
    cfg = cfg or CFG
    return parse(generate.build_profile(cfg, cfg["palette"]))


@case
def test_real_config_renders_every_zone():
    svg = render()
    for needle in ('class="frame"', 'class="crystal"', 'class="lily"', 'class="nick"',
                   'class="tw"', 'STACK · INSTRUMENTS', 'METRICS · LIVE', 'PROJECTS · TOP',
                   generate.esc(CFG["identity"]["role"])):
        assert needle in svg, f"missing {needle!r}"


@case
def test_svg_is_announced_to_screen_readers():
    svg = render()
    assert "<title id=" in svg and "<desc id=" in svg, "no accessible name"
    assert 'aria-labelledby="pt pd"' in svg, "title/desc not wired to the image role"
    title, desc = generate.a11y_label(CFG)
    assert CFG["identity"]["username"] in title, title
    assert "commits in the last year" in desc, desc


@case
def test_tag_status_maps_to_class():
    assert generate.tag_cls({"name": "x", "status": "core"}) == "tag core"
    assert generate.tag_cls({"name": "x", "status": "learning"}) == "tag learning"
    assert generate.tag_cls({"name": "x", "status": "planned"}) == "tag planned"
    assert generate.tag_cls({"name": "x", "status": "using"}) == "tag"
    assert generate.tag_cls({"name": "x"}) == "tag", "no status should mean `using`"
    assert generate.tag_cls({"name": "x", "hi": True}) == "tag core", "legacy `hi` lost"
    assert generate.tag_cls({"name": "x", "status": "nonsense"}) == "tag"


@case
def test_every_status_has_a_distinct_look():
    # Four tiers only help if they are visually different — a status whose CSS
    # class is missing renders as plain `using` and quietly overstates it.
    css = generate.CSS
    for cls in ("tag core", "tag learning", "tag planned"):
        assert f".{cls.replace(' ', '.')}{{" in css.replace("\n", ""), f"no CSS rule for {cls}"
    svg = render()
    for cls in ("tag core", "tag learning", "tag planned"):
        assert f'class="{cls}"' in svg, f"{cls} not used by the real config"


@case
def test_stack_height_follows_content():
    one = generate.cat_height([{"name": "Go"}])
    many = generate.cat_height([{"name": "n" * 20} for _ in range(6)])
    assert many > one * 2, f"a wrapping domain must reserve more rows ({one} -> {many})"
    # Synthetic stacks, not the live config — this asserts the reflow, and must
    # not start failing the day the real stack is trimmed.
    cfg = copy.deepcopy(CFG)
    cfg["stack"] = {"one": [{"name": "Go"}]}
    _, small = generate.stack_inner(cfg)
    cfg["stack"] = {f"d{i}": [{"name": "Go"}] for i in range(6)}
    _, tall = generate.stack_inner(cfg)
    assert tall > small, f"six domains must be taller than one ({small} -> {tall})"


@case
def test_language_strip_only_when_it_says_something():
    cfg = copy.deepcopy(CFG)
    cfg.pop("languages", None)
    assert generate.languages_inner(cfg) == ("", 0), "no data must render nothing"

    cfg["languages"] = [{"name": "Python", "pct": 100.0}]
    assert generate.languages_inner(cfg) == ("", 0), "a lone 100% bar states nothing"

    cfg["languages"] = [{"name": "Python", "pct": 60.0}, {"name": "Rust", "pct": 40.0}]
    html, h = generate.languages_inner(cfg)
    assert "Python" in html and "Rust" in html and h > 0

    cfg["measured"] = False
    assert generate.languages_inner(cfg) == ("", 0), "`measured: false` must hide it"


@case
def test_language_tail_folds_into_other():
    cfg = copy.deepcopy(CFG)
    cfg["languages"] = [{"name": f"L{i}", "pct": 10.0} for i in range(10)]
    html, _ = generate.languages_inner(cfg)
    assert "other</b> 60.0%" in html, "the tail past the ramp must sum into `other`"
    assert html.count("<span style=\"width:") == len(generate.LANG_RAMP)
    parse(generate.build_profile(cfg, cfg["palette"]))


@case
def test_stats_json_overlays_config():
    # Compared against stats.json itself, not against today's numbers — the
    # daily refresh must not turn this into a failing test every morning.
    import json
    live = json.loads(Path("stats.json").read_text(encoding="utf-8"))
    cfg = generate.load()
    assert cfg["metrics"]["commits"] == live["metrics"]["commits"], "metrics not applied"
    assert cfg["identity"]["status"] == live["activity"]["label"], "activity not applied"
    assert cfg["auto_projects"] == live["auto_projects"], "top repos not applied"


@case
def test_ampersands_in_config_stay_valid_xml():
    cfg = copy.deepcopy(CFG)
    hazard = "a & b < c > d \" e \\ f"
    cfg["vision"] = {"waves": [["echo hazard", hazard]]}
    cfg["quotes"] = [[hazard]]
    cfg["identity"]["role"] = hazard
    parse(generate.build_profile(cfg, cfg["palette"]))


@case
def test_reduced_motion_is_respected():
    assert "prefers-reduced-motion" in render(), "no calm fallback for reduced motion"


@case
def test_empty_projects_falls_back_to_a_message():
    cfg = copy.deepcopy(CFG)
    cfg["auto_projects"] = []
    inner, _, count = generate.projects_inner(cfg)
    assert count == 0 and "no public repositories yet" in inner


@case
def test_validator_catches_seeded_mistakes():
    cfg = copy.deepcopy(CFG)
    cfg["focuss"] = []                                              # unknown top-level key
    cfg["palette"]["gold"] = "goldenrod"                            # not a hex colour
    cfg["quotes"] = ["a bare string"]                               # not a list of lines
    cfg["vision"] = {"waves": [["cmd", "out", "orphan"]]}           # odd-length wave
    cfg["stack"] = {"d": [{"name": "Go", "stauts": "core"},         # misspelled key
                          {"name": "Rs", "status": "maining"}]}     # invalid status
    found = validate.check(cfg)
    for expect in ("focuss", "goldenrod", "bare string", "orphan", "stauts", "maining"):
        assert any(expect in w for w in found), f"validator missed {expect!r}: {found}"


@case
def test_validator_is_quiet_on_the_real_config():
    import yaml
    with open("config.yml", encoding="utf-8") as f:
        found = validate.check(yaml.safe_load(f))
    assert not found, f"config.yml has issues: {found}"


def main():
    print(f"{len(FAILS)} failure(s)" if FAILS else "✓ all tests passed")
    for f in FAILS:
        print(f"  {f}")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
