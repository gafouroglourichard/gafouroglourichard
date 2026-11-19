"""Generate the static animated SVGs for the GitHub profile README.

Writes:
  assets/header.svg        – banner with a looping "typing" role line
  assets/whoami.svg        – terminal window: ASCII monogram + neofetch-style card
  assets/orchestrator.svg  – live-looking 4MA multi-agent orchestrator

All motion is SMIL / CSS keyframes inside the SVG, because GitHub strips
<script> and inline CSS from READMEs but plays animations in <img> SVGs.

Run:  python scripts/make_art.py
Needs Pillow only for the ASCII monogram (pip install pillow).
"""
from __future__ import annotations

import math
import os
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

# Valorant-inspired palette
NAVY = "#0f1923"
PANEL = "#16222e"
LINE = "#2a3a4a"
RED = "#ff4655"
CREAM = "#ece8e1"
MUTED = "#8b97a5"
TEAL = "#17e8b0"
AMBER = "#ffb547"

MONO = "'JetBrains Mono','Cascadia Code','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
SANS = "'Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif"

STATIC = os.environ.get("STATIC") == "1"  # frozen frame for quick previews


def write(name: str, svg: str) -> None:
    (ASSETS / name).write_text(svg, encoding="utf-8")
    print(f"wrote assets/{name} ({len(svg) // 1024} KB)")


def fmt(x: float) -> str:
    return f"{x:.4f}".rstrip("0").rstrip(".") or "0"


# --------------------------------------------------------------------------
# 1. Header banner with typing roles
# --------------------------------------------------------------------------
NAME = "RICHARD GAFOUROGLOU"
ROLES = [
    "AI Engineer",
    "Forward Deployed Engineer",
    "Full-Stack AI Developer",
    "building 4MA \u2014 a 14-agent business OS",
]


def spin_cube(cx: float, cy: float, half: float = 30.0, frames: int = 72, secs: float = 9.0) -> str:
    """A flat-shaded 3D cube that turns forever (old-school game pickup).

    Pre-computes the projected faces for every frame and animates them with SMIL,
    because real 3D transforms don't survive inside a GitHub <img> SVG.
    """
    tilt = math.radians(-28)
    light = (-0.45, -0.7, 0.55)
    ln = math.sqrt(sum(c * c for c in light))
    light = tuple(c / ln for c in light)
    base_dark, base_lit = (58, 15, 24), (255, 82, 99)

    verts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    faces = [  # vertex indices (ccw seen from outside) + outward normal
        ((0, 1, 3, 2), (-1, 0, 0)),
        ((4, 6, 7, 5), (1, 0, 0)),
        ((0, 4, 5, 1), (0, -1, 0)),
        ((2, 3, 7, 6), (0, 1, 0)),
        ((0, 2, 6, 4), (0, 0, -1)),
        ((1, 5, 7, 3), (0, 0, 1)),
    ]

    def rot(v, a):
        x, y, z = v
        ca, sa = math.cos(a), math.sin(a)
        x, z = x * ca + z * sa, -x * sa + z * ca  # yaw (around Y)
        ct, st = math.cos(tilt), math.sin(tilt)
        y, z = y * ct - z * st, y * st + z * ct  # pitch (around X)
        return x, y, z

    def hexc(c):
        return "#%02x%02x%02x" % tuple(int(round(v)) for v in c)

    series = [dict(pts=[], fill=[], op=[]) for _ in faces]
    for f in range(frames + 1):
        a = 2 * math.pi * f / frames + math.radians(30)
        proj = [rot(v, a) for v in verts]
        for i, (idx, n) in enumerate(faces):
            nx, ny, nz = rot(n, a)
            pts = " ".join(f"{cx + proj[k][0] * half:.1f},{cy + proj[k][1] * half:.1f}" for k in idx)
            b = max(0.0, nx * light[0] + ny * light[1] + nz * light[2])
            b = 0.18 + 0.82 * b
            col = tuple(base_dark[j] + (base_lit[j] - base_dark[j]) * b for j in range(3))
            series[i]["pts"].append(pts)
            series[i]["fill"].append(hexc(col))
            series[i]["op"].append("1" if nz > 0.02 else "0")

    parts = []
    for s in series:
        if STATIC:
            parts.append(
                f'<polygon points="{s["pts"][8]}" fill="{s["fill"][8]}" opacity="{s["op"][8]}" '
                f'stroke="{CREAM}" stroke-opacity=".55" stroke-width="1.2" stroke-linejoin="round"/>'
            )
            continue
        dur = f'dur="{secs}s" repeatCount="indefinite"'
        parts.append(
            f'<polygon points="{s["pts"][0]}" fill="{s["fill"][0]}" opacity="{s["op"][0]}" '
            f'stroke="{CREAM}" stroke-opacity=".55" stroke-width="1.2" stroke-linejoin="round">'
            f'<animate attributeName="points" values="{";".join(s["pts"])}" {dur}/>'
            f'<animate attributeName="fill" values="{";".join(s["fill"])}" {dur}/>'
            f'<animate attributeName="opacity" values="{";".join(s["op"])}" calcMode="discrete" {dur}/>'
            f"</polygon>"
        )

    bob = (
        ""
        if STATIC
        else '<animateTransform attributeName="transform" type="translate" values="0 0;0 -6;0 0" dur="2.6s" repeatCount="indefinite"/>'
    )
    shadow_anim = (
        ""
        if STATIC
        else '<animate attributeName="rx" values="30;22;30" dur="2.6s" repeatCount="indefinite"/>'
        '<animate attributeName="opacity" values=".35;.18;.35" dur="2.6s" repeatCount="indefinite"/>'
    )
    return (
        f'<g>'
        f'<circle cx="{cx}" cy="{cy}" r="64" fill="{RED}" opacity=".07"/>'
        f'<ellipse cx="{cx}" cy="{cy + half * 1.75:.0f}" rx="30" ry="6" fill="#000" opacity=".35">{shadow_anim}</ellipse>'
        f'<g>{bob}{"".join(parts)}</g>'
        f'</g>'
    )


