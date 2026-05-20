# Issue 9D Numeric Score Dogfood Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Collect real fixture evidence that the Issue 9B advisory numeric score block is useful, safe, and correctly consumed by `/fig_loop` and `/fig_driver`.

**Architecture:** This is an evidence-first HITL slice, not a code slice. Host Claude produces or refreshes `critique.md` through `/fig_critique`; local scripts validate, ingest, and route the result; the milestone document records exactly what happened.

**Tech Stack:** figure-agent slash commands, Python scripts, pytest only if code defects are found, Markdown evidence documents.

---

## Source Of Truth

Read first:

- `plugins/figure-agent/docs/superpowers/issues/2026-05-19-issue-9d-numeric-score-dogfood-evidence.md`
- `plugins/figure-agent/docs/superpowers/issues/2026-05-19-issue-9-journal-grade-benchmark-scoring.md`
- `plugins/figure-agent/docs/superpowers/specs/2026-05-19-issue-9b-numeric-quality-score-calibration-design.md`
- `plugins/figure-agent/docs/milestones/2026-05-19-fresh-reaudit-dogfood-evidence.md`
- `plugins/figure-agent/commands/fig_critique.md`

## Dirty Worktree Guard

Before editing or running evidence commands:

```bash
git status --short --branch
```

Known unrelated dirty file:

```text
 M plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/subregion_iteration_log.md
```

Do not stage or modify that file for Issue 9D unless the user explicitly asks.

## Task 1: Create Evidence Milestone Skeleton

**Files:**

- Create: `plugins/figure-agent/docs/milestones/2026-05-19-numeric-score-dogfood-evidence.md`

- [ ] **Step 1: Add the milestone header**

Create the file with this content:

```markdown
# Numeric Score Dogfood Evidence (Issue 9D)

**Date opened:** 2026-05-19 KST
**Status:** open

This milestone records real host-LLM `/fig_critique` runs after Issue 9B added
optional advisory numeric score fields to `journal_grade_assessment`.

The purpose is to test whether `overall_score`, `sub_scores`, and
`score_rationale` are useful advisory evidence without becoming release gates,
progress meters, or substitutes for `quality_axes`, `benchmark_level`, human
review, export state, final-artifact state, accepted state, or golden state.

## Fixture Queue

1. `fig1_overview_v2_pair_001_vault`
2. `golden_trap_depth_picture`
3. `fig1_overview_v2`
4. `n3_trial_01_trap_depth`
5. `n3_trial_02_actuation_sequence`

## Result Summary

- Total attempted fixtures: 0
- Valid numeric score runs: 0
- Runs without complete score block: 0
- Validation or ingestion defects: 0
- Safety defects: 0

## Evidence Rows

Rows should use this structure:

### Run N: `<fixture>`

- **commands used:** `<exact sequence>`
- **critique source:** newly generated | reused fresh | not produced
- **critique schema:** `<schema or N/A>`
- **critique_input_hash:** `<sha256:... or N/A>`
- **assessed_artifact_hash:** `<sha256:... or N/A>`
- **benchmark_level:** `<value or N/A>`
- **overall_score:** `<number or N/A>`
- **sub_scores:** `<mapping or N/A>`
- **score_rationale:** `<text or N/A>`
- **score_policy from /fig_loop:** `<value or absent>`
- **score_is_gateable:** `<true/false/N/A>`
- **evaluation_state:** `<passed/stale/blocked/N/A>`
- **next_quality_bottleneck:** `<value or N/A>`
- **regression_detected:** `<true/false/N/A>`
- **regressions:** `<list or []/N/A>`
- **/fig_loop stop_reason:** `<value>`
- **/fig_loop escalation_level:** `<value>`
- **/fig_driver final action:** `<value>`
- **/fig_driver stop_boundary:** `<value or null>`
- **reviewer verdict:** useful | too_flat | contradictory | unsafe | invalid
- **rationale:** `<short evidence-grounded rationale>`

## Final Judgment

Pending 5 real fixture runs.
```

- [ ] **Step 2: Verify doc formatting**

Run:

```bash
git diff --check
```

Expected: exit 0.

## Task 2: Run Fixture Evidence Rows

**Files:**

- Modify: `plugins/figure-agent/docs/milestones/2026-05-19-numeric-score-dogfood-evidence.md`
- May modify through slash command only: `plugins/figure-agent/examples/<name>/critique.md`
- May modify through scaffold only: `plugins/figure-agent/examples/<name>/critique_adjudication.yaml`

