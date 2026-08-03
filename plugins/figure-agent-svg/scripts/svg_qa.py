"""QA helpers for SVG-first paper figures."""

from __future__ import annotations

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml
from PIL import Image, ImageChops
from svg_contract import issue_codes, validate_semantic_svg


def _norm(text: str) -> str:
    return " ".join(text.split())


def extract_svg_text(svg_path: Path) -> list[str]:
    """Return normalized visible SVG text node content."""
    root = ET.parse(svg_path).getroot()
    labels: list[str] = []
    for elem in root.iter():
        if elem.tag.endswith("text"):
            text = _norm("".join(elem.itertext()))
            if text:
                labels.append(text)
    return labels


def missing_required_labels(svg_path: Path, required_labels: list[str]) -> list[str]:
    present = set(extract_svg_text(svg_path))
    return [label for label in required_labels if label not in present]


def pdf_font_issues_from_pdffonts(output: str) -> list[str]:
    """Return font embedding/unicode issues from `pdffonts` output."""
    issues: list[str] = []
    for line in output.splitlines():
        if not line.strip() or line.startswith("name ") or line.startswith("-"):
            continue
        fields = line.split()
        if len(fields) < 8:
            continue
        name = fields[0]
        embedded = fields[-5]
        unicode_map = fields[-3]
        if embedded != "yes":
            issues.append(f"font not embedded: {name}")
        if unicode_map != "yes":
            issues.append(f"font lacks unicode map: {name}")
    return issues


def pdf_text_missing_labels(pdf_text: str, required_labels: list[str]) -> list[str]:
    normalized = " ".join(pdf_text.split())
    return [label for label in required_labels if " ".join(label.split()) not in normalized]


def pdf_font_issues(pdf_path: Path) -> list[str]:
    result = subprocess.run(
        ["pdffonts", str(pdf_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return pdf_font_issues_from_pdffonts(result.stdout)


def missing_pdf_required_labels(pdf_path: Path, required_labels: list[str]) -> list[str]:
    result = subprocess.run(
        ["pdftotext", str(pdf_path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return pdf_text_missing_labels(result.stdout, required_labels)


def has_white_background(png_path: Path, *, tolerance: int = 250) -> bool:
    """Check that PNG corners are opaque white."""
    with Image.open(png_path) as image:
        rgba = image.convert("RGBA")
        width, height = rgba.size
        corners = [
            rgba.getpixel((0, 0)),
            rgba.getpixel((width - 1, 0)),
            rgba.getpixel((0, height - 1)),
            rgba.getpixel((width - 1, height - 1)),
        ]
    return all(
        a == 255 and r >= tolerance and g >= tolerance and b >= tolerance
        for r, g, b, a in corners
    )


def visual_diff_fraction(reference_png: Path, candidate_png: Path, *, tolerance: int = 0) -> float:
    """Return fraction of pixels changed beyond per-channel tolerance."""
    with Image.open(reference_png) as ref_raw, Image.open(candidate_png) as cand_raw:
        ref = ref_raw.convert("RGB")
        cand = cand_raw.convert("RGB")
        if cand.size != ref.size:
            cand = cand.resize(ref.size)
        diff = ImageChops.difference(ref, cand)
        pixels = (
            diff.get_flattened_data()
            if hasattr(diff, "get_flattened_data")
            else diff.getdata()
        )
        changed = 0
        for pixel in pixels:
            if max(pixel) > tolerance:
                changed += 1
        width, height = ref.size
    return changed / (width * height)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SVG-first QA checks.")
    parser.add_argument("source_svg", type=Path)
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--pdf", type=Path)
    parser.add_argument("--png", type=Path)
    parser.add_argument("--reference-png", type=Path)
    parser.add_argument("--required-label", action="append", default=[])
    parser.add_argument("--max-diff", type=float)
    parser.add_argument("--diff-tolerance", type=int)
    args = parser.parse_args()

    failures: list[str] = []
    spec = {}
    if args.spec and args.spec.exists():
        spec = yaml.safe_load(args.spec.read_text(encoding="utf-8")) or {}
    visual_diff_spec = spec.get("visual_diff", {}) or {}
    diff_tolerance = args.diff_tolerance
    if diff_tolerance is None:
        diff_tolerance = int(visual_diff_spec.get("tolerance", 0) or 0)
    required_labels = list(
        dict.fromkeys([*(spec.get("required_labels", []) or []), *args.required_label])
    )
    contract_issues = validate_semantic_svg(args.source_svg, spec=spec)
    if contract_issues:
        failures.append("semantic contract: " + ", ".join(issue_codes(contract_issues)))
    missing = missing_required_labels(args.source_svg, required_labels)
    if missing:
        failures.append(f"missing labels: {', '.join(missing)}")
    if args.pdf:
        try:
            font_issues = pdf_font_issues(args.pdf)
            if font_issues:
                failures.append("PDF fonts: " + ", ".join(font_issues))
            missing_pdf_labels = missing_pdf_required_labels(args.pdf, required_labels)
            if missing_pdf_labels:
                failures.append("PDF missing labels: " + ", ".join(missing_pdf_labels))
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            failures.append(f"PDF QA unavailable or failed: {exc}")
    if args.png and not has_white_background(args.png):
        failures.append("PNG background is not opaque white")
    if args.reference_png and args.png and args.max_diff is not None:
        diff = visual_diff_fraction(args.reference_png, args.png, tolerance=diff_tolerance)
        if diff > args.max_diff:
            failures.append(f"visual diff {diff:.6f} exceeds max {args.max_diff:.6f}")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("OK: SVG QA passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
