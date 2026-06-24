"""Panel-aware candidate families for real figure improvement proposals."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import bounded_coordinate_offset
import candidate_contracts
import candidate_panel_model
import fixture_identity
import runtime_paths
from quality_manifest import file_sha256

SCHEMA = "figure-agent.candidate-set.v1"
SUPPORTED_FAMILY = "energy-trap-alignment"
SUPPORTED_PANEL = "C"
GENERIC_FAMILY = "label-repair"
ZERO_HASH = "sha256:" + "0" * 64
ENERGY_TERMS = ("mobility edge", "{shallow}", "{deep}", "siteS", "siteD")
CANONICAL_FAMILY_EDIT_CLASS = {
    "label-repair": "label_offset",
    "connector-routing": "leader_line_reroute",
    "panel-layout": "panel_spacing_adjust",
    "contrast-repair": "contrast_boost",
    "annotation-box-layout": "annotation_box_resize",
}
CANONICAL_EXPECTED_DELTA = {
    "label_offset": "improve label clearance",
    "leader_line_reroute": "reduce leader-line label collision risk",
    "panel_spacing_adjust": "increase panel boundary clearance",
    "contrast_boost": "increase low-contrast element legibility",
    "annotation_box_resize": "reduce annotation-box internal collision risk",
}


def _source_path(paths: runtime_paths.RuntimePaths, name: str) -> Path:
    fixture_identity.validate_fixture_name(name)
    return paths.examples_dir / name / f"{name}.tex"


def _base(source: Path) -> dict[str, str]:
    return {
        "tex_hash": file_sha256(source) if source.is_file() else ZERO_HASH,
        "status_hash": ZERO_HASH,
        "intent_model_hash": ZERO_HASH,
    }


def _refusal(name: str, source: Path, code: str) -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "fixture": name,
        "base": _base(source),
        "candidates": [],
        "refusals": [{"code": code}],
    }


def _candidate_selector(selectors: list[dict[str, Any]]) -> dict[str, Any] | None:
    for selector in selectors:
        text = str(selector.get("text", ""))
        if (
            text.lstrip().startswith("\\node")
            and any(term in text for term in ENERGY_TERMS)
            and bounded_coordinate_offset.offset_first_coordinate(text) is not None
        ):
            return selector
    return None


def derive_panel_family(
    name: str,
    panel: str | None,
    *,
    selectors: list[dict[str, Any]],
    panel_payload: dict[str, Any],
) -> str | None:
    offsettable = [
        selector
        for selector in selectors
        if bounded_coordinate_offset.offset_first_coordinate(str(selector.get("text", "")))
        is not None
    ]
    if not offsettable:
        return None
    if panel == SUPPORTED_PANEL and any(
        term in str(selector.get("text", "")) for selector in offsettable for term in ENERGY_TERMS
    ):
        return SUPPORTED_FAMILY
    return GENERIC_FAMILY


def _candidate(
    *,
    name: str,
    panel_model: dict[str, Any],
    selector: dict[str, Any],
) -> dict[str, Any]:
    source_rel = selector.get("path")
    original = str(selector.get("text", ""))
    replacement = bounded_coordinate_offset.offset_first_coordinate(original)
    if replacement is None:
        raise ValueError("selector_not_offsettable")
    stable_hash_payload = {
        "family": SUPPORTED_FAMILY,
        "target": {"panel": SUPPORTED_PANEL, "subregion": "energy-trap-labels"},
        "edit_class": "label_offset",
        "affected_files": [source_rel],
        "selector": {
            "kind": "tex_selector.v1",
            "path": source_rel,
            "panel": selector.get("panel"),
            "line_start": selector.get("line_start"),
            "line_end": selector.get("line_end"),
            "source_hash": selector.get("source_hash"),
            "selector_text_hash": selector.get("selector_text_hash"),
        },
        "operations": [
            {
                "kind": "replace_text",
                "path": source_rel,
                "original": original,
                "replacement": replacement,
            }
        ],
        "apply_authority": "review_only",
    }
    candidate: dict[str, Any] = {
        "id": "CAND001",
        "family": SUPPORTED_FAMILY,
        "target": {"panel": SUPPORTED_PANEL, "subregion": "energy-trap-labels"},
        "edit_class": "label_offset",
        "affected_files": [source_rel],
        "selector": {
            "kind": "tex_selector.v1",
            "path": source_rel,
            "panel": selector.get("panel"),
            "line_start": selector.get("line_start"),
            "line_end": selector.get("line_end"),
            "source_hash": selector.get("source_hash"),
            "selector_text_hash": selector.get("selector_text_hash"),
        },
        "selectors": [selector],
        "operations": [
            {
                "kind": "replace_text",
                "path": source_rel,
                "original": original,
                "replacement": replacement,
            }
        ],
        "risk": "medium",
        "expected_delta": ["increase trap-label clearance in Panel C"],
        "semantic_risks": [
            "energy alignment labels must remain semantically bound to their trap levels"
        ],
        "rollback": {"strategy": "reverse_operations"},
        "verification": {
            "required_commands": [
                f"fig-agent compile {name} --strict",
                f"fig-agent status {name} --json",
                f"fig-agent analyze-panel {name} C --json",
            ]
        },
        "apply_authority": "review_only",
        "blocked_if": ["semantic_invariant_failed", "render_failed", "human_rejected"],
        "panel": panel_model.get("panel"),
        "visual_review": panel_model.get("visual_review"),
    }
    candidate["candidate_hash"] = candidate_contracts.canonical_hash(stable_hash_payload)
    return candidate


def _first_offsettable_selector(selectors: list[dict[str, Any]]) -> dict[str, Any] | None:
    for selector in selectors:
        text = str(selector.get("text", ""))
        if bounded_coordinate_offset.offset_first_coordinate(text) is not None:
            return selector
    return None


def _canonical_candidate(
    *,
    name: str,
    family: str,
    panel: str | None,
    selector: dict[str, Any],
) -> dict[str, Any] | None:
    source_rel = str(selector.get("path") or "")
    original = str(selector.get("text") or "")
    replacement = bounded_coordinate_offset.offset_first_coordinate(original)
    if replacement is None:
        return None
    edit_class = CANONICAL_FAMILY_EDIT_CLASS[family]
    stable_hash_payload = {
        "family": family,
        "target": {"panel": panel, "subregion": edit_class},
        "edit_class": edit_class,
        "affected_files": [source_rel],
        "selector": {
            "kind": "tex_selector.v1",
            "path": source_rel,
            "panel": selector.get("panel"),
            "line_start": selector.get("line_start"),
            "line_end": selector.get("line_end"),
            "source_hash": selector.get("source_hash"),
            "selector_text_hash": selector.get("selector_text_hash"),
        },
        "operation": {
            "kind": "replace_text",
            "semantic_kind": "bounded_coordinate_offset",
            "path": source_rel,
            "original": original,
            "replacement": replacement,
        },
        "apply_authority": "review_only",
    }
    return {
        "id": "CAND001",
        "family": family,
        "target": {"panel": panel, "subregion": edit_class},
        "edit_class": edit_class,
        "affected_files": [source_rel],
        "selector": {
            "kind": "tex_selector.v1",
            "path": source_rel,
            "panel": selector.get("panel"),
            "line_start": selector.get("line_start"),
            "line_end": selector.get("line_end"),
            "source_hash": selector.get("source_hash"),
            "selector_text_hash": selector.get("selector_text_hash"),
        },
        "selectors": [selector],
        "operations": [
            {
                "kind": "replace_text",
                "semantic_kind": "bounded_coordinate_offset",
                "path": source_rel,
                "original": original,
                "replacement": replacement,
            }
        ],
        "risk": "medium" if edit_class != "label_offset" else "low",
        "expected_delta": [CANONICAL_EXPECTED_DELTA[edit_class]],
        "semantic_risks": []
        if edit_class == "label_offset"
        else ["synthetic smoke candidate needs human visual review before apply"],
        "rollback": {"strategy": "reverse_operations"},
        "verification": {
            "required_commands": [
                f"fig-agent compile {name} --strict",
                f"fig-agent status {name} --json",
            ]
        },
        "apply_authority": "review_only",
        "blocked_if": ["semantic_invariant_failed", "render_failed", "human_rejected"],
        "candidate_hash": candidate_contracts.canonical_hash(stable_hash_payload),
    }


def _canonical_family_candidates(
    name: str,
    *,
    source: Path,
    panel: str | None,
    family: str,
    panel_model: dict[str, Any],
) -> dict[str, Any]:
    selectors = [item for item in panel_model.get("selectors", []) if isinstance(item, dict)]
    selector = _first_offsettable_selector(selectors)
    if selector is None:
        return _refusal(name, source, "no_supported_candidate")
    candidate = _canonical_candidate(
        name=name,
        family=family,
        panel=panel,
        selector=selector,
    )
    if candidate is None:
        code = "source_missing" if not source.is_file() else "no_supported_candidate"
        return _refusal(name, source, code)
    return {
        "schema": SCHEMA,
        "fixture": name,
        "base": _base(source),
        "panel": panel,
        "family": family,
        "candidates": [candidate],
        "refusals": [],
    }


def build_family_candidates(
    name: str,
    *,
    panel: str | None,
    family: str | None,
    workspace_root: Path | None = None,
    plugin_root: Path | None = None,
) -> dict[str, Any]:
    paths = runtime_paths.resolve_runtime_paths(
        plugin_root=plugin_root,
        workspace_root=workspace_root,
    )
    source = _source_path(paths, name)
    if not source.is_file():
        return _refusal(name, source, "source_missing")

    panel_model: dict[str, Any] | None = None
    if panel is None:
        return _refusal(name, source, "unknown_panel")

    panel_model = candidate_panel_model.build_panel_model(
        name,
        panel,
        workspace_root=paths.workspace_root,
        plugin_root=paths.plugin_root,
    )
    if {"code": "panel_not_declared"} in panel_model.get("refusals", []):
        return _refusal(name, source, "panel_not_declared")

    if family is None and panel is not None:
        selectors = [item for item in panel_model.get("selectors", []) if isinstance(item, dict)]
        family = derive_panel_family(
            name,
            panel,
            selectors=selectors,
            panel_payload=panel_model.get("panel", {}),
        )
        if family is None:
            return _refusal(name, source, "no_supported_candidate")

    if family in CANONICAL_FAMILY_EDIT_CLASS:
        return _canonical_family_candidates(
            name,
            source=source,
            panel=panel,
            family=family,
            panel_model=panel_model,
        )
    if family != SUPPORTED_FAMILY:
        return _refusal(name, source, "unsupported_candidate_family")
    if panel != SUPPORTED_PANEL:
        return _refusal(name, source, "unsupported_panel_family")

    selectors = [item for item in panel_model.get("selectors", []) if isinstance(item, dict)]
    selector = _candidate_selector(selectors)
    if selector is None:
        return _refusal(name, source, "no_supported_candidate")
    return {
        "schema": SCHEMA,
        "fixture": name,
        "base": _base(source),
        "panel": panel,
        "family": family,
        "candidates": [
            _candidate(name=name, panel_model=panel_model, selector=selector),
        ],
        "refusals": [],
    }
