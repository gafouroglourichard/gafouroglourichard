"""Render data/contributions.json as an animated contribution heatmap SVG.

Boxes slide in diagonally once, then freeze. If the JSON is missing the
script draws an empty "syncing" grid so the README never shows a broken image.
"""
from __future__ import annotations

import json
import os
from datetime import date, timedelta
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "contrib-heatmap.svg"

NAVY, PANEL, LINE = "#0f1923", "#16222e", "#2a3a4a"
RED, CREAM, MUTED, TEAL = "#ff4655", "#ece8e1", "#8b97a5", "#17e8b0"
PALETTE = ["#1c2833", "#4a1f2a", "#7d2533", "#b8303f", "#ff4655", "#ff9aa2"]
MONO = "'JetBrains Mono','Cascadia Code','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"
STATIC = os.environ.get("STATIC") == "1"


def load() -> tuple[list[dict], dict | None]:
    if DATA.exists():
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        return payload["days"], payload["stats"]
    end = date.today()
    start = end - timedelta(days=364)
    start -= timedelta(days=(start.weekday() + 1) % 7)  # back to Sunday
    n = (end - start).days + 1
    return [{"date": (start + timedelta(d)).isoformat(), "count": 0, "level": 0} for d in range(n)], None


def level_of(day: dict, top: int) -> int:
    if day["count"] <= 0:
        return 0
    lvl = int(day.get("level") or 0)
    if lvl >= 4 and top and day["count"] >= top * 0.9:
        return 5  # neon top end for the very best days
    return max(1, min(4, lvl or 1))


def main() -> None:
    days, stats = load()
    first = date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7  # Sunday = row 0
    top = max((d["count"] for d in days), default=0)

    cell, gap = 12, 3
    step = cell + gap
    left, top_pad = 44, 58
    weeks = (lead + len(days) + 6) // 7
    W = 860
    grid_w = weeks * step
    left = max(36, (W - grid_w) // 2 + 10)
    H = top_pad + 7 * step + 64

    rects, months = [], []
    last_month = None
    for i, d in enumerate(days):
        idx = lead + i
        wk, dow = divmod(idx, 7)
        x, y = left + wk * step, top_pad + dow * step
        lvl = level_of(d, top)
        delay = (wk + dow) * 0.014
        style = "" if STATIC else f' style="animation-delay:{delay:.3f}s"'
        tip = f"{d['count']} contribution{'s' if d['count'] != 1 else ''} on {d['date']}"
        rects.append(
            f'<rect class="c" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{PALETTE[lvl]}"{style}><title>{tip}</title></rect>'
        )
        dt = date.fromisoformat(d["date"])
        if dow == 0 and dt.month != last_month:
            last_month = dt.month
            if wk < weeks - 2:  # avoid a clipped label at the far right
                months.append(f'<text x="{x}" y="{top_pad - 10}" class="m">{dt.strftime("%b")}</text>')

    labels = "".join(
        f'<text x="{left - 8}" y="{top_pad + r * step + 10}" text-anchor="end" class="m">{t}</text>'
        for r, t in ((1, "Mon"), (3, "Wed"), (5, "Fri"))
    )
    lg_x = left + grid_w - (len(PALETTE) * step) - 40
    legend = [f'<text x="{lg_x - 8}" y="{H - 44}" text-anchor="end" class="m">Less</text>']
    for k, c in enumerate(PALETTE):
        legend.append(f'<rect x="{lg_x + k * step}" y="{H - 54}" width="{cell}" height="{cell}" rx="3" fill="{c}"/>')
    legend.append(f'<text x="{lg_x + len(PALETTE) * step + 4}" y="{H - 44}" class="m">More</text>')

    if stats:
        best = stats["best_day"]
        footer = (
            f'<tspan class="big">{stats["total"]:,}</tspan> contributions in the last year'
            f'  <tspan fill="{LINE}">|</tspan>  streak <tspan class="hl">{stats["current_streak"]}d</tspan>'
            f'  <tspan fill="{LINE}">|</tspan>  longest <tspan class="hl">{stats["longest_streak"]}d</tspan>'
            f'  <tspan fill="{LINE}">|</tspan>  best day <tspan class="hl">{best["count"]}</tspan>'
        )
        stamp = f"synced {date.today().isoformat()}"
    else:
        footer = 'syncing contribution data<tspan class="hl">…</tspan>'
        stamp = "waiting for first sync"

    anim_css = "" if STATIC else """
    .c{opacity:0;transform-box:fill-box;transform-origin:center;animation:drop .5s cubic-bezier(.2,.8,.2,1) forwards}
    @keyframes drop{from{opacity:0;transform:translateY(-10px) scale(.6)}to{opacity:1;transform:none}}
    """
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub contribution heatmap">
  <title>Contribution heatmap</title>
  <style>
    .m{{font:500 10px {MONO};fill:{MUTED}}}
    .hdr{{font:700 12px {MONO};letter-spacing:3px;fill:{CREAM}}}
    .f{{font:500 12px {MONO};fill:{MUTED}}}
    .big{{font-weight:800;fill:{CREAM}}}
    .hl{{font-weight:700;fill:{RED}}}
    {anim_css}
  </style>
  <rect width="{W}" height="{H}" rx="10" fill="{NAVY}" stroke="{LINE}"/>
  <text x="24" y="30" class="hdr">CONTRIBUTIONS // LAST 12 MONTHS</text>
  <text x="{W - 24}" y="30" text-anchor="end" class="m">{escape(stamp)}</text>
  {''.join(months)}{labels}
  {''.join(rects)}
  <text x="{left}" y="{H - 44}" class="f">{footer}</text>
  {''.join(legend)}
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({weeks} weeks)")


if __name__ == "__main__":
    main()
