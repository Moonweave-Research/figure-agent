# Issue 97C - Reference Learning Accountability

Status: proposed

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
  learned_principles:
    - principle_id: <from critique_reference_pack.yaml>
      applied_to: <panel/subregion/figure>
      evidence: "<current artifact evidence>"
  rejected_copy_targets:
    - reference_trait: <trait id or description>
      reason: briefing | theory_guard | fixture_semantics | author_intent | journal_fit
  overcopying_risk:
    verdict: absent | present | needs_human
    evidence: "<why>"
  underlearning_risk:
    verdict: absent | present | needs_human
    evidence: "<why>"
```

## Acceptance

- Reference accountability appears only when a reference-learning pack exists.
- It does not use pixel identity or SSIM as a copy target.
- It cannot override briefing, theory guards, fixture semantics, or author
  intent.
- Over-copying and under-learning can route to human art direction or semantic
  backport, but not hidden auto-editing.

## Review Questions

1. Does this prevent wrong-reference coercion?
2. Does it still let references teach useful design principles?
3. Are ambiguous cases routed to a human instead of automation?
