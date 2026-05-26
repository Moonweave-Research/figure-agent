# Issue 51 — Label-Path Proximity Gate

Status: implemented; pending commit

## Problem

Dogfood on `fig1_overview_v2_pair_001_vault` exposed a remaining audit gap:
labels can be visually too close to nearby semantic lines or curves without
actually intersecting the rendered text bbox. Two concrete misses were:

- `mobility edge` visually stacked on a dashed reference line while the glyph
  bbox and line endpoint did not overlap.
- `shallow` visually crowded by a deep escape S-curve passing just below the
  label baseline.

`check_visual_clash.py` is intentionally local and bbox/raster-stat based. It
uses a small ring around text bboxes, so expanding that detector would create
many false positives from decorative fields and dense schematic marks. This
gap needs a separate report-only proximity layer.

## Scope

Add a deterministic label-path proximity report that fixture specs can use for
critical semantic lines and curves.

In scope:

- Add `scripts/check_label_path_proximity.py`.
- Support optional `spec.yaml.label_path_proximity_checks`.
- Serialize `build/label_path_proximity.json` during `/fig_compile`.
- Generate LP-centered audit crops under `build/audit_crops/label_path/` when
  the report has candidates and the compiled PDF is available.
- Add a `/fig_critique` brief section listing `LP###` candidates.
- Add micro-defect vocabulary for label/path proximity findings.
- Include the report in critique input hashing when present.
- Require accounting in `micro_defects[].label_path_ref` when a current critique
  schema sees a present report with candidates.

Out of scope:

- Parsing arbitrary TikZ paths or PDF drawing streams.
- Changing normal compile from report-only to fail-by-default.
- Auto-editing `.tex`.
- Mutating accepted/golden/export state.
- Requiring historical builds to have `label_path_proximity.json` before the
  next compile.

## Spec Contract

Fixtures may declare checks:

```yaml
label_path_proximity_checks:
  - id: panel_c_mobility_edge_reference
    kind: horizontal_line
    role: reference_line
    y_pdf_cm: 2.50
    x_range_pdf_cm: [12.0, 15.0]
    clearance_pt: 2.0
    text_phrases:
      - id: mobility_edge
        words: [mobility, edge]
  - id: panel_c_deep_escape_curve
    kind: polyline
    role: semantic_curve
    points_pdf_cm:
      - [12.0, 2.2]
      - [12.4, 2.5]
      - [12.7, 2.7]
    clearance_pt: 3.0
    text_allowlist: [shallow]
```

Coordinates use the existing PDF-cm convention: origin at the PDF page top-left,
x rightward, y downward.

Supported path kinds:

- `horizontal_line`
- `vertical_line`
- `polyline`

Candidate ids are deterministic (`LP001`, `LP002`, ...), sorted by path id and
text bbox. Normal compile remains report-only; `FIGURE_AGENT_STRICT=1` fails
when candidates are present.

## Output Contract

`build/label_path_proximity.json`:

```json
{
  "schema": "figure-agent.label-path-proximity.v1",
  "fixture": "fig1_overview_v2_pair_001_vault",
  "render_pdf": "build/fig1_overview_v2_pair_001_vault.pdf",
  "source": "spec.yaml:label_path_proximity_checks",
  "candidates": [
    {
      "id": "LP001",
      "kind": "label_stacked_on_reference_line",
      "text": "mobility edge",
      "path_id": "panel_c_mobility_edge_reference",
      "path_role": "reference_line",
      "bbox_pt": [443.4, 53.4, 491.8, 61.0],
      "path_pt": {"kind": "horizontal_line", "y": 56.6, "x_range": [430.0, 500.0]},
      "clearance_pt": 2.0,
      "distance_pt": 1.2
    }
  ],
  "total": 1
}
```

## Critique Contract

`critique_brief.py` emits:

```markdown
## Label-Path Proximity Candidates (from check_label_path_proximity.py)
```

The host LLM must review every `LP###` candidate and either:

- create/link a `micro_defects` entry via `label_path_ref`, or
- explicitly justify `status: accept_simplification`.

New micro-defect kinds:

- `label_stacked_on_reference_line`
- `label_curve_near_label`
- `label_path_near_miss`

When `build/audit_crops/manifest.json` contains matching `label_path_crop`
entries, each candidate line includes its LP-centered crop path, for example:

```markdown
- id=`LP001` ... crop=`build/audit_crops/label_path/LP001_mobility_edge.png`
```

Those crop ids are part of the normal crop-read accountability path through
`crop_audit_log`.

## Acceptance Criteria

- The checker detects label proximity to horizontal lines, vertical lines, and
  polylines from rendered PDF text bboxes.
- The checker writes zero-candidate JSON when no spec checks exist.
- `compile.sh` writes `build/label_path_proximity.json` after successful
  compile.
- `critique_brief.py` includes the new section when the report has candidates.
- LP candidates produce deterministic bbox-centered crops and manifest entries
  when PDF page sizing is available.
- `critique_lint.py` rejects missing, duplicate, or unknown `label_path_ref`
  accounting when a present report has candidates.
- `quality_manifest.py` includes the report in critique freshness when present.
- Normal compile stays report-only; strict mode fails on candidates.

## Review Questions

- Does the checker avoid global visual-clash threshold expansion?
- Does the spec-based contract make the non-inferred scope clear?
- Can a present report with candidates be silently ignored by `/fig_critique`?
- Does the compatibility path avoid breaking legacy builds before recompile?
