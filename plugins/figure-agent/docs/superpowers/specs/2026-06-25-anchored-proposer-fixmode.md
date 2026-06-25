# Anchored-Proposer Fix-Mode (Slice 5)

Status: Increment 1 + 2 shipped (TDD). Increment 3 (apply-pipeline e2e + geometry-derived
proposed_offset) open.
Branch: work/review-auto-fixes-2026-06-25. Backs memory `project_slice5_fig2_settles_clean_2026_06_25`.

## Problem (dogfood-grounded, not assumed)

Probing fig2_trap_design_space end-to-end revealed the genuine ceiling of the
auto-fix loop:

1. fig2 has a real defect — the conventional-cluster caption `PI, PDMS, PET`
   crosses the panel-b x-axis line (critique finding C001, `tex_lines [95,96]`,
   fix = lower the caption node `y 4.12 → ~3.62`). The detectors flagged it
   (visual_clash VC006/VC007/VC008); an over-confident host critique initially
   dismissed those as false positives (a FALSE-CLEAN — the critique gate is
   gameable by the eye).
2. C001 was adjudicated `apply`; the loop correctly reached
   `patch_target_recommended` for lines 95-96.
3. But `candidate_generator.build_candidate_set` only consumed the
   deterministic-audit ledger (QD001-006, **all `tex_lines=None`**, panel +
   sub-region only). The panel-B candidate it emitted (CAND005) moved the
   **y-axis line** `(6.10,3.90)--(6.10,9.15)` (fig2.tex:81, driven by UG009)
   left by 0.1cm — totally decoupled from C001 (lines 95-96).

The adjudicated finding's precise host-eye diagnosis (its own `tex_lines` + the
diagnosed edit) was never wired into candidate generation. That is the concrete
"blind nudge → bounded REFINE not authoring" ceiling.

## Increment 1 — anchored proposer (SHIPPED)

`candidate_generator._adjudicated_apply_candidates`: for each `apply` decision in
`critique_adjudication.yaml`, resolve the finding's `tex_lines` from
`critique.md`, and emit a bounded label-offset candidate anchored to the
finding's first tex_line. Merged into `build_candidate_set` (dedup by
`selector.start_line`, re-id `CAND001..N`).

Result on real fig2: `CAND007 | start_line=95 | source=adjudicated_finding |
id=C001 | \node[labelMute...]` — the candidate now targets the diagnosed element
(the PI/PDMS/PET node) instead of unrelated geometry.

Test: `tests/test_candidate_generator.py::
test_adjudicated_apply_finding_drives_candidate_at_finding_line` (RED→GREEN).

## Increment 2 — verifier-gated reposition (SHIPPED)

Increment 1 fixed "wrong element" but the candidate still nudged x by 0.1cm —
wrong direction, and `MAX_TRANSLATE_CM = 0.10` can't move the ~0.5cm C001 needs.
Increment 2 lets the eye's exact diagnosis drive the move:

- A finding may carry a structured `proposed_offset: {axis, dx_cm}` (the eye's
  diagnosed edit). For C001 that is `{axis: y, dx_cm: -0.50}` (4.12 → 3.62).
- `bounded_coordinate_offset.reposition_coordinate` translates the line on that
  axis with a larger bound (`MAX_REPOSITION_CM = 0.80`) than the nudge cap. Its
  SAFETY is the Slice 4 verifier (semantic recheck that the defect signature
  dropped + value-preservation CLASS_VERIFIERS + auto-rollback), NOT the tiny
  translate bound — the 0.80 cap only stops an absurd whole-figure move. The
  0.10cm nudge family's cap is untouched.
- `candidate_generator._finding_offset` emits a `label_reposition` candidate when
  `proposed_offset` is present, else falls back to the bounded nudge.

Result on real fig2: the anchored candidate now rewrites the PI/PDMS/PET node
`(7.60,4.12)` → `(7.60,3.62)` — the exact fix the eye diagnosed, which the
bounded-nudge family could never author.

Tests: `test_reposition_coordinate_*` (primitive), `test_adjudicated_finding_
with_proposed_offset_emits_reposition` (wiring).

## Increment 3 (open)

1. **Apply-pipeline e2e**: drive the fig2 `label_reposition` candidate through
   render → accept → apply and confirm the Slice 4 semantic recheck reports the
   PI/PDMS/PET crossing actually gone (and rolls back if not). The candidate is
   currently `review_only`/`human_required` at the acceptance gate.
2. **Geometry-derived `proposed_offset`**: today the eye supplies dx_cm by hand
   in the critique. Derive it from rendered geometry (label bbox vs crossed
   reference-line position + margin) so the loop proposes the magnitude itself.
3. **Critique-gate adversarial check**: the eye rubber-stamped a detector
   true-positive (VC006-008) as a false positive. An accept_simplification of a
   detector flag needs an adversarial second check, else any eye games the gate.

Also surfaced: the critique gate itself rubber-stamped a detector true-positive
as `accept_simplification:false_positive`. An EYE fix-mode needs an adversarial
check on accept_simplification of a detector flag, else any eye games the gate.
