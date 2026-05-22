# Issue 29 — Text Boundary Clash Gate

Status: implemented; pending commit

## Problem

Dogfood on `fig1_overview_v2_pair_001_vault` exposed a plugin-level audit gap: text can cross non-text figure geometry such as row boxes, panel dividers, column rules, and instrument outlines without being deterministically reported. Existing checks do not cover this:

- `check_collisions.py` compares text bbox against text bbox only.
- `check_visual_clash.py` reports local render statistics around text but has no semantic knowledge of box outlines or panel boundaries.
- `critique_lint.py` validates critique structure; it does not inspect PDF geometry.
- `/fig_critique` can only force the host LLM to inspect evidence that compile/brief provide.

The result is a class of layout defects that can survive many iterations unless a human notices them in a high-zoom screenshot.

## Scope

Implement a deterministic compile-time report for rendered PDF text crossing declared boundary geometry, then feed that report into `/fig_critique`.

In scope:

- Add `scripts/check_text_boundary_clash.py`.
- Support optional `spec.yaml.text_boundary_checks`.
- Serialize `build/text_boundary_clash.json` during `/fig_compile`.
- Add a `/fig_critique` brief section listing text-boundary candidates.
- Add micro-defect vocabulary for boundary-crossing findings.
- Add tests for geometry detection, JSON shape, strict mode, compile integration, and brief inclusion.

Out of scope:

- Inferring every TikZ line/box from source code.
- Auto-editing `.tex`.
- Changing accepted/golden/export state.
- Failing normal compile by default.
- Solving panel layout design or figure aesthetics directly.

## Boundary Spec Contract

Fixtures may declare boundaries in `examples/<name>/spec.yaml`:

```yaml
text_boundary_checks:
  - id: de_column_rule
    kind: vertical_line
    role: column_rule
    x_pdf_cm: 4.62
    y_range_pdf_cm: [0.0, 4.5]
    clearance_pt: 0.5
  - id: row2_frame_bottom
    kind: horizontal_line
    role: row_box_outline
    y_pdf_cm: 4.50
    x_range_pdf_cm: [0.0, 13.8]
    clearance_pt: 0.5
  - id: row2_box
    kind: rect
    role: row_box
    bbox_pdf_cm: [0.0, 0.0, 13.8, 4.5]
    mode: contain_text
    clearance_pt: 0.5
```

Coordinates use the existing PDF-cm convention: origin at the PDF page top-left, x rightward, y downward.

Supported boundary kinds:

- `vertical_line`: flag text whose bbox crosses or violates clearance around a vertical boundary.
- `horizontal_line`: flag text whose bbox crosses or violates clearance around a horizontal boundary.
- `rect` with `mode: contain_text`: flag text bbox outside the containing rectangle.
- `rect` with `mode: avoid_inside`: flag text bbox intersecting a forbidden rectangle.

If `text_boundary_checks` is absent, the checker writes a valid zero-candidate report and exits 0.

## Output Contract

`build/text_boundary_clash.json`:

```json
{
  "schema": "figure-agent.text-boundary-clash.v1",
  "fixture": "fig1_overview_v2_pair_001_vault",
  "render_pdf": "build/fig1_overview_v2_pair_001_vault.pdf",
  "source": "spec.yaml:text_boundary_checks",
  "candidates": [
    {
      "id": "TB001",
      "kind": "text_crosses_vertical_boundary",
      "text": "polymer",
      "boundary_id": "de_column_rule",
      "boundary_role": "column_rule",
      "bbox_pt": [120.0, 40.0, 150.0, 52.0],
      "boundary_pt": {"x": 131.0, "y_range": [0.0, 180.0]},
      "clearance_pt": 0.5
    }
  ],
  "total": 1
}
```

Candidate ids must be deterministic (`TB001`, `TB002`, ...), sorted by boundary id and text bbox.

## Critique Contract

`critique_brief.py` must emit:

```markdown
## Text Boundary Clash Candidates (from check_text_boundary_clash.py)
```

The host LLM must review every listed `TB###` candidate and either:

- create/link a `micro_defects` entry via `text_boundary_ref`, or
- explicitly justify `status: accept_simplification`.

New micro-defect kinds:

- `label_crosses_panel_boundary`
- `label_crosses_column_rule`
- `label_overflows_row_box`

## Acceptance Criteria

- `check_text_boundary_clash.py` detects vertical, horizontal, containment, and forbidden-rect boundary violations from rendered text bboxes.
- `compile.sh` writes `build/text_boundary_clash.json` after every successful compile.
- Normal compile remains report-only; `FIGURE_AGENT_STRICT=1` fails when candidates are present.
- `critique_brief.py` includes the new section when the report exists and contains candidates.
- `critique_schema_vocab.py` accepts the new micro-defect kinds.
- Tests cover checker behavior, JSON contract, strict mode, compile integration, brief inclusion, and schema vocabulary acceptance.

## Review Questions

- Can stale or missing boundary reports silently hide candidates?
- Does the checker preserve current report-only dogfood ergonomics?
- Is the spec-based coordinate contract explicit enough for fixture authors?
- Does the implementation avoid broad TikZ parsing and stay deterministic?

## Implementation Notes

- `compile.sh` now writes `build/text_boundary_clash.json` after visual-clash detection.
- Missing or malformed `text_boundary_clash.json` is surfaced by audit evidence summary for current schema critiques, so `/fig_status`, `/fig_driver`, and `/fig_loop` cannot silently proceed with stale audit evidence.
- `critique_lint.py` requires every `TB###` candidate in the report to be represented once through `micro_defects[].text_boundary_ref`.
- `build/text_boundary_clash.json` participates in the critique input hash, so candidate changes make existing critiques stale.
- Normal compile remains report-only; `FIGURE_AGENT_STRICT=1` makes text-boundary candidates fail the compile alongside existing strict collision/clash checks.
