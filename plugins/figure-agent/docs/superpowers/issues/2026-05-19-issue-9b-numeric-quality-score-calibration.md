# Issue 9B: Numeric Quality Score Calibration

**Date:** 2026-05-19 KST
**Status:** deferred
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

## Blocked by

- Issue 9A.
- Issue 9C fresh re-audit dogfood evidence.
- Human calibration decision after dogfood evidence.

## Out of scope

- Objective Nature/Science acceptance claims.
- Learned quality model.
- External API or journal corpus scraping.
