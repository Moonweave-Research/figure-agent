"""Prepare and export semantic SVG figures.

Export preparation removes locked vtracer underlay groups and adds an explicit
white background. The final source remains semantic SVG, while vtracer remains
coordinate evidence.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections.abc import Callable, Sequence
from pathlib import Path

from PIL import Image
from svg_contract import issue_codes, validate_semantic_svg

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
RASTER_DPI = 600

Runner = Callable[..., subprocess.CompletedProcess]


def _is_underlay(elem: ET.Element) -> bool:
    return (
        elem.get("id") == "vtracer-underlay"
        or elem.get("data-role") == "coordinate-evidence"
        or elem.get("data-final-source") == "false"
    )


def _strip_underlay(elem: ET.Element) -> None:
    for child in list(elem):
        if _is_underlay(child):
            elem.remove(child)
        else:
            _strip_underlay(child)


def _has_white_background(root: ET.Element) -> bool:
    for child in list(root):
        if child.tag.endswith("rect") and child.get("id") == "figure-agent-white-background":
            return True
    return False


def _insert_white_background(root: ET.Element) -> None:
    if _has_white_background(root):
        return
    rect = ET.Element(f"{{{SVG_NS}}}rect")
    rect.set("id", "figure-agent-white-background")
    rect.set("x", "0")
    rect.set("y", "0")
    rect.set("width", "100%")
    rect.set("height", "100%")
    rect.set("fill", "#ffffff")
    root.insert(0, rect)


def prepare_semantic_svg_for_export(source_svg: Path, output_svg: Path) -> Path:
    """Write export-ready SVG with underlays stripped and white background added."""
    tree = ET.parse(source_svg)
    root = tree.getroot()
    _strip_underlay(root)
    _insert_white_background(root)
    output_svg.parent.mkdir(parents=True, exist_ok=True)
    tree.write(output_svg, encoding="utf-8", xml_declaration=True)
    return output_svg


def _run_rsvg(runner: Runner, args: Sequence[str]) -> None:
    runner(list(args), check=True)


def export_artifacts(
    figure_dir: Path,
    name: str,
    *,
    runner: Runner = subprocess.run,
) -> dict[str, Path]:
    """Export source/<name>.svg to PDF, PNG, and TIFF artifacts."""
    source_svg = figure_dir / "source" / f"{name}.svg"
    if not source_svg.is_file():
        raise FileNotFoundError(source_svg)
    spec_path = figure_dir / "spec.yaml"
    spec = {}
    if spec_path.exists():
        import yaml

        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    issues = validate_semantic_svg(source_svg, spec=spec)
    if issues:
        raise ValueError(
            "semantic SVG validation failed: " + ", ".join(issue_codes(issues))
        )

    build_dir = figure_dir / "build"
    exports_dir = figure_dir / "exports"
    build_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)

    prepared_svg = prepare_semantic_svg_for_export(source_svg, build_dir / f"{name}.export.svg")
    pdf = exports_dir / f"{name}.pdf"
    png = exports_dir / f"{name}.png"
    tif = exports_dir / f"{name}.tif"

    _run_rsvg(
        runner,
        ("rsvg-convert", "-b", "white", "-f", "pdf", "-o", str(pdf), str(prepared_svg)),
    )
    _run_rsvg(
        runner,
        (
            "rsvg-convert",
            "-b",
            "white",
            "-d",
            str(RASTER_DPI),
            "-p",
            str(RASTER_DPI),
            "-f",
            "png",
            "-o",
            str(png),
            str(prepared_svg),
        ),
    )
    with Image.open(png) as image:
        image.convert("RGB").save(tif, dpi=(RASTER_DPI, RASTER_DPI))

    return {"prepared_svg": prepared_svg, "pdf": pdf, "png": png, "tif": tif}


def main() -> int:
    parser = argparse.ArgumentParser(description="Export semantic SVG to PDF/PNG/TIFF.")
    parser.add_argument("name")
    parser.add_argument("--examples-root", type=Path, default=Path("examples"))
    args = parser.parse_args()
    try:
        artifacts = export_artifacts(args.examples_root / args.name, args.name)
    except Exception as exc:
        print(f"svg_export.py: {exc}", file=sys.stderr)
        return 1
    print(
        "OK: exported "
        + ", ".join(str(artifacts[key]) for key in ("pdf", "png", "tif"))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
