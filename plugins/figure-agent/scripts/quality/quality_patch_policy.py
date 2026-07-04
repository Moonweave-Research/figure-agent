"""Patchability policy for the figure quality-improvement loop."""

from __future__ import annotations

from pathlib import Path
from typing import Any

SCHEMA = "figure-agent.quality-patch-policy.v1"

SAFE_CLASSES = {
    "label_offset": "mechanical_label_offset",
    "text_overlap": "mechanical_text_overlap",
    "whitespace_balance": "mechanical_whitespace_balance",
    "line_weight_style": "mechanical_style_normalization",
    "gradient_depth_fill": "bounded_gradient_depth_fill",
    "svg_visual_polish": "bounded_svg_visual_polish",
}
HUMAN_CLASSES = {
    "aesthetic_direction",
    "reference_balance",
    "semantic_meaning",
    "taste_decision",
    "publication_gate",
}


def _safe_fixture_relative_path(value: str) -> bool:
    path = Path(value)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and len(path.parts) >= 3
        and path.parts[0] == "examples"
    )


def classify_patchability(defect: dict[str, Any]) -> dict[str, Any]:
    """Return a stable patchability decision for one normalized defect."""
    defect_class = str(defect.get("defect_class") or "")
    evidence = defect.get("evidence")
    affected_files = defect.get("affected_files")
    blocked_codes: list[str] = []

    if not isinstance(evidence, list) or not evidence:
        blocked_codes.append("missing_evidence")
    if not isinstance(affected_files, list) or not affected_files:
        blocked_codes.append("missing_affected_file")
    else:
        for path in affected_files:
            if not isinstance(path, str) or not _safe_fixture_relative_path(path):
                blocked_codes.append("path_escape")
                break

    if defect_class in HUMAN_CLASSES:
        blocked_codes.append(defect_class)
        state = "human_required"
        reasons: list[str] = []
    elif defect_class in SAFE_CLASSES and not blocked_codes:
        state = "safe_candidate"
        reasons = [SAFE_CLASSES[defect_class]]
    elif blocked_codes:
        state = "unsupported"
        reasons = []
    else:
        state = "assisted_only"
        reasons = []

    return {
        "state": state,
        "reasons": reasons,
        "blocked_codes": sorted(set(blocked_codes)),
        "may_edit": False,
        "policy_version": SCHEMA,
    }
