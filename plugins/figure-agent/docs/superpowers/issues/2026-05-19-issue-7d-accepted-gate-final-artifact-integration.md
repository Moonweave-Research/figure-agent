# Issue 7D: Accepted Gate Final Artifact Integration

**Status:** open
**Design:** `docs/superpowers/specs/2026-05-19-final-artifact-svg-polish-contract-design.md`

## What to build

Extend accepted-mode validation so polished SVG is required only when a fixture
declares polished SVG as the final artifact.

## Public behavior

For generated-export fixtures, accepted-mode behavior remains unchanged. A
fixture becomes a polished-SVG fixture only when `spec.yaml.final_artifact.kind`
is `polished_svg`.

For polished-SVG fixtures, accepted-mode validation must require:

- valid `svg_polish_manifest.yaml`
- existing polished SVG
- fresh source/export/critique/polished hashes
- `semantic_change_declared: false`
- `backport_required: false`
- reviewer provenance
- publication safety and disclosure fields when submitting externally

## Acceptance criteria

- [ ] generated-export fixtures keep current accepted-gate behavior.
- [ ] draft `polish/` files without `spec.yaml.final_artifact.kind` set to
  `polished_svg` do not change accepted-mode behavior.
- [ ] polished-SVG fixtures fail accepted-mode validation when manifest is
  missing, invalid, or stale.
- [ ] polished-SVG fixtures fail when semantic backport is required.
- [ ] polished-SVG fixtures fail when reviewer provenance is absent.
- [ ] `accepted: true` is never set by the checker.
- [ ] generated exports are never overwritten by polished artifacts.

## Out of scope

- Implementing SVG editing.
- Deciding target journal policy automatically.
- Requiring polished SVG for non-polished fixtures.
