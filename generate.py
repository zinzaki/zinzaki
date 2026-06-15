#!/usr/bin/env python3
"""Profile generator.

Usage: python generate.py  ->  writes profile.svg

The layout is driven by config.yml; live data (metrics, streak, top repos) is
overlaid from stats.json, which the Update Stats workflow refreshes daily.
The whole profile is one panel rendered with foreignObject HTML/CSS — the only
way to style a GitHub README (no JS, no web fonts). Zones: identity, stack +
terminal, live metrics + streak, projects + focus, and a closing principle.
Contact links live as a clickable badge row in README.md (links inside an SVG
aren't clickable), so they are not rendered here.

Missing or renamed config keys fall back to defaults instead of failing the
build, so config.yml can be edited safely.
"""

import html
import json
import yaml
from pathlib import Path

CONFIG = Path("config.yml")
STATS = Path("stats.json")
W = 900
PADX = 52

DEFAULT_PALETTE = {
    "bg": "#0e0c09", "surface": "#15120d", "surface2": "#1c1812",
    "gold": "#c8a96e", "gold_dim": "#8a6f3e", "gold4": "#3a2e18",
    "text": "#ece2c6", "text_mid": "#bcae8c", "text_dim": "#8a7d62",
    "green": "#8fb37e", "amber": "#bf9a78",
}
DEFAULT_IDENTITY = {
    "username": "user", "display_nik": "user", "role": "",
    "jp_phrase": "", "jp_romaji": "", "principle_en": "", "principle_jp": "",
    "status": "online", "status_level": "on", "node": "01",
}


