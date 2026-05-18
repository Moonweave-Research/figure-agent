# Issue 7B: Final Artifact Status State

**Status:** open
**Design:** `docs/superpowers/specs/2026-05-19-final-artifact-svg-polish-contract-design.md`

## What to build

Expose final-artifact state in `/fig_status` while preserving existing status
semantics for fixtures that do not declare polished SVG as the final artifact.

## Public behavior

`/fig_status` should report:

- `final_artifact_state`: `NONE`, `MISSING`, `INVALID`, `STALE`, or `FRESH`
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

## Acceptance criteria

- [ ] no-polish fixtures report `final_artifact_state: NONE`.
- [ ] fixtures with no `spec.yaml.final_artifact` keep current readiness even
  if a draft polish manifest exists.
- [ ] missing declared polished SVG reports `MISSING`.
- [ ] malformed manifest reports `INVALID`.
- [ ] stale manifest reports `STALE`.
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
