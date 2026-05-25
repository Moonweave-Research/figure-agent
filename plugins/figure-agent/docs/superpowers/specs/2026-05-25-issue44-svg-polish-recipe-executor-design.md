# Issue 44 Design - SVG Polish Recipe Executor and Aesthetic Delta Gate

**Date:** 2026-05-25
**Status:** planned

## Purpose

`figure-agent` should help a semantically correct figure reach a hand-finished
journal artifact without becoming an autonomous illustrator. The plugin already
has strong compile, critique, loop, export, final-artifact, and aesthetic-lever
contracts. What is missing is a bounded execution layer for the visual-only SVG
polish that happens after `ready_for_svg_polish`.

The design adds a recipe-based SVG polish layer. A recipe is a small,
declarative list of visual-only edits that can be validated, dry-run, applied,
hashed, and reviewed. The recipe does not replace human art direction. It
turns safe polish intent into repeatable operations and forces a before/after
audit before the result can count as final.

## Current State

Implemented today:

- `/fig_critique` can require `aesthetic_lever_audit` for
  `aesthetic_intent.yaml` schema v2 fixtures.
- `/fig_loop` and `/fig_drive --mode polish` can route to
  `ready_for_svg_polish`, `continue_tikz`, `semantic_backport_required`, or
  `needs_human_art_direction`.
- `scripts/svg_polish_handoff.py` can scaffold `svg_polish_audit.md` and
  `svg_polish_manifest.yaml` after `polish/<name>.polished.svg` exists.
- `scripts/svg_polish_manifest.py` validates allowed edit classes, hashes
  source/export/critique/polish/audit inputs, and blocks final readiness when
  semantic backport is required.

Still missing:

- A contract for the concrete SVG changes an agent may apply.
- A dry-run-first executor for low-risk visual polish.
- A deterministic before/after review pack.
- A way to tell whether polish improved the artifact or introduced a visual or
  semantic regression.

## Design Principles

1. Recipes are bounded operations, not prose instructions.
2. Dry-run is the default and must be useful on its own.
3. The executor may write only under `polish/`.
4. Semantic changes are never treated as polish success.
5. Aesthetic delta is judged after application, not assumed from the recipe.
6. The existing manifest and final-artifact state remain the release gate.

## Recipe Contract

Add optional `examples/<name>/polish/svg_polish_recipe.yaml`.

```yaml
schema: figure-agent.svg-polish-recipe.v1
fixture: fig1_overview_v2_pair_001_vault
source_svg: exports/fig1_overview_v2_pair_001_vault.svg
target_svg: polish/fig1_overview_v2_pair_001_vault.polished.svg
recipe_input_hash: sha256:<hash of source svg + recipe-relevant context>
operations:
  - id: R001
    class: label_micro_position
    selector:
      kind: element_id
      value: label-panel-e-vs-meter
    action:
      type: translate
      dx: 0.0
      dy: -1.5
      unit: px
    rationale: "Move label away from display edge without changing meaning."
    linked_aesthetic_lever: typography_authority
    semantic_guard:
      allowed: true
      reason: "same label, same target, sub-2px optical adjustment"
```

### Required Fields

- `schema`: exactly `figure-agent.svg-polish-recipe.v1`.
- `fixture`: must match the fixture directory.
- `source_svg`: fixture-relative path under `exports/`.
- `target_svg`: fixture-relative path under `polish/`.
- `recipe_input_hash`: sha256-prefixed hash.
- `operations`: non-empty list.

Each operation requires:

- `id`: stable unique id.
- `class`: one of the allowed edit classes.
- `selector`: bounded SVG element selector.
- `action`: one supported action.
- `rationale`: non-empty.
- `linked_aesthetic_lever`: optional, but required when the fixture declares
  `aesthetic_intent.yaml` schema v2 and the operation is driven by a lever.
- `semantic_guard.allowed`: boolean.
- `semantic_guard.reason`: non-empty string.

Unknown future mapping fields may be preserved by parser/writer support, but
they must not bypass required-field validation.

## Allowed Operation Classes

The recipe class set intentionally matches the existing final-artifact manifest
edit classes:

- `label_micro_position`
- `leader_line_micro_position`
- `stroke_polish`
- `icon_detail`
- `spacing_balance`
- `color_opacity_polish`
- `typography_cleanup`
- `export_cleanup`

`component_fidelity` and `hand_craft` aesthetic levers may route to SVG polish,
but the actual recipe must still use one of the visual-only classes above.

## Supported MVP Actions

Issue 44B should start with a conservative subset:

- `translate`: apply a small `transform` translation to a selected element or
  group. Limit absolute movement to a small configured maximum.
- `set_stroke_width`: adjust stroke width within a narrow ratio range.
- `set_opacity`: adjust opacity within a narrow range.
- `set_fill_opacity`: adjust fill opacity within a narrow range.
- `set_stroke_opacity`: adjust stroke opacity within a narrow range.

Deferred actions:

