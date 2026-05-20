# Publication Gate UX Design

**Date:** 2026-05-20 KST
**Status:** implemented and verified
**Related:** Issue 14A/14B/14C/14D, `2026-05-19-fig1-publication-provenance-gate.md`

## Problem

The accepted/publication gate currently blocks unsafe promotion, but its failure
surface is too flat. `check_golden_artifacts.py` returns strings, `/fig_status`
summarizes acceptance as a single state, and `/fig_driver --mode release`
collapses distinct failures into a broad manual release blocker.

That protects against unsafe automation, but it makes real use harder because
technical work and human-only decisions are mixed together.

## Goal

Separate publication-gate failures into typed records, provide a safe
`QUALITY_AUDIT.md` scaffold, and surface the resulting publication gate in
status/driver outputs. The slice must improve handoff clarity without
accepting, exporting, or marking any figure submission-safe.

## Non-Goals

- Do not set `accepted: true`.
- Do not write `submission-safe: true` by default.
- Do not run `--force-golden`.
- Do not change `/fig_loop` behavior.
- Do not make `release_ready` depend on target-journal or provenance judgment;
  expose that as a separate publication gate surface.
- Do not decide target-journal policy automatically.

## Architecture

Add a small `scripts/publication_gate.py` module. It owns typed failure records,
publication-gate state, and the publication-audit scaffold text.
`check_golden_artifacts.py` keeps its existing string-returning public API, but
delegates publication-compliance classification to the new module and converts
records back to messages.

`/fig_status` adds `publication_gate_state` and
`publication_gate_failures`. `/fig_driver --mode release` uses those fields to
explain publication/provenance blockers before reporting a generic release
blocker, while preserving the existing `accepted_or_final_ready_required`
boundary.

## Failure Model

Each publication-gate finding is represented as:

```python
PublicationGateFailure(
    code="missing_submission_safe",
    category="publication_provenance",
    actor="human",
    message="QUALITY_AUDIT.md does not declare submission-safe: true",
    required_action="Human reviewer must decide submission safety and write an explicit value.",
)
```

Allowed categories:

- `technical_rebaseline`
- `artifact_contract`
- `quality_audit_stale`
- `publication_provenance`
- `human_acceptance`
- `manual_promotion`

Allowed actors:

- `agent`
- `human`
- `manual_command`

Publication gate states:

- `NOT_APPLICABLE`: `accepted` is not declared in `spec.yaml`.
- `PASS`: `accepted: true` and no publication-compliance failure records.
- `HUMAN_ACCEPTANCE_REQUIRED`: `accepted: false`; a human must explicitly
  decide acceptance/provenance before release.
- `PROVENANCE_REQUIRED`: `accepted: true`, but `QUALITY_AUDIT.md` is missing or
  incomplete.

## Publication Compliance Rules

The first structured rules mirror existing behavior:

- missing `QUALITY_AUDIT.md` -> `quality_audit_stale`, actor `agent`
- missing "Provenance and Publication Compliance" section ->
  `publication_provenance`, actor `human`
- missing `submission-safe: true` -> `publication_provenance`, actor `human`
- missing `disclosure-needed` when disclosure is required ->
  `publication_provenance`, actor `human`

`/fig_status` uses the same disclosure-required rule as the accepted gate:
declared `final_artifact.kind: polished_svg` requires the
`disclosure-needed` field because the release candidate includes final
human-edited SVG provenance.

The string messages must remain exactly compatible with current tests.

## QUALITY_AUDIT Scaffold

Add a helper that writes a conservative audit scaffold only when the file does
not exist, unless `force=True`.

Required properties:

- includes "Provenance and Publication Compliance";
- includes target venue, final artifact scope, AI/provenance fields,
  disclosure-needed, disclosure draft, human reviewer, and visual acceptance;
- uses `submission-safe: false` by default;
- includes `disclosure-needed: unresolved` by default;
- never writes `accepted: true`;
- never mutates source, export, golden, or final-artifact state.

## Tests

- structured records classify missing audit, missing section,
  missing submission-safe, and missing disclosure-needed;
- legacy `publication_compliance_failures()` returns the same strings;
- scaffold content contains required fields and conservative defaults;
- scaffold refuses to overwrite unless forced;
- `check_example(require_accepted=True)` still reports publication failures.
- `/fig_status` exposes `publication_gate_state` and typed
  `publication_gate_failures`.
- `/fig_driver --mode release` includes the first publication-gate blocker in
  its `reason` and compact status.

## Deferred

Later slices may add target-journal-specific policy checks and fig1 dogfood
reports.
