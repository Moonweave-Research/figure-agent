"""Minimum artifact gates for accepted golden figure fixtures."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml
from PIL import Image

REQUIRED_PDF_LABEL_TOKENS: dict[str, tuple[tuple[str, ...], ...]] = {
    "Experiment": (("experiment",),),
    "Mathematical interpretation": (("mathematical", "interpretation"),),
    "Molecular origin": (("molecular", "origin"),),
    "I(t)": (("i", "t"),),
    "slope": (("slope",),),
    "Discharge": (("discharge",),),
    "Debye": (("debye",),),
    "tau_d": (("tau", "d"),),
    "n": (("n",),),
    "g(E_t)": (("g", "e", "t"), ("g", "et")),
    "shallow": (("shallow",),),
    "deep": (("deep",),),
    "localized traps": (("localized", "traps"),),
    "S-rich segments": (("s", "rich", "segments"),),
    "chemical origin": (("chemical", "origin"),),
    "physical origin": (("physical", "origin"),),
    "converged trap-depth picture": (("converged", "trap", "depth", "picture"),),
    "Energy": (("energy",),),
    "CB": (("cb",),),
    "VB": (("vb",),),
    "E_t": (("e", "t"), ("et",)),
}

VISIBLE_SVG_TAGS = frozenset(
    {"circle", "ellipse", "line", "path", "polygon", "polyline", "rect", "text", "use"}
)
IGNORED_SVG_SUBTREES = frozenset({"defs", "desc", "metadata", "style", "title"})
MIN_SOURCE_INVENTORY = {
    "separator_lines": 2,
    "band_boxes": 2,
    "distribution_lobes": 2,
    "trap_levels": 8,
    "sulfur_markers": 10,
}


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def normalize_pdf_text(text: str) -> str:
    replacements = {
        "α": " alpha ",
        "τ": " tau ",
        "∝": " propto ",
        "−": "-",
        "–": "-",
        "—": "-",
        "_": " ",
        "-": " ",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return " ".join(re.findall(r"[a-zA-Z0-9]+", text.lower()))


def _contains_tokens(normalized_text: str, tokens: tuple[str, ...]) -> bool:
    haystack = f" {normalized_text} "
    return all(f" {token.lower()} " in haystack for token in tokens)


def missing_pdf_labels(
    text: str, required: dict[str, tuple[tuple[str, ...], ...]] | None = None
) -> list[str]:
    if required is None:
        required = REQUIRED_PDF_LABEL_TOKENS
    normalized = normalize_pdf_text(text)
    return [
        label
        for label, alternatives in required.items()
        if not any(_contains_tokens(normalized, tokens) for tokens in alternatives)
    ]


def extract_pdf_text(pdf_path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext failed for {pdf_path}: {result.stderr}")
    return result.stdout


def count_svg_visible_elements(svg_path: Path) -> int:
    root = ET.parse(svg_path).getroot()

    def visit(element: ET.Element, ignored: bool = False) -> int:
        local = _local_name(element.tag)
        ignored = ignored or local in IGNORED_SVG_SUBTREES
        count = 0
        if not ignored and local in VISIBLE_SVG_TAGS:
            count += 1
        for child in element:
            count += visit(child, ignored)
        return count

    return visit(root)


def png_has_white_opaque_corners(png_path: Path, tolerance: int = 8) -> bool:
    with Image.open(png_path) as image:
        rgba = image.convert("RGBA")
        width, height = rgba.size
        if width < 2 or height < 2:
            return False
        corners = ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))
        for point in corners:
            red, green, blue, alpha = rgba.getpixel(point)
            if alpha != 255:
                return False
            if any(channel < 255 - tolerance for channel in (red, green, blue)):
                return False
    return True


def fixture_is_accepted(spec_path: Path) -> bool:
    if not spec_path.exists():
        return False
    data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return False
    return data.get("accepted") is True


def source_inventory_counts(tex: str) -> dict[str, int]:
    counts = {
        "separator_lines": len(re.findall(r"\\draw\[sep\]", tex)),
        "band_boxes": len(re.findall(r"\\BandBox\b", tex)),
        "distribution_lobes": len(re.findall(r"\\SmallLobe\b", tex)),
        "trap_levels": len(re.findall(r"\\TrapLevel\b", tex)),
        "sulfur_markers": 0,
    }
    foreach_pattern = re.compile(r"\\foreach\s+\\x/\\y\s+in\s+\{(?P<items>[^}]*)\}")
    for match in foreach_pattern.finditer(tex):
        body_preview = tex[match.end() : match.end() + 300]
        if "text=cAmber" not in body_preview or "{S}" not in body_preview:
            continue
        items = [item.strip() for item in match.group("items").split(",") if item.strip()]
        counts["sulfur_markers"] += len(items)
    return counts


def source_inventory_failures(tex_path: Path) -> list[str]:
    counts = source_inventory_counts(tex_path.read_text(encoding="utf-8"))
    failures = []
    for name, minimum in MIN_SOURCE_INVENTORY.items():
        value = counts.get(name, 0)
        if value < minimum:
            failures.append(f"source inventory too low: {name} {value} < {minimum}")
    return failures


def audit_is_fresh(example_dir: Path, source_paths: tuple[Path, ...]) -> bool:
    audit = example_dir / "QUALITY_AUDIT.md"
    if not audit.exists():
        return False
    audit_mtime = audit.stat().st_mtime
    return all(path.exists() and path.stat().st_mtime <= audit_mtime for path in source_paths)


def checker_warning_counts(audit_text: str) -> tuple[int | None, int | None]:
    collision_match = re.search(r"(\d+)\s+collision\(s\)", audit_text)
    clash_match = re.search(r"(\d+)\s+visual clash candidate\(s\)", audit_text)
    if collision_match:
        collisions = int(collision_match.group(1))
    elif "OK: no collisions found" in audit_text:
        collisions = 0
    else:
        collisions = None
    visual_clashes = int(clash_match.group(1)) if clash_match else None
    return collisions, visual_clashes


def unresolved_visual_clash_count(audit_text: str) -> int | None:
    match = re.search(r"(\d+)\s+unresolved visual clash\(es\)", audit_text)
    return int(match.group(1)) if match else None


def checker_budget_failures(
    audit_path: Path, *, max_collisions: int, max_visual_clashes: int
) -> list[str]:
    if not audit_path.exists():
        return ["missing audit: QUALITY_AUDIT.md"]
    audit_text = audit_path.read_text(encoding="utf-8")
    collisions, visual_clashes = checker_warning_counts(audit_text)
    unresolved_visual_clashes = unresolved_visual_clash_count(audit_text)
    failures = []
    if collisions is None:
        failures.append("missing collision count in QUALITY_AUDIT.md")
    elif collisions > max_collisions:
        failures.append(f"collision budget exceeded: {collisions} > {max_collisions}")
    if visual_clashes is None:
        failures.append("missing visual clash count in QUALITY_AUDIT.md")
    if unresolved_visual_clashes is None:
        failures.append("missing unresolved visual clash count in QUALITY_AUDIT.md")
    elif unresolved_visual_clashes > max_visual_clashes:
        failures.append(
            "unresolved visual clash budget exceeded: "
            f"{unresolved_visual_clashes} > {max_visual_clashes}"
        )
    return failures


def check_example(
    example_dir: Path,
    *,
    min_svg_elements: int = 40,
    min_png_width: int = 1000,
    require_accepted: bool = False,
    max_collisions: int = 0,
    max_visual_clashes: int = 0,
) -> list[str]:
    name = example_dir.name
    exports = example_dir / "exports"
    spec = example_dir / "spec.yaml"
    tex = example_dir / f"{name}.tex"
    briefing = example_dir / "briefing.md"
    audit = example_dir / "QUALITY_AUDIT.md"
    pdf = exports / f"{name}.pdf"
    svg = exports / f"{name}.svg"
    png = exports / f"{name}.png"
    failures: list[str] = []

    for path in (pdf, svg, png):
        if not path.exists():
            failures.append(f"missing artifact: {path}")
    if failures:
        return failures

    missing = missing_pdf_labels(extract_pdf_text(pdf))
    if missing:
        failures.append(f"missing rendered PDF labels: {', '.join(missing)}")

    svg_count = count_svg_visible_elements(svg)
    if svg_count < min_svg_elements:
        failures.append(f"SVG has too few visible elements: {svg_count} < {min_svg_elements}")

    with Image.open(png) as image:
        width, _height = image.size
    if width < min_png_width:
        failures.append(f"PNG width too small: {width} < {min_png_width}")
    if not png_has_white_opaque_corners(png):
        failures.append("PNG corners are not opaque white")

    if require_accepted:
        if not fixture_is_accepted(spec):
            failures.append("fixture is not marked accepted: true")
        failures.extend(source_inventory_failures(tex))
        if not audit_is_fresh(example_dir, (spec, briefing, tex, pdf, svg, png)):
            failures.append("QUALITY_AUDIT.md is stale or missing")
        failures.extend(
            checker_budget_failures(
                audit,
                max_collisions=max_collisions,
                max_visual_clashes=max_visual_clashes,
            )
        )

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("example_dir", type=Path)
    parser.add_argument("--min-svg-elements", type=int, default=40)
    parser.add_argument("--min-png-width", type=int, default=1000)
    parser.add_argument("--require-accepted", action="store_true")
    parser.add_argument("--max-collisions", type=int, default=0)
    parser.add_argument("--max-visual-clashes", type=int, default=0)
    args = parser.parse_args()

    failures = check_example(
        args.example_dir,
        min_svg_elements=args.min_svg_elements,
        min_png_width=args.min_png_width,
        require_accepted=args.require_accepted,
        max_collisions=args.max_collisions,
        max_visual_clashes=args.max_visual_clashes,
    )
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print(f"OK: golden artifact gates passed for {args.example_dir.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
