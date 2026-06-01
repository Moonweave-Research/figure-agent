# Issue 100AP - Run Journal Declared Context Pack Staleness

Status: completed

Type: continuation UX, paper-wide context freshness, journal playbook freshness

## Problem

`fig_run_journal.py` is a non-authoritative continuation helper, but its stale
fixture-evidence sweep did not include spec-declared context packs outside the
fixture directory:

- `examples/_paper_aesthetic_contexts/<id>.yaml`
- `examples/_journal_art_direction_playbooks/<id>.yaml`

Those files participate in critique input hashing when declared by `spec.yaml`.
If either pack changed after an interrupted `/fig_run`, the previous journal
could still look `available` even though paper-wide or journal-specific art
direction had changed.

## Decision

Read `spec.yaml` best-effort and add declared paper-wide aesthetic context and
journal art-direction playbook paths to the journal staleness sweep.

Malformed specs or invalid context ids do not crash the journal helper. They
are ignored here because the helper is context-only; live `/fig_status`,
`/fig_drive`, and `/fig_critique` remain the authoritative validators.

## Tests

Covered by:

- `tests/test_fig_run_journal.py::test_latest_journal_summary_marks_declared_context_pack_newer_as_stale`
