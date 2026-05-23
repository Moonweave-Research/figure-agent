# Issue 24D: Historical Visual-Clash Regression Harness

**Date:** 2026-05-22 KST
**Status:** completed in commit `492e23a`
**Type:** deterministic regression hardening
**Parent:** `2026-05-22-issue-24-audit-gate-hardening-roadmap.md`

## What to build

Turn the Issue 21B dogfood result into deterministic lint coverage for the
historical `fig1_visual_clash_regression` fixture shape. If that regression
fixture reports the known `HV+` and `V_s` visual-clash candidates, the critique
must classify them with the expected micro-defect kinds.

## Current Problem

Issue 21B proved with host vision that:

- `VC050` / `HV+` maps to `label_backdrop_overflows_outline`;
- `VC026` / `V` and `VC027` / `s` map to
  `label_glyph_overlaps_internal_drawing`.

That proof is useful but not deterministic. Current lint can ensure every
`VC###` candidate is referenced exactly once, but it does not verify that these
known historical candidates are classified with the intended defect kind. A bad
critique could link `VC050` to an unrelated micro-defect kind and still satisfy
plain accounting.

## Acceptance Criteria

- [x] For fixture name `fig1_visual_clash_regression`, `critique_lint.py`
  rejects `VC050` / `HV+` unless the linked micro-defect kind is
  `label_backdrop_overflows_outline`.
- [x] For the same fixture, lint rejects `VC026` / `V` and `VC027` / `s` unless
  the linked micro-defect kind is `label_glyph_overlaps_internal_drawing`.
- [x] The failure category is `historical_visual_clash_regression`.
- [x] Correctly classified historical candidates pass.
- [x] Non-regression fixtures are unaffected, even if they happen to contain
  similar visual-clash ids or text.

## Implementation Notes

- The harness is deliberately scoped to the fixture name
  `fig1_visual_clash_regression`.
- It reuses existing `build/visual_clash.json` candidates and
  `micro_defects[].visual_clash_ref`.
- It does not run compile, vision, crop generation, or any external model.

## Implementation Contract

- Scope the deterministic harness to `example_dir.name ==
  "fig1_visual_clash_regression"` or `visual_clash.json.fixture ==
  "fig1_visual_clash_regression"`.
- Reuse the existing `visual_clash_ref` accounting data. Do not invent new
  schema fields.
- Do not run vision, OCR, compile, crop generation, or host LLM calls in lint.
- Do not apply this rule globally; candidate ids are stable only for the
  historical regression fixture.

## Suggested Files

- `scripts/critique_lint.py`
- `tests/test_critique_lint.py`
- `docs/superpowers/issues/2026-05-22-issue-24-audit-gate-hardening-roadmap.md`
- `docs/superpowers/issues/2026-05-22-issue-24d-historical-visual-clash-regression-harness.md`

## Verification

```bash
uv run pytest -q tests/test_critique_lint.py
uv run ruff check scripts/critique_lint.py tests/test_critique_lint.py
git diff --check
```

## Non-Goals

- No canonical figure source mutation.
- No host-vision dogfood rerun.
- No external model integration.
- No broad semantic classifier for arbitrary visual-clash candidates.
