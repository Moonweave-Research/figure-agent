# Issue 70B: Mechanical Boundary Handoff Packet

Status: implemented

Depends on: Issue 70A guided autonomy readiness matrix

Type: AFK

## Problem

When `/fig_run` stops, it embeds the driver summary, but the stop can still be
hard to operationalize. A downstream agent needs to know what evidence to read
and what action is forbidden without accidentally treating helper text as a new
route authority.

## What To Build

Add an additive handoff object to `/fig_run` result payloads for non-complete
stops. The object must be a mechanical projection of existing `action`,
`stop_boundary`, `safe_command`, `next_action_summary`, `loop_checkpoint`, and
`closeout` fields. It must not introduce an independent router.

Patch/source-mutation boundaries are excluded from this issue until Issue 70C
hardens the patch executor currentness and pending-closeout contract.

Suggested contract:

```yaml
boundary_handoff:
  schema: figure-agent.boundary-handoff.v1
  action: <existing driver action>
  stop_boundary: <existing driver stop_boundary | null>
  required_actor: host_llm | human | svg_editor | release_operator | workflow_agent
  blocking_reason: "<copied or compacted existing reason>"
  evidence_refs:
    - "<existing status/driver/loop/closeout evidence ref>"
  allowed_scope:
    - "<copied from next_action_summary>"
  forbidden_scope:
    - "<copied from next_action_summary>"
  closeout_checks:
    - "<checks required after the actor acts>"
  continuation_guidance:
    rerun_live_status_first: true
    rerun_live_driver_first: true
    note: "<plain-language continuation guidance, not an executable resume>"
```

70B must not emit an executable resume command. Concrete resume flags or replay
commands belong to Issue 70E only after live currentness rules are proven.

## Scope

In scope:

- Handoff object in `scripts/fig_run.py` or a focused helper module.
- Tests for host critique, existing adjudication repair, human gate,
  force-golden/tracked-golden, command failure, max-step stops, and a successful
  mechanical boundary.
- A regression test for a patch-handoff/source-mutation stop proving 70B emits
  either no handoff packet or a deferred marker with no patch scope guidance.
- Command docs explaining that handoff is explanatory.

Out of scope:

- Running the handoff actor.
- Generating host critique.
- Repairing adjudication.
- Editing source or SVG.
- Surfacing patch/source-mutation handoff details before Issue 70C.
- Forcing accepted/golden/release transitions.
- Generic "resume with fig_run" suggestions for manual boundaries.

## Acceptance

- Every non-complete stop includes a handoff packet or a documented reason why
  no handoff can be produced.
- The packet mirrors existing `action`/`stop_boundary`; it does not invent a
  second route.
- No boundary includes an automatic resume command.
- Patch/source-mutation boundaries are omitted or explicitly marked deferred
  until Issue 70C is complete.
- Tests prove the packet is additive and does not change existing runner fields.

## Verification

- `uv run pytest -q tests/test_fig_run.py tests/test_fig_driver.py tests/test_status.py`
- `uv run ruff check scripts/fig_run.py tests/test_fig_run.py`
- `git diff --check`

## Review Questions

1. Can the packet drift from the canonical driver?
2. Does any field look like permission to bypass a stop boundary?
3. Are manual boundaries clearly manual?
4. Can a new session understand the stop without reading issue history?
