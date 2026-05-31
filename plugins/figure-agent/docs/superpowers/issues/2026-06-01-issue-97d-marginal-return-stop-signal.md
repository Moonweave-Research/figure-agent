# Issue 97D - Marginal-Return Stop Signal

Status: implemented as additive `ready_improvement_summary.marginal_return_summary`

Type: loop UX, ready improvement closeout

Parent:

- Issue 97 - Top-Tier Aesthetic Edge-Case Audit Roadmap

## Problem

After blockers are gone, repeated polish loops can continue indefinitely. The
plugin now surfaces optional improvement candidates, but it does not yet say
when the remaining gains are too small or too subjective to justify more loops.

## Goal

Add a read-only marginal-return summary that helps the operator stop:

- how many optional candidates remain;
- highest expected gain;
- highest regression risk;
- whether further polish should continue, stop, or require human art direction;
- what evidence would justify reopening the loop.

## Implementation

Implemented inside `scripts/ready_improvement.py` as an additive nested summary
under `ready_improvement_summary`:

```yaml
ready_improvement_summary:
  marginal_return_summary:
    schema: figure-agent.marginal-return-summary.v1
    state: continue | stop_recommended | needs_human_art_direction | not_ready
    optional_candidate_count: <int>
    highest_expected_gain: none | low | medium | high
    highest_regression_risk: low | medium | high | needs_human
    reason: "<structured reason>"
    reopen_condition: "<what evidence would justify another loop>"
```

The summary consumes the already-computed optional candidates. It does not
create a second route selector, does not edit source/SVG/export state, and does
not change release readiness.

## Expected Contract

```yaml
marginal_return_summary:
  state: continue | stop_recommended | needs_human_art_direction | not_ready
  optional_candidate_count: <int>
  highest_expected_gain: none | low | medium | high
  highest_regression_risk: low | medium | high | needs_human
  reason: "<structured reason>"
  reopen_condition: "<what new evidence would justify another loop>"
```

## Acceptance

- [x] The summary is advisory and never changes release readiness.
- [x] It consumes `ready_improvement_summary` without duplicating route logic.
- [x] It does not hide blockers: `not_ready` stays `not_ready`.
- [x] It does not tell the operator to stop when open BLOCKER/MAJOR issues
  remain, because blocking loop/driver states never become optional candidates.

## Verification

- `uv run pytest -q tests/test_ready_improvement.py`
  - Result: 12 passed.
- `uv run pytest -q tests/test_ready_improvement.py tests/test_critique_brief.py::test_critique_brief_includes_aesthetic_antipattern_checklist tests/test_fig_driver.py`
  - Result: 87 passed.
- `uv run ruff check scripts/ready_improvement.py tests/test_ready_improvement.py scripts/critique_brief.py scripts/critique_brief_sections.py scripts/critique_schema_vocab.py tests/test_critique_brief.py`
  - Result: all checks passed.
- `git diff --check`
  - Result: clean.

## Review Questions

1. Does this reduce endless polish loops?
2. Does it avoid falsely certifying subjective quality?
3. Does it preserve the user’s ability to continue if they choose?
