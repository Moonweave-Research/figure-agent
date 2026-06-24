"""Compare generated and polished SVGs for semantic drift."""

from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
for script_dir in reversed(
    (
        SCRIPTS_DIR,
        SCRIPTS_DIR / "checks",
        SCRIPTS_DIR / "candidates",
        SCRIPTS_DIR / "quality",
        SCRIPTS_DIR / "loop",
        SCRIPTS_DIR / "driver",
        SCRIPTS_DIR / "svg_polish",
    )
):
    sys.path.insert(0, str(script_dir))

import fixture_identity  # noqa: E402
from quality_manifest import file_sha256  # noqa: E402
from svg_path_geometry import (  # noqa: E402
    canonical_polyline,
    frechet_distance,
    shape_signature,
)

SCHEMA = "figure-agent.svg-semantic-diff.v1"
SVG_SEMANTIC_DIFF_RELATIVE_PATH = "polish/svg_semantic_diff.json"
SEMANTIC_DIFF_PASS = "pass"
SEMANTIC_DIFF_NEEDS_HUMAN = "needs_human"
SEMANTIC_DIFF_BACKPORT = "semantic_backport_required"
SEMANTIC_DIFF_INVALID = "invalid"
FINDING_KINDS = frozenset(
    {
        "text_identity_loss",
        "element_inventory_change",
        "frame_change",
        "geometry_truth_violation",
        "truth_path_removed",
        "truth_path_occluded",
        "unsupported_svg_feature",
        "group_transform_risk",
        "marker_or_path_change",
        "semantic_color_remap",
    }
)
REPORT_STATES = frozenset(
    {
        SEMANTIC_DIFF_PASS,
        SEMANTIC_DIFF_NEEDS_HUMAN,
        SEMANTIC_DIFF_BACKPORT,
        SEMANTIC_DIFF_INVALID,
    }
)
UNSUPPORTED_TAGS = frozenset({"filter", "mask", "clipPath", "foreignObject", "image"})
UNSUPPORTED_ATTRS = frozenset({"filter", "mask", "clip-path"})
TRANSFORMED_LEAF_TAGS = frozenset(
    {"text", "path", "use", "rect", "circle", "ellipse", "line", "polygon", "polyline"}
)
FRAME_ATTRS = ("viewBox", "width", "height")
OPTICAL_ATTRS = ("fill", "stroke", "opacity", "fill-opacity", "stroke-opacity")
# Mirror of svg_polish_executor.MAX_TRANSLATE_PX (imported there would be circular:
# executor -> recipe -> manifest -> svg_semantic_diff). Keep both in sync.
MAX_TRANSLATE_PX = 10.0
HAND_OVERLAY_PREFIX = "hand:"


def _strip_hand_overlay(names: list[str]) -> list[str]:
    """Drop hand:* overlay names. Added/removed hand overlays are sanctioned
    decoration (spec §6 overlay-safe), not a structural inventory change."""
    return [name for name in names if not name.startswith(HAND_OVERLAY_PREFIX)]


def _is_hand_namespaced(element_id: str | None, class_attr: str | None) -> bool:
    """An element is a hand:* overlay if its id or any class token is hand:-prefixed."""
    if element_id and element_id.startswith(HAND_OVERLAY_PREFIX):
        return True
    if class_attr:
        return any(token.startswith(HAND_OVERLAY_PREFIX) for token in class_attr.split())
    return False


OCCLUSION_OPACITY = 0.95  # effective opacity at/above which an overlay hides what's beneath
OCCLUSION_COVERAGE = 0.5  # bbox-coverage fraction of a truth path that counts as occlusion


def _float_attr(element: ET.Element, name: str, default: float) -> float:
    try:
        return float(element.attrib.get(name, default))
    except (TypeError, ValueError):
        return default


def _polyline_bbox(points: list[complex]) -> tuple[float, float, float, float]:
    xs = [point.real for point in points]
    ys = [point.imag for point in points]
    return (min(xs), min(ys), max(xs), max(ys))


