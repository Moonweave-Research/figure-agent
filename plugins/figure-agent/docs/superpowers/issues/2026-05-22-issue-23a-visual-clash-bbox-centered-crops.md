# Issue 23A: Visual-Clash BBox-Centered Crops

**Date:** 2026-05-22 KST
**Status:** planned
**Type:** audit visibility hardening
**Parent:** `2026-05-22-issue-23-zoom-and-reference-calibrated-audit-roadmap.md`

## What to build

Generate deterministic zoom crops centered on each `build/visual_clash.json`
candidate and include them in `/fig_critique` brief output. The goal is to show
the host LLM the exact local geometry behind each `VC###` candidate instead of
expecting it to find sub-millimeter defects in full-render, panel, or quadrant
crops.

The crop layer should be report-only. It must not change source, accepted,
golden, export, or critique state by itself.

## Current Context

Already implemented:

- `check_visual_clash.py` serializes stable `VC###` candidates to
  `build/visual_clash.json`.
- `critique_zoom_crops.py` generates full-render quadrants, panel quadrants,
  panel 4x4 sub-quadrants, optional instrument crops, and print-scale images.
- `critique_brief.py` lists visual-clash candidates and high-zoom crops.

Missing:

- no crop is centered specifically on a visual-clash `bbox_px`;
- the brief lists candidate coordinates but does not show a local image crop
  for each candidate.

## Acceptance Criteria

- [ ] For every visual-clash candidate in `build/visual_clash.json`, the crop
  pack emits a deterministic image under `build/audit_crops/visual_clash/`.
- [ ] Each crop id preserves the candidate id, for example `VC050_HV_`.
- [ ] Crops include context padding around `bbox_px` and clamp to the render
  bounds.
- [ ] Tiny candidates are upscaled to a readable minimum width.
- [ ] Crop ordering is deterministic by candidate id.
- [ ] `/fig_critique` brief lists every visual-clash crop under the existing
  high-zoom or visual-clash section.
- [ ] Missing or malformed `visual_clash.json` degrades gracefully to the
  current behavior.
- [ ] Tests cover crop generation, bbox clamping, deterministic naming, and
  brief inclusion.

## Suggested Files

- `scripts/critique_zoom_crops.py`
- `scripts/critique_brief.py`
- `tests/test_critique_zoom_crops.py`
- `tests/test_critique_brief.py`

## Verification

```bash
uv run pytest -q tests/test_critique_zoom_crops.py tests/test_critique_brief.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Non-Goals

- No new visual-clash detector.
- No auto-classification of candidates into true/false positives.
- No requirement that every candidate is a defect.
- No mutation of `critique.md`.
