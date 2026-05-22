# Issue 23E: Fixture Freshness UX Cleanup

**Date:** 2026-05-22 KST
**Status:** completed in commit `7898ee8`
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

- [x] `/fig_status` plain text clearly separates plugin state, fixture artifact
  freshness, and human publication/provenance blockers.
- [x] `/fig_driver --dry-run` reason text names the first blocker and the next
  command without implying hidden execution.
- [x] Tracked golden state explains whether `--force-golden` is required and
  why it is manual.
- [x] Missing/stale critique states explain whether `/fig_critique` is required
  or optional.
- [x] Publication gate messages clearly identify human-only decisions.
- [x] Tests cover representative mixed states:
  stale render plus stale critique, tracked golden plus stale critique,
  release-ready false because of publication gate, and critique not required.

## Implementation Contract

Add a read-only explanation layer derived from the existing status vector. This
must not change stage inference, readiness booleans, stop boundaries, or driver
action ordering.

The shared explanation should make three buckets explicit:

1. `plugin_state` — whether the plugin can continue deterministically or is
   waiting on host/human/manual decisions.
2. `fixture_freshness` — stale or missing render, critique, export, tracked
   golden, final artifact, or reference inputs.
3. `human_blockers` — accepted/golden roll-forward, publication provenance, or
   human review gates that the plugin must not mutate.

Expose the explanation as structured data from `status.infer_stage()` so both
`/fig_status` and `/fig_driver --dry-run` can use the same source of truth. The
minimal public shape is:

```yaml
status_explanation:
  summary: "<one-line human-readable state>"
  first_blocker:
    code: <stable_code>
    category: plugin_state | fixture_freshness | human_blocker
    message: "<what is blocking>"
    next_command: "<slash or shell command, if deterministic>"
    manual: true | false
  buckets:
    plugin_state:
      - code: <stable_code>
        message: "<plain explanation>"
    fixture_freshness: []
    human_blockers: []
```

Stable codes should be intentionally small and tied to current contracts, for
example: `render_stale`, `critique_stale`, `critique_missing`,
`critique_reference_missing`, `export_stale`, `export_tracked_golden`,
`publication_gate_required`, `not_accepted`, and `critique_not_required`.

`/fig_status` should print this as a short "Explanation" block after `States`.
`/fig_driver --dry-run` should include the compact explanation object in JSON
and, when possible, include the first blocker code in `reason` without implying
that the driver will execute the command.

## Design Checks

- The explanation is derived from existing fields only; no filesystem scan is
  added outside `infer_stage()`.
- No existing key is removed or renamed.
- Existing `next` remains the canonical human command hint.
- `critique_not_required` is an explicit non-blocking explanation, not a prompt
  to fabricate a critique.
- Tracked golden remains manual: `--force-golden` may be named, but no driver
  action executes it or places it in a safe command unless an existing contract
  already allows that.

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
