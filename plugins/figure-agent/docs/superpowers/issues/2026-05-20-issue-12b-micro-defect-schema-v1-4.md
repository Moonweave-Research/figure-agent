# Issue 12B: Micro-Defect Schema v1.4

**Date:** 2026-05-20 KST
**Status:** open
**Type:** AFK schema/docs/tests
**Parent:** `2026-05-20-issue-12-critical-visual-audit-gaps.md`
**Blocked by:** Issue 12A

## What To Build

Advance the critique contract so small but publication-relevant defects have a
first-class schema surface. The current broad finding categories are too coarse
for line-through-label, arrow-tip fusion, floating semantic cues, and
drawing-order suspicion.

## Acceptance Criteria

- [ ] Brief output advances to `figure-agent.critique.v1.4`.
- [ ] Rubric version advances to `figure-agent.critique-rubric.v1.4`.
- [ ] The output schema includes:

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

- [ ] v1.4 validation rejects missing or malformed `micro_defects`.
- [ ] `BLOCKER` and `MAJOR` micro-defects must link to a normal finding or
  explicitly use `status: accept_simplification`.
- [ ] v1.3 critiques remain loadable/scaffoldable.
- [ ] `/fig_loop`, `/fig_driver`, `/fig_export`, accepted, golden, and final
  artifact behavior do not change in this slice.

## Blocked By

- Issue 12A, because the schema should point to actual crop evidence rather
  than prose-only screenshots.

