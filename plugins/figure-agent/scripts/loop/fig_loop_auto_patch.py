"""Auto-patch eligibility classification for fig_loop."""

from __future__ import annotations

from typing import Any

ALLOWED_TERMS = {
    "label offset": ("label offset", "offset label", "move the label", "move label"),
    "text overlap": ("overlap", "crowding", "crowded", "collision"),
    "clipping": ("clip",),
    "whitespace balance": ("whitespace",),
    "palette/style": ("palette violation", "style violation"),
    "line weight/style": ("line weight", "stroke weight"),
}

BLOCKED_TERMS = {
    "aesthetic direction": ("aesthetic", "art direction", "visual taste"),
    "chemistry topology": ("chemistry", "topology", "molecule", "bond"),
    "physical mechanism": ("mechanism", "causal", "physics"),
    "causal arrow semantics": ("arrow semantics", "causal arrow"),
    "theory guard evidence": ("theory", "guard"),
    "reference interpretation": ("reference", "interpretation"),
    "accepted/golden/export/build state": ("accepted", "golden", "export", "build"),
    "publication safety": ("publication", "safety"),
    "critique mutation": ("critique.md", "critique mutation"),
    "broad refactor": ("refactor", "rewrite"),
}

REQUIRED_EVIDENCE = [
    "before compile/export evidence",
    "after compile/export evidence",
    "rollback path",
]


def auto_patch_eligibility(
    loop_decision: dict[str, Any],
    patch_handoff: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not patch_handoff:
        return None

    haystack = " ".join(
        str(value)
        for value in (
            patch_handoff.get("target_id"),
            patch_handoff.get("patch_target"),
            patch_handoff.get("reason"),
            loop_decision.get("recommended_next_action"),
        )
        if value
    ).lower()
    allowed = [
        name
        for name, terms in ALLOWED_TERMS.items()
        if any(term in haystack for term in terms)
    ]
    blocked = [
        name
        for name, terms in BLOCKED_TERMS.items()
        if any(term in haystack for term in terms)
    ]

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
