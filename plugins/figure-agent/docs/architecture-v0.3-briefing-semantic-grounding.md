# Architecture v0.3 — Briefing Semantic Grounding

**Status:** DRAFT (2026-05-04)
**Trigger:** First v0.2 dogfood on `golden_trap_depth_picture` (N=1) failed §7 gate by 4× (2/11 ≈ 18% accuracy vs ≥80% threshold). Failure is structural, not tunable.
**Predecessor:** `architecture-v0.2-proposal.md` (ACCEPTED, shipped as v0.2.0)
**Active product direction:** `quality-kernel-goal.md`, `session_strategic_direction_2026_05_04` (memory)

---

## 1. Problem statement

L4.5 vision critique introduced in v0.2 reads the compiled PNG plus the textual briefing and proposes findings. First dogfood produced 11 findings across 3 iterations on a single fixture; 8 of them (73%) were reverted after comparison with the human-curated reference image because they replaced *deliberate author intent* with *generic style heuristics*.

Examples of drift (full list in `examples/golden_trap_depth_picture/critique.md`):
- Removed a deliberately-redundant axis label (the redundancy was an anchor for sideways g(E_t) reading)
- Shortened an in-plot annotation that the box title already names (the annotation served as in-plot reading aid)
- Added a chain arrow where the absent arrow signaled "icon launches the chain but isn't a transformation"
- Added "(single τ)" clarifier to a symbol whose unclarified form was the contrast device
- Added a symmetric continuation indicator where the asymmetry was the narrative point

These drifts are not noise. They are the systematic output of a vision LLM reading PNG + briefing without access to the author's *semantic intent* — the chemistry, physics, and reading-flow conventions that determined every choice the figure makes.

User observations on the post-revert build then exposed five additional issues that the critique layer cannot address regardless of accuracy improvements:
1. x-axis tick label overlap (L6 collision concern)
2. Polymer chains read as wavy worms, not chemical structure (L1 briefing / L3 author concern)
3. S-rich segments dashed-box highlight semantically unclear (L1 briefing concern)
4. Band-gap arrow overlap (L6 collision concern)
5. shallow/deep lobes have wrinkled/irregular shape (L3 macro/curve quality concern)

L4.5 cannot reach issues 2, 3, 5 by design — they require *authorship-time* semantic grounding, not *post-compile* style critique.

## 2. Strategic conclusion

**Adding more L4.5 fixtures will not reach the §7 gate.**

The §7 gate (≥80% finding accuracy across N=5 fixtures) was designed assuming critique-layer improvements (better prompts, reference grounding, iteration) could close the gap. The N=1 dogfood demonstrates the gap is structural — even with reference grounding, two failure modes remain:

- **Reference can be wrong.** First dogfood already produced one user-confirmed case (`#5`, bottom `g(E_t)` label was a reference defect). Reference grounding shifts the source of truth but doesn't make it infallible.
- **Reference doesn't capture intent for un-rendered alternatives.** Critique can match the reference but cannot reason about whether the reference itself made the right choice given the briefing's communicative goal.

Both failure modes require *semantic understanding of what the figure is supposed to depict*, not better visual style critique.

## 3. Proposal: L0 Briefing Semantic Grounding layer

Insert a new layer between L1 (briefing) and L3 (TikZ author) that converts briefing prose into a **structured semantic schema** the rest of the pipeline can reason about. The layer is host-orchestrated, like L4.5.

### 3.1 Inputs
- `briefing.md` (existing, prose)
- `spec.yaml` (existing, structural)
- Optional: domain ontology references (chemistry, physics, plot conventions)
- Optional: reference image for vision-aided semantic extraction

### 3.2 Outputs
A new file `briefing_semantic.yaml` with structured semantic intent. Sketch:

```yaml
schema: figure-agent.briefing_semantic.v1
fixture: golden_trap_depth_picture
domain: [polymer_chemistry, semiconductor_physics, statistical_mechanics]

elements:
  - id: polymer_chain
    role: visual_anchor
    domain: chemistry
    must_depict:
      - "Repeating monomer units, not abstract waves"
      - "S atoms bound to backbone, not floating circles"
      - "At least 2 distinct chain sections to support 'S-rich segments' highlight"
    reference_conventions: ["Nature Materials chemical-structure schematics"]

  - id: trap_distribution_lobes
    role: distribution_visualization
    domain: physics
    must_depict:
      - "Two-lobe density g(E_t) with shallow (near CB) and deep (near VB) clusters"
      - "Lobe area ∝ trap state count; shape may be smooth Gaussian-like or discrete-summed"
    reference_conventions: ["sideways DOS plots in band-diagram contexts"]

  - id: band_diagram
    role: energy_axis_visualization
    domain: physics
    must_depict:
      - "CB box at higher Energy than VB box (vertical convention)"
      - "Trap levels as discrete horizontal markers between CB and VB"
      - "Energy axis is monotonic; arrow conventionally points UP for higher Energy"

semantic_assertions:
  # Constraints L4.5 critique can verify against the rendered figure
  - "shallow trap markers are vertically closer to CB than to VB"
  - "deep trap markers are vertically closer to VB than to CB"
  - "g(E_t) shallow lobe peak vertically aligns with shallow trap cluster mean"
  - "S-rich segments highlight overlaps a chain region with above-average S density"
```