def make_header() -> None:
    W, H = 860, 230
    fs = 22
    cw = fs * 0.6  # monospace advance width
    x0 = 40 + 2 * cw  # role text starts after "> "
    slot = 4.0
    total = slot * len(ROLES)

    clips, texts = [], []
    cur_t, cur_x = [0.0], [x0]
    for i, role in enumerate(ROLES):
        w = len(role) * cw + 2
        t0 = i * slot
        type_end = t0 + min(1.6, 0.06 * len(role) + 0.3)
        hold_end = t0 + 3.3
        erase_end = t0 + 3.7
        times = [0.0, t0, type_end, hold_end, erase_end, total]
        vals = [0, 0, w, w, 0, 0]
        kt, kv = [], []
        for t, v in zip(times, vals):
            if kt and abs(t - kt[-1]) < 1e-9:
                kv[-1] = v
                continue
            kt.append(t)
            kv.append(v)
        key_times = ";".join(fmt(t / total) for t in kt)
        values = ";".join(fmt(v) for v in kv)
        anim = (
            ""
            if STATIC
            else f'<animate attributeName="width" dur="{total}s" repeatCount="indefinite" '
            f'keyTimes="{key_times}" values="{values}"/>'
        )
        init_w = w if (STATIC and i == 0) else 0
        clips.append(
            f'<clipPath id="role{i}"><rect x="{fmt(x0 - 1)}" y="140" height="32" width="{fmt(init_w)}">{anim}</rect></clipPath>'
        )
        texts.append(
            f'<text clip-path="url(#role{i})" x="{fmt(x0)}" y="163" class="role">{escape(role)}</text>'
        )
        # cursor path
        for t, x in ((t0, x0), (type_end, x0 + w), (hold_end, x0 + w), (erase_end, x0)):
            if abs(t - cur_t[-1]) < 1e-9:
                cur_x[-1] = x
            else:
                cur_t.append(t)
                cur_x.append(x)
    if cur_t[-1] < total:
        cur_t.append(total)
        cur_x.append(x0)
    cursor_anim = (
        ""
        if STATIC
        else f'<animate attributeName="x" dur="{total}s" repeatCount="indefinite" '
        f'keyTimes="{";".join(fmt(t / total) for t in cur_t)}" values="{";".join(fmt(x) for x in cur_x)}"/>'
        '<animate attributeName="opacity" dur="0.9s" repeatCount="indefinite" values="1;1;0;0" keyTimes="0;0.5;0.55;1"/>'
    )

    anim_css = "" if STATIC else """
    .in{opacity:0;animation:rise .7s cubic-bezier(.2,.8,.2,1) forwards}
    .d1{animation-delay:.1s}.d2{animation-delay:.35s}.d3{animation-delay:.6s}.d4{animation-delay:.85s}
    @keyframes rise{from{opacity:0;transform:translateX(-14px)}to{opacity:1;transform:none}}
    .glitch{opacity:0;animation:glitch 6s steps(1) 1.2s infinite}
    @keyframes glitch{0%{opacity:.85;transform:translate(3px,-1px)}3%{opacity:.6;transform:translate(-3px,1px)}6%{opacity:0}100%{opacity:0}}
    .spin{transform-origin:770px 112px;animation:spin 14s linear infinite}
    .spin2{transform-origin:770px 112px;animation:spin 9s linear infinite reverse}
    @keyframes spin{to{transform:rotate(360deg)}}
    .pulse{animation:pulse 1.6s ease-in-out infinite}
    @keyframes pulse{50%{opacity:.25}}
    .scan{animation:scan 5s linear infinite}
    @keyframes scan{from{transform:translateY(-40px)}to{transform:translateY(240px)}}
    """

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Richard — {escape(' / '.join(ROLES[:3]))}">
  <title>Richard — AI Engineer</title>
  <defs>
    <pattern id="grid" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M22 0H0V22" fill="none" stroke="#ffffff" stroke-opacity=".035"/></pattern>
    <linearGradient id="fadeR" x1="0" x2="1"><stop offset="0" stop-color="{NAVY}" stop-opacity="0"/><stop offset="1" stop-color="{RED}" stop-opacity=".10"/></linearGradient>
    <linearGradient id="scanG" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{RED}" stop-opacity="0"/><stop offset="1" stop-color="{RED}" stop-opacity=".07"/></linearGradient>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="10"/></clipPath>
    {''.join(clips)}
  </defs>
  <style>
    .name{{font:800 44px {SANS};letter-spacing:3px;fill:{CREAM}}}
    .tag{{font:600 12px {MONO};letter-spacing:3px;fill:{RED}}}
    .role{{font:500 {fs}px {MONO};fill:{CREAM}}}
    .pfx{{font:700 {fs}px {MONO};fill:{RED}}}
    .meta{{font:500 12px {MONO};letter-spacing:1.5px;fill:{MUTED}}}
    .ok{{font:700 11px {MONO};letter-spacing:2px;fill:{TEAL}}}
    {anim_css}
  </style>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="{NAVY}"/>
    <rect width="{W}" height="{H}" fill="url(#grid)"/>
    <rect x="430" width="430" height="{H}" fill="url(#fadeR)"/>
    <rect class="scan" width="{W}" height="40" fill="url(#scanG)"/>
    <polygon points="0,28 12,16 12,{H - 16} 0,{H - 28}" fill="{RED}"/>
    <rect x="0" y="{H - 3}" width="{W}" height="3" fill="{RED}" opacity=".85"/>

    <text x="40" y="54" class="tag in d1">▸ PROFILE // GAFOUROGLOURICHARD</text>
    <text x="40" y="110" class="name glitch" fill="{RED}" style="fill:{RED}">{NAME}</text>
    <text x="40" y="110" class="name in d2">{NAME}</text>
    <rect x="40" y="124" width="64" height="3" fill="{RED}" class="in d3"/>

    <text x="40" y="163" class="pfx">&gt;</text>
    {''.join(texts)}
    <rect y="146" width="11" height="22" fill="{RED}" x="{fmt(x0)}">{cursor_anim}</rect>

    <g class="in d4">
      <circle cx="46" cy="201" r="4.5" fill="{TEAL}" class="pulse"/>
      <text x="58" y="205" class="ok">OPEN TO WORK · REMOTE / HYBRID</text>
      <text x="{W - 40}" y="205" text-anchor="end" class="meta">HU · EN · DE · GR</text>
    </g>

    {spin_cube(770, 112)}
  </g>
