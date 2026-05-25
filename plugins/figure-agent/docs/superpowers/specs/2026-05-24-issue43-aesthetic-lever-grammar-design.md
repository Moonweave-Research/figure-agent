# Issue 43 Design — Aesthetic Lever Grammar

## Status

Implemented through Issue 43E in commits `a49bda8`, `4604dfa`, `aa1d6fd`,
`c65a4bd`, `a1a19ae`, `2107e39`, `1a02791`, `5511fba`, `d817022`, and
`91de4e9`. Issue 43F dogfood evidence was captured in
`docs/milestones/2026-05-24-aesthetic-lever-grammar-dogfood.md`.

The implemented slice adds the v2 intent parser, v1.11 critique brief/schema
contract, fixture-aware lint accountability, and `/fig_loop` summary surfacing.
It also makes hash freshness expect rubric v1.11 when a fixture declares
`aesthetic_intent.yaml` schema v2 and hardens the route gates found during
review. The dry-run driver also preserves the aesthetic lever summary from
latest loop checkpoints and blocks polish handoff when loop-level human/top-tier
blockers are still open.
It does not add automatic drawing edits, SVG polish mutation, score gates,
release shortcuts, or accepted/golden state changes.

## Context

The current plugin has a strong verification kernel:

- deterministic compile/export/status gates;
- high-zoom crop and crop-read accountability;
- visual-clash and text-boundary candidate accounting;
- reference-calibrated critique packs;
- top-tier and editorial art-direction audit fields;
- advisory journal-grade assessment;
- SVG polish final-artifact handoff.

Issues 35 and 36 added an optional `aesthetic_intent.yaml` file and lint
accountability for exact intent-anchor citations. That made fixture-specific
visual intent visible to `/fig_critique`, but it did not yet turn broad taste
language into a repeatable lever grammar.

This design addresses that gap. The goal is not to automate taste. The goal is
to make taste review explicit enough that a host LLM cannot simply say "improve
polish" without naming the aesthetic dimension, observed evidence, allowed next
action, forbidden action, and route.

## Design Principle

Treat aesthetics as bounded review levers, not as a free-form score.

Each lever answers five questions:

1. What visual dimension is being judged?
2. What positive signals would make this dimension pass?
3. What anti-patterns would make it fail?
4. What adjustments are allowed without changing scientific meaning?
5. Which route is appropriate: TikZ patch, SVG polish, semantic backport, or
   human art direction?

The plugin remains a verification and handoff layer. It can require accounting,
surface bottlenecks, and block silent skips. It must not decide subjective art
direction alone or mutate figure sources automatically.

## Proposed Contract: `aesthetic_intent.yaml` v2

Version v2 extends the current v1 file. Existing v1 files remain valid and keep
their current behavior. The parser must accept both schema strings explicitly;
it must not silently reinterpret a v1 file as v2.

```yaml
schema: figure-agent.aesthetic-intent.v2
fixture: fig1_overview_v2_pair_001_vault
target_journal: Nature Materials
visual_maturity: editorial
density: balanced
reference_style: multipanel_story
design_principles:
  - id: mature_restraint
    instruction: "Prefer restrained, publication-grade visual hierarchy over decorative emphasis."
must_avoid:
  - id: toy_diagram
    pattern: "Oversized arrows, rounded generic boxes, or poster-like saturation."
    severity: MAJOR
polish_triggers:
  - id: svg_micro_polish
    condition: "TikZ is semantically correct but optical spacing and strokes limit journal polish."
    recommended_path: ready_for_svg_polish
aesthetic_levers:
  - id: maturity_restraint
    dimension: maturity
    intent: "Make the figure read as controlled editorial science illustration, not toy schematic."
    priority: required
    positive_signals:
      - "restrained label scale"
      - "limited accent colors with semantic roles"
      - "no decorative gradients without explanatory role"
    anti_patterns:
      - "oversized arrows"
      - "generic rounded blocks"
      - "poster-like saturation"
    allowed_adjustments:
      - "reduce non-essential label prominence"
      - "rebalance accent color usage"
      - "simplify decorative marks"
    forbidden_adjustments:
      - "remove scientific components"
      - "change mechanism meaning"
    default_route: tikz_patch
```

