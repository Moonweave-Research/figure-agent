"""Validate and deterministically render bounded direct-SVG candidates."""

from __future__ import annotations

import copy
import hashlib
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

FORBIDDEN_ELEMENTS = {"script", "image", "foreignobject"}
GRADIENT_ELEMENTS = {"lineargradient", "radialgradient"}
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
URL_PATTERN = re.compile(r"url\(\s*([^)]*?)\s*\)", re.IGNORECASE)


class DirectSvgCandidateError(ValueError):
    """Raised when an SVG candidate or iteration receipt violates its contract."""


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_svg(path: Path) -> tuple[str, ET.Element]:
    try:
        text = path.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError, UnicodeDecodeError) as exc:
        raise DirectSvgCandidateError("svg_read_failed") from exc
    if re.search(r"<!DOCTYPE|<!ENTITY", text, flags=re.IGNORECASE):
        raise DirectSvgCandidateError("svg_doctype_forbidden")
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise DirectSvgCandidateError("svg_xml_invalid") from exc
    if _local_name(root.tag).lower() != "svg":
        raise DirectSvgCandidateError("svg_root_invalid")
    return text, root


def _validate_view_box(root: ET.Element) -> None:
    raw = root.get("viewBox")
    if raw is None:
        raise DirectSvgCandidateError("view_box_required")
    try:
        values = [float(value) for value in raw.replace(",", " ").split()]
    except ValueError as exc:
        raise DirectSvgCandidateError("view_box_invalid") from exc
    if len(values) != 4 or values[2] <= 0 or values[3] <= 0:
        raise DirectSvgCandidateError("view_box_invalid")


def _validate_urls(text: str, ids: set[str], gradient_ids: set[str]) -> None:
    for raw in URL_PATTERN.findall(text):
        value = raw.strip().strip("'\"")
        if not value.startswith("#") or value[1:] not in gradient_ids:
            raise DirectSvgCandidateError("external_url_forbidden")
    for value in re.findall(r"(?:href|src)\s*=\s*['\"]([^'\"]+)['\"]", text, re.I):
        if value.startswith("#") and value[1:] in ids:
            continue
        raise DirectSvgCandidateError("external_url_forbidden")


def validate_candidate(path: Path, *, required_ids: set[str]) -> dict[str, Any]:
    """Validate SVG editability, semantic IDs, and self-contained resources."""
    text, root = _parse_svg(path)
    _validate_view_box(root)

    ids: set[str] = set()
    group_ids: set[str] = set()
    gradient_ids: set[str] = set()
    live_text = False
    for element in root.iter():
        name = _local_name(element.tag).lower()
        if name in FORBIDDEN_ELEMENTS:
            raise DirectSvgCandidateError("forbidden_svg_element")
        element_id = element.get("id")
        if element_id:
            if element_id in ids:
                raise DirectSvgCandidateError("svg_id_duplicate")
            ids.add(element_id)
            if name == "g":
                group_ids.add(element_id)
            if name in GRADIENT_ELEMENTS:
                gradient_ids.add(element_id)
        if name == "text" and "".join(element.itertext()).strip():
            live_text = True
        for raw_name in element.attrib:
            if _local_name(raw_name).lower().startswith("on"):
                raise DirectSvgCandidateError("forbidden_svg_attribute")

    if not live_text:
        raise DirectSvgCandidateError("live_text_required")
    if not required_ids.issubset(group_ids):
        raise DirectSvgCandidateError("semantic_id_missing")
    _validate_urls(text, ids, gradient_ids)
    return {
        "view_box": root.get("viewBox"),
        "semantic_ids": sorted(required_ids),
        "source_sha256": _sha256(path),
        "publication_acceptance": "not_claimed",
    }


def begin_ledger(budget: dict[str, int], *, started_at: str) -> dict[str, Any]:
    """Create an empty bounded-iteration ledger."""
    if set(budget) != {"cycles", "wall_minutes_per_panel"} or any(
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
        for value in budget.values()
    ):
        raise DirectSvgCandidateError("iteration_budget_invalid")
    if not isinstance(started_at, str) or not started_at:
        raise DirectSvgCandidateError("started_at_required")
    return {
        "schema": "figure-agent.direct-svg-iteration-ledger.v1",
        "budget": dict(budget),
        "started_at": started_at,
        "iterations": [],
        "publication_acceptance": "not_claimed",
    }


