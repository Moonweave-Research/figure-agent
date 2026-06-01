# Issue 100BS - Reference Extract Path Boundary

Status: implemented

Type: reference-authoring evidence safety, path-boundary hardening

## Problem

`reference_extract.py` reads `spec.yaml.reference_image`, analyzes that PNG, and
writes `coordinate_hints.yaml`. Those hints feed semantic authoring and layout
drift checks, so the reference image is trusted authoring evidence for one
fixture.

Before this issue, a fixture could declare:

```yaml
reference_image: ../outside.png
```

If the normalized outside file existed, `/fig_extract` consumed it and wrote
fixture-local coordinate hints. This made unrelated images look like valid
fixture-bound reference evidence.

## Decision

Require `reference_image` to resolve under the fixture directory before any OCR,
palette clustering, structural extraction, or `coordinate_hints.yaml` write.

The resolver now rejects:

- absolute `reference_image` paths;
- parent-relative paths that escape the fixture;
- symlink-resolved paths that leave the fixture directory.

Normal fixture-local relative paths such as `reference/synth.png` and `ref.png`
remain valid.

## Tests

Covered by:

- `tests/test_reference_extract.py::test_extract_rejects_reference_image_outside_fixture`
- existing missing-reference, synthetic-palette, RGBA, OCR, rebuild, and
  structural-region tests

The new test was red before implementation: the outside PNG was consumed and
`coordinate_hints.yaml` was written.

## Review Notes

- The change is intentionally scoped to `reference_image` source ownership.
- It does not make `/fig_extract` mandatory.
- It does not alter reference metrics, critique freshness, status, loop, export,
  accepted, golden, SVG polish, or publication behavior.
- The failure mode remains controlled through the existing `(None, failures)`
  return path and CLI `FAIL:` reporting.
