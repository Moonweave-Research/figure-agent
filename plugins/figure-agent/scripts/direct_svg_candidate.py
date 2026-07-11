"""Validate and deterministically render bounded direct-SVG candidates."""

from __future__ import annotations

import copy
import hashlib
import os
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path, PurePosixPath
from typing import Any

import yaml
from PIL import Image, UnidentifiedImageError

FORBIDDEN_ELEMENTS = {"script", "image", "foreignobject"}
GRADIENT_ELEMENTS = {"lineargradient", "radialgradient"}
HASH_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
URL_PATTERN = re.compile(r"url\(\s*([^)]*?)\s*\)", re.IGNORECASE)
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
UNAVAILABLE_PRECOMMIT = "unavailable_precommit"
RENDER_COMMAND_PREFIX = ["uv", "run", "python", "scripts/direct_svg_render.py"]
RENDER_COMMAND_FLAGS = {
    "--root",
    "--svg",
    "--output",
    "--semantic-packet",
    "--panel",
    "--width",
    "--height",
    "--fontconfig",
    "--font",
    "--validation-mode",
}


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


def _semantic_text(element: ET.Element) -> str:
    explicit = element.get("data-semantic-text")
    if explicit:
        return explicit
    parts = [element.text or ""]
    for child in element:
        shift = child.get("baseline-shift")
        if shift == "sub":
            parts.append("_")
        elif shift == "super":
            parts.append("^")
        parts.append("".join(child.itertext()))
        parts.append(child.tail or "")
    return "".join(parts).strip()


def _semantic_text_key(value: str) -> str:
    return re.sub(r"[\s_^]", "", value.replace("µ", "μ"))


