# Operator Completion Explanation Dogfood

Status: completed on main after Issues 100DP-100DS

## Purpose

The Issue 100 roadmap kept a post-hardening evidence item open: mode-scoped
`complete` wording existed in driver, queue, command-plan, and queue-run paths,
but a real dogfood pass still needed to verify that operators would see the
broader-mode follow-up instead of reading local completion as whole-figure
completion.

## Fixture Queue Used

Command:

```bash
uv run python3 scripts/fig_queue.py --mode authoring --goal 'operator completion dogfood'
```

Observed table shape:

- 8 fixture rows.
- 7 mode-scoped `complete` rows.
- 1 workflow-agent `run_compile` row.
- Complete rows included explicit wording:
  `authoring mode is complete: render is fresh. This is not a whole-figure completion claim; run /fig_drive <fixture> --mode review for critique and loop review.`
- Summary included:
  - `summary by_action=complete:7,run_compile:1`
  - `summary by_required_actor=none:7,workflow_agent:1`
  - `summary by_blocking_source=driver.action:1`

Interpretation: complete rows no longer appear as blocker-source noise. The
only blocker-source count belongs to the executable compile row.

## Command-Plan JSON

Command:

```bash
uv run python3 scripts/fig_queue.py --mode authoring --goal 'operator completion dogfood' --command-plan --json
```

Observed command-plan counts:

- `executable_count: 1`
- `blocked_count: 0`
- `complete_count: 7`

Sample complete rows preserved `operator_handoff.next_step` with the same
broader-mode review pointer and no executable command.

Interpretation: batch-planning JSON separates complete rows from true
host/human/release/closeout/unsafe blockers.

## Queue-Run JSON

Command:

```bash
uv run python3 scripts/fig_queue_run.py --mode authoring --goal 'operator completion dogfood' --json
```

Observed summary:

- `planned_executable: 1`
- `planned_blocked: 0`
- `planned_complete: 7`
- `attempted: 1`
- `blocked: 0`

Interpretation: the bounded batch runner inherits the same complete-vs-blocked
distinction and does not hide complete rows inside nested command-plan JSON.

## Review

1. **Completion wording**
   Complete rows state that authoring-mode completion is not whole-figure
   completion and point to `/fig_drive <fixture> --mode review`.

2. **Blocked accounting**
   `blocked_count`, `planned_blocked`, and `summary.blocked` remain zero for
   mode-scoped complete rows.

3. **Status context**
   `by_first_blocker` can still show broader status context such as
   `critique_stale`, but Issue 100DS documents this as status context rather
   than current-mode blocker evidence.

## Conclusion

The operator completion explanation evidence item is satisfied for the current
authoring queue path. Remaining post-100DS roadmap candidates are real-fixture
SVG polish promotion evidence and installed-cache refresh after user-owned
dirty figure work is resolved.
