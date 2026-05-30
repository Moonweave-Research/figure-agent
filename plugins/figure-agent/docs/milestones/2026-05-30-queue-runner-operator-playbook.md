# Queue Runner Operator Playbook - Issue 82

Status: completed

Issue:

- `docs/superpowers/issues/2026-05-30-issue-82-queue-runner-dogfood-playbook.md`

## Purpose

Freeze the multi-fixture operator path after Issues 77-81 added:

- `/fig_queue`
- actor/action/blocker filters
- command-plan extraction
- `/fig_queue_run`

The goal is not to execute every fixture automatically. The goal is to make the
next actor and safe mechanical subset obvious before anyone mutates files.

## Canonical Operating Order

1. Inspect the whole queue:

   ```bash
   uv run python3 scripts/fig_queue.py --mode review --goal "<goal>"
   ```

2. Close host-vision critique rows first:

   ```bash
   uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor host_llm
   ```

   Run the listed `/fig_critique <name>` commands in the host LLM environment.

3. Inspect workflow-agent work:

   ```bash
   uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor workflow_agent --command-plan --json
   ```

4. Plan the bounded batch:

   ```bash
   uv run python3 scripts/fig_queue_run.py --mode review --goal "<goal>" --actor workflow_agent --max-fixtures 2
   ```

5. Execute only after reading the plan:

   ```bash
   uv run python3 scripts/fig_queue_run.py --mode review --goal "<goal>" --actor workflow_agent --max-fixtures 2 --execute
   ```

   `fig_queue_run.py` does not execute shell directly. It delegates each
   planned fixture to `fig_run.run_workflow()`, which revalidates live driver
   state before any deterministic command.

6. Handle human/release/SVG gates explicitly:

   ```bash
   uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor human
   uv run python3 scripts/fig_queue.py --mode review --goal "<goal>" --actor release_operator
   uv run python3 scripts/fig_queue.py --mode polish --goal "<goal>" --actor svg_editor
   ```

## Dogfood Commands

All commands below were plan-only/read-only. No source, export, accepted,
golden, publication, or generated artifact state was mutated.

```bash
uv run python3 scripts/fig_queue.py --mode review --goal "Issue 82 queue runner dogfood" --json
uv run python3 scripts/fig_queue.py --mode review --goal "Issue 82 queue runner dogfood" --actor host_llm --json
uv run python3 scripts/fig_queue.py --mode review --goal "Issue 82 queue runner dogfood" --actor workflow_agent --command-plan --json
uv run python3 scripts/fig_queue.py --mode review --goal "Issue 82 queue runner dogfood" --actor release_operator --json
uv run python3 scripts/fig_queue.py --mode review --goal "Issue 82 queue runner dogfood" --actor human --json
uv run python3 scripts/fig_queue_run.py --mode review --goal "Issue 82 queue runner dogfood" --actor workflow_agent --max-fixtures 2
```

## Current Queue Snapshot

Total fixtures: 8

Actor distribution:

| Actor | Count | Meaning |
|---|---:|---|
| `host_llm` | 2 | host vision critique refresh required |
| `workflow_agent` | 3 | deterministic workflow-agent work or closeout-blocked work |
| `release_operator` | 2 | golden/release approval boundary |
| `human` | 1 | human acceptance/review boundary |

Action distribution:

| Action | Count |
|---|---:|
| `run_critique` | 2 |
| `run_fig_loop` | 2 |
| `run_export` | 1 |
| `release_blocked` | 2 |
| `human_gate_stop` | 1 |

## Actor Queues

### Host LLM

Two fixtures need host critique:

| Fixture | Action | Stop boundary | First blocker |
|---|---|---|---|
| `n3_trial_01_trap_depth` | `run_critique` | `host_llm_critique_required` | `critique_stale` |
| `n3_trial_02_actuation_sequence` | `run_critique` | `host_llm_critique_required` | `critique_stale` |

### Workflow Agent

Three rows route to the workflow agent:

| Fixture | Action | Executable in command plan? | Reason |
|---|---|---|---|
| `fig3_trapping_concept` | `run_fig_loop` | yes | no stop boundary |
| `smoke_trap_demo` | `run_fig_loop` | yes | no stop boundary |
| `fig5_floating_clip_mechanism` | `run_export` | no | `stop_boundary:closeout_required` |

`/fig_queue_run --actor workflow_agent --max-fixtures 2` planned only the two
`run_fig_loop` fixtures and kept the closeout-blocked export out of execution.

### Release Operator

Two fixtures are release/golden boundaries:

| Fixture | Action | Stop boundary | First blocker |
|---|---|---|---|
| `fig1_overview_v2_pair_001_vault` | `release_blocked` | `force_golden_required` | `export_tracked_golden` |
| `golden_trap_depth_picture` | `release_blocked` | `force_golden_required` | `export_tracked_golden` |

### Human

One fixture is human-gated:

| Fixture | Action | Stop boundary | First blocker |
|---|---|---|---|
| `fig1_overview_v2` | `human_gate_stop` | `human_gate_required` | `not_accepted` |

## Review Notes

1. Safety: clean. The dogfood pass used read-only queue commands and plan-only
   queue-run. No generated `.scratch` records were needed.
2. Operator clarity: clean. Actor filters split the current queue into concrete
   host/workflow/release/human worklists.
3. Execution readiness: clean for plan-only. `--execute` remains intentionally
   separate and should be run only after reviewing `fig_queue_run.py` output.

## Verification

```bash
uv run pytest -q tests/test_fig_queue.py tests/test_fig_queue_run.py tests/test_fig_run.py
# 57 passed

git diff --check
# clean

claude plugin validate .claude-plugin/plugin.json
# passed

claude plugin validate .
# passed

claude plugin validate ../../.claude-plugin/marketplace.json
# passed
```

No known Issue 82 blocker remains.
