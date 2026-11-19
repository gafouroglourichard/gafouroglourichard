"""Scrape the public contribution calendar (no token needed) into data/contributions.json.

GitHub serves the same HTML fragment the profile page uses at
https://github.com/users/<username>/contributions
"""
from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USERNAME = os.environ.get("GH_USER", "gafouroglourichard")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"

COUNT_RE = re.compile(r"(\d[\d,]*|No)\s+contributions?", re.I)


def fetch_html() -> str:
    url = f"https://github.com/users/{USERNAME}/contributions"
    r = requests.get(url, headers={"User-Agent": "profile-art-bot"}, timeout=30)
    r.raise_for_status()
    return r.text


def parse(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    tips = {}
    for tip in soup.select("tool-tip[for]"):
        m = COUNT_RE.search(tip.get_text(" ", strip=True))
        if m:
            raw = m.group(1)
            tips[tip["for"]] = 0 if raw.lower() == "no" else int(raw.replace(",", ""))
    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        level = int(td.get("data-level", 0))
        count = tips.get(td.get("id", ""), None)
        if count is None:  # older markup kept the count on the cell itself
            m = COUNT_RE.search(td.get_text(" ", strip=True))
            count = 0 if not m or m.group(1).lower() == "no" else int(m.group(1).replace(",", ""))
        days.append({"date": td["data-date"], "count": count, "level": level})
    days.sort(key=lambda d: d["date"])
    return days


def stats(days: list[dict]) -> dict:
    total = sum(d["count"] for d in days)
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    # current streak: count back from today (today may still be empty)
    current = 0
    by_date = {d["date"]: d["count"] for d in days}
    cursor = date.fromisoformat(days[-1]["date"]) if days else date.today()
    if by_date.get(cursor.isoformat(), 0) == 0:
        cursor -= timedelta(days=1)
    while by_date.get(cursor.isoformat(), 0) > 0:
        current += 1
        cursor -= timedelta(days=1)
    best = max(days, key=lambda d: d["count"], default={"date": None, "count": 0})
    monthly = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]
    return {
        "total": total,
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": dict(monthly),
    }


def main() -> None:
    days = parse(fetch_html())
    if not days:
        raise SystemExit("No contribution cells found – GitHub markup may have changed.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {"username": USERNAME, "generated": date.today().isoformat(), "days": days, "stats": stats(days)}
    OUT.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    s = payload["stats"]
    print(f"{len(days)} days, {s['total']} contributions, streak {s['current_streak']} (longest {s['longest_streak']})")


if __name__ == "__main__":
    main()