</svg>
"""
    write("header.svg", svg)


# --------------------------------------------------------------------------
# 2. whoami terminal card: ASCII monogram + neofetch info
# --------------------------------------------------------------------------
INFO = [
    ("", "richard@github"),
    ("", "--------------"),
    ("Role", "AI Engineer @ ZERO GROUP · Full-Stack · FDE"),
    ("Motto", "AI prepares. Humans decide."),
    ("Now", "4MA OS — 14 agents live in production"),
    ("Prev", "ManagAI — business-management SaaS, sold 2025"),
    ("Prev", "gbutor.hu — own online store, 2019–2021"),
    ("Stack", "Python · TypeScript · Go · Next.js · Supabase"),
    ("Infra", "Docker · Kubernetes · Vercel · AWS/Azure/GCP"),
    ("LLMs", "Claude · DeepSeek · OpenRouter · Ollama/Qwen"),
    ("Learning", "Rust · Angular · cloud AI certs"),
    ("Langs", "Hungarian · English · German · Greek"),
    ("Base", "Debrecen, HU — remote / 1 day in Budapest"),
]
RAMP = " .:-=+*#%@"


def ascii_monogram(cols: int = 34, rows: int = 18) -> list[str]:
    """Rasterise a diamond emblem with an 'R' inside and map it to ASCII."""
    from PIL import Image, ImageDraw, ImageFont

    S = 12  # supersample
    W, H = cols * S, int(rows * S * 2.0)  # chars are ~2x taller than wide
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    cx, cy = W / 2, H / 2
    r = min(W, H) / 2 - 4
    outer = [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]
    inner_r = r * 0.84
    inner = [(cx, cy - inner_r), (cx + inner_r, cy), (cx, cy + inner_r), (cx - inner_r, cy)]
    d.polygon(outer, fill=255)
    d.polygon(inner, fill=35)
    font = None
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/Library/Fonts/Arial Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ):
        if os.path.exists(path):
            font = ImageFont.truetype(path, int(r * 1.35))
            break
    font = font or ImageFont.load_default()
    bbox = d.textbbox((0, 0), "R", font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]), "R", fill=255, font=font)
    small = img.resize((cols, rows), Image.LANCZOS)
    px = small.load()
    out = []
    for y in range(rows):
        line = "".join(RAMP[min(len(RAMP) - 1, px[x, y] * len(RAMP) // 256)] for x in range(cols))
        out.append(line.rstrip())
    return out


def make_whoami() -> None:
    W, H = 860, 400
    fs, lh = 13, 19
    cw = fs * 0.6
    art = ascii_monogram()
    art_x, art_y = 36, 74
    art_lh = 16

    rows = []
    for i, line in enumerate(art):
        y = art_y + i * art_lh
        w = len(line) * cw + 4
        begin = 0.25 + i * 0.07
        anim = (
            ""
            if STATIC
            else f'<animate attributeName="width" from="0" to="{fmt(w)}" begin="{fmt(begin)}s" dur=".35s" fill="freeze"/>'
        )
        rows.append(
            f'<clipPath id="a{i}"><rect x="{art_x - 2}" y="{y - 13}" height="{art_lh}" width="{fmt(w) if STATIC else 0}">{anim}</rect></clipPath>'
            f'<text clip-path="url(#a{i})" x="{art_x}" y="{y}" class="art">{escape(line)}</text>'
        )

    info_x = 330
    key_w = 10
    lines = []
    for i, (k, v) in enumerate(INFO):
        y = 80 + i * lh
        delay = 0.6 + i * 0.12
        style = "" if STATIC else f' style="animation-delay:{delay:.2f}s"'
        if i == 0:
            body = f'<tspan class="hl">richard</tspan><tspan class="v">@</tspan><tspan class="hl">github</tspan>'
        elif i == 1:
            body = f'<tspan class="v">{escape(v)}</tspan>'
        else:
            body = f'<tspan class="k">{escape(k)}</tspan><tspan class="v" x="{fmt(info_x + key_w * cw)}">{escape(v)}</tspan>'
        lines.append(f'<text x="{info_x}" y="{y}" class="ln"{style}>{body}</text>')

    sw_y = 80 + len(INFO) * lh + 6
    swatches = []
    for j, c in enumerate([NAVY, LINE, MUTED, CREAM, RED, "#bd3944", TEAL, AMBER]):
        style = "" if STATIC else f' style="animation-delay:{0.6 + len(INFO) * 0.12 + j * 0.05:.2f}s"'
        swatches.append(f'<rect class="ln" x="{info_x + j * 26}" y="{sw_y}" width="22" height="12" fill="{c}" stroke="{LINE}"{style}/>')

    prompt_y = H - 22
    anim_css = "" if STATIC else """
    .ln{opacity:0;animation:fadein .45s ease-out forwards}
    @keyframes fadein{from{opacity:0;transform:translateX(8px)}to{opacity:1;transform:none}}
    .blink{animation:blink 1s steps(1) infinite}
    @keyframes blink{50%{opacity:0}}
    """

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="whoami: Richard, AI Engineer">
  <title>whoami</title>
  <defs>{''.join(r.split('<text')[0] for r in rows)}</defs>
  <style>
    .art{{font:700 {fs}px {MONO};fill:{RED};white-space:pre}}
    .ln{{font:500 {fs}px {MONO};white-space:pre}}
    .k{{fill:{RED};font-weight:700}}
    .v{{fill:{CREAM}}}
    .hl{{fill:{RED};font-weight:700}}
    .ttl{{font:600 12px {MONO};fill:{MUTED};letter-spacing:1px}}
    .pr{{font:600 {fs}px {MONO};fill:{TEAL}}}
    {anim_css}
  </style>
  <rect width="{W}" height="{H}" rx="10" fill="{NAVY}" stroke="{LINE}"/>
  <path d="M0 10a10 10 0 0 1 10-10h{W - 20}a10 10 0 0 1 10 10v24H0z" fill="{PANEL}"/>
  <rect x="16" y="12" width="10" height="10" fill="{RED}"/>
  <rect x="32" y="12" width="10" height="10" fill="{AMBER}"/>
  <rect x="48" y="12" width="10" height="10" fill="{TEAL}"/>
  <text x="{W / 2}" y="22" text-anchor="middle" class="ttl">richard@4ma: ~ — whoami</text>
  <line x1="0" y1="34" x2="{W}" y2="34" stroke="{LINE}"/>
  <text x="{art_x}" y="56" class="pr">$ neofetch --ascii richard</text>
  {''.join('<text' + r.split('<text', 1)[1] for r in rows)}
  {''.join(lines)}
  {''.join(swatches)}
  <text x="{art_x}" y="{prompt_y}" class="pr">richard@github ~ $ <tspan fill="{CREAM}">./ship --next</tspan></text>
  <rect x="{art_x + len('richard@github ~ $ ./ship --next') * cw + 4}" y="{prompt_y - 12}" width="8" height="15" fill="{RED}" class="blink"/>
</svg>
"""
    write("whoami.svg", svg)


