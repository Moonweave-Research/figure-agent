# Issue 23B: Crop-Read Accountability

**Date:** 2026-05-22 KST
**Status:** planned
**Type:** critique evidence completeness hardening
**Parent:** `2026-05-22-issue-23-zoom-and-reference-calibrated-audit-roadmap.md`
**Blocked by:** Issue 23A crop-pack manifest

## What to build

Add a structured critique output surface that accounts for required zoom,
print-scale, and visual-clash crops. The host LLM must explicitly say whether
each required crop was inspected and whether it produced a defect, no defect,
or uncertainty.

This closes the gap where the brief can provide crops but the host critique can
silently ignore them.

This slice must consume the crop-pack manifest produced by Issue 23A. Do not
derive the required crop list from loose files under `build/audit_crops/`,
because stale crop files can survive between builds.

## Proposed Output Contract

Add a future schema field, for example:

```yaml
crop_audit_log:
  - crop_id: VC050
    path: build/audit_crops/visual_clash/VC050_HV_.png
    source: visual_clash:VC050
    inspected: true
    verdict: defect | no_defect | uncertain
    linked_micro_defect_id: M050
    rationale: "<local geometry reason>"
```

Exact field names can change at implementation time, but the contract must
preserve these semantics:

- every required crop is named;
- every required crop has a verdict;
- defect verdicts link to `micro_defects`;
- uncertain verdicts remain visible to `/fig_loop`;
- empty or missing crop-accounting output is invalid when required crops exist.

Expected schema policy:

- Introduce a new critique schema, expected to be
  `figure-agent.critique.v1.8`.
- Introduce the matching rubric version, expected to be
  `figure-agent.critique-rubric.v1.8`.
- Keep v1.7 and older critiques parseable through the existing legacy paths;
  do not mutate v1.7 in place.

## Acceptance Criteria

- [ ] `/fig_critique` brief requires a crop accountability block.
- [ ] New crop-accountability requirements are gated behind a new critique
  schema/rubric version rather than in-place mutation of v1.7.
- [ ] Validator/lint rejects missing crop-accounting output when required crops
  exist.
- [ ] Validator/lint rejects crop ids not present in the Issue 23A crop-pack
  manifest.
- [ ] Validator/lint rejects missing crop ids from the Issue 23A crop-pack
  manifest.
- [ ] `defect` crop verdicts require a linked `micro_defects[].id`.
- [ ] `uncertain` crop verdicts are surfaced as not silently passing.
- [ ] Legacy critiques without crop accountability remain parseable only under
  their legacy schema.
- [ ] Tests cover complete accounting, missing crop, unknown crop id, defect
  without link, and legacy compatibility.

## Suggested Files

- `scripts/critique_brief.py`
- `scripts/critique_schema_validator.py`
- `scripts/critique_lint.py`
- `scripts/fig_loop_assessments.py`
- `tests/test_critique_brief.py`
- `tests/test_critique_schema_validator.py`
- `tests/test_critique_lint.py`
- `tests/test_fig_loop.py`

## Verification

```bash
uv run pytest -q tests/test_critique_brief.py tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_fig_loop.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Non-Goals

- No claim that crop-accounting proves a human or model literally looked at the
  pixels.
- No visual model integration.
- No release gate based only on crop-accounting scores.
