# SVG Polish Promotion Evidence Refresh

Date: 2026-06-03

Related issues:

- `docs/superpowers/issues/2026-06-02-issue-100cq-svg-polish-queue-readiness-filters.md`
- `docs/superpowers/issues/2026-06-03-issue-100dt-polish-mode-forbidden-guidance.md`

Status: completed - real-fixture positive SVG polish candidate count remains 0

## Goal

Refresh the real-fixture SVG polish promotion evidence after the queue/driver
operator-guidance fixes through Issue 100DT. This pass is read-only: it does
not refresh host critiques, compile dirty source, export, force golden, edit
SVG, or mutate accepted/publication state.

## Commands

```bash
uv run python3 scripts/fig_queue.py \
  --mode polish \
  --goal 'svg promotion evidence refresh'

uv run python3 scripts/fig_queue.py \
  --mode polish \
  --goal 'svg promotion evidence refresh' \
  --can-start-svg-polish true \
  --json

uv run python3 scripts/fig_queue.py \
  --mode polish \
  --goal 'svg promotion evidence refresh' \
  --json
```

## Current Queue Result

`--can-start-svg-polish true` returned zero rows.

The full polish queue reported eight fixtures:

```text
by_action:
  polish_handoff_stop: 1
  run_compile: 1
  run_critique: 4
  run_fig_loop: 2

by_required_actor:
  host_llm: 4
  release_operator: 1
  workflow_agent: 3

by_svg_polish_gate_state:
  blocked: 6
  no_current_checkpoint: 2

by_svg_polish_next_action:
  rerun_fig_loop: 2
  resolve_release_boundary: 1
  run_fig_compile: 1
  run_fig_critique: 4

by_svg_polish_blocking_source:
  driver_blocker: 2
  driver_prerequisite: 6
```

## Fixture-Level Interpretation

| Fixture | action | actor | SVG next action | Interpretation |
| --- | --- | --- | --- | --- |
| `fig1_overview_v2` | `run_critique` | `host_llm` | `run_fig_critique` | critique refresh required before SVG evidence |
| `fig1_overview_v2_pair_001_vault` | `run_compile` | `workflow_agent` | `run_fig_compile` | user-owned dirty source made render missing/stale; do not touch in plugin hardening loop |
| `fig3_trapping_concept` | `run_fig_loop` | `workflow_agent` | `rerun_fig_loop` | no current loop checkpoint proves `ready_for_svg_polish` |
| `fig5_floating_clip_mechanism` | `polish_handoff_stop` | `release_operator` | `resolve_release_boundary` | accepted/final-ready release boundary wins before polish |
| `golden_trap_depth_picture` | `run_critique` | `host_llm` | `run_fig_critique` | critique refresh required before SVG evidence |
| `n3_trial_01_trap_depth` | `run_critique` | `host_llm` | `run_fig_critique` | critique refresh required before SVG evidence |
| `n3_trial_02_actuation_sequence` | `run_critique` | `host_llm` | `run_fig_critique` | critique refresh required before SVG evidence |
| `smoke_trap_demo` | `run_fig_loop` | `workflow_agent` | `rerun_fig_loop` | no current loop checkpoint proves `ready_for_svg_polish` |

## Defect Found And Fixed

During this evidence refresh, single-fixture driver output for
`fig3_trapping_concept` and `smoke_trap_demo` exposed a guidance contradiction:

- `stop_boundary: mode_forbidden_action`
- `svg_polish_gate.state: no_current_checkpoint`
- `operator_guidance.next_step` still said to run the selected `fig_loop`
  command.

Issue 100DT fixed the contradiction. The driver now says the selected next
action is not executable in polish mode and routes the operator back to
`/fig_drive <fixture> --mode review` before returning to polish mode.

## Judgment

The positive real-fixture SVG polish path is still unproven. This is currently
an evidence/prerequisite state, not a broad design failure:

- The plugin does not over-promote any real fixture to SVG polish.
- Queue filters make the zero-ready result explicit.
- Release, dirty-source, host-vision, and loop-checkpoint gates remain
  independent.
- The latest discovered guidance contradiction was fixed in Issue 100DT.

The next valid positive-evidence pass must first close the host-vision critique
refresh rows and avoid using the user-owned dirty
`fig1_overview_v2_pair_001_vault.tex` as plugin hardening work.