- path geometry rewriting;
- free-form path smoothing;
- shadow synthesis;
- texture generation;
- element creation;
- element deletion;
- font replacement.

## Selector Contract

Selectors must be deterministic and bounded:

- `element_id`: exact SVG `id`.
- `css_class`: exact SVG class, only if it resolves to a small bounded set.
- `text_exact`: exact text node match, only if it resolves uniquely.

The executor must fail when a selector resolves to zero elements or too many
elements. It must not silently apply broad document-wide edits.

## Prohibited Edits

The recipe and executor must reject operations that:

- add, delete, rename, or retarget scientific components;
- change label text, material identity, mechanism direction, panel order,
  charge/current/force direction, or scale/proximity meaning;
- edit outside `polish/<name>.polished.svg`;
- mutate `exports/`, `build/`, source TeX, critique, accepted, or golden state;
- apply broad transforms to the full figure or a full panel unless a future
  issue adds a panel-level visual-only contract;
- rely on non-deterministic randomness.

## Execution Flow

```text
/fig_loop says ready_for_svg_polish
-> /fig_export refreshes generated SVG
-> author or agent writes svg_polish_recipe.yaml
-> recipe executor dry-run validates and prints planned changes
-> write mode creates polish/<name>.polished.svg
-> handoff scaffolder writes audit + manifest
-> before/after delta pack is generated
-> /fig_critique or /fig_loop surfaces delta review
-> /fig_status requires polished_svg FRESH for final readiness
```

## Aesthetic Delta Pack

Issue 44C should add deterministic review inputs under `polish/aesthetic_delta/`
or an equivalent ignored build area:

- `before.png`: render of `exports/<name>.svg`.
- `after.png`: render of `polish/<name>.polished.svg`.
- `diff.png` or a compact changed-region image.
- `delta_manifest.json`: source hashes, recipe hash, generated file hashes, and
  operation ids.

The host critique must answer:

- Did journal polish improve?
- Did any label/readability/spacing issue regress?
- Did any scientific semantics change?
- Does the result still match the active `aesthetic_lever_audit` route?
- Should the route remain SVG polish, return to TikZ, or require human art
  direction?

## Freshness

Recipe freshness must include:

- source SVG hash;
- recipe file hash;
- relevant `aesthetic_intent.yaml` hash when present;
- critique hash when the recipe claims to resolve critique or lever findings;
- style lock or manifest context where already included by final-artifact
  source-set hashing.

If any input changes, the recipe output and delta pack must be stale.

## Integration Points

- `svg_polish_recipe.py`: parse, validate, write, and hash recipes.
- `svg_polish_executor.py`: dry-run and write polish output.
- `svg_polish_handoff.py`: optionally consume recipe metadata when scaffolding
  audit and manifest.
- `svg_polish_manifest.py`: no schema change required for Issue 44A/B unless
  recipe hash needs to be captured. Prefer additive optional fields if needed.
- `critique_brief.py`: Issue 44C may add a before/after aesthetic delta
  section when a fresh delta pack exists.
- `critique_lint.py`: reject missing or malformed delta review only when a
  critique schema explicitly requires it.
- `status.py` / `fig_loop.py` / `fig_driver.py`: surface stale recipe, stale
  delta, and semantic backport blockers without changing accepted/golden
  policy.

## Error Handling

Controlled failures are required for:

- malformed YAML;
- wrong schema;
- fixture mismatch;
- source or target outside allowed directories;
- unknown class or action;
- selector ambiguity;
- excessive movement or opacity/stroke changes;
- missing source SVG;
- stale recipe hash;
- target overwrite without explicit `--force`;
- semantic guard missing or false.

## Backward Compatibility

Fixtures without `svg_polish_recipe.yaml` keep the current Issue 42 behavior.
Existing polished-SVG manifests remain valid. The recipe layer is opt-in and
must not make generated-export fixtures fail.

## Review Boundaries

The executor may produce a visually better SVG, but it cannot declare the
result final. Final readiness still requires:

- fresh export;
- fresh or not-required critique;
- valid polish audit and manifest;
- semantic backport not required;
- `Final artifact: polished_svg FRESH`;
- existing accepted/golden/publication gates.

## Non-Goals

- No autonomous taste decisions.
- No external editor automation.
- No broad SVG optimizer.
- No new score gate.
- No publication acceptance claim.
- No paper-wide style propagation.

## Acceptance Criteria

- The design decomposes into 44A-44E without requiring a large all-at-once
  implementation.
- The recipe contract is narrow enough that a test fixture can prove every
  supported operation.
- The executor cannot mutate generated exports or semantic sources.
- The before/after delta path can show whether polish improved or regressed the
  final artifact.
- Semantic backport remains a blocking state, not an advisory note.

## Open Risk

SVG emitted by LaTeX/dvisvgm may not have stable element ids. Issue 44A must
therefore either define a robust selector strategy for current exports or scope
the first MVP to recipe fixtures that include stable ids/classes in a copied
polished SVG. If selectors are not stable enough, 44B must stop at dry-run and
manual handoff rather than apply broad edits.
