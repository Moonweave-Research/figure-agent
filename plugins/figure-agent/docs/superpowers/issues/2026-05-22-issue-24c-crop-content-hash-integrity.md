# Issue 24C: Crop Content Hash Integrity

**Date:** 2026-05-22 KST
**Status:** implemented in branch
**Type:** audit-input integrity hardening
**Parent:** `2026-05-22-issue-24-audit-gate-hardening-roadmap.md`

## What to build

Bind every generated audit crop PNG to the crop manifest with a `sha256:<hex>`
content hash, then make critique lint reject missing or mismatched crop files
for current crop-accounting schemas.

## Current Problem

`build/audit_crops/manifest.json` participates in critique input freshness, but
the PNG files named by that manifest are not themselves content-hashed inside
the manifest. If a crop PNG is deleted, corrupted, or overwritten while the
manifest file remains unchanged, a host critique can appear fresh even though
the image actually reviewed no longer matches the manifest contract.

## Acceptance Criteria

- [x] `critique_zoom_crops.py` writes `sha256` for every crop entry in
  `build/audit_crops/manifest.json`.
- [x] The hash uses the repo convention `sha256:<64 lowercase hex chars>`.
- [x] `critique_lint.py` rejects v1.8/v1.9 crop manifests when any required
  crop entry is missing `sha256`.
- [x] `critique_lint.py` rejects when a manifest crop path is missing on disk.
- [x] `critique_lint.py` rejects when a crop file hash differs from the
  manifest hash.
- [x] `critique_lint.py` rejects manifest crop paths that escape
  `build/audit_crops/` via absolute paths or `..` traversal.
- [x] Legacy v1.7 critiques remain outside crop-audit accounting.
- [x] Existing crop-audit accounting behavior for missing crop log, unknown
  crop id, and defect-without-link remains unchanged.

## Implementation Notes

- `critique_zoom_crops.py` computes crop hashes after files are saved and
  stores them in each manifest crop entry.
- `critique_lint.py` validates path scope, hash presence, crop file presence,
  and content hash equality for every crop id listed in `required_crop_ids`.
- Test fixture manifests now create crop files with matching hashes unless the
  test intentionally exercises missing or mismatched hash behavior.

## Implementation Contract

- Reuse `quality_manifest.file_sha256()` for hash format compatibility.
- Add `sha256` after each crop file is saved, not before.
- Validate only crop entries listed in `required_crop_ids`; non-required future
  entries may be ignored by this lint slice.
- Keep the manifest schema string stable as
  `figure-agent.audit-crop-manifest.v1`; this is tightening the v1 integrity
  contract, not changing the public manifest shape incompatibly.
- Return controlled `crop_audit_accounting` violations, not tracebacks.

## Suggested Files

- `scripts/critique_zoom_crops.py`
- `scripts/critique_lint.py`
- `tests/test_critique_zoom_crops.py`
- `tests/test_critique_lint.py`
- `docs/superpowers/issues/2026-05-22-issue-24-audit-gate-hardening-roadmap.md`
- `docs/superpowers/issues/2026-05-22-issue-24c-crop-content-hash-integrity.md`

## TDD Plan

1. Add a failing zoom-crop manifest test asserting every manifest crop has a
   valid `sha256` and that it equals `file_sha256(example_dir / crop["path"])`.
2. Add failing lint tests for:
   - required manifest crop missing `sha256`;
   - required crop path escaping `build/audit_crops/`;
   - required crop path missing on disk;
   - required crop hash mismatch.
3. Implement manifest hash writing.
4. Implement lint validation of required manifest crop hashes.
5. Update test fixture helpers to create crop files and correct hashes when
   tests are not about hash failure.
6. Run focused tests and full verification.

## Verification

```bash
uv run pytest -q tests/test_critique_zoom_crops.py tests/test_critique_lint.py
uv run ruff check scripts/critique_zoom_crops.py scripts/critique_lint.py tests/test_critique_zoom_crops.py tests/test_critique_lint.py
git diff --check
```

## Non-Goals

- No new critique schema version.
- No status or driver routing changes.
- No crop regeneration inside lint.
- No generated crop/build artifact commits.
