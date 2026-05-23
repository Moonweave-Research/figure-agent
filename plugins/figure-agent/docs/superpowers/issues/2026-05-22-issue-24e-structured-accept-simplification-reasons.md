# Issue 24E: Structured Accept-Simplification Reasons

**Date:** 2026-05-22 KST
**Status:** completed in commit `cecd420`
**Type:** audit-output hardening
**Parent:** `2026-05-22-issue-24-audit-gate-hardening-roadmap.md`

## What to build

Replace prose-only visual-clash `accept_simplification` justifications with a
structured reason enum and a separate human-readable rationale for current
critique output.

## Current Problem

Before this issue, `critique_lint.py` accepted visual-clash-linked
`accept_simplification` when the `observation` was long enough, named the
`VC###` id, and contained one of several prose markers. That prevented empty
hand-waves but still left the plugin guessing whether a candidate was accepted
because it was a false positive, an intentional schematic convention, outside
the target region, decorative background, or otherwise convention-acceptable.

## Acceptance Criteria

- [x] Current critique output uses schema `figure-agent.critique.v1.10` and
  rubric `figure-agent.critique-rubric.v1.10`.
- [x] `micro_defects[].status: accept_simplification` in v1.10 requires
  `accept_simplification_reason`.
- [x] Supported reason enum:
  - `false_positive`
  - `intentional_schematic`
  - `outside_target_region`
  - `convention_acceptable`
  - `decorative_background`
- [x] v1.10 requires non-empty `accept_simplification_rationale`.
- [x] `critique_lint.py` rejects visual-clash-linked v1.10 accepted candidates
  missing either structured field.
- [x] v1.9 and older visual-clash accepted candidates retain the legacy prose
  heuristic for backward compatibility.
- [x] `/fig_critique` brief, command docs, and skill guidance describe the new
  structured fields.

## Implementation Notes

- The schema validator enforces structured fields for any v1.10
  `micro_defects[].status: accept_simplification`.
- The lint layer keeps the stricter visual-clash-specific check because the
  risk came from accepting machine-generated visual-clash candidates too
  casually.
- Existing v1.7-v1.9 critiques remain parseable and lintable through the old
  prose heuristic.

## Implementation Contract

- Do not reinterpret existing v1.9 critiques as malformed.
- Do not add score or release behavior.
- Do not change the visual-clash candidate accounting contract except for the
  v1.10 structured reason requirement.
- Keep the reason enum closed so future vague categories require an explicit
  schema change.

## Verification

```bash
uv run pytest -q tests/test_critique_lint.py tests/test_critique_schema_validator.py tests/test_critique_schema_vocab.py tests/test_critique_brief.py
uv run ruff check scripts/critique_lint.py scripts/critique_schema_validator.py scripts/critique_schema_vocab.py scripts/critique_brief.py tests/test_critique_lint.py tests/test_critique_schema_validator.py tests/test_critique_schema_vocab.py tests/test_critique_brief.py
git diff --check
```

## Non-Goals

- No generated critique migration.
- No automatic accepted/golden/export mutation.
- No broad semantic classifier for arbitrary visual-clash candidates.
