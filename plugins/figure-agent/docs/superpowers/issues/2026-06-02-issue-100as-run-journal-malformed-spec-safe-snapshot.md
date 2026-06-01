# Issue 100AS - Run Journal Malformed Spec Safe Snapshot

Status: implemented

Type: continuation UX, malformed-input hardening, run journal contract

## Problem

Issue 100AR added hash snapshots to recorded fig_run journals. During follow-up
review, `evidence_snapshot()` still reused critique input path logic directly.
That logic assumes `spec.yaml.panels[]` entries are mappings. If a malformed
spec contains a scalar panel entry, snapshot generation raises an
`AttributeError`.

That is too brittle for a non-authoritative journal. `/fig_run --record` should
still be able to write a safety journal even when optional critique-manifest
expansion cannot interpret a malformed spec.

## Decision

Keep the core fixture evidence paths (`<name>.tex`, `briefing.md`,
`spec.yaml`, detector reports, critique/adjudication, build outputs, SVG polish
sidecars) independent of optional critique-manifest expansion.

If best-effort critique input expansion raises a shape/type error from malformed
spec content, skip only that optional expansion and still write a snapshot for
the known files.

The journal remains non-authoritative and still sends operators back to live
`/fig_status` and `/fig_drive`.

## Tests

Covered by:

- `tests/test_fig_run.py::test_main_records_run_journal_when_spec_shape_is_malformed`
