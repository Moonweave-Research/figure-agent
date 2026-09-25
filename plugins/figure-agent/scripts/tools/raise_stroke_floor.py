#!/usr/bin/env python3
"""Raise the thinnest strokes of a vector figure PDF to a floor without redrawing it.

Nature Communications asks that "the thinnest lines in the final figure should be no
smaller than one point wide" (nature.com/ncomms/submit/how-to-submit). Measured
published articles do not follow that literally, so the figures ship at their design
weights; this tool exists so a production request can be met in one pass instead of a
redesign. It rewrites the `w` (set line width) operators in the page content stream.

Two modes:
  shift   every width moves up by the same amount, so the thinnest lands on the floor
          and every weight difference is preserved exactly. This is the default.
  clamp   every width below the floor becomes the floor. Heavier lines are untouched,
          so the hierarchy below the floor collapses into a single weight.

Page geometry, text, colours and data are untouched.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pymupdf

_W_OP = re.compile(rb"(?<![0-9.])([0-9]*\.?[0-9]+)\s+w\b")


def _widths(pdf: Path) -> list[float]:
    page = pymupdf.open(pdf)[0]
    return [
        d["width"]
        for d in page.get_drawings()
        if d.get("type") in ("s", "fs") and d.get("width")
    ]


def rewrite(src: Path, dst: Path, floor: float, mode: str) -> dict[str, object]:
    doc = pymupdf.open(src)
    if doc.page_count != 1:
        raise SystemExit(f"expected a single-page figure, found {doc.page_count} pages")
    page = doc[0]
    observed = _widths(src)
    if not observed:
        raise SystemExit("no vector strokes found; is this a raster figure?")
    lo = min(observed)
    offset = max(0.0, floor - lo)
    changed = 0

    def sub(match: re.Match[bytes]) -> bytes:
        nonlocal changed
        value = float(match.group(1))
        if value <= 0:
            return match.group(0)
        new = max(value, floor) if mode == "clamp" else value + offset
        if abs(new - value) < 1e-6:
            return match.group(0)
        changed += 1
        return f"{new:.4g} w".encode()

    for xref in page.get_contents():
        doc.update_stream(xref, _W_OP.sub(sub, doc.xref_stream(xref)))
    dst.parent.mkdir(parents=True, exist_ok=True)
    doc.save(dst, garbage=4, deflate=True)
    doc.close()
    after = _widths(dst)
    return {
        "mode": mode,
        "operators_rewritten": changed,
        "offset_pt": round(offset, 3),
        "before": f"{round(lo, 3)}-{round(max(observed), 3)}",
        "after": f"{round(min(after), 3)}-{round(max(after), 3)}",
        "distinct_before": len({round(w, 2) for w in observed}),
        "distinct_after": len({round(w, 2) for w in after}),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--floor", type=float, default=1.0, help="minimum stroke width in points")
    ap.add_argument("--mode", choices=("shift", "clamp"), default="shift")
    args = ap.parse_args()
    report = rewrite(args.source, args.output, args.floor, args.mode)
    for key, value in report.items():
        print(f"{key}: {value}")
    after_min = float(str(report["after"]).split("-")[0])
    if after_min + 1e-6 < args.floor:
        print(
            "WARNING: some strokes are still below the floor; "
            "they are set outside the content stream"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
