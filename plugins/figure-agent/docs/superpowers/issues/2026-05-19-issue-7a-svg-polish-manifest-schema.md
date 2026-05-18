# Issue 7A: SVG Polish Manifest Schema

**Status:** open
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
- Preserve unknown future mapping fields on load/write.
- Detect stale polish when source, generated SVG, export PDF, critique, or
  polished SVG/audit content differs from the manifest hashes.
- Produce controlled validation errors for malformed YAML or malformed fields.

## Acceptance criteria

- [ ] valid manifest loads successfully.
- [ ] invalid schema fails with a controlled error.
- [ ] missing required fields fail.
- [ ] invalid polished path outside `examples/<name>/polish/` fails.
- [ ] manifest can be validated independently of `spec.yaml` opt-in, while
  release relevance is deferred to Issue 7B.
- [ ] invalid enum values fail.
- [ ] malformed YAML fails cleanly.
- [ ] matching hashes are fresh.
- [ ] changed source/export/critique/polished SVG hashes are stale.
- [ ] changed `svg_polish_audit.md` hash is stale.
- [ ] unknown future fields survive load/write.
- [ ] writer emits reloadable YAML.

## Out of scope

- Status integration.
- Export integration.
- Loop integration.
- Accepted/golden gate integration.
- SVG editing or auto-polish.

## Verification

Run targeted tests for the new module plus existing hash helper tests, then run
the full suite before commit.
