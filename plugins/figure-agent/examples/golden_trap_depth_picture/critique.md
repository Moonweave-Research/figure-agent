---
schema: figure-agent.critique.v1
fixture: golden_trap_depth_picture
generated_at: 2026-05-04T01:25:00Z
iteration: 3 (with reference reconciliation)
verdict: revise
dogfood_meta:
  total_findings_proposed: 11
  applied: 11
  reverted_after_reference_comparison: 8
  net_kept: 2
  reference_aligned_accuracy: 2/11 (~18%)
  gate_threshold_v0_2_§7: ≥80% across N=5 fixtures
  gate_status: FAIL on first dogfood
findings_kept:
  - id: C007
    severity: MINOR
    category: label_placement
    tex_lines: [94]
    observation: "Row 1 evidence arrow path simplified from 4-segment to 3-segment terminating at brace top region. Aligns with reference geometry."
    status: applied
  - id: C008
    severity: NIT
    category: whitespace
    tex_lines: [74]
    observation: "Row 1 box title moved from inside box (y=2.36) to outside box (y=2.92), font 6.2 → 6.5. Matches reference convention and Row 3 `localized traps` pattern."
    status: applied
findings_reverted:
  - id: C001
    reason: "Reference image has TWO g(E_t) labels (top + bottom). My fix removed the bottom one; reverted then re-removed because user observed reference itself was wrong here. Final state: bottom label REMOVED."
    final: applied (post-reference-correction)
  - id: C002
    reason: "Reference has full 'Debye exp(-t/τ)' inline annotation in Row 1 box. My shortening to '(Debye)' diverged."
    final: reverted to reference
  - id: C003
    reason: "Caption lift +0.08cm; reference has captions at original lower position. Reverted."
    final: reverted to reference
  - id: C004
    reason: "Lobe label peak alignment; reference has labels at original positions. Reverted."
    final: reverted to reference
  - id: C005
    reason: "Energy axis extension to CB/VB; reference has shorter floating axis. Reverted."
    final: reverted to reference
  - id: C006
    reason: "Removed inline '(Debye)' annotation entirely; reference has full text. Reverted (along with C002)."
    final: reverted to reference
  - id: C009
    reason: "Added Σ=∫ → I(t) chain arrow; reference has no such arrow (intentional gap). Reverted."
    final: reverted to reference
  - id: C010
    reason: "Added '(single τ)' clarifier to τ_d; reference has plain τ_d. Reverted."
    final: reverted to reference
  - id: C011
    reason: "Added shallow ellipsis for symmetry; reference deliberately asymmetric (deep-only continuation). Reverted."
    final: reverted to reference
unaddressable_by_critique_layer:
  - "Row 1/Debye plot x-axis tick labels are visually cluttered/overlapping (#1 user observation)"
  - "Row 3 polymer chain visualization reads as 'wavy worms' rather than chemical structure (#2)"
  - "Row 3 'S-rich segments' dashed-box highlight does not communicate semantic meaning (#3)"
  - "Right-panel arrow overlaps near band-gap region (#4)"
  - "Right-panel shallow/deep lobes have wrinkled/irregular shape (#6)"
---

# Vision Critique — golden_trap_depth_picture (final, post-reference-reconciliation)

## What this critique log records

This is N=1 dogfood data for the L4.5 vision critique loop introduced in figure-agent v0.2.0. Three iterations of `/fig_critique` were run by the host Claude Code main loop without reference image grounding. Eleven findings were generated across iterations 1–3 and applied to the .tex source. The user then directed a comparison against the original reference image at `reference/golden_target_001.png`. **Eight of eleven findings (73%) were reverted** because they diverged from the reference's deliberate composition — including findings that read as confident, well-reasoned style improvements during isolated review.

## Findings net result

After reconciliation:
- **2 findings kept** (C007 arrow path, C008 title position) — both happened to align with reference
- **8 findings reverted** (C001–C006, C009, C010, C011) — drifted away from reference
- **1 finding kept after user override** (C001 final) — user observed that reference itself was wrong on the bottom `g(E_t)` label, so removal stands

`reference_aligned_accuracy = 2/11 ≈ 18%`. The architecture-v0.2-proposal.md §7 gate requires ≥80% finding accuracy across N=5 dogfood fixtures before auto-apply automation can ship. **First dogfood already fails the gate by 4×.**

## Meta finding: critique without semantic grounding drifts toward generic best practice

The drift is not random. Every reverted finding traded a *deliberate authorial choice* for a *generic style heuristic*:

- C001/reference: two axis labels are redundant *unless* the reader needs both top and bottom anchors when the lobes don't cleanly attach to one
- C002/C006: annotation duplicates the box title *unless* it serves as in-plot reading aid that loses meaning if abbreviated
- C009: chain has inconsistent connector geometry *unless* the absent first arrow signals "icon launches but isn't a transformation"
- C010: τ_d is orphaned *unless* the reader is expected to know τ_d is a comparison anchor
- C011: continuation indicators are asymmetric *unless* the deeper-traps-extend-down narrative is the point

Each "unless" is a piece of author intent that is invisible in the rendered PNG. A vision LLM reading only the PNG + briefing will not recover them.

## What's blocked by the critique-layer alone

The user's six observations on the post-revert build expose issues the L4.5 critique layer cannot reach by design:

| Observation | Why critique alone can't fix it |
|---|---|
| #1 x-axis tick labels overlap | L6 collision check already fires (39 candidates); needs auto-repair, not just report |
| #2 polymer chains read as worms | Author lacks chemistry domain knowledge in TikZ output; critique can flag but can't author |
| #3 S-rich segments highlight unclear | Briefing has no specification for visual semantic of the highlight |
| #4 band-gap arrow overlap | L6 collision; same as #1 |
| #5 reference's bottom g(E_t) was wrong | Reference is not infallible ground truth; needs author override path |
| #6 lobes are wrinkled | TikZ control-point quality; macro-level concern, not critique-level |

Five of six map to layers other than L4.5. One (#5) maps to the meta-question: when reference and critique disagree, who arbitrates?

## Conclusion for this fixture

`golden_trap_depth_picture` remains a `revise` figure for paper-grade publication. The two surviving polish improvements (C007 arrow path, C008 title placement) are kept. The remaining authorial gaps are **not addressable by adding more critique iterations**; they require either better authoring (briefing semantic grounding) or post-processing (Inkscape polish). Both are deferred per `docs/architecture-v0.2-proposal.md` §7.

## Implications for v0.3

The dogfood data forces a strategic conclusion: **L4.5 vision critique without briefing semantic grounding is fundamentally limited and will not reach the §7 gate by adding fixtures.** The next architecture iteration should not chase the gate via more critique tuning. It should add a layer that gives the system semantic understanding of *what the figure is supposed to depict* — chemistry of S-rich polymers, physics of trap distributions, expected visual conventions for band diagrams — so that critique can reason about meaning, not just style.

This is `Gap 1` in the active product direction (`session_strategic_direction_2026_05_04`). Concrete spec to follow in `docs/architecture-v0.3-briefing-semantic-grounding.md` (this session).

---

_Critique iteration log: iter1 (5 findings, all applied), iter2 (3 findings, all applied), iter3 (3 findings, all applied), reconciliation pass (8 reverted, 2 kept, 1 user-overridden). Total dogfood interactions: 11 findings. Source-of-truth contention surfaced and is the primary v0.3 input._
