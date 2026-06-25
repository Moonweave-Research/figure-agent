# Anchored-Proposer Fix-Mode (Slice 5)

Status: Increment 1 shipped (TDD). Increment 2 specified, not built.
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

## Remaining ceilings (Increment 2+, NOT built)

Increment 1 fixes "wrong element". Two ceilings remain before the loop can
actually resolve a label-placement collision:

1. **Direction**: the anchored candidate reuses `offset_first_coordinate`, which
   offsets the FIRST coordinate (x=7.60) — moves the label sideways, not toward
   clearance. Needs a diagnosed-direction offset (the finding/geometry says move
   the y-coordinate away from the reference line).
2. **Magnitude**: `bounded_coordinate_offset.MAX_TRANSLATE_CM = 0.10`. C001 needs
   ~0.5cm (4.12 → 3.62). Even a correctly-directed candidate cannot move far
   enough. The bounded-offset family can only REFINE (≤0.1cm), not author this
   fix. The fix-mode needs either a finding-scoped larger translate budget (on a
   fail-loud verifier) or a richer edit family (anchor change / target-position
   move).

Every Increment-2 step must ride the Slice 4 verification spine (semantic
recheck + value-preservation CLASS_VERIFIERS + auto-rollback) — do not relax the
magnitude cap without a verifier that fails loud when a fix doesn't actually drop
the C001 signature.

Also surfaced: the critique gate itself rubber-stamped a detector true-positive
as `accept_simplification:false_positive`. An EYE fix-mode needs an adversarial
check on accept_simplification of a detector flag, else any eye games the gate.
