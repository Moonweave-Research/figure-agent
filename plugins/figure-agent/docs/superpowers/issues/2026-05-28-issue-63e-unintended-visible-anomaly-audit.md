# Issue 63E - Unintended-Visible Anomaly Audit

Status: proposed

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

- New critiques must account for unintended visible anomalies in required crop
  audit entries.
- Missing anomaly accounting fails lint for the new schema.
- `present` or `uncertain` anomalies cannot silently pass.
- Legacy critiques remain parseable through legacy paths.
- Tests cover missing field, present-without-link, uncertain-with-rationale,
  none-with-rationale, and legacy compatibility.

## Review Questions

1. Does the contract catch unintended artifacts without forcing over-reporting?
2. Can host LLMs answer the question reliably from zoom crops?
3. Are anomaly findings tied back to actionable evidence?
4. Does this reduce reference-copy accidents introduced by 63A/63B work?
