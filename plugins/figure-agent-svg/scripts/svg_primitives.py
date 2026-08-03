# ruff: noqa: E501
"""Render semantic SVG fragments from a small figure-primitive DSL.

This is deliberately above raw SVG paths and below a full paper-figure planner.
The LLM or user edits `primitives.yaml`; this module owns the coordinate
geometry for recurring scientific figure fragments.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import yaml

FRAGMENT_RE = re.compile(r"(?m)^[ \t]*<!--\s*figure-agent-fragment:([\w.-]+)\s*-->[ \t]*$")
REPO_ROOT = Path(__file__).resolve().parents[1]
JS_RENDERER_DIR = REPO_ROOT / "scripts" / "js"


def load_primitive_doc(path: Path) -> dict[str, Any]:
    """Load a primitive document from YAML."""
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def _bbox(value: list[float | int]) -> tuple[float, float, float, float]:
    if len(value) != 4:
        raise ValueError("bbox must have four values: x y width height")
    x, y, w, h = (float(part) for part in value)
    if w <= 0 or h <= 0:
        raise ValueError("bbox width and height must be positive")
    return x, y, w, h


def _fmt(value: float | int) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def _bbox_attr(x: float, y: float, w: float, h: float) -> str:
    return f"{_fmt(x)} {_fmt(y)} {_fmt(w)} {_fmt(h)}"


def _attr(value: str) -> str:
    return escape(value, {'"': "&quot;"})


def _text(
    *,
    role: str,
    x: float,
    y: float,
    w: float,
    h: float,
    value: str,
    fill: str = "#111827",
    font_size: int | None = None,
    opacity: float | None = None,
) -> str:
    sizes = {
        "title": 18,
        "panel_letter": 16,
        "label": 14,
        "axis_label": 12,
        "micro": 11,
    }
    size = font_size or sizes[role]
    opacity_attr = "" if opacity is None else f' opacity="{_fmt(opacity)}"'
    return (
        f'<text data-text-role="{role}" data-bbox="{_bbox_attr(x, y, w, h)}" '
        f'x="{_fmt(x)}" y="{_fmt(y + h - 4)}" font-family="Arial" '
        f'font-size="{size}" fill="{fill}"{opacity_attr}>{escape(value)}</text>'
    )


def _run_node_renderer(script_name: str, payload: dict[str, Any]) -> str:
    script = JS_RENDERER_DIR / script_name
    if not script.is_file():
        raise FileNotFoundError(script)
    result = subprocess.run(
        ["node", str(script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        cwd=REPO_ROOT,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or f"exit {result.returncode}"
        raise RuntimeError(f"{script.name} failed: {detail}")
    svg = result.stdout.strip()
    if "<svg" not in svg:
        raise RuntimeError(f"{script.name} did not return an SVG document")
    return svg


def _required_executable(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        raise RuntimeError(f"tikz primitive requires `{name}` on PATH")
    return path


def _run_tikz_command(args: list[str], *, cwd: Path, label: str) -> None:
    result = subprocess.run(
        args,
        text=True,
        capture_output=True,
        check=False,
        cwd=cwd,
    )
    if result.returncode != 0:
        detail = "\n".join(
            part for part in (result.stdout.strip(), result.stderr.strip()) if part
        ) or f"exit {result.returncode}"
        tail = "\n".join(detail.splitlines()[-24:])
        raise RuntimeError(f"tikz primitive {label} failed: {tail}")


def _tikz_document(source: str, *, width: float, height: float) -> str:
    return rf"""\documentclass[tikz,border=0pt]{{standalone}}