def _axis_coverage(t0: float, t1: float, o0: float, o1: float) -> float:
    """Fraction of truth interval [t0,t1] covered by overlay interval [o0,o1].
    A degenerate (zero-length) truth interval is covered (1.0) iff its point lies
    within the overlay interval."""
    if t1 <= t0:
        return 1.0 if o0 <= t0 <= o1 else 0.0
    lo, hi = max(t0, o0), min(t1, o1)
    return max(0.0, hi - lo) / (t1 - t0)


def _bbox_coverage(
    overlay: tuple[float, float, float, float],
    truth: tuple[float, float, float, float],
) -> float:
    """Fraction of the truth bbox covered by the overlay bbox. Degenerate
    (zero-area, e.g. axis-aligned line) truth bboxes use per-axis point
    containment so a covered horizontal/vertical truth segment is still detected."""
    ox0, oy0, ox1, oy1 = overlay
    tx0, ty0, tx1, ty1 = truth
    return _axis_coverage(tx0, tx1, ox0, ox1) * _axis_coverage(ty0, ty1, oy0, oy1)


def _parse_points(raw: str) -> list[complex]:
    coords = [float(token) for token in re.split(r"[\s,]+", raw.strip()) if token]
    return [complex(coords[i], coords[i + 1]) for i in range(0, len(coords) - 1, 2)]


def _shape_bbox(tag: str, element: ET.Element) -> tuple[float, float, float, float] | None:
    """Axis-aligned bbox for an occlusion-capable overlay shape, from its
    attributes. Returns None for elements with no resolvable extent (e.g. <use>,
    whose bbox needs href resolution — a documented gap) or no geometry."""
    if tag == "path":
        d = element.attrib.get("d")
        return _polyline_bbox(canonical_polyline(d)) if d else None
    if tag == "rect":
        x = _float_attr(element, "x", 0.0)
        y = _float_attr(element, "y", 0.0)
        return (
            x,
            y,
            x + _float_attr(element, "width", 0.0),
            y + _float_attr(element, "height", 0.0),
        )
    if tag == "circle":
        cx, cy, r = (
            _float_attr(element, "cx", 0.0),
            _float_attr(element, "cy", 0.0),
            _float_attr(element, "r", 0.0),
        )
        return (cx - r, cy - r, cx + r, cy + r)
    if tag == "ellipse":
        cx, cy = _float_attr(element, "cx", 0.0), _float_attr(element, "cy", 0.0)
        rx, ry = _float_attr(element, "rx", 0.0), _float_attr(element, "ry", 0.0)
        return (cx - rx, cy - ry, cx + rx, cy + ry)
    if tag in ("polygon", "polyline"):
        points = _parse_points(element.attrib.get("points", ""))
        return _polyline_bbox(points) if points else None
    return None


class SvgSemanticDiffError(ValueError):
    """Expected user-facing error for SVG semantic diff reports."""


