# Issue 100AN - Run Journal Optional Evidence Staleness

Status: completed

Type: continuation UX, journal safety, optional evidence freshness

## Problem

`fig_run_journal.py` is the safe continuation helper after interrupted
`/fig_run` sessions. It marked a journal stale when core fixture files,
critique/adjudication files, or build render files changed after the journal,
but it missed newer optional evidence files such as
`external_vision_review.yaml`.

That could make a continuation summary look `available` even though a
second-opinion review was authored after the journal stopped.

## Decision

Extend the journal staleness sweep to include optional critique/evidence inputs
that materially affect review and routing:

- `coordinate_hints.yaml`
- `critique_reference_pack.yaml`
- `aesthetic_intent.yaml`
- `external_vision_review.yaml`
- detector/audit evidence JSON under `build/`

The helper remains non-authoritative and still emits only live `/fig_status` and
`/fig_drive` commands for continuation.

## Tests

Covered by:

- `tests/test_fig_run_journal.py::test_latest_journal_summary_marks_external_review_evidence_newer_as_stale`
