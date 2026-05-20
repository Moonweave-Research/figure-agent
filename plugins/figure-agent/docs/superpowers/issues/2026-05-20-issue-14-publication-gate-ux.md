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

## Out of Scope

- Setting `accepted: true`.
- Setting `submission-safe: true`.
- Running `--force-golden`.
- `/fig_status` or `/fig_driver` surfacing.
- Target-journal policy automation.

## Verification

```bash
uv run pytest -q tests/test_publication_gate.py tests/test_golden_artifact_checks.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```