def _fixture_path(example_dir: Path, relative: str, label: str) -> Path:
    if Path(relative).is_absolute():
        raise SvgSemanticDiffError(f"{label} must be fixture-relative")
    root = example_dir.resolve()
    resolved = (example_dir / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise SvgSemanticDiffError(f"{label} must stay inside the fixture") from exc
    return resolved


def _resolve_example_dir_for_cli(value: Path) -> Path:
    if value.is_absolute():
        return value
    if value.parts and value.parts[0] == "examples":
        if len(value.parts) != 2 or ".." in value.parts:
            raise SvgSemanticDiffError("invalid fixture path: expected examples/<fixture-name>")
        _validate_fixture_name_for_cli(value.parts[1], str(value))
        return Path("examples") / value.parts[1]
    if len(value.parts) == 1:
        _validate_fixture_name_for_cli(str(value), str(value))
        examples_path = Path("examples") / value
        if examples_path.is_dir():
            return examples_path
        if value.exists():
            raise SvgSemanticDiffError(
                "invalid fixture path: relative fixture names must resolve under examples/"
            )
        return value
    raise SvgSemanticDiffError(
        "invalid fixture path: expected fixture name, examples/<fixture-name>, or an absolute path"
    )


def _validate_fixture_name_for_cli(name: str, original: str) -> None:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise SvgSemanticDiffError(f"invalid fixture path: {original}: {exc}") from exc


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SvgSemanticDiffError(f"{label} must be a mapping")
    return value


def _require_non_empty_string(data: dict[str, Any], key: str, *, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SvgSemanticDiffError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _require_sha256(value: str, label: str) -> None:
    if not value.startswith("sha256:") or len(value) != len("sha256:") + 64:
        raise SvgSemanticDiffError(f"{label} must be a sha256:<64 hex chars> string")
    suffix = value.removeprefix("sha256:")
    if any(char not in "0123456789abcdef" for char in suffix):
        raise SvgSemanticDiffError(f"{label} must be lowercase sha256 hex")


def _strip_namespace(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _multiset_difference(
    polished: list[tuple[str, str]], source: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    return list((Counter(polished) - Counter(source)).elements())


_TRANSLATE_FUNCTION = re.compile(r"translate\(\s*([^()]*?)\s*\)")


def _transform_within_executor_bounds(transform: str) -> bool:
    """True only for one-or-more translate() functions within the executor's bound.

    Mirrors svg_polish_executor's per-component MAX_TRANSLATE_PX gate so the
    sanctioned bounded-translate output passes while rotate/scale/matrix and
    over-bound translates (e.g. an undeclared off-position label) are flagged.
    """
    stripped = transform.strip()
    if not stripped:
        return False
    remainder = _TRANSLATE_FUNCTION.sub("", stripped).strip()
    if remainder:
        return False
    for match in _TRANSLATE_FUNCTION.finditer(stripped):
        components = [token for token in re.split(r"[ ,]+", match.group(1).strip()) if token]
        if len(components) not in (1, 2):
            return False
        try:
            values = [float(token) for token in components]
        except ValueError:
            return False
        if any(abs(value) > MAX_TRANSLATE_PX for value in values):
            return False
    return True


def _text_content(element: ET.Element) -> str:
    return " ".join("".join(element.itertext()).split())


def _parse_svg(path: Path) -> ET.Element:
    try:
        return ET.fromstring(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise SvgSemanticDiffError(f"invalid UTF-8 in SVG {path}: {exc}") from exc
    except ET.ParseError as exc:
        raise SvgSemanticDiffError(f"invalid SVG XML in {path}: {exc}") from exc


def _inventory(path: Path) -> dict[str, Any]:
    root = _parse_svg(path)
    texts: list[str] = []
    ids: set[str] = set()
    classes: set[str] = set()
    unsupported: list[str] = []
    group_transform_risks: list[str] = []
    transforms_by_id: dict[str, tuple[str, str]] = {}
    transforms_no_id: list[tuple[str, str]] = []
    colors_by_id: dict[str, tuple[str | None, ...]] = {}
    optical_signatures_no_id: list[tuple[str | None, ...]] = []
    path_count = 0
    marker_count = 0
    marker_attr_count = 0
    truth_geometry: dict[str, dict[str, Any]] = {}
    hand_overlays: list[dict[str, Any]] = []
    for order, element in enumerate(root.iter()):
        tag = _strip_namespace(element.tag)
        element_id = element.attrib.get("id")
        optical = tuple(element.attrib.get(attr) for attr in OPTICAL_ATTRS)
        if element_id:
            ids.add(element_id)
            colors_by_id[element_id] = optical
        elif any(value is not None for value in optical):
            optical_signatures_no_id.append(optical)
        class_attr = element.attrib.get("class")
        if class_attr:
            classes.update(token for token in class_attr.split() if token)
        if tag == "text":
            text = _text_content(element)
            if text:
                texts.append(text)
        if tag == "path":
            path_count += 1
            d = element.attrib.get("d")
            truth_bearing = element.attrib.get("data-truth-bearing") != "false"
            if d and truth_bearing and element_id:
                polyline = canonical_polyline(d)
                truth_geometry[element_id] = {
                    "signature": shape_signature(d),
                    "polyline": polyline,
                    "bbox": _polyline_bbox(polyline),
                    "order": order,
                }
        if _is_hand_namespaced(element_id, class_attr):
            overlay_bbox = _shape_bbox(tag, element)
            if overlay_bbox is not None:
                opacity = _float_attr(element, "opacity", 1.0) * _float_attr(
                    element, "fill-opacity", 1.0
                )
                hand_overlays.append(
                    {
                        "bbox": overlay_bbox,
                        "opacity": opacity,
                        "fill": element.attrib.get("fill", ""),
                        "order": order,
                    }
                )
        if tag == "marker":
            marker_count += 1
        marker_attr_count += sum(
            1 for key in ("marker-start", "marker-mid", "marker-end") if key in element.attrib
        )
        if tag in UNSUPPORTED_TAGS:
            unsupported.append(f"{tag}#{element_id or '?'}")
        for attr in UNSUPPORTED_ATTRS:
            if attr in element.attrib:
                unsupported.append(f"{tag}#{element_id or '?'}@{attr}")
        href = element.attrib.get("href") or element.attrib.get(
            "{http://www.w3.org/1999/xlink}href"
        )
        if href and re.match(r"^[a-z][a-z0-9+.-]*://", href, flags=re.IGNORECASE):
            unsupported.append(f"{tag}#{element_id or '?'}@external_href")
        if "transform" in element.attrib:
            transform = element.attrib["transform"]
            if tag == "g":
                semantic_children = sum(
                    1
                    for child in element.iter()
                    if child is not element and _strip_namespace(child.tag) in TRANSFORMED_LEAF_TAGS
                )
                if semantic_children > 1:
                    group_transform_risks.append(f"g#{element_id or '?'} transform={transform}")
                elif element_id:
                    transforms_by_id[element_id] = ("g", transform)
                else:
                    transforms_no_id.append(("g", transform))
            elif tag in TRANSFORMED_LEAF_TAGS:
                if element_id:
                    transforms_by_id[element_id] = (tag, transform)
                else:
                    transforms_no_id.append((tag, transform))
    return {
        "frame": {key: root.attrib.get(key, "") for key in FRAME_ATTRS},
        "texts": sorted(texts),
        "ids": sorted(ids),
        "classes": sorted(classes),
        "unsupported": sorted(set(unsupported)),
        "group_transform_risks": sorted(set(group_transform_risks)),
        "transforms_by_id": transforms_by_id,
        "transforms_no_id": sorted(transforms_no_id),
        "path_count": path_count,
        "marker_count": marker_count,
        "marker_attr_count": marker_attr_count,
        "colors_by_id": colors_by_id,
        "optical_signatures_no_id": sorted(
            tuple("" if value is None else value for value in optical)
            for optical in optical_signatures_no_id
        ),
        "truth_geometry": truth_geometry,
        "hand_overlays": hand_overlays,
    }


def _finding(
    index: int,
    *,
    kind: str,
    severity: str,
    evidence: str,
    recommended_route: str,
) -> dict[str, str]:
    return {
        "id": f"SD{index:03d}",
        "kind": kind,
        "severity": severity,
        "evidence": evidence,
        "recommended_route": recommended_route,
    }


def _compare(
    source: dict[str, Any], polished: dict[str, Any], *, frechet_bound: float = 0.5
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    def add(kind: str, severity: str, evidence: str, route: str) -> None:
        findings.append(
            _finding(
                len(findings) + 1,
                kind=kind,
                severity=severity,
                evidence=evidence,
                recommended_route=route,
            )
        )

    source_text_counts = Counter(source["texts"])
    polished_text_counts = Counter(polished["texts"])
    dropped_texts = source_text_counts - polished_text_counts
    for text in sorted(dropped_texts):
        add(
            "text_identity_loss",
            "BLOCKER",
            f"missing text label {text!r} "
            f"(count {source_text_counts[text]} to {polished_text_counts[text]})",
            SEMANTIC_DIFF_BACKPORT,
        )
    if source["frame"] != polished["frame"]:
        add(
            "frame_change",
            "MAJOR",
            f"frame changed from {source['frame']} to {polished['frame']}",
            SEMANTIC_DIFF_BACKPORT,
        )
    new_unsupported = sorted(set(polished["unsupported"]) - set(source["unsupported"]))
    for item in new_unsupported:
        add(
            "unsupported_svg_feature",
            "MAJOR",
            f"polished SVG introduces {item}",
            SEMANTIC_DIFF_BACKPORT,
        )
    for item in polished["group_transform_risks"]:
        add(
            "group_transform_risk",
            "MAJOR",
            item,
            SEMANTIC_DIFF_BACKPORT,
        )
    for element_id, polished_transform in sorted(polished["transforms_by_id"].items()):
        if source["transforms_by_id"].get(
            element_id
        ) != polished_transform and not _transform_within_executor_bounds(polished_transform[1]):
            tag, transform = polished_transform
            add(
                "group_transform_risk",
                "MAJOR",
                f"{tag}#{element_id} transform={transform}",
                SEMANTIC_DIFF_BACKPORT,
            )
    added_transforms_no_id = _multiset_difference(
        polished["transforms_no_id"], source["transforms_no_id"]
    )
    for tag, transform in sorted(added_transforms_no_id):
        if not _transform_within_executor_bounds(transform):
            add(
                "group_transform_risk",
                "MAJOR",
                f"{tag}#? transform={transform}",
                SEMANTIC_DIFF_BACKPORT,
            )
    if (
        source["path_count"] != polished["path_count"]
        or source["marker_count"] != polished["marker_count"]
        or source["marker_attr_count"] != polished["marker_attr_count"]
    ):
        add(
            "marker_or_path_change",
            "MINOR",
            "path/marker inventory changed "
            f"from path={source['path_count']}, marker={source['marker_count']}, "
            f"marker_attr={source['marker_attr_count']} to "
            f"path={polished['path_count']}, marker={polished['marker_count']}, "
            f"marker_attr={polished['marker_attr_count']}",
            SEMANTIC_DIFF_NEEDS_HUMAN,
        )
    removed_ids = _strip_hand_overlay(sorted(set(source["ids"]) - set(polished["ids"])))
    added_ids = _strip_hand_overlay(sorted(set(polished["ids"]) - set(source["ids"])))
    removed_classes = _strip_hand_overlay(sorted(set(source["classes"]) - set(polished["classes"])))
    added_classes = _strip_hand_overlay(sorted(set(polished["classes"]) - set(source["classes"])))
    if removed_ids or added_ids or removed_classes or added_classes:
        add(
            "element_inventory_change",
            "MINOR",
            f"ids removed={removed_ids} added={added_ids}; "
            f"classes removed={removed_classes} added={added_classes}",
            SEMANTIC_DIFF_NEEDS_HUMAN,
        )
    for element_id, source_colors in sorted(source["colors_by_id"].items()):
        polished_colors = polished["colors_by_id"].get(element_id)
        if polished_colors is not None and polished_colors != source_colors:
            add(
                "semantic_color_remap",
                "MINOR",
                f"{element_id} color/opacity changed from {source_colors} to {polished_colors}",
                SEMANTIC_DIFF_NEEDS_HUMAN,
            )
    if source["optical_signatures_no_id"] != polished["optical_signatures_no_id"]:
        add(
            "semantic_color_remap",
            "MINOR",
            "non-id color/opacity inventory changed from "
            f"{source['optical_signatures_no_id']} to "
            f"{polished['optical_signatures_no_id']}",
            SEMANTIC_DIFF_NEEDS_HUMAN,
        )
    src_geo = source.get("truth_geometry", {})
    pol_geo = polished.get("truth_geometry", {})
    for element_id, src_entry in sorted(src_geo.items()):
        pol_entry = pol_geo.get(element_id)
        if pol_entry is None:
            add(
                "truth_path_removed",
                "BLOCKER",
                f"truth path #{element_id} is gone from the polished SVG "
                "(removed, renamed, or downgraded to decorative); no overlay may "
                "replace a truth path",
                SEMANTIC_DIFF_BACKPORT,
            )
            continue
        if src_entry["signature"] != pol_entry["signature"]:
            add(
                "geometry_truth_violation",
                "BLOCKER",
                f"truth path #{element_id} shape signature changed "
                f"({src_entry['signature']} -> {pol_entry['signature']})",
                SEMANTIC_DIFF_BACKPORT,
            )
            continue
        drift = frechet_distance(src_entry["polyline"], pol_entry["polyline"])
        if drift > frechet_bound:
            add(
                "geometry_truth_violation",
                "BLOCKER",
                f"truth path #{element_id} drifted {drift:.3f} > bound {frechet_bound}",
                SEMANTIC_DIFF_BACKPORT,
            )
    truth_geo = polished.get("truth_geometry", {})
    # Occlusion is a deterministic bbox + effective-opacity + paint-order proxy.
    # Known gaps (a covering element of these forms is NOT flagged here; the
    # Plan 3 shipped-artifact pixel gate is the backstop): <use> (extent needs
    # href resolution), wide stroke-only overlays (stroke geometry not modelled),
    # and opacity from an ancestor <g> or a CSS `style=`/class (not resolved).
    # The bbox proxy also over-counts coverage for L-shaped/frame overlays
    # (errs toward over-blocking — the safe direction for a truth guard).
    for overlay in polished.get("hand_overlays", []):
        if overlay["fill"] == "none" or overlay["opacity"] < OCCLUSION_OPACITY:
            continue  # stroke-only or translucent overlay cannot hide truth
        for occluded_id, truth in sorted(truth_geo.items()):
            if overlay["order"] <= truth["order"]:
                continue  # overlay painted beneath the truth path
            if _bbox_coverage(overlay["bbox"], truth["bbox"]) >= OCCLUSION_COVERAGE:
                add(
                    "truth_path_occluded",
                    "BLOCKER",
                    f"opaque hand overlay covers >= {int(OCCLUSION_COVERAGE * 100)}% of "
                    f"truth path #{occluded_id} and is painted on top; "
                    "an overlay must not visually replace a truth path",
                    SEMANTIC_DIFF_BACKPORT,
                )
    return findings


def _summary_state(findings: list[dict[str, str]]) -> str:
    if not findings:
        return SEMANTIC_DIFF_PASS
    if any(finding["severity"] in {"BLOCKER", "MAJOR"} for finding in findings):
        return SEMANTIC_DIFF_BACKPORT
    return SEMANTIC_DIFF_NEEDS_HUMAN


def build_svg_semantic_diff_report(
    example_dir: Path,
    *,
    source_svg: str | None = None,
    polished_svg: str | None = None,
    frechet_bound: float = 0.5,
) -> Path:
    """Write a semantic SVG diff report and return its path."""
    source_rel = source_svg or f"exports/{example_dir.name}.svg"
    polished_rel = polished_svg or f"polish/{example_dir.name}.polished.svg"
    source_path = _fixture_path(example_dir, source_rel, "source_svg")
    polished_path = _fixture_path(example_dir, polished_rel, "polished_svg")
    source_inventory = _inventory(source_path)
    polished_inventory = _inventory(polished_path)
    findings = _compare(source_inventory, polished_inventory, frechet_bound=frechet_bound)
    blocker_count = sum(1 for finding in findings if finding["severity"] in {"BLOCKER", "MAJOR"})
    warning_count = len(findings) - blocker_count
    report = {
        "schema": SCHEMA,
        "fixture": example_dir.name,
        "source_svg": source_rel,
        "polished_svg": polished_rel,
        "source_svg_hash": file_sha256(source_path),
        "polished_svg_hash": file_sha256(polished_path),
        "summary": {
            "state": _summary_state(findings),
            "blocker_count": blocker_count,
            "warning_count": warning_count,
        },
        "findings": findings,
    }
    report_path = example_dir / SVG_SEMANTIC_DIFF_RELATIVE_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return report_path


def load_svg_semantic_diff_report(path: Path, *, example_dir: Path) -> dict[str, Any]:
    """Load and validate an SVG semantic diff report."""
    canonical = (example_dir / SVG_SEMANTIC_DIFF_RELATIVE_PATH).resolve()
    if path.resolve() != canonical:
        raise SvgSemanticDiffError(
            f"SVG semantic diff report path must be {SVG_SEMANTIC_DIFF_RELATIVE_PATH}"
        )
    if not path.is_file():
        raise SvgSemanticDiffError(f"missing SVG semantic diff report: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise SvgSemanticDiffError(f"invalid UTF-8 in {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SvgSemanticDiffError(f"invalid JSON in {path}: {exc}") from exc
    data = _require_mapping(data, "semantic_diff")
    if data.get("schema") != SCHEMA:
        raise SvgSemanticDiffError(f"semantic_diff.schema must be {SCHEMA}")
    fixture = _require_non_empty_string(data, "fixture", label="semantic_diff")
    if fixture != example_dir.name:
        raise SvgSemanticDiffError("semantic_diff.fixture must match fixture directory")
    _fixture_path(
        example_dir,
        _require_non_empty_string(data, "source_svg", label="semantic_diff"),
        "source_svg",
    )
    _fixture_path(
        example_dir,
        _require_non_empty_string(data, "polished_svg", label="semantic_diff"),
        "polished_svg",
    )
    for key in ("source_svg_hash", "polished_svg_hash"):
        value = _require_non_empty_string(data, key, label="semantic_diff")
        _require_sha256(value, f"semantic_diff.{key}")
    summary = _require_mapping(data.get("summary"), "semantic_diff.summary")
    state = _require_non_empty_string(summary, "state", label="semantic_diff.summary")
    if state not in REPORT_STATES:
        raise SvgSemanticDiffError("semantic_diff.summary.state is invalid")
    for key in ("blocker_count", "warning_count"):
        if not isinstance(summary.get(key), int) or summary[key] < 0:
            raise SvgSemanticDiffError(f"semantic_diff.summary.{key} must be a non-negative int")
    findings = data.get("findings")
    if not isinstance(findings, list):
        raise SvgSemanticDiffError("semantic_diff.findings must be a list")
    for index, finding in enumerate(findings):
        finding = _require_mapping(finding, f"semantic_diff.findings[{index}]")
        _require_non_empty_string(finding, "id", label=f"semantic_diff.findings[{index}]")
        kind = _require_non_empty_string(finding, "kind", label=f"semantic_diff.findings[{index}]")
        if kind not in FINDING_KINDS:
            raise SvgSemanticDiffError(f"semantic_diff.findings[{index}].kind is invalid")
        severity = _require_non_empty_string(
            finding,
            "severity",
            label=f"semantic_diff.findings[{index}]",
        )
        if severity not in {"BLOCKER", "MAJOR", "MINOR", "NIT"}:
            raise SvgSemanticDiffError(f"semantic_diff.findings[{index}].severity is invalid")
        _require_non_empty_string(finding, "evidence", label=f"semantic_diff.findings[{index}]")
        route = _require_non_empty_string(
            finding,
            "recommended_route",
            label=f"semantic_diff.findings[{index}]",
        )
        allowed_routes = {
            SEMANTIC_DIFF_BACKPORT,
            SEMANTIC_DIFF_NEEDS_HUMAN,
            "accept_simplification",
        }
        if route not in allowed_routes:
            raise SvgSemanticDiffError(
                f"semantic_diff.findings[{index}].recommended_route is invalid"
            )
    return data


def svg_semantic_diff_report_is_stale(path: Path, *, example_dir: Path) -> bool:
    """Return True when the semantic diff report hashes differ from current SVGs."""
    data = load_svg_semantic_diff_report(path, example_dir=example_dir)
    source_path = _fixture_path(example_dir, data["source_svg"], "source_svg")
    polished_path = _fixture_path(example_dir, data["polished_svg"], "polished_svg")
    return data["source_svg_hash"] != file_sha256(source_path) or data[
        "polished_svg_hash"
    ] != file_sha256(polished_path)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for rebuilding the semantic SVG diff report."""
    args = list(argv if argv is not None else sys.argv[1:])
    if args in (["-h"], ["--help"]):
        print("usage: svg_semantic_diff.py examples/<name>")
        return 0
    if len(args) != 1:
        print("usage: svg_semantic_diff.py examples/<name>", file=sys.stderr)
        return 2
    try:
        example_dir = _resolve_example_dir_for_cli(Path(args[0]))
        report_path = build_svg_semantic_diff_report(example_dir)
    except SvgSemanticDiffError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"wrote SVG semantic diff report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
