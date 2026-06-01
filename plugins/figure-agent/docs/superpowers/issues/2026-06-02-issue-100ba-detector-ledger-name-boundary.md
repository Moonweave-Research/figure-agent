# Issue 100BA - Detector Feedback Ledger Fixture Name Boundary

Status: implemented

Type: diagnostic safety, path-boundary hardening, fixture identity consistency

## Problem

`detector_feedback_ledger.py` aggregates detector-feedback signals across
selected fixtures. When explicit fixture names were provided, it resolved each
entry as:

- `<examples-root>/<fixture_name>`.

Before this issue, `fixture_name` was not validated as a single fixture
identity. A selected name such as `../outside` could escape the examples root
and be included in the ledger if the normalized directory existed and contained
a `critique.md`.

The ledger is read-only, but it informs detector tuning and whole-plugin review
decisions. Its selected fixture set must not be polluted by traversal syntax.

## Decision

Reuse `fixture_identity.validate_fixture_name()` for explicit selected fixture
names before any directory lookup.

Default all-fixture mode still scans direct child directories of
`examples_root`, but skips entries whose resolved path escapes the resolved
examples root. Unknown safe fixture names continue to produce the existing
`fixture not found` error.

## Tests

Covered by:

- `tests/test_detector_feedback_ledger.py::test_ledger_rejects_unsafe_selected_fixture_before_reading_outside_root`
- `tests/test_detector_feedback_ledger.py::test_ledger_default_fixture_selection_skips_symlink_escape`
- `tests/test_detector_feedback_ledger.py::test_cli_rejects_unsafe_selected_fixture_cleanly`
