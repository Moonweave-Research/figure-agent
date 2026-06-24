# Issue 9C: Fresh Re-Audit Dogfood Evidence

**Date:** 2026-05-19 KST
**Status:** completed in milestone `docs/milestones-archive/2026-05-19-fresh-reaudit-dogfood-evidence.md`.
**Parent:** Issue 9
**Depends on:** Issue 9A
**Unblocks:** Issue 9B
**Type:** HITL

## Problem

Issue 9A added `journal_grade_assessment` to v1.2 critiques and surfaces that
assessment in `/fig_loop`, but the contract has not yet been proven against
real host-LLM critique runs. Moving directly to Issue 9B numeric scoring would
calibrate numbers against synthetic tests instead of real failure modes.

The missing evidence is not whether the code parses the field. That is already
covered by tests. The missing evidence is whether a host LLM can repeatedly use
the level-only fresh re-audit rubric to expose the next real bottleneck without
treating the score as cumulative progress.

## Goal

Collect at least five real v1.2 critique/loop observations that show whether
level-only `journal_grade_assessment` is sufficient, confusing, or too coarse
before implementing any numeric `overall_score` or `sub_scores`.

## Result

The original five-fixture queue produced two valid v1.2 critique-grounded runs
and three critique-not-required blockers. A substitute pass found three
additional existing fixtures that already declared `reference_image` and did
not require spec or reference authoring. Final evidence:

- 8 total attempted fixtures.
- 5 valid v1.2 critique-grounded runs.
- 3 critique-not-required blockers retained as honest evidence.
- Observed levels: `draft` (2) and `solid_manuscript` (3).
- Observed gate shapes: `force_golden_required`, `human_gate_required`, and
  `agent_action_required`.

Issue 9B numeric calibration may proceed, but it must not assume a single
escalation shape and must not overfit to the five observed levels; no real
fixture has yet exercised `high_impact_candidate`,
`needs_human_art_direction`, or `blocked`.

## Required Fixtures

Use real fixtures already present in the plugin. Prefer this order:

1. `fig1_overview_v2_pair_001_vault`
2. `golden_trap_depth_picture`
3. `smoke_trap_demo`
4. `fig3_trapping_concept`
5. `fig5_floating_clip_mechanism`

If a fixture cannot produce a v1.2 critique because it lacks required visual or
reference inputs, record the blocker instead of substituting a synthetic case.

## Per-Run Procedure

For each fixture, start from the canonical driver:

```bash
uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood 9A fresh re-audit" --dry-run
```

Then follow the returned `safe_command`. If the driver returns
`/fig_critique <name>`, run that slash command in host Claude so the host model
reads the current build image and writes `examples/<name>/critique.md`.

After the critique is written, run:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <name>
uv run python3 scripts/fig_loop.py <name> --goal "dogfood 9A fresh re-audit" --json
uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood 9A fresh re-audit" --dry-run
```

Do not patch source, force golden exports, edit accepted state, or migrate
existing examples solely to make this evidence look cleaner.

## Evidence To Capture

Create a milestone document:

- `docs/milestones-archive/2026-05-19-fresh-reaudit-dogfood-evidence.md`

For each run, record:

- fixture name
- command sequence actually used
- whether `critique.md` is schema `figure-agent.critique.v1.2`
- `critique_input_hash`
- `journal_grade_assessment.assessed_artifact_hash`
- `score_is_gateable`
- `benchmark_level`
- `confidence`
- `next_quality_bottleneck`
- `regression_detected`
- any `regressions`
- `/fig_loop` `stop_reason`
- `/fig_loop` surfaced `journal_grade_assessment.evaluation_state`
- `/fig_driver` next action after loop ingestion
- reviewer verdict: `useful`, `too_coarse`, `confusing`, or `invalid`
- short rationale for the verdict

## Review Rubric

Mark a run `useful` only when:

- the host critique filled all mandatory v1.2 audit and quality-axis blocks;
- `journal_grade_assessment` is fresh and gateable;
- the selected `benchmark_level` is consistent with the blocking axes;
- `next_quality_bottleneck` points to a concrete next loop target; and
- the assessment does not imply monotonic progress from prior runs.

Mark a run `too_coarse` when the level is valid but cannot distinguish two
materially different quality states that would need different next actions.

Mark a run `confusing` when the host LLM fills the field but uses it as a
progress score, contradicts quality axes, or gives no actionable bottleneck.

Mark a run `invalid` when validation fails, required fields are missing, hashes
do not match, or `/fig_loop` cannot ingest the assessment.

## Claude Handoff Prompt

Use this compact prompt in a Claude session for the first dogfood run:

```text
Goal: Run Issue 9C dogfood evidence for fixture <name>.

Workspace: /Users/choemun-yeong/workspace/ResearchOS/[figure-agent]
Plugin root: plugins/figure-agent

Source of truth:
- docs/superpowers/issues/2026-05-19-issue-9c-fresh-reaudit-dogfood-evidence.md
- commands/fig_critique.md

Task:
1. cd plugins/figure-agent
2. Run:
   uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood 9A fresh re-audit" --dry-run
3. Follow only the returned safe_command. If it is /fig_critique <name>, run /fig_critique <name> using host vision. Write critique.md only through that command contract.
4. Run:
   uv run python3 scripts/critique_adjudication.py scaffold <name>
   uv run python3 scripts/fig_loop.py <name> --goal "dogfood 9A fresh re-audit" --json
   uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood 9A fresh re-audit" --dry-run
5. Append one row to docs/milestones-archive/2026-05-19-fresh-reaudit-dogfood-evidence.md with all fields required by Issue 9C.

Constraints:
- Do not patch source.
- Do not force golden exports.
- Do not edit accepted state.
- Do not invent numeric scores.
- Do not claim success unless v1.2 critique validation, fig_loop ingestion, and driver dry-run all complete.
```

## Acceptance Criteria

- [x] At least five real fixture runs are recorded.
- [x] Each recorded run uses a host-authored v1.2 `critique.md` or records why
  v1.2 critique could not be produced.
- [x] Every valid run records a fresh/gateable or stale/non-gateable
  `journal_grade_assessment` outcome.
- [x] `/fig_loop` ingestion behavior is captured for every valid run.
- [x] `/fig_driver` next action after loop ingestion is captured for every
  valid run.
- [x] Every run has reviewer verdict `useful`, `too_coarse`, `confusing`, or
  `invalid`.
- [x] Any validation or ingestion defect is either fixed with tests or recorded
  as a follow-up issue.
- [x] Issue 9B remains deferred unless evidence shows level-only assessment is
  insufficient and numeric scoring has a concrete calibration policy.

## Verification

If only the evidence document changes:

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

If code changes are required to fix a dogfood defect:

```bash
uv run pytest -q tests/test_critique_adjudication.py tests/test_fig_loop.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Out of Scope

- Numeric `overall_score` or `sub_scores`.
- Auto-patching.
- Auto-export or `--force-golden` execution.
- Accepted-state mutation.
- Claiming a journal acceptance level as objective fact.
