# Issue 23D: Reference-Calibrated Scoring Guidance

**Date:** 2026-05-22 KST
**Status:** planned
**Type:** advisory score calibration
**Parent:** `2026-05-22-issue-23-zoom-and-reference-calibrated-audit-roadmap.md`
**Blocked by:** Issue 23C

## What to build

Extend the journal-grade assessment prompt and loop surfacing so advisory
scores can cite the reference-calibration pack. The purpose is not to make
scores authoritative. The purpose is to make scores explain what reference
class and visual ambition they are calibrated against.

## Required Policy

- Scores remain advisory fresh re-audit diagnostics.
- Scores never unlock export, release, acceptance, golden, final artifact, or
  human gates.
- A high score cannot override non-passing `quality_axes`, unresolved
  `top_tier_audit`, unresolved `editorial_art_direction`, or crop-audit
  uncertainty.
- Scoring can go down after a patch if the current artifact regresses.

## Proposed Critique Additions

Inside `journal_grade_assessment`, require reference-calibrated rationale when
a reference pack exists:

```yaml
journal_grade_assessment:
  reference_calibration:
    reference_pack_hash: sha256:<hash>
    reference_class: mechanism_schematic
    visual_ambition: high_impact_candidate
    score_basis: current_artifact_vs_pack
    limiting_reference_traits:
      - T003
    rationale: "<why the score follows from the reference pack>"
```

Exact names can change, but the assessment must preserve the idea that scores
cite the reference pack rather than generic taste.

Expected schema policy:

- If Issue 23B already introduced `figure-agent.critique.v1.8`, extend that
  schema only when the v1.8 contract already includes reference-calibration
  scoring hooks.
- Otherwise introduce the next critique schema version and matching rubric
  version.
- Do not mutate v1.7 score semantics in place.

## Acceptance Criteria

- [ ] `/fig_critique` brief explains how to score against a reference pack when
  one exists.
- [ ] Reference-calibrated scoring is introduced through an explicit schema /
  rubric version policy.
- [ ] Validator accepts complete reference-calibration scoring metadata.
- [ ] Validator rejects partial reference-calibration scoring metadata.
- [ ] `fig_loop` surfaces compact reference-calibration score metadata.
- [ ] Scores remain advisory and cannot change release action selection.
- [ ] Tests cover complete metadata, partial metadata rejection, loop surfacing,
  and no release-gate effect.

## Suggested Files

- `scripts/critique_brief_sections.py`
- `scripts/critique_schema_validator.py`
- `scripts/fig_loop_assessments.py`
- `scripts/fig_driver.py`
- `tests/test_critique_schema_validator.py`
- `tests/test_fig_loop.py`
- `tests/test_fig_driver.py`

## Verification

```bash
uv run pytest -q tests/test_critique_schema_validator.py tests/test_fig_loop.py tests/test_fig_driver.py
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Non-Goals

- No learned scoring model.
- No strict mapping from score ranges to journal acceptance.
- No score-driven release gate.
- No automatic target-journal policy decision.
