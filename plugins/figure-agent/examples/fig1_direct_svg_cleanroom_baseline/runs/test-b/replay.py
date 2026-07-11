"""Validate, render, or replay the immutable Test B direct-SVG artifacts."""

from __future__ import annotations

import argparse
import hashlib
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[4]
FIXTURE_ROOT = Path(__file__).resolve().parents[2]
RUN_ROOT = Path(__file__).resolve().parent
PACKET_PATH = FIXTURE_ROOT / "packets" / "test-b-synthesis.yaml"
FONTCONFIG_PATH = FIXTURE_ROOT / "contract" / "fontconfig.xml"
REPLAY_RELATIVE_PATH = "examples/fig1_direct_svg_cleanroom_baseline/runs/test-b/replay.py"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from direct_svg_candidate import (  # noqa: E402
    DirectSvgCandidateError,
    render_candidate,
    validate_candidate,
)
from direct_svg_packet import validate_packet  # noqa: E402


class TestBRunError(ValueError):
    """Raised when the Test B run is not internally cross-bound."""


PROVENANCE_TASK = "Task 20 Step 2 Test B semantic synthesis"
PROVENANCE_METHOD = "manual_llm_direct_svg"
PROVENANCE_PROVIDER = "OpenAI"
PROVENANCE_MODEL = "GPT-5 Codex API session"
PROVENANCE_NOT_EXPOSED = "not_exposed_to_session"
PROVENANCE_TOOLS = ["apply_patch", "render_candidate", "view_image"]
PROVENANCE_FLAGS = {
    "network_used": False,
    "image_generation_used": False,
    "target_or_reference_pixels_available": False,
    "reference_pixels_available": False,
    "reference_hashes_available": False,
    "geometry_derivatives_available": False,
    "test_a_history_available": False,
    "test_a_outputs_available": False,
}


