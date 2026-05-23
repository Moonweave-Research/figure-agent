# Issue 42 SVG Polish UX and Semantic Backport Design

**Date:** 2026-05-23
**Status:** implemented

## Purpose

`figure-agent` should remain a quality kernel, not an SVG editor. The next
useful product step is to make the existing Layer 5.5 polished-SVG contract easy
to use after a human or outer agent performs optical SVG polish.

The implementation should reduce manual hash/audit work while preserving the
hard boundary: TikZ, briefing, spec, references, critique, and adjudication stay
the semantic source of truth. SVG polish may only carry visual-only edits unless
the manifest blocks release with `backport_required: true`.

## Current State

Already implemented:

- `scripts/svg_polish_manifest.py` validates, writes, and freshness-checks
  `polish/svg_polish_manifest.yaml`.
- `/fig_status` surfaces final-artifact state.
- Accepted-mode checks require a fresh polished SVG only when `spec.yaml`
  declares `final_artifact.kind: polished_svg`.
- `/fig_loop` and `/fig_drive --mode polish` can route to polish or semantic
  backport.

Still missing:

- A first-class command/module that creates the audit and manifest from current
  fixture files.
- A structured audit template that makes semantic-backport review explicit.
- A narrow UX path that avoids hand-written hash snippets.

## Design

Add a small scaffolder module, `scripts/svg_polish_handoff.py`.

The module operates on one fixture directory. It assumes the human or outer
agent has already created:

- `exports/<name>.svg`
- `exports/<name>.pdf`
- `critique.md`
- `polish/<name>.polished.svg`

It writes:

- `polish/svg_polish_audit.md`
- `polish/svg_polish_manifest.yaml`

It must not edit:

- `exports/`
- `build/`
- `critique.md`
- accepted/golden state
- unrelated fixtures
- TikZ, briefing, or spec semantics

## Semantic-Backport Classification

The generated audit must contain these required checks:

- components
- labels/material identity
- mechanism directions
- panel/storyline meaning
- scale/proximity meaning
- unresolved critique findings

Each check is recorded as prose in `svg_polish_audit.md`. The machine-readable
release boundary remains in the manifest:

```yaml
polished:
  semantic_change_declared: true | false
  backport_required: true | false
```

If either value is true, existing final-artifact status must report `BLOCKED`
after the fixture opts into polished SVG. The scaffolder should not invent a new
state machine.

## CLI Contract

Recommended command shape:

```bash
uv run python3 scripts/svg_polish_handoff.py examples/<name> \
  --reviewer "author" \
  --editor human \
  --toolchain "Inkscape:1.4" \
  --edit-class label_micro_position \
  --edit-class stroke_polish \
  --reviewed-at 2026-05-23T00:00:00Z \
  --notes "visual-only polish" \
  --write
```

Without `--write`, the command should validate inputs and print the files it
would write. With `--write`, it writes the audit first, then writes the manifest
last so the manifest hashes current audit content.

## Error Handling

The command must fail with controlled user-facing errors when:

- the fixture path is invalid
- required input files are missing
- an edit class is not one of `svg_polish_manifest.ALLOWED_EDIT_CLASSES`
- the editor is not one of `svg_polish_manifest.ALLOWED_EDITORS`
- output files already exist and `--force` was not supplied

## Backward Compatibility

No existing fixture changes behavior unless the new command is explicitly run.
Fixtures without `spec.yaml.final_artifact.kind: polished_svg` continue on the
generated-export path. A generated manifest without opt-in remains non-release
relevant, matching the existing final-artifact contract.

## Tests

Add `tests/test_svg_polish_handoff.py` covering:

- generated audit includes all semantic-backport checks
- generated manifest loads through `load_svg_polish_manifest`
- generated manifest is fresh when source/export/critique/polish/audit are
  unchanged
- unknown edit class fails before files are written
- `backport_required: true` produces a manifest that existing status logic can
  classify as `BLOCKED` when the fixture opts in
- CLI dry run does not write files

## Non-Goals

- No SVG geometry modification.
- No automatic source patching.
- No automatic accepted/golden mutation.
- No paper-wide style propagation in this issue.
- No schema bump to `figure-agent.svg-polish-manifest.v2`.
