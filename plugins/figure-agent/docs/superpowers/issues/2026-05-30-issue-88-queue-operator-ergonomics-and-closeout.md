# Issue 88 - Queue Operator Ergonomics And Closeout Follow-Through

Status: completed in commit `8f6df5c`

Depends on:

- Issue 82 - queue runner dogfood and operator playbook
- Issue 85 - blocked row operator handoff
- Issue 86 - queue table next step
- Issue 87 - closeout handoff rehearsal

Type: operator UX hardening, queue closeout evidence

## Problem

The queue runner stack was functionally safe, but a 10-pass review found
operator-facing rough edges that could still cause hesitation or misreads:

- generated driver commands did not quote fixture names;
- the human-readable queue table looked columnar while using whitespace inside
  `next_step` and `next_command`;
- single-fixture `/fig_run` closeout guidance was less explicit than the queue
  handoff;
- `/fig_queue_run` did not expose how many executable rows were left unattempted
  when `--max-fixtures` truncated a batch.

These were not release-boundary safety defects, but they mattered because the
queue is now the canonical multi-fixture operating surface.

## Implemented Behavior

- `fig_driver_commands.py` now shell-quotes fixture-derived command segments.
- `/fig_queue` table output is tab-separated.
- `closeout_required` queue handoff quotes fixture names in the generated
  `fig_closeout.py` command.
- `/fig_run` closeout stops now state the exact read-only closeout command,
  including the instruction to read JSON output even when closeout exits `1`.
- `/fig_queue_run` summary includes `unattempted_executable`.

## Queue Closeout Evidence

After the patch was pushed, the current queue was rehearsed again:

1. `/fig_queue --actor workflow_agent --command-plan --json` showed two
   executable verify-only loop rows (`fig3_trapping_concept`,
   `smoke_trap_demo`) and one blocked closeout row
   (`fig5_floating_clip_mechanism`).
2. `/fig_queue_run --actor workflow_agent --max-fixtures 2 --execute` executed
   the two loop rows and stopped both on `repeated_executable_action` after one
   successful loop record each.
3. `fig_closeout.py fig5_floating_clip_mechanism --json` reported export and
   loop-rerun blockers, with next action `/fig_export`.
4. `run_export.py fig5_floating_clip_mechanism` regenerated draft exports.
5. `fig_loop.py fig5_floating_clip_mechanism --goal "roadmap queue closeout"
   --json` recorded the required post-export loop.
6. `fig_closeout.py fig5_floating_clip_mechanism --json` then returned
   `closeout_complete: true`.

No source, accepted, golden, publication, or SVG-polish state was changed. The
generated export and loop journal artifacts are intentionally not committed.

## Verification

For commit `8f6df5c`:

- `uv run pytest -q tests/test_fig_queue.py tests/test_fig_queue_run.py tests/test_fig_run.py`
  - `62 passed`
- `uv run pytest -q`
  - `1468 passed, 1 skipped, 1 xfailed, 6 warnings`
- `uv run ruff check .`
  - passed
- `git diff --check`
  - clean
- `claude plugin validate .claude-plugin/plugin.json`
  - passed
- `claude plugin validate .`
  - passed
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - passed

## Remaining Boundaries

- `n3_trial_01_trap_depth` and `n3_trial_02_actuation_sequence` still require
  host `/fig_critique` refresh.
- `fig1_overview_v2` remains a human acceptance gate.
- `fig1_overview_v2_pair_001_vault` and `golden_trap_depth_picture` remain
  release-operator / tracked-golden gates.
- Verify-only loop rows for non-accepted fixtures remain visible, but rerunning
  them without a state change will correctly stop as repeated action.

No known Issue 88 blocker remains.
