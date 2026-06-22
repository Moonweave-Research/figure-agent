# Single Next Action UX - Issue 58

Status: implemented

## Summary

Issue 58 adds a shared compact `next_action_summary` object to the operator
surfaces that already compute next-step evidence:

- `/fig_status`
- `/fig_drive --dry-run`
- `/fig_loop --json`
- `/fig_closeout --json`

The slice is intentionally conservative. It does not create a new state
machine and does not weaken any gate. `/fig_drive --dry-run` remains the
canonical mode-aware action selector.

## Contract

Every summary has schema `figure-agent.next-action-summary.v1` and includes:

- `action`
- `reason`
- `blocking_source`
- `safe_command`
- `requires_human`
- `allowed_scope`
- `forbidden_scope`
- `evidence_refs`

The object is a UX compression layer. Detailed fields such as
`status_explanation`, `audit_evidence`, `loop_checkpoint`, `closeout.steps[]`,
and raw status vectors remain the audit/debugging source.

## Scope Containment

No figure source, generated export, accepted state, golden artifact, build
artifact, or `.scratch` record is changed by this implementation.

No new action vocabulary was needed. The summary reuses the existing driver
actions:

- `create_or_fix_source`
- `run_compile`
- `run_critique`
- `run_adjudicate`
- `run_fig_loop`
- `run_export`
- `patch_handoff_stop`
- `human_gate_stop`
- `polish_handoff_stop`
- `release_blocked`
- `complete`

## Review

### Contract/Schema Correctness

`tests/test_next_action_summary.py` verifies the shared shape for status,
driver, loop, and closeout cases. Integration tests verify the object is
included in existing public outputs.

### Backward Compatibility

All detailed fields remain present. Existing consumers that ignore unknown
fields keep working because the addition is top-level and additive.

### Integration Readiness

Issue 59 can consume `next_action_summary` for SVG polish promotion UX without
reimplementing driver action selection.

## Verification

```bash
uv run pytest -q tests/test_next_action_summary.py tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop_records.py tests/test_fig_closeout.py tests/test_real_fixture_audit_adoption.py
uv run ruff check scripts/next_action_summary.py scripts/status.py scripts/fig_driver.py scripts/fig_loop.py scripts/fig_loop_records.py scripts/fig_closeout.py tests/test_next_action_summary.py tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop_records.py tests/test_fig_closeout.py
git diff --check
```

All targeted commands passed during implementation.
