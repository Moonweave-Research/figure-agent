# Fig Loop Contract v0.1 Design

**Date:** 2026-05-17
**Status:** proposed implementation contract
**Scope owner:** `figure-agent`
**Primary pilot:** `examples/fig1_overview_v2_pair_001_vault`
**Decision:** define the loop contract before building an auto-editing runner.

## 1. Problem

`figure-agent` now has strong quality-kernel surfaces after authoring:
`/fig_compile`, `/fig_critique`, `/fig_export`, `/fig_status`, reference
freshness, accepted artifact gates, theory guards, reference packs, and
sub-region logs. These surfaces can detect many failures, but they do not yet
form a closed improvement loop.

The missing layer is the decision contract between one iteration and the next:

```text
goal -> inspect current state -> choose patch target -> patch -> verify
-> critique -> adjudicate findings -> decide next action or stop
```

Without that contract, an agent can run commands repeatedly and still fail to
improve the figure because it has no durable definition of:

- what the loop is trying to optimize,
- which findings are true positives,
- which sub-region is the active patch target,
- when a finding is resolved,
- when the loop should stop,
- when human approval is mandatory.

## 2. Goals

The first implementation should make loops auditable and decision-driven, not
autonomous by default.

The v0.1 loop must:

1. Preserve `figure-agent` as a paper-figure quality kernel rather than a
   black-box figure-generation orchestrator.
2. Record every iteration as evidence: inputs read, commands run, artifacts
   inspected, findings adjudicated, patch targets chosen, and stop reason.
3. Separate evaluation axes instead of collapsing quality into one pass/fail:
   render freshness, static visual QA, vision critique, theory correctness,
   reference-role fidelity, story/hierarchy, export readiness, and publication
   safety.
4. Let an external agent perform patches, while `figure-agent` owns the loop
   contract, state checks, and durable evidence.
5. Start verify-only, then add narrowly-scoped auto-patch only after the
   adjudication data proves which edits are safe.

## 3. Non-Goals

- Do not auto-set `accepted: true`.
- Do not declare a figure submission-safe without explicit human/domain review.
- Do not implement external image-generation API calls.
- Do not revive the deleted v0.1 prompt/preview-selection orchestration.
- Do not build a reference retrieval/vault layer inside `figure-agent`.
- Do not auto-apply scientific or mechanism-level changes in v0.1.
- Do not make `.scratch/` run outputs tracked artifacts.

## 4. Loop Modes

### 4.1 `verify-only`

The first supported mode. It runs checks, parses state, records evidence, and
recommends the next patch target. It does not edit `<name>.tex`, `spec.yaml`,
or acceptance artifacts.

Use this mode to prove the loop decision contract on the pilot without risking
source churn.

### 4.2 `patch-assisted`

Deferred. The loop may ask the host agent to patch one target at a time, but
the patch is still performed by the host agent, not by a hidden internal
autofixer. Each patch must trace to an adjudicated finding or active target.

### 4.3 `auto-patch-safe`

Deferred until at least five dogfood loop runs show that specific finding
classes are reliable. Initial candidate classes:

- label offset adjustments,
- whitespace balancing,
- palette/style violations already backed by lint,
- obvious text overlap or clipping fixes.

Excluded from auto-patch:

- chemistry topology,
- causal arrows and mechanism semantics,
- reference-transfer decisions,
- theory guard pass/fail evidence,
- `accepted` or publication-safety fields.

## 5. Inputs

A loop run is started with:

- fixture name,
- natural-language goal,
- mode (`verify-only` for v0.1),
- max iterations,
- optional focus target (`panel`, `sub-region`, or finding id),
- optional stop policy.

The runner reads only existing project artifacts:

- `briefing.md`,
- `spec.yaml`,
- `<name>.tex`,
- `coordinate_hints.yaml`, when present,
- `authoring_contract.md`, when present,
- `reference/reference_pack.md`, when present,
- `authoring_plan.md`, when present,
- `theory_guard.md`, when present,
- `subregion_iteration_log.md`, when present,
- `critique.md`, when present,
- `QUALITY_AUDIT.md`, when present,
- build/export/status outputs.

## 6. Outputs

### 6.1 Scratch Run Directory

