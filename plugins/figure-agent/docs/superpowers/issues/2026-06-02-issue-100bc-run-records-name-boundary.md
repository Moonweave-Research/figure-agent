# Issue 100BC - Fig Run Journal Writer Fixture Name Boundary

Status: implemented

Type: continuation safety, path-boundary hardening, fixture identity consistency

## Problem

`fig_run_records.py` writes non-authoritative `/fig_run` journals under a
configured runs root. The main `/fig_run` path already inherits fixture-name
validation from `fig_driver.py`, and Issue 100BB protected the read-only journal
summary helper.

The writer helper itself still accepted a raw `payload["fixture"]`, sanitized it
for the run directory name, and then recorded an evidence snapshot for that raw
fixture value. A direct module caller or a test that bypassed the driver could
therefore create a journal for traversal syntax such as `../outside`.

The journal is non-authoritative, but it is write-capable continuation evidence.
It should share the same fixture identity boundary as the driver, queue,
exporter, direct commands, and journal summary helper.

## Decision

Reuse `fixture_identity.validate_fixture_name()` inside
`write_run_journal()` after the existing non-empty string check and before:

- allocating a run directory;
- writing `run_manifest.json`, `run.json`, step JSON, or `stop.md`;
- computing the journal evidence snapshot.

The `/fig_run` CLI keeps its existing journal-write failure behavior: if a
protected writer error occurs after a run payload has been produced, the payload
is still printed with a non-authoritative `journal_error` block instead of
hiding the live runner result.

## Tests

Covered by:

- `tests/test_fig_run.py::test_main_refuses_to_record_journal_for_unsafe_fixture_name`
- `tests/test_fig_run.py::test_write_run_journal_rejects_unsafe_fixture_name_before_writing`
- existing safe journal-recording tests for normal fixture names.
