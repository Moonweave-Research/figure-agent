# Top-Tier Aesthetic Edge-Case Audit Roadmap

Date: 2026-06-01

## Status

Partially implemented hardening track.

## Current Truth

`figure-agent` is now a strong quality kernel. It can make bad states visible:
stale evidence, missing crop accounting, visual clash candidates,
text-boundary errors, label-path near misses, undeclared geometry, crop
anomalies, reference-learning divergence, SVG polish readiness, SVG delta
regressions, publication gates, accepted/golden gates, and loop/driver stop
boundaries.

It is not yet a complete design coach. A host LLM can still decide that a
figure is "ready" while a human notices a softer but important aesthetic
problem: generic template feel, weak eye path, childish shape language, low
visual authority, paper-wide inconsistency, or a reference that was shown but
not learned from correctly.

The next track should therefore improve the audit language, not weaken the
release model. The plugin should keep blocking deterministic or contract
violations, and surface aesthetic/design issues as structured optional or human
art-direction decisions.

## What Is Already Covered

- Structural completeness, label-target matching, physical plausibility, and
  conceptual completeness.
- Ten journal-grade quality axes: storyline, panel roles, subregion
  integration, component fidelity, scientific plausibility, composition,
  labels, polish, reference fidelity, and publication readiness.
- Top-tier audit slots: first-glance message, journal fit, novelty support,
  caption coupling, economy, cross-panel grammar, misinterpretation risk,
  print readability, accessibility, and aesthetic coherence.
- Editorial art-direction slots, including the TikZ versus SVG polish route.
- Aesthetic intent and aesthetic lever audits when a fixture declares
  `aesthetic_intent.yaml` schema v2.
- Paper-wide aesthetic context and journal playbook packs when fixtures opt in.
- Closed-set micro-defects for hard visual failures such as label/path/box/rule
  collisions and near misses.
- Ready improvement discovery for optional non-blocking polish candidates.

## Remaining Edge-Case Gaps

### 1. Aesthetic Anti-Pattern Specificity

The current aesthetic gate asks broad questions such as maturity, hierarchy,
journal fit, and hand-crafted finish. That is better than generic taste prose,
but it still lets the host LLM answer with vague statements unless the fixture
has a strong `aesthetic_intent.yaml`.

The plugin needs a closed anti-pattern checklist that makes the host LLM
explicitly inspect:

- childish/cartoonish shape language;
- poster-like gradients or decorative effects;
- generic template/schematic look;
- dead-flat vector finish where depth cues are needed;
- too-uniform line weight rhythm;
- weak hero or no visual anchor;
- cramped, dead, or accidental whitespace;
- low-authority typography;
- annotation noise that competes with the science;
- style incoherence across panels;
- reference over-copying;
- reference under-learning;
- decorative detail that does not reduce explanation cost.

### 2. Weakest-Panel And Paper-Series Coherence

The current audits can pass each panel locally while one panel still looks
visibly weaker than the rest. Top-tier papers often fail by weakest-panel
perception: the reader judges the whole figure by the panel that feels least
designed, least integrated, or most template-like.

The plugin needs a structured weakest-panel check that names the weakest panel,
why it is weak, whether the issue is semantic or aesthetic, and whether the
fix belongs in TikZ, SVG polish, paper-wide context, or human art direction.

### 3. Reference Learning Misuse

Reference learning already distinguishes allowed transfer from forbidden copy
targets. The remaining gap is audit accountability: the host LLM should state
which reference principle was learned, which was rejected, and whether the
current figure still shows over-copying or under-learning.

This must not become pixel similarity or forced topology copying. References
teach visual principles; briefing, theory guards, fixture semantics, and author
intent remain authoritative.

### 4. Last-Five-Percent Stop Signal

The loop can detect blockers and optional improvements, but it still lacks a
clear "stop polishing" explanation when all remaining changes are subjective,
low-gain, or likely to risk regressions.

The plugin needs a marginal-return summary:

- remaining candidate count;
- highest expected gain;
- highest regression risk;
- recommended stop/continue decision;
- what evidence would justify reopening polish.

### 5. TikZ Versus SVG Polish Boundary

SVG polish is now safer, but the operator still needs a sharper distinction:

- source-level semantic repair;
- TikZ micro-polish;
- SVG optical cleanup;
- human art-direction decision;
- do not touch.

The plugin should make this boundary visible in the same place the user sees
optional improvement candidates.

## Design Rules

- Do not add hidden auto-design or hidden source/SVG edits.
- Do not let aesthetic scores or anti-pattern checks bypass accepted, golden,
  export, publication, human, or SVG gates.
- Do not make references into copy targets.
- Do not require every fixture to have a reference pack, paper context, or SVG
  polish state.
- Do not silently mutate old critique schemas. If a new required output field
  is introduced, bump schema/rubric.
- Prefer additive summaries and lintable contracts over prose-only prompts.
- Keep `fig_driver` and `fig_run` actor boundaries intact. If the loop-improve
  orchestrator branch is later merged, these signals should feed it without
  changing its stop-boundary model.

## Proposed Issue Order

1. **Issue 97A - Aesthetic Anti-Pattern Checklist.**
   Add a closed, non-prose checklist to the critique brief and validation path
   so generic "looks polished" answers are rejected. This is the highest value
   because it translates vague taste into inspectable categories.
   Status: implemented through v1.17 `aesthetic_antipattern_audit` for grounded
   critiques.

2. **Issue 97B - Weakest-Panel Coherence Summary.**
   Add a structured summary that names the weakest panel/subregion and routes
   the repair to TikZ, SVG, human art direction, or accept-simplification.
   Status: implemented through v1.17 `weakest_panel_coherence`.

3. **Issue 97C - Reference Learning Accountability.**
   Require reference-learning critiques to distinguish learned principle,
   forbidden copy target, over-copying, and under-learning.
   Status: implemented through v1.17 `reference_learning_accountability`.

4. **Issue 97D - Marginal-Return Stop Signal.**
   Add a stop/continue summary for optional polish candidates so the plugin can
   say when further loops are likely low value.
   Status: implemented as
   `ready_improvement_summary.marginal_return_summary`.

5. **Issue 97E - Operator-Facing Integration.**
   Surface the above in `/fig_driver`, and in the loop-improve orchestrator if
   that branch is merged, without changing action vocabulary or release
   authority.
   Status: implemented for `/fig_driver.next_action_summary`.

## First Slice Recommendation

Start with Issue 97A. It has the best risk/reward ratio:

- it directly addresses the user's "what aesthetic edge cases are still being
  missed?" concern;
- it can be tested without running host vision;
- it does not require source drawing work or SVG editing;
- it creates vocabulary that Issues 97B-E can reuse.

## Review Questions

1. Does the roadmap add real audit pressure, or just more words?
2. Can any new aesthetic signal accidentally block release without human
   authority?
3. Can reference learning accidentally force the current figure to imitate the
   wrong reference?
4. Can optional improvements obscure real blockers?
5. Is each issue independently testable?
6. Does this preserve the plugin identity as a quality kernel plus guided
   operator loop, not an autonomous hidden designer?
