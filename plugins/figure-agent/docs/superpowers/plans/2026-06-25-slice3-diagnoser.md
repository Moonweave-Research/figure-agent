# Slice 3 — Stop-Point Diagnoser + Harness (measure-only) Implementation Plan

> For agentic workers: REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax.

**Goal:** Add a read-only, deterministic stop-point diagnoser that classifies every sub-region of each cohort figure into one of seven measured stop causes, writes a `stop-report.v1` per run, and gates the cohort on a non-degenerate `dominant_premature_cause` — without applying any fix.

**Architecture:** A pure classifier (`stop_cause_classify.py`) consuming both the candidate/refusal signal and the reference-ceiling signal sits below a read-only diagnoser (`fig_loop_stop_diagnoser.py`) that enumerates sub-regions from the re-read quality ledger plus the active-target set, re-invokes the candidate/audit builders read-only, classifies each sub-region, and emits the report; a pure router (`fig_loop_stop_router.py`) maps cause→fix-mode as a data descriptor only; a minimal harness (`dogfood_metrics.py` + `dogfood_cohort.json`) rolls run-dir histograms up to a `dominant_premature_cause` with a `--check` exit-code gate. No unit both classifies and acts; the diagnoser and router never mutate the run.

**Tech Stack:** Python 3.13 (`uv run`), pytest, ruff, stdlib `json`/`enum`/`pathlib`/`argparse`/`re`. No new third-party deps. All modules live under `scripts/`; tests under `tests/`. Runtime sys.path is supplied by `tests/conftest.py` (inserts `scripts/`, `scripts/checks`, `scripts/candidates`, `scripts/quality`, `scripts/loop`, `scripts/driver`, `scripts/svg_polish`).

---

## Grounding ledger (verified against real code — every classifier branch reads one of these)

All line cites verified by reading the source on branch `work/review-auto-fixes-2026-06-25`.

