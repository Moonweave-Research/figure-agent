# Issue 30 — Text Boundary Spec Helper

Status: completed in branch `codex/boundary-spec-helper`

## Problem

Issue 29 added deterministic text-vs-boundary clash detection, but fixtures only benefit when `spec.yaml.text_boundary_checks` is present. Writing those checks by hand is verbose and error-prone. In real authoring sessions, the operator usually thinks in higher-level layout terms:

- "Row 2 is this containing box."
- "The D/E separator is this vertical column rule."
- "This meter display rectangle is forbidden for label glyphs."

The plugin should provide a narrow helper that turns those author-facing layout declarations into the exact `text_boundary_checks` contract consumed by `check_text_boundary_clash.py`.

## Scope

Add `scripts/text_boundary_spec_helper.py`.

In scope:

- Read optional `spec.yaml.text_boundary_layout`.
- Generate deterministic `text_boundary_checks`.
- Print the generated YAML by default.
- Write the generated checks back into `spec.yaml` only with explicit `--write`.
- Validate malformed layout input with controlled errors.
- Add focused tests.

Out of scope:

- Parsing TikZ source to infer boundaries automatically.
- Editing `.tex`.
- Guessing boundaries from raster images.
- Reformatting existing specs except under explicit `--write`.
- Running compile or critique.

## Layout Contract

Fixture authors may add:

```yaml
text_boundary_layout:
  clearance_pt: 0.5
  row_boxes:
    - id: row2
      bbox_pdf_cm: [0.0, 0.0, 13.8, 4.5]
  column_rules:
    - id: de
      x_pdf_cm: 4.62
      y_range_pdf_cm: [0.0, 4.5]
  horizontal_rules:
    - id: row2_bottom
      y_pdf_cm: 4.5
      x_range_pdf_cm: [0.0, 13.8]
      role: panel_boundary
  forbidden_rects:
    - id: vs_meter_display
      bbox_pdf_cm: [8.08, 3.58, 9.00, 4.05]
      role: instrument_internal_drawing
```

The helper generates:

- `row_boxes[]` -> `rect` / `mode: contain_text` / `role: row_box`
- `column_rules[]` -> `vertical_line` / `role: column_rule`
- `horizontal_rules[]` -> `horizontal_line` / default `role: panel_boundary`
- `forbidden_rects[]` -> `rect` / `mode: avoid_inside`

Generated ids are stable:

- `<id>_contain_text`
- `<id>_column_rule`
- `<id>_horizontal_rule`
- `<id>_avoid_inside`

## CLI Contract

```bash
uv run python3 scripts/text_boundary_spec_helper.py examples/<name>
uv run python3 scripts/text_boundary_spec_helper.py examples/<name> --write
```

Default output is a YAML snippet:

```yaml
text_boundary_checks:
  - id: row2_contain_text
    kind: rect
    role: row_box
    bbox_pdf_cm: [0.0, 0.0, 13.8, 4.5]
    mode: contain_text
    clearance_pt: 0.5
```

`--write` replaces `spec.yaml.text_boundary_checks` with the generated checks. Existing manually-authored checks are intentionally replaced, not merged, so repeated runs are deterministic.

## Acceptance Criteria

- Helper generates row-box containment, column-rule, horizontal-rule, and forbidden-rect checks.
- Helper applies layout-level `clearance_pt` and allows item-level overrides.
- Malformed `text_boundary_layout` fails with a controlled error and exit code 2.
- `--write` updates `spec.yaml.text_boundary_checks` deterministically.
- Tests cover generation, default printing, write mode, malformed input, and no-layout behavior.

## Review Questions

- Does this stay narrow enough to avoid unreliable TikZ parsing?
- Does it make Issue 29 usable without weakening the explicit spec contract?
- Does `--write` have predictable behavior for repeated runs?
