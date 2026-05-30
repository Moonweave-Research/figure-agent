# Whole-Corpus Release Smoke

**Date:** 2026-05-30 KST
**Issue:** 89C - Whole-Corpus Release Smoke
**Status:** completed on `codex/issue70-guided-autonomy-roadmap`

## Scope

Run the real fixture corpus through the queue in `review`, `release`, and
`polish` modes. The goal is not to fix figures. The goal is to verify that each
fixture lands in an explicit operator bucket and that no protected boundary can
be crossed by queue automation.

## Commands

```bash
uv run python3 scripts/fig_queue.py --mode review --goal "v0.9 release smoke" --json
uv run python3 scripts/fig_queue.py --mode release --goal "v0.9 release smoke" --json
uv run python3 scripts/fig_queue.py --mode polish --goal "v0.9 release smoke" --json

uv run python3 scripts/fig_queue_run.py --mode review --goal "v0.9 release smoke" --actor workflow_agent
uv run python3 scripts/fig_queue_run.py --mode release --goal "v0.9 release smoke" --actor workflow_agent
uv run python3 scripts/fig_queue_run.py --mode polish --goal "v0.9 release smoke" --actor workflow_agent
```

All commands exited 0.

## Queue Summary

### Review Mode

Total fixtures: 8

| Actor | Count | Meaning |
|---|---:|---|
| `workflow_agent` | 3 | safe verify-only loop checkpoint work |
| `host_llm` | 2 | stale critiques requiring `/fig_critique` |
| `release_operator` | 2 | tracked-golden / force-golden review |
| `human` | 1 | human decision gate |

Action distribution:

- `run_fig_loop`: 3
- `run_critique`: 2
- `release_blocked`: 2
- `human_gate_stop`: 1

Command-plan check:

- `planned_executable`: 3
- `planned_blocked`: 0 for the `workflow_agent` filter
- `executed_commands`: 0 because this was plan-only

### Release Mode

Total fixtures: 8

| Actor | Count | Meaning |
|---|---:|---|
| `release_operator` | 5 | accepted/final-ready release boundary |
| `host_llm` | 2 | stale critiques before release work |
| `human` | 1 | human gate |

Action distribution:

- `release_blocked`: 5
- `run_critique`: 2
- `human_gate_stop`: 1

Workflow-agent plan check:

- `planned_executable`: 0
- `planned_blocked`: 0
- `executed_commands`: 0

This is the expected release posture: release mode does not silently execute
golden, accepted, or publication decisions.

### Polish Mode

Total fixtures: 8

| Actor | Count | Meaning |
|---|---:|---|
| `workflow_agent` | 5 | blocked at `mode_forbidden_action`; no executable plan |
| `host_llm` | 2 | stale critiques before polish routing can be trusted |
| `human` | 1 | human gate |

Action distribution:

- `run_fig_loop`: 5
- `run_critique`: 2
- `human_gate_stop`: 1

Workflow-agent plan check:

- `planned_executable`: 0
- `planned_blocked`: 5
- `executed_commands`: 0

The `run_fig_loop` rows include a `safe_command` because the dry-run driver can
name the mechanical next command, but the queue command plan correctly blocks
them when `stop_boundary: mode_forbidden_action` is present. This is not an
execution risk; `/fig_queue_run --actor workflow_agent` produced no runs.

## Fixture Classification

| Fixture | Review | Release | Polish |
|---|---|---|---|
| `fig1_overview_v2` | human gate | human gate | human gate |
| `fig1_overview_v2_pair_001_vault` | release operator | release operator | blocked/no-op |
| `fig3_trapping_concept` | workflow agent | release operator | blocked/no-op |
| `fig5_floating_clip_mechanism` | workflow agent | release operator | blocked/no-op |
| `golden_trap_depth_picture` | release operator | release operator | blocked/no-op |
| `n3_trial_01_trap_depth` | host critique | host critique | host critique |
| `n3_trial_02_actuation_sequence` | host critique | host critique | host critique |
| `smoke_trap_demo` | workflow agent | release operator | blocked/no-op |

Every row lands in one of the accepted buckets: workflow-agent mechanical work,
host-vision critique, human decision, release operator, or blocked/no-op. No SVG
editor row appeared in this corpus snapshot because no fixture currently routes
to `ready_for_svg_polish`.

## Review Notes

1. Contract correctness: all queue outputs used
   `figure-agent.fixture-driver-queue.v1`; no row returned `error`.
2. Mutation safety: only plan/read commands were run; no source, export,
   accepted, golden, publication, or SVG state was mutated.
3. Operator usability: polish-mode `mode_forbidden_action` rows are safe but
   can look surprising because the dry-run row still carries a `safe_command`.
   The command plan is the authoritative execution surface and blocks them.

No known Issue 89C blocker remains.
