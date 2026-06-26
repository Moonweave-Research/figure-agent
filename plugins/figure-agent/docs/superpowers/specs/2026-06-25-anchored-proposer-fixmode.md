# Anchored-Proposer Fix-Mode (Slice 5)

Status: Increment 1 + 2 + 3 shipped (TDD). Increment 4 (destination-aware geometry,
richer edits for tight layouts, apply-e2e on apply_eligible figure) open.
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

## Increment 3 — finding↔verifier bridge (SHIPPED)

Apply-e2e dogfooding found the shipped fix-mode was NOT end-to-end functional:
- The eye's hand-supplied `proposed_offset` for fig2 (`-0.50cm`) is geometrically
  WRONG — applied + recompiled, the caption collides with the panel-c title
  (axis↔panel-c-title gap is only 0.75cm). A coordinate offset has no clean
  solution for that tight layout. (Reverted the experiment.)
- VERIFIER-DEAD-ON-ARRIVAL: the anchored candidate's `source_defect.id` is the
  critique finding id (`C001`), never in `quality_defect_ledger` (QD001-006, ALL
  undeclared_geometry-grounded). `_semantic_recheck_verdict('C001', …)` →
  `source_defect_absent_pre_apply`, so EVERY anchored candidate always failed the
  recheck. ROOT: critique findings are **visual_clash**-grounded (VC###) while the
  ledger/verifier is **undeclared_geometry**-grounded (QD/UG###) — the verifier is
  structurally BLIND to the defect class the critique catches.

Fix (the bridge): a finding-sourced fix verifies against the **post-apply
visual_clash** detector, not the ledger.
- `candidate_apply._finding_recheck_verdict(target_texts, post_crossing_texts)`:
  resolved iff none of the texts the finding targeted still cross.
- `_post_apply_semantic_recheck` branches on `source_defect.source ==
  "adjudicated_finding"` → reads post `build/visual_clash.json` texts → finding
  recheck; no `target_texts` ⇒ fail-safe (`finding_target_texts_missing`).
- The finding carries structured `target_texts`; `candidate_generator` threads
  them into the candidate's `source_defect`.
- Real fig2: CAND007 carries `target_texts=[PI,, PDMS,, PET]`; recheck →
  `failed/finding_crossing_unresolved` against the bad-reposition post (PI,/PET
  still cross), `success` against a clean post. The verifier now CATCHES the
  wrong fix.

Tests: `test_finding_recheck_*`, `test_post_apply_recheck_finding_sourced_*`,
`test_adjudicated_finding_carries_target_texts_for_verifier`.

## Increment 4 (open)

1. **DESTINATION-aware geometry-derived `proposed_offset`**: derive dx_cm from
   rendered geometry AND confirm the destination is clear of all nearby elements
   (fig2 showed moving DOWN hits panel c) — not just clear of the one crossed line.
2. **Richer edit family for tight layouts**: when no coordinate offset has a clean
   solution (fig2's 0.75cm gap), the loop needs anchor/text-width edits or must
   escalate to human redesign.
3. **Apply-pipeline e2e on an apply_eligible figure**: drive a finding-sourced
   reposition through the real `apply_candidate` (fig2 is `review_only` by panel
   design); the spine + bridge are unit-proven (good fix → applied, bad →
   failed-verification).
4. **Critique-gate adversarial check** on `accept_simplification` of a detector
   true-positive (the eye rubber-stamped VC006-008 once), else any eye games the gate.
