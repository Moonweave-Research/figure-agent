"""Panel-aware candidate families for real figure improvement proposals."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import candidate_contracts
import candidate_panel_model
import fixture_identity
import runtime_paths
from quality_manifest import file_sha256

SCHEMA = "figure-agent.candidate-set.v1"
SUPPORTED_FAMILY = "energy-trap-alignment"
KNOWN_UNSUPPORTED_PANEL_FAMILIES = frozenset({"plot-marker-hierarchy"})
SUPPORTED_PANEL = "C"
ZERO_HASH = "sha256:" + "0" * 64
ENERGY_TERMS = ("mobility edge", "{shallow}", "{deep}", "siteS", "siteD")
NODE_AT_RE = re.compile(r"at\s*\((?P<x>-?\d+(?:\.\d+)?),\s*(?P<y>-?\d+(?:\.\d+)?)\)")


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


def _offset_label(text: str) -> str | None:
    match = NODE_AT_RE.search(text)
    if match is None:
        return None
    x = float(match.group("x"))
    replacement = f"at ({x + 0.10:.2f}, {match.group('y')})"
    return NODE_AT_RE.sub(replacement, text, count=1)


def _candidate_selector(selectors: list[dict[str, Any]]) -> dict[str, Any] | None:
    for selector in selectors:
        text = str(selector.get("text", ""))
        if (
            text.lstrip().startswith("\\node")
            and any(term in text for term in ENERGY_TERMS)
            and _offset_label(text) is not None
        ):
            return selector
    return None


def _candidate(
    *,
    name: str,
    panel_model: dict[str, Any],
    selector: dict[str, Any],
) -> dict[str, Any]:
    source_rel = selector.get("path")
    original = str(selector.get("text", ""))
    replacement = _offset_label(original)
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
    if family in KNOWN_UNSUPPORTED_PANEL_FAMILIES:
        return _refusal(name, source, "unsupported_panel_family")
    if family != SUPPORTED_FAMILY:
        return _refusal(name, source, "unsupported_candidate_family")
    if panel != SUPPORTED_PANEL:
        return _refusal(name, source, "unsupported_panel_family")

    panel_model = candidate_panel_model.build_panel_model(
        name,
        panel,
        workspace_root=paths.workspace_root,
        plugin_root=paths.plugin_root,
    )
    if {"code": "panel_not_declared"} in panel_model.get("refusals", []):
        return _refusal(name, source, "panel_not_declared")
    selectors = [
        item
        for item in panel_model.get("selectors", [])
        if isinstance(item, dict)
    ]
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