### 3.3 Generation modes
- **Manual** (v0.3.0): author writes `briefing_semantic.yaml` by hand, possibly with LLM assistance from a `/fig_brief_ground` slash command (host-orchestrated). Schema is the contract; LLM is the convenience.
- **Vision-grounded** (v0.3.1+): a separate slash command reads `reference/*.png` (when present) and proposes a draft `briefing_semantic.yaml` for author review. This is the "briefing automation via vision loop" that memory has tagged as Gap 1.

### 3.4 How it changes downstream layers

**L3 (author):** TikZ author (human or LLM) consumes `briefing_semantic.yaml` in addition to briefing.md. The "must_depict" lists give chemistry-aware authoring guidance: "polymer_chain → repeating monomers, not abstract waves." This addresses observations #2, #3 from N=1 dogfood.

**L4.5 (critique):** Critique brief includes `semantic_assertions` and `must_depict` lists. Critique becomes:
```
For each semantic_assertion: does the rendered figure satisfy it? (BLOCKER if violated)
For each must_depict bullet: is it visible? (MAJOR if missing)
For each reference_convention: does the figure follow it? (MINOR if violated)
... (existing aesthetic rubric)
```
This grounds critique in author intent and prevents the generic-best-practice drift demonstrated by the N=1 dogfood.

**L6 (drift check):** Reference comparison gains a tiebreaker — if reference and rendered build disagree on a `semantic_assertion`, the assertion wins (reference can be defective).

### 3.5 Backward compatibility
Pre-existing fixtures without `briefing_semantic.yaml` skip L0. L4.5 falls back to current behavior (style-only critique). No breaking change to existing slash commands.

## 4. Out of scope for v0.3

These are the un-fixed observations from N=1 dogfood that remain v0.3+ work:

- **L6 auto-repair (issues #1, #4):** L6 collision detection is already producing 39 candidates per compile but is report-only. Auto-repair would tweak label positions / arrow paths to resolve overlaps. Out of scope here; tracked separately.

- **L7 Polish / Inkscape (issue #6):** TikZ macro quality (e.g., wrinkled lobes from poor control points) is partly addressable by macro improvements (`SmallLobe`, lobe-drawing macros) and partly by post-process polish in Inkscape. Both deferred per v0.2 §7.

- **Reference defect protocol (issue #5):** When semantic grounding flags a reference as inconsistent with `briefing_semantic.yaml`, the rendered build can override. Detailed override flow deferred to v0.3.1.

## 5. Open questions

1. Schema completeness: the `briefing_semantic.yaml` sketch in §3.2 is illustrative. Real schema needs design pass — how to express "shallow lobe peak aligns with shallow cluster mean" formally enough for L4.5 to verify but loose enough that the author isn't writing pixel-coordinates.

2. Domain ontology source: chemistry/physics conventions can be encoded in the schema, in a separate `ontology/` directory, or assumed to be in the LLM's training data. Trade-offs on portability vs verbosity.

3. Adoption gradient: do we require `briefing_semantic.yaml` for new fixtures (forcing-function), or stay opt-in? Memory entry `byte_identity_vs_default_style` suggests strict requirements break flagship-macro patterns; lean opt-in.

4. Cost of vision-grounded mode: §3.3 mode b reads reference PNG via host main loop. Subscription tokens only, but adds critique-bandwidth-comparable load to authoring time. Acceptable?

5. Relation to Athena-style semantic kernel ideas: is there overlap with Athena workspace's semantic-grounding work, or is this strictly a figure-agent layer?

## 6. Decision points

| Decision | Owner | Default |
|---|---|---|
| Adopt v0.3 direction (briefing semantic grounding as next layer) | author | YES — N=1 dogfood is sufficient evidence |
| Schema design pass next session | author | YES |
| Vision-grounded mode (§3.3 mode b) included in v0.3.0 or deferred to v0.3.1 | author | DEFER — manual schema first, automation after schema is stable |
| Require `briefing_semantic.yaml` for new fixtures | author | NO — opt-in until at least 3 fixtures validate the schema |

## 7. Acceptance criteria for v0.3 graduation

- [ ] `briefing_semantic.yaml` schema designed, documented, and validated on `golden_trap_depth_picture`
- [ ] L4.5 critique brief consumes `semantic_assertions` and produces grounded findings on at least 1 fixture
- [ ] N≥3 dogfood runs at ≥60% finding accuracy (relaxed from §7's ≥80% — semantic grounding is the experiment, not yet the production gate)
- [ ] Author can override reference using semantic assertions (issue #5 protocol)

`§7 gate (≥80% on N≥5)` is *postponed* until briefing semantic grounding is validated; tightening the gate before the underlying capability lands is premature.

---

_Authored at the close of the v0.2.0 first dogfood session. The N=1 critique log is the primary input to this proposal and lives at `examples/golden_trap_depth_picture/critique.md`. This document supersedes nothing yet — `architecture-v0.2-proposal.md` remains active. v0.3 will live next to v0.2, not replace it._
