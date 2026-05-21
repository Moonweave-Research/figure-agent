# Status Next-Hint Policy Extraction Plan

**Date:** 2026-05-21 KST
**Parent issue:** `2026-05-21-issue-17-driver-status-state-machine-refactor.md`
**Slice:** Issue 17C

## Goal

Make `/fig_status` easier to review by moving command-facing `next` hint
selection out of `scripts/status.py` and into a pure policy helper.

This is behavior-preserving. The public `/fig_status` JSON/text contract must
not change.

## Current Risk

`status.py` computes filesystem/spec state and also owns the remediation
priority ladder for stage 1-4. That makes the highest-risk command advice hard
to test without assembling full fixture directories.

The most fragile precedence is stage 4:

1. malformed spec/style profile;
2. missing briefing;
3. missing declared reference inputs;
4. stale exports plus missing/stale critique;
5. tracked-golden roll-forward;
6. source/build/export freshness;
7. partial export;
8. critique-required;
9. final-artifact repair;
10. accepted gate;
11. done.

## Implementation

- Add `scripts/status_next_policy.py`.
- Expose `select_next_hint(...)` as a pure function that accepts:
  - stage;
  - fixture name;
  - notes;
  - critique state;
  - export substate;
  - source/export freshness booleans;
  - render state;
  - partial-export flag;
  - final-artifact state;
  - accepted flag.
- Keep `status.py` responsible for computing state only.
- Keep `critique_needs_action()` in the policy module so workflow gating and
  next-hint selection share the same critique-action definition.

## TDD Coverage

Add `tests/test_status_next_policy.py` before implementation.

Focused precedence cases:

- spec parse errors beat export and accepted hints;
- missing briefing beats critique/export/final-artifact hints;
- missing reference input beats stale export;
- tracked-golden plus fresh render and stale critique skips compile;
- stale source plus stale render and stale critique includes compile;
- final-artifact blocked beats not-accepted after core outputs are ready;
- not-accepted beats done when final artifact is ready;
- stage 3 stale critique requires critique before export;
- stage 2 missing briefing avoids compile;
- stage 1 spec parse error beats authoring.

## Verification

- `uv run pytest -q tests/test_status_next_policy.py tests/test_status.py`
- `uv run pytest -q -m "not render"`
- `uv run pytest -q`
- `uv run ruff check .`
- `git diff --check`

## Non-Goals

- No wording changes to current `next` hints.
- No new stage, note, gate, export, critique, or final-artifact behavior.
- No fixture migration.
- No public CLI/JSON schema change.
