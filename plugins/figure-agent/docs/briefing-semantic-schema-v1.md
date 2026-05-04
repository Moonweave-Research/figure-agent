# `briefing_semantic.yaml` Schema v1

**Status:** DRAFT (2026-05-04)
**Parent:** `architecture-v0.3-briefing-semantic-grounding.md` §3.2
**Goal:** define a schema authors can write that gives L3 (TikZ author), L4.5 (vision critique), and L6 (drift check) shared semantic ground truth — what the figure is supposed to depict and how to verify the rendering preserves intent.

This is the v1 schema. It is intentionally **flat, self-contained, and verbose**. Ontology imports, inheritance, and DSL syntactic sugar are deferred to v2 once N≥3 fixtures expose real reuse patterns. **Don't pre-optimize.**

---

## 1. Design constraints

The schema fields below were chosen against four hard constraints. Anything that fails a constraint is rejected from v1.

| Constraint | What it means | Test |
|---|---|---|
| **Verifiable** | every assertion can be checked against the rendered PNG | "vision LLM reading PNG can answer yes/no" |
| **Actionable** | every must_depict bullet gives author enough to draw | "human or LLM can write TikZ for this without further questions" |
| **Domain-portable** | schema works for chemistry, physics, biology, etc. | "no chemistry-specific keys at top level" |
| **Terse** | author writes ≤100 lines per typical fixture | "no required boilerplate beyond ~5 lines" |

Schemas that pass `Verifiable` but fail `Actionable` produce figures the critique passes but readers can't understand. Schemas that pass `Actionable` but fail `Verifiable` give the critique nothing to ground on. Both are required.

## 2. Top-level structure

```yaml
schema: figure-agent.briefing_semantic.v1   # required, version pin
fixture: <name>                              # required, matches dir name

# § 3. Context
domain:
  fields: [<field>, ...]                     # tags; not enforced, used by future ontology
  conventions: [<short citation>, ...]       # narrative reference, free text

# § 4. Elements (what's in the figure)
elements:
  - id: <element_id>                         # required, unique within fixture
    role: <role_kind>                        # required, see § 4.1
    domain: <field>                          # required, one of domain.fields
    must_depict: [<bullet>, ...]             # ≥1 required
    must_avoid: [<bullet>, ...]              # optional

# § 5. Assertions (how to check)
assertions:
  - id: <assertion_id>                       # required, unique
    on: <element_id> | global                # required
    statement: "<verifiable claim>"          # required
    verify_by: vision | structural | both    # required, see § 5.1
    severity: BLOCKER | MAJOR | MINOR        # required

# § 6. Reference grounding
reference:
  source: <relative path>                    # optional; e.g. reference/golden_target_001.png
  authority: ground_truth | guidance_only | known_defects
  known_defects:                             # optional, see § 6.2
    - statement: "<what's wrong with the reference>"
      override: "<correct alternative>"
```

## 3. `domain` field

Free-text tags + short narrative citations. **Not enforced in v1.** Used by v2 ontology imports and by future analytics. Authors should still fill it; future tooling will rely on consistent field tags.

```yaml
domain:
  fields: [polymer_chemistry, semiconductor_physics, statistical_mechanics]
  conventions:
    - "Nature Materials schematic conventions"
    - "Sze 'Physics of Semiconductor Devices' band diagram conventions"
```

Field tag conventions:
- snake_case
- prefer narrow over broad (`polymer_chemistry` not `chemistry`)
- multiple OK; figure can sit at intersection

## 4. `elements`

Each element is a *semantic object* the figure depicts. An element is not a TikZ primitive — it's an authorial unit the reader is expected to perceive.

### 4.1 `role` enum

| Role | Meaning | Example |
|---|---|---|
| `visual_anchor` | reader's spatial reference point | polymer chain backbone, axis lines |
| `data_visualization` | quantity rendered into geometry | g(E_t) lobes, power-law plot |
| `process_flow` | causal/temporal arrows or chain | math chain `Σ → I(t) → n → ...` |
| `annotation` | text explaining adjacent geometry | "S-rich segments" caption |
| `legend` | color/symbol → meaning mapping | "shallow / deep" labels next to lobes |
| `boundary` | grouping or scope marker | teal brace, dashed segment box |
| `icon` | compact pictogram standing for a concept | Σ=∫ box, monitor icon |

