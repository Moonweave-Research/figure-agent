# Issue 66: Safe Workflow Runner

Status: completed

Completed in: Safe Workflow Runner implementation branch.

## Problem

`/fig_drive --dry-run` now chooses the correct next action, but the operator
still has to copy each safe command into the shell. That is intentional for
host-vision critique, human gates, patch handoff, SVG polish, accepted state,
and golden roll-forward. It is unnecessarily noisy for deterministic shell
steps such as a stale render that only needs `/fig_compile`.

The result is operational friction: agents repeatedly ask the user to approve
obvious compile/status transitions even though the existing driver has already
identified the next safe command.

## Decision

Add a conservative runner on top of the existing driver:

- `scripts/fig_run.py` reads the same driver JSON contract as `/fig_drive`.
- Default mode is plan-only and never executes.
- `--execute` may run only a narrow allowlist of deterministic shell actions.
- Issue 66A allowlist is intentionally limited to `run_compile`.
- The runner re-queries the driver after each executed step.
- It stops at host, human, patch, polish, export, adjudication, loop, release,
  accepted, and golden boundaries.
- It emits `figure-agent.run.v1` JSON evidence so an outer agent can see what
  was executed, what was skipped, and why the loop stopped.

This does not weaken `/fig_drive`: the driver remains the canonical selector,
and the runner is only a bounded executor for actions the driver already chose.

## Scope

Implement:

- `commands/fig_run.md`
- `scripts/fig_run.py`
- `tests/test_fig_run.py`
- Minimal SKILL.md workflow note, if needed, so agents know when to use it.

Do not implement:

- host `/fig_critique` automation
- hidden source patching
- automatic adjudication mutation
- automatic `/fig_loop` execution
- automatic export
- accepted/golden mutation
- SVG polish editing
- git staging, commit, push, branch switching, or cleanup

## Contract

`fig_run.py <name> --mode <mode> --goal "<goal>"` emits:

```yaml
schema: figure-agent.run.v1
fixture: <name>
mode: authoring | review | release | polish
goal: <goal>
execute: false | true
max_steps: <int>
executable_actions:
  - run_compile
steps:
  - index: 1
    action: run_compile
    safe_command: bash scripts/compile.sh examples/<name>/<name>.tex
    executed: false | true
    returncode: <int | null>
    stop_reason: plan_only | command_failed | host_boundary | not_executable_action | complete | max_steps_exceeded | null
final_action: <driver action>
final_stop_boundary: <driver stop_boundary | null>
final_stop_reason: <runner stop reason>
executed_count: <int>
```

The embedded driver summary may be included per step for traceability. Consumers
must ignore unknown fields.

## Safety Rules

- A command is executable only if the driver action is allowlisted and the
  command is a shell command, not a slash command.
- Issue 66A allowlist: `run_compile` only.
- `run_critique` always stops because it requires host vision.
- `run_adjudicate`, `run_fig_loop`, and `run_export` stop in Issue 66A even
  when they are shell commands, because they mutate review/export state and need
  separate policy hardening before automation.
- Any non-zero return code stops the runner immediately.
- `--max-steps` prevents accidental loops if driver state does not advance.

## Tests

- Plan-only mode reports the executable compile step without executing it.
- Execute mode runs `run_compile`, re-queries the driver, and stops at
  `run_critique` without trying to run the slash command.
- Execute mode stops immediately at host-vision critique boundaries.
- Execute mode stops at non-allowlisted shell actions such as adjudication.
- Non-zero compile return code stops with `command_failed`.
- Repeated executable actions stop at `max_steps_exceeded`.
- CLI emits stable JSON and requires `--execute` to mutate.

## Verification

- `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py` — 76 passed
- `uv run ruff check scripts/fig_run.py tests/test_fig_run.py` — passed
- `git diff --check` — passed
- `uv run pytest -q` — 1385 passed, 1 skipped, 1 xfailed
- `claude plugin validate .claude-plugin/plugin.json` — passed
- `claude plugin validate .` — passed
- `claude plugin validate ../../.claude-plugin/marketplace.json` — passed

## Review Notes

1. Contract/schema/freshness review: clean after documenting that successful
   intermediate executed steps may have `stop_reason: null`.
2. Scope containment review: clean. Issue 66A executes only `run_compile` and
   stops on host critique, adjudication, loop, export, patch, polish, human,
   accepted, and golden boundaries.
3. Test/integration review: clean after adding CLI `--execute` and invalid
   `--max-steps` coverage.