### Top-Level Fields

v2 keeps these v1 fields unchanged:

- `schema`
- `fixture`
- `target_journal`
- `visual_maturity`
- `density`
- `reference_style`
- `design_principles`
- `must_avoid`
- `polish_triggers`

v2 adds:

- `aesthetic_levers`: non-empty list of lever mappings.

### Lever Fields

Each `aesthetic_levers[]` item requires:

- `id`: stable non-empty string, unique within the file.
- `dimension`: one of the closed set below.
- `intent`: one concrete aesthetic objective.
- `priority`: `required | recommended | optional`.
- `positive_signals`: non-empty list of strings.
- `anti_patterns`: non-empty list of strings.
- `allowed_adjustments`: non-empty list of strings.
- `forbidden_adjustments`: non-empty list of strings.
- `default_route`: `tikz_patch | svg_polish | semantic_backport | human_art_direction`.

Unknown future mapping fields may be preserved by the parser but must not bypass
required-field validation.

The v2 lever list has a hard size limit of 10 entries. The recommended range is
6-10 for real figures. More than 10 entries must fail validation because it
turns the host critique into an attention-management problem rather than a
bounded audit.

### Lever Dimensions

The initial closed set is:

- `maturity`: restraint, non-toy visual language, professional finish.
- `hero_hierarchy`: first fixation, main claim visibility, panel emphasis.
- `whitespace_breathing`: density, negative space, local crowding, visual rest.
- `typography_authority`: label scale, hierarchy, math/subscript readability,
  print-scale authority.
- `color_harmony`: semantic color economy, saturation, grayscale robustness,
  accent discipline.
- `line_weight_rhythm`: foreground/background line hierarchy, emphasis, support
  strokes, repeated stroke monotony.
- `component_fidelity`: material, apparatus, molecular, or mechanism detail
  sufficient for the stated claim.
- `hand_craft`: organic variance, macro-repeat feel, subtle detail, non-generic
  finish.
- `cross_panel_grammar`: consistent visual language across panels.
- `polish_route`: whether the remaining issue belongs in TikZ, SVG polish,
  semantic backport, or human art direction.

This set is intentionally small enough for every critique to enumerate.

## Critique Output Contract

When `aesthetic_intent.yaml` schema v2 exists, `/fig_critique` must bump the
critique schema and rubric to:

- `schema: figure-agent.critique.v1.11`
- `rubric_version: figure-agent.critique-rubric.v1.11`

When the intent file is absent or uses schema v1, `/fig_critique` must keep the
current v1.10 output contract. This avoids forcing every fixture onto the v2
lever grammar before it has a declared target.

The output adds a top-level field:

```yaml
aesthetic_lever_audit:
  - lever_id: maturity_restraint
    dimension: maturity
    verdict: pass | weak | fail | needs_human | not_applicable
    confidence: low | medium | high
    observed_positive_signals:
      - "restrained label scale"
    observed_anti_patterns:
      - "poster-like saturation in Panel B callout"
    route: none | tikz_patch | svg_polish | semantic_backport | human_art_direction
    linked_evidence:
      - "top_tier_audit.aesthetic_coherence"
      - "editorial_art_direction.visual_identity"
      - "C001"
    allowed_next_adjustment: "rebalance accent color usage in Panel B only"
    forbidden_adjustment_guard: "do not change mechanism arrows or material identity"
    rationale: "The lever cites maturity_restraint and toy_diagram; Panel B still reads poster-like."
```

### Output Rules

- Every declared v2 lever must appear exactly once in `aesthetic_lever_audit`.
- `lever_id` must match an `aesthetic_levers[].id`.
- `dimension` must match the declared lever dimension.
- `priority: required` levers cannot use `verdict: not_applicable`.
- `verdict: pass` must have at least one `observed_positive_signals` entry and
  must use `route: none`.