If a candidate element doesn't fit any role, it's probably below the granularity threshold (it's a TikZ detail, not a semantic element). Skip it.

### 4.2 `must_depict` bullets — actionability test

Each bullet must pass: *"can a human or LLM write TikZ for this without asking a follow-up question?"*

❌ Fails: `"polymer chain"` — what backbone? how many monomers? S placement?
✅ Passes: `"Wavy line with at least 12 monomer units, S atoms drawn as filled circles attached perpendicular to backbone at indices 2, 5, 7, 11"`

❌ Fails: `"Lobes representing g(E_t)"` — which orientation? smooth or discrete?
✅ Passes: `"Two smooth Gaussian-like lobes opening rightward from a vertical axis, shallow lobe centered above deep lobe with a small gap"`

The test is strict by design. Vague depict bullets are why v0.2 critique drifted — generic vision LLMs fill in vague intent with generic best practice.

### 4.3 `must_avoid` — negative space

Optional, but powerful when the briefing has a known anti-pattern.

```yaml
- id: polymer_chain
  must_avoid:
    - "Featureless wavy lines without distinguishable monomer units"
    - "Sulfur atoms drawn as floating circles unattached to backbone"
```

This addresses N=1 dogfood issue #2 directly: the current TikZ renders polymer chains as featureless waves. `must_avoid` flags this as a target the rendered build must NOT match.

## 5. `assertions`

Each assertion is a **machine-checkable claim** about the rendered figure. The assertion statement, plus the verify_by mode, plus severity, gives L4.5 critique an actionable check.

### 5.1 `verify_by` modes

| Mode | Who checks | Suitable for |
|---|---|---|
| `vision` | host LLM reading PNG | "shallow lobe peak is above deep lobe peak" |
| `structural` | static .tex parser | "trap_shallow style is used for upper traps only" |
| `both` | check both, BLOCKER if either fails | high-stakes physics invariants |

`vision` mode is the v0.2 baseline. `structural` mode is new in v0.3 and wraps the existing Style Lock mechanism with assertion-level granularity. `both` is for invariants where either failure mode is a defect.

### 5.2 Statement-writing tests

- **Atomicity**: one statement = one yes/no question. Compound statements ("X above Y AND Z to the left") split into two assertions.
- **Tolerance specified**: when geometry matters, give a numeric tolerance ("within ±0.3 cm of cluster mean" not "near"). Otherwise verifier hallucinates the threshold.
- **No nested negation**: "shallow does NOT lie below deep" is harder to verify than "shallow lies above deep". Phrase positively.

### 5.3 Severity ladder

| Severity | When to use |
|---|---|
| `BLOCKER` | violation makes figure misleading or wrong (e.g., CB below VB) |
| `MAJOR` | violation breaks reader comprehension but not factual claim |
| `MINOR` | violation is style or polish |

`BLOCKER` assertions should be a small set per fixture (the physics/chemistry invariants); `MAJOR` is comprehension; `MINOR` is the bulk.

## 6. `reference` block

### 6.1 `authority` levels

| Level | Behavior |
|---|---|
| `ground_truth` | reference image is canonical; build must match within drift tolerance |
| `guidance_only` | reference is an inspiration sketch; deviations OK if assertions pass |
| `known_defects` | reference is mostly authoritative but has documented errors (see § 6.2) |

v0.2 implicitly assumed `ground_truth`. N=1 dogfood issue #5 demonstrated reference can be wrong, which forced the `known_defects` mode.

### 6.2 `known_defects` — issue #5 protocol

When the author identifies a reference defect, log it here. L4.5 critique reads `known_defects` and **ignores or inverts** the corresponding reference comparison.

```yaml
reference:
  source: reference/golden_target_001.png
  authority: known_defects
  known_defects:
    - statement: "Reference shows two g(E_t) axis labels (top + bottom of lobe plot); only top is correct"
      override: "Build must show single g(E_t) label at top of lobe plot"
```

L6 drift check learns to skip the `tex_lines` underlying the defect; L4.5 critique is grounded against the override, not the reference.

## 7. Worked example: `golden_trap_depth_picture`

This is a v1 schema written by hand for the N=1 dogfood fixture. It will ship in step A of the v0.3 plan as `examples/golden_trap_depth_picture/briefing_semantic.yaml` and be the first validation case for whether v1 schema is sufficient.

```yaml
schema: figure-agent.briefing_semantic.v1
fixture: golden_trap_depth_picture

domain:
  fields: [polymer_chemistry, semiconductor_physics, statistical_mechanics]
  conventions:
    - "Nature Materials schematic conventions"
    - "Band-diagram conventions per Sze 'Physics of Semiconductor Devices'"
    - "Density-of-states sideways plots in trap-physics literature"

elements:
  - id: polymer_chain
    role: visual_anchor
    domain: polymer_chemistry
    must_depict:
      - "Three parallel chains drawn as wavy lines, ~14 segments each"
      - "S atoms drawn as filled amber circles attached to the backbone, not floating"
      - "Visible distinct S-density variation along chain to support 'S-rich segments' annotation"
    must_avoid:
      - "Featureless waves with no monomer-level texture"
      - "S atoms positioned independent of chain (free-floating)"

  - id: trap_levels_band_gap
    role: data_visualization
    domain: semiconductor_physics
    must_depict:
      - "Discrete horizontal trap-level markers between CB and VB rectangles"
      - "Shallow markers cluster near CB top; deep markers cluster near VB bottom"
      - "At least one continuation indicator (dashes or ellipsis) signaling 'more states than rendered'"
    must_avoid:
      - "Trap markers at the same Energy as CB or VB themselves (must be in the gap)"

  - id: trap_distribution_lobes
    role: data_visualization
    domain: statistical_mechanics
    must_depict:
      - "Two smooth Gaussian-like lobes opening rightward from a vertical axis"
      - "Shallow lobe (amber) above deep lobe (red/purple), with a visible gap between them"
      - "Inline labels 'shallow' and 'deep' anchored at each lobe's right side at the lobe peak height"
    must_avoid:
      - "Wrinkled/irregular lobe shapes from poorly-chosen control points"
      - "Lobes touching or overlapping vertically"

  - id: math_chain
    role: process_flow
    domain: statistical_mechanics
    must_depict:
      - "Left-to-right chain: I(t)∝t^-n  →  n  →  Debye exp(-t/τ) [with τ_d branch]  →  g(E_t)  →  shallow/deep mini-lobes"
      - "Each transition has an evidence arrow with consistent style"
      - "Σ=∫ icon precedes the chain as a launching pictogram (no arrow into the chain — icon is identifier, not transformation)"
    must_avoid:
      - "Inconsistent arrow geometry within the chain"

  - id: convergence_brace
    role: boundary
    domain: semiconductor_physics
    must_depict:
      - "Teal vertical curly brace on the right, grouping CB / VB / trap-levels / lobes as 'converged trap-depth picture'"
      - "All three evidence-row arrows from Experiment / Mathematical interpretation / Molecular origin terminate at the brace"

assertions:
  - id: cb_above_vb
    on: trap_levels_band_gap
    statement: "CB rectangle is rendered at higher pixel-y position than VB rectangle"
    verify_by: vision
    severity: BLOCKER

  - id: shallow_near_cb
    on: trap_levels_band_gap
    statement: "All shallow trap markers are vertically closer to CB than to VB (mean shallow y above midpoint of CB/VB y range)"
    verify_by: vision
    severity: BLOCKER

  - id: deep_near_vb
    on: trap_levels_band_gap
    statement: "All deep trap markers are vertically closer to VB than to CB"
    verify_by: vision
    severity: BLOCKER

  - id: lobe_orientation
    on: trap_distribution_lobes
    statement: "Two lobes open rightward (lobes' bulges point to positive x)"
    verify_by: vision
    severity: MAJOR

  - id: lobe_label_alignment
    on: trap_distribution_lobes
    statement: "Inline 'shallow' label is vertically within ±0.3 cm of upper lobe peak; same for 'deep' and lower lobe"
    verify_by: vision
    severity: MINOR

  - id: chain_arrow_consistency
    on: math_chain
    statement: "Every arrow within the I(t)∝t^-n → ... → mini-lobes chain uses evidenceArrow style with consistent line width"
    verify_by: structural
    severity: MAJOR

  - id: polymer_S_density_variation
    on: polymer_chain
    statement: "Visible spatial variation in S-marker density along chains (some sections denser than others)"
    verify_by: vision
    severity: MAJOR

  - id: brace_arrow_termination
    on: convergence_brace
    statement: "All three row-exit arrows have endpoints within ±0.4 cm of the brace's left vertical edge"
    verify_by: vision
    severity: MINOR

reference:
  source: reference/golden_target_001.png
  authority: known_defects
  known_defects:
    - statement: "Reference shows g(E_t) axis label at both top and bottom of the lobe plot"
      override: "Build must show single g(E_t) label at top only (per author 2026-05-04 review)"
```

## 8. How L4.5 critique consumes this

For each iteration, the critique brief auto-populates from `briefing_semantic.yaml`:

```
=== Semantic ground truth (from briefing_semantic.yaml) ===

REQUIRED ASSERTIONS (verify each — BLOCKER / MAJOR / MINOR per severity):
  [BLOCKER] cb_above_vb: CB rectangle ... [check vs PNG]
  [BLOCKER] shallow_near_cb: ...
  [MAJOR]   lobe_orientation: ...
  ...

REQUIRED ELEMENTS (verify each is depicted with required properties):
  polymer_chain (role: visual_anchor, must_depict):
    - Three parallel chains... [yes/no/partial]
    - S atoms attached to backbone... [yes/no/partial]
    - Visible S-density variation... [yes/no/partial]
  ...

REFERENCE: known_defects mode. Override:
  - "Build must show single g(E_t) label at top only"
  (do not flag missing bottom label as an issue)
```

Critique output is rejected if it includes findings that violate `must_avoid` clauses or contradict `known_defects` overrides. This blocks the v0.2 drift mode where the LLM proposed "add second g(E_t) for symmetry."

## 9. Open issues for v1 → v2

1. **Ontology library** — when N≥3 fixtures share `cb_above_vb` and similar, refactor into `ontology/physics/band_diagram.yaml` and let fixtures `imports:`. Defer until reuse is demonstrated.

2. **Verification automation** — `verify_by: vision` currently relies on host LLM. v2 may add `verify_by: bbox_compute` for assertions reducible to TikZ AST analysis, dropping LLM cost for that subset.

3. **Schema validation** — v1 has no JSON Schema or pydantic model; authors are trusted to write valid YAML. v1.1 should add `scripts/validate_briefing_semantic.py` that lints the file before L0 emits.

4. **Error message UX** — when assertions fail, what does the author see? The critique format must report which assertion ID failed and which element it was on. Output schema TBD.

5. **Reference defect detection** — currently `known_defects` is hand-maintained. L4.5 could detect *new* defects (build matches assertions but diverges from reference) and propose new `known_defects` entries. v1.1 work.

## 10. v1 → v0.3.0 implementation plan

Step A (next session): write `examples/golden_trap_depth_picture/briefing_semantic.yaml` matching § 7. Run `/fig_critique` manually with the brief enriched by reading the file. Compare critique output against the v0.2 ungrounded run. Target: ≥60% finding accuracy on this fixture (relaxed v0.3 gate).

Step B (next session): repeat on at least 2 more fixtures (`fig3_trapping_concept`, `n3_trial_01_trap_depth`) to surface schema friction.

Step C (after step B): refactor schema based on patterns observed; ship v0.3.0 with the slash command `/fig_brief_ground` that scaffolds a starter `briefing_semantic.yaml` from `briefing.md` + `spec.yaml`.

---

_v1 schema designed at the close of N=1 dogfood. Step A validation will be the first quantitative test of whether semantic grounding closes the v0.2 critique drift._