def _validate_iteration_receipt(receipt: dict[str, Any]) -> None:
    required = {
        "cycle",
        "elapsed_minutes",
        "source_sha256",
        "render_sha256",
        "command",
        "tool_model_receipt",
        "correction_reason",
        "publication_acceptance",
    }
    if not required.issubset(receipt):
        raise DirectSvgCandidateError("iteration_receipt_incomplete")
    if not HASH_PATTERN.fullmatch(str(receipt["source_sha256"])) or not HASH_PATTERN.fullmatch(
        str(receipt["render_sha256"])
    ):
        raise DirectSvgCandidateError("iteration_hash_invalid")
    if receipt["publication_acceptance"] != "not_claimed":
        raise DirectSvgCandidateError("publication_claim_forbidden")


def record_iteration(ledger: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    """Append one receipt while enforcing the declared cycle and wall budget."""
    _validate_iteration_receipt(receipt)
    updated = copy.deepcopy(ledger)
    iterations = updated.get("iterations")
    budget = updated.get("budget")
    if not isinstance(iterations, list) or not isinstance(budget, dict):
        raise DirectSvgCandidateError("iteration_ledger_invalid")
    expected_cycle = len(iterations) + 1
    if receipt["cycle"] != expected_cycle:
        raise DirectSvgCandidateError("cycle_sequence_invalid")
    if expected_cycle > budget["cycles"]:
        raise DirectSvgCandidateError("cycle_budget_exceeded")
    elapsed = receipt["elapsed_minutes"]
    if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed < 0:
        raise DirectSvgCandidateError("elapsed_minutes_invalid")
    if elapsed > budget["wall_minutes_per_panel"]:
        raise DirectSvgCandidateError("wall_time_budget_exceeded")
    iterations.append(copy.deepcopy(receipt))
    return updated


def _normalize_png(path: Path) -> None:
    try:
        with Image.open(path) as opened:
            image = opened.convert("RGB")
            image.save(path, format="PNG")
    except (OSError, UnidentifiedImageError) as exc:
        raise DirectSvgCandidateError("render_output_invalid") from exc


def render_candidate(
    svg_path: Path,
    output_path: Path,
    *,
    width: int,
    height: int,
    fontconfig_file: Path,
) -> dict[str, Any]:
    """Render twice with isolated fontconfig and reject nondeterministic output."""
    renderer = shutil.which("rsvg-convert")
    if renderer is None:
        raise DirectSvgCandidateError("rsvg_convert_missing")
    if not svg_path.is_file() or not fontconfig_file.is_file():
        raise DirectSvgCandidateError("render_input_missing")
    if (
        not isinstance(width, int)
        or isinstance(width, bool)
        or not isinstance(height, int)
        or isinstance(height, bool)
        or width <= 0
        or height <= 0
    ):
        raise DirectSvgCandidateError("render_geometry_invalid")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    repeats = [output_path.with_suffix(f".repeat-{index}.png") for index in (1, 2)]
    env = {
        **os.environ,
        "FONTCONFIG_FILE": str(fontconfig_file.resolve()),
        "FONTCONFIG_PATH": str(fontconfig_file.parent.resolve()),
    }
    command_prefix = [
        renderer,
        "-b",
        "white",
        "-w",
        str(width),
        "-h",
        str(height),
    ]
    try:
        for repeat in repeats:
            subprocess.run(
                [*command_prefix, "-o", str(repeat), str(svg_path)],
                check=True,
                capture_output=True,
                env=env,
                text=True,
            )
            _normalize_png(repeat)
        hashes = [_sha256(repeat) for repeat in repeats]
        if hashes[0] != hashes[1]:
            raise DirectSvgCandidateError("nondeterministic_render")
        output_path.write_bytes(repeats[0].read_bytes())
    except subprocess.CalledProcessError as exc:
        raise DirectSvgCandidateError("rsvg_render_failed") from exc
    finally:
        for repeat in repeats:
            repeat.unlink(missing_ok=True)

    return {
        "source_sha256": _sha256(svg_path),
        "render_sha256": _sha256(output_path),
        "fontconfig_sha256": _sha256(fontconfig_file),
        "command": [*command_prefix, "-o", str(output_path), str(svg_path)],
        "width": width,
        "height": height,
        "publication_acceptance": "not_claimed",
    }
