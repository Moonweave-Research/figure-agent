"""Panel-aware candidate families for real figure improvement proposals."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import bounded_coordinate_offset
import bounded_text_width
import candidate_contracts
import candidate_panel_model
import fixture_identity
import gradient_depth_fill
import line_weight_tier
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
    "label_offset": "label_offset",
    "text_width_refit": "text_width_refit",
    "connector-routing": "leader_line_reroute",
    "panel-layout": "panel_spacing_adjust",
    "panel_spacing_adjustment": "panel_spacing_adjust",
    "contrast-repair": "contrast_boost",
    "annotation-box-layout": "annotation_box_resize",
    "line-weight-tier": "line_weight_style",
    "stroke_hierarchy_adjustment": "line_weight_style",
    "gradient-depth-fill": "gradient_depth_fill",
    "nonsemantic_background_quieting": "gradient_depth_fill",
}
CANONICAL_EXPECTED_DELTA = {
    "label_offset": "improve label clearance",
    "text_width_refit": "refit wrapped label footprint without changing label text",
    "leader_line_reroute": "reduce leader-line label collision risk",
    "panel_spacing_adjust": "increase panel boundary clearance",
    "contrast_boost": "increase low-contrast element legibility",
    "annotation_box_resize": "reduce annotation-box internal collision risk",
    "line_weight_style": "tier line weights for narrative rhythm",
    "gradient_depth_fill": "add material depth via same-hue gradient",
}
# Default tier when a line-weight-tier family candidate carries no explicit
# variant: raise the targeted path to the primary narrative spine.
_DEFAULT_LINE_WEIGHT_TIER = "primary"
# Depth step (percent points) for the dark stop derived from a flat fill's own
# base hue; keeps the gradient same-hue by construction.
_GRADIENT_DEPTH_STEP_PCT = 16
_FLAT_FILL_BASE_RE = re.compile(
    r"^\s*\\fill\[\s*(?P<base>[A-Za-z][A-Za-z0-9]*)(?:!(?P<pct>\d+))?\b"
)
_TEXT_WIDTH_RE = re.compile(r"text width\s*=\s*(?P<w>-?\d+(?:\.\d+)?)\s*cm")


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


def _gradient_stops_for(text: str) -> tuple[str, str] | None:
    """Derive a same-hue (light, dark) pair from a flat fill's own base token."""
    match = _FLAT_FILL_BASE_RE.match(text)
    if match is None:
        return None
    base = match.group("base")
    light_pct = int(match.group("pct")) if match.group("pct") else 100
    dark_pct = min(light_pct + _GRADIENT_DEPTH_STEP_PCT, 100)
    light = f"{base}!{light_pct}" if match.group("pct") else base
    dark = f"{base}!{dark_pct}"
    return light, dark


def _apply_edit_transform(edit_class: str, text: str) -> tuple[str, str] | None:
    """Return (replacement, semantic_kind) for an edit class, or None if N/A."""
    if edit_class == "text_width_refit":
        match = _TEXT_WIDTH_RE.search(text)
        if match is None:
            return None
        target_cm = float(match.group("w")) + 0.4
        replacement = bounded_text_width.set_text_width(text, target_cm=target_cm)
        return (replacement, "text_width_refit") if replacement is not None else None
    if edit_class == "line_weight_style":
        replacement = line_weight_tier.retier_line_width(text, tier=_DEFAULT_LINE_WEIGHT_TIER)
        return (replacement, "line_weight_tier") if replacement is not None else None
    if edit_class == "gradient_depth_fill":
        stops = _gradient_stops_for(text)
        if stops is None:
            return None
        light, dark = stops
        replacement = gradient_depth_fill.shade_flat_fill(text, light=light, dark=dark)
        return (replacement, "gradient_depth_fill") if replacement is not None else None
    replacement = bounded_coordinate_offset.offset_first_coordinate(text)
    return (replacement, "bounded_coordinate_offset") if replacement is not None else None


def _semantic_risks_for(edit_class: str) -> list[str]:
    if edit_class == "label_offset":
        return []
    if edit_class == "text_width_refit":
        return [
            "text-width refit must preserve label text and semantic binding after render review"
        ]
    if edit_class == "panel_spacing_adjust":
        return [
            "panel-spacing adjustment must not change panel identity, ordering, "
            "or scientific claims"
        ]
    if edit_class == "line_weight_style":
        return [
            "narrative-rhythm retier is an aesthetic taste call; "
            "human must confirm the spine/annotation/secondary hierarchy reads correctly"
        ]
    if edit_class == "gradient_depth_fill":
        return [
            "same-hue depth gradient is an aesthetic taste call; "
            "human must confirm the added material depth improves the figure"
        ]
    return ["synthetic smoke candidate needs human visual review before apply"]


def _edit_class_selector(
    selectors: list[dict[str, Any]],
    edit_class: str,
) -> dict[str, Any] | None:
    for selector in selectors:
        text = str(selector.get("text", ""))
        if _apply_edit_transform(edit_class, text) is not None:
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
    edit_class = CANONICAL_FAMILY_EDIT_CLASS[family]
    transform = _apply_edit_transform(edit_class, original)
    if transform is None:
        return None
    replacement, semantic_kind = transform
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
            "semantic_kind": semantic_kind,
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
                "semantic_kind": semantic_kind,
                "path": source_rel,
                "original": original,
                "replacement": replacement,
            }
        ],
        "risk": "medium" if edit_class != "label_offset" else "low",
        "expected_delta": [CANONICAL_EXPECTED_DELTA[edit_class]],
        "semantic_risks": _semantic_risks_for(edit_class),
        "boundedness": {
            "changes": CANONICAL_EXPECTED_DELTA[edit_class],
            "does_not_change": [
                "fixture source unless separately applied",
                "accepted state",
                "tracked golden exports",
                "release state",
                "SVG artifacts",
            ],
            "requires_human_review": True,
            "not_svg_polish": True,
        },
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
    edit_class = CANONICAL_FAMILY_EDIT_CLASS[family]
    selector = _edit_class_selector(selectors, edit_class)
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