# --------------------------------------------------------------------------
# 3. 4MA orchestrator – hub + 8 agents with flowing cables
# --------------------------------------------------------------------------
AGENTS = ["SALES", "MARKETING", "SUPPORT", "FINANCE", "OPERATIONS", "DOCUMENTS", "COMPLIANCE", "QA · CRITIC"]
STEPS = ["INTAKE", "PLAN", "EXECUTE", "REVIEW", "DONE"]


def make_orchestrator() -> None:
    W, H = 860, 470
    cx, cy = 430, 210
    rx, ry = 320, 140
    cycle = 8.0

    cables, packets, nodes, defs = [], [], [], []
    for i, name in enumerate(AGENTS):
        ang = -math.pi / 2 + i * 2 * math.pi / len(AGENTS)
        ax, ay = cx + rx * math.cos(ang), cy + ry * math.sin(ang)
        # gentle curve: control point pushed sideways
        mx, my = (cx + ax) / 2, (cy + ay) / 2
        nx, ny = -(ay - cy), (ax - cx)
        nl = math.hypot(nx, ny) or 1
        bend = 22 if i % 2 else -22
        qx, qy = mx + nx / nl * bend, my + ny / nl * bend
        pid = f"p{i}"
        d = f"M{fmt(cx)} {fmt(cy)} Q{fmt(qx)} {fmt(qy)} {fmt(ax)} {fmt(ay)}"
        defs.append(f'<path id="{pid}" d="{d}"/>')
        flow = "" if STATIC else f'<animate attributeName="stroke-dashoffset" from="0" to="-24" dur="{1.1 + (i % 3) * 0.25:.2f}s" repeatCount="indefinite"/>'
        cables.append(f'<path d="{d}" fill="none" stroke="{LINE}" stroke-width="2"/>')
        cables.append(f'<path d="{d}" fill="none" stroke="{RED}" stroke-opacity=".55" stroke-width="1.6" stroke-dasharray="4 8">{flow}</path>')

        offset = i * cycle / len(AGENTS)
        if not STATIC:
            # task out (red) then result back (teal)
            packets.append(
                f'<circle r="4" fill="{RED}" opacity="0"><animateMotion dur="{cycle}s" begin="{fmt(offset)}s" repeatCount="indefinite" keyPoints="0;1;1" keyTimes="0;0.22;1" calcMode="linear"><mpath href="#{pid}"/></animateMotion>'
                f'<animate attributeName="opacity" dur="{cycle}s" begin="{fmt(offset)}s" repeatCount="indefinite" keyTimes="0;0.02;0.2;0.23;1" values="0;1;1;0;0"/></circle>'
            )
            packets.append(
                f'<circle r="4" fill="{TEAL}" opacity="0"><animateMotion dur="{cycle}s" begin="{fmt(offset)}s" repeatCount="indefinite" keyPoints="1;1;0;0" keyTimes="0;0.5;0.72;1" calcMode="linear"><mpath href="#{pid}"/></animateMotion>'
                f'<animate attributeName="opacity" dur="{cycle}s" begin="{fmt(offset)}s" repeatCount="indefinite" keyTimes="0;0.5;0.52;0.7;0.73;1" values="0;0;1;1;0;0"/></circle>'
            )

        # status: idle -> running (amber) -> done (teal) synced with packets
        status_anim = (
            ""
            if STATIC
            else f'<animate attributeName="fill" dur="{cycle}s" begin="{fmt(offset)}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;0.22;0.5;0.72" values="{MUTED};{AMBER};{TEAL};{MUTED}"/>'
        )
        glow_anim = (
            ""
            if STATIC
            else f'<animate attributeName="stroke-opacity" dur="{cycle}s" begin="{fmt(offset)}s" repeatCount="indefinite" keyTimes="0;0.22;0.3;0.5;1" values="0;0;.9;0;0"/>'
            f'<animate attributeName="r" dur="{cycle}s" begin="{fmt(offset)}s" repeatCount="indefinite" keyTimes="0;0.22;0.5;1" values="16;16;30;30"/>'
        )
        lbl_y = ay + 34 if ay >= cy - 5 else ay - 24
        nodes.append(
            f'<g><circle cx="{fmt(ax)}" cy="{fmt(ay)}" r="16" fill="none" stroke="{AMBER}" stroke-opacity="0" stroke-width="2">{glow_anim}</circle>'
            f'<rect x="{fmt(ax - 13)}" y="{fmt(ay - 13)}" width="26" height="26" transform="rotate(45 {fmt(ax)} {fmt(ay)})" fill="{PANEL}" stroke="{RED}" stroke-width="2"/>'
            f'<circle cx="{fmt(ax)}" cy="{fmt(ay)}" r="4.5" fill="{MUTED}">{status_anim}</circle>'
            f'<text x="{fmt(ax)}" y="{fmt(lbl_y)}" text-anchor="middle" class="agent">{escape(name)}</text></g>'
        )

    # workflow tracker along the bottom
    tr_y = H - 44
    seg_w = 150
    tr_x0 = (W - seg_w * (len(STEPS) - 1)) / 2
    tracker = [f'<line x1="{fmt(tr_x0)}" y1="{tr_y}" x2="{fmt(tr_x0 + seg_w * (len(STEPS) - 1))}" y2="{tr_y}" stroke="{LINE}" stroke-width="3"/>']
    prog_anim = "" if STATIC else f'<animate attributeName="x2" dur="{cycle}s" repeatCount="indefinite" values="{fmt(tr_x0)};{fmt(tr_x0 + seg_w * (len(STEPS) - 1))};{fmt(tr_x0 + seg_w * (len(STEPS) - 1))}" keyTimes="0;0.85;1"/>'
    tracker.append(f'<line x1="{fmt(tr_x0)}" y1="{tr_y}" x2="{fmt(tr_x0 if not STATIC else tr_x0 + seg_w * 2)}" y2="{tr_y}" stroke="{RED}" stroke-width="3">{prog_anim}</line>')
    for k, step in enumerate(STEPS):
        sx = tr_x0 + k * seg_w
        reach = 0.85 * k / (len(STEPS) - 1)
        fill_anim = (
            ""
            if STATIC
            else f'<animate attributeName="fill" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;{fmt(max(reach, 0.0001)) if k else 0}" values="{PANEL};{TEAL if k == len(STEPS) - 1 else RED}"/>'
        )
        if k == 0 and not STATIC:
            fill_anim = f'<animate attributeName="fill" dur="{cycle}s" repeatCount="indefinite" calcMode="discrete" keyTimes="0;0.98" values="{RED};{PANEL}"/>'
        tracker.append(
            f'<rect x="{fmt(sx - 6)}" y="{tr_y - 6}" width="12" height="12" transform="rotate(45 {fmt(sx)} {tr_y})" fill="{PANEL}" stroke="{RED}" stroke-width="2">{fill_anim}</rect>'
            f'<text x="{fmt(sx)}" y="{tr_y + 26}" text-anchor="middle" class="step">{step}</text>'
        )

    anim_css = "" if STATIC else f"""
    .core{{transform-origin:{cx}px {cy}px;animation:spin 18s linear infinite}}
    .core2{{transform-origin:{cx}px {cy}px;animation:spin 11s linear infinite reverse}}
    @keyframes spin{{to{{transform:rotate(360deg)}}}}
    .beat{{transform-origin:{cx}px {cy}px;animation:beat 2s ease-in-out infinite}}
    @keyframes beat{{50%{{transform:scale(1.07)}}}}
    .live{{animation:blink 1.2s steps(1) infinite}}
    @keyframes blink{{50%{{opacity:.2}}}}
    """

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="4MA orchestrator: a core routing tasks to 8 specialised agents">
  <title>4MA orchestrator</title>
  <defs>
    <pattern id="g2" width="22" height="22" patternUnits="userSpaceOnUse"><path d="M22 0H0V22" fill="none" stroke="#ffffff" stroke-opacity=".03"/></pattern>
    <radialGradient id="halo"><stop offset="0" stop-color="{RED}" stop-opacity=".35"/><stop offset="1" stop-color="{RED}" stop-opacity="0"/></radialGradient>
    {''.join(defs)}
  </defs>
  <style>
    .agent{{font:700 11px {MONO};letter-spacing:1.5px;fill:{CREAM}}}
    .step{{font:600 10px {MONO};letter-spacing:2px;fill:{MUTED}}}
    .hdr{{font:700 12px {MONO};letter-spacing:3px;fill:{CREAM}}}
    .sub{{font:500 11px {MONO};letter-spacing:1px;fill:{MUTED}}}
    .corelbl{{font:800 15px {SANS};letter-spacing:2px;fill:{CREAM}}}
    .coresub{{font:600 9px {MONO};letter-spacing:2px;fill:{RED}}}
    {anim_css}
  </style>
  <rect width="{W}" height="{H}" rx="10" fill="{NAVY}" stroke="{LINE}"/>
  <rect width="{W}" height="{H}" rx="10" fill="url(#g2)"/>
  <text x="24" y="32" class="hdr">4MA // ORCHESTRATOR CORE</text>
  <text x="24" y="50" class="sub">tasks out <tspan fill="{RED}">●</tspan>  results back <tspan fill="{TEAL}">●</tspan>  running <tspan fill="{AMBER}">●</tspan></text>
  <circle cx="{W - 70}" cy="28" r="5" fill="{RED}" class="live"/>
  <text x="{W - 58}" y="32" class="hdr" style="fill:{RED}">LIVE</text>

  <circle cx="{cx}" cy="{cy}" r="90" fill="url(#halo)"/>
  {''.join(cables)}
  {''.join(packets)}
  <g class="core"><rect x="{cx - 44}" y="{cy - 44}" width="88" height="88" transform="rotate(45 {cx} {cy})" fill="none" stroke="{RED}" stroke-width="1.5" stroke-dasharray="8 7"/></g>
  <g class="core2"><circle cx="{cx}" cy="{cy}" r="50" fill="none" stroke="{CREAM}" stroke-opacity=".35" stroke-dasharray="2 6"/></g>
  <g class="beat">
    <rect x="{cx - 32}" y="{cy - 32}" width="64" height="64" transform="rotate(45 {cx} {cy})" fill="{PANEL}" stroke="{RED}" stroke-width="2.5"/>
    <text x="{cx}" y="{cy + 3}" text-anchor="middle" class="corelbl">4MA</text>
    <text x="{cx}" y="{cy + 17}" text-anchor="middle" class="coresub">CORE</text>
  </g>
  {''.join(nodes)}
  {''.join(tracker)}