- `verdict: fail`, `weak`, or `needs_human` must have non-empty
  `observed_anti_patterns` and non-empty `linked_evidence`.
- `route` must follow the declared `default_route` for schema v1.11. Route
  override rationale is deferred until a future schema has an explicit field for it.
- `route: tikz_patch` must link to a normal finding or a
  `quality_axes.blocking_items` entry.
- `route: svg_polish` must cite
  `editorial_art_direction.tikz_vs_svg_polish_trigger`, that trigger must state
  `recommended_path: ready_for_svg_polish`, and the route must not change
  scientific meaning.
- `route: semantic_backport` must cite
  `editorial_art_direction.tikz_vs_svg_polish_trigger`, and that trigger must
  state `recommended_path: semantic_backport_required`. Free-text rationale is
  not enough to activate the route.
- `route: human_art_direction` must surface as a human gate, not as
  `accept_simplification`, and must cite
  `editorial_art_direction.human_art_direction_gate`.
- `route: none` is valid only for `pass` or `not_applicable`.
- `linked_evidence` entries must use one of these forms:
  `top_tier_audit.<slot_key>`, `editorial_art_direction.<slot_key>`,
  `quality_axes.<axis_key>`, `micro_defects.<id>`, or a normal finding id such
  as `C001` / `P001`.

## Brief Behavior

When v2 intent exists, `critique_brief.py` must replace the current short
`## Aesthetic Intent Calibration` section with a stronger section:

```markdown
## Aesthetic Lever Grammar (host LLM MUST enumerate)

The fixture declares aesthetic intent schema v2. You MUST fill
top-level YAML field `aesthetic_lever_audit` with exactly one entry for every
declared lever id. Generic prose such as "improve polish" is invalid unless it
is tied to a lever id, observed evidence, allowed adjustment, forbidden guard,
and route.

For each lever:
1. inspect the full render, high-zoom crops, print-scale images, reference pack,
   and existing audit evidence;
2. list observed positive signals;
3. list observed anti-patterns;
4. choose a route;
5. link the route to existing critique evidence.
```

The brief must still emit the v1 anchor-citation text for top-tier/editorial
slots. The v2 lever audit is additional accounting, not a replacement for those
slots.

## Lint and Validation

`critique_schema_validator.py` must validate the shape of
`aesthetic_lever_audit` for v1.11 critiques.

`critique_lint.py` must validate fixture-specific v2 accountability:

- reject missing `aesthetic_lever_audit` when v2 intent exists;
- reject duplicate or unknown `lever_id`;
- reject missing required lever ids;
- reject mismatched `dimension`;
- reject `route: none` for non-passing verdicts;
- reject `route` other than `none` for passing verdicts;
- reject `not_applicable` for required levers;
- reject non-passing levers without concrete `observed_anti_patterns`;
- reject active routes that do not match the declared `default_route`;
- reject `route: tikz_patch` without a linked finding or quality-axis blocker;
- reject `route: svg_polish` unless the editorial polish trigger is cited and
  its `recommended_path` is `ready_for_svg_polish`;
- reject `route: semantic_backport` unless the editorial polish trigger is cited
  and its `recommended_path` is `semantic_backport_required`;
- reject `route: human_art_direction` unless the human art-direction gate is
  cited;
- reject `route: human_art_direction` if hidden behind `accept_simplification`;
- reject `journal_grade_assessment.benchmark_level: high_impact_candidate` when
  any required lever is `fail`, `needs_human`, or `weak` with a route other than
  `none`;
- report malformed v2 intent as a controlled lint blocker.

Legacy behavior:

- fixtures without `aesthetic_intent.yaml`: unchanged;
- v1 intent files: current Issue 35/36 behavior unchanged;
- v1.10 and older critiques: remain parseable through existing legacy paths.

## Loop Surfacing