def semantic_requirements(path: Path, *, panel: str) -> dict[str, set[Any]]:
    """Derive candidate IDs, live text, and declared relations from authority."""
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise DirectSvgCandidateError("semantic_packet_invalid") from exc
    if not isinstance(loaded, dict) or loaded.get("schema") != (
        "figure-agent.direct-svg-semantic-packet.v1"
    ):
        raise DirectSvgCandidateError("semantic_packet_invalid")
    if panel not in {"C", "F"} or panel not in loaded.get("panels", []):
        raise DirectSvgCandidateError("semantic_panel_invalid")

    panel_key = f"panel_{panel.lower()}"
    scientific_objects = loaded.get("scientific_objects", {}).get(panel_key)
    visual_roles = loaded.get("visual_roles", {}).get(panel_key)
    text_content = loaded.get("text_content", {}).get(panel_key)
    relations = loaded.get("object_relations")
    if (
        not isinstance(scientific_objects, list)
        or not isinstance(visual_roles, dict)
        or not isinstance(text_content, list)
        or not isinstance(relations, list)
    ):
        raise DirectSvgCandidateError("semantic_packet_invalid")

    object_ids = {
        item.get("id")
        for item in scientific_objects
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    role_ids = {key for key in visual_roles if isinstance(key, str)}
    required_text = {item for item in text_content if isinstance(item, str)}
    declared_relations = {
        (item.get("subject"), item.get("predicate"), item.get("object"))
        for item in relations
        if isinstance(item, dict)
        and all(isinstance(item.get(key), str) for key in ("subject", "predicate", "object"))
        and item.get("subject") in object_ids
    }
    if len(object_ids) != len(scientific_objects) or len(required_text) != len(text_content):
        raise DirectSvgCandidateError("semantic_packet_invalid")
    return {
        "required_ids": object_ids | role_ids,
        "required_text": required_text,
        "relations": declared_relations,
    }


def validate_candidate(
    path: Path,
    *,
    required_ids: set[str],
    required_text: set[str] | None = None,
) -> dict[str, Any]:
    """Validate SVG editability, semantic IDs, and self-contained resources."""
    text, root = _parse_svg(path)
    _validate_view_box(root)

    ids: set[str] = set()
    group_ids: set[str] = set()
    gradient_ids: set[str] = set()
    live_text = False
    semantic_text: set[str] = set()
    semantic_group_text: set[str] = set()
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
            semantic_text.add(_semantic_text(element))
        if name == "g":
            grouped = "".join(
                "".join(descendant.itertext()).strip()
                for descendant in element.iter()
                if _local_name(descendant.tag).lower() == "text"
            )
            if grouped:
                semantic_group_text.add(grouped)
        for raw_name in element.attrib:
            if _local_name(raw_name).lower().startswith("on"):
                raise DirectSvgCandidateError("forbidden_svg_attribute")

    if not live_text:
        raise DirectSvgCandidateError("live_text_required")
    if not required_ids.issubset(group_ids):
        raise DirectSvgCandidateError("semantic_id_missing")
    if required_text is not None:
        observed_keys = {_semantic_text_key(value) for value in semantic_text | semantic_group_text}
        if any(_semantic_text_key(value) not in observed_keys for value in required_text):
            raise DirectSvgCandidateError("semantic_text_missing")
    _validate_urls(text, ids, gradient_ids)
    return {
        "view_box": root.get("viewBox"),
        "semantic_ids": sorted(required_ids),
        "source_sha256": _sha256(path),
        "publication_acceptance": "not_claimed",
    }


def validate_candidate_from_semantic_packet(
    path: Path,
    semantic_packet: Path,
    *,
    panel: str,
) -> dict[str, Any]:
    """Validate candidate structure against the declared semantic authority."""
    requirements = semantic_requirements(semantic_packet, panel=panel)
    result = validate_candidate(
        path,
        required_ids=requirements["required_ids"],
        required_text=requirements["required_text"],
    )
    _, root = _parse_svg(path)
    relation_keys = ("data-subject", "data-predicate", "data-object")
    validated_relations: set[tuple[str, str, str]] = set()
    for element in root.iter():
        values = tuple(element.get(key) for key in relation_keys)
        if not any(value is not None for value in values):
            continue
        if any(value is None for value in values):
            raise DirectSvgCandidateError("semantic_relation_incomplete")
        if values not in requirements["relations"]:
            raise DirectSvgCandidateError("semantic_relation_undeclared")
        validated_relations.add(values)
    if validated_relations != requirements["relations"]:
        raise DirectSvgCandidateError("semantic_relation_missing")
    result["semantic_packet_sha256"] = _sha256(semantic_packet)
    result["semantic_text"] = sorted(requirements["required_text"])
    result["validated_relations"] = [list(item) for item in sorted(validated_relations)]
    return result


def begin_ledger(budget: dict[str, int], *, started_at: str, panel: str) -> dict[str, Any]:
    """Create an empty bounded-iteration ledger."""
    if set(budget) != {"cycles", "wall_minutes_per_panel"} or any(
        not isinstance(value, int) or isinstance(value, bool) or value <= 0
        for value in budget.values()
    ):
        raise DirectSvgCandidateError("iteration_budget_invalid")
    if not isinstance(started_at, str) or not started_at:
        raise DirectSvgCandidateError("started_at_required")
    if panel not in {"C", "F"}:
        raise DirectSvgCandidateError("iteration_panel_invalid")
    return {
        "schema": "figure-agent.direct-svg-iteration-ledger.v1",
        "panel": panel,
        "budget": dict(budget),
        "started_at": started_at,
        "iterations": [],
        "publication_acceptance": "not_claimed",
    }


def _is_relative_posix_path(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and value == path.as_posix()


def _require_closed_keys(value: Any, expected: set[str], error: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != expected:
        raise DirectSvgCandidateError(error)
    return value


def _validate_runtime_receipt(runtime: Any, receipt: dict[str, Any]) -> dict[str, Any]:
    runtime = _require_closed_keys(
        runtime,
        {
            "schema",
            "path_base",
            "validation_mode",
            "source_path",
            "source_sha256",
            "render_path",
            "render_sha256",
            "semantic_packet",
            "fontconfig",
            "font",
            "rsvg",
            "python",
            "pillow",
            "environment",
            "producer",
            "width",
            "height",
            "publication_acceptance",
        },
        "iteration_runtime_receipt_invalid",
    )
    if (
        runtime["schema"] != "figure-agent.direct-svg-runtime-receipt.v1"
        or runtime["path_base"] != "plugin_root"
    ):
        raise DirectSvgCandidateError("iteration_runtime_receipt_invalid")
    if runtime["validation_mode"] not in {
        "declared_relation_coverage",
        "historical_structure_replay",
    }:
        raise DirectSvgCandidateError("iteration_runtime_receipt_invalid")
    if runtime["publication_acceptance"] != "not_claimed":
        raise DirectSvgCandidateError("publication_claim_forbidden")
    if any(not _is_relative_posix_path(runtime[key]) for key in ("source_path", "render_path")):
        raise DirectSvgCandidateError("iteration_path_invalid")
    if any(
        runtime[key] != receipt[key]
        for key in ("source_path", "source_sha256", "render_path", "render_sha256")
    ):
        raise DirectSvgCandidateError("iteration_runtime_mismatch")
    for name in ("semantic_packet", "fontconfig", "font"):
        item = _require_closed_keys(
            runtime[name], {"path", "sha256"}, "iteration_runtime_receipt_invalid"
        )
        if not _is_relative_posix_path(item["path"]) or not HASH_PATTERN.fullmatch(
            str(item["sha256"])
        ):
            raise DirectSvgCandidateError("iteration_runtime_receipt_invalid")
    if runtime["semantic_packet"]["sha256"] != receipt["semantic_packet_sha256"]:
        raise DirectSvgCandidateError("iteration_runtime_mismatch")
    rsvg = _require_closed_keys(
        runtime["rsvg"], {"executable", "version"}, "iteration_runtime_receipt_invalid"
    )
    if (
        rsvg["executable"] != "rsvg-convert"
        or not isinstance(rsvg["version"], str)
        or not rsvg["version"]
    ):
        raise DirectSvgCandidateError("iteration_runtime_receipt_invalid")
    python = _require_closed_keys(
        runtime["python"], {"implementation", "version"}, "iteration_runtime_receipt_invalid"
    )
    pillow = _require_closed_keys(
        runtime["pillow"], {"version"}, "iteration_runtime_receipt_invalid"
    )
    environment = _require_closed_keys(
        runtime["environment"],
        {"FONTCONFIG_FILE", "FONTCONFIG_PATH", "LANG", "LC_ALL"},
        "iteration_runtime_receipt_invalid",
    )
    producer = _require_closed_keys(
        runtime["producer"],
        {
            "wrapper_path",
            "wrapper_sha256",
            "validator_path",
            "validator_sha256",
            "lock_path",
            "lock_sha256",
            "base_commit",
            "head_commit",
            "head_commit_status",
        },
        "iteration_runtime_receipt_invalid",
    )
    if not all(
        isinstance(item, str) and item
        for item in (*python.values(), *pillow.values(), *environment.values())
    ):
        raise DirectSvgCandidateError("iteration_runtime_receipt_invalid")
    if (
        environment["FONTCONFIG_FILE"] != runtime["fontconfig"]["path"]
        or environment["FONTCONFIG_PATH"]
        != PurePosixPath(runtime["fontconfig"]["path"]).parent.as_posix()
        or environment["LANG"] != environment["LC_ALL"]
    ):
        raise DirectSvgCandidateError("iteration_environment_mismatch")
    if any(
        not _is_relative_posix_path(environment[key])
        for key in ("FONTCONFIG_FILE", "FONTCONFIG_PATH")
    ):
        raise DirectSvgCandidateError("iteration_environment_mismatch")
    for path_key, hash_key in (
        ("wrapper_path", "wrapper_sha256"),
        ("validator_path", "validator_sha256"),
        ("lock_path", "lock_sha256"),
    ):
        if not _is_relative_posix_path(producer[path_key]) or not HASH_PATTERN.fullmatch(
            str(producer[hash_key])
        ):
            raise DirectSvgCandidateError("iteration_runtime_receipt_invalid")
    if not COMMIT_PATTERN.fullmatch(str(producer["base_commit"])):
        raise DirectSvgCandidateError("iteration_runtime_receipt_invalid")
    head_commit = producer["head_commit"]
    head_status = producer["head_commit_status"]
    if not (
        (head_commit == UNAVAILABLE_PRECOMMIT and head_status == UNAVAILABLE_PRECOMMIT)
        or (
            isinstance(head_commit, str)
            and COMMIT_PATTERN.fullmatch(head_commit)
            and head_status == "recorded"
        )
    ):
        raise DirectSvgCandidateError("iteration_runtime_receipt_invalid")
    if any(
        not isinstance(runtime[key], int) or isinstance(runtime[key], bool) or runtime[key] <= 0
        for key in ("width", "height")
    ):
        raise DirectSvgCandidateError("iteration_runtime_receipt_invalid")
    return producer


def _validate_tool_model_receipt(value: Any) -> dict[str, Any]:
    receipt = _require_closed_keys(
        value,
        {
            "provider",
            "model",
            "model_identity_independently_verified",
            "snapshot",
            "reasoning",
            "token_cap",
            "compute_cap",
            "task",
            "tools",
        },
        "iteration_tool_model_receipt_invalid",
    )
    if not isinstance(receipt["model_identity_independently_verified"], bool):
        raise DirectSvgCandidateError("iteration_tool_model_receipt_invalid")
    if not all(isinstance(receipt[key], str) and receipt[key] for key in ("provider", "model")):
        raise DirectSvgCandidateError("iteration_tool_model_receipt_invalid")
    task = _require_closed_keys(
        receipt["task"],
        {"name", "mode", "branch", "base_commit"},
        "iteration_tool_model_receipt_invalid",
    )
    tools = _require_closed_keys(
        receipt["tools"],
        {"authoring", "validation_and_render", "visual_inspection", "image_generation"},
        "iteration_tool_model_receipt_invalid",
    )
    if not all(isinstance(item, str) and item for item in (*task.values(), *tools.values())):
        raise DirectSvgCandidateError("iteration_tool_model_receipt_invalid")
    if not COMMIT_PATTERN.fullmatch(task["base_commit"]):
        raise DirectSvgCandidateError("iteration_provenance_invalid")
    return task


def _parse_render_command(command: Any) -> dict[str, str]:
    if (
        not isinstance(command, list)
        or not all(isinstance(item, str) for item in command)
        or command[:4] != RENDER_COMMAND_PREFIX
    ):
        raise DirectSvgCandidateError("iteration_command_invalid")
    arguments = command[4:]
    if len(arguments) != 2 * len(RENDER_COMMAND_FLAGS):
        raise DirectSvgCandidateError("iteration_command_invalid")
    parsed: dict[str, str] = {}
    for index in range(0, len(arguments), 2):
        flag, value = arguments[index : index + 2]
        if flag not in RENDER_COMMAND_FLAGS or flag in parsed or not value:
            raise DirectSvgCandidateError("iteration_command_invalid")
        parsed[flag] = value
    if set(parsed) != RENDER_COMMAND_FLAGS:
        raise DirectSvgCandidateError("iteration_command_invalid")
    return parsed


def _validate_iteration_receipt(receipt: dict[str, Any], *, panel: str) -> None:
    required = {
        "cycle",
        "elapsed_minutes",
        "semantic_packet_sha256",
        "source_path",
        "source_sha256",
        "render_path",
        "render_sha256",
        "command",
        "runtime_receipt",
        "tool_model_receipt",
        "correction_reason",
        "correction_type",
        "render_changed_from_prior",
        "publication_acceptance",
    }
    if not isinstance(receipt, dict) or not required.issubset(receipt):
        raise DirectSvgCandidateError("iteration_receipt_incomplete")
    if set(receipt) != required:
        raise DirectSvgCandidateError("iteration_receipt_keys_invalid")
    if any(not _is_relative_posix_path(receipt[key]) for key in ("source_path", "render_path")):
        raise DirectSvgCandidateError("iteration_path_invalid")
    if not HASH_PATTERN.fullmatch(str(receipt["source_sha256"])) or not HASH_PATTERN.fullmatch(
        str(receipt["render_sha256"])
    ):
        raise DirectSvgCandidateError("iteration_hash_invalid")
    if not HASH_PATTERN.fullmatch(str(receipt["semantic_packet_sha256"])):
        raise DirectSvgCandidateError("iteration_hash_invalid")
    if (
        not isinstance(receipt["cycle"], int)
        or isinstance(receipt["cycle"], bool)
        or receipt["cycle"] <= 0
    ):
        raise DirectSvgCandidateError("iteration_receipt_type_invalid")
    if not isinstance(receipt["render_changed_from_prior"], bool) or not all(
        isinstance(receipt[key], str) and receipt[key]
        for key in ("correction_reason", "correction_type")
    ):
        raise DirectSvgCandidateError("iteration_receipt_type_invalid")
    runtime = receipt["runtime_receipt"]
    producer = _validate_runtime_receipt(runtime, receipt)
    task = _validate_tool_model_receipt(receipt["tool_model_receipt"])
    if task["base_commit"] != producer["base_commit"]:
        raise DirectSvgCandidateError("iteration_provenance_mismatch")
    command = _parse_render_command(receipt["command"])
    expected_command = {
        "--root": ".",
        "--svg": receipt["source_path"],
        "--output": receipt["render_path"],
        "--semantic-packet": runtime["semantic_packet"]["path"],
        "--panel": panel,
        "--width": str(runtime["width"]),
        "--height": str(runtime["height"]),
        "--fontconfig": runtime["fontconfig"]["path"],
        "--font": runtime["font"]["path"],
        "--validation-mode": runtime["validation_mode"],
    }
    if command != expected_command:
        raise DirectSvgCandidateError("iteration_command_mismatch")
    if receipt["publication_acceptance"] != "not_claimed":
        raise DirectSvgCandidateError("publication_claim_forbidden")


def record_iteration(ledger: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    """Append one receipt while enforcing the declared cycle and wall budget."""
    panel = ledger.get("panel")
    if panel not in {"C", "F"}:
        raise DirectSvgCandidateError("iteration_panel_invalid")
    _validate_iteration_receipt(receipt, panel=panel)
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
        "LANG": "en_US.UTF-8",
        "LC_ALL": "en_US.UTF-8",
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