</svg>
"""
    write("orchestrator.svg", svg)


# --------------------------------------------------------------------------
# 4. Stat tiles (swing in, count up, shine) and link buttons
# --------------------------------------------------------------------------
TILES = [
    ("tile-agents.svg", 14, "", "AGENTS IN PRODUCTION", "4MA OS at ZERO GROUP", 0.2),
    ("tile-autonomy.svg", 95, "%", "ROUTINE TASKS AUTONOMOUS", "5% wait for a manager", 0.45),
    ("tile-leads.svg", 131, "", "LEADS SINCE AUTOMATION", "Marketing Intelligence", 0.7),
]


def make_tile(fname: str, value: int, suffix: str, label: str, sub: str, delay: float) -> None:
    W, H = 280, 150
    frames = 22
    count_start, count_dur = delay + 0.55, 1.1
    nums = []
    for k in range(frames + 1):
        p = k / frames
        v = round(value * (1 - (1 - p) ** 3))  # ease-out count
        t = count_start + p * count_dur
        if STATIC:
            if k == frames:
                nums.append(f'<text x="24" y="86" class="num">{v}<tspan class="suf">{suffix}</tspan></text>')
            continue
        timing = f'begin="{t:.3f}s"' + ("" if k == frames else f' dur="{count_dur / frames + 0.001:.3f}s"')
        nums.append(
            f'<text x="24" y="86" class="num" visibility="hidden">{v}<tspan class="suf">{suffix}</tspan>'
            f'<set attributeName="visibility" to="visible" {timing}/></text>'
        )
    anim_css = "" if STATIC else f"""
    .card{{opacity:0;transform-origin:20px 150px;animation:swing .9s cubic-bezier(.2,1.5,.4,1) {delay}s forwards}}
    @keyframes swing{{0%{{opacity:0;transform:translateY(46px) rotate(-7deg)}}60%{{opacity:1}}100%{{opacity:1;transform:none}}}}
    .shine{{animation:shine 5s ease-in-out {delay + 2:.2f}s infinite}}
    @keyframes shine{{0%{{transform:translateX(-160px)}}30%,100%{{transform:translateX(440px)}}}}
    .ring{{transform-origin:263px 15px;animation:ring 2.4s ease-out {delay + 1:.2f}s infinite}}
    @keyframes ring{{0%{{transform:scale(.3);opacity:.9}}100%{{transform:scale(2.2);opacity:0}}}}
    .arrow{{animation:nudge 1.8s ease-in-out infinite}}
    @keyframes nudge{{50%{{transform:translate(3px,-3px)}}}}
    """
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{value}{suffix} {escape(label.lower())}">
  <title>{value}{suffix} {escape(label.lower())}</title>
  <defs>
    <linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".09"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <clipPath id="cc"><rect width="{W}" height="{H}" rx="10"/></clipPath>
  </defs>
  <style>
    .num{{font:800 54px {SANS};fill:{CREAM};letter-spacing:1px}}
    .suf{{fill:{RED}}}
    .lbl{{font:700 11px {MONO};letter-spacing:1.8px;fill:{CREAM}}}
    .sub{{font:500 11px {MONO};fill:{MUTED}}}
    {anim_css}
  </style>
  <g class="card">
    <g clip-path="url(#cc)">
      <rect width="{W}" height="{H}" fill="{NAVY}"/>
      <polygon points="{W - 46},0 {W},0 {W},46" fill="{RED}"/>
      <rect class="shine" x="0" y="0" width="120" height="{H}" fill="url(#sh)" transform="skewX(-18)"/>
      <rect x="0" y="{H - 3}" width="{W}" height="3" fill="{RED}" opacity=".8"/>
    </g>
    <rect x=".5" y=".5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{LINE}"/>
    <circle class="ring" cx="263" cy="15" r="7" fill="none" stroke="{CREAM}" stroke-width="1.5" opacity="0"/>
    <text x="264" y="20" text-anchor="middle" class="lbl arrow" style="fill:{NAVY};font-size:13px">↗</text>
    {''.join(nums)}
    <text x="24" y="112" class="lbl">{escape(label)}</text>
    <text x="24" y="131" class="sub">{escape(sub)}</text>
  </g>
</svg>
"""
    write(fname, svg)


