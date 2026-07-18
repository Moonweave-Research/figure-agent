#!/usr/bin/env python3
"""Derive panel-frame text-boundary coverage from an authored source.

The R5.2 failure was silent zero coverage: an authored figure declared no
text-boundary geometry, so a label crossing its own panel frame was invisible to
every declared check. This module closes that gap declaratively.

Panel frame geometry is read from the authored source itself -- the ``% Panel
<id>`` marker blocks and the ``panel frame`` styled rectangle inside each block --
never from product-code constants. The rendered frame position pins the
source-to-PDF affine so the derived boundary lines live in the same coordinate
space as the extracted words. Each panel frame becomes up to four boundary-line
checks fed to the existing text-boundary detector (no threshold change, additive
only). A declared per-panel intentional-overflow allowlist distinguishes an
intended overhang from an accidental boundary crossing. Panels with no frame and
no explicit boundary geometry report zero coverage loudly rather than passing
silently.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

from check_text_boundary_clash import CM_TO_PT, detect_text_boundary_clashes  # noqa: E402
from check_visual_clash import extract_pdf_words_and_page  # noqa: E402

SCHEMA = "figure-agent.panel-boundary-coverage.v1"
FRAME_MATCH_TOL_PT = 2.0
AFFINE_MATCH_TOL_PT = 2.5

_PANEL_MARKER = re.compile(r"^\s*%\s*Panel\s+(\S+)\s*$")
_PANEL_FRAME_RECT = re.compile(
    r"\\draw\s*\[[^\]]*panel frame[^\]]*\]\s*"
    r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)\s*"
    r"rectangle\s*"
    r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)"
)
_SCOPE_SHIFT = re.compile(
    r"shift\s*=\s*\{\s*\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)\s*\}"
)
_SCOPE_TRANSFORM = re.compile(r"\\begin\{scope\}\s*\[[^\]]*\b(scale|rotate|xscale|yscale)\b")


class PanelBoundaryError(ValueError):
    """Controlled fail-closed error for panel-boundary coverage derivation."""


@dataclass(frozen=True)
class PanelFrame:
    panel_id: str
    source_bbox: tuple[float, float, float, float] | None


def parse_panel_frames(tex_text: str) -> list[PanelFrame]:
    """Extract ordered ``% Panel <id>`` blocks and their frame source geometry.

    Fails closed on missing markers, duplicate markers, more than one panel-frame
    rectangle in a block, or an unmodelled scope transform (scale/rotate).
    """
    lines = tex_text.splitlines()
    markers: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = _PANEL_MARKER.match(line)
        if match is not None:
            markers.append((index, match.group(1).strip()))
    if not markers:
        raise PanelBoundaryError("no % Panel <id> markers found in source")

    seen: set[str] = set()
    for _, panel_id in markers:
        if panel_id in seen:
            raise PanelBoundaryError(f"duplicate panel marker: {panel_id}")
        seen.add(panel_id)

    frames: list[PanelFrame] = []
    for position, (line_index, panel_id) in enumerate(markers):
        end_index = markers[position + 1][0] if position + 1 < len(markers) else len(lines)
        block = "\n".join(lines[line_index + 1 : end_index])
        frames.append(PanelFrame(panel_id, _frame_source_bbox(block, panel_id)))
    return frames


def _frame_source_bbox(block: str, panel_id: str) -> tuple[float, float, float, float] | None:
    rects = list(_PANEL_FRAME_RECT.finditer(block))
    if not rects:
        return None
    if len(rects) > 1:
        raise PanelBoundaryError(
            f"panel {panel_id} has {len(rects)} panel-frame rectangles; expected one"
        )
    rect = rects[0]
    x0, y0, x1, y1 = (float(rect.group(i)) for i in range(1, 5))

    before = block[: rect.start()]
    if _SCOPE_TRANSFORM.search(before):
        raise PanelBoundaryError(
            f"panel {panel_id} scope uses an unmodelled transform (scale/rotate)"
        )
    shift_x, shift_y = 0.0, 0.0
    shifts = list(_SCOPE_SHIFT.finditer(before))
    if shifts:
        shift_x = float(shifts[-1].group(1))
        shift_y = float(shifts[-1].group(2))

    xs = (x0 + shift_x, x1 + shift_x)
    ys = (y0 + shift_y, y1 + shift_y)
    return (min(xs), min(ys), max(xs), max(ys))


Affine = tuple[float, float, float]


def solve_source_to_pdf_affine(
    source_bboxes: list[tuple[float, float, float, float]],
    pdf_frame_bboxes: list[tuple[float, float, float, float]],
) -> Affine:
    """Return (scale, tx, ty) mapping source cm to top-origin PDF points.

    Scale is derived from the aggregate frame extents (uniform scale assumed and
    validated). The transform is confirmed by a bijective per-frame match; any
    inconsistency fails closed.
    """
    if not source_bboxes:
        raise PanelBoundaryError("no framed panels to solve an affine for")
    if len(pdf_frame_bboxes) != len(source_bboxes):
        raise PanelBoundaryError(
            f"frame count mismatch: {len(source_bboxes)} source vs {len(pdf_frame_bboxes)} rendered"
        )

    src_xmin = min(b[0] for b in source_bboxes)
    src_ymin = min(b[1] for b in source_bboxes)
    src_xmax = max(b[2] for b in source_bboxes)
    src_ymax = max(b[3] for b in source_bboxes)
    src_w = src_xmax - src_xmin
    src_h = src_ymax - src_ymin
    if src_w <= 0 or src_h <= 0:
        raise PanelBoundaryError("degenerate source frame extent")

    pdf_x0 = min(f[0] for f in pdf_frame_bboxes)
    pdf_top = min(f[1] for f in pdf_frame_bboxes)
    pdf_x1 = max(f[2] for f in pdf_frame_bboxes)
    pdf_bottom = max(f[3] for f in pdf_frame_bboxes)

    scale_x = (pdf_x1 - pdf_x0) / src_w
    scale_y = (pdf_bottom - pdf_top) / src_h
    if not math.isclose(scale_x, scale_y, rel_tol=0.02):
        raise PanelBoundaryError(
            f"non-uniform source-to-PDF scale (x={scale_x:.3f}, y={scale_y:.3f})"
        )
    scale = (scale_x + scale_y) / 2.0
    tx = pdf_x0 - scale * src_xmin
    ty = pdf_top + scale * src_ymax

    remaining = list(pdf_frame_bboxes)
    for source_bbox in source_bboxes:
        predicted = map_source_to_pdf(source_bbox, (scale, tx, ty))
        matched_index = None
        for index, actual in enumerate(remaining):
            if all(abs(predicted[axis] - actual[axis]) <= AFFINE_MATCH_TOL_PT for axis in range(4)):
                matched_index = index
                break
        if matched_index is None:
            raise PanelBoundaryError("source frame does not match any rendered frame")
        remaining.pop(matched_index)
    return (scale, tx, ty)


def map_source_to_pdf(
    bbox: tuple[float, float, float, float], affine: Affine
) -> tuple[float, float, float, float]:
    scale, tx, ty = affine
    sxmin, symin, sxmax, symax = bbox
    return (
        scale * sxmin + tx,
        ty - scale * symax,
        scale * sxmax + tx,
        ty - scale * symin,
    )


def _frame_edge_checks(
    panel_id: str, pdf_bbox: tuple[float, float, float, float]
) -> list[dict[str, Any]]:
    x0, top, x1, bottom = (value / CM_TO_PT for value in pdf_bbox)
    y_range = [top, bottom]
    x_range = [x0, x1]
    return [
        {
            "id": f"panel-{panel_id}-frame-left",
            "kind": "vertical_line",
            "role": f"panel_{panel_id}_frame_left",
            "x_pdf_cm": x0,
            "y_range_pdf_cm": y_range,
            "clearance_pt": 0.0,
        },
        {
            "id": f"panel-{panel_id}-frame-right",
            "kind": "vertical_line",
            "role": f"panel_{panel_id}_frame_right",
            "x_pdf_cm": x1,
            "y_range_pdf_cm": y_range,
            "clearance_pt": 0.0,
        },
        {
            "id": f"panel-{panel_id}-frame-top",
            "kind": "horizontal_line",
            "role": f"panel_{panel_id}_frame_top",
            "y_pdf_cm": top,
            "x_range_pdf_cm": x_range,
            "clearance_pt": 0.0,
        },
        {
            "id": f"panel-{panel_id}-frame-bottom",
            "kind": "horizontal_line",
            "role": f"panel_{panel_id}_frame_bottom",
            "y_pdf_cm": bottom,
            "x_range_pdf_cm": x_range,
            "clearance_pt": 0.0,
        },
    ]


def _overflow_pairs(intentional_overflow: list[dict[str, Any]] | None) -> set[tuple[str, str]]:
    if intentional_overflow is None:
        return set()
    pairs: set[tuple[str, str]] = set()
    for index, entry in enumerate(intentional_overflow):
        if not isinstance(entry, dict):
            raise PanelBoundaryError(f"intentional_overflow[{index}] must be a mapping")
        panel = entry.get("panel")
        text = entry.get("text")
        if not isinstance(panel, str) or not panel.strip():
            raise PanelBoundaryError(f"intentional_overflow[{index}].panel is required")
        if not isinstance(text, str) or not text.strip():
            raise PanelBoundaryError(f"intentional_overflow[{index}].text is required")
        pairs.add((panel.strip(), text.strip()))
    return pairs


def evaluate_panel_boundary_coverage(
    tex_text: str,
    pdf_frame_bboxes: list[tuple[float, float, float, float]],
    words: list[dict[str, Any]],
    page_size_pt: tuple[float, float],
    intentional_overflow: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Report per-panel boundary coverage and accidental frame crossings."""
    frames = parse_panel_frames(tex_text)
    framed = [frame for frame in frames if frame.source_bbox is not None]

    checks: list[dict[str, Any]] = []
    check_panel: dict[str, str] = {}
    coverage: dict[str, str] = {}

    if framed:
        affine = solve_source_to_pdf_affine(
            [frame.source_bbox for frame in framed if frame.source_bbox is not None],
            pdf_frame_bboxes,
        )
        for frame in framed:
            assert frame.source_bbox is not None
            pdf_bbox = map_source_to_pdf(frame.source_bbox, affine)
            edge_checks = _frame_edge_checks(frame.panel_id, pdf_bbox)
            checks.extend(edge_checks)
            for check in edge_checks:
                check_panel[check["id"]] = frame.panel_id
            coverage[frame.panel_id] = "covered"

    for frame in frames:
        if frame.source_bbox is None:
            coverage[frame.panel_id] = "zero_coverage"

    raw_candidates = detect_text_boundary_clashes(words, page_size_pt, checks) if checks else []
    overflow_pairs = _overflow_pairs(intentional_overflow)

    candidates: list[dict[str, Any]] = []
    suppressed = 0
    for candidate in raw_candidates:
        panel = check_panel[candidate["boundary_id"]]
        candidate["panel"] = panel
        if (panel, candidate["text"]) in overflow_pairs:
            suppressed += 1
            continue
        candidates.append(candidate)
    for index, candidate in enumerate(candidates, start=1):
        candidate["id"] = f"PB{index:03d}"

    zero_coverage_panels = sorted(
        pid for pid, state in coverage.items() if state == "zero_coverage"
    )
    covered_panels = sorted(pid for pid, state in coverage.items() if state == "covered")
    return {
        "schema": SCHEMA,
        "candidates": candidates,
        "total": len(candidates),
        "coverage": coverage,
        "covered_panels": covered_panels,
        "zero_coverage_panels": zero_coverage_panels,
        "zero_coverage": bool(zero_coverage_panels),
        "checked_edges": len(checks),
        "intentional_overflow_suppressed": suppressed,
    }


