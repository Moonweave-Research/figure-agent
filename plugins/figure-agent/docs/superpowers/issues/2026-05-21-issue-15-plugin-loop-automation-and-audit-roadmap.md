# Issue 15: Plugin Loop Automation and Audit Hardening Roadmap

**Date:** 2026-05-21 KST
**Status:** proposed
**Type:** parent issue / implementation backlog
**Spec:** `../specs/2026-05-21-plugin-loop-automation-audit-design.md`

## Problem

The plugin has most of the required loop primitives, but real use still has
too much operator judgment about which primitive to run next. The most valuable
next work is not "make the agent edit everything automatically." It is to
reduce workflow ambiguity while preserving the current safety boundaries.

Two directions remain important:

1. **Automation strengthening:** let the plugin move from advisory fragments
   toward a canonical loop path, then later toward opt-in bounded single-target
   patches.
2. **Audit quality strengthening:** ensure the host critique actually proves
   it used high-zoom, print-scale, top-tier, and micro-defect evidence before
   the loop trusts the result.

## Current State

Implemented and verified surfaces:

- `/fig_status` canonical state vector.
- `/fig_drive` dry-run mode-aware recommender.
- `/fig_loop` verify-only checkpoint.
- `/fig_closeout` read-only post-patch checklist.
- v1.4 critique contract with quality axes, top-tier audit, journal-grade
  assessment, and micro-defects.
- freshness-bound `critique_adjudication.yaml`.
- high-zoom and print-scale evidence packs.
- publication and final-artifact gates.
- CI split into fast tests and full-render tests with timeout guardrails.

Open architecture risk:

- `/fig_drive` and `/fig_closeout` are adjacent but not unified. A user can
  still run the right command family in the wrong order.
- `critique_lint.py` validates schema and duplicate ids, but does not yet
  enforce complete evidence use for every required audit surface.
- auto-patch eligibility exists, but no executor should be added before the
  driver and audit contract can prove the current boundary.
- `fig_driver.py` and `status.py` are large state-machine files; new work
  should extract helper modules instead of growing them further.

## Issue Breakdown

### Issue 15A: Driver-Closeout Unification

**Type:** AFK
**Blocked by:** None

Teach `/fig_drive --mode review` to surface `/fig_closeout` when the latest
loop checkpoint or workspace state implies a post-patch closeout is incomplete.
The driver remains dry-run; it recommends the closeout boundary, it does not
run compile, critique, adjudication, export, or loop commands itself.

Acceptance criteria:

- [x] `/fig_drive --mode review` can include closeout summary fields from
  `fig_closeout.compute_closeout()`.
- [x] When closeout is incomplete, the driver returns one canonical action and
  reason instead of falling through to ambiguous `run_fig_loop`.
- [x] Golden roll-forward remains manual; `--force-golden` is never emitted as
  an automatic safe command.
- [x] Tests cover closeout-driven export, loop rerun, tracked golden manual
  approval, complete closeout pass-through, and real closeout export gaps.
  Compile, critique, and adjudication closeout primitives remain covered in
  `tests/test_fig_closeout.py`.
- [x] Existing `figure-agent.driver.v1` consumers remain backward compatible.

### Issue 15B: Audit Evidence Completeness Linter

**Type:** AFK
**Blocked by:** None

Harden `critique_lint.py` so a fresh v1.4 critique cannot pass while omitting
required evidence-use claims. This should catch under-evidenced host critiques,
not judge the artistic quality of a figure.

Acceptance criteria:

- [ ] v1.4 critiques must include non-empty `micro_defects`.
- [ ] Any open `BLOCKER`/`MAJOR` micro-defect must link to a normal finding.
- [ ] Any failed or `needs_human` `top_tier_audit` slot with
  `blocks_high_impact: true` must appear in a normal finding or in
  `quality_axes.*.blocking_items`.
- [ ] `journal_polish` and `publication_readiness` cannot pass unless the
  critique records print-scale evidence.
- [ ] The linter emits controlled, actionable errors and does not mutate files.
- [ ] Legacy v1.0-v1.3 critiques remain parseable under existing compatibility
  rules.

### Issue 15C: Bounded Auto-Patch Executor Pilot

**Type:** AFK, but gated behind 15A and 15B
**Blocked by:** Issue 15A, Issue 15B

Add an opt-in pilot executor for exactly one local, safe patch target selected
by existing adjudication and loop handoff. This is not a general autonomous
editor. It is a narrow executor for low-risk style/label/whitespace changes
with mandatory closeout.

Acceptance criteria:

- [ ] Default behavior remains non-mutating.
- [ ] Executor requires explicit opt-in flag and a single `apply` target.
- [ ] Executor refuses science, structure, physics, reference interpretation,
  target-journal, accepted, golden, export, final-artifact, and semantic
  backport findings.
- [ ] Executor writes only within `patch_handoff.allowed_edit_scope`.
- [ ] Executor records before/after evidence and a rollback path.
- [ ] Executor runs or requires `/fig_closeout` after the edit and does not
  claim completion while closeout is incomplete.
- [ ] Tests prove refusal paths are more numerous than success paths.

### Issue 15D: Orchestration Boundary Refactor

**Type:** AFK
**Blocked by:** Issue 15A

Keep the codebase maintainable while adding loop automation. Extract new
driver/closeout/audit policy glue into focused helper modules instead of
adding another policy layer directly inside `fig_driver.py` or `status.py`.

Acceptance criteria:

- [ ] New Issue 15A/15C logic lives in focused modules with narrow public
  functions.
- [ ] `fig_driver.py` remains the CLI/controller, not the owner of every
  policy detail.
- [ ] `status.py` remains the canonical state reader; it does not absorb
  patch-executor or audit-lint policy.
- [ ] Existing tests continue to pass without broad fixture rewrites.
- [ ] The refactor is behavior-preserving except for the explicitly tested
  Issue 15A/15C surfaces.

## Priority

1. Issue 15A first. It improves real-use loop consistency without mutation.
2. Issue 15B second. It prevents automation from trusting an incomplete host
   critique.
3. Issue 15C third. Mutating automation is only acceptable after 15A and 15B.
4. Issue 15D alongside 15A/15C when the implementation would otherwise bloat
   `fig_driver.py` or `status.py`.

## Out of Scope

- Merging or judging any specific figure fixture.
- Automatic publication acceptance.
- Automatic host-vision critique writing.
- External Gemini/vision API integration as a first-class dependency.
- Full SVG polish automation.
