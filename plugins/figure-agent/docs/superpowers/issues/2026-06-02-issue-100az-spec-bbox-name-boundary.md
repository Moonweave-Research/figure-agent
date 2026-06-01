# Issue 100AZ - Spec BBox Helper Fixture Name Boundary

Status: implemented

Type: helper safety, path-boundary hardening, fixture identity consistency

## Problem

`spec_bbox_helper.py` is a read-only helper that converts source TikZ panel
boxes into `spec.yaml` `bbox_pdf_cm` values. It accepts a fixture `name` and an
optional `--examples-root`, then reads:

- `<examples-root>/<name>/<name>.tex`.

Before this issue, the helper did not validate that `name` was a single fixture
identity. A name such as `../outside` could escape the examples root and read an
unrelated TeX file if the filesystem layout happened to make the normalized
path valid.

Even though the helper is read-only, it participates in authoring reference
geometry and should follow the same fixture identity boundary as the rest of
the command surface.

## Decision

Reuse `fixture_identity.validate_fixture_name()` at the start of
`spec_bbox_helper.run()`.

The helper still supports a custom `--examples-root`; only the `name` segment is
restricted to a non-empty single path component. Validation failures are
translated into the helper's existing `BboxHelperError` so CLI behavior remains
controlled through the existing `ERROR: ...` path.

## Tests

Covered by:

- `tests/test_spec_bbox_helper.py::test_spec_bbox_helper_rejects_unsafe_fixture_name_before_reading_tex`
- `tests/test_spec_bbox_helper.py::test_spec_bbox_helper_preserves_safe_custom_examples_root`

