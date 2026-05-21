# Issue 23E: Fixture Freshness UX Cleanup

**Date:** 2026-05-22 KST
**Status:** planned
**Type:** workflow usability hardening
**Parent:** `2026-05-22-issue-23-zoom-and-reference-calibrated-audit-roadmap.md`

## What to build

Improve status and driver messaging when plugin core behavior is correct but
fixture artifacts are stale. The user should be able to tell whether they are
blocked by plugin defects, stale render, stale critique, tracked golden export,
missing reference, missing adjudication, final artifact, or human publication
provenance.

This issue is about clarity, not changing state semantics.

## Current Problem

Real dogfood often produces states like:

- `render=STALE`
- `critique=STALE`
- `export=TRACKED_GOLDEN`
- `acceptance=NOT_ACCEPTED`
- `publication_gate=HUMAN_ACCEPTANCE_REQUIRED`

The driver returns safe next actions, but users can still confuse fixture
freshness work with plugin core failures.

## Acceptance Criteria

- [ ] `/fig_status` plain text clearly separates plugin state, fixture artifact
  freshness, and human publication/provenance blockers.
- [ ] `/fig_driver --dry-run` reason text names the first blocker and the next
  command without implying hidden execution.
- [ ] Tracked golden state explains whether `--force-golden` is required and
  why it is manual.
- [ ] Missing/stale critique states explain whether `/fig_critique` is required
  or optional.
- [ ] Publication gate messages clearly identify human-only decisions.
- [ ] Tests cover representative mixed states:
  stale render plus stale critique, tracked golden plus stale critique,
  release-ready false because of publication gate, and critique not required.

## Suggested Files

- `scripts/status.py`
- `scripts/status_next_policy.py`
- `scripts/fig_driver.py`
- `commands/fig_status.md`
- `commands/fig_drive.md`
- `tests/test_status.py`
- `tests/test_fig_driver.py`

## Verification

```bash
uv run pytest -q tests/test_status.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Non-Goals

- No change to readiness booleans.
- No automatic export or golden roll-forward.
- No mutation of fixture files.
- No hidden publication-provenance decision.
