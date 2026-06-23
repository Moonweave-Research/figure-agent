from __future__ import annotations

from pathlib import Path
from typing import Final

import composition_scene
import fixture_identity

COMPOSITION_LINT_SCHEMA: Final = "figure-agent.composition-lint.v1"
PLOT_KINDS: Final = frozenset({"inset_plot", "mini_plot", "plot", "sparkline"})
ANNOTATION_KINDS: Final = frozenset({"annotation", "text_label", "callout"})
ARROW_KINDS: Final = frozenset({"arrow", "measurement_span"})
HUMAN_COMMENTARY_REASONS: Final = {
    "measurement_arrow_crosses_data": "requires_rendered_geometry",
    "thin_glitch_primitive": "requires_rendered_geometry",
    "panel_density_imbalance": "requires_rendered_geometry_or_bbox_density",
    "path_mechanicalness": "requires_human_path_morphology_review",
}


def _object_items(scene: dict[str, object]) -> list[tuple[str, dict[str, object]]]:
    objects = scene.get("objects")
    if not isinstance(objects, dict):
        return []
    return [
        (str(object_id), payload)
        for object_id, payload in objects.items()
        if isinstance(payload, dict)
    ]


def _object_ids(scene: dict[str, object]) -> set[str]:
    return {object_id for object_id, _payload in _object_items(scene)}


def _panel_ids(scene: dict[str, object]) -> list[str]:
    panels = scene.get("panels")
    if not isinstance(panels, list):
        return []
    panel_ids: list[str] = []
    for panel in panels:
        if isinstance(panel, dict) and isinstance(panel.get("id"), str):
            panel_ids.append(panel["id"])
    return panel_ids


def _deterministic_finding(
    check: str,
    metric: str,
    threshold: dict[str, int],
    evidence_object: dict[str, object],
) -> dict[str, object]:
    return {
        "check": check,
        "mode": "deterministic",
        "metric": metric,
        "threshold": threshold,
        "evidence_object": evidence_object,
        "rank_eligible": True,
        "blocking_allowed": False,
    }


def _human_commentary(check: str, reason: str) -> dict[str, object]:
    return {
        "check": check,
        "mode": "human_commentary",
        "reason": reason,
        "rank_eligible": False,
        "blocking_allowed": False,
    }


def _orphan_plot_findings(scene: dict[str, object]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for object_id, payload in _object_items(scene):
        if payload.get("kind") in PLOT_KINDS and not payload.get("anchor_target"):
            findings.append(
                _deterministic_finding(
                    "orphan_plot",
                    "unanchored_plot_count",
                    {"review": 1},
                    {
                        "object_id": object_id,
                        "panel": payload.get("panel"),
                        "kind": payload.get("kind"),
                        "anchor_target": None,
                    },
                )
            )
    return findings


def _floating_annotation_findings(scene: dict[str, object]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for object_id, payload in _object_items(scene):
        is_annotation = payload.get("kind") in ANNOTATION_KINDS
        has_anchor = bool(payload.get("anchor_target"))
        is_caption = payload.get("role") == "panel_caption"
        if is_annotation and not has_anchor and not is_caption:
            findings.append(
                _deterministic_finding(
                    "floating_annotation",
                    "unanchored_annotation_count",
                    {"review": 1},
                    {
                        "object_id": object_id,
                        "panel": payload.get("panel"),
                        "kind": payload.get("kind"),
                        "role": payload.get("role"),
                        "anchor_target": None,
                    },
                )
            )
    return findings


def _arrow_clutter_findings(scene: dict[str, object]) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for panel_id in _panel_ids(scene):
        arrow_ids = sorted(
            object_id
            for object_id, payload in _object_items(scene)
            if payload.get("panel") == panel_id and payload.get("kind") in ARROW_KINDS
        )
        if len(arrow_ids) > 3:
            findings.append(
                _deterministic_finding(
                    "arrow_clutter",
                    "arrow_like_object_count",
                    {"review": 3},
                    {"panel": panel_id, "object_ids": arrow_ids, "count": len(arrow_ids)},
                )
            )
    return findings


def _anchor_ambiguity_findings(scene: dict[str, object]) -> list[dict[str, object]]:
    known_ids = _object_ids(scene)
    findings: list[dict[str, object]] = []
    for object_id, payload in _object_items(scene):
        anchor = payload.get("anchor_target")
        if isinstance(anchor, str) and anchor not in known_ids:
            findings.append(
                _deterministic_finding(
                    "anchor_ambiguity",
                    "unresolved_anchor_target_count",
                    {"review": 1},
                    {
                        "object_id": object_id,
                        "panel": payload.get("panel"),
                        "anchor_target": anchor,
                    },
                )
            )
    return findings


def _findings(scene: dict[str, object]) -> list[dict[str, object]]:
    findings = [
        *_orphan_plot_findings(scene),
        *_floating_annotation_findings(scene),
        *_arrow_clutter_findings(scene),
        *_anchor_ambiguity_findings(scene),
        *[
            _human_commentary(check, reason)
            for check, reason in sorted(HUMAN_COMMENTARY_REASONS.items())
        ],
    ]
    return sorted(findings, key=lambda item: str(item["check"]))


def build_composition_lint(
    name: str,
    *,
    workspace_root: Path | None = None,
) -> dict[str, object]:
    fixture_identity.validate_fixture_name(name)
    scene = composition_scene.build_semantic_scene_model(name, workspace_root=workspace_root)
    if scene.get("status") == "blocked":
        return {
            "schema": COMPOSITION_LINT_SCHEMA,
            "fixture": name,
            "status": "blocked",
            "findings": [],
            "diagnostics": scene.get("diagnostics", []),
        }
    return {
        "schema": COMPOSITION_LINT_SCHEMA,
        "fixture": name,
        "status": "ready",
        "findings": _findings(scene),
        "diagnostics": [],
    }
