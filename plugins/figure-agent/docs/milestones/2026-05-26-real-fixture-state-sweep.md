# Real Fixture State Sweep

**Date:** 2026-05-26 KST
**Status:** implemented; one polish-route defect found and fixed

## Scope

This sweep checked whether real fixture states produce conservative,
non-contradictory next actions across `/fig_status` and
`/fig_drive --mode authoring|review|polish|release`.

No compile/export/critique command was run. No fixture source, generated export,
accepted/golden state, or publication provenance file was intentionally
mutated.

## Fixtures

Representative fixtures with different state shapes:

- `fig1_overview_v2`
- `fig1_overview_v2_pair_001_vault`
- `fig3_trapping_concept`
- `fig5_floating_clip_mechanism`
- `golden_trap_depth_picture`
- `n3_trial_01_trap_depth`
- `n3_trial_02_actuation_sequence`
- `smoke_trap_demo`

## Sweep Findings

Most fixtures routed consistently:

| Fixture shape | Observed next action |
| --- | --- |
| stale render | all modes returned `run_compile` |
| fresh render + stale critique | review/polish/release returned `run_critique`; authoring stopped at render-fresh completion |
| critique not required + stale render | all modes returned `run_compile` |

One defect surfaced:

| Fixture | Mode | Before fix | Why it was wrong |
| --- | --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | polish | `polish_handoff_stop` with no current loop checkpoint | Issue 48 made `ready_for_svg_polish` a necessary route for SVG polish; polish mode was still falling back to export-current handoff without a loop checkpoint. |

## Fix

`scripts/fig_driver.py` now returns `run_fig_loop` /
`mode_forbidden_action` when polish mode reaches a current generated export but
does not have a current loop checkpoint whose editorial summary routes
`ready_for_svg_polish`.

The existing ready-path behavior is preserved: when a valid current loop
checkpoint routes `ready_for_svg_polish`, polish mode still proceeds to the
bounded recipe/executor/delta/handoff sequence.

## Post-Fix Spot Check

For `fig1_overview_v2_pair_001_vault` in polish mode:

```text
action: run_fig_loop
stop_boundary: mode_forbidden_action
safe_command: uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault --goal 'Issue 50 real fixture state sweep' --json
first_blocker: export_tracked_golden
```

This is conservative: it no longer silently enters SVG polish, and it keeps the
tracked-golden human blocker visible in the reason string.

## Clean Re-Run Summary

After committing the fix, the 8-fixture x 4-mode dry-run sweep was re-run from a
clean workspace. Every row reported `workspace_warnings: 0`.

| Pattern | Fixtures | Result |
| --- | --- | --- |
| stale render first | `fig1_overview_v2`, `fig3_trapping_concept`, `fig5_floating_clip_mechanism`, `n3_trial_01_trap_depth`, `n3_trial_02_actuation_sequence`, `smoke_trap_demo` | all modes returned `run_compile` |
| fresh render + stale critique | `golden_trap_depth_picture` | authoring stopped at render-fresh completion; review/polish/release returned `run_critique` |
| fresh render + fresh critique + tracked golden | `fig1_overview_v2_pair_001_vault` | review/release remained manually blocked; polish returned `run_fig_loop` until a current loop checkpoint proves `ready_for_svg_polish` |

## Follow-Up

The next useful sweep should be run after fixture authors refresh stale renders
and critiques. This issue deliberately did not execute compile/export/critique
because it was testing the dry-run state surfaces, not changing fixture state.
