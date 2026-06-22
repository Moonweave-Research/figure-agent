# Plugin Readiness Matrix — 2026-05-23

## Purpose

This milestone checks the plugin as a workflow product rather than a single
validator: for real fixtures, do `/fig_status`, `/fig_driver --dry-run`, and
`/fig_loop` point the operator toward the same next stage?

Commands were run through Python entry points against real fixtures. `fig_loop`
used a temporary runs-root under `/tmp` and the directory was removed after the
pass, so no `.scratch` artifacts were left in the repo.

## Fixtures

| Fixture | Render | Critique | Export | Audit | First blocker | Driver review action | Loop next action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `fig1_overview_v2_pair_001_vault` | `STALE` | `STALE` | `TRACKED_GOLDEN` | `passed` | `render_stale` | `run_compile` | compile, then critique, then force-golden export |
| `golden_trap_depth_picture` | `FRESH` | `STALE` | `TRACKED_GOLDEN` | `legacy` | `critique_stale` | `run_critique` | critique refresh |
| `fig1_overview_v2` | `STALE` | `STALE` | `FRESH` | `legacy` | `render_stale` | `run_compile` | compile, then critique, then export |
| `n3_trial_01_trap_depth` | `STALE` | `STALE` | `MISSING` | `legacy` | `render_stale` | `run_compile` | compile |
| `n3_trial_02_actuation_sequence` | `STALE` | `STALE` | `MISSING` | `legacy` | `render_stale` | `run_compile` | compile |
| `smoke_trap_demo` | `STALE` | `NOT_REQUIRED` | `FRESH` | `not_applicable` | `render_stale` | `run_compile` | compile, then export |
| `fig3_trapping_concept` | `STALE` | `NOT_REQUIRED` | `FRESH` | `not_applicable` | `render_stale` | `run_compile` | compile, then export |
| `fig5_floating_clip_mechanism` | `STALE` | `NOT_REQUIRED` | `MISSING` | `not_applicable` | `render_stale` | `run_compile` | compile |

## Finding

Initial matrix pass found one inconsistency:

- `/fig_driver` prioritized stale render and recommended compile.
- `/fig_loop` prioritized stale critique and recommended `/fig_critique`.

That was misleading because host critique should assess the current render.
Issue 40 fixes this by making `/fig_loop` defer to the canonical `/fig_status`
next action when render is missing or stale.

## Post-Fix Judgment

After the fix, all tested fixtures route stale render to compile first. Critique
refresh remains the next action only when render is already fresh.

This confirms the current operator entry rule:

1. Start with `/fig_status <name>` or `/fig_driver <name> --mode review
   --goal ... --dry-run`.
2. If render is stale or missing, run `/fig_compile <name>` before critique.
3. If render is fresh and critique is missing/stale, run `/fig_critique
   <name>`.
4. Use `/fig_loop <name> --goal ...` to record a verify-only checkpoint after
   status prerequisites are closed or to inspect the current stop reason.

## Remaining Risks

- Most sample fixtures are currently stale, so this pass mainly validates
  blocker ordering rather than ready-state closeout.
- `audit_state: legacy` remains common for older fixtures; that is expected but
  means they do not fully exercise the newest audit surfaces until refreshed.
- Golden roll-forward still correctly requires explicit human approval.
