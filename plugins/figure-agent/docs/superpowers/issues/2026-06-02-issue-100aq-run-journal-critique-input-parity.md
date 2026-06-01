# Issue 100AQ - Run Journal Critique Input Parity

Status: completed

Type: continuation UX, critique input freshness, manifest parity

## Problem

`fig_run_journal.py` had accumulated a hand-maintained evidence list for
staleness checks. Issues 100AN-100AP added more optional files, but the helper
still did not fully follow the same critique input set used by
`quality_manifest.py`.

In particular, reference images, panel reference images with `bbox_pdf_cm`,
`reference/reference_pack.md`, and the shared style lock can affect
`/fig_critique` freshness while a prior run journal still appeared
`available`.

## Decision

Reuse `quality_manifest.critique_manifest_paths()` inside the journal helper
and merge those paths with journal-only evidence such as critique/adjudication,
inspection traces, SVG polish final manifests, and build outputs.

The journal helper remains best-effort and non-authoritative. It does not
validate critique inputs or replay old commands; it only marks prior journals
stale so the operator returns to live `/fig_status` and `/fig_drive`.

## Tests

Covered by:

- `tests/test_fig_run_journal.py::test_latest_journal_summary_marks_reference_inputs_newer_as_stale`
