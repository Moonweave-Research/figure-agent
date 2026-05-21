# Visual Clash Evidence Integration Design

**Date:** 2026-05-21 KST
**Status:** approved for implementation
**Parent issue:** `../issues/2026-05-21-issue-20-visual-clash-evidence-integration.md`

## Problem

`examples/fig1_overview_v2_pair_001_vault` exposed a structural QA failure:
`check_visual_clash.py` emitted relevant WARN lines for intra-instrument label
overflow and text-on-fill risk, but the pipeline left those warnings in compile
logs. `/fig_critique` did not receive a structured candidate list, high-zoom
crops were too coarse for small instrument boxes, and the micro-defect taxonomy
had no precise kind for label backdrops or glyphs failing inside an enclosing
instrument box.

The failure is not that the checker missed all evidence. The failure is that
the evidence was not promoted into the critique/adjudication loop.

## Goals

1. Preserve WARN-by-default authoring ergonomics.
2. Make visual clash candidates a first-class critique input.
3. Extend the micro-defect contract for instrument-box label failures.
4. Increase crop resolution for small apparatus regions without requiring
   hand-authored instrument metadata.
5. Add a CI-facing visual clash budget so new fixtures cannot silently ship
   unexplained warning floods.

## Non-Goals

- Do not edit `examples/fig1_overview_v2_pair_001_vault/*.tex`.
- Do not auto-promote visual clash WARNs to local compile failures outside
  strict/CI mode.
- Do not add automatic vision API calls.
- Do not implement a heuristic instrument detector in this slice.
- Do not remove or rename existing `micro_defect.kind` values.

## Design

### 20A: Critique schema v1.6 micro-defect taxonomy

Add schema `figure-agent.critique.v1.6` as a backward-compatible extension of
v1.5. The new schema keeps every v1.5 field and adds two allowed
`micro_defects[].kind` values:

- `label_backdrop_overflows_outline`: a label fill/backdrop rectangle extends
  outside its enclosing instrument-box outline.
- `label_glyph_overlaps_internal_drawing`: label glyphs or their backdrop cross
  internally drawn elements of the same enclosing box, such as a display
  rectangle, axis line, meter needle, or internal separator.

`BLOCKER` and `MAJOR` items of these kinds follow the existing micro-defect
rule: they must link to a normal finding via `linked_finding_id` unless the
item uses `status: accept_simplification` with an explicit observation.

### 20B: Denser high-zoom crops

`critique_zoom_crops.py` will preserve current full-render 2x2 and print-scale
outputs, then add a second high-zoom layer for panel crops:

- If `spec.yaml` declares `panels[].instruments[]`, create deterministic
  instrument crops named `panel_<panel_id>_instr_<name>.png`.
- If no instruments are declared for a panel, create a 4x4 sub-quadrant grid
  named `panel_<panel_id>_sNN.png`.

Instrument crop metadata uses `bbox_pdf_cm` in the same coordinate convention
as panel bbox declarations. To keep implementation deterministic and
non-magic, this slice does not guess apparatus boxes from pixels.

### 20C: Visual clash JSON as critique input

`check_visual_clash.py` will support `--json-out <path>` and emit
`build/visual_clash.json` from `compile.sh` after every successful PDF render.
The JSON shape is:

```json
{
  "fixture": "name",
  "render_pdf": "build/name.pdf",
  "candidates": [
    {
      "kind": "text_on_fill",
      "text": "HV+",
      "bbox_px": [1750, 1409, 1871, 1466],
      "metric": {"dark": 0.041, "edge": 0.006},
      "tex_lines": null
    }
  ],
  "total": 1
}
```

The compile footer should point to the JSON report rather than making the raw
count the dominant signal. `critique_brief.py` reads this file when present and
adds `## Visual Clash Candidates (from check_visual_clash.py)`. The host LLM is
required to inspect each candidate and either link it to a `micro_defects` item
or justify `accept_simplification`.

Candidate order is deterministic: kind, text, bbox.

### 20D: CI visual clash budget

Add a budget checker that reads `build/visual_clash.json` and enforces
`spec.yaml.visual_clash_cap`. Missing cap defaults to 0. Existing fixtures may
carry a higher cap, but cap > 0 is not a readiness claim; the critique must
still account for candidates through the 20C brief section.

The CI guardrail runs in strict or explicit budget mode. Local authoring
remains report-only unless `FIGURE_AGENT_STRICT=1` or the budget checker is
invoked.

## Acceptance

- v1.6 critiques accept the two new micro-defect kinds.
- v1.6 critiques reject unknown micro-defect kinds.
- `BLOCKER`/`MAJOR` new-kind micro-defects without a linked finding fail unless
  marked `accept_simplification`.
- `/fig_critique` brief includes the new v1.6 schema text and examples.
- Panel audit crops include instrument crops when instruments are declared and
  4x4 sub-quadrants otherwise.
- `bash scripts/compile.sh examples/<name>/<name>.tex` writes
  `examples/<name>/build/visual_clash.json`.
- `/fig_critique` brief includes a deterministic Visual Clash Candidates
  section sourced from `visual_clash.json`.
- CI/budget checker fails when `visual_clash.json.total` exceeds
  `visual_clash_cap`.

## Verification

Targeted:

```bash
uv run pytest -q tests/test_critique_schema_vocab.py tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_critique_brief.py tests/test_critique_zoom_crops.py tests/test_strict_mode.py
```

Full:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