- [ ] **Step 1: For each fixture, start from driver**

Run:

```bash
cd plugins/figure-agent
uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood 9D numeric score evidence" --dry-run
```

Expected: JSON with `schema: figure-agent.driver.v1`, `may_execute: false`,
and either a `safe_command` or a stop boundary.

- [ ] **Step 2: Follow exactly one safe command**

If `safe_command` is `/fig_critique <name>`, run the slash command in host
Claude. The host critique must attempt:

```yaml
journal_grade_assessment:
  overall_score: 0-100
  sub_scores:
    storyline: 0-100
    composition: 0-100
    component_fidelity: 0-100
    scientific_plausibility: 0-100
    label_semantics: 0-100
    polish: 0-100
    reference_fidelity: 0-100
    export_scale_readability: 0-100
  score_rationale: "<current artifact only>"
```

If the driver returns a non-critique safe command, run only that command and
record why no score critique was produced.

- [ ] **Step 3: Validate and ingest**

Run:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <name> --force
uv run python3 scripts/fig_loop.py <name> --goal "dogfood 9D numeric score evidence" --json
uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood 9D numeric score evidence" --dry-run
```

Expected for a valid score run:

- scaffold exits 0;
- `/fig_loop` JSON contains `journal_grade_assessment.overall_score`;
- `/fig_loop` JSON contains `journal_grade_assessment.score_policy:
  advisory_fresh_reaudit_not_gate` only when score is fresh and gateable;
- `/fig_driver` does not invent or mutate scores.

- [ ] **Step 4: Append evidence row**

Append the full row to
`docs/milestones/2026-05-19-numeric-score-dogfood-evidence.md`.

- [ ] **Step 5: Repeat until 5 fixture attempts are recorded**

Stop only after every fixture in the queue has either a valid row or a recorded
blocker row.

## Task 3: Review Evidence

**Files:**

- Modify: `plugins/figure-agent/docs/milestones/2026-05-19-numeric-score-dogfood-evidence.md`

- [ ] **Step 1: Score usefulness review**

For each valid run, classify:

- `useful`: score block validates, sub-scores distinguish real dimensions,
  rationale is current-artifact-only, and stop boundaries are unchanged.
- `too_flat`: score block validates but sub-scores are near-identical or do not
  identify the bottleneck.
- `contradictory`: score contradicts benchmark level, quality axes, or visible
  blockers.
- `unsafe`: score implies release/acceptance/export/human gate bypass.
- `invalid`: missing score block, stale hash, validation failure, or ingestion
  failure.

- [ ] **Step 2: Cross-run pattern review**

Add final summary bullets for:

- valid numeric score run count;
- verdict distribution;
- score range by `benchmark_level`;
- whether `sub_scores` are meaningfully differentiated;
- whether score ever changed stop reason or driver action;
- whether a code defect was found.

- [ ] **Step 3: Follow-up decision**

End the milestone with exactly one recommendation:

- keep numeric scores as advisory-only and proceed to UI/driver display design;
- revise prompt wording and rerun 9D;
- open a code defect issue;
- remove/defer numeric scoring.

## Task 4: Verification And Commit

**Files:**

- Stage only Issue 9D docs and any host-generated critique/adjudication files
  that are intentionally part of the evidence run.

- [ ] **Step 1: Run docs-only verification if no code changed**

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all pass.

- [ ] **Step 2: Run code verification if any code changed**

```bash
uv run pytest -q tests/test_critique_brief.py tests/test_critique_adjudication.py tests/test_fig_loop.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Expected: all pass with the repository's known skip/xfail counts.

- [ ] **Step 3: Confirm unrelated dirty files are excluded**

```bash
git status --short --branch
git diff --cached --name-only
```

Expected: unrelated
`plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/subregion_iteration_log.md`
is not staged.

- [ ] **Step 4: Commit**

```bash
git commit -m "Open numeric score dogfood evidence"
```

Expected: one narrow commit for Issue 9D setup or evidence closeout.

## Self-Review

- **Spec coverage:** The plan covers fixture queue, per-run procedure, evidence
  fields, review rubric, verification, and scope boundaries from Issue 9D.
- **Placeholder scan:** No TODO/TBD placeholders are present. Angle-bracket
  fields appear only in reusable command/evidence templates that the runner
  replaces per fixture.
- **Type consistency:** The score field names match Issue 9B:
  `overall_score`, `sub_scores`, `score_rationale`, `score_policy`, and
  `score_is_gateable`.