Every run writes an untracked scratch directory:

```text
.scratch/fig-loop-runs/<YYYYMMDD-HHMMSS>-<name>/
├── run_manifest.json
├── iteration_001.json
├── iteration_002.json
├── command_logs/
└── decision.md
```

`run_manifest.json` records stable run metadata:

- fixture name,
- branch and commit SHA,
- mode,
- goal,
- max iterations,
- start/end timestamps,
- final stop reason,
- generated artifact paths,
- command exit codes.

### 6.2 Iteration Record

Each `iteration_NNN.json` records:

- pre-state from `/fig_status`,
- command results,
- source/artifact hashes relevant to critique freshness,
- findings seen,
- adjudication state,
- active patch target,
- escalation level and whether user/domain review is required,
- recommended next action,
- human gate status.

### 6.3 Durable Fixture Artifacts

The only durable fixture artifact proposed for v0.1 is:

```text
examples/<name>/critique_adjudication.yaml
```

This file maps critique findings to decisions:

```yaml
schema: figure-agent.critique-adjudication.v1
fixture: <name>
source_critique_hash: sha256:<critique.md content hash>
decisions:
  - finding_id: C001
    decision: apply | dismiss | defer | needs_human | resolved
    reason: "<short reason>"
    patch_target: "<panel/sub-region/source line target>"
    evidence: "<command, image, theory guard, or human note>"
```

The loop must not edit `critique.md` in place to mark decisions. Critique is
the reviewer output; adjudication is the author/loop decision layer.

## 7. Evaluation Axes

The loop records separate verdicts for each axis:

| Axis | Source | Machine action |
|---|---|---|
| render | `/fig_status`, `/fig_compile` | can block patch/export if stale or failing |
| static_visual | collision, clash, drift, perception pack | can recommend patch target |
| critique | `critique.md` + freshness metadata | can open findings |
| theory | `theory_guard.md` | can block acceptance, not auto-resolve |
| reference_fidelity | `reference_pack.md`, panel references | can mark needs_human for transfer decisions |
| story_hierarchy | authoring contract, critique findings | can recommend but not auto-accept |
| export | `/fig_export`, export freshness | can block release readiness |
| publication_safety | `QUALITY_AUDIT.md` | human gate only |

No v0.1 command should convert these axes into one opaque score. A compact
summary may exist, but the raw axis verdicts must remain available.

## 8. Stop Policy

The loop stops when any of these is true:

- `max_iterations` reached.
- No actionable finding remains after adjudication.
- The next action requires human/domain judgment.
- `/fig_status` reports reference input missing.
- `/fig_compile` fails before producing a reviewable render.
- The same finding remains unresolved after two patch attempts.
- The loop reaches workflow-ready state for the requested mode.

The stop reason must be explicit in `decision.md`.

The loop also records an escalation level so manual approval and human/domain
review are not conflated:

| Level | Meaning |
|---|---|
| `none` | Loop is closed for the requested mode. |
| `agent_action_required` | Routine command or local loop-contract work is needed. |
| `patch_allowed` | Exactly one safe patch target exists. |
| `manual_approval_required` | A deliberate state promotion is needed, such as `--force-golden` or `accepted: true`. |
| `human_review_required` | Domain judgment is needed for mechanism, topology, reference role, publication safety, or conflicting reviewer signals. |
| `ambiguous_patch_selection` | More than one patch target is actionable, so the loop must not choose one silently. |

## 9. Runner Boundary

The first runner should live outside the core compile/export scripts:

```text
scripts/fig_loop.py
```

Its v0.1 responsibilities:

1. create the scratch run directory,
2. run read-only status/preflight commands,
3. run requested verification commands,
4. parse `critique.md` and `critique_adjudication.yaml`,
5. write iteration records and `decision.md`,
6. recommend the next action.

It must reject direct git mutation commands and must not stage, commit, reset,
checkout, clean, or push.

The runner may call existing script interfaces but should not duplicate their
logic. For example, critique freshness remains owned by `status.py` and
`quality_manifest.py`.

## 10. Human Gates

The loop must stop and ask for human/domain review when:

