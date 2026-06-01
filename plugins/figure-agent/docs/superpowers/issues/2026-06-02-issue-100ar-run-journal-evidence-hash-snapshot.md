# Issue 100AR - Run Journal Evidence Hash Snapshot

Status: implemented

Type: continuation UX, freshness hardening, run journal contract

## Problem

`fig_run_journal.py` marked interrupted run journals stale only when known
fixture evidence files had a newer mtime than the journal. That catches normal
edits, but it misses content changes whose mtime is preserved, restored, or
older than the journal.

This is a realistic continuation hazard because humans and tools can rewrite
briefing/spec/evidence files while preserving timestamps. In that case
`latest_journal_summary()` could report `available` even though the evidence
content changed.

## Decision

Add a non-authoritative evidence hash snapshot to newly recorded fig_run
journals:

```yaml
evidence_snapshot:
  schema: figure-agent.fig-run-evidence-snapshot.v1
  items:
    - path: examples/<name>/briefing.md
      sha256: sha256:<file-content-hash>
```

The snapshot is generated from the same shared evidence source set used by the
journal mtime fallback, including the critique input manifest paths. It records
only existing files.

`fig_run_journal.py` now combines:

- legacy mtime fallback for old journals without a snapshot;
- hash comparison for new journals with `evidence_snapshot`.

If a snapshotted file is missing or its current sha256 differs, the journal is
reported as `stale` and the changed path appears in `stale_against`.

The journal remains non-authoritative. The snapshot does not permit replaying
old commands; it only prevents stale continuation summaries.

## Scope

Implemented:

- shared evidence path and snapshot helper in `scripts/fig_run_evidence.py`;
- manifest writer support in `scripts/fig_run_records.py`;
- hash-based stale check in `scripts/fig_run_journal.py`;
- tests for preserved/older mtime content change and manifest snapshot writing.

Not implemented:

- run replay;
- automatic repair of stale journals;
- snapshot validation as a public CLI command;
- migration of historical journals.

## Tests

Covered by:

- `tests/test_fig_run_journal.py::test_latest_journal_summary_marks_hash_changed_evidence_as_stale`
- `tests/test_fig_run.py::test_main_records_non_authoritative_run_journal`
