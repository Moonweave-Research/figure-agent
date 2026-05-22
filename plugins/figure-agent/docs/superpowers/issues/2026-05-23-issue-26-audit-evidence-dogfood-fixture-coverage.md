# Issue 26: Audit Evidence Dogfood Fixture Coverage

**Date:** 2026-05-23 KST
**Status:** planned
**Type:** plugin QA coverage

## Problem

Issue 25 surfaces audit evidence through `/fig_status`, `/fig_drive`, and
`/fig_loop`, but the current tracked real examples on `main` only exercise the
legacy path. They do not include committed current-schema critique evidence plus
matching audit input artifacts such as `build/visual_clash.json` and
`build/audit_crops/manifest.json`.

That means the test suite covers current audit-evidence states, but dogfood
runs on tracked examples cannot prove the operator UX for:

- `missing_input`
- `needs_action`
- `stale_or_mismatched`
- `passed`

## Goal

Create deterministic plugin-QA coverage for current audit-evidence states
without relying on a real manuscript figure or a host vision run.

## Direction

Prefer a test-only or fixture-only harness that does not mutate accepted,
golden, export, or real manuscript examples. It should be explicit that this is
for plugin QA, not publication evidence.

## Required Scenarios

1. **Missing input**
   - Current-schema `critique.md` exists.
   - `build/visual_clash.json` or `build/audit_crops/manifest.json` is absent.
   - `/fig_status`, `/fig_drive`, and `/fig_loop` surface `missing_input`.

2. **Needs action**
   - `visual_clash.json` has a candidate such as `VC050`.
   - `critique.md` omits or mistypes the matching
     `micro_defects[].visual_clash_ref`.
   - All three surfaces show the compact blocker id.

3. **Stale or mismatched**
   - Audit-crop manifest exists but a required crop hash/path no longer matches.
   - All three surfaces show the stale/mismatched crop id.

4. **Passed**
   - Visual-clash refs and crop audit logs fully account for required inputs.
   - All three surfaces show `passed` or omit noisy warnings as designed.

## Constraints

- Do not edit real manuscript figure source.
- Do not commit generated export/build artifacts from real fixtures.
- Do not weaken lint, status, driver, or loop gates.
- Keep the fixture/harness deterministic and cheap enough for CI.
- If stored under `examples/`, make the fixture visibly non-publication QA.
- If stored under tests, ensure it still exercises the command-facing code path
  enough to catch UX regressions.

## Acceptance Criteria

- Focused tests cover `/fig_status`, `/fig_drive`, and `/fig_loop` propagation
  for at least `missing_input`, `needs_action`, and `passed`.
- One documented dogfood command sequence demonstrates the QA fixture.
- No changes to real manuscript examples.
- `uv run pytest -q` passes.
- `uv run ruff check .` passes.
- `git diff --check` is clean.

## Open Design Question

The main design choice is whether to keep this as test-only generated fixtures
or add a small tracked `examples/_audit_evidence_smoke` fixture. Test-only
fixtures avoid committing pseudo-build artifacts; a tracked smoke example makes
manual dogfood easier. The implementation should choose the least misleading
option.
