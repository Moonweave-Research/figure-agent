# Issue 97C - Reference Learning Accountability

Status: implemented through schema v1.17

Type: reference-learning audit, anti-copy guard

Parent:

- Issue 97 - Top-Tier Aesthetic Edge-Case Audit Roadmap

## Problem

References should teach editorial principles, not become copy targets. Current
reference-learning support is bounded, but host critique output can still be
too vague about what was learned, what was rejected, and whether the current
figure over-copied or under-learned the reference.

## Goal

Require reference-learning critiques to account for:

- learned editorial principles;
- forbidden copy targets rejected;
- over-copying risk;
- under-learning risk;
- conflicts with briefing, theory guards, or author intent.

## Expected Contract

```yaml
reference_learning_accountability:
  learned_principle: "<what was learned, or not_applicable with reason>"
  rejected_copy_target: "<what was intentionally not copied, or not_applicable with reason>"
  overcopying: absent | present | needs_human | not_applicable
  underlearning: absent | present | needs_human | not_applicable
  route: none | tikz_patch | svg_polish | semantic_backport | human_art_direction | accept_simplification
  evidence: "<current artifact/reference evidence>"
  rationale: "<why this is reference learning, not forced copying>"
  linked_evidence:
    - journal_grade_assessment.reference_calibration | top_tier_audit.<slot> | editorial_art_direction.<slot> | finding id | micro_defect id
```

## Acceptance

- [x] Reference accountability appears only when a reference-learning pack exists.
- [x] It does not use pixel identity or SSIM as a copy target.
- [x] It cannot override briefing, theory guards, fixture semantics, or author
  intent.
- [x] Over-copying and under-learning are described as routed audit issues, not
  hidden auto-editing.
- [x] Schema v1.17 requires a structured `reference_learning_accountability`
  field for grounded critiques.
- [x] Present over-copying or under-learning requires a non-`none` route and
  linked evidence.

## Verification

- `uv run pytest -q tests/test_critique_brief.py::test_critique_brief_includes_reference_learning_contract`
  - Result: 1 passed.
- `uv run pytest -q tests/test_critique_schema_validator.py tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_status.py::test_hash_metadata_accepts_v1_17_rubric_for_audit_crop_manifest`
  - Result: 183 passed.

## Review Questions

1. Does this prevent wrong-reference coercion?
2. Does it still let references teach useful design principles?
3. Are ambiguous cases routed to a human instead of automation?