def _sha256(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _load(path: Path) -> dict[str, Any]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise TestBRunError("run_yaml_invalid") from exc
    if not isinstance(loaded, dict):
        raise TestBRunError("run_yaml_invalid")
    return loaded


def _plugin_relative(path: Path, plugin_root: Path) -> str:
    try:
        return path.resolve().relative_to(plugin_root.resolve()).as_posix()
    except ValueError as exc:
        raise TestBRunError("input_path_invalid") from exc


def _packet_input(
    packet_path: Path,
    packet: dict[str, Any],
    *,
    role: str,
) -> tuple[Path, dict[str, str]]:
    inputs = packet.get("allowed_inputs")
    if not isinstance(inputs, list):
        raise TestBRunError("input_binding_mismatch")
    matches = [item for item in inputs if isinstance(item, dict) and item.get("role") == role]
    if len(matches) != 1:
        raise TestBRunError("input_binding_mismatch")
    item = matches[0]
    root = packet_path.parent if packet["path_base"] == "packet_root" else packet_path.parent.parent
    path = (root / str(item["path"])).resolve()
    return path, {"path": str(item["path"]), "sha256": str(item["sha256"])}


def _require_binding(
    value: Any,
    expected: dict[str, str],
    *,
    error: str,
) -> None:
    if value != expected:
        raise TestBRunError(error)


def _require_exact_mapping(value: Any, expected: dict[str, Any]) -> None:
    if not isinstance(value, dict) or value != expected:
        raise TestBRunError("provenance_contract_invalid")


def _validate_environment_provenance(
    environment: dict[str, Any], packet: dict[str, Any]
) -> dict[str, Any]:
    """Validate the semantic-synthesis identity and return cycle expectations."""
    for key in (
        "reference_pixels_available",
        "reference_hashes_available",
        "geometry_derivatives_available",
        "test_a_history_available",
        "test_a_outputs_available",
    ):
        if packet.get(key) is not False:
            raise TestBRunError("provenance_contract_invalid")
    if packet.get("test_kind") != "synthesis":
        raise TestBRunError("provenance_contract_invalid")

    expected_top_level = {
        "schema",
        "task",
        "method",
        "provider",
        "model",
        "model_snapshot",
        "reasoning_setting",
        "tools",
        "renderer",
        "runtime",
        "environment",
        "semantic_packet",
        "synthesis_packet",
        "font",
        "fontconfig",
        "publication_acceptance",
    }
    if set(environment) != expected_top_level:
        raise TestBRunError("provenance_contract_invalid")
    expected_identity = {
        "schema": "figure-agent.direct-svg-environment-receipt.v1",
        "task": PROVENANCE_TASK,
        "method": PROVENANCE_METHOD,
        "provider": PROVENANCE_PROVIDER,
        "model": PROVENANCE_MODEL,
        "model_snapshot": PROVENANCE_NOT_EXPOSED,
        "reasoning_setting": PROVENANCE_NOT_EXPOSED,
        "tools": PROVENANCE_TOOLS,
        "publication_acceptance": "not_claimed",
    }
    if any(environment.get(key) != value for key, value in expected_identity.items()):
        raise TestBRunError("provenance_contract_invalid")

    renderer = environment.get("renderer")
    runtime = environment.get("runtime")
    environment_values = environment.get("environment")
    if not isinstance(renderer, dict) or set(renderer) != {
        "executable",
        "version",
        "cairo",
        "pango",
        "harfbuzz",
        "fontconfig",
    }:
        raise TestBRunError("provenance_contract_invalid")
    if not isinstance(runtime, dict) or set(runtime) != {"python", "pillow"}:
        raise TestBRunError("provenance_contract_invalid")
    if not isinstance(environment_values, dict):
        raise TestBRunError("provenance_contract_invalid")
    _require_exact_mapping(
        environment_values,
        {
            "platform": "macOS-26.5.1-arm64-arm-64bit",
            "working_directory": "plugin_root",
            **PROVENANCE_FLAGS,
        },
    )
    expected_runtime = {
        "executable": "rsvg-convert",
        "version": "2.62.1",
        "cairo": "1.18.4",
        "pango": "1.57.0",
        "harfbuzz": "14.1.0",
        "fontconfig": "2.17.1",
    }
    if renderer != expected_runtime or runtime != {"python": "3.12.13", "pillow": "12.2.0"}:
        raise TestBRunError("provenance_contract_invalid")

    return {
        "task": PROVENANCE_TASK,
        "provider": PROVENANCE_PROVIDER,
        "model": PROVENANCE_MODEL,
        "model_snapshot": PROVENANCE_NOT_EXPOSED,
        "reasoning_setting": PROVENANCE_NOT_EXPOSED,
        "method": PROVENANCE_METHOD,
        "tools": PROVENANCE_TOOLS,
        "renderer_executable": renderer["executable"],
        "renderer_version": f"{renderer['executable']} {renderer['version']}",
        "python_version": runtime["python"],
        "pillow_version": runtime["pillow"],
        "environment_platform": environment_values["platform"],
        "working_directory": environment_values["working_directory"],
        **PROVENANCE_FLAGS,
    }


def _run_relative(run_root: Path, raw: Any, *, suffix: str) -> Path:
    if not isinstance(raw, str) or not raw:
        raise TestBRunError("run_artifact_path_invalid")
    relative = Path(raw)
    path = (run_root / relative).resolve()
    if (
        relative.is_absolute()
        or not path.is_relative_to(run_root.resolve())
        or path.suffix.lower() != suffix
    ):
        raise TestBRunError("run_artifact_path_invalid")
    return path


def _retained_evidence_paths(run_root: Path) -> set[Path]:
    state_path = run_root / "run-state.yaml"
    retained = {state_path.resolve()}
    state = _load(state_path)
    environment = state.get("environment_receipt")
    if isinstance(environment, dict):
        retained.add((run_root / str(environment.get("path", ""))).resolve())
    artifacts = state.get("candidate_artifacts")
    if not isinstance(artifacts, list):
        raise TestBRunError("render_path_invalid")
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise TestBRunError("render_path_invalid")
        for key in ("svg_path", "png_path", "ledger_path"):
            retained.add((run_root / str(artifact.get(key, ""))).resolve())
        ledger_path = (run_root / str(artifact.get("ledger_path", ""))).resolve()
        ledger = _load(ledger_path)
        iterations = ledger.get("iterations")
        if not isinstance(iterations, list):
            raise TestBRunError("render_path_invalid")
        for receipt in iterations:
            if not isinstance(receipt, dict):
                raise TestBRunError("render_path_invalid")
            retained.add((run_root / str(receipt.get("svg_path", ""))).resolve())
            retained.add((run_root / str(receipt.get("png_path", ""))).resolve())
    return retained


def resolve_render_paths(
    *,
    plugin_root: Path,
    run_root: Path,
    svg: str,
    png: str,
) -> tuple[Path, Path]:
    """Resolve a render pair while confining both paths to runs/test-b."""
    raw_svg = Path(svg)
    raw_png = Path(png)
    unresolved_svg = plugin_root / raw_svg
    unresolved_png = plugin_root / raw_png
    svg_path = unresolved_svg.resolve()
    png_path = unresolved_png.resolve()
    if (
        raw_svg.is_absolute()
        or raw_png.is_absolute()
        or not svg_path.is_relative_to(run_root.resolve())
        or not png_path.is_relative_to(run_root.resolve())
        or svg_path.suffix.lower() != ".svg"
        or png_path.suffix.lower() != ".png"
        or svg_path == png_path
        or not svg_path.is_file()
        or not png_path.parent.is_dir()
        or unresolved_png.is_symlink()
        or png_path.exists()
        or png_path in _retained_evidence_paths(run_root)
    ):
        raise TestBRunError("render_path_invalid")
    return svg_path, png_path


def resolve_verify_paths(
    *,
    plugin_root: Path,
    run_root: Path,
    svg: str,
    expected_png: str,
) -> tuple[Path, Path]:
    """Resolve retained read-only evidence for a single reproducibility check."""
    raw_svg = Path(svg)
    raw_png = Path(expected_png)
    svg_path = (plugin_root / raw_svg).resolve()
    png_path = (plugin_root / raw_png).resolve()
    if (
        raw_svg.is_absolute()
        or raw_png.is_absolute()
        or not svg_path.is_relative_to(run_root.resolve())
        or not png_path.is_relative_to(run_root.resolve())
        or svg_path.suffix.lower() != ".svg"
        or png_path.suffix.lower() != ".png"
        or svg_path == png_path
        or not svg_path.is_file()
        or not png_path.is_file()
    ):
        raise TestBRunError("verify_path_invalid")
    return svg_path, png_path


def _panel_contract(semantic: dict[str, Any], panel: str) -> dict[str, Any]:
    key = f"panel_{panel}"
    raw_objects = semantic.get("scientific_objects", {}).get(key)
    raw_text = semantic.get("text_content", {}).get(key)
    raw_roles = semantic.get("visual_roles", {}).get(key)
    raw_relations = semantic.get("object_relations")
    if (
        not isinstance(raw_objects, list)
        or not isinstance(raw_text, list)
        or not isinstance(raw_roles, dict)
        or not isinstance(raw_relations, list)
    ):
        raise TestBRunError("semantic_packet_incomplete")
    ids = [item.get("id") for item in raw_objects if isinstance(item, dict)]
    if (
        len(ids) != len(raw_objects)
        or any(not isinstance(item, str) or not item for item in ids)
        or len(set(ids)) != len(ids)
        or any(not isinstance(item, str) or not item for item in raw_text)
        or not set(ids).issubset(raw_roles)
    ):
        raise TestBRunError("semantic_packet_incomplete")
    relations = {
        (
            str(item["subject"]),
            str(item["predicate"]),
            str(item["object"]),
            str(item.get("qualification", "")),
        )
        for item in raw_relations
        if isinstance(item, dict) and str(item.get("subject", "")).startswith(f"{panel}_")
    }
    return {
        "required_ids": ids,
        "required_text": raw_text,
        "visual_roles": raw_roles,
        "relations": relations,
    }


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _relation_metadata(root: ET.Element) -> set[tuple[str, str, str, str]]:
    return {
        (
            element.attrib["data-relation-subject"],
            element.attrib["data-relation-predicate"],
            element.attrib["data-relation-object"],
            element.attrib.get("data-qualification", ""),
        )
        for element in root.iter()
        if element.attrib.get("data-coverage") == "declared-not-spatially-verified"
    }


def _validate_svg(path: Path, contract: dict[str, Any]) -> None:
    try:
        validate_candidate(path, required_ids=set(contract["required_ids"]))
        root = ET.parse(path).getroot()
    except (DirectSvgCandidateError, ET.ParseError, OSError) as exc:
        raise TestBRunError("semantic_svg_incomplete") from exc
    live_text = {
        "".join(element.itertext()).strip()
        for element in root.iter()
        if _local_name(element.tag) == "text"
    }
    if not set(contract["required_text"]).issubset(live_text):
        raise TestBRunError("semantic_svg_incomplete")
    if _relation_metadata(root) != contract["relations"]:
        raise TestBRunError("relation_metadata_incomplete")


def _canonical_command(
    *,
    panel: str,
    width: int,
    height: int,
    semantic_path: str,
    fontconfig_path: str,
    svg_path: str,
    png_path: str,
) -> list[str]:
    return [
        "uv",
        "run",
        "python",
        REPLAY_RELATIVE_PATH,
        "--verify",
        "--panel",
        panel,
        "--width",
        str(width),
        "--height",
        str(height),
        "--semantic-packet",
        semantic_path,
        "--fontconfig",
        fontconfig_path,
        svg_path,
        png_path,
    ]


def _validate_recorded_command(value: Any, expected: list[str]) -> None:
    if (
        not isinstance(value, list)
        or any(not isinstance(item, str) for item in value)
        or value != expected
    ):
        raise TestBRunError("recorded_command_invalid")


def validate_run(*, plugin_root: Path, fixture_root: Path) -> dict[str, Any]:
    """Validate every Test B binding and packet-derived semantic requirement."""
    plugin_root = plugin_root.resolve()
    fixture_root = fixture_root.resolve()
    run_root = fixture_root / "runs" / "test-b"
    packet_path = fixture_root / "packets" / "test-b-synthesis.yaml"
    packet = validate_packet(packet_path)
    semantic_path, _ = _packet_input(packet_path, packet, role="semantic_packet")
    font_path, _ = _packet_input(packet_path, packet, role="licensed_font")
    semantic = _load(semantic_path)
    packet_binding = {
        "path": _plugin_relative(packet_path, plugin_root),
        "sha256": _sha256(packet_path),
    }
    semantic_binding = {
        "path": _plugin_relative(semantic_path, plugin_root),
        "sha256": _sha256(semantic_path),
    }
    font_binding = {
        "path": _plugin_relative(font_path, plugin_root),
        "sha256": _sha256(font_path),
    }
    fontconfig_path = fixture_root / "contract" / "fontconfig.xml"
    fontconfig_binding = {
        "path": _plugin_relative(fontconfig_path, plugin_root),
        "sha256": _sha256(fontconfig_path),
    }

    state = _load(run_root / "run-state.yaml")
    _require_binding(
        state.get("semantic_packet"),
        semantic_binding,
        error="input_binding_mismatch",
    )
    _require_binding(
        state.get("synthesis_packet"),
        packet_binding,
        error="input_binding_mismatch",
    )
    if state.get("state") != "machine_review_ready" or state.get("execution_started") is not True:
        raise TestBRunError("run_state_invalid")

    environment_binding = state.get("environment_receipt")
    if not isinstance(environment_binding, dict):
        raise TestBRunError("environment_binding_invalid")
    environment_path = _run_relative(
        run_root,
        environment_binding.get("path"),
        suffix=".yaml",
    )
    if environment_binding.get("sha256") != _sha256(environment_path):
        raise TestBRunError("environment_binding_invalid")
    environment = _load(environment_path)
    _require_binding(
        environment.get("semantic_packet"),
        semantic_binding,
        error="semantic_binding_mismatch",
    )
    _require_binding(
        environment.get("synthesis_packet"),
        packet_binding,
        error="synthesis_binding_mismatch",
    )
    _require_binding(environment.get("font"), font_binding, error="font_binding_mismatch")
    _require_binding(
        environment.get("fontconfig"),
        fontconfig_binding,
        error="fontconfig_binding_mismatch",
    )
    cycle_provenance = _validate_environment_provenance(environment, packet)

    raw_artifacts = state.get("candidate_artifacts")
    if not isinstance(raw_artifacts, list):
        raise TestBRunError("candidate_artifacts_invalid")
    artifacts = {
        str(item.get("panel", "")).lower(): item for item in raw_artifacts if isinstance(item, dict)
    }
    if set(artifacts) != {"c", "f"}:
        raise TestBRunError("candidate_artifacts_invalid")

    panel_reports: dict[str, Any] = {}
    cycles_validated = 0
    for panel in ("c", "f"):
        panel_name = panel.upper()
        contract = _panel_contract(semantic, panel)
        artifact = artifacts[panel]
        ledger_path = _run_relative(
            run_root,
            artifact.get("ledger_path"),
            suffix=".yaml",
        )
        if artifact.get("ledger_sha256") != _sha256(ledger_path):
            raise TestBRunError("ledger_binding_invalid")
        ledger = _load(ledger_path)
        _require_binding(
            ledger.get("semantic_packet"),
            semantic_binding,
            error="semantic_binding_mismatch",
        )
        _require_binding(
            ledger.get("synthesis_packet"),
            packet_binding,
            error="synthesis_binding_mismatch",
        )
        if (
            ledger.get("panel") != panel_name
            or ledger.get("budget") != packet["budgets"]["utility"]
            or ledger.get("elapsed_provenance") != "self_reported_during_authoring"
            or ledger.get("timestamp_reconstruction")
            != "not_available_and_not_reconstructable_from_git_timestamps"
            or "started_at" in ledger
            or "elapsed_basis" in ledger
        ):
            raise TestBRunError("ledger_contract_invalid")
        iterations = ledger.get("iterations")
        if (
            not isinstance(iterations, list)
            or len(iterations) != packet["budgets"]["utility"]["cycles"]
        ):
            raise TestBRunError("ledger_contract_invalid")

        previous_elapsed = -1.0
        last_svg: Path | None = None
        last_png: Path | None = None
        source_hashes: set[str] = set()
        render_hashes: set[str] = set()
        for expected_cycle, receipt in enumerate(iterations, start=1):
            if not isinstance(receipt, dict) or receipt.get("cycle") != expected_cycle:
                raise TestBRunError("cycle_sequence_invalid")
            if (
                receipt.get("reproducibility_mode") != "read_only_verify"
                or receipt.get("temporary_render_retention") != "deleted_after_hash_comparison"
            ):
                raise TestBRunError("reproducibility_receipt_invalid")
            elapsed = receipt.get("elapsed_minutes")
            if (
                not isinstance(elapsed, (int, float))
                or isinstance(elapsed, bool)
                or elapsed < previous_elapsed
                or elapsed < 0
                or elapsed > ledger["budget"]["wall_minutes_per_panel"]
            ):
                raise TestBRunError("elapsed_minutes_invalid")
            previous_elapsed = float(elapsed)

            svg_path = _run_relative(run_root, receipt.get("svg_path"), suffix=".svg")
            png_path = _run_relative(run_root, receipt.get("png_path"), suffix=".png")
            if not svg_path.is_file() or not png_path.is_file():
                raise TestBRunError("run_artifact_missing")
            source_hash = _sha256(svg_path)
            render_hash = _sha256(png_path)
            if (
                receipt.get("source_sha256") != source_hash
                or receipt.get("render_sha256") != render_hash
            ):
                raise TestBRunError("artifact_hash_mismatch")

            tool = receipt.get("tool_model_receipt")
            if not isinstance(tool, dict):
                raise TestBRunError("tool_model_receipt_invalid")
            if (
                tool.get("panel") != panel_name
                or tool.get("width") != receipt.get("render_width")
                or tool.get("height") != receipt.get("render_height")
            ):
                raise TestBRunError("tool_model_receipt_invalid")
            _require_binding(
                {
                    "path": tool.get("semantic_packet_path"),
                    "sha256": tool.get("semantic_packet_sha256"),
                },
                semantic_binding,
                error="semantic_binding_mismatch",
            )
            _require_binding(
                {
                    "path": tool.get("synthesis_packet_path"),
                    "sha256": tool.get("synthesis_packet_sha256"),
                },
                packet_binding,
                error="synthesis_binding_mismatch",
            )
            _require_binding(
                {
                    "path": tool.get("font_path"),
                    "sha256": tool.get("font_sha256"),
                },
                font_binding,
                error="font_binding_mismatch",
            )
            _require_binding(
                {
                    "path": tool.get("fontconfig_path"),
                    "sha256": tool.get("fontconfig_sha256"),
                },
                fontconfig_binding,
                error="fontconfig_binding_mismatch",
            )
            _require_exact_mapping(
                tool,
                {
                    **cycle_provenance,
                    "panel": panel_name,
                    "width": receipt.get("render_width"),
                    "height": receipt.get("render_height"),
                    "semantic_packet_path": semantic_binding["path"],
                    "semantic_packet_sha256": semantic_binding["sha256"],
                    "synthesis_packet_path": packet_binding["path"],
                    "synthesis_packet_sha256": packet_binding["sha256"],
                    "font_path": font_binding["path"],
                    "font_sha256": font_binding["sha256"],
                    "fontconfig_path": fontconfig_binding["path"],
                    "fontconfig_sha256": fontconfig_binding["sha256"],
                },
            )

            svg_plugin_path = _plugin_relative(svg_path, plugin_root)
            png_plugin_path = _plugin_relative(png_path, plugin_root)
            expected_command = _canonical_command(
                panel=panel_name,
                width=receipt["render_width"],
                height=receipt["render_height"],
                semantic_path=semantic_binding["path"],
                fontconfig_path=fontconfig_binding["path"],
                svg_path=svg_plugin_path,
                png_path=png_plugin_path,
            )
            _validate_recorded_command(receipt.get("command"), expected_command)
            _validate_svg(svg_path, contract)
            source_hashes.add(source_hash)
            render_hashes.add(render_hash)
            last_svg = svg_path
            last_png = png_path
            cycles_validated += 1

        if len(source_hashes) != len(iterations) or len(render_hashes) != len(iterations):
            raise TestBRunError("cycle_hashes_not_distinct")
        if last_svg is None or last_png is None:
            raise TestBRunError("candidate_artifacts_invalid")
        if (
            artifact.get("cycles") != len(iterations)
            or artifact.get("svg_path") != last_svg.relative_to(run_root).as_posix()
            or artifact.get("png_path") != last_png.relative_to(run_root).as_posix()
            or artifact.get("source_sha256") != _sha256(last_svg)
            or artifact.get("render_sha256") != _sha256(last_png)
        ):
            raise TestBRunError("candidate_artifacts_invalid")
        panel_reports[panel] = {
            "required_ids": sorted(contract["required_ids"]),
            "required_text": contract["required_text"],
            "visual_roles": contract["visual_roles"],
            "relations": sorted(contract["relations"]),
        }

    machine = state.get("machine_validation")
    if not isinstance(machine, dict):
        raise TestBRunError("run_state_invalid")
    if (
        machine.get("relation_metadata_complete") != "passed_all_6_cycles"
        or machine.get("spatial_scientific_verification") != "pending_human_review"
    ):
        raise TestBRunError("run_state_invalid")
    return {
        "cycles_validated": cycles_validated,
        "relation_metadata_complete": True,
        "spatial_scientific_verification": "pending_human_review",
        "panels": panel_reports,
    }


def _render(
    *,
    svg: str,
    png: str,
    panel: str,
    width: int,
    height: int,
    semantic_packet: str,
    fontconfig: str,
) -> None:
    svg_path, png_path = resolve_render_paths(
        plugin_root=PLUGIN_ROOT,
        run_root=RUN_ROOT,
        svg=svg,
        png=png,
    )
    packet = validate_packet(PACKET_PATH)
    semantic_path, _ = _packet_input(PACKET_PATH, packet, role="semantic_packet")
    if (
        panel not in {"C", "F"}
        or f"panel-{panel.lower()}" not in svg_path.parts
        or Path(semantic_packet) != Path(_plugin_relative(semantic_path, PLUGIN_ROOT))
        or Path(fontconfig) != Path(_plugin_relative(FONTCONFIG_PATH, PLUGIN_ROOT))
    ):
        raise TestBRunError("render_contract_invalid")
    result = render_candidate(
        svg_path,
        png_path,
        width=width,
        height=height,
        fontconfig_file=FONTCONFIG_PATH,
    )
    print(yaml.safe_dump(result, sort_keys=False).strip())


def _verify_retained(
    *,
    svg: str,
    expected_png: str,
    panel: str,
    width: int,
    height: int,
    semantic_packet: str,
    fontconfig: str,
) -> None:
    svg_path, expected_path = resolve_verify_paths(
        plugin_root=PLUGIN_ROOT,
        run_root=RUN_ROOT,
        svg=svg,
        expected_png=expected_png,
    )
    packet = validate_packet(PACKET_PATH)
    semantic_path, _ = _packet_input(PACKET_PATH, packet, role="semantic_packet")
    if (
        panel not in {"C", "F"}
        or f"panel-{panel.lower()}" not in svg_path.parts
        or f"panel-{panel.lower()}" not in expected_path.parts
        or Path(semantic_packet) != Path(_plugin_relative(semantic_path, PLUGIN_ROOT))
        or Path(fontconfig) != Path(_plugin_relative(FONTCONFIG_PATH, PLUGIN_ROOT))
    ):
        raise TestBRunError("verify_contract_invalid")
    with tempfile.TemporaryDirectory(prefix="figure-agent-test-b-verify-") as tmp:
        temporary_png = Path(tmp) / "render.png"
        result = render_candidate(
            svg_path,
            temporary_png,
            width=width,
            height=height,
            fontconfig_file=FONTCONFIG_PATH,
        )
        if result["render_sha256"] != _sha256(expected_path):
            raise TestBRunError("replay_mismatch")
    print("verification matched retained PNG")


def _verify_all() -> None:
    report = validate_run(plugin_root=PLUGIN_ROOT, fixture_root=FIXTURE_ROOT)
    verified = 0
    for panel in ("c", "f"):
        ledger = _load(RUN_ROOT / f"panel-{panel}" / "ledger.yaml")
        for receipt in ledger["iterations"]:
            command = receipt["command"]
            _verify_retained(
                svg=command[-2],
                expected_png=command[-1],
                panel=panel.upper(),
                width=receipt["render_width"],
                height=receipt["render_height"],
                semantic_packet=receipt["tool_model_receipt"]["semantic_packet_path"],
                fontconfig=receipt["tool_model_receipt"]["fontconfig_path"],
            )
            verified += 1
    if verified != report["cycles_validated"]:
        raise TestBRunError("replay_cycle_count_mismatch")
    print(f"replay verified: {verified}/6 deterministic renders")


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--render", action="store_true")
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--verify-all", action="store_true")
    parser.add_argument("--panel", choices=("C", "F"))
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--semantic-packet")
    parser.add_argument("--fontconfig")
    parser.add_argument("svg", nargs="?")
    parser.add_argument("png", nargs="?")
    args = parser.parse_args()
    if args.verify_all:
        if any(
            value is not None
            for value in (
                args.panel,
                args.width,
                args.height,
                args.semantic_packet,
                args.fontconfig,
                args.svg,
                args.png,
            )
        ):
            parser.error("--verify-all accepts no artifact arguments")
        _verify_all()
        return
    if any(
        value is None
        for value in (
            args.panel,
            args.width,
            args.height,
            args.semantic_packet,
            args.fontconfig,
            args.svg,
            args.png,
        )
    ):
        parser.error("--render and --verify require the complete artifact contract")
    if args.verify:
        _verify_retained(
            svg=args.svg,
            expected_png=args.png,
            panel=args.panel,
            width=args.width,
            height=args.height,
            semantic_packet=args.semantic_packet,
            fontconfig=args.fontconfig,
        )
    else:
        _render(
            svg=args.svg,
            png=args.png,
            panel=args.panel,
            width=args.width,
            height=args.height,
            semantic_packet=args.semantic_packet,
            fontconfig=args.fontconfig,
        )


if __name__ == "__main__":
    main()
