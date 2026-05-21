# Issue 15A: Driver-Closeout Unification

**Date:** 2026-05-21 KST
**Status:** proposed
**Parent:** Issue 15
**Spec:** `../specs/2026-05-21-plugin-loop-automation-audit-design.md`

## Problem

`/fig_drive`, `/fig_loop`, and `/fig_closeout` are individually useful, but
real users can still run them in the wrong order. After a patch handoff, the
driver can recommend another loop checkpoint while compile, critique,
adjudication, export, or loop-rerun closeout evidence is incomplete.

## What to Build

Extend `/fig_drive --mode review` so it can read the read-only closeout report
and recommend the closeout boundary when closeout is incomplete. The driver
must stay dry-run and non-mutating.

## Acceptance Criteria

- [ ] Add a compact closeout summary to driver output when relevant.
- [ ] When closeout is incomplete, return a single canonical action and reason
  that points to `/fig_closeout <name>` or the closeout report's next action.
- [ ] Do not automatically run compile, critique, adjudication, export, loop,
  or golden roll-forward.
- [ ] Preserve `may_execute: false`.
- [ ] Preserve `figure-agent.driver.v1` backward compatibility by adding only
  optional fields.
- [ ] Tests cover incomplete compile, critique, adjudication, export, and
  loop-rerun closeout states.

## Verification

```bash
uv run pytest -q tests/test_fig_driver.py tests/test_fig_closeout.py tests/test_status.py
uv run pytest -q
uv run ruff check scripts/fig_driver.py scripts/fig_closeout.py tests/test_fig_driver.py tests/test_fig_closeout.py
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```
