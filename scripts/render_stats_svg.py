"""Render data/contributions.json as a slim stats bar (assets/contrib-stats.svg)."""
from __future__ import annotations

import json
from datetime import date
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "contributions.json"
OUT = ROOT / "assets" / "contrib-stats.svg"

BG, LINE, CREAM, MUTED, GREEN = "#161b22", "#30363d", "#e6edf3", "#8b949e", "#39d353"
MONO = "'JetBrains Mono','Cascadia Code','SFMono-Regular',Menlo,Consolas,monospace"


def main() -> None:
    stats = json.loads(DATA.read_text(encoding="utf-8")).get("stats") if DATA.exists() else None
    if stats:
        parts = [
            ("big", f"{stats['total']:,}", "contributions in the last year"),
            ("hl", f"{stats['current_streak']}d", "streak"),
            ("hl", f"{stats['longest_streak']}d", "longest"),
            ("hl", str(stats["best_day"]["count"]), "best day"),
        ]
        stamp = f"synced {date.today().isoformat()}"
    else:
        parts = [("hl", "...", "syncing contribution data")]
        stamp = "waiting for first sync"

    sep = f'  <tspan fill="{LINE}">|</tspan>  '
    line = sep.join(f'<tspan class="{c}">{escape(v)}</tspan> {escape(t)}' for c, v, t in parts)
    W, H = 860, 52
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub contribution stats">
  <title>Contribution stats</title>
  <style>
    .f{{font:500 12px {MONO};fill:{MUTED}}}
    .m{{font:500 10px {MONO};fill:{MUTED}}}
    .big{{font-weight:800;fill:{CREAM}}}
    .hl{{font-weight:700;fill:{GREEN}}}
  </style>
  <rect width="{W}" height="{H}" rx="10" fill="{BG}" stroke="{LINE}"/>
  <text x="24" y="31" class="f">{line}</text>
  <text x="{W - 24}" y="31" text-anchor="end" class="m">{escape(stamp)}</text>
</svg>
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
