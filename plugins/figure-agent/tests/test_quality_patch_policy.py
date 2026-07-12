from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import quality_patch_policy  # noqa: E402


def _defect(**overrides: object) -> dict:
    payload = {
        "id": "QD001",
        "defect_class": "text_overlap",
        "owner": "tool",
        "affected_files": ["examples/quality_demo/quality_demo.tex"],
        "evidence": [{"uri": "figure://quality_demo/audit/text-boundary"}],
        "attribution": {"state": "exact"},
        "selector_hint": {
            "kind": "semantic_anchor",
            "selector_id": "panel_f.label.repulsion",
            "anchor_start": "% figure-agent:start panel_f.label.repulsion",
            "anchor_end": "% figure-agent:end panel_f.label.repulsion",
            "source_hash": "sha256:" + "1" * 64,
        },
        "protected_invariants": ["panel_f.electrode_relation"],
        "patchability": {"state": "safe_candidate", "reasons": []},
    }
    payload.update(overrides)
    return payload


def test_policy_marks_narrow_text_overlap_as_safe_candidate() -> None:
    result = quality_patch_policy.classify_patchability(_defect())

    assert result == {
        "state": "safe_candidate",
        "reasons": ["mechanical_text_overlap"],
        "blocked_codes": [],
        "may_edit": False,
        "policy_version": "figure-agent.quality-patch-policy.v1",
    }


def test_policy_blocks_semantic_and_publication_defects() -> None:
    for defect_class in (
        "aesthetic_direction",
        "reference_balance",
        "semantic_meaning",
        "taste_decision",
        "publication_gate",
    ):
        result = quality_patch_policy.classify_patchability(
            _defect(defect_class=defect_class)
        )

        assert result["state"] == "human_required"
        assert defect_class in result["blocked_codes"]
        assert result["may_edit"] is False


def test_policy_blocks_missing_evidence_and_external_paths() -> None:
    result = quality_patch_policy.classify_patchability(
        _defect(evidence=[], affected_files=["../outside.tex"])
    )

    assert result["state"] == "unsupported"
    assert "missing_evidence" in result["blocked_codes"]
    assert "path_escape" in result["blocked_codes"]


def test_safe_class_requires_exact_attribution_and_stable_selector() -> None:
    defect = _defect(
        attribution={"state": "ambiguous"},
        selector_hint={"kind": "line_range", "value": "4:4"},
    )
    result = quality_patch_policy.classify_patchability(defect)
    assert result["state"] == "assisted_only"
    assert "exact_attribution_required" in result["blocked_codes"]


def test_safe_class_requires_protected_invariants() -> None:
    defect = _defect(protected_invariants=[])
    result = quality_patch_policy.classify_patchability(defect)
    assert result["state"] == "assisted_only"
    assert "protected_invariants_required" in result["blocked_codes"]
