# Issue 7D: Accepted Gate Final Artifact Integration

**Status:** completed in commit `89ad2a1`.
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
- publication safety and a `disclosure-needed` declaration for polished SVG
  acceptance

## Acceptance criteria

- [x] generated-export fixtures keep current accepted-gate behavior.
- [x] draft `polish/` files without `spec.yaml.final_artifact.kind` set to
  `polished_svg` do not change accepted-mode behavior.
- [x] polished-SVG fixtures fail accepted-mode validation when manifest is
  missing, invalid, or stale.
- [x] polished-SVG fixtures fail when semantic backport is required.
- [x] polished-SVG fixtures with `final_artifact_state: BLOCKED` fail
  accepted-mode validation with a backport-oriented message, not a malformed
  manifest message.
- [x] polished-SVG fixtures fail when reviewer provenance is absent.
- [x] `accepted: true` is never set by the checker.
- [x] generated exports are never overwritten by polished artifacts.

## Implementation

- `scripts/svg_polish_manifest.py` now owns the shared final-artifact state
  classifier used by both `/fig_status` and the accepted gate.
- `scripts/check_golden_artifacts.py` now runs a final-artifact gate only inside
  accepted mode.
- Fixtures with no `final_artifact` block, or with
  `final_artifact.kind: generated_export`, keep the existing generated-export
  accepted-gate behavior.
- `spec.yaml.final_artifact.kind: polished_svg` requires a contained
  `polish/svg_polish_manifest.yaml`, valid manifest schema, fresh hashes,
  existing polished SVG and audit, reviewer provenance, and no declared
  semantic change or required backport.
- Non-canonical manifest paths are invalid; the active contract is exactly
  `polish/svg_polish_manifest.yaml`.
- `semantic_change_declared: true` or `backport_required: true` fails with a
  semantic-backport message instead of a malformed-manifest message.
- Malformed `spec.yaml` fails cleanly in default, basic, accepted, and status
  paths instead of crashing or being mislabeled as a golden-contract error.
- `/fig_status` now exposes final-artifact missing/invalid/stale/blocked next
  actions while keeping generated-export fixtures on the old path.
- `/fig_loop` remains verify-only, but it no longer reports
  `verify_only_complete` when status says workflow inputs are ready but the
  final artifact is not final-ready. Its decision/JSON summaries include the
  final-artifact state/kind/path for handoff visibility.
- Tests live in `tests/test_golden_artifact_checks.py`,
  `tests/test_status.py`, `tests/test_svg_polish_manifest.py`, and
  `tests/test_fig_loop.py`.

## Review notes

- TDD red check: polished-SVG missing, stale, blocked, and invalid provenance
  cases initially passed accepted mode because no final-artifact gate was wired.
- Scope review: clean after keeping final-artifact checks in accepted mode only;
  draft `polish/` files without opt-in remain unchanged. Malformed `spec.yaml`
  now fails in all checker modes because accepted/final-artifact policy cannot
  be safely inferred from an invalid spec.
- Safety review: clean after confirming the checker only reads files and returns
  failures; it does not set `accepted: true`, overwrite generated exports, or
  promote polished artifacts.
- External review fix: replaced broad `"missing"` substring classification with
  load-vs-staleness error handling so malformed manifests remain `INVALID` even
  when fixture paths contain the word `missing`.
- External review fix: enforced the canonical
  `polish/svg_polish_manifest.yaml` manifest path in both `/fig_status` and the
  accepted gate to keep the 7A-7D contract single-source.
- External review fix: added regression coverage for read-only safety,
  `final_artifact` partial-block compatibility, missing polished SVG files, and
  both required provenance fields.
- External review fix: malformed `spec.yaml` is now a controlled failure in the
  accepted checker even when accepted mode is not requested.
- External review fix: `/fig_status` now prioritizes malformed spec repair and
  final-artifact remediation messages before acceptance signoff.
- External review fix: `/fig_loop` now treats non-final-ready polished artifacts
  as `status_action_required` instead of a completed verify-only loop.
- External review fix: final-artifact source hash helpers no longer double-wrap
  malformed `spec.yaml` errors.
- External review fix: legacy generated-export fixtures with non-final-artifact
  spec validation errors no longer report `final_artifact_invalid`.
- External review fix: `style_profile_unknown` now has a blocking `/fig_status`
  next action instead of contradicting `workflow_ready=false` with a done
  message.
- External review fix: `/fig_loop` decision/JSON output now exposes
  final-artifact state/kind/path while leaving full Issue 7E taxonomy deferred.

## Out of scope

- Implementing SVG editing.
- Deciding target journal policy automatically.
- Requiring polished SVG for non-polished fixtures.
