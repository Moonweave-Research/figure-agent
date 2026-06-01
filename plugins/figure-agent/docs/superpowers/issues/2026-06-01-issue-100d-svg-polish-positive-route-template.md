# Issue 100D - SVG Polish Positive-Route Recipe Template

Status: completed

Type: SVG polish UX, recipe starter, positive-route dogfood

## Problem

The SVG polish path has strong safety contracts: recipes are bounded, executor
actions are limited, stale recipes are blocked, and final artifacts are gated.
The remaining production gap is positive-route usability. When `/fig_loop` or
`/fig_drive` says `ready_for_svg_polish`, operators still need to hand-author a
recipe from scratch.

That makes SVG polish feel like a safety gate rather than a practical last-mile
polish lane.

## Scope

Add a fixture-aware recipe starter template to `scripts/svg_polish_recipe.py`.

In scope:

- emit `figure-agent.svg-polish-recipe.v1` YAML from a real fixture directory;
- compute the correct `recipe_input_hash` for the fixture's exported SVG;
- include conservative visual-only starter operations that validate as recipe
  schema but still require operator selector edits before execution;
- document that the template is a starter, not proof that SVG polish is
  appropriate;
- keep executor safety and stale checks unchanged.

Out of scope:

- no automatic SVG polish application;
- no generated export/polish artifact commits;
- no semantic edits or new allowed edit classes;
- no release/accepted/golden mutation;
- no change to `ready_for_svg_polish` routing thresholds.

## Expected Public Behavior

```bash
uv run python3 scripts/svg_polish_recipe.py --template examples/<name>
uv run python3 scripts/svg_polish_recipe.py --template examples/<name> --write-template
```

prints a deterministic YAML recipe, or writes it to
`polish/svg_polish_recipe.yaml` with `--write-template`, with:

- `source_svg: exports/<name>.svg`
- `target_svg: polish/<name>.polished.svg`
- current `recipe_input_hash`
- three conservative starter operations:
  - `label_micro_position`
  - `stroke_polish`
  - `typography_cleanup`

The emitted YAML should be reloadable by `load_svg_polish_recipe()`. Executor
dry-run may still fail until the operator replaces placeholder selectors with
real SVG IDs/text/classes; that is intentional.

## Review Notes

- This is a usability slice, not a claim that SVG polish is always beneficial.
- The template must preserve semantic guard language so operators do not treat
  SVG as a hidden source-edit lane.
- Executor dry-run still resolves selectors against the current SVG and remains
  the required next check before writing `polish/<name>.polished.svg`.
