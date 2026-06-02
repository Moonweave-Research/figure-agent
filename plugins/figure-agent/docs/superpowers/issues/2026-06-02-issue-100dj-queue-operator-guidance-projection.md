# Issue 100DJ - Queue Operator Guidance Projection

Status: implemented in this slice

Type: operator UX, queue contract, mode-scoped completion

## Problem

Issue 100CO made `/fig_drive` complete states mode-scoped. For example,
`/fig_drive --mode authoring` can correctly return `action: complete` while
also saying that only authoring is complete and the next broader review should
run through `--mode review`.

`/fig_queue` still dropped that `operator_guidance` block when projecting
driver summaries into compact rows. In table output and command-plan handoff
output, complete rows therefore looked like generic queue completion instead
of carrying the driver's mode-scoped follow-up. This repeated the user-facing
confusion that Issue 100CO was meant to reduce: "why does the plugin say it is
complete?"

## Scope

- Preserve `/fig_drive.operator_guidance` in queue rows when present.
- Use `operator_guidance.next_step` in the table for `action: complete` rows.
- Use `operator_guidance.next_step` in `command_plan.blocked[].operator_handoff`
  for `action: complete` rows.
- Keep blocked-row queue handoff policy unchanged.
- Update `/fig_queue` documentation so the row contract and table behavior name
  the mode-scoped completion guidance.

## Non-goals

- Do not change the `/fig_drive` action vocabulary.
- Do not reinterpret blocked host/human/release/SVG handoff rows.
- Do not make complete rows executable.
- Do not mutate source, critique, export, accepted, golden, publication, or SVG
  polish state.

## Verification

- TDD red:
  - `uv run pytest -q tests/test_fig_queue.py::test_queue_rows_preserve_driver_operator_guidance_for_complete_modes tests/test_fig_queue.py::test_queue_table_uses_operator_guidance_for_complete_rows`
  failed because queue rows did not contain `operator_guidance`, and table
  output did not contain the driver's mode-scoped next step.
  - `uv run pytest -q tests/test_fig_queue.py::test_queue_command_plan_uses_operator_guidance_for_complete_rows`
  failed because command-plan handoff still used the generic blocked-row next
  step for complete rows.
- Green:
  - The same targeted tests passed after row projection and table next-step
    handling were added.

## Review Notes

1. **Contract safety** - `operator_guidance` is additive in queue rows. Existing
   row fields and summary counts are unchanged.
2. **Blocked-row containment** - Table and command-plan output use driver
   guidance only for `action: complete`; blocked host/human/release/SVG rows
   still use the queue operator-handoff policy.
3. **Workflow clarity** - Multi-fixture queue output now preserves the same
   mode-local completion boundary as single-fixture `/fig_drive`, so authoring
   completion cannot silently masquerade as whole-figure release readiness.