BUTTONS = [
    ("btn-portfolio.svg", "PORTFOLIO"),
    ("btn-linkedin.svg", "LINKEDIN"),
    ("btn-cv.svg", "CV · EN"),
    ("btn-cv-hu.svg", "CV · HU"),
]


def make_button(fname: str, text: str, i: int) -> None:
    W, H = 200, 44
    anim_css = "" if STATIC else f"""
    .b{{opacity:0;animation:pop .5s cubic-bezier(.2,1.4,.4,1) {0.15 + i * 0.12:.2f}s forwards}}
    @keyframes pop{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
    .sw{{animation:sw 4s ease-in-out {1.5 + i * 0.3:.2f}s infinite}}
    @keyframes sw{{0%{{transform:translateX(-90px)}}35%,100%{{transform:translateX(300px)}}}}
    """
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{escape(text.title())}">
  <title>{escape(text.title())}</title>
  <defs>
    <linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff" stop-opacity=".18"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
    <clipPath id="c"><polygon points="10,0 {W},0 {W},{H - 10} {W - 10},{H} 0,{H} 0,10"/></clipPath>
  </defs>
  <style>
    .t{{font:700 13px {MONO};letter-spacing:2.5px;fill:{CREAM}}}
    {anim_css}
  </style>
  <g class="b">
    <g clip-path="url(#c)">
      <rect width="{W}" height="{H}" fill="{NAVY}"/>
      <rect width="5" height="{H}" fill="{RED}"/>
      <rect class="sw" width="60" height="{H}" fill="url(#g)" transform="skewX(-20)"/>
    </g>
    <polygon points="10,.75 {W - .75},.75 {W - .75},{H - 10} {W - 10},{H - .75} .75,{H - .75} .75,10" fill="none" stroke="{RED}" stroke-width="1.5"/>
    <text x="{W / 2 + 2}" y="27" text-anchor="middle" class="t">{escape(text)} <tspan fill="{RED}">↗</tspan></text>
  </g>
</svg>
"""
    write(fname, svg)


if __name__ == "__main__":
    make_header()
    make_whoami()
    make_orchestrator()
    for t in TILES:
        make_tile(*t)
    for i, (fname, text) in enumerate(BUTTONS):
        make_button(fname, text, i)