`fig_loop.py` must surface a compact summary when v1.11 critique is fresh:

```json
"aesthetic_lever_summary": {
  "source": "critique.aesthetic_lever_audit",
  "evaluation_state": "passed | needs_patch | needs_human | blocked | stale",
  "worst_verdict": "pass | weak | fail | needs_human | not_applicable",
  "next_aesthetic_bottleneck": {
    "lever_id": "maturity_restraint",
    "dimension": "maturity",
    "route": "tikz_patch",
    "linked_evidence": ["C001"]
  }
}
```

This summary is advisory for routing, not a release shortcut. Any existing
non-aesthetic gate remains authoritative.

## Route Semantics

`tikz_patch`:

- for source-level visual hierarchy, line-weight, label scale, spacing,
  component fidelity, or grammar issues that can be represented in TikZ without
  semantic ambiguity.

`svg_polish`:

- for optical finishing after generated export is current and semantic critique
  blockers are closed. Allowed only within the existing SVG polish handoff edit
  classes.

`semantic_backport`:

- for any requested polish that changes mechanism, material identity, label
  meaning, panel role, scientific proximity, or storyline.

`human_art_direction`:

- for taste, target-journal fit, cover-like ambition, novelty framing, or
  conflicting reference-style choices that automation must not decide.
  Automation must surface this route as a human gate.

## Failure Modes and Guards

1. **Generic taste prose**
   - Guard: lint requires lever id, evidence, allowed adjustment, forbidden
     guard, and route.

2. **Aesthetic route bypasses science**
   - Guard: no route may override physics, critique freshness, export, accepted,
     golden, publication, or final-artifact gates.

3. **SVG polish hides semantic changes**
   - Guard: semantic-change triggers must route to `semantic_backport`, not
     `svg_polish`.

4. **Too many levers overwhelm critique**
   - Guard: recommend 6-10 levers per fixture and fail only on declared levers.

5. **Single reference lock-in**
   - Guard: use levers as intent constraints, not as copied visual templates.

6. **v1 fixture churn**
   - Guard: v1 remains supported; v2 is opt-in.

7. **Score inflation**
   - Guard: scores remain advisory and cannot pass a failed lever.

## Implementation Slices

### Issue 43A — v2 Intent Parser

- Extend `scripts/aesthetic_intent.py` for schema v2.
- Add `aesthetic_levers[]` validation.
- Preserve v1 behavior.
- Tests: valid v2, malformed v2, duplicate lever ids, invalid dimension,
  invalid route, v1 compatibility.
- Target files:
  - `scripts/aesthetic_intent.py`
  - `tests/test_aesthetic_intent.py`

### Issue 43B — Brief and Hash Integration

- Update `scripts/critique_brief.py` to emit `## Aesthetic Lever Grammar`.
- Keep `aesthetic_intent.yaml` in critique input hashing.
- Tests: brief includes lever ids and required host instructions; missing/v1
  behavior unchanged.
- Update command and skill docs so host-LLM instructions match the generated
  brief.
- Target files:
  - `scripts/critique_brief.py`
  - `commands/fig_critique.md`
  - `skills/figure-agent/SKILL.md`
  - `tests/test_critique_brief.py`

### Issue 43C — Critique Schema v1.11

- Add `aesthetic_lever_audit` schema block to the brief.
- Validate v1.11 in `critique_schema_validator.py`.
- Tests: complete audit passes; missing audit fails; unknown verdict/route fails.
- Keep `critique_adjudication.py` compatibility by relying on the common schema
  validator and existing normal finding decisions. Aesthetic levers do not add a
  second adjudication decision list.
- Target files:
  - `scripts/critique_brief_sections.py`
  - `scripts/critique_schema_validator.py`
  - `scripts/critique_schema_vocab.py`
  - `tests/test_critique_brief_sections.py`
  - `tests/test_critique_schema_validator.py`
  - `tests/test_critique_adjudication.py`

### Issue 43D — Lint Accountability