def read_pdf_frame_bboxes(
    pdf_path: Path, source_frame_sizes_pt: list[tuple[float, float]]
) -> list[tuple[float, float, float, float]]:
    """Read rendered frame bboxes matching the authored frame sizes.

    Sizes come from the parsed source (assuming the standalone default 1cm unit);
    a non-default render scale simply fails the downstream frame-count match.
    """
    import pdfplumber

    def size_matches(width: float, height: float) -> bool:
        return any(
            abs(width - target_w) <= FRAME_MATCH_TOL_PT
            and abs(height - target_h) <= FRAME_MATCH_TOL_PT
            for target_w, target_h in source_frame_sizes_pt
        )

    found: list[tuple[float, float, float, float]] = []
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        for obj in list(page.rects) + list(page.curves):
            bbox = (float(obj["x0"]), float(obj["top"]), float(obj["x1"]), float(obj["bottom"]))
            if size_matches(bbox[2] - bbox[0], bbox[3] - bbox[1]):
                rounded = tuple(round(value, 1) for value in bbox)
                if all(
                    any(abs(rounded[axis] - kept[axis]) > 1.0 for axis in range(4))
                    for kept in found
                ):
                    found.append(bbox)
    return found


def _load_overflow(path: Path | None) -> list[dict[str, Any]] | None:
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("intentional_overflow")
    if data is None:
        return None
    if not isinstance(data, list):
        raise PanelBoundaryError("intentional_overflow declaration must be a list")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Panel-frame boundary coverage from source")
    parser.add_argument("tex", type=Path, help="Authored TikZ source with % Panel markers")
    parser.add_argument("--pdf", type=Path, required=True, help="Rendered PDF of that source")
    parser.add_argument(
        "--overflow",
        type=Path,
        default=None,
        help="Optional intentional-overflow allowlist JSON",
    )
    parser.add_argument("--json-output", type=Path, default=None, help="Report output path")
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="exit 1 when any accidental crossing or zero-coverage panel is found",
    )
    args = parser.parse_args()

    if not args.tex.exists():
        raise FileNotFoundError(f"source not found: {args.tex}")
    if not args.pdf.exists():
        raise FileNotFoundError(f"PDF not found: {args.pdf}")

    tex_text = args.tex.read_text(encoding="utf-8")
    try:
        frames = parse_panel_frames(tex_text)
        source_sizes = [
            (
                (frame.source_bbox[2] - frame.source_bbox[0]) * CM_TO_PT,
                (frame.source_bbox[3] - frame.source_bbox[1]) * CM_TO_PT,
            )
            for frame in frames
            if frame.source_bbox is not None
        ]
        pdf_frame_bboxes = read_pdf_frame_bboxes(args.pdf, source_sizes) if source_sizes else []
        words, page_size = extract_pdf_words_and_page(args.pdf)
        report = evaluate_panel_boundary_coverage(
            tex_text,
            pdf_frame_bboxes,
            words,
            page_size,
            intentional_overflow=_load_overflow(args.overflow),
        )
    except PanelBoundaryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    report["source"] = str(args.tex)
    report["render_pdf"] = str(args.pdf)
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    if report["zero_coverage_panels"]:
        print(f"ZERO-COVERAGE panels (no frame boundary): {report['zero_coverage_panels']}")
    if not report["candidates"]:
        print(
            f"OK: no accidental frame crossings ({report['checked_edges']} edges, "
            f"covered={report['covered_panels']})"
        )
        return 1 if (args.strict and report["zero_coverage_panels"]) else 0

    for candidate in report["candidates"]:
        print(
            "WARN panel_boundary: "
            f"{candidate['id']} panel={candidate['panel']} kind={candidate['kind']} "
            f'text="{candidate["text"]}" boundary={candidate["boundary_id"]}'
        )
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
