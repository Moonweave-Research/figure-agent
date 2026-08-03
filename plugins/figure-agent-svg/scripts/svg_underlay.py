"""Create a locked vtracer underlay SVG from a reference or draft image.

The underlay is coordinate evidence only. It is deliberately marked as
non-final so export code and human reviewers can distinguish it from the
semantic SVG source layer.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections.abc import Callable
from pathlib import Path

import yaml

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

Converter = Callable[..., None]


def _default_converter() -> Converter:
    try:
        import vtracer
    except ImportError as exc:
        raise RuntimeError(
            "vtracer is not importable. Install/enable vtracer for underlay extraction; "
            "do not use bitmap tracing as final source."
        ) from exc
    return vtracer.convert_image_to_svg_py


def _copy_canvas_attributes(raw_root: ET.Element, target_root: ET.Element) -> None:
    for key in ("width", "height", "viewBox"):
        value = raw_root.get(key)
        if value:
            target_root.set(key, value)


def create_locked_underlay(
    reference_path: Path,
    output_path: Path,
    *,
    converter: Converter | None = None,
    reference_label: str | None = None,
) -> Path:
    """Vectorize `reference_path` and write a locked coordinate-evidence SVG."""
    if not reference_path.is_file():
        raise FileNotFoundError(reference_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    converter = converter or _default_converter()

    with tempfile.TemporaryDirectory() as tmp_str:
        raw_path = Path(tmp_str) / "raw_vtracer.svg"
        converter(
            str(reference_path),
            str(raw_path),
            colormode="color",
            hierarchical="stacked",
            mode="spline",
            filter_speckle=4,
            color_precision=6,
            layer_difference=16,
            corner_threshold=60,
            length_threshold=4.0,
            max_iterations=10,
            splice_threshold=45,
            path_precision=3,
        )
        raw_root = ET.parse(raw_path).getroot()

    root = ET.Element(f"{{{SVG_NS}}}svg")
    _copy_canvas_attributes(raw_root, root)
    root.set("data-figure-agent", "svg-first")
    root.set("data-role", "coordinate-evidence")
    root.set("data-generator", "vtracer")
    root.set("data-final-source", "false")

    title = ET.SubElement(root, f"{{{SVG_NS}}}title")
    title.text = "Locked vtracer coordinate underlay, not final editable source"
    group = ET.SubElement(root, f"{{{SVG_NS}}}g")
    group.set("id", "vtracer-underlay")
    group.set("data-role", "coordinate-evidence")
    group.set("data-locked", "true")
    group.set("data-final-source", "false")
    group.set("data-reference", reference_label or str(reference_path))

    for child in list(raw_root):
        group.append(child)

    ET.ElementTree(root).write(output_path, encoding="utf-8", xml_declaration=True)
    return output_path


def create_locked_underlay_from_spec(
    figure_dir: Path,
    *,
    converter: Converter | None = None,
) -> Path:
    """Resolve spec.yaml.reference_image and write underlay/<name>.underlay.svg."""
    spec_path = figure_dir / "spec.yaml"
    if not spec_path.is_file():
        raise FileNotFoundError(spec_path)
    spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
    name = spec.get("name") or figure_dir.name
    reference = spec.get("reference_image")
    if not isinstance(reference, str) or not reference.strip():
        raise ValueError(f"{spec_path} must declare reference_image")
    reference = reference.strip()
    return create_locked_underlay(
        figure_dir / reference,
        figure_dir / "underlay" / f"{name}.underlay.svg",
        converter=converter,
        reference_label=reference,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Create locked vtracer underlay SVG.")
    parser.add_argument("reference_image", nargs="?", type=Path)
    parser.add_argument("output_svg", nargs="?", type=Path)
    parser.add_argument(
        "--from-spec",
        type=Path,
        help="figure directory containing spec.yaml.reference_image",
    )
    args = parser.parse_args()
    try:
        if args.from_spec is not None:
            out = create_locked_underlay_from_spec(args.from_spec)
        elif args.reference_image is not None and args.output_svg is not None:
            out = create_locked_underlay(args.reference_image, args.output_svg)
        else:
            parser.error("pass reference_image output_svg, or --from-spec examples/<name>")
    except Exception as exc:
        print(f"svg_underlay.py: {exc}", file=sys.stderr)
        return 1
    print(f"OK: wrote locked vtracer underlay to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
