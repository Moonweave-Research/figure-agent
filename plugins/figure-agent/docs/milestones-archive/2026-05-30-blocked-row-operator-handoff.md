# Blocked Row Operator Handoff - Issue 85

Status: completed

Issue:

- `docs/superpowers/issues/2026-05-30-issue-85-blocked-row-operator-handoff.md`

## Purpose

Make blocked queue rows actionable without making them executable.

The queue had already separated deterministic automation from host, human,
release, SVG, and closeout boundaries. This slice adds a small
`operator_handoff` packet to `command_plan.blocked[]` so the operator can see
the next action directly in the queue JSON.

## Contract

Each blocked row now includes:

| Field | Meaning |
|---|---|
| `schema` | `figure-agent.queue-operator-handoff.v1` |
| `fixture` | target fixture |
| `required_actor` | actor that must handle the row |
| `next_step` | one-line operator action |
| `command` | optional command/slash command for the operator |
| `reason` | blocked reason copied from command-plan policy |
| `allowed_scope` | what the actor may inspect or edit |
| `forbidden_scope` | what must not be mutated |
| `closeout_checks` | checks after the actor acts |

## Dogfood

Workflow-agent blocked row:

```bash
uv run python3 scripts/fig_queue.py --mode review \
  --goal "Issue 85 blocked row handoff dogfood" \
  --actor workflow_agent --command-plan --json
```

Observed blocked handoff:

- fixture: `fig5_floating_clip_mechanism`
- action: `run_export`
- reason: `stop_boundary:closeout_required`
- next step: read-only closeout inspection
- command:
  `uv run python3 scripts/fig_closeout.py fig5_floating_clip_mechanism --json`

Host-LLM blocked rows:

```bash
uv run python3 scripts/fig_queue.py --mode review \
  --goal "Issue 85 blocked row handoff dogfood" \
  --actor host_llm --command-plan --json
```

Observed blocked handoffs:

- `n3_trial_01_trap_depth` -> `/fig_critique n3_trial_01_trap_depth`
- `n3_trial_02_actuation_sequence` -> `/fig_critique n3_trial_02_actuation_sequence`

Both host handoffs include critique lint, adjudication sync/scaffold, and queue
rerun checks.

## Verification

```bash
uv run pytest -q tests/test_fig_queue.py::test_build_queue_can_include_command_plan tests/test_fig_queue.py::test_command_plan_blocked_handoff_covers_human_and_release_rows
# 2 passed

uv run pytest -q tests/test_fig_queue.py tests/test_fig_queue_run.py tests/test_fig_run.py
# 58 passed

uv run ruff check scripts/fig_queue.py tests/test_fig_queue.py
# All checks passed

uv run python3 scripts/fig_queue_run.py --mode review --goal "Issue 85 blocked row handoff dogfood" --actor workflow_agent --max-fixtures 1
# queue.command_plan.blocked[0].operator_handoff present for fig5_floating_clip_mechanism

uv run pytest -q
# 1464 passed, 1 skipped, 1 xfailed, 6 warnings

uv run ruff check .
# All checks passed

git diff --check
# clean

claude plugin validate .claude-plugin/plugin.json
# passed

claude plugin validate .
# passed

claude plugin validate ../../.claude-plugin/marketplace.json
# passed
```

## Review Notes

1. Scope: clean. `/fig_queue` remains read-only and `/fig_queue_run` still
   attempts only executable rows.
2. Safety: clean. Handoff commands are visible guidance, not queued execution.
3. Usability: clean. Host, human, release, SVG, closeout, and fallback cases
   now have explicit next steps.

No known Issue 85 blocker remains.
