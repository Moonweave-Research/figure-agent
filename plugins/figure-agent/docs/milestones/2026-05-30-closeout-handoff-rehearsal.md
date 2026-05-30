# Closeout Handoff Rehearsal - Issue 87

Status: completed

Issue:

- `docs/superpowers/issues/2026-05-30-issue-87-closeout-handoff-rehearsal.md`

## Purpose

Validate the real operator path from a `closeout_required` queue row into
`fig_closeout.py --json`.

## Queue Evidence

Command:

```bash
uv run python3 scripts/fig_queue.py --mode review \
  --goal "Issue 87 closeout handoff rehearsal" \
  --actor workflow_agent
```

The current closeout-blocked row:

| Fixture | Action | Stop boundary | Next command |
|---|---|---|---|
| `fig5_floating_clip_mechanism` | `run_export` | `closeout_required` | `uv run python3 scripts/fig_closeout.py fig5_floating_clip_mechanism --json` |

## Closeout Evidence

Command:

```bash
uv run python3 scripts/fig_closeout.py fig5_floating_clip_mechanism --json
```

Result:

- exit code: `1`
- schema: `figure-agent.closeout.v1`
- `closeout_complete: false`
- `blocking_step_ids: ["export", "loop_rerun"]`
- `next_action: /fig_export fig5_floating_clip_mechanism`
- `next_action_summary.blocking_source: closeout:export`
- export step: `needs_action`, `export_state is MISSING`
- loop rerun step: `blocked`, blocked by `export`

This is expected behavior. `/fig_closeout` exits `1` when closeout is
incomplete so automation does not overclaim completion.

## Handoff Adjustment

The queue closeout handoff now includes:

```yaml
closeout_checks:
  - read JSON output even when exit code is 1
  - follow closeout.next_action
  - rerun /fig_queue after resolving the blocked row
```

## Verification

```bash
uv run pytest -q tests/test_fig_queue.py::test_build_queue_can_include_command_plan
# 1 passed

uv run python3 scripts/fig_queue.py --mode review --goal "Issue 87 closeout handoff rehearsal" --actor workflow_agent --command-plan --json
# closeout handoff includes exit-code guidance

uv run pytest -q tests/test_fig_queue.py tests/test_fig_queue_run.py tests/test_fig_run.py
# 59 passed

uv run pytest -q
# 1465 passed, 1 skipped, 1 xfailed, 6 warnings

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

1. Scope: clean. No export/source/accepted/golden/publication/SVG files were
   changed.
2. Safety: clean. The queue still recommends read-only closeout inspection
   before any export.
3. Usability: clean. Operators now know that exit `1` can be the expected
   incomplete-closeout signal.

No known Issue 87 blocker remains.
