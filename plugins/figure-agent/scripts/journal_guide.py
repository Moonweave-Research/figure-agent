"""Build and evaluate hard journal-guide constraints from fixture-local inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import convergence_models
import fixture_identity
import runtime_paths
import yaml

SCHEMA = convergence_models.JOURNAL_GUIDE_SCHEMA
DEFAULT_OUTPUT_FORMATS = ["pdf", "png", "svg"]
DEFAULT_HARD_CONSTRAINTS = {
    "output_formats": DEFAULT_OUTPUT_FORMATS,
    "editable_required": True,
    "font_size_min_pt": None,
    "line_width_range_pt": None,
    "color_mode": "unspecified",
    "colorblind_safe_required": False,
}


class JournalGuideError(ValueError):
    """Raised when guide inputs are malformed or unsafe."""


def _load_yaml_mapping(path: Path, label: str) -> dict[str, Any]:
    if path.is_symlink():
        raise JournalGuideError(f"{label}_symlink")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise JournalGuideError(f"{label}_unreadable") from exc
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise JournalGuideError(f"{label}_invalid")
    return raw


def _resolve_paths(
    *,
    plugin_root: Path | None,
    workspace_root: Path | None,
) -> runtime_paths.RuntimePaths:
    return runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )


def _safe_playbook_path(example_dir: Path, raw_id: Any) -> Path | None:
    if raw_id is None:
        return None
    if not isinstance(raw_id, str) or not raw_id.strip():
        raise JournalGuideError("playbook_id_invalid")
    playbook_id = raw_id.strip()
    if "/" in playbook_id or "\\" in playbook_id or ".." in Path(playbook_id).parts:
        raise JournalGuideError("playbook_path_escape")
    path = example_dir.parent / "_journal_art_direction_playbooks" / f"{playbook_id}.yaml"
    root = (example_dir.parent / "_journal_art_direction_playbooks").resolve()
    try:
        path.resolve().relative_to(root)
    except ValueError as exc:
        raise JournalGuideError("playbook_path_escape") from exc
    return path


def _string_list(value: Any, *, label: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise JournalGuideError(f"{label}_invalid")
    return list(value)


def _float_or_none(value: Any, *, label: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise JournalGuideError(f"{label}_invalid") from exc


def _line_width_range(value: Any) -> list[float] | None:
    if value is None:
        return None
    if not isinstance(value, list) or len(value) != 2:
        raise JournalGuideError("line_width_range_pt_invalid")
    low = _float_or_none(value[0], label="line_width_range_pt")
    high = _float_or_none(value[1], label="line_width_range_pt")
    if low is None or high is None or low < 0 or high < low:
        raise JournalGuideError("line_width_range_pt_invalid")
    return [low, high]


def _target_journal(spec: dict[str, Any], aesthetic_intent: dict[str, Any] | None) -> str:
    for source in (spec, aesthetic_intent or {}):
        value = source.get("target_journal")
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "unknown"


def _hard_constraints(spec: dict[str, Any]) -> dict[str, Any]:
    constraints = dict(DEFAULT_HARD_CONSTRAINTS)
    raw = spec.get("journal_constraints")
    if raw is None:
        return constraints
    if not isinstance(raw, dict):
        raise JournalGuideError("journal_constraints_invalid")
    output_formats = _string_list(raw.get("output_formats"), label="output_formats")
    if output_formats:
        constraints["output_formats"] = output_formats
    if "editable_required" in raw:
        if not isinstance(raw["editable_required"], bool):
            raise JournalGuideError("editable_required_invalid")
        constraints["editable_required"] = raw["editable_required"]
    constraints["font_size_min_pt"] = _float_or_none(
        raw.get("font_size_min_pt"),
        label="font_size_min_pt",
    )
    constraints["line_width_range_pt"] = _line_width_range(raw.get("line_width_range_pt"))
    color_mode = raw.get("color_mode")
    if color_mode is not None:
        if not isinstance(color_mode, str) or not color_mode.strip():
            raise JournalGuideError("color_mode_invalid")
        constraints["color_mode"] = color_mode.strip()
    if "colorblind_safe_required" in raw:
        if not isinstance(raw["colorblind_safe_required"], bool):
            raise JournalGuideError("colorblind_safe_required_invalid")
        constraints["colorblind_safe_required"] = raw["colorblind_safe_required"]
    return constraints


def build_journal_guide(
    name: str,
    *,
    plugin_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise JournalGuideError("fixture_name_invalid") from exc
    paths = _resolve_paths(plugin_root=plugin_root, workspace_root=workspace_root)
    example_dir = paths.examples_dir / name
    spec_path = example_dir / "spec.yaml"
    spec = _load_yaml_mapping(spec_path, "spec")
    aesthetic_path = example_dir / "aesthetic_intent.yaml"
    aesthetic_intent = (
        _load_yaml_mapping(aesthetic_path, "aesthetic_intent")
        if aesthetic_path.exists()
        else None
    )
    playbook_path = _safe_playbook_path(example_dir, spec.get("journal_art_direction_playbook"))
    sources = ["default_kernel_constraints", "spec.yaml"]
    if aesthetic_intent is not None:
        sources.append("aesthetic_intent.yaml")
    if playbook_path is not None:
        if not playbook_path.is_file():
            raise JournalGuideError("playbook_missing")
        _load_yaml_mapping(playbook_path, "journal_art_direction_playbook")
        sources.append(playbook_path.relative_to(example_dir.parent).as_posix())
    guide = {
        "schema": SCHEMA,
        "target_journal": _target_journal(spec, aesthetic_intent),
        "guide_hash": "sha256:" + "0" * 64,
        "hard_constraints": _hard_constraints(spec),
        "sources": sources,
        "invented_external_journal_rules": False,
    }
    guide["guide_hash"] = convergence_models.canonical_hash(
        {key: value for key, value in guide.items() if key != "guide_hash"}
    )
    return convergence_models.validate_journal_guide(guide)


def evaluate_journal_constraints(
    guide: dict[str, Any],
    *,
    outputs: dict[str, Any],
) -> dict[str, Any]:
    guide = convergence_models.validate_journal_guide(guide)
    constraints = guide["hard_constraints"]
    violations: list[dict[str, Any]] = []
    if constraints.get("editable_required") is True and not outputs.get("editable"):
        violations.append(
            {
                "id": "editable_output_missing",
                "severity": "hard",
                "source": "JournalGuide.hard_constraints.editable_required",
            }
        )
    for fmt in sorted(str(item) for item in constraints.get("output_formats", [])):
        if not outputs.get(str(fmt)):
            violations.append(
                {
                    "id": f"required_output_format_missing:{fmt}",
                    "severity": "hard",
                    "source": "JournalGuide.hard_constraints.output_formats",
                }
            )
    return {
        "schema": "figure-agent.journal-constraint-evaluation.v1",
        "passed": not violations,
        "violations": violations,
        "guide_hash": guide["guide_hash"],
    }