| Signal | Real source (fn:line) | Shape used by Slice 3 |
|---|---|---|
| 11 stop reasons | `scripts/loop/fig_loop_decision.py:47,57,64,74,81,91,100,112,124,133,146,156,164,172,179` | `loop_decision()["stop_reason"]` string |
| Reroute → `human_gate_required` | `scripts/fig_loop.py:_apply_aesthetic_lever_stop:92` (writes `:105`), `_apply_external_vision_stop:114`, `_apply_reference_aesthetic_metrics_stop:158` | lever_id embedded **only in prose** `recommended_next_action:106` |
| Reroute → `basin_detected` | `scripts/fig_loop.py:_apply_basin_stop:199` (writes `:205`) | `basin_summary` persisted at `:405` (often absent) |
| Persisted run state | `scripts/fig_loop.py:377-405` | iteration_001.json keys: `status`, `audit_evidence`, `aesthetic_lever_summary`, `human_gate_status`, `active_patch_target`, `recommended_next_action`; **optional**: `basin_summary` (:405), `reference_aesthetic_metrics_summary` (:403) |
| Sub-region key (STRING) | `scripts/quality/quality_defect_ledger.py:_subregion_for_defect:130` → `sel:<12hex>` (:143/:146) or `<defect_class>#<index>` (:152); `_assign_subregion_keys:155` called at `:680` | defect `target["subregion"]` |
| Ledger builder | `scripts/quality/quality_defect_ledger.py:build_quality_defect_ledger:632` | `build_quality_defect_ledger(name) -> {"defects":[...]}`; defect has `id` (QD###, :543), `target.{panel,subregion}`, `patchability.state`, `actionability.gaps`, `defect_class` |
| Candidate set (diagnoser-invoked, read-only) | `scripts/candidates/candidate_generator.py:build_candidate_set:511`; `_validate_output_path` no-ops when `output_path is None` (:52) | `build_candidate_set(name) -> {"candidates":[...],"refusals":[...]}`; refusal = `{"code","defect_id"?}` |
| Default candidate fields | `candidate_generator.py:107-159` | `edit_family="bounded_coordinate_offset"` (:111), `target`, `edit_class="label_offset"` |
| Family candidate fields | `scripts/candidates/candidate_families.py:262-311` | `family` (`line-weight-tier`/`gradient-depth-fill`), `edit_class` (`line_weight_style`/`gradient_depth_fill`), **no `edit_family` key**; `CANONICAL_FAMILY_EDIT_CLASS:24` |
| Refusal codes | `candidate_generator.py:ACTIONABILITY_REFUSAL_CODES:24` = `{stale_detector_evidence, unknown_panel, missing_selector_hash, unsupported_candidate_family}`; inline `no_bounded_operation:441`, `no_supported_candidate:572`, `source_missing:549` |
| Semantic blocking | `scripts/semantic_candidate_review.py:PURE_MECHANICAL_FAMILIES:15`; `build_semantic_review_state:205` requires `(example_dir, manifest_path, manifest, *, spec=None)`; `blocks_apply` key `:65`; `semantic_blocking_reasons:257` |
| Audit summary | `scripts/audit_evidence_summary.py:summarize_audit_evidence:459`; `crop_audit.uncertain_crop_ids:74`; `detector_feedback.unadjudicated_candidate_count:103`; per-detector `candidate_count`/`accounted_count` (`visual_clash`/`text_boundary`/`label_path`/`undeclared_geometry`) |
| Reference metric state | `scripts/reference_aesthetic_metrics.py:reference_aesthetic_metrics_summary:368` → `evaluation_state ∈ {passed,warning,severe_divergence,skipped,missing}` (`:444,450`). **No premium band exists.** |
| Lever tiers | `scripts/line_weight_tier.py:TIERS:12`, `FLOOR_PT:13`; **no `CEILING_PT`** |
| Active target rows | `scripts/subregion_active_set.py:parse_active_target_rows:83` → `[ActiveTargetRow(state,raw_id,ids,evidence,notes)]`; `active_subregion_ids:101` |
| Write report | `scripts/loop/fig_loop_records.py:write_json:18` |
| Mirror row | `scripts/subregion_iteration_log.py:append_iteration_row:95` (raises `SubregionIterationLogError:107` if log missing); `subregion_iteration_log_template:40`, `write_subregion_iteration_log:61` |
| Route sinks (data strings only) | `scripts/critique_schema_vocab.py:human_art_direction:255`, `needs_human_art_direction:281`; `scripts/critique_brief_sections.py:journal_quality_axes:63` |

**Measured cohort state (empirical, this branch):** fresh `run_loop` on all three cohort fixtures stops at **`status_action_required` (100% plumbing at the loop level)**. Per-sub-region ledger classification is non-degenerate: fig2 → 6 sub-regions all carrying `stale_detector_evidence` refusals → `decision_weak`; fig3 → 1 sub-region (`acceptance_not_declared#0`, refusal `no_supported_candidate`) → `lever_exhausted`. **The diagnoser therefore classifies per sub-region from the ledger+candidate signal regardless of the loop-level plumbing stop**, which is what makes the cohort gate non-degenerate. Only fig1 has a `subregion_iteration_log.md`; fig2/fig3 do not (mirror step must guard).

---

## Applied critic corrections (correction wins; noted)

1. **Six unhandled stop reasons mapped (CORR a).** `{stale_adjudication, invalid_adjudication, missing_adjudication, ambiguous_patch_selection, patch_target_recommended, active_subregion_recommended, status_action_required, reference_input_missing}` → `plumbing_stop` (all setup/pipeline-state, with per-reason `fig_loop_decision.py` line cites). None silently bucket as `settled_verified` or `not_stopped`.
2. **Per-sub-region classification drives the gate (CORR b).** The loop-level stop is recorded as `raw_stop_reason`; the histogram is built from per-sub-region classification of the re-read ledger + diagnoser-invoked candidate set, so the gate is non-degenerate even when the loop stops at plumbing. `--check` still EXITS NON-ZERO if the cohort is 100% plumbing/settled (honest "fix plumbing first").
3. **Real STRING sub-region key everywhere (CORR c).** `subregion_id` = exact `quality_defect_ledger` string (`sel:<12hex>` / `<class>#<n>`). The spec's `F::sha256:…` example is fictional and is corrected.
4. **Three builders re-invoked read-only (CORR d).** `build_candidate_set(name)` (no panel/family/output_path), `build_quality_defect_ledger(name)`, `summarize_audit_evidence(example_dir)`. `aesthetic_lever_summary`, `basin_summary`, `reference_aesthetic_metrics_summary`, `status` read from stored `iteration_001.json`.
5. **`gate_capped(ii)` tests per candidate SHAPE (CORR e).** default candidate → `edit_family not in PURE_MECHANICAL_FAMILIES`; family candidate (no `edit_family`) → `family in {line-weight-tier, gradient-depth-fill}`.
6. **Reroute attribution stays read-only (CORR f).** lever_id parsed from `recommended_next_action` prose; basin recurrence read from stored `basin_summary`. `gate_capped(iii)` and the basin→`decision_weak` branch are **best-effort, prose-derived**, marked unverifiable-until-structured-tag; they never crash, they fall through to the deterministic branches.
7. **Enum + histogram exact 7 lowercase strings (CORR g).** `dominant_premature_cause` = argmax over **four quality causes only** `{gate_capped, lever_exhausted, decision_weak, headroom_blind}`. REFUSAL_CODE table covers `source_missing → plumbing_stop` and resolves `unsupported_candidate_family` by precedence (decision_weak wins over lever_exhausted).
8. **Minimal harness (CORR h).** Cohort histogram roll-up → `dominant_premature_cause` + `--check` non-degeneracy exit code. No `ceiling_distance`/`autonomy_fraction`/`regression`/series (deferred to Slice 4+).
9. **Router carries refusal code STRING, never `anti_pattern_id` (CORR — 0 fields verified).** `Route(cause, fix_mode, action, payload, blocked_by)` and nothing more.
10. **Mirror guarded (CORR — append raises on missing log).** Mirror only when `subregion_iteration_log.md` exists; only dominant-cause rows; `Why = "<stop_cause>; <one-line evidence with source_ref>"`. fig2/fig3 (no log) skip the mirror and keep only the run-dir report.

**Deferred (out of Slice 3 scope):** premium-band ceiling metric (Slice 5); `anti_pattern_id`→edit_class mapping / HAND registry (Slice 5+); `headroom.json`/`_headroom_anchor_violations`/pairwise proposer/`accept_headroom`/continuation precondition (Slice 5); `autonomy_frontier_ledger`/graduation/`may_edit`-conditional/`CLASS_VERIFIERS`/semantic-recheck (Slice 4); `ceiling_distance`/`human_touch_count`/`autonomy_fraction`/`per_cause` series/`regression_count` (Slice 4+). `headroom_blind(ii)` (premium band) is dropped; only the deterministic residual proxy (§4.5.5) is used. `not_stopped` is near-vacuous for committed runs (every `run_manifest` has a terminal `final_stop_reason`); retained for the live-decision call signature only.

---

## File Structure

| File | Responsibility |
|---|---|
| `scripts/loop/stop_cause_classify.py` | The single 7-member `StopCause` enum, the canonical `REFUSAL_CODE_CAUSE` + `STOP_REASON_CAUSE` tables, and the pure `classify_stop_cause(subregion, bundle) -> ClassifiedStop`. No I/O, no other-module imports beyond stdlib + the two gate tables it reads. |
| `scripts/loop/fig_loop_stop_diagnoser.py` | Read-only: enumerate sub-regions (ledger composite keys + active-target set), build the signal bundle (re-invoke `build_candidate_set`/`build_quality_defect_ledger`/`summarize_audit_evidence`; read stored summaries), classify each, write `stop-report.v1` via `write_json`, mirror dominant-cause rows via `append_iteration_row` (guarded). |
| `scripts/loop/fig_loop_stop_router.py` | Pure `route_stop_cause(subregion_report) -> Route` data descriptor (cause→fix_mode). No apply, no fix-mode import. |
| `scripts/dogfood_metrics.py` | Cohort/run-dir roll-up of cause histograms → `dominant_premature_cause`; `--check` exit-code non-degeneracy gate. Minimal — no deferred series. |
| `scripts/dogfood_cohort.json` | The 3 verified fixtures: fig1 (regression anchor — Slice-3 role = recorded cohort member only), fig2, fig3. |
| `scripts/loop/fig_loop_decision.py` (edit) | Add module-level `TERMINAL_STOPS` and `PLUMBING_STOPS` frozensets (the trigger superset) for the diagnoser to import. |
| (mirror logic lives inside `fig_loop_stop_diagnoser.py`) | The Why-mirror is a guarded call within the diagnoser; no separate file. |
| `tests/test_stop_cause_classify.py` | Unit tests for the pure classifier + tables. |
| `tests/test_fig_loop_stop_diagnoser.py` | Tests enumeration + bundle + report write + guarded mirror on real fixtures. |
| `tests/test_fig_loop_stop_router.py` | Tests the pure router table. |
| `tests/test_dogfood_metrics.py` | Tests roll-up + `--check` exit codes (degenerate fails, non-degenerate passes). |
| `tests/test_slice3_cohort_dogfood.py` | The REAL outcome gate: runs the loop on fig2+fig3, diagnoses, rolls up, asserts non-degenerate. |

---

## Task 1 — `stop_cause_classify.py`: enum + tables + pure classifier

**Files:** `scripts/loop/stop_cause_classify.py`, `tests/test_stop_cause_classify.py`

- [ ] Write the failing test (COMPLETE):

```python
# tests/test_stop_cause_classify.py
from __future__ import annotations

from stop_cause_classify import (
    StopCause,
    REFUSAL_CODE_CAUSE,
    STOP_REASON_CAUSE,
    QUALITY_CAUSES,
    classify_stop_cause,
)


def _bundle(*, refusals=None, candidates=None, defects=None, audit=None,
            aesthetic_lever_summary=None, basin_summary=None,
            reference_aesthetic_metrics_summary=None,
            raw_stop_reason="no_actionable_findings",
            recommended_next_action=""):
    return {
        "raw_stop_reason": raw_stop_reason,
        "recommended_next_action": recommended_next_action,
        "candidate_set": {"candidates": candidates or [], "refusals": refusals or []},
        "defects": defects or [],
        "audit_evidence_summary": audit or {
            "crop_audit": {"uncertain_crop_ids": []},
            "detector_feedback": {"unadjudicated_candidate_count": 0},
        },
        "aesthetic_lever_summary": aesthetic_lever_summary,
        "basin_summary": basin_summary,
        "reference_aesthetic_metrics_summary": reference_aesthetic_metrics_summary,
    }


def test_enum_has_exactly_seven_lowercase_members():
    assert {c.value for c in StopCause} == {
        "gate_capped", "lever_exhausted", "decision_weak",
        "headroom_blind", "settled_verified", "plumbing_stop", "not_stopped",
    }


def test_quality_causes_are_the_four_for_argmax():
    assert QUALITY_CAUSES == (
        StopCause.gate_capped, StopCause.lever_exhausted,
        StopCause.decision_weak, StopCause.headroom_blind,
    )


def test_plumbing_stop_reasons_all_map_to_plumbing():
    for reason in (
        "status_action_required", "reference_input_missing",
        "stale_adjudication", "invalid_adjudication", "missing_adjudication",
        "ambiguous_patch_selection", "patch_target_recommended",
        "active_subregion_recommended",
    ):
        assert STOP_REASON_CAUSE[reason] is StopCause.plumbing_stop


def test_refusal_table_covers_all_codes_with_precedence():
    assert REFUSAL_CODE_CAUSE["stale_detector_evidence"] is StopCause.decision_weak
    assert REFUSAL_CODE_CAUSE["unknown_panel"] is StopCause.decision_weak
    assert REFUSAL_CODE_CAUSE["missing_selector_hash"] is StopCause.decision_weak
    assert REFUSAL_CODE_CAUSE["unsupported_candidate_family"] is StopCause.decision_weak
    assert REFUSAL_CODE_CAUSE["no_bounded_operation"] is StopCause.lever_exhausted
    assert REFUSAL_CODE_CAUSE["no_supported_candidate"] is StopCause.lever_exhausted
    assert REFUSAL_CODE_CAUSE["source_missing"] is StopCause.plumbing_stop


def test_plumbing_precedence_first():
    bundle = _bundle(raw_stop_reason="status_action_required")
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.plumbing_stop
    assert result.evidence[0]["source_module"] == "fig_loop_decision"


def test_stale_refusal_is_decision_weak_not_lever_exhausted():
    bundle = _bundle(
        refusals=[{"code": "stale_detector_evidence", "defect_id": "QD001"}],
        defects=[{"id": "QD001", "target": {"panel": "A", "subregion": "sel:abc"}}],
    )
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.decision_weak
    assert any(e["signal_key"] == "stale_detector_evidence" for e in result.evidence)


def test_no_supported_candidate_is_lever_exhausted():
    bundle = _bundle(
        refusals=[{"code": "no_supported_candidate"}],
        defects=[{"id": "QD001", "target": {"panel": "B", "subregion": "x#0"}}],
    )
    result = classify_stop_cause("x#0", bundle)
    assert result.cause is StopCause.lever_exhausted


def test_gate_capped_family_lever_blocked_by_pure_mechanical_check():
    bundle = _bundle(
        candidates=[{
            "id": "C1", "family": "line-weight-tier", "edit_class": "line_weight_style",
            "target": {"panel": "A", "subregion": "sel:abc"},
        }],
        defects=[{"id": "QD001", "patchability": {"state": "safe_candidate"},
                  "target": {"panel": "A", "subregion": "sel:abc"}}],
    )
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.gate_capped
    assert any(e["signal_key"] == "value_preserving_lever" for e in result.evidence)


def test_decision_weak_from_uncertain_crop():
    bundle = _bundle(
        audit={
            "crop_audit": {"uncertain_crop_ids": ["sel:abc"]},
            "detector_feedback": {"unadjudicated_candidate_count": 0},
        },
        defects=[{"id": "QD001", "target": {"panel": "A", "subregion": "sel:abc"}}],
    )
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.decision_weak


def test_headroom_blind_residual_proxy_with_unused_lever():
    bundle = _bundle(
        candidates=[{
            "id": "C1", "family": "gradient-depth-fill", "edit_class": "gradient_depth_fill",
            "target": {"panel": "A", "subregion": "sel:abc"},
        }],
        defects=[{"id": "QD001", "patchability": {"state": "clean"},
                  "target": {"panel": "A", "subregion": "sel:abc"}}],
        audit={
            "crop_audit": {"uncertain_crop_ids": []},
            "detector_feedback": {"unadjudicated_candidate_count": 0},
            "text_boundary": {"candidate_count": 3, "accounted_count": 1},
        },
    )
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.headroom_blind


def test_settled_verified_when_no_signal():
    bundle = _bundle(
        defects=[{"id": "QD001", "patchability": {"state": "clean"},
                  "target": {"panel": "A", "subregion": "sel:abc"}}],
    )
    result = classify_stop_cause("sel:abc", bundle)
    assert result.cause is StopCause.settled_verified


def test_every_evidence_entry_cites_a_real_source_module():
    bundle = _bundle(
        refusals=[{"code": "no_supported_candidate"}],
        defects=[{"id": "QD001", "target": {"panel": "B", "subregion": "x#0"}}],
    )
    result = classify_stop_cause("x#0", bundle)
    for entry in result.evidence:
        assert set(entry) >= {"signal_class", "signal_key", "source_module", "source_ref"}
        assert entry["source_module"] and entry["source_ref"]
```

- [ ] Run to fail: `NO_COLOR=1 uv run pytest tests/test_stop_cause_classify.py -q` → expect `ModuleNotFoundError: No module named 'stop_cause_classify'`.

- [ ] Minimal implementation (COMPLETE):

```python
# scripts/loop/stop_cause_classify.py
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
    "reference_input_missing": StopCause.plumbing_stop,          # fig_loop_decision.py:47
    "status_action_required": StopCause.plumbing_stop,           # :57,:64,:146,:156,:164
    "stale_adjudication": StopCause.plumbing_stop,               # :74
    "invalid_adjudication": StopCause.plumbing_stop,             # :81
    "ambiguous_patch_selection": StopCause.plumbing_stop,        # :100
    "patch_target_recommended": StopCause.plumbing_stop,         # :112
    "missing_adjudication": StopCause.plumbing_stop,             # :124
    "active_subregion_recommended": StopCause.plumbing_stop,     # :133
    # Quality terminal stops fall through to per-sub-region signal classification;
    # they are NOT short-circuited to a cause here.
    "human_gate_required": None,                                 # :91 / fig_loop.py:105
    "basin_detected": None,                                      # fig_loop.py:205
    "no_actionable_findings": None,                              # :172
    "verify_only_complete": None,                                # :179
}

# Canonical REFUSAL_CODE -> cause table. ACTIONABILITY codes are an
# evidence-quality problem (decision_weak); lever-absence codes are a missing-op
# problem (lever_exhausted); source_missing is pipeline-state (plumbing_stop).
# unsupported_candidate_family is in BOTH the actionability frozenset and the
# lever discussion; precedence resolves it to decision_weak.
REFUSAL_CODE_CAUSE: dict[str, StopCause] = {
    "stale_detector_evidence": StopCause.decision_weak,          # candidate_generator.py:26
    "unknown_panel": StopCause.decision_weak,                    # :27
    "missing_selector_hash": StopCause.decision_weak,            # :28
    "unsupported_candidate_family": StopCause.decision_weak,     # :29 (precedence: decision_weak)
    "no_bounded_operation": StopCause.lever_exhausted,           # :441
    "no_supported_candidate": StopCause.lever_exhausted,         # :572
    "source_missing": StopCause.plumbing_stop,                   # :549
}


@dataclass(frozen=True)
class ClassifiedStop:
    subregion_id: str
    cause: StopCause
    evidence: list[dict[str, str]] = field(default_factory=list)


def _evidence(signal_class: str, signal_key: str, source_module: str, source_ref: str) -> dict[str, str]:
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
            # fixture-level refusal (e.g. no_supported_candidate / source_missing):
            # attach to a single-sub-region fixture or when only one sub-region exists.
            if len({_subregion_of(d) for d in defects if isinstance(d, dict)} - {None}) <= 1:
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
    return (
        (isinstance(family, str) and family in VALUE_PRESERVING_FAMILIES)
        or (isinstance(edit_class, str) and edit_class in VALUE_PRESERVING_EDIT_CLASSES)
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

    # 1. plumbing_stop (loop-level pipeline state).
    raw = str(bundle.get("raw_stop_reason") or "")
    if STOP_REASON_CAUSE.get(raw) is StopCause.plumbing_stop:
        evidence.append(_evidence("loop_stop", raw, "fig_loop_decision", "fig_loop_decision.py"))
        return ClassifiedStop(subregion, StopCause.plumbing_stop, evidence)

    refusals = _refusals_for(subregion, bundle)
    refusal_causes = [REFUSAL_CODE_CAUSE.get(str(r.get("code") or "")) for r in refusals]
    if StopCause.plumbing_stop in refusal_causes:
        code = next(r.get("code") for r in refusals
                    if REFUSAL_CODE_CAUSE.get(str(r.get("code") or "")) is StopCause.plumbing_stop)
        evidence.append(_evidence("refusal", str(code), "candidate_generator", "candidate_generator.py:549"))
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
            evidence.append(_evidence(
                "candidate", "value_preserving_lever",
                "semantic_candidate_review", "semantic_candidate_review.py:15"))
            return ClassifiedStop(subregion, StopCause.gate_capped, evidence)

    # 3. decision_weak: evidence-quality problem (actionability refusals, uncertain
    #    crops, unadjudicated candidates).
    audit = bundle.get("audit_evidence_summary") or {}
    uncertain = (audit.get("crop_audit") or {}).get("uncertain_crop_ids") or []
    unadjudicated = int((audit.get("detector_feedback") or {}).get("unadjudicated_candidate_count", 0) or 0)
    decision_weak_codes = [
        str(r.get("code")) for r in refusals
        if REFUSAL_CODE_CAUSE.get(str(r.get("code") or "")) is StopCause.decision_weak
    ]
    if decision_weak_codes:
        evidence.append(_evidence(
            "refusal", decision_weak_codes[0], "candidate_generator", "candidate_generator.py:24"))
        return ClassifiedStop(subregion, StopCause.decision_weak, evidence)
    if subregion in uncertain:
        evidence.append(_evidence(
            "audit", "uncertain_crop_ids", "audit_evidence_summary", "audit_evidence_summary.py:74"))
        return ClassifiedStop(subregion, StopCause.decision_weak, evidence)
    if unadjudicated > 0 and (defect is not None or refusals):
        evidence.append(_evidence(
            "audit", "unadjudicated_candidate_count",
            "audit_evidence_summary", "audit_evidence_summary.py:103"))
        return ClassifiedStop(subregion, StopCause.decision_weak, evidence)

    # 4. lever_exhausted: lever-absence refusal codes.
    lever_codes = [
        str(r.get("code")) for r in refusals
        if REFUSAL_CODE_CAUSE.get(str(r.get("code") or "")) is StopCause.lever_exhausted
    ]
    if lever_codes:
        ref = "candidate_generator.py:572" if "no_supported_candidate" in lever_codes else "candidate_generator.py:441"
        evidence.append(_evidence("refusal", lever_codes[0], "candidate_generator", ref))
        return ClassifiedStop(subregion, StopCause.lever_exhausted, evidence)

    # 5. headroom_blind: positive residual-proxy headroom AND an unused premium
    #    lever candidate (never asserted from absence). Premium-band check is
    #    deferred to Slice 5; only the deterministic proxy is used here.
    unused_lever = any(_is_value_preserving_lever(c) for c in _candidates_for(subregion, bundle))
    if _residual_headroom(bundle) and unused_lever:
        evidence.append(_evidence(
            "audit", "candidate_count_gt_accounted",
            "audit_evidence_summary", "audit_evidence_summary.py:44"))
        evidence.append(_evidence(
            "candidate", "unused_value_preserving_lever",
            "line_weight_tier", "line_weight_tier.py:12"))
        return ClassifiedStop(subregion, StopCause.headroom_blind, evidence)

    # 6. settled_verified: no positive signal of any kind.
    evidence.append(_evidence("settled", "no_positive_headroom_signal", "stop_cause_classify", "stop_cause_classify.py"))
    return ClassifiedStop(subregion, StopCause.settled_verified, evidence)
```

- [ ] Run to pass: `NO_COLOR=1 uv run pytest tests/test_stop_cause_classify.py -q` → expect all tests pass (`N passed`).
- [ ] Commit: `git add scripts/loop/stop_cause_classify.py tests/test_stop_cause_classify.py && git commit -m "feat(loop): Slice 3 — pure 7-cause stop classifier + refusal/stop tables"`.

---

## Task 2 — Trigger superset in `fig_loop_decision.py`

**Files:** `scripts/loop/fig_loop_decision.py`, `tests/test_fig_loop_decision.py` (append)

- [ ] Write the failing test (COMPLETE — append to the existing file's imports/tests):

```python
# tests/test_fig_loop_decision.py  (append)
def test_terminal_stops_superset_includes_reroutes():
    from fig_loop_decision import TERMINAL_STOPS, PLUMBING_STOPS
    assert TERMINAL_STOPS == frozenset({
        "no_actionable_findings", "verify_only_complete",
        "human_gate_required", "basin_detected",
    })
    assert PLUMBING_STOPS == frozenset({
        "status_action_required", "reference_input_missing",
        "stale_adjudication", "invalid_adjudication", "missing_adjudication",
        "ambiguous_patch_selection", "patch_target_recommended",
        "active_subregion_recommended",
    })


def test_trigger_sets_partition_all_eleven_reasons():
    from fig_loop_decision import TERMINAL_STOPS, PLUMBING_STOPS
    all_reasons = {
        "reference_input_missing", "status_action_required", "stale_adjudication",
        "invalid_adjudication", "human_gate_required", "ambiguous_patch_selection",
        "patch_target_recommended", "missing_adjudication",
        "active_subregion_recommended", "no_actionable_findings", "verify_only_complete",
        "basin_detected",
    }
    assert TERMINAL_STOPS | PLUMBING_STOPS == all_reasons
    assert TERMINAL_STOPS.isdisjoint(PLUMBING_STOPS)
```

- [ ] Run to fail: `NO_COLOR=1 uv run pytest tests/test_fig_loop_decision.py -q -k terminal_stops_superset` → expect `ImportError: cannot import name 'TERMINAL_STOPS'`.

- [ ] Minimal implementation — add after the imports block (top of `scripts/loop/fig_loop_decision.py`, before `def reference_input_missing`):

```python
# Trigger superset for the stop-point diagnoser. TERMINAL_STOPS carries the
# aesthetic-lever reroute (human_gate_required, fig_loop.py:105) and the basin
# reroute (basin_detected, fig_loop.py:205); PLUMBING_STOPS is every
# pipeline-state reason. Together they partition all eleven loop_decision reasons.
TERMINAL_STOPS = frozenset(
    {
        "no_actionable_findings",      # :172
        "verify_only_complete",        # :179
        "human_gate_required",         # :91 / fig_loop.py:105
        "basin_detected",              # fig_loop.py:205
    }
)
PLUMBING_STOPS = frozenset(
    {
        "status_action_required",      # :57,:64,:146,:156,:164
        "reference_input_missing",     # :47
        "stale_adjudication",          # :74
        "invalid_adjudication",        # :81
        "missing_adjudication",        # :124
        "ambiguous_patch_selection",   # :100
        "patch_target_recommended",    # :112
        "active_subregion_recommended",  # :133
    }
)
```

- [ ] Run to pass: `NO_COLOR=1 uv run pytest tests/test_fig_loop_decision.py -q` → expect all pass.
- [ ] Commit: `git add scripts/loop/fig_loop_decision.py tests/test_fig_loop_decision.py && git commit -m "feat(loop): Slice 3 — TERMINAL_STOPS/PLUMBING_STOPS trigger superset"`.

---

## Task 3 — `fig_loop_stop_diagnoser.py`: enumerate + bundle + classify + write + mirror

**Files:** `scripts/loop/fig_loop_stop_diagnoser.py`, `tests/test_fig_loop_stop_diagnoser.py`

- [ ] Write the failing test (COMPLETE — runs against a real fresh fig2 run dir + the real ledger):

```python
# tests/test_fig_loop_stop_diagnoser.py
from __future__ import annotations

import json
from pathlib import Path

import pytest

import fig_loop
from fig_loop_stop_diagnoser import diagnose_run, enumerate_subregions, build_signal_bundle

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = PLUGIN_ROOT / "examples"


@pytest.fixture
def fig2_run(tmp_path):
    return fig_loop.run_loop("fig2_trap_design_space", "slice3 test", runs_root=tmp_path)


@pytest.fixture
def fig3_run(tmp_path):
    return fig_loop.run_loop("fig3_resistance_mechanism", "slice3 test", runs_root=tmp_path)


def test_enumerate_subregions_uses_real_string_keys(fig2_run):
    subregions = enumerate_subregions("fig2_trap_design_space", fig2_run)
    assert subregions, "fig2 must enumerate ledger sub-regions"
    for sub in subregions:
        assert sub.startswith("sel:") or "#" in sub  # real key forms only


def test_build_signal_bundle_reinvokes_candidate_set(fig2_run):
    bundle = build_signal_bundle("fig2_trap_design_space", fig2_run)
    assert "candidate_set" in bundle and "candidates" in bundle["candidate_set"]
    assert "refusals" in bundle["candidate_set"]
    assert "defects" in bundle
    assert "audit_evidence_summary" in bundle
    assert "raw_stop_reason" in bundle


def test_diagnose_run_writes_stop_report_v1(fig2_run):
    report = diagnose_run("fig2_trap_design_space", fig2_run)
    report_path = fig2_run / "stop_report.json"
    assert report_path.is_file()
    written = json.loads(report_path.read_text())
    assert written["schema"] == "figure-agent.stop-report.v1"
    assert set(written["cause_histogram"]) == {
        "gate_capped", "lever_exhausted", "decision_weak",
        "headroom_blind", "settled_verified", "plumbing_stop", "not_stopped",
    }
    assert written["dominant_premature_cause"] in (
        None, "gate_capped", "lever_exhausted", "decision_weak", "headroom_blind",
    )
    # fig2 sub-regions all carry stale_detector_evidence -> decision_weak.
    assert written["cause_histogram"]["decision_weak"] >= 1
    for sub in written["subregions"]:
        assert sub["subregion_id"].startswith("sel:") or "#" in sub["subregion_id"]
        for ev in sub["evidence"]:
            assert ev["source_module"] and ev["source_ref"]


def test_diagnose_run_fig3_is_lever_exhausted(fig3_run):
    report = diagnose_run("fig3_resistance_mechanism", fig3_run)
    assert report["cause_histogram"]["lever_exhausted"] >= 1


def test_mirror_skipped_when_log_absent(fig2_run):
    # fig2 has no subregion_iteration_log.md -> mirror must not raise.
    diagnose_run("fig2_trap_design_space", fig2_run)  # no exception
    assert not (EXAMPLES / "fig2_trap_design_space" / "subregion_iteration_log.md").exists()
```

- [ ] Run to fail: `NO_COLOR=1 uv run pytest tests/test_fig_loop_stop_diagnoser.py -q` → expect `ModuleNotFoundError: No module named 'fig_loop_stop_diagnoser'`.

- [ ] Minimal implementation (COMPLETE):

```python
# scripts/loop/fig_loop_stop_diagnoser.py
"""Read-only stop-point diagnoser (Slice 3, measure-only).

Enumerates each figure's sub-regions (re-read quality ledger composite keys plus
the active-target set), assembles a per-sub-region signal bundle by re-invoking
three builders read-only and reading the run's persisted summaries, classifies
each sub-region via the pure classifier, writes a stop-report.v1 into the run
dir, and mirrors only dominant-cause rows into subregion_iteration_log.md when
that log exists. Never mutates run state; never applies a candidate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "candidates"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "quality"))

from audit_evidence_summary import summarize_audit_evidence  # noqa: E402
from candidate_generator import build_candidate_set  # noqa: E402
from fig_loop_records import write_json  # noqa: E402
from quality_defect_ledger import build_quality_defect_ledger  # noqa: E402
from stop_cause_classify import QUALITY_CAUSES, StopCause, classify_stop_cause  # noqa: E402
from subregion_active_set import active_subregion_ids, parse_active_target_rows  # noqa: E402
from subregion_iteration_log import (  # noqa: E402
    SubregionIterationLogError,
    append_iteration_row,
)

SCHEMA = "figure-agent.stop-report.v1"
_HISTOGRAM_KEYS = tuple(cause.value for cause in StopCause)


def _plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _example_dir(name: str) -> Path:
    return _plugin_root() / "examples" / name


def _read_iteration(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "iteration_001.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _read_manifest(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "run_manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}


def _ledger_defects(name: str) -> list[dict[str, Any]]:
    ledger = build_quality_defect_ledger(name)
    return [defect for defect in ledger.get("defects", []) if isinstance(defect, dict)]


def enumerate_subregions(name: str, run_dir: Path) -> list[str]:
    """Union of ledger composite keys (sel:<hex> / <class>#<n>) and active-target
    set ids. Stable, deterministic, deduplicated, order-preserving."""
    ordered: list[str] = []
    seen: set[str] = set()
    for defect in _ledger_defects(name):
        target = defect.get("target")
        sub = target.get("subregion") if isinstance(target, dict) else None
        if isinstance(sub, str) and sub and sub not in seen:
            seen.add(sub)
            ordered.append(sub)
    log_path = _example_dir(name) / "subregion_iteration_log.md"
    if log_path.is_file():
        rows = parse_active_target_rows(log_path.read_text(encoding="utf-8"))
        for sub in active_subregion_ids(rows):
            if sub and sub not in seen:
                seen.add(sub)
                ordered.append(sub)
    return ordered


def build_signal_bundle(name: str, run_dir: Path) -> dict[str, Any]:
    """Re-invoke build_candidate_set / build_quality_defect_ledger /
    summarize_audit_evidence read-only; read stored summaries from the run."""
    iteration = _read_iteration(run_dir)
    manifest = _read_manifest(run_dir)
    return {
        "raw_stop_reason": manifest.get("final_stop_reason") or iteration.get("stop_reason") or "",
        "recommended_next_action": iteration.get("recommended_next_action") or "",
        "status_result": iteration.get("status"),
        "candidate_set": build_candidate_set(name),  # output_path=None => read-only
        "defects": _ledger_defects(name),
        "audit_evidence_summary": summarize_audit_evidence(_example_dir(name)),
        "aesthetic_lever_summary": iteration.get("aesthetic_lever_summary"),
        "basin_summary": iteration.get("basin_summary"),
        "reference_aesthetic_metrics_summary": iteration.get("reference_aesthetic_metrics_summary"),
    }


def _panel_of(subregion_id: str, defects: list[dict[str, Any]]) -> str:
    for defect in defects:
        target = defect.get("target")
        if isinstance(target, dict) and target.get("subregion") == subregion_id:
            return str(target.get("panel") or "unknown")
    return "unknown"


def diagnose_run(name: str, run_dir: Path) -> dict[str, Any]:
    bundle = build_signal_bundle(name, run_dir)
    manifest = _read_manifest(run_dir)
    subregions = enumerate_subregions(name, run_dir)

    histogram = {key: 0 for key in _HISTOGRAM_KEYS}
    report_subregions: list[dict[str, Any]] = []
    for subregion_id in subregions:
        result = classify_stop_cause(subregion_id, bundle)
        histogram[result.cause.value] += 1
        report_subregions.append(
            {
                "subregion_id": subregion_id,
                "panel": _panel_of(subregion_id, bundle["defects"]),
                "stop_cause": result.cause.value,
                "settled": result.cause is StopCause.settled_verified,
                "evidence": list(result.evidence),
            }
        )

    dominant_cause, dominant_count = _dominant_premature(histogram)
    report = {
        "schema": SCHEMA,
        "fixture": name,
        "run_dir": str(run_dir),
        "commit": manifest.get("commit"),
        "branch": manifest.get("branch"),
        "raw_stop_reason": bundle["raw_stop_reason"],
        "subregions": report_subregions,
        "cause_histogram": histogram,
        "dominant_premature_cause": dominant_cause,
        "dominant_premature_count": dominant_count,
    }
    write_json(run_dir / "stop_report.json", report)
    if dominant_cause is not None:
        _mirror_dominant_rows(name, report_subregions, dominant_cause)
    return report


def _dominant_premature(histogram: dict[str, int]) -> tuple[str | None, int]:
    best_cause: str | None = None
    best_count = 0
    for cause in QUALITY_CAUSES:
        count = histogram.get(cause.value, 0)
        if count > best_count:
            best_count = count
            best_cause = cause.value
    return (best_cause, best_count)


def _mirror_dominant_rows(name: str, subregions: list[dict[str, Any]], dominant_cause: str) -> None:
    """Mirror only dominant-cause rows; skip when no log exists (flood + raise guard)."""
    log_path = _example_dir(name) / "subregion_iteration_log.md"
    if not log_path.is_file():
        return
    for sub in subregions:
        if sub["stop_cause"] != dominant_cause:
            continue
        first = sub["evidence"][0] if sub["evidence"] else {}
        why = f"{sub['stop_cause']}; {first.get('signal_key', 'n/a')} ({first.get('source_ref', 'n/a')})"
        try:
            append_iteration_row(
                log_path,
                iteration="stop-diagnosis",
                subregion_id=sub["subregion_id"],
                problem="measure-only stop diagnosis",
                patch_summary="none (measure-only)",
                result="diagnosed",
                why=why,
                follow_up="none",
            )
        except SubregionIterationLogError:
            return
```

- [ ] Run to pass: `NO_COLOR=1 uv run pytest tests/test_fig_loop_stop_diagnoser.py -q` → expect all pass (fig2 histogram `decision_weak >= 1`, fig3 `lever_exhausted >= 1`, mirror not raising).
- [ ] Commit: `git add scripts/loop/fig_loop_stop_diagnoser.py tests/test_fig_loop_stop_diagnoser.py && git commit -m "feat(loop): Slice 3 — read-only stop diagnoser (enumerate+bundle+classify+report+guarded mirror)"`.

---

## Task 4 — `fig_loop_stop_router.py`: pure data-only router

**Files:** `scripts/loop/fig_loop_stop_router.py`, `tests/test_fig_loop_stop_router.py`

- [ ] Write the failing test (COMPLETE):

```python
# tests/test_fig_loop_stop_router.py
from __future__ import annotations

from fig_loop_stop_router import Route, route_stop_cause


def _subregion_report(cause, *, refusal_codes=None, unused_lever_id=None, blocked_by=None):
    return {
        "subregion_id": "sel:abc",
        "stop_cause": cause,
        "refusal_codes": refusal_codes or [],
        "unused_lever_id": unused_lever_id,
        "blocked_by": blocked_by,
    }


def test_route_is_pure_dataclass_with_fixed_fields():
    route = route_stop_cause(_subregion_report("decision_weak"))
    assert isinstance(route, Route)
    assert set(vars(route)) == {"cause", "fix_mode", "action", "payload", "blocked_by"}


def test_gate_capped_routes_to_gate():
    route = route_stop_cause(_subregion_report("gate_capped", blocked_by="semantic_review"))
    assert route.fix_mode == "gate"
    assert route.action == "evaluate_gate_lift"
    assert route.blocked_by == "semantic_review"


def test_lever_exhausted_payload_is_refusal_code_string_not_anti_pattern_id():
    route = route_stop_cause(_subregion_report("lever_exhausted", refusal_codes=["no_supported_candidate"]))
    assert route.fix_mode == "hand"
    assert route.action in {"extend_candidate_family", "human_art_direction"}
    assert route.payload == "no_supported_candidate"
    # anti_pattern_id does not exist in candidate_families.py (0 fields) — must not appear.
    assert "anti_pattern_id" not in (route.payload if isinstance(route.payload, dict) else {})


def test_lever_exhausted_no_refusal_routes_to_human_art_direction():
    route = route_stop_cause(_subregion_report("lever_exhausted"))
    assert route.action == "human_art_direction"


def test_decision_weak_routes_to_eye():
    route = route_stop_cause(_subregion_report("decision_weak"))
    assert route.fix_mode == "eye"
    assert route.action == "ground_decision_against_reference"


def test_headroom_blind_routes_to_eye_raise_ceiling():
    route = route_stop_cause(_subregion_report("headroom_blind", unused_lever_id="line_weight_tier:hero"))
    assert route.fix_mode == "eye"
    assert route.action == "raise_critique_ceiling"
    assert route.payload == "line_weight_tier:hero"


def test_settled_and_plumbing_route_to_none():
    for cause in ("settled_verified", "plumbing_stop", "not_stopped"):
        route = route_stop_cause(_subregion_report(cause))
        assert route.fix_mode == "none"
        assert route.action is None
```

- [ ] Run to fail: `NO_COLOR=1 uv run pytest tests/test_fig_loop_stop_router.py -q` → expect `ModuleNotFoundError: No module named 'fig_loop_stop_router'`.

- [ ] Minimal implementation (COMPLETE):

```python
# scripts/loop/fig_loop_stop_router.py
"""Pure cause -> fix-mode router (Slice 3, data descriptor only — no apply).

Maps a classified sub-region report to a Route dispatch descriptor. Carries the
refusal code STRING for lever_exhausted (candidate_families.py has zero
anti_pattern_id fields; the Hand mapping is a deferred Slice-5 deliverable).
Fix-modes do not act in Slice 3; route_stop_cause never imports a fix-mode
module and never applies anything. action strings are data only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Route:
    cause: str
    fix_mode: str
    action: str | None
    payload: Any
    blocked_by: Any


def route_stop_cause(subregion_report: dict[str, Any]) -> Route:
    cause = str(subregion_report.get("stop_cause") or "")
    if cause == "gate_capped":
        return Route(cause, "gate", "evaluate_gate_lift", None, subregion_report.get("blocked_by"))
    if cause == "lever_exhausted":
        refusal_codes = subregion_report.get("refusal_codes") or []
        if refusal_codes:
            return Route(cause, "hand", "extend_candidate_family", str(refusal_codes[0]), None)
        return Route(cause, "hand", "human_art_direction", None, None)
    if cause == "decision_weak":
        return Route(cause, "eye", "ground_decision_against_reference",
                     subregion_report.get("reference_handle"), None)
    if cause == "headroom_blind":
        return Route(cause, "eye", "raise_critique_ceiling",
                     subregion_report.get("unused_lever_id"), None)
    return Route(cause, "none", None, None, None)
```

- [ ] Run to pass: `NO_COLOR=1 uv run pytest tests/test_fig_loop_stop_router.py -q` → expect all pass.
- [ ] Commit: `git add scripts/loop/fig_loop_stop_router.py tests/test_fig_loop_stop_router.py && git commit -m "feat(loop): Slice 3 — pure cause->fix-mode router (data descriptor, no apply)"`.

---

## Task 5 — `dogfood_metrics.py` + `dogfood_cohort.json`: minimal roll-up + `--check`

**Files:** `scripts/dogfood_metrics.py`, `scripts/dogfood_cohort.json`, `tests/test_dogfood_metrics.py`

- [ ] Write the failing test (COMPLETE):

```python
# tests/test_dogfood_metrics.py
from __future__ import annotations

import json
from pathlib import Path

from dogfood_metrics import (
    load_cohort,
    roll_up_run_dirs,
    is_degenerate,
    main,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _write_report(run_dir: Path, histogram: dict[str, int], dominant):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "stop_report.json").write_text(json.dumps({
        "schema": "figure-agent.stop-report.v1",
        "cause_histogram": histogram,
        "dominant_premature_cause": dominant,
    }), encoding="utf-8")


def _hist(**kw):
    base = {"gate_capped": 0, "lever_exhausted": 0, "decision_weak": 0,
            "headroom_blind": 0, "settled_verified": 0, "plumbing_stop": 0, "not_stopped": 0}
    base.update(kw)
    return base


def test_cohort_json_lists_three_verified_fixtures():
    cohort = load_cohort(PLUGIN_ROOT / "scripts" / "dogfood_cohort.json")
    assert cohort["fixtures"] == [
        "fig1_overview_v2_pair_001_vault",
        "fig2_trap_design_space",
        "fig3_resistance_mechanism",
    ]
    assert cohort["regression_anchor"] == "fig1_overview_v2_pair_001_vault"


def test_roll_up_sums_histograms_and_finds_dominant(tmp_path):
    _write_report(tmp_path / "r1", _hist(decision_weak=3), "decision_weak")
    _write_report(tmp_path / "r2", _hist(decision_weak=1, lever_exhausted=2), "decision_weak")
    summary = roll_up_run_dirs([tmp_path / "r1", tmp_path / "r2"])
    assert summary["cohort_histogram"]["decision_weak"] == 4
    assert summary["cohort_histogram"]["lever_exhausted"] == 2
    assert summary["dominant_premature_cause"] == "decision_weak"


def test_degenerate_when_all_plumbing(tmp_path):
    _write_report(tmp_path / "r1", _hist(plumbing_stop=5), None)
    summary = roll_up_run_dirs([tmp_path / "r1"])
    assert is_degenerate(summary) is True
    assert summary["dominant_premature_cause"] is None


def test_degenerate_when_all_settled(tmp_path):
    _write_report(tmp_path / "r1", _hist(settled_verified=5), None)
    summary = roll_up_run_dirs([tmp_path / "r1"])
    assert is_degenerate(summary) is True


def test_non_degenerate_with_quality_cause(tmp_path):
    _write_report(tmp_path / "r1", _hist(decision_weak=2, plumbing_stop=3), "decision_weak")
    summary = roll_up_run_dirs([tmp_path / "r1"])
    assert is_degenerate(summary) is False


def test_check_exit_nonzero_on_degenerate(tmp_path):
    _write_report(tmp_path / "r1", _hist(plumbing_stop=5), None)
    code = main(["--check", "--run-dir", str(tmp_path / "r1")])
    assert code == 1


def test_check_exit_zero_on_non_degenerate(tmp_path):
    _write_report(tmp_path / "r1", _hist(decision_weak=2), "decision_weak")
    code = main(["--check", "--run-dir", str(tmp_path / "r1")])
    assert code == 0
```

- [ ] Run to fail: `NO_COLOR=1 uv run pytest tests/test_dogfood_metrics.py -q` → expect `ModuleNotFoundError: No module named 'dogfood_metrics'`.

- [ ] Create `scripts/dogfood_cohort.json`:

```json
{
  "schema": "figure-agent.dogfood-cohort.v1",
  "fixtures": [
    "fig1_overview_v2_pair_001_vault",
    "fig2_trap_design_space",
    "fig3_resistance_mechanism"
  ],
  "regression_anchor": "fig1_overview_v2_pair_001_vault",
  "note": "fig1 is the regression anchor; in Slice 3 (measure-only) its role is solely to be a recorded cohort member whose dominant cause is logged. The ceiling_distance/regression comparison is deferred to Slice 4."
}
```

- [ ] Minimal implementation (COMPLETE):

```python
# scripts/dogfood_metrics.py
"""Minimal cohort dogfood roll-up + non-degeneracy gate (Slice 3, measure-only).

Rolls per-run stop-report cause_histograms into a cohort histogram, computes
dominant_premature_cause over the FOUR quality causes only, and --check exits
non-zero when the cohort is degenerate (no quality cause / 100% plumbing or
settled). The ceiling_distance / autonomy_fraction / regression series are
deferred to Slice 4+ and are deliberately NOT emitted here.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent / "loop"))

from stop_cause_classify import QUALITY_CAUSES, StopCause  # noqa: E402

_HISTOGRAM_KEYS = tuple(cause.value for cause in StopCause)
_QUALITY_KEYS = tuple(cause.value for cause in QUALITY_CAUSES)


def load_cohort(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _empty_histogram() -> dict[str, int]:
    return {key: 0 for key in _HISTOGRAM_KEYS}


def _dominant(histogram: dict[str, int]) -> str | None:
    best_cause: str | None = None
    best_count = 0
    for key in _QUALITY_KEYS:
        count = histogram.get(key, 0)
        if count > best_count:
            best_count = count
            best_cause = key
    return best_cause


def roll_up_run_dirs(run_dirs: list[Path]) -> dict[str, Any]:
    cohort_histogram = _empty_histogram()
    counted = 0
    for run_dir in run_dirs:
        report_path = run_dir / "stop_report.json"
        if not report_path.is_file():
            continue
        report = json.loads(report_path.read_text(encoding="utf-8"))
        histogram = report.get("cause_histogram") or {}
        for key in _HISTOGRAM_KEYS:
            cohort_histogram[key] += int(histogram.get(key, 0))
        counted += 1
    return {
        "schema": "figure-agent.dogfood-rollup.v1",
        "runs_counted": counted,
        "cohort_histogram": cohort_histogram,
        "dominant_premature_cause": _dominant(cohort_histogram),
    }


def is_degenerate(summary: dict[str, Any]) -> bool:
    """Degenerate = no quality cause present (100% plumbing/settled/not_stopped)
    or no dominant cause could be chosen."""
    histogram = summary.get("cohort_histogram") or {}
    quality_total = sum(int(histogram.get(key, 0)) for key in _QUALITY_KEYS)
    return quality_total == 0 or summary.get("dominant_premature_cause") is None


def _resolve_run_dirs(args: argparse.Namespace) -> list[Path]:
    if args.run_dir:
        return [Path(d) for d in args.run_dir]
    runs_root = Path(args.runs_root)
    return sorted(p for p in runs_root.iterdir() if (p / "stop_report.json").is_file())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", action="append", help="explicit run dir (repeatable)")
    parser.add_argument("--runs-root", default=str(Path(__file__).resolve().parent.parent / ".scratch" / "fig-loop-runs"))
    parser.add_argument("--check", action="store_true", help="exit non-zero on a degenerate cohort")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    run_dirs = _resolve_run_dirs(args)
    summary = roll_up_run_dirs(run_dirs)
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(f"dominant_premature_cause={summary['dominant_premature_cause']} "
              f"runs={summary['runs_counted']} histogram={summary['cohort_histogram']}")
    if args.check and is_degenerate(summary):
        print("dogfood_metrics: DEGENERATE cohort (no quality cause; fix plumbing/setup first)",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] Run to pass: `NO_COLOR=1 uv run pytest tests/test_dogfood_metrics.py -q` → expect all pass.
- [ ] Commit: `git add scripts/dogfood_metrics.py scripts/dogfood_cohort.json tests/test_dogfood_metrics.py && git commit -m "feat(dogfood): Slice 3 — minimal cohort roll-up + --check non-degeneracy gate"`.

---

## Task 6 — REAL cohort dogfood gate (the actual outcome, not a unit test)

**Files:** `tests/test_slice3_cohort_dogfood.py`

This task runs the loop on the real cohort, diagnoses each run, rolls up, and asserts the result is non-degenerate. Per the measured grounding, fig2 yields `decision_weak` and fig3 yields `lever_exhausted` from the per-sub-region ledger signal even though the loop stops at plumbing — so the cohort gate is non-degenerate. If a future cohort state flips to 100% plumbing, this test fails LOUD (honest "fix plumbing first") rather than passing vacuously.

- [ ] Write the gate test (COMPLETE):

```python
# tests/test_slice3_cohort_dogfood.py
from __future__ import annotations

import json
from pathlib import Path

import fig_loop
from dogfood_metrics import is_degenerate, load_cohort, roll_up_run_dirs
from fig_loop_stop_diagnoser import diagnose_run

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
COHORT = PLUGIN_ROOT / "scripts" / "dogfood_cohort.json"


def test_cohort_dogfood_gate_is_non_degenerate(tmp_path):
    cohort = load_cohort(COHORT)
    # Run the active-improvement set (fig2, fig3); fig1 is the recorded anchor.
    active = ["fig2_trap_design_space", "fig3_resistance_mechanism"]
    run_dirs: list[Path] = []
    for fixture in active:
        run_dir = fig_loop.run_loop(fixture, "slice3 cohort dogfood", runs_root=tmp_path)
        report = diagnose_run(fixture, run_dir)
        assert (run_dir / "stop_report.json").is_file()
        run_dirs.append(run_dir)

    summary = roll_up_run_dirs(run_dirs)
    # Empirical (this branch): fig2 -> decision_weak, fig3 -> lever_exhausted.
    assert summary["dominant_premature_cause"] is not None, (
        "GATE FAILED: cohort produced no quality cause — fix plumbing/setup first. "
        f"histogram={summary['cohort_histogram']}"
    )
    assert is_degenerate(summary) is False
    assert summary["cohort_histogram"]["decision_weak"] >= 1
    assert summary["cohort_histogram"]["lever_exhausted"] >= 1


def test_fig1_anchor_run_also_diagnoses(tmp_path):
    run_dir = fig_loop.run_loop("fig1_overview_v2_pair_001_vault", "slice3 anchor", runs_root=tmp_path)
    report = diagnose_run("fig1_overview_v2_pair_001_vault", run_dir)
    assert report["schema"] == "figure-agent.stop-report.v1"
    # fig1 has a real subregion_iteration_log.md; mirror of dominant rows is allowed.
    assert set(report["cause_histogram"]) == {
        "gate_capped", "lever_exhausted", "decision_weak",
        "headroom_blind", "settled_verified", "plumbing_stop", "not_stopped",
    }
```

- [ ] Run the gate: `NO_COLOR=1 uv run pytest tests/test_slice3_cohort_dogfood.py -q` → expect all pass; `decision_weak >= 1` AND `lever_exhausted >= 1`, `is_degenerate == False`.
- [ ] Run the CLI gate as the real outcome (writes reports into a scratch root, then checks):

```bash
NO_COLOR=1 uv run python -c "
import sys; from pathlib import Path
S=Path('scripts').resolve()
for d in reversed([S,S/'checks',S/'candidates',S/'quality',S/'loop',S/'driver',S/'svg_polish']): sys.path.insert(0,str(d))
import fig_loop; from fig_loop_stop_diagnoser import diagnose_run
root=Path('.scratch/slice3-gate'); root.mkdir(parents=True, exist_ok=True)
for f in ['fig2_trap_design_space','fig3_resistance_mechanism']:
    rd=fig_loop.run_loop(f,'slice3 gate',runs_root=root); diagnose_run(f,rd); print('diagnosed',f,rd.name)
"
NO_COLOR=1 uv run python scripts/dogfood_metrics.py --check --runs-root .scratch/slice3-gate
echo "exit=$?"
```

Expected: prints `dominant_premature_cause=decision_weak runs=2 histogram={...}` then `exit=0`. (If the cohort ever degenerates to 100% plumbing, this prints `DEGENERATE` and `exit=1` — the honest finding.)

- [ ] Commit: `git add tests/test_slice3_cohort_dogfood.py && git commit -m "test(dogfood): Slice 3 — REAL cohort gate (loop->diagnose->rollup, non-degenerate)"`.

---

## Task 7 — Full suite + ruff + final commit

**Files:** (none new)

- [ ] Run the full suite: `NO_COLOR=1 uv run pytest -q` → expect prior baseline (2614 collected) + the new tests all passing, 0 failures. (Do NOT set `FORCE_COLOR`; `FORCE_COLOR=3` breaks 2 pre-existing cowork argparse tests — env artifact, unrelated to this slice.)
- [ ] Lint only the new/edited files: `uv run ruff check scripts/loop/stop_cause_classify.py scripts/loop/fig_loop_stop_diagnoser.py scripts/loop/fig_loop_stop_router.py scripts/loop/fig_loop_decision.py scripts/dogfood_metrics.py` → expect `All checks passed!`.
- [ ] Format check: `uv run ruff format --check scripts/loop/stop_cause_classify.py scripts/loop/fig_loop_stop_diagnoser.py scripts/loop/fig_loop_stop_router.py scripts/dogfood_metrics.py` → expect no reformat needed (run `ruff format` and re-stage if it reports changes).
- [ ] Final commit if ruff applied any format change: `git add -A && git commit -m "chore(loop): Slice 3 — ruff format diagnoser/classifier/router/harness"`.

---

## Self-Review

### Spec-coverage (each spec §4/§7 Slice-3 item → task)

- §4.1 single 7-member enum, one module → **Task 1** (`StopCause`, 7 lowercase values).
- §4.2 trigger superset incl. aesthetic-lever reroute (`human_gate_required`) + basin (`basin_detected`); plumbing counted separately → **Task 2** (`TERMINAL_STOPS`/`PLUMBING_STOPS`); plumbing handled in **Task 1** (`STOP_REASON_CAUSE`).
- §4.3 sub-region enumeration via ledger composite key (`sel:`/`#`) + active-target set → **Task 3** (`enumerate_subregions`).
- §4.4 signal bundle (status_result, ledger re-read, candidate_set diagnoser-invoked, aesthetic_lever_summary, audit_evidence_summary, basin_summary, reference_aesthetic_metrics_summary) → **Task 3** (`build_signal_bundle`, re-invokes `build_candidate_set`/`build_quality_defect_ledger`/`summarize_audit_evidence`).
- §4.5 precedence classifier consuming candidate AND reference signal; refusal-code disambiguation; canonical `REFUSAL_CODE → cause` table; residual-proxy headroom → **Task 1** (`classify_stop_cause`, precedence 1–6; `REFUSAL_CODE_CAUSE`; `_residual_headroom`).
- §4.6 `stop-report.v1` schema with per-sub-region `subregion_id`/`stop_cause`/`evidence[source_module,source_ref]`, `cause_histogram` (7 keys), `dominant_premature_cause`; Why-mirror via `append_iteration_row` (guarded, dominant-only) → **Task 3** (`diagnose_run`, `_mirror_dominant_rows`).
- §4.7 pure router `route_stop_cause → Route(cause, fix_mode, action, payload, blocked_by)`; lever payload = refusal code string; `human_art_direction` sink; settled/plumbing → none → **Task 4**.
- §7 minimal harness: cohort histogram roll-up → `dominant_premature_cause` (argmax over four quality causes), `--check` non-degeneracy exit code; `dogfood_cohort.json` (fig1 anchor + fig2 + fig3) → **Task 5**; the real non-degenerate gate → **Task 6**.
- §8 Slice-3 row "dominant_premature_cause emitted and non-degenerate; if plumbing dominates → fix plumbing first" → **Task 6** (gate asserts non-degenerate; `--check` exits non-zero on degeneracy).

### Placeholder scan

No `TODO`/`FIXME`/stub/`pass`-only bodies in any code step; every function has a complete body. Deferred items (premium band, `anti_pattern_id`, autonomy ledger, Slice-4 series) are named in the deferred list and are NOT stubbed in code — they are absent by design, not placeholdered.

### Type/name consistency

- `StopCause` enum values are the exact 7 lowercase strings; `cause_histogram` keys (`fig_loop_stop_diagnoser._HISTOGRAM_KEYS`) and `dogfood_metrics._HISTOGRAM_KEYS` both derive from `tuple(c.value for c in StopCause)` — no drift.
- `QUALITY_CAUSES` defined once in `stop_cause_classify`, imported by both diagnoser (`_dominant_premature`) and harness (`_dominant`) — single argmax definition over the four.
- `ClassifiedStop(subregion_id, cause: StopCause, evidence)` and report rows use `.cause.value` consistently; `Route` fields `{cause, fix_mode, action, payload, blocked_by}` match the router test's `set(vars(route))`.
- `append_iteration_row` called with exactly its required kwargs (`iteration, subregion_id, problem, patch_summary, result, why, follow_up`) — matches `subregion_iteration_log.py:95`.
- `build_candidate_set(name)` called with no `output_path`/`panel`/`family` (read-only path, `candidate_generator.py:52,526`); `build_quality_defect_ledger(name)` and `summarize_audit_evidence(example_dir)` match their real signatures.

### Scope (measure-only; deferred items named)

- Diagnoser and router are READ-ONLY/PURE: the diagnoser only re-invokes read-only builders and `write_json`s an additive report + (guarded) log row; it never calls `apply_candidate` or mutates the figure source. The router imports no fix-mode module and returns data only.
- No fix-mode acts; no autonomy graduation; no `may_edit` change; no `CLASS_VERIFIERS`; no semantic-recheck replacement (all Slice 4).
- No premium band, no `headroom.json`, no continuation precondition, no `anti_pattern_id` mapping (all Slice 5+).
- No `ceiling_distance`/`human_touch_count`/`autonomy_fraction`/per-cause series/`regression_count` (Slice 4+); harness emits only the cohort histogram + dominant cause + `--check`.
- `headroom_blind(ii)` (premium band) dropped; only the deterministic residual proxy is used — the classifier never reads `reference_aesthetic_metrics` warning/severe state as an at-ceiling signal.
- The cohort gate is non-vacuous: it asserts a real quality dominant cause (empirically `decision_weak` + `lever_exhausted`) and `--check` exits non-zero on a degenerate cohort, surfacing plumbing-dominance as an honest finding rather than hiding it.
