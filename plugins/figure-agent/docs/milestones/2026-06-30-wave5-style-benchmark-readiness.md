# Wave 5 Style Benchmark Readiness

Date: 2026-06-30

Source of truth: `docs/superpowers/specs/2026-06-30-human-guided-style-overhaul-readiness-design.md` Wave 5.

## Scope and non-mutation boundary

This readiness packet selects a benchmark fixture for future human-guided style redesign evaluation. It is documentation-only and intentionally does not mutate fixture source, accepted state, golden exports, reference assets, critique files, or publication state.

Hard boundaries preserved:

- Did not edit `examples/fig5_actuation_mechanism/fig5_actuation_mechanism.tex`.
- Did not edit any fixture `.tex`, `briefing.md`, `spec.yaml`, `design.md`, `caption.md`, `critique.md`, `reference/`, `build/`, `exports/`, or accepted-state files.
- Did not run compile/export/acceptance/golden/publication commands.
- Did not select SVG polish as a default style repair path.

## Selected flagship benchmark fixture

| Field | Selection |
| --- | --- |
| Fixture | `fig1_overview_v2_pair_001_vault` |
| Current artifact | `examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex` plus tracked quality/context artifacts |
| Target style class | restrained editorial multipanel scientific schematic for a Nature Materials / Nature Communications main-text overview figure |
| Existing benchmark assets | `benchmark_contract.yaml`, `aesthetic_intent.yaml`, `QUALITY_AUDIT.md`, `spec.yaml`, `critique.md`, and reference-pack context |
| Why this fixture | It already records accepted high-impact dogfood evidence, panel-level style intent, reference provenance, typography/whitespace/color levers, and explicit semantic guardrails. |

This fixture is a benchmark for comparison criteria, not an instruction to rewrite its source in this wave.

## Current style strengths

- Mature multipanel story structure with explicit A-F panel roles and row-level evidence flow.
- Style profile is already paper-local (`style_profile: polymer-paper`) and backed by Style Lock palette/macro conventions.
- `aesthetic_intent.yaml` names concrete style levers: maturity restraint, hero hierarchy, row-2 whitespace, print typography authority, semantic color economy, line-weight rhythm, and component-fidelity finish.
- `QUALITY_AUDIT.md` records prior compile/export/quality evidence and explains which remaining gates are human policy/provenance gates rather than TikZ patch work.
- `benchmark_contract.yaml` gives a detector-grounded comparison contract for label-overlap repair without treating subjective taste as an implicit mutation request.

## Current style weaknesses or watchpoints

- Dense Row 2 evidence panels can regress into cramped labels or column-rule crowding if redesigned without a whitespace/typography contract.
- The fixture depends on a restrained semantic color economy; extra accent hues or decorative gradients would weaken the scientific code.
- Component detail must stay mechanism-bound. Generic icon polish, repeated preset grammar, or toy-like rounded boxes would be style regressions.
- Publication/provenance acceptance remains a human policy gate; a prettier redesign cannot close that gate automatically.

## Higher-style alternative criteria

A future redesign candidate should improve:

1. Print-scale label authority without introducing `\tiny`, `\scriptsize`, `\huge`, or `\Huge` local overrides.
2. Row-2 breathing room while preserving the D/E/F evidence roles and required labels.
3. Foreground/support stroke hierarchy without weakening semantic arrows, axes, or apparatus cues.
4. Semantic color economy: amber/blue/red/gray families remain meaning-bound and non-semantic accents stay subordinate.
5. Component fidelity: apparatus and polymer details become more concrete only when they clarify the declared mechanism.

## Forbidden semantic changes

A redesign candidate must not:

- Change A/B/C/D/E/F panel roles or move evidence between columns.
- Rename symbols, measured quantities, force families, or apparatus labels.
- Swap shallow/deep trap color semantics or force-direction meaning.
- Remove required labels, spokes, apparatus elements, or theory-guarded mechanisms.
- Use SVG polish to repair scientific, semantic, or label-target errors that belong in TikZ/source review.

## Comparison criteria for future redesign work

Future redesign packets should compare the candidate against this benchmark using:

- Style Lock lint output, including typography hierarchy warnings.
- Text-boundary and visual-clash detector deltas where rendered artifacts exist.
- The existing `aesthetic_intent.yaml` levers and forbidden adjustments.
- `benchmark_contract.yaml` hard regressions: no compile failure and no candidate hard-gate rejection.
- Human review only for non-measurable art direction, journal fit, and policy/provenance readiness.

## Stop condition

Wave 5 is ready when future redesign work can be evaluated against the named fixture, current artifact, target style class, forbidden semantic changes, and explicit comparison criteria above instead of vague "better style" language. This packet satisfies that stop condition without source mutation.
