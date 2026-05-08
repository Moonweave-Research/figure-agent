"""Convert source-cm panel boxes into PDF-cm bbox_pdf_cm values.

The helper reads the figure's .tex wrapper for the resizebox target width,
standalone border, and source canvas size. Panel inputs stay in source TikZ
coordinates (cm, y-up); output uses PDF cm with top-left origin and y-down.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path


class BboxHelperError(Exception):
    """Expected user-facing error while converting source panel boxes."""


@dataclass(frozen=True)
class TexGeometry:
    resizebox_width_cm: float
    source_size_cm: tuple[float, float]
    border_pt: float

    @property
    def cm_per_source(self) -> float:
        return self.resizebox_width_cm / self.source_size_cm[0]

    @property
    def origin_offset_cm(self) -> float:
        return self.border_pt * 2.54 / 72.0


_RESIZEBOX_RE = re.compile(
    r"\\resizebox\s*\{\s*([0-9]+(?:\.[0-9]+)?)\s*(cm|mm|pt|in)\s*\}\s*\{\s*!\s*\}",
    re.IGNORECASE,
)
_DOCUMENTCLASS_RE = re.compile(r"\\documentclass\s*(?:\[(?P<opts>[^\]]*)\])?\s*\{standalone\}")
_BORDER_RE = re.compile(r"border\s*=\s*([0-9]+(?:\.[0-9]+)?)\s*pt", re.IGNORECASE)
_CANVAS_COMMENT_RE = re.compile(
    "Canvas:\\s*([0-9]+(?:\\.[0-9]+)?)\\s*cm\\s*"
    "[xX\\u00d7]\\s*([0-9]+(?:\\.[0-9]+)?)\\s*cm"
)
_BOUNDING_BOX_RE = re.compile(
    r"\\path\s*\[[^\]]*use\s+as\s+bounding\s+box[^\]]*\]\s*"
    r"\(\s*0\s*,\s*0\s*\)\s*rectangle\s*"
    r"\(\s*([0-9]+(?:\.[0-9]+)?)\s*,\s*([0-9]+(?:\.[0-9]+)?)\s*\)",
    re.IGNORECASE,
)
_UNIT_TO_CM = {
    "cm": 1.0,
    "mm": 0.1,
    "pt": 2.54 / 72.0,
    "in": 2.54,
}


def _dimension_to_cm(value: str, unit: str) -> float:
    return float(value) * _UNIT_TO_CM[unit.lower()]


def _parse_resizebox_width_cm(tex: str) -> float:
    match = _RESIZEBOX_RE.search(tex)
    if match is None:
        raise BboxHelperError("could not find \\resizebox{<width>}{!}{...} in .tex")
    return _dimension_to_cm(match.group(1), match.group(2))


def _parse_border_pt(tex: str) -> float:
    documentclass = _DOCUMENTCLASS_RE.search(tex)
    if documentclass is None:
        raise BboxHelperError("could not find standalone \\documentclass[...] in .tex")
    opts = documentclass.group("opts") or ""
    border = _BORDER_RE.search(opts)
    if border is None:
        raise BboxHelperError("could not find border=<pt>pt in standalone documentclass")
    return float(border.group(1))


def _parse_source_size_cm(tex: str) -> tuple[float, float]:
    comment = _CANVAS_COMMENT_RE.search(tex)
    if comment is not None:
        return (float(comment.group(1)), float(comment.group(2)))

    bounding_box = _BOUNDING_BOX_RE.search(tex)
    if bounding_box is not None:
        return (float(bounding_box.group(1)), float(bounding_box.group(2)))

    raise BboxHelperError(
        "could not infer source canvas size; add a '% Canvas: <W>cm x <H>cm' comment"
    )


def parse_tex_geometry(tex: str) -> TexGeometry:
    return TexGeometry(
        resizebox_width_cm=_parse_resizebox_width_cm(tex),
        source_size_cm=_parse_source_size_cm(tex),
        border_pt=_parse_border_pt(tex),
    )


def convert_source_bbox_to_pdf_cm(
    bbox_source_cm: Sequence[float], geometry: TexGeometry
) -> list[float]:
    if len(bbox_source_cm) != 4:
        raise BboxHelperError("source bbox must contain x0, y0, x1, y1")
    x0, y0, x1, y1 = [float(value) for value in bbox_source_cm]
    if x1 <= x0 or y1 <= y0:
        raise BboxHelperError("source bbox must satisfy x1>x0 and y1>y0")

    scale = geometry.cm_per_source
    origin = geometry.origin_offset_cm
    source_height = geometry.source_size_cm[1]
    return [
        origin + x0 * scale,
        origin + (source_height - y1) * scale,
        origin + x1 * scale,
        origin + (source_height - y0) * scale,
    ]


def format_panel_bbox(panel_id: str, bbox_pdf_cm: Sequence[float]) -> str:
    values = ", ".join(f"{value:.3f}" for value in bbox_pdf_cm)
    return f"  - id: {panel_id}\n    bbox_pdf_cm: [{values}]"


def _parse_pair(raw: str, label: str) -> tuple[float, float]:
    parts = [part.strip() for part in raw.split(",")]
    if len(parts) != 2:
        raise BboxHelperError(f"{label}= must contain two comma-separated numbers")
    try:
        first, second = (float(parts[0]), float(parts[1]))
    except ValueError as exc:
        raise BboxHelperError(f"{label}= must contain numeric values") from exc
    if second <= first:
        raise BboxHelperError(f"{label}= must satisfy upper > lower")
    return first, second


def parse_panel_arg(tokens: Sequence[str]) -> tuple[str, tuple[float, float, float, float]]:
    fields: dict[str, str] = {}
    for token in tokens:
        key, sep, value = token.partition("=")
        if not sep:
            raise BboxHelperError(f"invalid --panel token {token!r}; expected key=value")
        fields[key.strip()] = value.strip()
    missing = {"id", "x", "y"} - fields.keys()
    if missing:
        raise BboxHelperError(f"--panel missing required field(s): {', '.join(sorted(missing))}")
    x0, x1 = _parse_pair(fields["x"], "x")
    y0, y1 = _parse_pair(fields["y"], "y")
    return fields["id"], (x0, y0, x1, y1)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert source TikZ cm panel boxes into spec.yaml bbox_pdf_cm values "
            "(PDF cm, top-left origin, y-down)."
        )
    )
    parser.add_argument("name", help="Fixture name under examples/<name>/")
    parser.add_argument(
        "--examples-root",
        default="examples",
        help="Examples directory root; default: examples",
    )
    parser.add_argument(
        "--panel",
        action="append",
        nargs="+",
        metavar="FIELD",
        help=(
            "Panel definition in source cm, e.g. "
            "--panel id=row1 x=0,4.5 y=5,9. Repeat for multiple panels."
        ),
    )
    return parser


def run(argv: Sequence[str] | None = None) -> str:
    args = _build_parser().parse_args(argv)
    example_dir = Path(args.examples_root) / args.name
    tex_path = example_dir / f"{args.name}.tex"
    if not tex_path.is_file():
        raise BboxHelperError(f"missing {tex_path}")

    geometry = parse_tex_geometry(tex_path.read_text(encoding="utf-8"))
    lines = [
        f"# {args.name}",
        f"cm_per_source: {geometry.cm_per_source:.6f}",
        "origin_offset_cm: "
        f"[{geometry.origin_offset_cm:.6f}, {geometry.origin_offset_cm:.6f}]",
        "source_size_cm: "
        f"[{geometry.source_size_cm[0]:.3f}, {geometry.source_size_cm[1]:.3f}]",
    ]
    if not args.panel:
        lines.append("# add --panel id=<id> x=<x0>,<x1> y=<y0>,<y1> to print bbox_pdf_cm")
        return "\n".join(lines) + "\n"

    lines.append("panels:")
    for panel_tokens in args.panel:
        panel_id, bbox_source_cm = parse_panel_arg(panel_tokens)
        bbox_pdf_cm = convert_source_bbox_to_pdf_cm(bbox_source_cm, geometry)
        lines.append(format_panel_bbox(panel_id, bbox_pdf_cm))
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    try:
        print(run(argv), end="")
    except BboxHelperError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
