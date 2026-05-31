# Issue 91D - Crop And Delta Observation Grounding

Status: completed

Type: host-vision critique accountability, crop evidence quality, SVG delta
evidence quality

Depends on:

- Issue 91A - SVG delta artifact hash and renderer provenance
- Issue 91B - SVG semantic diff checker
- Issue 91C - TikZ boundary and near-miss auto-discovery

## What To Build

Strengthen host-vision critique evidence so "I inspected this crop" is not
enough. Each required crop and SVG delta image should include locally grounded
evidence that names the visible object, candidate id, relative position, and
observed relationship.

This is a lint/accounting contract. It does not prove visual truth, but it
makes shallow crop claims harder to pass and easier for a reviewer to audit.

Because the required critique shape changes, this slice must bump the current
critique schema/rubric version. Legacy v1.15 and older critiques must remain
parseable and must not be retroactively invalidated only because they lack the
new fields.

## Required Evidence Shape

For each `crop_audit_log` entry, require:

- `crop_id`
- `path`
- `verdict`
- `observed_objects`: non-empty list of object names visible in the crop
- `local_relationship`: one sentence naming relative position or clearance
- `candidate_refs`: list of related VC/TB/LP/UG ids, empty only when no
  deterministic candidate exists for that crop
- `unintended_visible_anomaly`
- `anomaly_rationale`

For each `svg_polish_delta_audit.delta_image_audit_log` entry, require:

- `image_id`
- `path`
- `verdict`
- `observed_objects`
- `local_relationship`
- `delta_focus`: what changed or did not change in this image
- `observation`

## Acceptance Criteria

- [x] Current-schema critiques reject crop entries missing object names.
- [x] Current-schema critiques reject crop entries with generic
      `local_relationship`.
- [x] Delta audit entries reject generic observations that do not mention
      before/after/diff-local objects.
- [x] Legacy v1.14 and older critiques remain parseable through legacy paths.
- [x] `fig_loop` surfaces grounded-evidence uncertainty through the existing
      `critique_lint_blocked` status blocker instead of silent pass.
- [x] Tests cover missing object names, generic relationship, missing candidate
      refs where candidates exist, legacy compatibility, and loop surfacing.

## Implementation Notes

- Current SVG-polish-delta critiques now emit schema
  `figure-agent.critique.v1.16` and rubric
  `figure-agent.critique-rubric.v1.16`.
- v1.16 `crop_audit_log[]` entries require `observed_objects`,
  non-generic `local_relationship`, and deterministic `candidate_refs` when
  the crop source names a VC/TB/LP/UG candidate.
- v1.16 `svg_polish_delta_audit.delta_image_audit_log[]` entries require
  `observed_objects`, non-generic `local_relationship`, `delta_focus`, and a
  non-generic `observation`.
- Legacy v1.15 and older schema validation remains available for already
  authored critiques. Fresh SVG polish delta lint now requires the current
  v1.16 contract.

## Edge Cases

- A crop genuinely has no deterministic candidate id.
- A print-scale crop is global and should cite panel/label groups rather than
  one VC/TB/LP/UG id.
- A full-render quadrant contains multiple panels.
- A delta diff image has no visible pixels because the polish made no
  meaningful change.
- A host critique uses correct crop ids but describes an object from another
  crop.

## Verification

- `uv run pytest -q tests/test_critique_lint.py tests/test_fig_loop.py tests/test_critique_schema_validator.py`
- `uv run ruff check scripts/critique_lint.py scripts/critique_schema_validator.py scripts/fig_loop.py`
- `git diff --check`

Implemented verification:

- `uv run pytest -q tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_status.py tests/test_fig_loop.py`
  - Result: 499 passed.
- `uv run ruff check scripts/critique_schema_validator.py scripts/critique_schema_vocab.py scripts/quality_manifest.py scripts/critique_brief.py scripts/critique_lint.py tests/test_critique_schema_validator.py tests/test_quality_manifest.py tests/test_critique_brief.py tests/test_critique_lint.py`
  - Result: All checks passed.
- `git diff --check`
  - Result: clean.
