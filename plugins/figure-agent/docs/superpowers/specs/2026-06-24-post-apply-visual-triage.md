# Post-Apply Visual Triage Workflow

Source of truth: `2026-06-24-post-apply-visual-triage.workflow.plan.json`

## Research And Prior Art

The fig3 dogfood loop has now exercised candidate generation, rendered visual
comparison, hash-bound acceptance, apply, compile, and export. The latest run
exposed a useful product gap: after apply, strict compile can fail because a
detector reports visual clash candidates even when TeX renders successfully and
exports are current.

## Product Position And Non-Goals

figure-agent should not collapse this state into a vague failure. It should
produce a post-apply receipt that separates source/apply truth, render truth,
export truth, detector warnings, and next actions.

Non-goals:

- no model or API calls;
- no detector threshold changes;
- no accepted or golden artifact refresh;
- no automatic visual-clash repair in this slice.

## Workflow Architecture

Pattern: sequential pipeline with adversarial verification.

Phases:

1. Capture post-apply state.
2. Implement `compose-post-apply-verify`.
3. Dogfood on `fig3_resistance_mechanism`.
4. Run focused tests and release gate.

## Execution Model

The command reads existing files only, then writes one receipt:

- source and candidate copy hashes;
- apply result and rollback patch presence;
- build PDF/PNG status;
- export PDF/PNG/SVG/TIF status;
- detector report counts;
- strict compile interpretation;
- required next actions.

## Safety And Verification Gates

The command must not run TeX, export, critique, or mutate source. It only
summarizes current artifacts. Golden and accepted artifacts stay untouched.

## Evaluation Fixture

Primary fixture: `fig3_resistance_mechanism`, candidate `CFAM_COMBO_002`.

## Release Plan

Use TDD:

1. Add a failing CLI test for `compose-post-apply-verify`.
2. Implement the smallest module and CLI handler.
3. Generate the real fig3 receipt.
4. Run focused pytest, ruff, py_compile, and release gate targeted suite.
