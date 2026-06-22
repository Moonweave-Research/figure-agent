# Fig Loop Dogfood Evidence Matrix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the evidence checkpoint that decides whether Issue 5B safe auto-patch design may begin, without enabling auto-editing.

**Architecture:** Keep `/fig_loop` verify-only. Use temporary repo-root loop runs to exercise machine states without mutating tracked examples, then record the evidence matrix and remaining risk in milestone docs. Treat this as a pre-5B readiness checkpoint, not as proof that auto-editing is reliable on real manuscript figures.

**Tech Stack:** Python stdlib, existing `scripts/fig_loop.py`, existing `critique_adjudication.yaml` contract, markdown milestone docs, `git diff --check`, Claude plugin validation.

---

## Non-Developer Summary

This step is the safety audit before building an automatic patcher.

The plugin now knows how to:

- identify one possible patch target,
- classify whether that target looks mechanically safe,
- record the file hashes before a patch,
- compare the next run against those hashes,
- say whether the attempt looks `resolved`, `unresolved`, `regressed`, or `ambiguous`.

That is still not the same as proving automatic editing is good. The evidence
matrix asks: when the loop sees common cases, does it stop, record, or block in
the way we expect?

## File Structure

- Create: `plugins/figure-agent/docs/milestones-archive/2026-05-18-fig-loop-dogfood-evidence-matrix.md`
  - Records the seven scenario outcomes and the readiness verdict.
- Modify: `plugins/figure-agent/docs/superpowers/specs/2026-05-17-fig-loop-contract-design.md`
  - Adds Issue 5A.2 as a required checkpoint between Issue 5A.1 and Issue 5B.
- Modify: `plugins/figure-agent/docs/milestones-archive/2026-05-18-fig-loop-dogfood-usability-findings.md`
  - Adds a pointer from the earlier dogfood notes to the evidence matrix.

No runner behavior changes are required for this slice.

## Required Evidence Scenarios

The matrix must cover at least these states:

- safe label/spacing candidate,
- unresolved patch attempt,
- resolved post-patch adjudication,
- ambiguous multiple-apply selection,
- mechanism or science-class block,
- explicit `needs_human` gate,
- regressed post-patch state when render freshness is stale,
- generic label wording remains patch-assisted only,
- non-label offset remains patch-assisted only,
- publication-safety changes are blocked.

## Task 1: Record Evidence Matrix

**Files:**

- Create: `plugins/figure-agent/docs/milestones-archive/2026-05-18-fig-loop-dogfood-evidence-matrix.md`

- [x] **Step 1: Run temporary-root evidence scenarios**

Run a Python harness that imports `run_loop()`, creates fixtures under
`tempfile.TemporaryDirectory(prefix="fig-loop-evidence-10-")`, and writes
`critique_adjudication.yaml` inputs for each scenario.

Expected:

- no tracked example source changes,
- each scenario writes only ignored `.scratch` data inside the temp root,
- output is a JSON list with stop reason, handoff presence, evidence presence,
  post-patch verdict, and `may_edit`.

- [x] **Step 2: Record the scenario table**

Copy the observed results into the milestone document as a markdown table.

- [x] **Step 3: Record readiness judgment**

State that the matrix validates the read-only loop contract, but does not yet
authorize Issue 5B auto-editing on real figures.

## Task 2: Update Contract

**Files:**

- Modify: `plugins/figure-agent/docs/superpowers/specs/2026-05-17-fig-loop-contract-design.md`

- [x] **Step 1: Add Issue 5A.2**

Add a subsection between Issue 5A.1 and Issue 5B requiring an evidence matrix
for the ten states listed above.

- [x] **Step 2: Tighten Issue 5B prerequisite**

Require Issue 5A.2 in addition to Issues 1-4, 5A, and 5A.1, and raise the
real-fixture prerequisite to ten apply-handoff dogfood runs.

## Task 3: Link Prior Dogfood Notes

**Files:**

- Modify: `plugins/figure-agent/docs/milestones-archive/2026-05-18-fig-loop-dogfood-usability-findings.md`

- [x] **Step 1: Add a follow-up pointer**

Point readers to the evidence matrix as the next checkpoint after the initial
readiness gate notes.

## Verification

Run:

```bash
uv run pytest -q tests/test_fig_loop.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected:

- `tests/test_fig_loop.py` passes,
- diff whitespace check passes,
- all plugin validation commands pass.

## Self-Review

Spec coverage:

- Issue 5B remains blocked behind evidence.
- The matrix covers safe, unresolved, resolved, ambiguous, human-gated, unsafe,
  assisted-only negative, publication-safety, and regressed loop states.
- No source or artifact mutation is introduced.

Placeholder scan:

- No `TBD` or `TODO` placeholders.
- The next required action is explicit: collect ten real apply-handoff examples
  before enabling auto-edit.

Type consistency:

- Uses existing field names: `auto_patch_eligibility`, `patch_evidence`,
  `post_patch_evidence`, `may_edit`, `stop_reason`.
