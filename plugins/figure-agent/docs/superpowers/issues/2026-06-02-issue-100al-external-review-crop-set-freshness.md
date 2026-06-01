# Issue 100AL - External Review Crop-Set Freshness

Status: completed

Type: external review freshness, crop manifest contract

## Problem

`external_vision_review.yaml` hashes the reviewed render and each reviewed crop.
That catches changed or missing reviewed files, but it did not catch the crop
set itself changing after the review was authored. If
`build/audit_crops/manifest.json` later added a new high-zoom crop, the old
external review could remain `fresh` even though the reviewer never inspected
that new crop.

## Decision

When the current audit-crop manifest exists, external-review freshness now
compares the current manifest crop paths with `reviewed_crops[]`.

- New current manifest crop not listed in `reviewed_crops[]` => `stale`.
- Reviewed crop no longer listed by the current manifest => `stale`.
- Malformed current manifest => `invalid`.
- Legacy/manual reviews without a manifest keep the previous file-hash behavior.

## Implemented Contract

- `external_vision_review_freshness()` now treats manifest crop-set drift as a
  stale external review.
- Existing stale/missing reviewed-file behavior remains unchanged.

## Tests

Covered by:

- `tests/test_external_vision_review.py::test_external_vision_review_freshness_detects_manifest_crop_set_drift`
