# SVG Polish Readiness Filter Evidence

Date: 2026-06-02

Related issue:

- `docs/superpowers/issues/2026-06-02-issue-100cr-svg-polish-gate-blocker-source-filters.md`

Status: completed - real-fixture positive SVG polish candidate count is still 0

## Goal

Use the Issue 100CQ queue filters to make the real-fixture SVG polish promotion
question repeatable:

```bash
uv run python3 scripts/fig_queue.py --mode polish --can-start-svg-polish true --json
```

The pass also verifies whether SVG blocker-source filters can explain the
no-ready result without manual JSON post-processing.

## Baseline

Fresh isolated worktree:

```text
/fig_queue --mode polish --can-start-svg-polish true
unfiltered_total: 8
rows: []
```

`/fig_queue --mode polish --command-plan` reported eight executable compile
actions. No source, critique, accepted, golden, SVG polish, or publication state
was edited.

## Mechanical Prerequisite Pass

Command:

```bash
uv run python3 scripts/fig_queue_run.py \
  --mode polish \
  --goal issue100cr-svg-polish-readiness-evidence \
  --max-fixtures 8 \
  --execute
```

Result:

- planned executable: 8
- planned blocked: 0
- attempted: 8
- failed: 0
- executed commands: 10

The extra executed commands came from `/fig_run` continuing safe deterministic
steps for some fixtures after compile, such as export for critique-not-required
fixtures. This stayed inside generated build/export state in the isolated
worktree.

## Post-Pass Queue

After the mechanical pass:

```text
by_action:
  run_critique: 5
  run_fig_loop: 2
  polish_handoff_stop: 1

by_required_actor:
  host_llm: 5
  workflow_agent: 2
  release_operator: 1

by_svg_polish_gate_state:
  blocked: 5
  no_current_checkpoint: 3
```

`--can-start-svg-polish true` still returned zero rows.

The five host-LLM rows are:

- `fig1_overview_v2`
- `fig1_overview_v2_pair_001_vault`
- `golden_trap_depth_picture`
- `n3_trial_01_trap_depth`
- `n3_trial_02_actuation_sequence`

All five are blocked by critique refresh before SVG polish evidence can be
meaningful.

The three no-current-checkpoint rows are:

- `fig3_trapping_concept`
- `fig5_floating_clip_mechanism`
- `smoke_trap_demo`

They cannot start SVG polish because no current loop checkpoint proves
`ready_for_svg_polish`; `fig5_floating_clip_mechanism` additionally routes
through an accepted/final-ready release boundary.

## Defect Found And Fixed

The evidence pass found that:

```bash
uv run python3 scripts/fig_queue.py \
  --mode polish \
  --svg-polish-blocking-source driver_blocker \
  --json
```

returned zero rows even though the no-current-checkpoint rows had
`svg_polish_gate.blocking_items[].source: driver_blocker`.

Root cause: queue rows copied `svg_polish_blocking_sources` only from
`svg_polish_readiness.blocking_items`, not from
`svg_polish_gate.blocking_items`.

Fix: `fig_queue.py` now merges blocker sources from both gate and readiness
objects. The same command now returns the three no-current-checkpoint rows, and
`--svg-polish-blocking-source driver_prerequisite` returns the five critique
prerequisite rows.

## Judgment

No real fixture currently proves positive `ready_for_svg_polish` in this
isolated pass. The plugin did not over-promote any fixture. The route remains
conservative, but the queue can now explain the no-ready result directly:

- `driver_prerequisite`: five critique refresh blockers
- `driver_blocker`: three no-current-checkpoint/final-boundary blockers

The next positive-evidence pass must refresh the five host-vision critiques
first, then rerun:

```bash
uv run python3 scripts/fig_queue.py --mode polish --can-start-svg-polish true
```
