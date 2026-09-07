#!/usr/bin/env python3
"""config.yml sanity checks.

generate.py deliberately falls back to defaults instead of crashing, which
keeps hand-edits safe but also means a typo (`stauts: core`, a quote written
as a bare string, an odd-length terminal wave) degrades *silently* — the
profile still builds, just wrong. This module says so out loud.

Every finding is a warning: `generate.py` prints them and carries on, while
CI runs `generate.py --strict`, which turns them into a failed build. Only
structurally impossible config (stack that isn't a mapping) raises here.

Usage: python3 validate.py   (exits non-zero if anything is off)
"""

import re

STATUSES = {"core", "using", "learning", "planned"}
HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

TOP_KEYS = {
    "identity", "focus", "current", "quotes", "vision", "stack",
    "projects", "auto_projects", "palette", "metrics", "streak", "measured",
}
IDENTITY_KEYS = {
    "username", "display_nik", "role", "principle_en", "principle_jp",
    "jp_phrase", "jp_romaji", "status", "status_level", "node", "host",
}
PALETTE_KEYS = {
    "bg", "surface", "surface2", "gold", "gold_dim", "gold4",
    "text", "text_mid", "text_dim", "green", "amber",
}
TAG_KEYS = {"name", "status", "hi"}
# fastfetch info rows beyond this get clipped: .vt is a fixed 252px box
FASTFETCH_MAX_INFO = 6


class ConfigError(Exception):
    """config.yml is shaped in a way generate.py cannot render at all."""


def _unknown(where, got, known):
    return [f"{where}: unknown key {k!r} — typo? (known: {', '.join(sorted(known))})"
            for k in sorted(set(got) - known)]


def _check_stack(stack):
    out = []
    if not isinstance(stack, dict):
        raise ConfigError(f"stack: expected a mapping of domain -> [tags], got {type(stack).__name__}")
    for domain, items in stack.items():
        if not isinstance(items, list):
            raise ConfigError(f"stack[{domain!r}]: expected a list of tags, got {type(items).__name__}")
        for i, it in enumerate(items):
            at = f"stack[{domain!r}][{i}]"
            if not isinstance(it, dict):
                out.append(f"{at}: expected {{ name: ..., status: ... }}, got {it!r}")
                continue
            if not str(it.get("name", "")).strip():
                out.append(f"{at}: missing a non-empty `name`")
            out += _unknown(at, it, TAG_KEYS)
            if "hi" in it:
                out.append(f"{at}: `hi` is the legacy spelling — use `status: core`")
            st = it.get("status")
            if st is not None and str(st).lower() not in STATUSES:
                out.append(f"{at}: status {st!r} is not one of {sorted(STATUSES)} "
                           f"— it will silently render as `using`")
    return out


def _check_quotes(quotes):
    out = []
    if quotes is None:
        return out
    if not isinstance(quotes, list):
        return [f"quotes: expected a list of quotes, got {type(quotes).__name__}"]
    for i, q in enumerate(quotes):
        if isinstance(q, str):
            out.append(f"quotes[{i}]: a bare string is rendered one character per line "
                       f"— wrap it in a list: [{q!r}]")
        elif not isinstance(q, list) or not q:
            out.append(f"quotes[{i}]: expected a non-empty list of lines, got {q!r}")
    return out


def _check_vision(vision):
    out = []
    if not isinstance(vision, dict):
        return [f"vision: expected a mapping, got {type(vision).__name__}"]
    ff = vision.get("fastfetch")
    if ff:
        if not isinstance(ff, dict):
            out.append(f"vision.fastfetch: expected a mapping, got {type(ff).__name__}")
        elif len(ff.get("info") or []) > FASTFETCH_MAX_INFO:
            out.append(f"vision.fastfetch.info: {len(ff['info'])} rows — anything past "
                       f"{FASTFETCH_MAX_INFO} is clipped by the terminal box")
    for i, wave in enumerate(vision.get("waves") or []):
        if not isinstance(wave, list) or not wave:
            out.append(f"vision.waves[{i}]: expected a flat [cmd, out, ...] list, got {wave!r}")
        elif len(wave) % 2:
            out.append(f"vision.waves[{i}]: has {len(wave)} entries — commands and outputs "
                       f"pair up, so the trailing {wave[-1]!r} is dropped")
    return out


def _check_projects(projects):
    out = []
    if not isinstance(projects, dict):
        return [f"projects: expected a mapping, got {type(projects).__name__}"]
    mode = projects.get("mode", "auto")
    if mode not in ("auto", "manual"):
        out.append(f"projects.mode: {mode!r} is not 'auto' or 'manual' — treated as 'manual'")
    mx = projects.get("max", 3)
    if not isinstance(mx, int) or mx < 1:
        out.append(f"projects.max: expected a positive integer, got {mx!r}")
    if mode == "manual" and not (projects.get("pinned") or []):
        out.append("projects.mode is 'manual' but `pinned` is empty — the panel will read as empty")
    return out


def check(cfg):
    """Return a list of human-readable warnings. Raises ConfigError only on
    config that cannot be rendered at all."""
    if not isinstance(cfg, dict):
        raise ConfigError(f"config.yml: expected a mapping at the top level, got {type(cfg).__name__}")

    out = _unknown("config.yml", cfg, TOP_KEYS)
    out += _unknown("identity", cfg.get("identity") or {}, IDENTITY_KEYS)
    out += _unknown("palette", cfg.get("palette") or {}, PALETTE_KEYS)

    for k, v in (cfg.get("palette") or {}).items():
        if isinstance(v, str) and not HEX.match(v.strip()):
            out.append(f"palette.{k}: {v!r} is not a #rrggbb colour — the CSS rule using it is dropped")

    out += _check_stack(cfg.get("stack") or {})
    out += _check_quotes(cfg.get("quotes"))
    out += _check_vision(cfg.get("vision") or {})
    out += _check_projects(cfg.get("projects") or {})

    for x in cfg.get("focus") or []:
        if not isinstance(x, str):
            out.append(f"focus: expected plain strings, got {x!r}")

    if "measured" in cfg and not isinstance(cfg["measured"], bool):
        out.append(f"measured: expected true or false, got {cfg['measured']!r}")

    spark = (cfg.get("streak") or {}).get("spark")
    if spark is not None and (not isinstance(spark, list)
                              or not all(isinstance(v, (int, float)) for v in spark)):
        out.append(f"streak.spark: expected a list of numbers, got {spark!r}")

    return out


def main():
    import sys
    import yaml
    with open("config.yml", encoding="utf-8") as f:
        warnings = check(yaml.safe_load(f) or {})
    for w in warnings:
        print(f"! {w}")
    print(f"{'✗' if warnings else '✓'} config.yml: {len(warnings)} issue(s)")
    sys.exit(1 if warnings else 0)


if __name__ == "__main__":
    main()
