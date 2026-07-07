"""Auto-patch eligibility classification for fig_loop."""

from __future__ import annotations

from typing import Any

AUTO_PATCH_CLASSES = {
    "label_offset",
    "text_overlap",
    "clipping",
    "whitespace_balance",
    "palette_style",
    "line_weight_style",
}

HUMAN_REVIEW_CLASSES = {
    "aesthetic_direction",
    "chemistry_topology",
    "physical_mechanism",
    "causal_arrow_semantics",
    "theory_guard_evidence",
    "reference_interpretation",
    "accepted_golden_export_build_state",
    "publication_safety",
    "critique_mutation",
    "broad_refactor",
}

REQUIRED_EVIDENCE = [
    "before compile/export evidence",
    "after compile/export evidence",
    "rollback path",
]


def _structured_patch_classes(
    loop_decision: dict[str, Any],
    patch_handoff: dict[str, Any],
) -> list[str]:
    values: list[Any] = [
        patch_handoff.get("patch_class"),
        patch_handoff.get("patch_classes"),
    ]
    active_patch_target = loop_decision.get("active_patch_target")
    if isinstance(active_patch_target, dict):
        values.extend(
            [
                active_patch_target.get("patch_class"),
                active_patch_target.get("patch_classes"),
            ]
        )

    classes: list[str] = []
    for value in values:
        if isinstance(value, str) and value:
            classes.append(value)
        elif isinstance(value, list):
            classes.extend(item for item in value if isinstance(item, str) and item)
    return sorted(dict.fromkeys(classes))


def auto_patch_eligibility(
    loop_decision: dict[str, Any],
    patch_handoff: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not patch_handoff:
        return None

    patch_classes = _structured_patch_classes(loop_decision, patch_handoff)
    allowed = [value for value in patch_classes if value in AUTO_PATCH_CLASSES]
    blocked = [value for value in patch_classes if value in HUMAN_REVIEW_CLASSES]

    if blocked:
        level = "human_review_required"
    elif allowed:
        level = "auto_patch_candidate"
    else:
        level = "patch_assisted_only"

    return {
        "level": level,
        "target_type": patch_handoff["target_type"],
        "target_id": patch_handoff["target_id"],
        "allowed_reasons": allowed,
        "blocked_reasons": blocked,
        "required_evidence": list(REQUIRED_EVIDENCE),
        "may_edit": False,
    }
