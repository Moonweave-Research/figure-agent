# Issue 7B: Final Artifact Status State

**Status:** open
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

- [ ] no-polish fixtures report `final_artifact_state: NONE`.
- [ ] `final_artifact.kind: generated_export` reports generated-export behavior
  and does not require a polish manifest.
- [ ] fixtures with no `spec.yaml.final_artifact` keep current readiness even
  if a draft polish manifest exists.
- [ ] missing declared polished SVG reports `MISSING`.
- [ ] malformed manifest reports `INVALID`.
- [ ] stale manifest reports `STALE`.
- [ ] valid hash-fresh manifest with `semantic_change_declared: true` or
  `backport_required: true` reports `BLOCKED`.
- [ ] matching manifest and polished SVG reports `FRESH`.
- [ ] existing `workflow_ready`, `golden_ready`, `release_ready`, and
  `final_ready` behavior is unchanged unless polished SVG is declared as the
  final artifact.
- [ ] status output remains read-only.

## Out of scope

- Changing `/fig_export`.
- Changing accepted-mode gates.
- Editing SVG files.
- Requiring polish for all fixtures.
