"""Load and validate fixture-local benchmark contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fixture_identity
import runtime_paths
import yaml

SCHEMA = "figure-agent.benchmark-contract.v1"

DEFECT_CLASSES = frozenset(
    {
        "label_overlap",
        "leader_line_collision",
        "panel_boundary_overlap",
        "low_contrast",
        "annotation_box_collision",
    }
)
FAMILY_IDS = frozenset(
    {
        "label-repair",
        "connector-routing",
        "panel-layout",
        "contrast-repair",
        "annotation-box-layout",
    }
)
EDIT_CLASSES = frozenset(
    {
        "label_offset",
        "leader_line_reroute",
        "panel_spacing_adjust",
        "contrast_boost",
        "annotation_box_resize",
    }
)
HARD_REGRESSIONS = frozenset(
    {
        "source_compile_failure",
        "candidate_hard_gate_rejected",
        "text_boundary_blocker_increase",
        "semantic_anchor_removed",
        "detector_report_missing",
        "required_detector_missing",
    }
)
MOVEMENT_OPERATORS = frozenset(
    {"decrease", "decrease_or_equal", "increase", "increase_or_equal", "unchanged"}
)
REFERENCE_POLICY_KINDS = frozenset(
    {"repo_authored_synthetic", "user_owned_dogfood", "reference_derived_pattern"}
)
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".tif", ".tiff", ".pdf", ".svg"})


class BenchmarkContractError(ValueError):
    """Raised when a benchmark contract is malformed or leaves fixture bounds."""


def _as_string_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise BenchmarkContractError(f"{key}_invalid")
    return list(value)


def _as_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise BenchmarkContractError(f"{key}_invalid")
    return value


def _fixture_local_path(fixture_dir: Path, raw_path: str, *, label: str) -> Path:
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise BenchmarkContractError(f"{label}_path_escape")
    path = fixture_dir / relative
    try:
        path.resolve().relative_to(fixture_dir.resolve())
    except ValueError as exc:
        raise BenchmarkContractError(f"{label}_path_escape") from exc
    for parent in [path, *path.parents]:
        if parent == fixture_dir.parent:
            break
        if parent.is_symlink():
            raise BenchmarkContractError(f"{label}_path_symlink")
    return path


def _validate_detector_reports(
    fixture_dir: Path,
    required_detectors: list[str],
    detector_reports: dict[str, Any],
) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for detector in required_detectors:
        raw = detector_reports.get(detector)
        if raw is None:
            continue
        if not isinstance(raw, str):
            raise BenchmarkContractError("detector_report_path_invalid")
        _fixture_local_path(fixture_dir, raw, label="detector_report")
        normalized[detector] = raw
    for detector, raw in detector_reports.items():
        if not isinstance(detector, str) or not isinstance(raw, str):
            raise BenchmarkContractError("detector_report_path_invalid")
        _fixture_local_path(fixture_dir, raw, label="detector_report")
        normalized[detector] = raw
    return normalized


def _validate_reference_policy(
    fixture_dir: Path,
    policy: Any,
    *,
    suite_role: str | None,
) -> dict[str, Any]:
    if not isinstance(policy, dict):
        if suite_role == "patterns":
            raise BenchmarkContractError("reference_policy_missing")
        raise BenchmarkContractError("reference_policy_invalid")
    kind = str(policy.get("kind") or "")
    if kind not in REFERENCE_POLICY_KINDS:
        raise BenchmarkContractError("reference_policy_kind_unknown")
    if kind == "reference_derived_pattern":
        if bool(policy.get("golden_target_allowed")):
            raise BenchmarkContractError("reference_policy_golden_target_forbidden")
        for path in fixture_dir.rglob("*"):
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES:
                raise BenchmarkContractError("reference_policy_external_image_forbidden")
    return dict(policy)


def _validate_expected_movement(payload: dict[str, Any]) -> dict[str, str]:
    movements = _as_mapping(payload, "expected_movement")
    normalized: dict[str, str] = {}
    for metric, operator in movements.items():
        if not isinstance(metric, str) or not isinstance(operator, str):
            raise BenchmarkContractError("expected_movement_invalid")
        if operator not in MOVEMENT_OPERATORS:
            raise BenchmarkContractError(f"movement_operator_unknown:{operator}")
        normalized[metric] = operator
    return normalized


def load_contract(
    name: str,
    *,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
    suite_role: str | None = None,
) -> dict[str, Any]:
    """Load a fixture benchmark contract or return structured missing state."""
    try:
        fixture_identity.validate_fixture_name(name)
    except ValueError as exc:
        raise BenchmarkContractError(str(exc)) from exc
    paths = runtime_paths.resolve_runtime_paths(
        workspace_root=workspace_root,
        plugin_root=plugin_root,
    )
    fixture_dir = paths.examples_dir / name
    contract_path = fixture_dir / "benchmark_contract.yaml"
    if contract_path.is_symlink():
        raise BenchmarkContractError("contract_symlink_forbidden")
    if not contract_path.is_file():
        return {
            "schema": SCHEMA,
            "state": "missing",
            "fixture": name,
            "path": "benchmark_contract.yaml",
        }
    raw = yaml.safe_load(contract_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise BenchmarkContractError("contract_yaml_invalid")
    if raw.get("schema") != SCHEMA:
        raise BenchmarkContractError("schema_invalid")
    if raw.get("fixture") != name:
        raise BenchmarkContractError("fixture_mismatch")
    defect_class = str(raw.get("defect_class") or "")
    if defect_class not in DEFECT_CLASSES:
        raise BenchmarkContractError(f"defect_class_unknown:{defect_class}")
    families = _as_string_list(raw, "candidate_families")
    for family in families:
        if family not in FAMILY_IDS:
            raise BenchmarkContractError(f"candidate_family_invalid:{family}")
    edit_classes = _as_string_list(raw, "candidate_edit_classes")
    for edit_class in edit_classes:
        if edit_class not in EDIT_CLASSES:
            raise BenchmarkContractError(f"candidate_edit_class_invalid:{edit_class}")
    required_detectors = _as_string_list(raw, "required_detectors")
    detector_reports_raw = raw.get("detector_reports") or {}
    if not isinstance(detector_reports_raw, dict):
        raise BenchmarkContractError("detector_reports_invalid")
    detector_reports = _validate_detector_reports(
        fixture_dir,
        required_detectors,
        detector_reports_raw,
    )
    expected_movement = _validate_expected_movement(raw)
    hard_regressions = _as_string_list(raw, "hard_regressions")
    for code in hard_regressions:
        if code not in HARD_REGRESSIONS:
            raise BenchmarkContractError(f"unknown_hard_regression:{code}")
    reference_policy = _validate_reference_policy(
        fixture_dir,
        raw.get("reference_policy"),
        suite_role=suite_role,
    )
    release = raw.get("release") if isinstance(raw.get("release"), dict) else {}
    return {
        "schema": SCHEMA,
        "state": "present",
        "fixture": name,
        "defect_class": defect_class,
        "candidate_families": families,
        "candidate_edit_classes": edit_classes,
        "required_detectors": required_detectors,
        "detector_reports": detector_reports,
        "expected_movement": expected_movement,
        "hard_regressions": hard_regressions,
        "reference_policy": reference_policy,
        "release": release,
    }