\usepackage{{xcolor}}
\usepackage{{tikz}}
\usetikzlibrary{{arrows.meta,calc,decorations.pathreplacing,positioning}}
\definecolor{{fgink}}{{HTML}}{{111827}}
\definecolor{{fgmuted}}{{HTML}}{{6B7280}}
\definecolor{{fgsoftgray}}{{HTML}}{{E5E7EB}}
\definecolor{{fgblue}}{{HTML}}{{2563EB}}
\definecolor{{fgteal}}{{HTML}}{{14B8A6}}
\definecolor{{fgorange}}{{HTML}}{{F97316}}
\definecolor{{fgpurple}}{{HTML}}{{7C3AED}}
\definecolor{{fgwhite}}{{HTML}}{{FFFFFF}}
\def\fgW{{{_fmt(width)}}}
\def\fgH{{{_fmt(height)}}}
\begin{{document}}
{source}
\end{{document}}
"""


def _fit_svg_size(svg: str, *, width: float, height: float) -> str:
    svg = re.sub(r"^\s*<\?xml[^>]*>\s*", "", svg)
    svg = re.sub(r"^\s*<!DOCTYPE[^>]*>\s*", "", svg)
    svg = re.sub(r'(<svg\b[^>]*?)\swidth=(["\']).*?\2', rf'\1 width="{_fmt(width)}"', svg, count=1)
    svg = re.sub(r'(<svg\b[^>]*?)\sheight=(["\']).*?\2', rf'\1 height="{_fmt(height)}"', svg, count=1)
    if "preserveAspectRatio=" not in svg.partition(">")[0]:
        svg = re.sub(r"(<svg\b[^>]*)(>)", r'\1 preserveAspectRatio="none"\2', svg, count=1)
    return svg


def _run_tikz_renderer(source: str, *, width: float, height: float) -> str:
    _required_executable("pdflatex")
    latexmk = shutil.which("latexmk")
    dvisvgm = shutil.which("dvisvgm")
    pdf2svg = shutil.which("pdf2svg")
    if dvisvgm is None and pdf2svg is None:
        raise RuntimeError("tikz primitive requires `dvisvgm` or `pdf2svg` on PATH")

    with tempfile.TemporaryDirectory(prefix="figure-agent-svg-tikz-") as tmp_name:
        tmp = Path(tmp_name)
        tex_path = tmp / "fragment.tex"
        pdf_path = tmp / "fragment.pdf"
        svg_path = tmp / "fragment.svg"
        tex_path.write_text(_tikz_document(source, width=width, height=height), encoding="utf-8")
        if latexmk:
            _run_tikz_command(
                [
                    latexmk,
                    "-pdf",
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    tex_path.name,
                ],
                cwd=tmp,
                label="latexmk",
            )
        else:
            _run_tikz_command(
                [
                    _required_executable("pdflatex"),
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-file-line-error",
                    tex_path.name,
                ],
                cwd=tmp,
                label="pdflatex",
            )
        if not pdf_path.is_file():
            raise RuntimeError("tikz primitive did not produce fragment.pdf")
        if dvisvgm:
            _run_tikz_command(
                [
                    dvisvgm,
                    "--pdf",
                    "--exact-bbox",
                    "-o",
                    str(svg_path),
                    str(pdf_path),
                ],
                cwd=tmp,
                label="dvisvgm",
            )
        else:
            _run_tikz_command([pdf2svg, str(pdf_path), str(svg_path)], cwd=tmp, label="pdf2svg")
        if not svg_path.is_file():
            raise RuntimeError("tikz primitive did not produce fragment.svg")
        svg = svg_path.read_text(encoding="utf-8").strip()
    if "<svg" not in svg:
        raise RuntimeError("tikz primitive did not return an SVG document")
    return _fit_svg_size(svg, width=width, height=height)


def _external_svg_group(
    *,
    object_id: str,
    generated_by: str,
    x: float,
    y: float,
    w: float,
    h: float,
    svg: str,
    metadata: dict[str, str] | None = None,
    overlays: str = "",
) -> str:
    metadata_attrs = ""
    for key, value in (metadata or {}).items():
        metadata_attrs += f' {key}="{_attr(value)}"'
    return f"""<g data-object-id="{object_id}" data-generated-by="{generated_by}"
        data-overlap="allow" data-bbox="{_bbox_attr(x, y, w, h)}"{metadata_attrs}>
        <g data-external-svg="true" transform="translate({_fmt(x)} {_fmt(y)})">
          {svg}
        </g>
        {overlays}
      </g>"""


def _render_semantic_overlays(fragment: dict[str, Any], x: float, y: float) -> str:
    overlays: list[str] = []
    for item in fragment.get("semantic_objects", []) or []:
        object_id = item["object_id"]
        bx, by, bw, bh = _bbox(item["bbox"])
        overlays.append(
            f"""<g data-object-id="{_attr(object_id)}" data-generated-by="tikz"
          data-overlap="allow" data-bbox="{_bbox_attr(x + bx, y + by, bw, bh)}"/>"""
        )
    for item in fragment.get("semantic_labels", []) or []:
        bx, by, bw, bh = _bbox(item["bbox"])
        overlays.append(
            _text(
                role=item.get("role", "label"),
                x=x + bx,
                y=y + by,
                w=bw,
                h=bh,
                value=item["value"],
                fill=item.get("fill", "#111827"),
                opacity=item.get("opacity"),
            )
        )
    return "\n        ".join(overlays)


def _polyline_path(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    head, *tail = points
    parts = [f"M{_fmt(head[0])} {_fmt(head[1])}"]
    parts.extend(f"L{_fmt(x)} {_fmt(y)}" for x, y in tail)
    return " ".join(parts)


def _sample_power_law(
    x0: float,
    y0: float,
    w: float,
    h: float,
    *,
    count: int = 10,
) -> list[tuple[float, float]]:
    points = []
    for idx in range(count):
        t = idx / (count - 1)
        x = x0 + w * (0.08 + 0.84 * t)
        y = y0 + h * (0.18 + 0.64 * t)
        points.append((x, y))
    return points


def _render_loglog_plot(fragment: dict[str, Any]) -> str:
    object_id = fragment.get("object_id", "discharge-loglog-plot")
    x, y, w, h = _bbox(fragment["bbox"])
    frame_x = x + w * 0.10
    frame_y = y + h * 0.12
    frame_w = w * 0.82
    frame_h = h * 0.70
    points = _sample_power_law(frame_x, frame_y, frame_w, frame_h)
    marker_paths = "\n          ".join(
        f"M{_fmt(px)} {_fmt(py)} m-4 0 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0"
        for px, py in points
    )
    power_path = _polyline_path(points)
    debye_path = (
        f"M{_fmt(frame_x + frame_w * 0.04)} {_fmt(frame_y + frame_h * 0.32)} "
        f"C{_fmt(frame_x + frame_w * 0.22)} {_fmt(frame_y + frame_h * 0.38)} "
        f"{_fmt(frame_x + frame_w * 0.42)} {_fmt(frame_y + frame_h * 0.62)} "
        f"{_fmt(frame_x + frame_w * 0.58)} {_fmt(frame_y + frame_h)} "
        f"C{_fmt(frame_x + frame_w * 0.68)} {_fmt(frame_y + frame_h * 1.08)} "
        f"{_fmt(frame_x + frame_w * 0.80)} {_fmt(frame_y + frame_h * 1.02)} "
        f"{_fmt(frame_x + frame_w * 0.86)} {_fmt(frame_y + frame_h)}"
    )
    return f"""<g data-object-id="{object_id}" data-generated-by="svg_primitives"
        data-overlap="allow" data-bbox="{_bbox_attr(x, y, w, h)}">
        <rect x="{_fmt(x)}" y="{_fmt(y)}" width="{_fmt(w)}" height="{_fmt(h)}"
          fill="#FFFFFF" stroke="#111827" stroke-width="1.2"/>
        <path d="M{_fmt(frame_x)} {_fmt(frame_y + frame_h)} L{_fmt(frame_x + frame_w)} {_fmt(frame_y + frame_h)}
                 M{_fmt(frame_x)} {_fmt(frame_y + frame_h)} L{_fmt(frame_x)} {_fmt(frame_y)}"
          fill="none" stroke="#111827" stroke-width="1.2"/>
        <path d="M{_fmt(frame_x)} {_fmt(frame_y + frame_h * 0.70)} L{_fmt(frame_x + frame_w)} {_fmt(frame_y + frame_h * 0.70)}
                 M{_fmt(frame_x)} {_fmt(frame_y + frame_h * 0.44)} L{_fmt(frame_x + frame_w)} {_fmt(frame_y + frame_h * 0.44)}
                 M{_fmt(frame_x)} {_fmt(frame_y + frame_h * 0.18)} L{_fmt(frame_x + frame_w)} {_fmt(frame_y + frame_h * 0.18)}"
          fill="none" stroke="#E5E7EB" stroke-width="0.8"/>
        <path data-object-id="power-law-curve" data-overlap="allow"
          data-bbox="{_bbox_attr(frame_x + frame_w * 0.07, frame_y + frame_h * 0.15, frame_w * 0.86, frame_h * 0.70)}"
          d="{power_path}" fill="none" stroke="#2563EB" stroke-width="2.4"/>
        <path data-object-id="debye-reference-curve" data-overlap="allow"
          data-bbox="{_bbox_attr(frame_x + frame_w * 0.04, frame_y + frame_h * 0.30, frame_w * 0.82, frame_h * 0.78)}"
          d="{debye_path}" fill="none" stroke="#6B7280" stroke-width="1.8"
          stroke-dasharray="10 8"/>
        <path data-object-id="power-law-markers" data-overlap="allow"
          data-bbox="{_bbox_attr(frame_x + frame_w * 0.06, frame_y + frame_h * 0.14, frame_w * 0.88, frame_h * 0.72)}"
          d="{marker_paths}" fill="#2563EB" stroke="#2563EB" stroke-width="0.8"/>
        {_text(role="axis_label", x=frame_x + 10, y=frame_y + 34, w=44, h=16, value="log I")}
        {_text(role="axis_label", x=frame_x + frame_w * 0.50, y=frame_y + frame_h + 38, w=42, h=16, value="log t")}
        {_text(role="label", x=frame_x + frame_w * 0.66, y=frame_y + 28, w=88, h=18, value="Power-law", fill="#2563EB")}
        {_text(role="micro", x=frame_x + frame_w * 0.67, y=frame_y + 62, w=142, h=16, value="I proportional to t^-n", fill="#2563EB")}
        {_text(role="label", x=frame_x + 50, y=frame_y + frame_h * 0.66, w=126, h=18, value="Debye reference", fill="#6B7280")}
        {_text(role="micro", x=frame_x + 50, y=frame_y + frame_h * 0.79, w=154, h=16, value="I proportional to exp(-t/tau_d)", fill="#6B7280")}
      </g>"""


def _render_polymer_chain(fragment: dict[str, Any]) -> str:
    object_id = fragment.get("object_id", "sulfur-rich-polymer-chain")
    x, y, w, h = _bbox(fragment["bbox"])
    top = y + h * 0.30
    bottom = y + h * 0.70
    step = w / 14
    points = []
    for idx in range(15):
        px = x + step * idx
        py = bottom if idx % 2 == 0 else top
        points.append((px, py))
    path = _polyline_path(points)
    sulfur_positions = [
        (x + step * 1.2, top - 18),
        (x + step * 4.0, top - 18),
        (x + step * 7.7, top - 18),
        (x + step * 10.8, top - 18),
    ]
    sulfur_labels = "\n        ".join(
        _text(role="micro", x=sx, y=sy, w=18, h=16, value="S", fill="#F97316")
        for sx, sy in sulfur_positions
    )
    return f"""<g data-object-id="{object_id}" data-generated-by="svg_primitives"
        data-overlap="allow" data-bbox="{_bbox_attr(x, y, w, h)}">
        <path d="{path}" fill="none" stroke="#111827" stroke-width="1.8"/>
        <path d="M{_fmt(x)} {_fmt(y + 10)} L{_fmt(x)} {_fmt(y + h - 10)}
                 M{_fmt(x + w)} {_fmt(y + 10)} L{_fmt(x + w)} {_fmt(y + h - 10)}"
          fill="none" stroke="#111827" stroke-width="1.2"/>
        {sulfur_labels}
        <circle data-object-id="chemical-origin-highlight" data-overlap="allow"
          data-bbox="{_bbox_attr(x + step * 2.0, y + h * 0.42, 54, 54)}"
          cx="{_fmt(x + step * 2.0 + 27)}" cy="{_fmt(y + h * 0.42 + 27)}" r="27"
          fill="none" stroke="#F97316" stroke-width="2.4"/>
        {_text(role="micro", x=x + step * 2.0 + 21, y=y + h * 0.42 + 18, w=18, h=16, value="S", fill="#F97316")}
        <path data-object-id="physical-origin-highlight" data-overlap="allow"
          data-bbox="{_bbox_attr(x + step * 9.1, y + h * 0.42, 82, 58)}"
          d="M{_fmt(x + step * 9.1)} {_fmt(y + h * 0.42 + 29)}
             C{_fmt(x + step * 9.1 + 16)} {_fmt(y + h * 0.42 - 1)}
              {_fmt(x + step * 9.1 + 66)} {_fmt(y + h * 0.42 - 1)}
              {_fmt(x + step * 9.1 + 82)} {_fmt(y + h * 0.42 + 29)}
             C{_fmt(x + step * 9.1 + 66)} {_fmt(y + h * 0.42 + 59)}
              {_fmt(x + step * 9.1 + 16)} {_fmt(y + h * 0.42 + 59)}
              {_fmt(x + step * 9.1)} {_fmt(y + h * 0.42 + 29)}"
          fill="none" stroke="#7C3AED" stroke-width="1.8" stroke-dasharray="8 6"/>
        {_text(role="micro", x=x + step * 9.1 + 24, y=y + h * 0.42 + 18, w=30, h=16, value="S-S", fill="#F97316")}
        {_text(role="label", x=x + step * 2.0 - 48, y=y + h + 22, w=122, h=18, value="chemical origin", fill="#F97316")}
        {_text(role="micro", x=x + step * 2.0 - 68, y=y + h + 52, w=158, h=16, value="electron-rich sulfur sites")}
        {_text(role="label", x=x + step * 8.5, y=y + h + 22, w=110, h=18, value="physical origin", fill="#7C3AED")}
        {_text(role="micro", x=x + step * 8.0, y=y + h + 52, w=204, h=16, value="conformational heterogeneity")}
      </g>"""


def _render_energy_band(fragment: dict[str, Any]) -> str:
    object_id = fragment.get("object_id", "unified-energy-diagram")
    x, y, w, h = _bbox(fragment["bbox"])
    band_x = x + w * 0.26
    band_w = w * 0.38
    cb_y = y + h * 0.08
    vb_y = y + h * 0.82
    band_h = h * 0.10
    axis_x = x + w * 0.14
    density_x = x + w * 0.73
    density_w = w * 0.22
    et_y = y + h * 0.36
    shallow_ys = [y + h * part for part in (0.23, 0.28, 0.34)]
    deep_ys = [y + h * part for part in (0.50, 0.56, 0.65, 0.72)]
    shallow_lines = "\n          ".join(
        f"M{_fmt(band_x + band_w * 0.18 + (idx % 2) * 24)} {_fmt(level_y)} "
        f"L{_fmt(band_x + band_w * 0.70 + (idx % 2) * 24)} {_fmt(level_y)}"
        for idx, level_y in enumerate(shallow_ys)
    )
    deep_lines = "\n          ".join(
        f"M{_fmt(band_x + band_w * 0.18 + (idx % 2) * 24)} {_fmt(level_y)} "
        f"L{_fmt(band_x + band_w * 0.70 + (idx % 2) * 24)} {_fmt(level_y)}"
        for idx, level_y in enumerate(deep_ys)
    )
    return f"""<g data-object-id="{object_id}" data-generated-by="svg_primitives"
        data-overlap="allow" data-bbox="{_bbox_attr(x, y, w, h)}">
        <path d="M{_fmt(axis_x)} {_fmt(y + h * 0.88)} L{_fmt(axis_x)} {_fmt(y + h * 0.08)}
                 M{_fmt(axis_x - 14)} {_fmt(y + h * 0.10)} L{_fmt(axis_x)} {_fmt(y + h * 0.08)} L{_fmt(axis_x + 14)} {_fmt(y + h * 0.10)}"
          fill="none" stroke="#111827" stroke-width="1.8"/>
        <rect x="{_fmt(band_x)}" y="{_fmt(cb_y)}" width="{_fmt(band_w)}"
          height="{_fmt(band_h)}" rx="4" fill="#E5E7EB" stroke="#2563EB"
          stroke-width="1.2"/>
        <rect x="{_fmt(band_x)}" y="{_fmt(vb_y)}" width="{_fmt(band_w)}"
          height="{_fmt(band_h)}" rx="4" fill="#E5E7EB" stroke="#2563EB"
          stroke-width="1.2"/>
        <path d="M{_fmt(band_x)} {_fmt(cb_y + band_h + 24)} L{_fmt(band_x + band_w * 0.86)} {_fmt(cb_y + band_h + 24)}
                 M{_fmt(band_x)} {_fmt(vb_y - 24)} L{_fmt(band_x + band_w * 0.86)} {_fmt(vb_y - 24)}
                 M{_fmt(band_x)} {_fmt(et_y)} L{_fmt(density_x + density_w)} {_fmt(et_y)}"
          fill="none" stroke="#6B7280" stroke-width="1.2" stroke-dasharray="10 8"/>
        <path d="M{_fmt(band_x)} {_fmt(et_y)} L{_fmt(band_x + band_w * 0.42)} {_fmt(et_y)}"
          fill="none" stroke="#111827" stroke-width="1.2"/>
        <g data-object-id="shallow-trap-levels" data-generated-by="svg_primitives"
          data-overlap="allow" data-bbox="{_bbox_attr(band_x + band_w * 0.15, shallow_ys[0] - 16, band_w * 0.82, shallow_ys[-1] - shallow_ys[0] + 44)}">
          <path d="{shallow_lines}" fill="none" stroke="#F97316" stroke-width="1.8"/>
          <path d="M{_fmt(band_x + band_w * 0.84)} {_fmt(shallow_ys[0] - 24)}
                   C{_fmt(band_x + band_w * 0.94)} {_fmt(shallow_ys[0] - 24)}
                    {_fmt(band_x + band_w * 0.94)} {_fmt(shallow_ys[0] - 24)}
                    {_fmt(band_x + band_w * 0.94)} {_fmt(shallow_ys[0] - 8)}
                   L{_fmt(band_x + band_w * 0.94)} {_fmt(shallow_ys[-1] + 8)}
                   C{_fmt(band_x + band_w * 0.94)} {_fmt(shallow_ys[-1] + 24)}
                    {_fmt(band_x + band_w * 0.94)} {_fmt(shallow_ys[-1] + 24)}
                    {_fmt(band_x + band_w * 0.84)} {_fmt(shallow_ys[-1] + 24)}"
            fill="none" stroke="#F97316" stroke-width="1.8"/>
          <path d="M{_fmt(band_x + band_w * 0.40)} {_fmt(sum(shallow_ys) / len(shallow_ys))}
                   m-4 0 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0"
            fill="#F97316" stroke="#F97316" stroke-width="0.8"/>
        </g>
        <g data-object-id="deep-trap-levels" data-generated-by="svg_primitives"
          data-overlap="allow" data-bbox="{_bbox_attr(band_x + band_w * 0.15, deep_ys[0] - 16, band_w * 0.82, deep_ys[-1] - deep_ys[0] + 44)}">
          <path d="{deep_lines}" fill="none" stroke="#7C3AED" stroke-width="1.8"/>
          <path d="M{_fmt(band_x + band_w * 0.84)} {_fmt(deep_ys[0] - 24)}
                   C{_fmt(band_x + band_w * 0.94)} {_fmt(deep_ys[0] - 24)}
                    {_fmt(band_x + band_w * 0.94)} {_fmt(deep_ys[0] - 24)}
                    {_fmt(band_x + band_w * 0.94)} {_fmt(deep_ys[0] - 8)}
                   L{_fmt(band_x + band_w * 0.94)} {_fmt(deep_ys[-1] + 8)}
                   C{_fmt(band_x + band_w * 0.94)} {_fmt(deep_ys[-1] + 24)}
                    {_fmt(band_x + band_w * 0.94)} {_fmt(deep_ys[-1] + 24)}
                    {_fmt(band_x + band_w * 0.84)} {_fmt(deep_ys[-1] + 24)}"
            fill="none" stroke="#7C3AED" stroke-width="1.8"/>
          <path d="M{_fmt(band_x + band_w * 0.38)} {_fmt(sum(deep_ys) / len(deep_ys))}
                   m-4 0 a4 4 0 1 0 8 0 a4 4 0 1 0 -8 0"
            fill="#7C3AED" stroke="#7C3AED" stroke-width="0.8"/>
        </g>
        <g data-object-id="trap-depth-distribution" data-generated-by="svg_primitives"
          data-overlap="allow" data-bbox="{_bbox_attr(density_x, y + h * 0.08, density_w, h * 0.80)}">
          <path d="M{_fmt(density_x)} {_fmt(y + h * 0.88)} L{_fmt(density_x + density_w)} {_fmt(y + h * 0.88)}
                   M{_fmt(density_x)} {_fmt(y + h * 0.88)} L{_fmt(density_x)} {_fmt(y + h * 0.08)}
                   M{_fmt(density_x - 14)} {_fmt(y + h * 0.10)} L{_fmt(density_x)} {_fmt(y + h * 0.08)} L{_fmt(density_x + 14)} {_fmt(y + h * 0.10)}
                   M{_fmt(density_x + density_w - 14)} {_fmt(y + h * 0.86)} L{_fmt(density_x + density_w)} {_fmt(y + h * 0.88)} L{_fmt(density_x + density_w - 14)} {_fmt(y + h * 0.90)}"
            fill="none" stroke="#111827" stroke-width="1.8"/>
          <path d="M{_fmt(density_x)} {_fmt(cb_y + band_h + 24)}
                   C{_fmt(density_x + density_w * 0.24)} {_fmt(y + h * 0.26)}
                    {_fmt(density_x + density_w * 0.86)} {_fmt(y + h * 0.28)}
                    {_fmt(density_x + density_w * 0.76)} {_fmt(y + h * 0.38)}
                   C{_fmt(density_x + density_w * 0.64)} {_fmt(y + h * 0.48)}
                    {_fmt(density_x + density_w * 0.10)} {_fmt(y + h * 0.43)}
                    {_fmt(density_x)} {_fmt(et_y)}"
            fill="none" stroke="#F97316" stroke-width="2.4"/>
          <path d="M{_fmt(density_x)} {_fmt(et_y)}
                   C{_fmt(density_x + density_w * 0.28)} {_fmt(y + h * 0.52)}
                    {_fmt(density_x + density_w * 0.96)} {_fmt(y + h * 0.58)}
                    {_fmt(density_x + density_w * 0.84)} {_fmt(y + h * 0.70)}
                   C{_fmt(density_x + density_w * 0.70)} {_fmt(y + h * 0.82)}
                    {_fmt(density_x + density_w * 0.18)} {_fmt(y + h * 0.75)}
                    {_fmt(density_x)} {_fmt(vb_y - 24)}"
            fill="none" stroke="#7C3AED" stroke-width="2.4"/>
        </g>
        {_text(role="label", x=band_x + band_w * 0.45, y=cb_y + 28, w=30, h=18, value=fragment.get("cb_label", "CB"))}
        {_text(role="label", x=band_x + band_w * 0.45, y=vb_y + 28, w=30, h=18, value=fragment.get("vb_label", "VB"))}
        {_text(role="axis_label", x=axis_x - 34, y=y + h * 0.36 - 16, w=42, h=16, value="Energy")}
        {_text(role="axis_label", x=band_x - 4, y=et_y + 12, w=24, h=16, value="E_t")}
        {_text(role="axis_label", x=axis_x - 34, y=et_y + 10, w=26, h=16, value="E_g")}
        {_text(role="label", x=band_x + band_w * 0.88, y=y + h * 0.26, w=92, h=18, value=fragment.get("shallow_label", "Shallow traps"), fill="#F97316")}
        {_text(role="label", x=band_x + band_w * 0.88, y=y + h * 0.57, w=72, h=18, value=fragment.get("deep_label", "Deep traps"), fill="#7C3AED")}
        {_text(role="axis_label", x=density_x + 14, y=y + h * 0.07, w=44, h=16, value=fragment.get("density_label", "g(E_t)"))}
        {_text(role="axis_label", x=density_x + density_w * 0.44, y=y + h * 0.91, w=24, h=16, value="E_t")}
      </g>"""


def _render_energy_band_v2(fragment: dict[str, Any]) -> str:
    object_id = fragment.get("object_id", "unified-energy-diagram")
    x, y, w, h = _bbox(fragment["bbox"])
    axis_x = x + w * 0.10
    band_x = x + w * 0.26
    band_w = w * 0.36
    density_x = x + w * 0.70
    density_w = w * 0.24
    cb_y = y + h * 0.08
    vb_y = y + h * 0.82
    band_h = h * 0.095
    gap_y = cb_y + band_h + h * 0.035
    gap_bottom = vb_y - h * 0.030
    gap_h = gap_bottom - gap_y
    et_y = y + h * 0.45
    shallow_ys = [y + h * part for part in (0.25, 0.305, 0.36)]
    deep_ys = [y + h * part for part in (0.55, 0.62, 0.70, 0.775)]
    shallow_x0 = band_x + band_w * 0.12
    shallow_x1 = band_x + band_w * 0.70
    deep_x0 = band_x + band_w * 0.12
    deep_x1 = band_x + band_w * 0.73

    shallow_lines = "\n             ".join(
        f"M{_fmt(shallow_x0 + idx * 10)} {_fmt(level_y)} "
        f"L{_fmt(shallow_x1 + idx * 10)} {_fmt(level_y)}"
        for idx, level_y in enumerate(shallow_ys)
    )
    deep_lines = "\n             ".join(
        f"M{_fmt(deep_x0 + (idx % 2) * 12)} {_fmt(level_y)} "
        f"L{_fmt(deep_x1 + (idx % 2) * 12)} {_fmt(level_y)}"
        for idx, level_y in enumerate(deep_ys)
    )
    shallow_markers = "\n             ".join(
        f"M{_fmt(shallow_x0 + band_w * 0.32)} {_fmt(level_y)} "
        "m-3 0 a3 3 0 1 0 6 0 a3 3 0 1 0 -6 0"
        for level_y in shallow_ys
    )
    deep_markers = "\n             ".join(
        f"M{_fmt(deep_x0 + band_w * 0.30)} {_fmt(level_y)} "
        "m-3 0 a3 3 0 1 0 6 0 a3 3 0 1 0 -6 0"
        for level_y in deep_ys
    )
    density_base_y = vb_y + band_h * 0.42
    density_top_y = cb_y
    density_axis_h = density_base_y - density_top_y
    shallow_curve = (
        f"M{_fmt(density_x)} {_fmt(shallow_ys[0] - h * 0.035)} "
        f"C{_fmt(density_x + density_w * 0.16)} {_fmt(shallow_ys[0] - h * 0.045)} "
        f"{_fmt(density_x + density_w * 0.72)} {_fmt(shallow_ys[1] - h * 0.065)} "
        f"{_fmt(density_x + density_w * 0.82)} {_fmt(shallow_ys[1])} "
        f"C{_fmt(density_x + density_w * 0.70)} {_fmt(shallow_ys[1] + h * 0.070)} "
        f"{_fmt(density_x + density_w * 0.18)} {_fmt(shallow_ys[-1] + h * 0.040)} "
        f"{_fmt(density_x)} {_fmt(shallow_ys[-1] + h * 0.030)}"
    )
    deep_curve = (
        f"M{_fmt(density_x)} {_fmt(deep_ys[0] - h * 0.040)} "
        f"C{_fmt(density_x + density_w * 0.24)} {_fmt(deep_ys[0] - h * 0.020)} "
        f"{_fmt(density_x + density_w * 0.92)} {_fmt(deep_ys[1] - h * 0.015)} "
        f"{_fmt(density_x + density_w * 0.86)} {_fmt(deep_ys[2])} "
        f"C{_fmt(density_x + density_w * 0.78)} {_fmt(deep_ys[-1] + h * 0.055)} "
        f"{_fmt(density_x + density_w * 0.22)} {_fmt(deep_ys[-1] + h * 0.040)} "
        f"{_fmt(density_x)} {_fmt(deep_ys[-1] + h * 0.020)}"
    )

    return f"""<g data-object-id="{object_id}" data-generated-by="energy_band_v2"
        data-overlap="allow" data-bbox="{_bbox_attr(x, y, w, h)}">
        <g data-object-id="energy-axis" data-generated-by="energy_band_v2"
          data-overlap="allow" data-bbox="{_bbox_attr(axis_x - 18, cb_y - 6, 36, vb_y + band_h - cb_y + 12)}">
          <path d="M{_fmt(axis_x)} {_fmt(vb_y + band_h)} L{_fmt(axis_x)} {_fmt(cb_y)}
                   M{_fmt(axis_x - 12)} {_fmt(cb_y + 14)}
                   L{_fmt(axis_x)} {_fmt(cb_y)} L{_fmt(axis_x + 12)} {_fmt(cb_y + 14)}"
            fill="none" stroke="#111827" stroke-width="1.8"/>
        </g>
        <rect data-object-id="band-gap-window" data-generated-by="energy_band_v2"
          data-overlap="allow" data-bbox="{_bbox_attr(band_x, gap_y, band_w, gap_h)}"
          x="{_fmt(band_x)}" y="{_fmt(gap_y)}" width="{_fmt(band_w)}"
          height="{_fmt(gap_h)}" fill="#FFFFFF" stroke="#E5E7EB"
          stroke-width="1.2" stroke-dasharray="8 8"/>
        <rect data-object-id="conduction-band" data-generated-by="energy_band_v2"
          data-overlap="allow" data-bbox="{_bbox_attr(band_x, cb_y, band_w, band_h)}"
          x="{_fmt(band_x)}" y="{_fmt(cb_y)}" width="{_fmt(band_w)}"
          height="{_fmt(band_h)}" fill="#E5E7EB" stroke="#2563EB"
          stroke-width="1.8"/>
        <rect data-object-id="valence-band" data-generated-by="energy_band_v2"
          data-overlap="allow" data-bbox="{_bbox_attr(band_x, vb_y, band_w, band_h)}"
          x="{_fmt(band_x)}" y="{_fmt(vb_y)}" width="{_fmt(band_w)}"
          height="{_fmt(band_h)}" fill="#E5E7EB" stroke="#2563EB"
          stroke-width="1.8"/>
        <path data-object-id="trap-reference-lines" data-generated-by="energy_band_v2"
          data-overlap="allow" data-bbox="{_bbox_attr(band_x, gap_y, density_x + density_w - band_x, gap_h)}"
          d="M{_fmt(band_x)} {_fmt(gap_y)} L{_fmt(density_x + density_w)} {_fmt(gap_y)}
             M{_fmt(band_x)} {_fmt(et_y)} L{_fmt(density_x + density_w)} {_fmt(et_y)}
             M{_fmt(band_x)} {_fmt(gap_bottom)} L{_fmt(density_x + density_w)} {_fmt(gap_bottom)}"
          fill="none" stroke="#6B7280" stroke-width="0.8" stroke-dasharray="10 8"/>
        <g data-object-id="shallow-trap-levels" data-generated-by="energy_band_v2"
          data-overlap="allow" data-bbox="{_bbox_attr(shallow_x0, shallow_ys[0] - 10, shallow_x1 - shallow_x0 + 44, shallow_ys[-1] - shallow_ys[0] + 20)}">
          <path d="{shallow_lines}" fill="none" stroke="#F97316" stroke-width="1.8"/>
          <path d="{shallow_markers}" fill="#F97316" stroke="#F97316" stroke-width="0.8"/>
          <path d="M{_fmt(shallow_x1 + 34)} {_fmt(shallow_ys[0] - 14)}
                   C{_fmt(shallow_x1 + 50)} {_fmt(shallow_ys[0] - 14)}
                    {_fmt(shallow_x1 + 50)} {_fmt(shallow_ys[-1] + 14)}
                    {_fmt(shallow_x1 + 34)} {_fmt(shallow_ys[-1] + 14)}"
            fill="none" stroke="#F97316" stroke-width="1.8"/>
        </g>
        <g data-object-id="deep-trap-levels" data-generated-by="energy_band_v2"
          data-overlap="allow" data-bbox="{_bbox_attr(deep_x0, deep_ys[0] - 10, deep_x1 - deep_x0 + 44, deep_ys[-1] - deep_ys[0] + 20)}">
          <path d="{deep_lines}" fill="none" stroke="#7C3AED" stroke-width="1.8"/>
          <path d="{deep_markers}" fill="#7C3AED" stroke="#7C3AED" stroke-width="0.8"/>
          <path d="M{_fmt(deep_x1 + 34)} {_fmt(deep_ys[0] - 14)}
                   C{_fmt(deep_x1 + 50)} {_fmt(deep_ys[0] - 14)}
                    {_fmt(deep_x1 + 50)} {_fmt(deep_ys[-1] + 14)}
                    {_fmt(deep_x1 + 34)} {_fmt(deep_ys[-1] + 14)}"
            fill="none" stroke="#7C3AED" stroke-width="1.8"/>
        </g>
        <g data-object-id="density-axis" data-generated-by="energy_band_v2"
          data-overlap="allow" data-bbox="{_bbox_attr(density_x - 8, density_top_y - 8, density_w + 16, density_axis_h + 24)}">
          <path d="M{_fmt(density_x)} {_fmt(density_base_y)} L{_fmt(density_x)} {_fmt(density_top_y)}
                   M{_fmt(density_x - 12)} {_fmt(density_top_y + 14)}
                   L{_fmt(density_x)} {_fmt(density_top_y)} L{_fmt(density_x + 12)} {_fmt(density_top_y + 14)}
                   M{_fmt(density_x)} {_fmt(density_base_y)}
                   L{_fmt(density_x + density_w)} {_fmt(density_base_y)}
                   M{_fmt(density_x + density_w - 14)} {_fmt(density_base_y - 12)}
                   L{_fmt(density_x + density_w)} {_fmt(density_base_y)}
                   L{_fmt(density_x + density_w - 14)} {_fmt(density_base_y + 12)}"
            fill="none" stroke="#111827" stroke-width="1.8"/>
        </g>
        <g data-object-id="trap-depth-distribution" data-generated-by="energy_band_v2"
          data-overlap="allow" data-bbox="{_bbox_attr(density_x, shallow_ys[0] - h * 0.055, density_w, deep_ys[-1] - shallow_ys[0] + h * 0.115)}">
          <path d="{shallow_curve}" fill="none" stroke="#F97316" stroke-width="2.4"/>
          <path d="{deep_curve}" fill="none" stroke="#7C3AED" stroke-width="2.4"/>
        </g>
        {_text(role="label", x=band_x + band_w * 0.42, y=cb_y + band_h * 0.33, w=30, h=18, value=fragment.get("cb_label", "CB"))}
        {_text(role="label", x=band_x + band_w * 0.42, y=vb_y + band_h * 0.33, w=30, h=18, value=fragment.get("vb_label", "VB"))}
        {_text(role="axis_label", x=axis_x - 32, y=cb_y + h * 0.28, w=42, h=16, value="Energy")}
        {_text(role="axis_label", x=band_x - 2, y=et_y + 10, w=24, h=16, value="E_t")}
        {_text(role="axis_label", x=axis_x - 30, y=et_y - 8, w=26, h=16, value="E_g")}
        {_text(role="label", x=band_x + band_w * 0.84, y=shallow_ys[1] - 10, w=92, h=18, value=fragment.get("shallow_label", "Shallow traps"), fill="#F97316")}
        {_text(role="label", x=band_x + band_w * 0.84, y=deep_ys[1] + 4, w=72, h=18, value=fragment.get("deep_label", "Deep traps"), fill="#7C3AED")}
        {_text(role="axis_label", x=density_x + 18, y=density_top_y - 26, w=44, h=16, value=fragment.get("density_label", "g(E_t)"))}
        {_text(role="axis_label", x=density_x + density_w * 0.44, y=density_base_y + 18, w=24, h=16, value="E_t")}
      </g>"""


def _render_vega_loglog_plot(fragment: dict[str, Any]) -> str:
    object_id = fragment.get("object_id", "discharge-loglog-plot")
    x, y, w, h = _bbox(fragment["bbox"])
    svg = _run_node_renderer(
        "render_vega_loglog_plot.mjs",
        {
            "width": round(w),
            "height": round(h),
            "data": fragment.get("data"),
            "x_label": fragment.get("x_label", "log t"),
            "y_label": fragment.get("y_label", "log I"),
            "colors": fragment.get("colors", ["#2563EB", "#6B7280"]),
        },
    )
    overlays = f"""
        <g data-object-id="power-law-curve" data-overlap="allow"
          data-bbox="{_bbox_attr(x + w * 0.17, y + h * 0.16, w * 0.60, h * 0.56)}"/>
        <g data-object-id="debye-reference-curve" data-overlap="allow"
          data-bbox="{_bbox_attr(x + w * 0.17, y + h * 0.30, w * 0.60, h * 0.42)}"/>
        <g data-object-id="power-law-markers" data-overlap="allow"
          data-bbox="{_bbox_attr(x + w * 0.17, y + h * 0.16, w * 0.60, h * 0.56)}"/>
        {_text(role="label", x=x + w * 0.68, y=y + h * 0.14, w=88, h=18, value="Power-law", fill="#2563EB")}
        {_text(role="micro", x=x + w * 0.68, y=y + h * 0.24, w=142, h=16, value="I proportional to t^-n", fill="#2563EB")}
        {_text(role="label", x=x + w * 0.08, y=y + h * 0.50, w=126, h=18, value="Debye reference", fill="#6B7280")}
        {_text(role="micro", x=x + w * 0.08, y=y + h * 0.60, w=154, h=16, value="I proportional to exp(-t/tau_d)", fill="#6B7280")}"""
    return _external_svg_group(
        object_id=object_id,
        generated_by="vega_loglog_plot",
        x=x,
        y=y,
        w=w,
        h=h,
        svg=svg,
        overlays=overlays,
    )


def _render_tikz(fragment: dict[str, Any]) -> str:
    object_id = fragment.get("object_id", "tikz-fragment")
    x, y, w, h = _bbox(fragment["bbox"])
    source = fragment.get("source")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("tikz primitive requires a non-empty source string")
    svg = _run_tikz_renderer(source, width=w, height=h)
    return _external_svg_group(
        object_id=object_id,
        generated_by="tikz",
        x=x,
        y=y,
        w=w,
        h=h,
        svg=svg,
        metadata={"data-renderer": "tikz"},
        overlays=_render_semantic_overlays(fragment, x, y),
    )


def _render_openchemlib_molecule(fragment: dict[str, Any]) -> str:
    object_id = fragment.get("object_id", "sulfur-rich-polymer-chain")
    x, y, w, h = _bbox(fragment["bbox"])
    smiles = str(fragment.get("smiles", "CCSCCSCC"))
    svg = _run_node_renderer(
        "render_openchemlib_molecule.mjs",
        {
            "width": round(w),
            "height": round(h),
            "smiles": smiles,
            "id": object_id,
        },
    )
    chemical_x = x + w * 0.39
    chemical_y = y + h * 0.46
    physical_x = x + w * 0.72
    physical_y = y + h * 0.46
    overlays = f"""
        <circle data-object-id="chemical-origin-highlight" data-overlap="allow"
          data-bbox="{_bbox_attr(chemical_x - 28, chemical_y - 28, 56, 56)}"
          cx="{_fmt(chemical_x)}" cy="{_fmt(chemical_y)}" r="28"
          fill="none" stroke="#F97316" stroke-width="2.4"/>
        <path data-object-id="physical-origin-highlight" data-overlap="allow"
          data-bbox="{_bbox_attr(physical_x - 44, physical_y - 30, 88, 60)}"
          d="M{_fmt(physical_x - 44)} {_fmt(physical_y)}
             C{_fmt(physical_x - 26)} {_fmt(physical_y - 30)}
              {_fmt(physical_x + 26)} {_fmt(physical_y - 30)}
              {_fmt(physical_x + 44)} {_fmt(physical_y)}
             C{_fmt(physical_x + 26)} {_fmt(physical_y + 30)}
              {_fmt(physical_x - 26)} {_fmt(physical_y + 30)}
              {_fmt(physical_x - 44)} {_fmt(physical_y)}"
          fill="none" stroke="#7C3AED" stroke-width="1.8" stroke-dasharray="8 6"/>
        {_text(role="label", x=x + 48, y=y + h + 20, w=122, h=18, value="chemical origin", fill="#F97316")}
        {_text(role="micro", x=x + 28, y=y + h + 50, w=158, h=16, value="electron-rich sulfur sites")}
        {_text(role="label", x=x + w * 0.58, y=y + h + 20, w=110, h=18, value="physical origin", fill="#7C3AED")}
        {_text(role="micro", x=x + w * 0.54, y=y + h + 50, w=204, h=16, value="conformational heterogeneity")}"""
    return _external_svg_group(
        object_id=object_id,
        generated_by="openchemlib_molecule",
        x=x,
        y=y,
        w=w,
        h=h,
        svg=svg,
        metadata={"data-source-smiles": smiles},
        overlays=overlays,
    )


RENDERERS = {
    "energy_band": _render_energy_band,
    "energy_band_v2": _render_energy_band_v2,
    "loglog_plot": _render_loglog_plot,
    "openchemlib_molecule": _render_openchemlib_molecule,
    "polymer_chain": _render_polymer_chain,
    "tikz": _render_tikz,
    "vega_loglog_plot": _render_vega_loglog_plot,
}


def render_fragment(name: str, primitive_doc: dict[str, Any]) -> str:
    """Render one named fragment from a primitive document."""
    fragments = primitive_doc.get("fragments", {}) or {}
    if name not in fragments:
        raise KeyError(f"missing primitive fragment: {name}")
    fragment = fragments[name] or {}
    kind = fragment.get("kind")
    if kind not in RENDERERS:
        raise ValueError(f"unsupported primitive kind for {name}: {kind}")
    return RENDERERS[kind](fragment)


def render_source_from_fragments(template_text: str, primitive_doc: dict[str, Any]) -> str:
    """Replace `figure-agent-fragment:<name>` comments with rendered SVG groups."""

    def replace(match: re.Match[str]) -> str:
        return render_fragment(match.group(1), primitive_doc)

    rendered = FRAGMENT_RE.sub(replace, template_text)
    unresolved = FRAGMENT_RE.findall(rendered)
    if unresolved:
        raise ValueError("unresolved fragments: " + ", ".join(unresolved))
    return rendered


def render_figure_dir(figure_dir: Path) -> Path:
    """Render source/<name>.svg from source/<name>.template.svg and primitives.yaml."""
    spec_path = figure_dir / "spec.yaml"
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    name = spec.get("name") or figure_dir.name
    template_path = figure_dir / "source" / f"{name}.template.svg"
    output_path = figure_dir / "source" / f"{name}.svg"
    primitive_doc = load_primitive_doc(figure_dir / "primitives.yaml")
    rendered = render_source_from_fragments(
        template_path.read_text(encoding="utf-8"),
        primitive_doc,
    )
    output_path.write_text(rendered, encoding="utf-8")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render SVG-first primitive fragments.")
    parser.add_argument("figure_dir", type=Path)
    args = parser.parse_args()
    try:
        out = render_figure_dir(args.figure_dir)
    except Exception as exc:
        print(f"svg_primitives.py: {exc}", file=sys.stderr)
        return 1
    print(f"OK: rendered primitive-backed semantic SVG to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
