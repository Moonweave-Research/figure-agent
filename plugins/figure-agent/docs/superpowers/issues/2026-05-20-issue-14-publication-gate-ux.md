# Issue 14: Publication Gate UX

**Date:** 2026-05-20 KST
**Status:** implemented and verified
**Spec:** `../specs/2026-05-20-publication-gate-ux-design.md`
**Type:** release/provenance UX hardening

## Problem

The current publication gate blocks unsafe accepted-mode promotion, but the
failure surface is not structured enough for agents or humans to know what kind
of work remains.

## Slice 14A/14B Scope

- Add typed publication-gate failure records.
- Preserve existing string-returning gate behavior.
- Add a conservative `QUALITY_AUDIT.md` scaffold helper.
- Do not change status, driver, loop, export, accepted, or golden behavior.

## Slice 14C/14D Scope

- Add `publication_gate_state` and `publication_gate_failures` to
  `/fig_status` output.
- Keep `release_ready` backward-compatible; publication/provenance judgment is
  exposed as a separate gate state.
- Make `/fig_driver --mode release` explain the first publication-gate blocker
  instead of only reporting a generic release blocker.
- Preserve the existing `accepted_or_final_ready_required` stop boundary.
- Do not let the driver set `accepted`, write `QUALITY_AUDIT.md`, force golden,
  or mutate provenance.

## Acceptance Criteria

- [x] Publication compliance failures can be returned as typed records.
- [x] Typed records include `code`, `category`, `actor`, `message`, and
  `required_action`.
- [x] Existing `publication_compliance_failures()` messages remain compatible.
- [x] `QUALITY_AUDIT.md` scaffold includes provenance and publication fields.
- [x] Scaffold defaults are conservative: `submission-safe: false` and
  `disclosure-needed: unresolved`.
- [x] Scaffold refuses to overwrite unless forced.
- [x] Tests cover structured classification, backward-compatible messages,
  scaffold safety, and accepted-gate integration.
- [x] `/fig_status` exposes `publication_gate_state` for accepted, not
  accepted, and undeclared fixtures.
- [x] `/fig_status` exposes typed publication-gate failure records without
  requiring callers to parse strings.
- [x] `/fig_driver --mode release` includes publication-gate state and the first
  blocker code/action in its release-blocked reason.
- [x] `/fig_driver --mode release` remains dry-run and non-mutating.

## Out of Scope

- Setting `accepted: true`.
- Setting `submission-safe: true`.
- Running `--force-golden`.
- Target-journal policy automation.

## Verification

```bash
uv run pytest -q tests/test_publication_gate.py tests/test_golden_artifact_checks.py tests/test_status.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```
