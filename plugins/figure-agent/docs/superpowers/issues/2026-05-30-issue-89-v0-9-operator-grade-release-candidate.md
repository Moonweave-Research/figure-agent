# Issue 89 - v0.9 Operator-Grade Release Candidate

Status: in progress

Depends on:

- Issue 63 - reference learning and aesthetic metrics
- Issue 70 - operator-grade guided autonomy
- Issue 71 - real fixture production readiness
- Issue 72 - export driver/runner contract alignment
- Issue 73 - SVG polish trigger semantics
- Issue 74 - post-v1.14 host critique refresh queue
- Issue 75 - SVG polish readiness source-gate clarity
- Issue 76 - release not-declared gate explanation
- Issues 77-88 - fixture queue, queue runner, operator handoff, and closeout UX

Type: release hardening, contract freeze, packaging readiness

## Problem

The plugin has moved beyond a single-fixture quality kernel. It now has:

- reference-grounded critique contracts;
- deterministic visual/text/path checks;
- crop and candidate accountability;
- reference-learning and aesthetic metrics;
- bounded single-fixture runner;
- multi-fixture queue and queue runner;
- operator handoffs for host, human, release, SVG, closeout, and workflow-agent
  boundaries.

The risk is no longer missing one obvious feature. The risk is release drift:
many contracts have landed quickly, and operators need a frozen, validated
truth surface before another aesthetic or SVG-polish expansion begins.

## Goal

Prepare a v0.9 release candidate that freezes the current operator-grade
workflow as the plugin's default operating model.

v0.9 should say, plainly:

1. `/fig_status` and `/fig_drive` are the single-fixture traffic controllers.
2. `/fig_run` may execute only safe mechanical single-fixture work.
3. `/fig_queue` and `/fig_queue_run` are the multi-fixture operator surface.
4. Host critique, human decisions, release/golden approval, source patches, and
   SVG polish remain explicit boundaries.
5. Scores, metrics, reference learning, and aesthetic signals are routing and
   suspicion aids, not release authority.

## Scope

### 89A - Release Contract Freeze

- Reconcile `SKILL.md`, command docs, README/release docs, and issue roadmap so
  the canonical operating sequence is not split across stale text.
- Record the final command vocabulary and actor vocabulary.
- Explicitly mark replay/resume, hidden auto-patch, and hidden release mutation
  as out of scope.

### 89B - Package And Version Metadata

- Decide whether the next plugin version is `0.9.0`.
- If yes, update plugin manifest and release docs consistently.
- Run plugin package audit and validation.
- Do not include generated `.scratch/`, build, export, or fixture output
  artifacts in the package.

Status: completed on `codex/issue70-guided-autonomy-roadmap`. Evidence:
`docs/milestones/2026-05-30-v0-9-package-and-version-metadata.md`.

### 89C - Whole-Corpus Release Smoke

- Run queue snapshots for `review`, `release`, and `polish` modes.
- Confirm each fixture lands in one of:
  - workflow-agent mechanical work;
  - host-vision critique;
  - human decision;
  - release operator;
  - SVG editor;
  - completed/no-op.
- Any surprising row must become a narrow defect issue before release.

Status: completed on `codex/issue70-guided-autonomy-roadmap`. Evidence:
`docs/milestones/2026-05-30-whole-corpus-release-smoke.md`.

### 89D - Release Notes And Operator Playbook

- Write release notes for the operator-grade workflow.
- Include a concise "how to use it today" path:
  - single fixture;
  - multi-fixture queue;
  - host critique refresh;
  - closeout after patch/export;
  - release/golden gate.
- Include "what it still does not do":
  - no automatic top-tier art direction;
  - no hidden SVG polish;
  - no accepted/golden mutation;
  - no external provider requirement.

### 89E - Final Review And Merge Readiness

- Run full pytest, ruff, diff check, plugin validate, package audit, and secret
  scan.
- Run at least three reviews:
  1. contract and documentation consistency;
  2. execution safety and mutation boundaries;
  3. packaging, release notes, and operator usability.
- Open or update a PR from `codex/issue70-guided-autonomy-roadmap`.
- Do not merge unless CI is clean and the release gate review is explicit.

## Out Of Scope

- New critique schema expansion.
- New aesthetic metrics.
- New SVG polish executor behavior.
- Source drawing work.
- Fixture source patching.
- Automatic host-vision critique authoring.
- Automatic accepted/golden/publication mutation.
- Changing real fixture acceptance state.

## Acceptance

- Current plugin behavior is documented as one coherent operating model.
- Version/package metadata is either intentionally unchanged or consistently
  bumped.
- Queue behavior is verified on the real fixture corpus.
- All protected mutation boundaries remain explicit.
- Full local verification passes.
- CI/PR path is ready for human merge decision.

## Review Questions

1. Does v0.9 freeze what is already proven rather than adding speculative new
   behavior?
2. Can a new operator tell which command to run first without reading the whole
   issue archive?
3. Are generated artifacts and fixture maintenance clearly excluded from the
   release package?
4. Are host/human/release/SVG/source-patch boundaries still impossible to cross
   accidentally?
5. Does the release candidate leave a clean next track for v1.0 aesthetic/SVG
   polish work?
