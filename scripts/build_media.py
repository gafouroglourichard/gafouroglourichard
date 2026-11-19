"""Turn the real portfolio videos and screenshots into README-friendly media.

GitHub READMEs only autoplay images, so every MP4 becomes a short, looping,
silent animated WebP. Sources are downloaded from the live portfolio site.

Writes assets/media/*.webp|jpg and assets/media/manifest.json.
Needs ffmpeg + Pillow + requests. Run:  python scripts/build_media.py
For a dry run without network:  FAKE_SRC=some.mp4 python scripts/build_media.py
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import requests
from PIL import Image

BASE = "https://richard-portfolio-2026-27.vercel.app"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "media"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MAX_BYTES = 3_500_000  # keep every file light enough for the profile page
FAKE_SRC = os.environ.get("FAKE_SRC")

ISO = "/assets/13-IN-DEVELOPMENT/iso-{}-en.mp4"
DEMO = "/assets/{}/Demo-Recordings/{}-demo-en.mp4"

# name -> (source path, width, fps, max seconds of output, speed-up)
LOOPS = {
    # real screen recordings of the live systems (client data masked)
    "minicrm": (DEMO.format("04-MINICRM", "minicrm"), 640, 10, 12, 2.0),
    "marketing-intelligence": (DEMO.format("02-MARKETING-INTELLIGENCE", "marketing-intelligence"), 640, 10, 12, 2.0),
    "autoseo": (DEMO.format("03-AUTOSEO", "autoseo"), 640, 10, 12, 2.0),
    "knowledge-hub": (DEMO.format("09-ZERO-TUDASTAR", "tudastar"), 640, 10, 12, 2.0),
    "ticketing": (DEMO.format("10-AI-TICKETING", "ticketing"), 640, 10, 12, 2.0),
    "managai": (DEMO.format("11-MANAGAI", "managai"), 640, 10, 12, 2.0),
    "graffler": (DEMO.format("12-GRAFFLER", "graffler"), 640, 10, 12, 2.0),
    # iso-flow illustrations of the apps in development
    "iso-warehouse": (ISO.format("wh"), 640, 10, 9, 1.0),
    "iso-fleet": (ISO.format("fleet"), 640, 10, 9, 1.0),
    "iso-day-counter": (ISO.format("cal"), 640, 10, 9, 1.0),
    "iso-cashflow": (ISO.format("cash"), 640, 10, 9, 1.0),
    "iso-clinic": (ISO.format("clinic"), 640, 10, 9, 1.0),
    "iso-production-line": (ISO.format("line"), 640, 10, 9, 1.0),
    "iso-maintenance": (ISO.format("maint"), 640, 10, 9, 1.0),
    "iso-pharma": (ISO.format("pharma"), 640, 10, 9, 1.0),
    "iso-office": (ISO.format("office"), 640, 10, 9, 1.0),
    "iso-real-estate": (ISO.format("estate"), 640, 10, 9, 1.0),
}
TEASER_SRC = "/assets/07-FINAL-VIDEOS/portfolio-v4-en.mp4"
STILLS = {
    "4ma-dashboard": ("/assets/06-HIGGSFIELD-ASSETS/karakterek/zero-studio-dashboard-mascot-koncepcio.png", 1720),
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def fetch(path: str, dest: Path) -> Path:
    if FAKE_SRC:
        if path.endswith(".png"):
            Image.new("RGB", (1920, 1080), "#16222e").save(dest)
        else:
            dest.write_bytes(Path(FAKE_SRC).read_bytes())
        return dest
    with requests.get(BASE + path, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(1 << 16):
                f.write(chunk)
    return dest


def duration(src: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(src)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    return float(out or 0)


def encode_webp(src: Path, dest: Path, width: int, fps: int, max_s: float, speed: float) -> None:
    """Encode an animated WebP, stepping quality/fps down until it fits MAX_BYTES."""
    for quality, f in ((62, fps), (50, fps), (42, max(6, fps - 2)), (35, max(5, fps - 4))):
        chain = f"setpts=PTS/{speed},fps={f},scale={width}:-2:flags=lanczos"
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
            "-t", str(max_s),
            "-vf", chain, "-an", "-c:v", "libwebp_anim", "-lossless", "0",
            "-quality", str(quality), "-compression_level", "6", "-loop", "0", str(dest),
        ])
        if dest.stat().st_size <= MAX_BYTES:
            return
    print(f"  ! {dest.name} still {dest.stat().st_size // 1024} KB after the smallest setting")


def make_teaser(src: Path, dest: Path) -> None:
    """Three short real moments from the 3-minute portfolio video, with a play badge."""
    total = duration(src) or 180
    seg = 4.0
    starts = [total * p for p in (0.18, 0.48, 0.78)]
    parts = "".join(
        f"[0:v]trim=start={s:.2f}:duration={seg},setpts=PTS-STARTPTS[s{i}];" for i, s in enumerate(starts)
    )
    badge = (
        "drawbox=x=24:y=ih-78:w=372:h=54:color=0xff4655@0.92:t=fill,"
        f"drawtext=fontfile={FONT}:text='▶  WATCH  ·  MY WORK IN 3 MIN':x=44:y=h-60:fontsize=19:fontcolor=0xece8e1"
    )
    graph = (
        parts
        + "".join(f"[s{i}]" for i in range(len(starts)))
        + f"concat=n={len(starts)}:v=1:a=0,fps=10,scale=860:-2:flags=lanczos,{badge}[out]"
    )
    for quality in (60, 48, 38):
        run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
            "-filter_complex", graph, "-map", "[out]", "-an",
            "-c:v", "libwebp_anim", "-lossless", "0", "-quality", str(quality),
            "-compression_level", "6", "-loop", "0", str(dest),
        ])
        if dest.stat().st_size <= MAX_BYTES:
            return


def info(path: Path) -> dict:
    im = Image.open(path)
    return {
        "file": path.name,
        "kb": path.stat().st_size // 1024,
        "size": list(im.size),
        "frames": getattr(im, "n_frames", 1),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"source": BASE, "files": []}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for name, (path, width) in STILLS.items():
            src = fetch(path, tmp / Path(path).name)
            im = Image.open(src).convert("RGB")
            if im.width > width:
                im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
            dest = OUT / f"{name}.jpg"
            im.save(dest, "JPEG", quality=86, optimize=True, progressive=True)
            manifest["files"].append(info(dest))
            print("still", dest.name)

        src = fetch(TEASER_SRC, tmp / "teaser.mp4")
        dest = OUT / "portfolio-teaser.webp"
        make_teaser(src, dest)
        manifest["files"].append(info(dest))
        print("teaser", dest.name)

        for name, (path, width, fps, max_s, speed) in LOOPS.items():
            src = fetch(path, tmp / f"{name}.mp4")
            dest = OUT / f"{name}.webp"
            encode_webp(src, dest, width, fps, max_s, speed)
            manifest["files"].append(info(dest))
            print("loop", dest.name, manifest["files"][-1]["kb"], "KB")

    total = sum(f["kb"] for f in manifest["files"])
    manifest["total_kb"] = total
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"done: {len(manifest['files'])} files, {total // 1024} MB total")


if __name__ == "__main__":
    main()
