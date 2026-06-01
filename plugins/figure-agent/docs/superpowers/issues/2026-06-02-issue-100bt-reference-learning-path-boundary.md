# Issue 100BT - Reference-Learning Path Boundary

Status: completed; see git history for implementation commit

Type: hardening, reference-learning contract, path boundary

## Problem

`critique_reference_pack.py` validated
`reference_learning.references[].path` as a non-empty string, but did not reject
absolute paths or parent-relative paths at the pack contract layer.

`reference_aesthetic_metrics.py` had a downstream safety check and skipped unsafe
paths before reading them. That prevented escaped reads, but it still made the
authoring contract ambiguous: an unsafe reference-learning anchor could look like
a missing/skipped metric rather than an invalid pack.

## Goal

Reject unsafe reference-learning paths when loading the reference pack, before
status, loop, critique brief, or metric generation can treat the pack as a valid
opt-in reference-learning contract.

## Scope

In scope:

- Reject absolute `reference_learning.references[].path` values.
- Reject paths containing `..`.
- Preserve existing valid fixture-local reference paths.
- Preserve legacy v1 pack parseability for safe paths.
- Keep downstream `reference_aesthetic_metrics.py` skip defense intact.

Out of scope:

- Validating `comparison_references[].path_or_citation`, which can be a paper
  citation rather than a local image path.
- Changing metric thresholds, warning/severe routing, or release behavior.
- Adding provider calls or learned aesthetic models.

## Acceptance

- `load_reference_pack()` rejects `../outside.png`.
- `load_reference_pack()` rejects `/tmp/outside.png`.
- Existing reference-aesthetic metric tests still pass.
- No existing reference-learning metric behavior changes for safe paths.

## Implementation Notes

Added a small path-boundary check in `critique_reference_pack.py` and applied it
to `reference_learning.references[].path`.

Verification:

- `uv run pytest -q tests/test_critique_reference_pack.py::test_load_reference_pack_rejects_unsafe_reference_learning_path tests/test_critique_reference_pack.py tests/test_reference_aesthetic_metrics.py`

## Review Questions

1. Does invalid authoring input fail at the reference pack layer, not only in
   downstream metric generation?
2. Are citation-like fields left alone so real literature references still work?
3. Does this preserve the reference-learning principle that references are style
   anchors, not arbitrary filesystem inputs?