- Add fixture-specific v2 lint checks in `critique_lint.py`.
- Tests: missing lever, duplicate lever, unknown lever, route-none failure,
  TikZ patch without linked finding, SVG polish without editorial trigger,
  human art direction hidden by simplification.
- Target files:
  - `scripts/critique_lint.py`
  - `tests/test_critique_lint.py`

### Issue 43E — Loop Summary

- Add `aesthetic_lever_summary` extraction to `/fig_loop`.
- Tests: fresh v1.11 summary, stale critique returns stale/none, worst verdict
  ordering, next bottleneck selection.
- Target files:
  - `scripts/fig_loop_assessments.py`
  - `scripts/fig_loop.py`
  - `tests/test_fig_loop_assessments.py`
  - `tests/test_fig_loop.py`

### Issue 43F — Dogfood Evidence

- Apply v2 intent to one real fixture without changing figure source.
- Regenerate critique through host vision.
- Record whether the lever audit produces more actionable bottlenecks than
  Issue 35/36 anchor-only behavior.
- Target files:
  - one fixture `aesthetic_intent.yaml` may be upgraded to v2 only if the
    dogfood fixture is intentionally selected;
  - milestone evidence under `docs/milestones/`.

## Verification Plan for Implementation

Targeted:

```bash
uv run pytest -q tests/test_aesthetic_intent.py tests/test_critique_brief.py tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_fig_loop_assessments.py tests/test_fig_loop.py
uv run ruff check scripts/aesthetic_intent.py scripts/critique_brief.py scripts/critique_schema_validator.py scripts/critique_lint.py scripts/fig_loop_assessments.py scripts/fig_loop.py tests/test_aesthetic_intent.py tests/test_critique_brief.py tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_fig_loop_assessments.py tests/test_fig_loop.py
git diff --check
```

Final:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

## Non-Goals

- This design does not make the plugin generate beautiful figures by itself.
- This design does not claim Nature/Science acceptance readiness.
- This design does not replace human art direction.
- This design does not add hidden auto-editing.
- This design does not make SVG polish mandatory.

## Review Checklist

- Does every subjective concept become a concrete lever field?
- Can a host LLM still ignore the levers while passing lint?
- Can a semantic change be mislabeled as SVG polish?
- Can a failed aesthetic lever accidentally pass release?
- Does v1 compatibility remain intact?
- Are implementation slices small enough for TDD?

## Design Review Log

Review 1: schema and route correctness.

- Finding: v2 schema selection was ambiguous and could have forced non-v2
  fixtures onto v1.11 critique output.
- Fix: explicitly require v1.11 only when `aesthetic_intent.yaml` uses schema
  v2; absent/v1 intent keeps v1.10 behavior.
- Finding: `semantic_backport` lint was phrased as if lint could know that a
  future loop would block final-artifact promotion.
- Fix: make lint validate concrete linked evidence, and leave stop-boundary
  surfacing to `/fig_loop`.
- Finding: required levers could escape as `not_applicable`.
- Fix: forbid `not_applicable` for `priority: required`.
- Finding: review found that schema freshness, route defaults, and human-gate
  routing could still drift through prose-level interpretation.
- Fix: make v1.11 freshness schema-aware, require unresolved lever anti-pattern
  evidence, require active routes to match declared `default_route`, require SVG
  and semantic-backport routes to match the editorial trigger path, and make
  `/fig_loop` stop on `human_art_direction` lever summaries.

Review 2: implementation readiness.

- Finding: command/skill docs and adjudication compatibility were not listed in
  the implementation slices.
- Fix: add target files for `/fig_critique`, SKILL.md, shared schema validator,
  and adjudication compatibility tests.

Review 3: ambiguity scan.

- Finding: several validation requirements used soft "should" language.
- Fix: convert validation and schema requirements to `must`, define the
  `linked_evidence` allowed forms, and mark the issue design-reviewed rather
  than merely in progress.

No known Issue 43 design blocker remains.
