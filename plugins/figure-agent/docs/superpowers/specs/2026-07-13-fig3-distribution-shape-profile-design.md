# Fig3 Distribution Shape Profile Experiment Design

**Status:** Approved experiment design; non-authoritative evidence

**Authority:** `docs/product-spec.md` and `docs/execution-plan.md` remain the
only product and execution authorities. This document does not promote a new
renderer, illustration grammar, or publication-quality claim.

## Decision

Test one attempt-scoped `shape_profile` that constrains the scientific and
graphical relationship between the S60 and S80 trap-energy distributions while
leaving TikZ composition to the authoring LLM.

This is not a reusable illustration grammar. The current evidence is one Fig3
family and one TikZ backend, so it does not satisfy the product specification's
cross-figure, cross-backend, or human-improvement promotion requirements.

## Scientific visual model

Panel B uses two separate qualitative mini-plots connected by one named
composition transition:

```text
S60 narrow single peak -- increasing sulfur / disorder --> S80 broad single peak
```

Both plots share the same axis semantics, baseline, stroke family, and encoding
policy. The curves are qualitative schematics rather than measured functions.
Their height or area must not imply a quantitative density comparison.

The profile preserves these relations:

- S60 is discrete and narrower than S80;
- S80 is continuous, broad, and single-peaked;
- increasing sulfur/disorder names the transition instead of implying an
  unqualified causal arrow;
- `n` denotes distribution breadth;
- `rho_60s` remains an orthogonal magnitude cue; and
- breadth is not trap density.

## Constraint boundary

Figure Agent owns only a compact attempt-scoped contract:

- stable curve IDs and semantic roles;
- `single_peak` topology for both distributions;
- the comparative relation `S60 narrower_than S80`;
- shared baseline, axis semantics, stroke family, and fill policy;
- forbidden self-intersection, baseline crossing, axis truncation, unexplained
  mixed fill treatment, and curve/label overlap;
- existing panel-owned labels, mutual clearance, and text budgets; and
- provenance binding from the selected profile to the generated attempt.

The LLM retains exact control points, plot proportions, spacing, approved role
colors, arrow placement, optical adjustment, and TikZ source structure.

The contract must not prescribe coordinates, Gaussian parameters, arbitrary
peak height, journal-wide thresholds, or a general-purpose path language.

## Implementation surface

Add an experimental `figure-agent.shape-profile.v1` YAML contract selected by
an individual generation attempt. The context-pack loader validates it and
emits concise authoring directives. It does not render curves or mutate source.

The generated attempt is additive under
`examples/fig3_resistance_mechanism/review/failure-first/`. It must not modify
the maintained Fig3 source or any historical attempt.

The attempt manifest binds:

- profile path and SHA-256;
- authority/input packet hash;
- model, budget, starting prompt, transcript, and generated source hashes;
- TikZ/PDF/PNG render receipt;
- existing layout and text reports; and
- named human outcome when available.

## Verification and epistemic boundary

Machine checks may prove schema validity, declared relation completeness,
forbidden-import absence, source/render/provenance binding, compilation,
required-label ownership, label clearance, and text budgets.

Machine checks do not prove that a curve looks natural, contemporary, or
publication-ready. Until a renderer-bound curve-geometry receipt exists, shape
naturalness and graphical coherence remain named human-review fields. The
profile must not claim that prompt compliance proves rendered compliance.

The experiment succeeds only if a new clean generation:

1. preserves all declared scientific relations;
2. avoids the known clipping, label overlap, and text-budget failures;
3. uses coherent paired distribution shapes without manual polishing of the
   rejected artifact;
4. is reproducible from bound inputs; and
5. receives an explicit human verdict on shape coherence and overall quality.

Passing machine gates yields `review_ready`, never publication acceptance.

## Failure handling

- Invalid profile: fail before generation.
- Missing or stale profile hash: attempt is provenance-incomplete.
- Generation violates machine-visible layout or semantic constraints: preserve
  the attempt as rejected evidence; do not patch it into a pass.
- Shape remains visually unnatural despite machine validity: record a human
  rejection and retain the profile as experimental negative evidence.
- One successful Fig3 attempt: do not promote the profile.

## Promotion boundary

Promotion requires the existing product rules: the same control failure and
profile must transfer to a materially different figure family, at least two
backends must preserve the same roles, and named human review must show quality
or correction-cost improvement. Until then, the outcome is
`retain_experimental` or `retire`, not `promote`.