- a BLOCKER theory guard is missing, failed, or ambiguous,
- a finding changes scientific mechanism or topology,
- a reference is being used beyond its declared role,
- publication-compliance status is unknown,
- a patch would change `accepted`, `golden_contract`, or submission-safety
  fields,
- two reviewers or axes disagree on whether a finding is real.

This is not a weakness of the loop. It is the safety layer that prevents
automated polish from silently changing the manuscript claim.

## 11. Issue Slices

### Issue 1: Critique Adjudication Schema

Add parser/writer support for `critique_adjudication.yaml`.

Files:

- `scripts/critique_adjudication.py`
- `tests/test_critique_adjudication.py`
- `docs/superpowers/specs/2026-05-17-fig-loop-contract-design.md`

Acceptance:

- validates schema and allowed decisions,
- detects stale adjudication when `critique.md` hash changes,
- preserves unknown future fields,
- no changes to compile/export behavior.

### Issue 2: Verify-Only Fig Loop Runner

Add `scripts/fig_loop.py` in verify-only mode.

Files:

- `scripts/fig_loop.py`
- `tests/test_fig_loop.py`
- `commands/fig_loop.md`
- `skills/figure-agent/SKILL.md`

Acceptance:

- creates `.scratch/fig-loop-runs/...`,
- writes `run_manifest.json`, `iteration_001.json`, and `decision.md`,
- calls existing status/check surfaces instead of duplicating them,
- blocks git mutation commands,
- leaves the git worktree unchanged.

### Issue 3: Loop Status Summary

Teach the runner to summarize axis verdicts and stop reason.

Files:

- `scripts/fig_loop.py`
- `tests/test_fig_loop.py`

Acceptance:

- reports each axis separately,
- stops on missing reference inputs,
- stops on human-gated findings,
- identifies next patch target from adjudicated findings or active sub-region
  context.

### Issue 4: Patch-Assisted Protocol

Define the handoff contract for an outer agent to patch one sub-region.

Files:

- `commands/fig_loop.md`
- `docs/milestones/2026-05-17-fig-loop-pilot.md`

Acceptance:

- no hidden auto-editing,
- patch target must be one finding id or one sub-region id,
- compile/critique freshness must close after the patch,
- unresolved findings remain visible.

### Issue 5A: Safe Auto-Patch Readiness Gate

Before any safe auto-patch runner exists, `/fig_loop` must classify a single
patch handoff as `auto_patch_candidate`, `patch_assisted_only`, or
`human_review_required`. This classification is read-only and must set
`may_edit: false`.

Acceptance:

- no source or artifact mutation,
- one selected target only,
- candidate classes limited to label/style/spacing/clipping/whitespace,
- mechanism, topology, theory, reference interpretation, accepted/golden, and
  publication-safety changes blocked,
- before/after evidence and rollback path listed as required future evidence.

### Issue 5B: Safe Auto-Patch Pilot

Only after Issues 1-4, Issue 5A, and at least five dogfood runs.

Acceptance:

- limited to label/style/spacing classes,
- rollback path documented,
- no theory or mechanism edits,
- before/after evidence captured in scratch run directory.

## 12. Verification Plan

Initial documentation verification:

```bash
git diff --check
```

Future Issue 1-2 verification:

```bash
uv run pytest -q tests/test_critique_adjudication.py tests/test_fig_loop.py
uv run pytest -q tests/test_status.py tests/test_quality_manifest.py
uv run ruff check .
git diff --check
```

Plugin validation after adding `/fig_loop`:

```bash
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## 13. Open Questions

The following are intentionally deferred until after the verify-only runner has
real dogfood evidence:

- whether `critique_adjudication.yaml` should be committed for every fixture or
  only for golden/pilot fixtures,
- whether loop summaries should feed `QUALITY_AUDIT.md` automatically,
- whether safe auto-patch should be a runner mode or a separate host-agent
  protocol,
- whether blind A/B scoring belongs inside `figure-agent` or in an external
  evaluation harness.

## 14. First Implementation Decision

Build Issue 1 first.

Rationale: without `critique_adjudication.yaml`, the runner cannot distinguish
true positives from dismissed findings, cannot know what was already resolved,
and cannot choose a defensible next patch target. The adjudication schema is the
smallest durable interface that turns critique from a report into loop state.
