# Issue 7A: SVG Polish Manifest Schema

**Status:** implemented; pending final verification commit
**Design:** `docs/superpowers/specs/2026-05-19-final-artifact-svg-polish-contract-design.md`

## What to build

Add a small module for loading, validating, writing, and checking freshness of
`examples/<name>/polish/svg_polish_manifest.yaml`.

The module should not change `/fig_status`, `/fig_export`, `/fig_loop`, or
accepted-mode behavior in this issue.

## Public behavior

- Load `svg_polish_manifest.yaml`.
- Validate `schema: figure-agent.svg-polish-manifest.v1`.
- Validate fixture name, bounded enum values, in-fixture polished SVG path, and
  `sha256:<hash>` fields.
- Validate `polished.audit_hash` against `polish/svg_polish_audit.md`.
- Use the repo's existing `scripts/quality_manifest.py` hash conventions where
  practical; do not invent a second hash format.
- Compute and validate `base.source_set_hash` from the final-artifact input
  set, including style lock, coordinate hints, authoring context, reference
  pack, theory guard, sub-region log, and declared references when present.
- Validate bounded `polished.edit_classes` values:
  `label_micro_position`, `leader_line_micro_position`, `stroke_polish`,
  `icon_detail`, `spacing_balance`, `color_opacity_polish`,
  `typography_cleanup`, and `export_cleanup`.
- Preserve unknown future mapping fields on load/write.
- Detect stale polish when source, generated SVG, export PDF, critique, or
  polished SVG/audit content differs from the manifest hashes.
- Produce controlled validation errors for malformed YAML or malformed fields.

## Acceptance criteria

- [x] valid manifest loads successfully.
- [x] invalid schema fails with a controlled error.
- [x] missing required fields fail.
- [x] invalid polished path outside `examples/<name>/polish/` fails.
- [x] manifest can be validated independently of `spec.yaml` opt-in, while
  release relevance is deferred to Issue 7B.
- [x] invalid enum values fail.
- [x] unknown edit class fails instead of being silently accepted.
- [x] malformed YAML fails cleanly.
- [x] matching hashes are fresh.
- [x] changed source/export/critique/polished SVG hashes are stale.
- [x] changed style lock, coordinate hints, authoring context, reference pack,
  theory guard, sub-region log, or declared reference image makes the manifest
  stale through `base.source_set_hash`.
- [x] changed `svg_polish_audit.md` hash is stale.
- [x] unknown future fields survive load/write.
- [x] writer emits reloadable YAML.

## Implementation

- Module: `scripts/svg_polish_manifest.py`
- Tests: `tests/test_svg_polish_manifest.py`
- Public API:
  - `load_svg_polish_manifest`
  - `validate_svg_polish_manifest`
  - `write_svg_polish_manifest`
  - `svg_polish_manifest_is_stale`
  - `final_artifact_source_paths`
  - `final_artifact_source_set_hash`
  - `SvgPolishManifestError`

## Out of scope

- Status integration.
- Export integration.
- Loop integration.
- Accepted/golden gate integration.
- SVG editing or auto-polish.

## Verification

Run targeted tests for the new module plus existing hash helper tests, then run
the full suite before commit.
