# Plugin Loop Automation and Audit Hardening Design

**Date:** 2026-05-21 KST
**Status:** design proposed
**Related issues:** Issue 15, 15A, 15B, 15C, 15D

## Current Repo Truth

The plugin is no longer a compile/export wrapper. It already has a layered
workflow:

- `/fig_status` is the canonical state reader.
- `/fig_drive` is a dry-run recommender over status and latest loop evidence.
- `/fig_loop` is a verify-only checkpoint writer.
- `/fig_closeout` is a read-only post-patch checklist.
- `critique.md` v1.4 carries mandatory audit enumeration, quality axes,
  top-tier audit, journal-grade assessment, and micro-defects.
- `critique_adjudication.yaml` records finding-level decisions bound to the
  current critique hash.
- high-zoom crops, print-scale crops, drawing-order lints, and short-arrow
  lints provide deterministic evidence for host vision critique.
- publication gate and final-artifact gate are explicit and conservative.

The codebase has broad test coverage around these surfaces:
`test_fig_driver.py`, `test_fig_loop*.py`, `test_fig_closeout.py`,
`test_critique_lint.py`, `test_critique_adjudication.py`,
`test_status.py`, `test_run_export.py`, `test_publication_gate.py`,
and audit-pack tests.

## Architecture Findings

### Finding 1: The next bottleneck is operational closure, not raw capability.

`/fig_drive`, `/fig_loop`, and `/fig_closeout` all exist, but the user still has
to know when to switch between them. In real use this creates mode confusion:
agents can loop on compile, stop at critique, forget adjudication sync, or
miss closeout even though each individual command is correct.

The first priority is therefore not hidden auto-editing. It is a canonical
"what now?" path that incorporates closeout state into the driver contract.

### Finding 2: Audit surfaces exist, but audit completeness is still partly
prompt-trust.

Issue 12 added high-zoom and print-scale evidence. Issue 11/12B/12E added
schema and lint surfaces. The remaining risk is that a host critique can still
claim a pass without proving it read every required evidence class, or can
leave an open micro-defect unlinked to a normal finding.

The second priority is an evidence-completeness linter for the critique
contract, not another broad visual heuristic.

### Finding 3: Bounded auto-patch should be downstream of closeout and audit
completeness.

`fig_loop_auto_patch.py` already classifies eligibility but deliberately sets
`may_edit: false`. That is the right current state. Before any mutating
executor exists, the repo needs:

- driver/closeout integration so the executor knows the current boundary;
- audit completeness lint so the executor does not patch from a malformed or
  under-evidenced critique;
- one-target patch evidence requirements that remain non-bypassable.

### Finding 4: Module size is manageable but watch-listed.

`status.py` and `fig_driver.py` are large because they own cross-cutting state
machines. This is acceptable while behavior is stable and heavily tested, but
future changes should avoid further growth by extracting new contracts into
focused helper modules. Refactoring should be triggered by new work in those
areas, not done as a broad cleanup.

## Recommended Priority Order

1. **Issue 15A: Driver-Closeout Unification.** Make `/fig_drive --mode review`
   recommend `/fig_closeout` when a loop checkpoint exists but closeout is
   incomplete. This closes the biggest real-use confusion without adding
   mutation.
2. **Issue 15B: Audit Evidence Completeness Linter.** Make `critique_lint.py`
   fail when fresh v1.4 critiques omit required evidence links for high-zoom,
   print-scale, micro-defects, or top-tier blockers.
3. **Issue 15C: Bounded Auto-Patch Executor Pilot.** Add an opt-in,
   single-target, non-default patch executor only after 15A and 15B are in
   place. It must never handle science, structure, publication, accepted,
   golden, final-artifact, or multi-target decisions.
4. **Issue 15D: Orchestration Boundary Refactor.** Extract only the new
   driver/closeout/audit-decision glue introduced by Issues 15A-15C so
   `fig_driver.py` and `status.py` do not absorb another layer of policy.

## Non-Goals

- No hidden source editing.
- No automatic host critique authoring.
- No automatic accepted/golden/final-artifact promotion.
- No score-as-hard-gate.
- No replacement of host vision critique with deterministic image heuristics.
- No broad refactor before behavior is locked by tests.

## Success Criteria

The next phase is successful when an agent can run `/fig_drive` repeatedly and
always get a single conservative next boundary:

1. compile if render is stale,
2. host critique if critique is stale,
3. adjudicate if critique is fresh but decisions are missing or stale,
4. closeout if a patch was applied but compile/critique/adjudication/export
   evidence is incomplete,
5. loop checkpoint if prerequisites are closed,
6. human gate only for real domain/policy decisions,
7. bounded patch candidate only when the target is local, safe, and fully
   evidenced.
