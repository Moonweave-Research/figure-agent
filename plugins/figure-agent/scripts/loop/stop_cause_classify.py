"""Pure, deterministic stop-cause classifier (measure-only, Slice 3).

One 7-member enum; one canonical REFUSAL_CODE -> cause table; one classifier
that consumes BOTH the candidate/refusal signal and the reference-ceiling
signal. No I/O, no LLM judgment: every emitted evidence row cites a real
source_module:source_ref so a verdict is falsifiable by re-derivation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

PURE_MECHANICAL_FAMILIES = {"bounded_coordinate_offset", "coordinate_offset", "label_offset"}
VALUE_PRESERVING_FAMILIES = {"line-weight-tier", "gradient-depth-fill"}
VALUE_PRESERVING_EDIT_CLASSES = {"line_weight_style", "gradient_depth_fill"}


class StopCause(Enum):
    gate_capped = "gate_capped"
    lever_exhausted = "lever_exhausted"
    decision_weak = "decision_weak"
    headroom_blind = "headroom_blind"
    settled_verified = "settled_verified"
    plumbing_stop = "plumbing_stop"
    not_stopped = "not_stopped"


# argmax for dominant_premature_cause is restricted to these four.
QUALITY_CAUSES: tuple[StopCause, ...] = (
    StopCause.gate_capped,
    StopCause.lever_exhausted,
    StopCause.decision_weak,
    StopCause.headroom_blind,
)

# Loop-level stop reasons -> cause. All non-quality reasons are pipeline-state
# (setup/adjudication/workflow), so they map to plumbing_stop. Source cites are
# fig_loop_decision.py line numbers (the producer).
STOP_REASON_CAUSE: dict[str, StopCause] = {
    "reference_input_missing": StopCause.plumbing_stop,  # fig_loop_decision.py:47
    "status_action_required": StopCause.plumbing_stop,  # :57,:64,:146,:156,:164
    "stale_adjudication": StopCause.plumbing_stop,  # :74
    "invalid_adjudication": StopCause.plumbing_stop,  # :81
    "ambiguous_patch_selection": StopCause.plumbing_stop,  # :100
    "patch_target_recommended": StopCause.plumbing_stop,  # :112
    "missing_adjudication": StopCause.plumbing_stop,  # :124
    "active_subregion_recommended": StopCause.plumbing_stop,  # :133
    # Quality terminal stops fall through to per-sub-region signal classification;
    # they are NOT short-circuited to a cause here.
    "human_gate_required": None,  # :91 / fig_loop.py:105
    "basin_detected": None,  # fig_loop.py:205
    "no_actionable_findings": None,  # :172
    "verify_only_complete": None,  # :179
}

# Canonical REFUSAL_CODE -> cause table. ACTIONABILITY codes are an
# evidence-quality problem (decision_weak); lever-absence codes are a missing-op
# problem (lever_exhausted); source_missing is pipeline-state (plumbing_stop).
# unsupported_candidate_family is in BOTH the actionability frozenset and the
# lever discussion; precedence resolves it to decision_weak.
REFUSAL_CODE_CAUSE: dict[str, StopCause] = {
    "stale_detector_evidence": StopCause.decision_weak,  # candidate_generator.py:26
    "unknown_panel": StopCause.decision_weak,  # :27
    "missing_selector_hash": StopCause.decision_weak,  # :28
    "unsupported_candidate_family": StopCause.decision_weak,  # :29 (precedence: decision_weak)
    "no_bounded_operation": StopCause.lever_exhausted,  # :441
    "no_supported_candidate": StopCause.lever_exhausted,  # :572
    "source_missing": StopCause.plumbing_stop,  # :549
}


@dataclass(frozen=True)
class ClassifiedStop:
    subregion_id: str
    cause: StopCause
    evidence: list[dict[str, str]] = field(default_factory=list)


def _evidence(
    signal_class: str, signal_key: str, source_module: str, source_ref: str
) -> dict[str, str]:
    return {
        "signal_class": signal_class,
        "signal_key": signal_key,
        "source_module": source_module,
        "source_ref": source_ref,
    }


def _defect_by_id(defects: list[dict[str, Any]], defect_id: str) -> dict[str, Any] | None:
    for defect in defects:
        if isinstance(defect, dict) and str(defect.get("id") or "") == defect_id:
            return defect
    return None


def _subregion_of(item: dict[str, Any]) -> str | None:
    target = item.get("target")
    if isinstance(target, dict):
        sub = target.get("subregion")
        if isinstance(sub, str) and sub:
            return sub
    return None


def _refusals_for(subregion_id: str, bundle: dict[str, Any]) -> list[dict[str, str]]:
    candidate_set = bundle.get("candidate_set") or {}
    defects = bundle.get("defects") or []
    matched: list[dict[str, str]] = []
    for refusal in candidate_set.get("refusals", []):
        if not isinstance(refusal, dict):
            continue
        defect_id = str(refusal.get("defect_id") or "")
        if defect_id:
            defect = _defect_by_id(defects, defect_id)
            if defect is not None and _subregion_of(defect) == subregion_id:
                matched.append(refusal)
        else:
            # Fixture-level refusal (e.g. no_supported_candidate / source_missing):
            # it applies to every enumerated subregion unless a defect_id narrows it.
            matched.append(refusal)
    return matched


def _candidates_for(subregion_id: str, bundle: dict[str, Any]) -> list[dict[str, Any]]:
    candidate_set = bundle.get("candidate_set") or {}
    return [
        candidate
        for candidate in candidate_set.get("candidates", [])
        if isinstance(candidate, dict) and _subregion_of(candidate) == subregion_id
    ]


def _is_value_preserving_lever(candidate: dict[str, Any]) -> bool:
    # Default candidates carry edit_family (candidate_generator.py:111); family
    # candidates carry family/edit_class only (candidate_families.py:262-264).
    edit_family = candidate.get("edit_family")
    if isinstance(edit_family, str):
        return edit_family not in PURE_MECHANICAL_FAMILIES
    family = candidate.get("family")
    edit_class = candidate.get("edit_class")
    return (isinstance(family, str) and family in VALUE_PRESERVING_FAMILIES) or (
        isinstance(edit_class, str) and edit_class in VALUE_PRESERVING_EDIT_CLASSES
    )


def _defect_for_subregion(subregion_id: str, bundle: dict[str, Any]) -> dict[str, Any] | None:
    for defect in bundle.get("defects") or []:
        if isinstance(defect, dict) and _subregion_of(defect) == subregion_id:
            return defect
    return None


def _residual_headroom(bundle: dict[str, Any]) -> bool:
    # Reference-free deterministic proxy (§4.5.5): any detector block has
    # candidate_count > accounted_count (audit_evidence_summary.py:44-97).
    audit = bundle.get("audit_evidence_summary") or {}
    for source in ("visual_clash", "text_boundary", "label_path", "undeclared_geometry"):
        block = audit.get(source)
        if isinstance(block, dict):
            if int(block.get("candidate_count", 0)) > int(block.get("accounted_count", 0)):
                return True
    return False


def classify_stop_cause(subregion: str, bundle: dict[str, Any]) -> ClassifiedStop:
    """Deterministic precedence: plumbing -> gate_capped -> decision_weak ->
    lever_exhausted -> headroom_blind -> settled_verified. not_stopped is only
    reachable for a live (uncommitted) decision and is never returned here for a
    terminal run (every run_manifest carries a terminal final_stop_reason)."""
    evidence: list[dict[str, str]] = []

    # Per-sub-region signals take precedence over the loop-level stop reason
    # (CORR-b): the loop may stop at a pipeline-state reason (e.g.
    # status_action_required) while a sub-region still carries a real
    # refusal/candidate signal. The loop-level plumbing reason is a FALLBACK
    # (step 5b below), applied only when a sub-region has no signal of its own.
    refusals = _refusals_for(subregion, bundle)
    refusal_causes = [REFUSAL_CODE_CAUSE.get(str(r.get("code") or "")) for r in refusals]
    if StopCause.plumbing_stop in refusal_causes:
        code = next(
            r.get("code")
            for r in refusals
            if REFUSAL_CODE_CAUSE.get(str(r.get("code") or "")) is StopCause.plumbing_stop
        )
        evidence.append(
            _evidence("refusal", str(code), "candidate_generator", "candidate_generator.py:549")
        )
        return ClassifiedStop(subregion, StopCause.plumbing_stop, evidence)

    # 2. gate_capped: a value-preserving lever candidate exists for a safe defect.
    defect = _defect_for_subregion(subregion, bundle)
    is_safe = (
        isinstance(defect, dict)
        and isinstance(defect.get("patchability"), dict)
        and defect["patchability"].get("state") == "safe_candidate"
    )
    for candidate in _candidates_for(subregion, bundle):
        if _is_value_preserving_lever(candidate) and is_safe:
            evidence.append(
                _evidence(
                    "candidate",
                    "value_preserving_lever",
                    "semantic_candidate_review",
                    "semantic_candidate_review.py:15",
                )
            )
            return ClassifiedStop(subregion, StopCause.gate_capped, evidence)

    # 3. decision_weak: evidence-quality problem (actionability refusals, uncertain
    #    crops, unadjudicated candidates).
    audit = bundle.get("audit_evidence_summary") or {}
    uncertain = (audit.get("crop_audit") or {}).get("uncertain_crop_ids") or []
    unadjudicated = int(
        (audit.get("detector_feedback") or {}).get("unadjudicated_candidate_count", 0) or 0
    )
    decision_weak_codes = [
        str(r.get("code"))
        for r in refusals
        if REFUSAL_CODE_CAUSE.get(str(r.get("code") or "")) is StopCause.decision_weak
    ]
    if decision_weak_codes:
        evidence.append(
            _evidence(
                "refusal",
                decision_weak_codes[0],
                "candidate_generator",
                "candidate_generator.py:24",
            )
        )
        return ClassifiedStop(subregion, StopCause.decision_weak, evidence)
    if subregion in uncertain:
        evidence.append(
            _evidence(
                "audit",
                "uncertain_crop_ids",
                "audit_evidence_summary",
                "audit_evidence_summary.py:74",
            )
        )
        return ClassifiedStop(subregion, StopCause.decision_weak, evidence)
    if unadjudicated > 0 and (defect is not None or refusals):
        evidence.append(
            _evidence(
                "audit",
                "unadjudicated_candidate_count",
                "audit_evidence_summary",
                "audit_evidence_summary.py:103",
            )
        )
        return ClassifiedStop(subregion, StopCause.decision_weak, evidence)

    # 4. lever_exhausted: lever-absence refusal codes.
    lever_codes = [
        str(r.get("code"))
        for r in refusals
        if REFUSAL_CODE_CAUSE.get(str(r.get("code") or "")) is StopCause.lever_exhausted
    ]
    if lever_codes:
        ref = (
            "candidate_generator.py:572"
            if "no_supported_candidate" in lever_codes
            else "candidate_generator.py:441"
        )
        evidence.append(_evidence("refusal", lever_codes[0], "candidate_generator", ref))
        return ClassifiedStop(subregion, StopCause.lever_exhausted, evidence)

    # 5. headroom_blind: positive residual-proxy headroom AND an unused premium
    #    lever candidate (never asserted from absence). Premium-band check is
    #    deferred to Slice 5; only the deterministic proxy is used here.
    unused_lever = any(_is_value_preserving_lever(c) for c in _candidates_for(subregion, bundle))
    if _residual_headroom(bundle) and unused_lever:
        evidence.append(
            _evidence(
                "audit",
                "candidate_count_gt_accounted",
                "audit_evidence_summary",
                "audit_evidence_summary.py:44",
            )
        )
        evidence.append(
            _evidence(
                "candidate",
                "unused_value_preserving_lever",
                "line_weight_tier",
                "line_weight_tier.py:12",
            )
        )
        return ClassifiedStop(subregion, StopCause.headroom_blind, evidence)

    # 5b. plumbing_stop fallback: the loop stopped at a pipeline-state reason and
    #     this sub-region carries no quality signal of its own (CORR-b).
    raw = str(bundle.get("raw_stop_reason") or "")
    if STOP_REASON_CAUSE.get(raw) is StopCause.plumbing_stop:
        evidence.append(_evidence("loop_stop", raw, "fig_loop_decision", "fig_loop_decision.py"))
        return ClassifiedStop(subregion, StopCause.plumbing_stop, evidence)

    # 6. settled_verified: no positive signal of any kind.
    evidence.append(
        _evidence(
            "settled",
            "no_positive_headroom_signal",
            "stop_cause_classify",
            "stop_cause_classify.py",
        )
    )
    return ClassifiedStop(subregion, StopCause.settled_verified, evidence)
