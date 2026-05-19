# Issue 9B: Numeric Quality Score Calibration

**Date:** 2026-05-19 KST
**Status:** implemented as advisory-only numeric score contract; verification passed on branch `codex/issue-9b-numeric-quality-score-calibration`
**Parent:** Issue 9
**Type:** HITL

## What to build

After Issue 9C has dogfood evidence from real host-LLM critique runs, decide
whether numeric quality scores are worth adding. If adopted, add advisory
non-monotonic `overall_score` and `sub_scores` to
`journal_grade_assessment`.

Numeric scores must remain fresh re-audit scores. They must be allowed to fall
when a later patch introduces a new defect or damages visual balance.

## Acceptance criteria

- [ ] At least 5 real loop runs show that level-only assessment is useful but
  insufficient.
- [ ] Score calibration policy is documented before implementation.
- [ ] Scores cannot override blocker precedence.
- [ ] Scores are not cumulative progress meters.
- [ ] Tests cover score decrease after regression.

## Preconditions

- [x] Issue 9A implemented.
- [x] Issue 9C reached N=5 valid v1.2 critique-grounded runs.
- [x] Human calibration decision: proceed with advisory-only scores, no score-driven gates.

## Implementation Policy

- Numeric scores are optional v1.2 `journal_grade_assessment` fields.
- If any score field appears, `overall_score`, complete `sub_scores`, and
  `score_rationale` are required.
- Scores are fresh re-audit diagnostics, not cumulative progress meters.
- Scores may decrease after a patch.
- Scores cannot override `quality_axes`, `benchmark_level`, stale/freshness
  gates, human gates, export gates, final-artifact gates, or accepted/golden
  gates.

## Out of scope

- Objective Nature/Science acceptance claims.
- Learned quality model.
- External API or journal corpus scraping.
