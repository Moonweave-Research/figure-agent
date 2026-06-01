# Issue 63E - Unintended-Visible Anomaly Audit

Status: completed; merged to main

Depends on: Issue 63A reference-learning contract

## Problem

Current critique contracts ask many forms of "is the intended element present,
legible, and correctly linked?" They are weaker at asking the inverse question:
"is there anything visible that was not intended?"

This gap matters for spurious bonds, accidental grouping, phantom lines,
unintended components, stray visual hierarchy, or reference-inspired artifacts
that the figure did not mean to introduce.

## Goal

Add explicit anomaly accountability to high-zoom and reference-calibrated
critique so every required crop is checked for unintended visible artifacts.

## Scope

In scope:

- Add a mandatory crop-audit question:
  - `unintended_visible_anomaly: none | present | uncertain`
- Require a short rationale for `present` and `uncertain`.
- Require `present` anomalies to link to a finding, micro-defect, or explicit
  accept-simplification decision.
- Include examples in the critique brief:
  - stray bond;
  - unintended line continuation;
  - accidental component grouping;
  - misleading reference transfer;
  - phantom boundary or texture.
- Preserve legacy critique parsing.

Out of scope:

- Automatic visual anomaly detection.
- Provider API calls.
- Patching source.
- Rejecting every decorative artifact without author-intent context.

## Acceptance

- [x] New critiques must account for unintended visible anomalies in required
  crop audit entries.
- [x] Missing anomaly accounting fails lint for the new schema.
- [x] `present` or `uncertain` anomalies cannot silently pass.
- [x] Legacy critiques remain parseable through legacy paths.
- [x] Tests cover missing field, present-without-link,
  uncertain-with-rationale, none-with-rationale, and legacy compatibility.

## Implementation Notes

- Added critique schema `figure-agent.critique.v1.13` and rubric
  `figure-agent.critique-rubric.v1.13` for `reference_learning` opt-in
  critiques.
- `crop_audit_log` entries in v1.13 must include:
  - `unintended_visible_anomaly: none | present | uncertain`
  - `anomaly_rationale`
  - `anomaly_link`
- `present` anomalies must link to a finding id, `micro_defects[].id`, or
  `accept_simplification:<reason>`.
- `uncertain` anomalies require rationale but do not force a false defect link.
- Legacy v1.12 and older critiques remain parseable without anomaly fields.
- `critique_brief.py` now asks the inverse crop question and gives examples:
  stray bond, unintended line continuation, accidental component grouping,
  misleading reference transfer, and phantom boundary or texture.

## Verification

- `uv run pytest -q tests/test_critique_schema_validator.py::test_validate_critique_schema_accepts_v1_13_crop_anomaly_accounting tests/test_critique_schema_validator.py::test_validate_critique_schema_rejects_v1_13_missing_anomaly_field tests/test_critique_schema_validator.py::test_validate_critique_schema_rejects_v1_13_present_anomaly_without_link tests/test_critique_schema_validator.py::test_validate_critique_schema_accepts_v1_13_uncertain_anomaly_with_rationale tests/test_critique_schema_validator.py::test_validate_critique_schema_accepts_v1_13_none_anomaly_with_rationale tests/test_critique_schema_validator.py::test_validate_critique_schema_keeps_v1_12_legacy_without_anomaly_accounting tests/test_critique_brief.py::test_critique_brief_includes_unintended_visible_anomaly_contract tests/test_critique_brief.py::test_critique_brief_includes_reference_learning_contract tests/test_critique_lint.py::test_lint_critique_rejects_v1_13_missing_unintended_visible_anomaly`
  - 9 passed.
- `uv run pytest -q tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_critique_brief.py tests/test_quality_manifest.py`
  - 243 passed.
- `uv run ruff check scripts/critique_brief.py scripts/critique_lint.py scripts/critique_schema_validator.py scripts/critique_schema_vocab.py scripts/quality_manifest.py tests/test_critique_brief.py tests/test_critique_lint.py tests/test_critique_schema_validator.py tests/test_quality_manifest.py`
  - All checks passed.

## Review Questions

1. Does the contract catch unintended artifacts without forcing over-reporting?
2. Can host LLMs answer the question reliably from zoom crops?
3. Are anomaly findings tied back to actionable evidence?
4. Does this reduce reference-copy accidents introduced by 63A/63B work?
