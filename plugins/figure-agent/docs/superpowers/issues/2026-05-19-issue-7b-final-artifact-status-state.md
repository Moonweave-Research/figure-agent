# Issue 7B: Final Artifact Status State

**Status:** completed in commits `832d72d`, `89ad2a1`.
**Design:** `docs/superpowers/specs/2026-05-19-final-artifact-svg-polish-contract-design.md`

## What to build

Expose final-artifact state in `/fig_status` while preserving existing status
semantics for fixtures that do not declare polished SVG as the final artifact.

## Public behavior

`/fig_status` should report:

- `final_artifact_state`: `NONE`, `MISSING`, `INVALID`, `STALE`, `BLOCKED`,
  or `FRESH`
- `final_artifact_kind`: `generated_export` or `polished_svg`
- `final_artifact_path`
- validation notes when the state blocks release

Ordinary fixtures without a polish manifest remain compatible. Their generated
export remains the current artifact path.

Polished SVG is release-relevant only when `spec.yaml` opts in:

```yaml
final_artifact:
  kind: polished_svg
  manifest: polish/svg_polish_manifest.yaml
```

A stray polish manifest without this opt-in may produce an informational note,
but it must not change readiness semantics.

`final_artifact.kind: generated_export` is an explicit spelling of the current
default and should behave like no polish opt-in.

## Acceptance criteria

- [x] no-polish fixtures report `final_artifact_state: NONE`.
- [x] `final_artifact.kind: generated_export` reports generated-export behavior
  and does not require a polish manifest.
- [x] fixtures with no `spec.yaml.final_artifact` keep current readiness even
  if a draft polish manifest exists.
- [x] missing declared polished SVG reports `MISSING`.
- [x] malformed manifest reports `INVALID`.
- [x] stale manifest reports `STALE`.
- [x] valid hash-fresh manifest with `semantic_change_declared: true` or
  `backport_required: true` reports `BLOCKED`.
- [x] matching manifest and polished SVG reports `FRESH`.
- [x] existing `workflow_ready`, `golden_ready`, `release_ready`, and
  `final_ready` behavior is unchanged unless polished SVG is declared as the
  final artifact.
- [x] invalid final-artifact config blocks release readiness without blocking
  workflow readiness.
- [x] status output remains read-only.

## Implementation

- `scripts/status.py` now reports:
  - `final_artifact_state`
  - `final_artifact_kind`
  - `final_artifact_path`
- `/fig_status <name>` output includes a `Final artifact:` line.
- `final_artifact_*` notes are non-blocking for `workflow_ready`, but polished
  SVG states other than `FRESH` block `release_ready`/`final_ready` when the
  fixture opts into `polished_svg`.
- Tests live in `tests/test_status.py`.

## Out of scope

- Changing `/fig_export`.
- Changing accepted-mode gates.
- Editing SVG files.
- Requiring polish for all fixtures.
