# Issue 42 — SVG Polish UX and Semantic Backport Classifier

**Status:** implemented on main through Issue 44 SVG polish recipe executor
**Spec:** `../specs/2026-05-23-issue42-svg-polish-ux-and-semantic-backport-design.md`
**Plan:** `../plans/2026-05-23-issue42-svg-polish-ux-and-semantic-backport.md`

## Problem

The final-artifact contract is implemented, but the operator experience is too
manual. A human or outer agent can polish `exports/<name>.svg` into
`polish/<name>.polished.svg`, but the repo still expects them to hand-author the
audit markdown, compute hashes, assemble `svg_polish_manifest.yaml`, and decide
whether each edit is visual-only or requires semantic backport.

This leaves the biggest current product gap: the plugin can say SVG polish is
needed, but it does not yet make the polish handoff easy, repeatable, or hard to
misclassify.

## In Scope

- A deterministic polish handoff scaffolder that writes:
  - `polish/svg_polish_audit.md`
  - `polish/svg_polish_manifest.yaml`
- Controlled semantic-backport classification fields in the generated audit.
- Reuse the existing `figure-agent.svg-polish-manifest.v1` schema and freshness
  logic.
- Keep `/fig_loop`, `/fig_status`, accepted/golden behavior backward
  compatible.
- Tests for generated audit/manifest validity, stale/fresh behavior, invalid
  edit classes, and backport-required behavior.

## Out of Scope

- Editing SVG geometry automatically.
- Running Inkscape, Affinity, browser automation, or external image tools.
- Mutating `exports/`, `build/`, `critique.md`, accepted state, or golden
  contracts.
- Paper-wide style propagation.
- New scoring or release-gating policy.

## Acceptance Criteria

- A command or module can scaffold the audit and manifest for one polished SVG.
- The generated manifest loads through `scripts/svg_polish_manifest.py`.
- With current source/export/critique/polish/audit content, the generated
  manifest is not stale.
- If `backport_required` or `semantic_change_declared` is true, the existing
  final-artifact state reports `BLOCKED` once the fixture opts into
  `polished_svg`.
- Unknown edit classes are rejected before writing files.
- Generated audit text contains explicit semantic-backport checks for
  components, labels/material identity, mechanism directions,
  panel/storyline meaning, scale/proximity meaning, and unresolved critique
  finding visibility.

## Priority

This is the next plugin-product priority after v0.5.6 because audit coverage is
already strong enough to identify the last polish bottleneck. The missing piece
is a safe execution path for the last optical-polish layer.