def load():
    """Read config.yml, fill in defaults, and overlay live data from stats.json."""
    with open(CONFIG, encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    cfg["palette"] = {**DEFAULT_PALETTE, **(cfg.get("palette") or {})}
    cfg["identity"] = {**DEFAULT_IDENTITY, **(cfg.get("identity") or {})}
    cfg.setdefault("stack", {})
    if STATS.exists():
        try:
            data = json.loads(STATS.read_text(encoding="utf-8"))
            if data.get("metrics"):
                cfg.setdefault("metrics", {}).update(data["metrics"])
            if data.get("streak"):
                cfg.setdefault("streak", {}).update(data["streak"])
            if "auto_projects" in data:
                cfg["auto_projects"] = data["auto_projects"]
            if data.get("activity"):   # real status derived daily from GH activity
                cfg["identity"]["status"] = data["activity"].get("label", cfg["identity"]["status"])
                cfg["identity"]["status_level"] = data["activity"].get("level", "on")
        except (ValueError, OSError):
            pass   # malformed stats.json → fall back to config defaults
    return cfg


def esc(s):
    return html.escape(str(s), quote=True)


def css_str(s):
    """Escape a string for a CSS `content:"..."` value that lives inside an SVG
    <style>. CSS escapes first (backslash, quote, newline -> \\A), then XML
    escapes (& < >) — the style block is XML character data, so a raw &/</> is
    invalid and breaks the whole SVG."""
    s = str(s).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\A ")
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


CSS = """
*{box-sizing:border-box;margin:0;padding:0;}
.root{color:%TEXT%;font-family:'Courier New',Courier,monospace;position:relative;overflow:hidden;
  background:radial-gradient(rgba(200,169,110,.02) 1px,transparent 1px) 0 0 / 26px 26px,%BG%;}
.root::after{content:'';position:absolute;inset:0;pointer-events:none;z-index:40;
  background:radial-gradient(150% 100% at 50% -20%,transparent 64%,rgba(0,0,0,.3));}

@keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes spinr{to{transform:rotate(-360deg)}}
@keyframes typ{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
@keyframes curin{0%{opacity:1}50%{opacity:0}100%{opacity:1}}
/* a soft, slow breath of light — not a neon glow */
@keyframes coremorph{0%,100%{transform:rotate(0) scale(1);opacity:.9}
  50%{transform:rotate(90deg) scale(.62);opacity:.6}}
@keyframes corepulse{0%,100%{opacity:.5}50%{opacity:.95}}

/* ── sharp skeleton: outer frame + corner brackets (the architectural grid) ── */
.frame{position:absolute;inset:14px;border:1px solid rgba(200,169,110,.1);pointer-events:none;z-index:3;}
.cnr{position:absolute;width:15px;height:15px;border:1.5px solid rgba(200,169,110,.65);z-index:4;}
.cnr.tl{top:10px;left:10px;border-right:0;border-bottom:0}
.cnr.tr{top:10px;right:10px;border-left:0;border-bottom:0}
.cnr.bl{bottom:10px;left:10px;border-right:0;border-top:0}
.cnr.br{bottom:10px;right:10px;border-left:0;border-top:0}

.kage{position:absolute;top:-18px;left:26px;z-index:1;font-size:205px;color:%GOLD%;opacity:.03;
  pointer-events:none;user-select:none;}

/* crystal sigil — sharp geometric jewel (kept, glow dimmed) */
.crystal{position:absolute;width:62px;height:62px;z-index:2;color:%GOLD%;}
.sig{width:62px;height:62px;overflow:visible;}
.sig .r{fill:none;stroke:currentColor;}
.sig .s1{transform-box:fill-box;transform-origin:center;animation:spin 40s linear infinite;opacity:.4;}
.sig .s2{transform-box:fill-box;transform-origin:center;animation:spinr 30s linear infinite;opacity:.6;}
.sig .s3{transform-box:fill-box;transform-origin:center;animation:spin 22s linear infinite;opacity:.8;}
.sig .s4{transform-box:fill-box;transform-origin:center;animation:spinr 22s linear infinite;opacity:.8;}
.sig .s5{transform-box:fill-box;transform-origin:center;animation:spin 15s linear infinite;opacity:.5;}
/* the scarlet heart of the sigil — the lily's memory; a bright catch-point up
   top that pairs with the bloom below (gold rings, scarlet core) */
.sig .score{transform-box:fill-box;transform-origin:center;fill:#BB3C33;stroke:none;
  filter:drop-shadow(0 0 5px rgba(187,60,51,.75));animation:coremorph 6s ease-in-out infinite;}
.sig .dot{fill:#D4665C;animation:corepulse 3s ease-in-out infinite;}

/* zones */
.zone{position:relative;z-index:5;padding:0 %PADX%px;}
.divln{border-top:1px solid rgba(200,169,110,.09);}
.zt{position:relative;display:flex;align-items:center;justify-content:space-between;
  font-size:12.5px;letter-spacing:.22em;color:rgba(214,189,140,.9);}
.zt.sub{font-size:11px;color:rgba(214,189,140,.66);}
/* sharp diamond marker — a skeleton accent, static */
.zt .mk{display:inline-block;width:7px;height:7px;background:%GOLD%;margin-right:13px;
  transform:rotate(45deg);box-shadow:0 0 5px rgba(200,169,110,.3);}
.zt .lbl{display:inline-flex;align-items:center;}
.zt .txt{position:relative;display:inline-block;}
.zt .d{color:%TEXT_DIM%;letter-spacing:.14em;font-size:11.5px;}
.cols{display:flex;}
.cR{border-left:1px solid rgba(200,169,110,.08);}

/* header */
.meta{position:absolute;font-size:10.5px;letter-spacing:.22em;color:rgba(210,184,135,.5);z-index:6;}
.meta.tl{top:34px;left:50px}.meta.tr{top:34px;right:50px;text-align:right}
.dot{display:inline-block;width:6px;height:6px;border-radius:50%;margin-right:7px;
  vertical-align:middle;background:%TEXT_DIM%;}
.dot.on{background:%GREEN%;box-shadow:0 0 5px rgba(143,172,111,.55);animation:pulse 2.8s ease-in-out infinite;}
.dot.mid{background:%AMBER%;}
.dot.off{background:%TEXT_DIM%;opacity:.55;}
.hz{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;height:100%;}
.jp{font-size:33px;letter-spacing:.42em;text-indent:.42em;color:%GOLD%;text-shadow:0 0 11px rgba(200,169,110,.2);}
.romaji{font-size:11.5px;letter-spacing:.36em;text-indent:.36em;color:%TEXT_DIM%;margin-top:13px;}
.nickslot{position:relative;width:760px;height:90px;margin-top:26px;
  display:flex;align-items:center;justify-content:center;}
.nick{position:absolute;font-size:29px;letter-spacing:.16em;color:#F7EED2;white-space:nowrap;}
.nick .ch{display:inline-block;animation:typ .3s ease backwards;}
.cur{display:inline-block;width:11px;height:25px;background:%GOLD%;vertical-align:-4px;margin-left:8px;
  border-radius:1px;opacity:0;animation:curin 1.1s step-end infinite;}
.quotes{position:absolute;max-width:730px;font-size:16px;line-height:1.5;letter-spacing:.04em;
  color:#e7dcc0;font-style:italic;text-align:center;opacity:0;}
.qt::after{content:"";white-space:pre-line;}
.role{font-size:13px;letter-spacing:.26em;text-indent:.26em;color:%TEXT_MID%;margin-top:22px;}

/* stack — sharp section accents, softly-rounded pills (the corner blend) */
.stackgrid{display:flex;flex-wrap:wrap;gap:19px 36px;}
.cat{flex:1 1 0;min-width:300px;}
.cl{font-size:10px;letter-spacing:.22em;text-transform:uppercase;color:%GOLD%;opacity:.78;
  margin-bottom:10px;padding-left:9px;border-left:2px solid %GOLD%;line-height:1.1;}
.tags{display:flex;flex-wrap:wrap;gap:7px;}
/* using → outlined (default); core → gold fill; learning → dashed + dim */
.tag{font-size:12.5px;color:%TEXT_MID%;border:1px solid rgba(200,169,110,.22);
  background:rgba(200,169,110,.03);padding:4px 11px;border-radius:6px;letter-spacing:.02em;line-height:1.5;}
.tag.core{color:%GOLD%;border-color:rgba(200,169,110,.55);background:rgba(200,169,110,.1);font-weight:bold;}
.tag.learning{color:%TEXT_DIM%;background:transparent;border-style:dashed;
  border-color:rgba(138,111,62,.45);}

/* streak — rounded card */
.streak{display:flex;align-items:center;gap:28px;margin-top:16px;padding:14px 18px;
  background:%SURFACE2%;border:1px solid rgba(200,169,110,.14);border-radius:9px;}
.skv{display:flex;flex-direction:column;}
.skn{font-size:24px;color:#F7EED2;line-height:1;}
.skn small{font-size:12px;color:%TEXT_DIM%;margin-left:3px;}
.skl{font-size:9.5px;letter-spacing:.2em;text-transform:uppercase;color:%TEXT_DIM%;margin-top:7px;}
.spark{display:flex;align-items:flex-end;gap:3px;height:38px;margin-left:auto;}
.spark .bar{width:7px;background:rgba(200,169,110,.3);border-radius:2px 2px 0 0;min-height:2px;}
.spark .bar.hot{background:%GOLD%;opacity:.85;}

/* vision terminal — rounded card */
.vterm{border:1px solid rgba(200,169,110,.14);background:rgba(0,0,0,.2);overflow:hidden;border-radius:9px;}
.vbar{display:flex;align-items:center;gap:6px;padding:8px 13px;border-bottom:1px solid rgba(200,169,110,.1);}
.vbar .wd{width:8px;height:8px;border-radius:50%;border:1px solid rgba(200,169,110,.4);}
.vbar .vbt{margin-left:8px;font-size:10.5px;letter-spacing:.12em;color:%TEXT_DIM%;}
/* fixed height + clip: the terminal types/clears WITHOUT reflowing the layout */
.vt{height:252px;overflow:hidden;padding:12px 14px;font-size:13px;line-height:1.95;color:%TEXT_MID%;}
.tw::after{content:"$ ▌";white-space:pre;}  /* static idle prompt; the animation overrides it */

/* metrics — rounded tiles with a small sharp corner accent (the blend, again) */
.mrow{display:flex;flex-wrap:wrap;gap:13px;margin-top:18px;}
.met{flex:1 1 40%;min-width:120px;position:relative;background:%SURFACE2%;
  border:1px solid rgba(200,169,110,.14);padding:18px 12px 15px;text-align:center;border-radius:9px;}
.met::before{content:'';position:absolute;top:9px;left:9px;width:9px;height:9px;
  border-top:1.5px solid rgba(200,169,110,.55);border-left:1.5px solid rgba(200,169,110,.55);}
.mv{display:block;font-size:31px;color:#F7EED2;line-height:1;}
.ml{display:block;font-size:10.5px;letter-spacing:.2em;text-transform:uppercase;color:%TEXT_DIM%;margin-top:11px;}

/* projects */
.pj{display:flex;flex-direction:column;padding:11px 0;border-bottom:1px solid rgba(200,169,110,.07);}
.pj:last-child{border-bottom:0;}
.pjh{display:flex;align-items:center;font-size:16px;}
.lamp{width:7px;height:7px;border-radius:50%;flex:none;margin-right:13px;}
.lamp.h3{background:%GREEN%;box-shadow:0 0 5px rgba(143,172,111,.45);}
.lamp.h2{background:%GOLD%;}
.lamp.h1{background:%GOLD_DIM%;}.lamp.h0{background:%TEXT_DIM%;}
.pjn{color:#F7EED2;letter-spacing:.02em;}
.pjlang{font-size:11.5px;color:%TEXT_DIM%;margin-left:12px;}
.pjs{margin-left:auto;font-size:12.5px;color:%GOLD%;opacity:.85;}
.pjd{font-size:13px;color:%TEXT_MID%;line-height:1.5;margin-top:5px;padding-left:20px;}
.empty{border:1px dashed rgba(200,169,110,.18);padding:22px;text-align:center;border-radius:8px;}
.el1{color:%TEXT_MID%;font-size:13.5px;letter-spacing:.04em;}
.el2{color:%TEXT_DIM%;font-size:11.5px;margin-top:8px;}

/* focus — sharp diamond bullets */
.nowln{font-size:13px;color:%GOLD%;margin-bottom:12px;}
.nowln b{color:%GOLD_DIM%;font-weight:normal;}
.fi{display:flex;align-items:baseline;font-size:13.5px;color:%TEXT_MID%;line-height:2.05;}
.fi .b{width:6px;height:6px;flex:none;background:%GOLD%;margin-right:13px;
  transform:translateY(-1px) rotate(45deg);}
.fhint{font-size:10.5px;color:%TEXT_DIM%;letter-spacing:.04em;margin-top:16px;}

/* closing block (folded into the main panel): contacts + principle */
.outro{text-align:center;}
.rule{display:flex;align-items:center;justify-content:center;width:340px;margin:0 auto;}
.rule .l{flex:1;height:1px;background:rgba(200,169,110,.16);}
/* the one scarlet bloom — Lycoris on the border line (rare trigger color) */
.lily{flex:none;margin:0 17px;width:30px;height:30px;line-height:0;}
.lily svg{width:30px;height:30px;overflow:visible;display:block;
  filter:drop-shadow(0 0 5px rgba(187,60,51,.5));}
.lily .st path{fill:none;stroke:#BB3C33;stroke-width:1.15;stroke-linecap:round;}
.lily .an circle{fill:#D4665C;}
.lily .core{fill:#BB3C33;}
.fj{font-size:17px;letter-spacing:.34em;text-indent:.34em;color:%GOLD%;margin-top:18px;text-shadow:0 0 10px rgba(200,169,110,.2);}
.fr{font-size:10.5px;letter-spacing:.3em;text-indent:.3em;color:%TEXT_DIM%;margin-top:11px;}

/* Respect the OS "reduce motion" setting: drop to a calm static banner —
   name visible, terminal idle, crystal still. Also lighter on weak machines. */
@media (prefers-reduced-motion: reduce){
  .tw::after,.qt::after,.nick,.quotes,.cur,.dot.on,
  .sig .s1,.sig .s2,.sig .s3,.sig .s4,.sig .s5,.sig .score,.sig .dot{
    animation:none !important;
  }
}
"""


def inject(css, pal):
    repl = {
        "%BG%": pal["bg"], "%SURFACE%": pal["surface"], "%SURFACE2%": pal["surface2"],
        "%GOLD%": pal["gold"], "%GOLD_DIM%": pal["gold_dim"], "%GOLD4%": pal["gold4"],
        "%TEXT%": pal["text"], "%TEXT_MID%": pal["text_mid"], "%TEXT_DIM%": pal["text_dim"],
        "%GREEN%": pal["green"], "%AMBER%": pal["amber"], "%PADX%": str(PADX),
    }
    for k, v in repl.items():
        css = css.replace(k, v)
    return css


def wrap(w, h, css, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img">\n'
        f'<foreignObject width="{w}" height="{h}">\n'
        f'<div xmlns="http://www.w3.org/1999/xhtml">\n'
        f'<style>{css}</style>\n'
        f'<div class="root" style="width:{w}px;height:{h}px;">\n{body}\n</div>\n'
        f'</div>\n</foreignObject>\n</svg>\n'
    )


def fmt(n):
    try:
        n = int(n)
    except (TypeError, ValueError):
        return str(n)
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def ztitle(label, right, sub=False):
    cls = "zt sub" if sub else "zt"
    rt = f'<span class="d">{right}</span>' if right else "<span></span>"
    return (f'<div class="{cls}">'
            f'<span class="lbl"><span class="mk"></span>'
            f'<span class="txt">{label}</span></span>{rt}</div>')


CRYSTAL = """<div class="crystal" style="top:84px;right:44px;">
  <svg class="sig" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
    <circle class="r s1" cx="50" cy="50" r="46" stroke-width="1" stroke-dasharray="3 7"/>
    <polygon class="r s2" points="50,8 86,29 86,71 50,92 14,71 14,29" stroke-width="1.1"/>
    <polygon class="r s3" points="50,18 82,70 18,70" stroke-width="1"/>
    <polygon class="r s4" points="50,82 82,30 18,30" stroke-width="1"/>
    <rect class="r s5" x="34" y="34" width="32" height="32" stroke-width="1"/>
    <polygon class="score" points="50,40 60,50 50,60 40,50"/>
    <circle class="dot" cx="50" cy="50" r="2.4"/>
  </svg></div>"""

# The one scarlet bloom (canon: rarity = power, one bloom per screen). A stylized
# Lycoris radiata — the spider lily that blooms on the border of worlds — set on
# the closing rule, the border of the card. Curved radial stamens + anther tips.
LYCORIS = """<span class="lily"><svg viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
  <g class="st">
    <path d="M24,24 Q19.5,12.9 24,4"/>
    <path d="M24,24 Q13.8,17.6 12.2,7.8"/>
    <path d="M24,24 Q12,24.8 5,17.8"/>
    <path d="M24,24 Q14.8,31.7 5,30.2"/>
    <path d="M24,24 Q21.1,35.6 12.2,40.2"/>
    <path d="M24,24 Q28.5,35.1 24,44"/>
    <path d="M24,24 Q34.2,30.4 35.8,40.2"/>
    <path d="M24,24 Q36,23.2 43,30.2"/>
    <path d="M24,24 Q33.2,16.3 43,17.8"/>
    <path d="M24,24 Q26.9,12.4 35.8,7.8"/>
  </g>
  <g class="an">
    <circle cx="24" cy="4" r="1.5"/><circle cx="12.2" cy="7.8" r="1.5"/>
    <circle cx="5" cy="17.8" r="1.5"/><circle cx="5" cy="30.2" r="1.5"/>
    <circle cx="12.2" cy="40.2" r="1.5"/><circle cx="24" cy="44" r="1.5"/>
    <circle cx="35.8" cy="40.2" r="1.5"/><circle cx="43" cy="30.2" r="1.5"/>
    <circle cx="43" cy="17.8" r="1.5"/><circle cx="35.8" cy="7.8" r="1.5"/>
  </g>
  <circle class="core" cx="24" cy="24" r="1.8"/>
</svg></span>"""


def terminal_css(vision):
    # Animating `content` is the heaviest thing on the page (each frame is a
    # full text repaint, no GPU). Keep the frame COUNT small: one char per
    # frame, short holds, and a clean cut instead of typing "clear".
    CARET = "▌"
    HOLD = 7                                              # frames an output rests before clearing
    frames = []

    def type_cmd(buf, cmd):                               # one character per frame
        base = buf + "$ "
        for k in range(1, len(cmd) + 1):
            frames.append(base + cmd[:k] + CARET)
        return base

    def clear_wave(buf):
        frames.extend([buf + "$ " + CARET] * HOLD)        # hold so the output is readable
        frames.extend(["$ " + CARET] * 2)                 # cut straight back to an empty prompt

    # ── fastfetch wave: logo (left) + info (right), aligned ──
    ff = vision.get("fastfetch")
    if ff:
        logo, info = ff.get("logo", []), ff.get("info", [])
        width = max((len(x) for x in logo), default=0)
        rows = max(len(logo), len(info))
        off = max(0, (len(info) - len(logo)) // 2)        # vertically centre the logo
        lines = []
        for i in range(rows):
            li = i - off
            lg = (logo[li] if 0 <= li < len(logo) else "").ljust(width)
            lines.append(lg + "   " + (info[i] if i < len(info) else ""))
        base = type_cmd("", "fastfetch")
        out_block = "".join("  " + ln + "\n" for ln in lines)
        buf = base + "fastfetch\n" + out_block
        frames.extend([buf + "$ " + CARET] * HOLD)        # hold so the output is readable
        clear_wave(buf)

    # ── ordinary command waves ──
    for wave in vision.get("waves", []):
        buf = ""
        for cmd, out in zip(wave[0::2], wave[1::2]):
            base = type_cmd(buf, cmd)
            out_block = "".join("  " + ln + "\n" for ln in str(out).split("\n"))
            buf = base + cmd + "\n" + out_block
            frames.extend([buf + "$ " + CARET] * HOLD)     # hold each command's output
        clear_wave(buf)

    n = len(frames) or 1
    parts = [f'{i * 100.0 / n:.3f}%{{content:"{css_str(fr)}"}}' for i, fr in enumerate(frames)]
    dur = max(18.0, n * 0.13)                              # slower = fewer content repaints / sec
    return ("@keyframes termw{" + "".join(parts) + "}"
            f".tw::after{{animation:termw {dur:.1f}s steps(1,end) infinite;}}")


def quotes_css(quotes, nick_hold=5.5, tr=0.7):
    """nick ↔ quotes crossfade cycle. Returns (css, total_seconds)."""
    if not quotes:
        return "", 0.0
    segs = []  # (dur, kind, content)
    for q in quotes:
        text = '"' + css_str("\n".join(str(l) for l in q)) + '"'
        chars = sum(len(str(l)) for l in q)
        qd = max(3.2, min(7.0, chars * 0.045 + 2.4))
        segs += [(nick_hold, "nick", '""'), (tr, "toq", text),
                 (qd, "quote", text), (tr, "ton", text)]
    T = sum(d for d, _, _ in segs)
    nf, qf, qc = [(0.0, 1)], [(0.0, 0)], [(0.0, '""')]
    t = 0.0
    for d, kind, content in segs:
        s, e = t / T * 100, (t + d) / T * 100
        if kind == "nick":
            nf.append((s, 1)); qf.append((s, 0)); qc.append((s, '""'))
        elif kind == "toq":
            nf += [(s, 1), (e, 0)]; qf += [(s, 0), (e, 1)]; qc.append((s, content))
        elif kind == "quote":
            nf.append((s, 0)); qf.append((s, 1))
        elif kind == "ton":
            nf += [(s, 0), (e, 1)]; qf += [(s, 1), (e, 0)]
        t += d
    nf.append((100.0, 1)); qf.append((100.0, 0)); qc.append((100.0, '""'))

    def kf(name, pairs, prop):
        seen = {}
        for p, v in pairs:
            seen[round(p, 3)] = v
        body = "".join(f"{p:.3f}%{{{prop}:{v}}}" for p, v in sorted(seen.items()))
        return f"@keyframes {name}{{{body}}}"

    css = (kf("nfade", nf, "opacity") + kf("qfade", qf, "opacity") + kf("qcontent", qc, "content")
           + f".nick{{animation:nfade {T:.1f}s ease infinite;}}"
           + f".quotes{{animation:qfade {T:.1f}s ease infinite;}}"
           + f".qt::after{{animation:qcontent {T:.1f}s steps(1,end) infinite;}}")
    return css, T


def nick_html(nick):
    out, d = [], 0.0
    for ch in nick:
        c = "&#160;" if ch == " " else esc(ch)
        out.append(f'<span class="ch" style="animation-delay:{d:.2f}s">{c}</span>')
        d += 0.12
    return "".join(out), d + 0.2   # caret appears after the last letter


def header_html(cfg):
    idn = cfg["identity"]
    h = 318
    nick, caret_d = nick_html(idn['display_nik'])
    return f"""<div class="zone" style="height:{h}px;">
  <div class="meta tl">UNIT — {esc(idn['username'].upper())}</div>
  <div class="meta tr">NODE {esc(idn['node'])} · <span class="dot {esc(idn.get('status_level','on'))}"></span>{esc(idn['status'].upper())}</div>
  {CRYSTAL}
  <div class="hz">
    <div class="jp">{esc(idn['jp_phrase'])}</div>
    <div class="romaji">{esc(idn['jp_romaji'])}</div>
    <div class="nickslot">
      <div class="nick">{nick}<span class="cur" style="animation-delay:{caret_d:.2f}s"></span></div>
      <div class="quotes"><span class="qt"></span></div>
    </div>
    <div class="role">{esc(idn.get('role',''))}</div>
  </div>
</div>""", h


def tag_cls(it):
    """Map a tag's status to its CSS class. Legacy `hi: true` → core."""
    status = (it.get("status") or ("core" if it.get("hi") else "using")).lower()
    return {"core": "tag core", "learning": "tag learning"}.get(status, "tag")


def stack_inner(cfg):
    cats = []
    for cat_name, items in cfg["stack"].items():
        tags = "".join(
            f'<span class="{tag_cls(it)}">{esc(it["name"])}</span>' for it in items)
        cats.append(f'<div class="cat"><div class="cl">{esc(cat_name)}</div>'
                    f'<div class="tags">{tags}</div></div>')
    rows = -(-len(cfg["stack"]) // 2) or 1          # two domains per row
    return f'<div class="stackgrid">{"".join(cats)}</div>', rows * 88


def streak_inner(cfg):
    """Current/longest streak + a 14-day contribution sparkline (self-hosted)."""
    s = cfg.get("streak", {}) or {}
    spark = s.get("spark") or [0]
    mx = max(spark) or 1
    bars = "".join(
        f'<span class="bar{" hot" if v >= mx * 0.66 else ""}" '
        f'style="height:{2 + round(v / mx * 36)}px"></span>'
        for v in spark)
    return (
        '<div class="streak">'
        f'<div class="skv"><span class="skn">{esc(s.get("current", 0))}<small>d</small></span>'
        '<span class="skl">current streak</span></div>'
        f'<div class="skv"><span class="skn">{esc(s.get("longest", 0))}<small>d</small></span>'
        '<span class="skl">longest</span></div>'
        f'<div class="spark">{bars}</div></div>')


def focus_inner(cfg):
    cur = (cfg.get("current") or "").strip()
    now = f'<div class="nowln"><b>now →</b> {esc(cur)}</div>' if cur else ""
    items = cfg.get("focus", []) or []
    fis = "".join(f'<div class="fi"><span class="b"></span>{esc(x)}</div>' for x in items)
    hint = '<div class="fhint">// shown in the work, not the words</div>'
    n = len(items) + (1 if cur else 0)
    return now + fis + hint, n * 30 + 30


def projects_inner(cfg):
    pcfg = cfg.get("projects") or {}
    mode = pcfg.get("mode", "auto")
    projs = (pcfg.get("pinned", []) if mode == "manual" else cfg.get("auto_projects", [])) or []
    projs = projs[:pcfg.get("max", 3)]
    if projs:
        rows = []
        for p in projs:
            heat = int(p.get("heat", 1))
            lang = f'<span class="pjlang">{esc(p["lang"])}</span>' if p.get("lang") else ""
            d = (p.get("desc") or "").strip()
            if len(d) > 48:                              # trim at a word, never mid-word
                d = d[:48].rsplit(" ", 1)[0].rstrip(" ·,—-:;.") + " …"
            desc = f'<div class="pjd">{esc(d)}</div>' if d else ""
            stars = int(p.get("stars", 0) or 0)
            star = f'<span class="pjs">★ {stars}</span>' if stars > 0 else ""
            rows.append(f'<div class="pj"><div class="pjh"><span class="lamp h{heat}"></span>'
                        f'<span class="pjn">{esc(p["name"])}</span>{lang}{star}</div>{desc}</div>')
        return "".join(rows), len(projs) * 76, len(projs)
    inner = ('<div class="empty"><div class="el1">// no public repositories yet</div>'
             '<div class="el2">building in silence — deployments will surface here</div></div>')
    return inner, 96, 0


def build_profile(cfg, pal):
    head, hh = header_html(cfg)
    SUB = 44
    idn = cfg['identity']
    user = esc(idn['username'])
    vshell = esc(f"{idn['username'].lower()}@{idn.get('host', 'nixos')}")

    # ── STACK: full-width grid of domains (two per row, reflows automatically) ──
    st_in, st_h = stack_inner(cfg)
    n = len(cfg["stack"])
    rstack_h = 70 + st_h + 22
    rstack = f"""<div class="zone divln" style="padding-top:22px;padding-bottom:24px;">
  {ztitle('STACK · INSTRUMENTS', f'{n} domains')}
  <div style="margin-top:18px;">{st_in}</div>
</div>"""

    # ── DATA: live metrics + streak (left) · vision terminal (right) ──
    m = cfg.get("metrics", {})
    tiles = [(fmt(m.get("commits", 0)), "commits · yr"), (fmt(m.get("repos", 0)), "repos"),
             (fmt(m.get("stars", 0)), "stars"), (fmt(m.get("followers", 0)), "followers")]
    th = "".join(f'<div class="met"><span class="mv">{esc(v)}</span><span class="ml">{esc(l)}</span></div>'
                 for v, l in tiles)
    sk_in = streak_inner(cfg)
    data_h = 70 + 262
    rdata = f"""<div class="zone divln" style="padding-top:22px;padding-bottom:26px;">
  {ztitle('METRICS · LIVE', f"github · {user}")}
  <div class="cols" style="margin-top:16px;">
    <div style="flex:1.18;padding-right:30px;">
      <div class="mrow" style="margin-top:0;">{th}</div>
      {sk_in}
    </div>
    <div class="cR" style="flex:1;padding-left:30px;">
      <div style="margin-bottom:12px;">{ztitle('VISION', '', sub=True)}</div>
      <div class="vterm">
        <div class="vbar"><span class="wd"></span><span class="wd"></span><span class="wd"></span><span class="vbt">{vshell}</span></div>
        <div class="vt"><span class="tw"></span></div>
      </div>
    </div>
  </div>
</div>"""

    pr_in, pr_h, pcnt = projects_inner(cfg)
    fc_in, fc_h = focus_inner(cfg)
    row3_h = 70 + max(pr_h, SUB + fc_h)
    row3 = f"""<div class="zone divln" style="padding-top:22px;padding-bottom:24px;">
  {ztitle('PROJECTS · TOP', f'{pcnt} shown')}
  <div class="cols" style="margin-top:14px;">
    <div style="flex:1.32;padding-right:34px;">{pr_in}</div>
    <div class="cR" style="flex:1;padding-left:34px;">
      <div style="margin-bottom:14px;">{ztitle('FOCUS', '', sub=True)}</div>
      {fc_in}
    </div>
  </div>
</div>"""

    # ── OUTRO: the principle, folded into the one panel. Contacts live only as
    # the clickable badge row in README (links inside an SVG aren't clickable). ──
    outro_h = 64 + 74
    outro = f"""<div class="zone divln outro" style="padding-top:30px;padding-bottom:34px;">
  <div class="rule"><span class="l"></span>{LYCORIS}<span class="l"></span></div>
  <div class="fj">{esc(idn['principle_jp'])}</div>
  <div class="fr">{esc(idn['principle_en'])}</div>
</div>"""

    # The per-zone heights above are heuristic estimates; they intentionally
    # overshoot so the last line always clears the bottom frame inset.
    SAFETY = 22
    total = hh + rstack_h + data_h + row3_h + outro_h + SAFETY
    qcss, _ = quotes_css(cfg.get("quotes", []))
    css = inject(CSS, pal) + terminal_css(cfg.get("vision", {})) + qcss
    body = ('<div class="kage">影</div>'
            '<div class="frame"></div>'
            '<div class="cnr tl"></div><div class="cnr tr"></div>'
            '<div class="cnr bl"></div><div class="cnr br"></div>\n'
            + head + rstack + rdata + row3 + outro)
    return wrap(W, total, css, body)


def main():
    cfg = load()
    pal = cfg["palette"]
    svg = build_profile(cfg, pal)
    Path("profile.svg").write_text(svg, encoding="utf-8")
    print(f"✓ profile.svg ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
