# Issue 12B: Micro-Defect Schema v1.4

**Date:** 2026-05-20 KST
**Status:** completed in commit `d21e395`
**Type:** AFK schema/docs/tests
**Parent:** `2026-05-20-issue-12-critical-visual-audit-gaps.md`
**Blocked by:** Issue 12A

## What To Build

Advance the critique contract so small but publication-relevant defects have a
first-class schema surface. The current broad finding categories are too coarse
for line-through-label, arrow-tip fusion, floating semantic cues, and
drawing-order suspicion.

## Acceptance Criteria

- [x] Brief output advances to `figure-agent.critique.v1.4`.
- [x] Rubric version advances to `figure-agent.critique-rubric.v1.4`.
- [x] The output schema includes:

```yaml
micro_defects:
  - id: M001
    crop: examples/<name>/build/audit_crops/<crop>.png
    kind: line_crosses_label | wire_crosses_label | arrow_tip_fused | label_target_detached | floating_semantic_cue | drawing_order_suspect | print_scale_unreadable
    severity: BLOCKER | MAJOR | MINOR | NIT
    observation: "<visible micro-defect>"
    linked_finding_id: "<P001/C001 or empty when accepted simplification>"
    status: open | resolved | accept_simplification
```

- [x] v1.4 validation rejects missing or malformed `micro_defects`.
- [x] `BLOCKER` and `MAJOR` micro-defects must link to a normal finding or
  explicitly use `status: accept_simplification`.
- [x] v1.3 critiques remain loadable/scaffoldable.
- [x] `/fig_loop`, `/fig_driver`, `/fig_export`, accepted, golden, and final
  artifact behavior do not change in this slice.

## Implementation Notes

- `figure-agent.critique.v1.4` is intentionally additive over v1.3.
- `micro_defects: []` is valid after explicit crop inspection when no crop-scale
  defect is visible.
- `BLOCKER` and `MAJOR` micro-defects must either reference an existing
  panel/top-level finding id through `linked_finding_id` or use
  `status: accept_simplification`.
- `/fig_loop` treats v1.4 as v1.3 plus micro-defects for quality-axis and
  top-tier summary visibility; the micro-defect list is not release-gating by
  itself in this slice.

## Verification

- `uv run pytest -q tests/test_critique_schema_validator.py tests/test_critique_brief.py tests/test_fig_loop.py tests/test_status.py` — 229 passed.
- `uv run pytest -q` — 721 passed, 1 skipped, 1 xfailed.
- `uv run ruff check ...` — all checks passed.
- `git diff --check` — clean.
- `claude plugin validate .claude-plugin/plugin.json` — passed.
- `claude plugin validate .` — passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json` — passed.

## Blocked By

- Issue 12A, because the schema should point to actual crop evidence rather
  than prose-only screenshots.
