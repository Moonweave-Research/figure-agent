# Issue 7C: SVG Polish Audit and Handoff

**Status:** open
**Design:** `docs/superpowers/specs/2026-05-19-final-artifact-svg-polish-contract-design.md`

## What to build

Document the handoff for a human or outer agent to polish exactly one generated
SVG into `examples/<name>/polish/<name>.polished.svg` without changing the
semantic source of truth.

## Public behavior

The handoff must state:

- base generated export path and hash
- target polished SVG path
- `spec.yaml.final_artifact` opt-in requirement
- allowed visual-only edit classes
- must-backport edit classes
- forbidden edit scope
- required manifest fields
- required `svg_polish_audit.md` closeout
- required post-polish commands

## Required closeout

- Re-run compile/export when source changed before polish.
- Re-run critique when freshness requires it.
- Validate or recreate `svg_polish_manifest.yaml`.
- Add or confirm `spec.yaml.final_artifact.kind: polished_svg` only when the
  polished SVG is intended to become the final artifact.
- Record human semantic-preservation decision.
- Record toolchain and reviewer provenance.
- Re-run `/fig_status` or the future final-artifact validator.
- Do not set `accepted: true` unless publication provenance and final artifact
  checks are closed.

## Out of scope

- Building an SVG editor.
- Auto-applying SVG changes.
- Batch-polishing multiple fixtures.
- Auto-acceptance or publication-safety decisions.
