# Issue 6B: Journal-Grade Figure Quality Axes v1.2

## What to build

Extend the critique/loop contract so `figure-agent` audits a figure as a
journal-grade scientific figure, not only as a compiled TikZ artifact with
local layout issues. Issue 6A made the host LLM enumerate structural,
label-target, physical, and conceptual audit evidence. Issue 6B adds durable
quality axes that the critique must fill and a follow-up loop slice can surface.

This issue introduces:

- `figure-agent.critique.v1.2`
- `figure-agent.critique-rubric.v1.2`
- required `quality_axes` frontmatter in `critique.md`
- a journal-grade audit taxonomy covering figure-level, panel-level,
  sub-region-level, component-level, story, layout, science, polish, and
  reference-fidelity concerns

## Why now

Dogfood showed that local fixes can improve coordinates, fonts, labels, and
palette while still leaving a figure below manuscript quality. The missing
contract is not another collision checker. The missing contract is a stable
question set that every critique and loop run must ask:

- Does the figure communicate a clear scientific story?
- Does each panel have a necessary role?
- Are sub-regions and components structurally credible?
- Is the composition natural and visually economical?
- Are physical/mechanistic cues plausible?
- Does the figure read like a polished high-impact scientific schematic?
- Does reference use preserve role and topology without copying or hallucinating?

Without those axes, the loop can keep resolving narrow findings while the
overall figure remains weak.

## Acceptance criteria

- [ ] `/fig_critique` brief requires `quality_axes` in schema
  `figure-agent.critique.v1.2`.
- [ ] `quality_axes` includes these required axes:
  - `message_storyline`
  - `panel_role_coherence`
  - `subregion_integration`
  - `component_fidelity`
  - `scientific_plausibility`
  - `composition_layout`
  - `label_annotation_semantics`
  - `journal_polish`
  - `reference_fidelity`
  - `publication_readiness`
- [ ] Each axis records `verdict`, `confidence`, `rationale`, `evidence`,
  `blocking_items`, and `recommended_action`.
- [ ] Verdict values are bounded:
  `pass`, `needs_patch`, `needs_human`, `block`, `not_applicable`.
- [ ] Confidence values are bounded:
  `low`, `medium`, `high`.
- [ ] Recommended action values are bounded:
  `none`, `patch`, `human_review`, `revise_briefing`, `block_release`.
- [ ] `blocking_items` is always a list; use `[]` when no blocker exists.
- [ ] `pass`, `needs_patch`, `needs_human`, and `block` axes require non-empty
  `rationale` and `evidence`.
- [ ] `needs_patch` and `block` axes require at least one `blocking_items`
  entry so actionable problems cannot hide in prose only.
- [ ] `recommended_action` is consistent with `verdict`:
  `pass`/`not_applicable` use `none`, `needs_patch` uses `patch` or
  `revise_briefing`, `needs_human` uses `human_review` or `revise_briefing`,
  and `block` uses `block_release` or `human_review`.
- [ ] The brief includes force-enumeration prompts for each axis, with explicit
  panel-level and sub-region-level checks where relevant.
- [ ] The brief states that no single opaque quality score can replace axis
  verdicts.
- [ ] The brief may compute a compact readiness summary, but raw axis verdicts
  must remain available.
- [ ] v1 and v1.1 critiques remain legacy-parseable.
- [ ] v1.2 critiques with missing or malformed `quality_axes` fail controlled
  validation before adjudication scaffold.
- [ ] `publication_readiness.verdict` cannot be less severe than any
  applicable upstream quality axis.
- [ ] `publication_readiness.verdict` cannot be `not_applicable` when any
  upstream quality axis is applicable.
- [ ] The v1.2 schema is designed so a follow-up `/fig_loop.axis_verdicts`
  slice can ingest quality axes without changing compile/export behavior in
  this issue.
- [ ] No hidden auto-editing or auto-acceptance is introduced.

## Audit axes

### 1. Message and Storyline

The critique must judge whether the figure has a clear scientific message, a
natural reading order, and an obvious relationship to the manuscript claim.

### 2. Panel Role Coherence

The critique must identify each panel's role and flag missing, redundant, or
misordered panels.

### 3. Sub-region Integration

The critique must check whether active sub-regions fit the whole figure, do not
damage stable areas, and preserve local/global visual grammar.

### 4. Component Fidelity

The critique must check whether individual objects, apparatus parts, material
regions, supports, frames, mounts, connections, and boundaries are recognizable
and scientifically credible.

### 5. Scientific Plausibility

The critique must check arrows, forces, fields, charge signs, currents, energy
ordering, flow direction, spatial proximity, and theory-guard constraints.

### 6. Composition and Layout

The critique must check hierarchy, spacing, balance, alignment, density, scale,
thumbnail readability, and whether the figure reads as one coherent system.

### 7. Label and Annotation Semantics

The critique must check label-target identity, leader lines, terminology,
annotation density, and consistency of label placement grammar.

### 8. Journal Polish

The critique must check typography, line weight, contrast, palette economy,
schematic restraint, export-scale readability, and absence of decorative noise.

### 9. Reference Fidelity

The critique must check whether references were translated by role/topology
rather than pixel-copied, and whether deviations are intentional omissions or
incomplete drawing.

### 10. Publication Readiness

The critique must summarize whether the figure is ready for manuscript use,
needs local patching, needs domain/human review, or is blocked by a core
scientific/structural problem.

## Out of scope

- Guaranteeing Nature/Science acceptance or claiming journal-level quality as
  an objective fact.
- Calling external literature, image-generation, or vision APIs.
- Auto-applying structural, scientific, mechanism, or story-level changes.
- Auto-setting `accepted: true`.
- Migrating existing critique files to v1.2.
- Replacing collision, visual clash, layout drift, or freshness gates.
- Building a reference retrieval/vault layer inside `figure-agent`.

## Implementation reference

Use the design spec:

- `docs/superpowers/specs/2026-05-18-journal-grade-quality-axes-v1-2-design.md`

## Blocked by

Issue 6A is a prerequisite because v1.2 builds on the mandatory
`audit_enumeration` contract introduced there.
