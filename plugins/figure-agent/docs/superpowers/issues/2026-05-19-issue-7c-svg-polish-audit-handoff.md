# Issue 7C: SVG Polish Audit and Handoff

**Status:** implemented; pending final verification commit
**Design:** `docs/superpowers/specs/2026-05-19-final-artifact-svg-polish-contract-design.md`

## What to build

Document the handoff for a human or outer agent to polish exactly one generated
SVG into `examples/<name>/polish/<name>.polished.svg` without changing the
semantic source of truth.

## Public behavior

The handoff must state:

- [x] base generated export path and hash
- [x] target polished SVG path
- [x] `spec.yaml.final_artifact` opt-in requirement
- [x] allowed visual-only edit classes
- [x] must-backport edit classes
- [x] forbidden edit scope
- [x] required manifest fields
- [x] required `svg_polish_audit.md` closeout
- [x] required post-polish commands

## Required closeout

- [x] Re-run compile/export when source changed before polish.
- [x] Re-run critique when freshness requires it.
- [x] Validate or recreate `svg_polish_manifest.yaml`.
- [x] Add or confirm `spec.yaml.final_artifact.kind: polished_svg` only when the
  polished SVG is intended to become the final artifact.
- [x] Record human semantic-preservation decision.
- [x] Record toolchain and reviewer provenance.
- [x] Re-run `/fig_status` or the future final-artifact validator.
- [x] Do not set `accepted: true` unless publication provenance and final artifact
  checks are closed.

## Implementation

- `/fig_loop` command documentation now includes an SVG polish handoff section.
- `docs/superpowers/plans/2026-05-19-svg-polish-audit-handoff.md` defines the
  operational protocol, allowed writes, forbidden writes, bounded edit classes,
  must-backport classes, manifest requirements, audit closeout template, and
  required status check.
- This slice is docs-only. No runner metadata or validation code changed because
  Issue 7A already supplies the manifest contract and Issue 7B already exposes
  final-artifact validation through `/fig_status`.

## Review notes

- Protocol safety review: clean after documenting exactly one fixture, one
  polished SVG target, bounded allowed writes, and forbidden accepted/golden,
  generated export, build, critique, and unrelated-fixture writes.
- Freshness review: fixed a closeout-order defect. `spec.yaml` opt-in and
  `svg_polish_audit.md` must be final before `svg_polish_manifest.yaml` is
  hashed; otherwise `/fig_status` correctly reports the manifest as stale.
- Integration review: clean after keeping `/fig_loop` verify-only and routing
  validation through the already implemented `/fig_status` final-artifact state.

## Out of scope

- Building an SVG editor.
- Auto-applying SVG changes.
- Batch-polishing multiple fixtures.
- Auto-acceptance or publication-safety decisions.
