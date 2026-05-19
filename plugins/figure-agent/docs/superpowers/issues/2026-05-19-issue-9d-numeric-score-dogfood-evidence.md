# Issue 9D: Numeric Score Dogfood Evidence

**Date:** 2026-05-19 KST
**Status:** open
**Parent:** Issue 9
**Depends on:** Issue 9B
**Type:** HITL evidence

## Problem

Issue 9B added optional advisory numeric score fields to
`journal_grade_assessment` and hardened validator/loop behavior. The code now
knows how to accept, reject, and surface scores, but the plugin has not yet
proven that host-authored `/fig_critique` runs produce useful numeric scores on
real fixtures.

The risk is not schema shape. The risk is calibration behavior:

- host critiques may omit scores even when the prompt recommends them;
- host critiques may produce numbers that contradict `benchmark_level`;
- `overall_score` may be mistaken for cumulative progress;
- `sub_scores` may collapse to one flat number and add no diagnostic value;
- numeric score may distract agents from the actual stop boundary or human
  gate.

Issue 9D collects real evidence before any UI, driver, or release workflow
treats numeric scores as more than advisory context.

## Goal

Collect at least five real fixture runs using the Issue 9B numeric score
contract and decide whether the score fields are useful, confusing, too coarse,
or unsafe as advisory loop evidence.

## Fixture Queue

Use real fixtures that already declared reference grounding during Issue 9C:

1. `fig1_overview_v2_pair_001_vault`
2. `golden_trap_depth_picture`
3. `fig1_overview_v2`
4. `n3_trial_01_trap_depth`
5. `n3_trial_02_actuation_sequence`

Do not substitute critique-not-required fixtures unless the queue cannot run.
Do not author new reference images or edit fixture specs to make the evidence
look cleaner.

## Per-Run Procedure

Start each run from the canonical driver:

```bash
cd plugins/figure-agent
uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood 9D numeric score evidence" --dry-run
```

Follow only the returned `safe_command`.

If the driver returns `/fig_critique <name>`, run that slash command in host
Claude so the host reads the current build image, references, briefing, and
generated brief. The resulting `critique.md` should be schema
`figure-agent.critique.v1.2` and should include:

- `journal_grade_assessment.overall_score`
- complete `journal_grade_assessment.sub_scores`
- `journal_grade_assessment.score_rationale`

After a critique is written, run:

```bash
uv run python3 scripts/critique_adjudication.py scaffold <name> --force
uv run python3 scripts/fig_loop.py <name> --goal "dogfood 9D numeric score evidence" --json
uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood 9D numeric score evidence" --dry-run
```

If the driver does not require critique because an existing v1.2 score-bearing
critique is fresh, record that as a reuse case only if the critique contains a
complete score block and `score_policy` appears in `/fig_loop`.

## Evidence To Capture

Append each run to:

- `docs/milestones/2026-05-19-numeric-score-dogfood-evidence.md`

For each run, record:

- fixture name;
- command sequence actually used;
- whether the critique was newly generated or reused;
- `critique_input_hash`;
- `journal_grade_assessment.assessed_artifact_hash`;
- `benchmark_level`;
- `overall_score`;
- every `sub_scores` key/value;
- `score_rationale`;
- `score_policy` from `/fig_loop`, if present;
- `score_is_gateable`;
- `evaluation_state`;
- `next_quality_bottleneck`;
- `regression_detected` and any `regressions`;
- `/fig_loop` `stop_reason`;
- `/fig_loop` `escalation_level`;
- `/fig_driver` final action and stop boundary;
- reviewer verdict: `useful`, `too_flat`, `contradictory`, `unsafe`, or
  `invalid`;
- short rationale for the verdict.

## Review Rubric

Mark a run `useful` when:

- score block is complete and validates;
- `overall_score` broadly agrees with `benchmark_level` without becoming a
  gate;
- `sub_scores` separate at least two meaningful quality dimensions;
- `score_rationale` explains current artifact quality, not progress history;
- `next_quality_bottleneck` remains concrete and actionable;
- `/fig_loop` and `/fig_driver` keep stop boundaries unchanged by score.

Mark a run `too_flat` when scores validate but most sub-scores are near-identical
or fail to distinguish the actual bottleneck.

Mark a run `contradictory` when numeric scores contradict quality axes,
benchmark level, or visible blockers without an explicit rationale.

Mark a run `unsafe` when the score wording or downstream state suggests release,
acceptance, export, or human gates can be bypassed.

Mark a run `invalid` when the critique omits required score fields after trying
to score, fails validation, has stale hashes, or `/fig_loop` cannot ingest the
assessment.

## Acceptance Criteria

- [ ] At least five real fixture runs are recorded.
- [ ] Every valid run includes a complete numeric score block or records why the
  host did not produce one.
- [ ] Every valid score block passes `critique_adjudication.py scaffold`.
- [ ] Every valid run records `/fig_loop` score surfacing and `/fig_driver`
  follow-up action.
- [ ] At least one run demonstrates that score does not bypass a non-score gate
  such as `force_golden_required`, `human_gate_required`, or
  `agent_action_required`.
- [ ] Every run has reviewer verdict `useful`, `too_flat`, `contradictory`,
  `unsafe`, or `invalid`.
- [ ] Any validation, ingestion, or safety defect is either fixed with tests or
  recorded as a follow-up issue.
- [ ] No source patch, golden export, accepted state, or publication provenance
  state is mutated solely for score dogfood.

## Verification

If only evidence documents change:

```bash
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

If code changes are required to fix a dogfood defect:

```bash
uv run pytest -q tests/test_critique_brief.py tests/test_critique_adjudication.py tests/test_fig_loop.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Out of Scope

- Score-driven release gates.
- UI score display.
- Driver action changes.
- Deterministic OCR/raster score model.
- Learned quality model.
- New reference authoring for critique-not-required fixtures.
- Auto-patching, auto-export, golden mutation, accepted mutation, or
  publication provenance mutation.

## Claude Handoff Prompt

Use this compact prompt for each fixture:

```text
Goal: Run Issue 9D numeric-score dogfood evidence for fixture <name>.

Workspace: /Users/choemun-yeong/workspace/ResearchOS/[figure-agent]
Plugin root: plugins/figure-agent

Source of truth:
- docs/superpowers/issues/2026-05-19-issue-9d-numeric-score-dogfood-evidence.md
- commands/fig_critique.md

Task:
1. cd plugins/figure-agent
2. Run:
   uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood 9D numeric score evidence" --dry-run
3. Follow only the returned safe_command. If it is /fig_critique <name>, run /fig_critique <name> using host vision. Write critique.md only through that command contract.
4. Ensure the host critique attempts the Issue 9B score block: overall_score, complete sub_scores, and score_rationale.
5. Run:
   uv run python3 scripts/critique_adjudication.py scaffold <name> --force
   uv run python3 scripts/fig_loop.py <name> --goal "dogfood 9D numeric score evidence" --json
   uv run python3 scripts/fig_driver.py <name> --mode review --goal "dogfood 9D numeric score evidence" --dry-run
6. Append one row to docs/milestones/2026-05-19-numeric-score-dogfood-evidence.md with all fields required by Issue 9D.

Constraints:
- Do not patch source.
- Do not force golden exports.
- Do not edit accepted state.
- Do not mutate publication provenance.
- Do not invent scores outside the host-authored critique.
- Do not claim success unless critique validation, fig_loop ingestion, and driver dry-run all complete.
```
