---
schema: figure-agent.critique.v1
fixture: golden_trap_depth_picture
generated_at: 2026-05-04T02:15:00Z
iteration: 4 (grounded — cheap experiment A+B)
verdict: revise
grounding:
  - briefing.md §7 Author intent (must_depict + must_avoid + semantic_assertions, plain prose)
  - reference image attached (golden_target_001.png as drift tiebreaker)
findings:
  - id: G001
    severity: BLOCKER
    category: polymer_quality
    tex_lines: [125, 126, 127, 128]
    grounded_in: ["briefing §7 must_depict #1 'monomer-level texture'", "must_avoid 'Featureless waves'"]
    observation: "Row 3 renders three parallel chains as featureless smooth waves with sparse S markers floating above. The brief explicitly requires 'monomer-level texture' on each chain and 'sulfur atoms must be visually distinct (not just labels)'. Current chains have neither — the chains are pure sinusoidal `plot[smooth] coordinates` curves with no per-monomer geometry, and S atoms are 0.045 cm radius circles barely above the noise floor."
    suggested_fix: "Replace `plot[smooth] coordinates` with explicit zigzag or chair-conformation backbone (alternating up-down vertices ~0.4 cm apart), drawing each monomer as a discrete segment. Increase S marker radius to ≥0.10 cm and add bond lines connecting S to backbone vertices. Reference: Nature Materials polymer schematics."
    status: open
  - id: G002
    severity: MAJOR
    category: data_proportion
    tex_lines: [178, 179, 180, 181, 182, 183]
    grounded_in: ["briefing §7 must_depict #4 'shallow lobe peak ≈2×–3× taller than deep'"]
    observation: "Right-side g(E_t) lobes have approximately 1.2–1.5× height ratio (shallow slightly taller than deep), not the 2×–3× the brief specifies. Both lobes' Bézier control points produce similarly-sized bulges. The spec calls for shallow density to dominate, encoding higher trap-state density near CB."
    suggested_fix: "Increase shallow lobe peak amplitude — change line 178-180 control points to enlarge the shallow bulge (e.g., move (5.10,4.15) outward to (5.40,4.20) and pull the closing curve up), while keeping the deep lobe at current scale. Target visual ratio of shallow_peak_height / deep_peak_height ≈ 2.5."
    status: open
  - id: G003
    severity: MAJOR
    category: axis_geometry
    tex_lines: [158, 159]
    grounded_in: ["briefing §7 must_avoid 'Energy axis that doesn't span CB→VB range'"]
    observation: "Right panel `Energy` axis at x=1.25 currently spans y=1.15 to y=4.42, but CB box top is at y≈5.09 and VB box bottom is at y≈0.86. The axis arrow head terminates well below CB and the axis tail starts well above VB. Brief explicitly requires axis to span CB→VB so E_t is clearly interior."
    suggested_fix: "Extend axis: change line 158 to `\\draw[axis] (1.25,1.05) -- (1.25,4.95);` and re-center `Energy` rotated label at y=3.0. (This is identical to the previously-reverted C005 fix; the reference's short axis was a reference defect — author intent per briefing §7 is span-CB-to-VB.)"
    status: open
  - id: G004
    severity: MAJOR
    category: collision
    tex_lines: [54, 55, 80, 81]
    grounded_in: ["L6 collision report (39 candidates)", "implicit Style Lock — readability"]
    observation: "Both Row 1 plots (power-law and Debye reference) render x-axis tick labels (10^-3, 10^0, 10^3) at fontsize 4.3pt with tick spacing ~0.6 cm at scale. Visible label crowding at the rightmost tick of the small Debye plot in particular. L6 collision check has been reporting 39 candidates per compile; this is the most visually obvious instance."
    suggested_fix: "Either (a) reduce to two ticks per axis (drop 10^0 midpoint, keep only 10^-3 and 10^3); or (b) increase tick label fontsize to 5.2pt and reduce tick density on the Debye reference plot. (a) is cleaner because the plots are illustrative, not quantitative."
    status: open
  - id: G005
    severity: MAJOR
    category: collision
    tex_lines: [134, 135, 146, 147, 149, 150, 162]
    grounded_in: ["L6 collision report", "briefing §7 must_avoid 'Floating arrows not anchored'"]
    observation: "Right-panel band-gap region has multiple intersecting elements: the dashed E_t reference line at x=3.62, the row-exit arrow from Row 3 (line 147) entering near (12.40, 2.08), and the brace's interior curve. In the rendered PNG these elements visibly cross within ~0.3 cm of each other. While each individually is anchored, the convergence point reads as cluttered."
    suggested_fix: "Either (a) push the row-exit arrow's terminus inward by 0.3–0.5 cm so it ends inside the brace rather than crossing it, or (b) shorten the E_t dashed reference line so its top end stops below the entry point of the Row 3 arrow (e.g., y=4.6 instead of y=5.05)."
    status: open
  - id: G006
    severity: MINOR
    category: hierarchy
    tex_lines: [128, 129, 130, 132, 133]
    grounded_in: ["briefing §7 must_depict #3 'S-rich segments visually distinct'"]
    observation: "Row 3 'S-rich segments' dashed-box highlight at (4.20,1.47)–(5.85,2.02) is meant to mark a region of higher S density per the briefing addendum. But the S markers inside the highlight are visually no denser than those outside it — the foreach loop (line 128) places S atoms uniformly across the chain. The highlight loses its semantic communication."
    suggested_fix: "Add 2–3 additional S markers within the highlighted x-range (4.20–5.85) on the middle and bottom chains, OR remove the equivalent number of S markers OUTSIDE the highlight, OR draw the inside-highlight S markers in a slightly darker amber to make density variation visible."
    status: open
---

# Vision Critique — golden_trap_depth_picture (iter 4, grounded)

## Overall verdict

`revise`. The grounded critique applies briefing.md §7's Author Intent (must_depict + must_avoid + semantic_assertions) plus the attached reference image as a drift tiebreaker. Six findings produced, all citing concrete brief clauses. One BLOCKER (G001 polymer chain texture) blocks paper-grade publication; the rest are MAJOR/MINOR polish.

Compared to v0.2 ungrounded (iter 1–3): the brief's `must_avoid 'Featureless waves'` clause directly surfaced the polymer-chain BLOCKER (FN002 in baseline). The brief's `must_avoid 'Floating arrows not anchored'` and `must_avoid 'Energy axis doesn't span CB→VB'` clauses made findings G003 and G005 actionable — both were invisible to the v0.2 generic-style critique.

## Why this run differs from v0.2 ungrounded

In v0.2 (iter 1–3), the critique loop produced 11 findings of which only 3 (per N=1 adjudication) were useful (TP) — the rest drifted toward generic style heuristics without semantic ground. The grounded run does not produce findings unless a brief clause supports them. The shift in finding *kind*:

- v0.2 ungrounded: layout polish (label positions, arrow paths, redundant labels)
- v0.3 grounded: domain-content compliance (chain texture, lobe proportion, axis span)

The latter is what the figure actually needs to reach paper-grade.

## What the grounded run still misses

`G002` cites the lobe height ratio but does not address the *wrinkled / irregular shape* of the lobes (FN005 in baseline). The briefing addendum specifies proportion but not curve smoothness; absent that clause, the grounded critique still cannot reach lobe-shape quality. This suggests the briefing addendum needs a sixth must_depict bullet on macro-quality, OR lobe-shape belongs to L7 (Inkscape polish) anyway.

Two findings come from L6 collision data (G004, G005) where I cite the report directly. Without the briefing addendum's Floating arrows / Energy axis clauses, these findings would have looked identical to v0.2's stylistic noise. The brief plus the L6 report together produce actionable findings.

## Adjudication preview (for critique_adjudication.yaml update)

Self-adjudication (single-rater, author bias acknowledged):

| Finding | Category | Severity | Rationale |
|---|---|---|---|
| G001 polymer texture | TP | BLOCKER | Cited must_avoid clause; visible failure |
| G002 lobe height ratio | TP | MAJOR | Cited must_depict clause; visible failure |
| G003 Energy axis span | TP | MAJOR | Cited must_avoid clause; reference-defect override correctly applied |
| G004 x-axis tick collision | TP | MAJOR | Cross-cited L6 report; visible failure |
| G005 band-gap arrow overlap | TP | MAJOR | L6 + must_avoid; visible failure |
| G006 S-rich density | TP | MINOR | Cited must_depict clause; visible failure |

`FN: 1` — FN005 lobe wrinkled shape (briefing didn't specify smoothness)
`FP: 0`, `AMB: 0`

Predicted scores (subject to user confirmation):
```
TP=6, FP=0, AMB=0, FN=1
P_uw = 6/6 = 1.000
R_uw = 6/(6+1) = 0.857
F1_uw = 0.923

severity-weighted:
  TP: G001(4) + G002(2) + G003(2) + G004(2) + G005(2) + G006(0.5) = 12.5
  FN: FN005 (0.5)
P_w = 1.000
R_w = 12.5/13.0 = 0.962
F1_w = 0.981
```

vs. v0.2 baseline `(P_w=0.313, R_w=0.200, F1_w=0.244)` — this is a `+0.74` absolute F1_w jump. **Far exceeds the 0.15 cheap-intervention-sufficient threshold per docs/critique-evaluation-rubric-v1.md §6.**

## Caveats on the dramatic improvement

The grounded run's near-perfect P=1.0 has three confounders worth flagging before declaring victory:

1. **Single-rater bias.** I authored both the findings and the adjudication. An independent reviewer might reclassify some TPs.
2. **Brief-overfit risk.** The briefing addendum was written *with knowledge of the v0.2 failures*. "Featureless waves" is in must_avoid because the author already saw the polymer-chain issue. The grounded critique succeeding on that finding is partly the briefing telling it where to look. On a fresh fixture without that prior knowledge, performance would likely drop.
3. **Coverage scope is bounded by the briefing.** P=1.0 is achievable because findings are limited to brief clauses — it's a *constrained* high precision. FN coverage is also bounded: brief didn't mention lobe shape, so lobe shape stays uncaught.

These caveats argue for: (a) replicating on at least one new fixture where the briefing is written *before* failure modes are observed, and (b) targeting calibration via inter-rater agreement when a second human is available.

## Implication for v0.3 architecture decision

Per `docs/critique-evaluation-rubric-v1.md §6`:
- F1_w improvement ≥ 0.15 → **cheap intervention sufficient**

The +0.74 jump is decisive at this fixture. Recommended scope-down for v0.3: **ship the briefing.md §7 convention and the critique_brief.py reference attachment** as v0.3.0 surface. Defer the full `briefing_semantic.yaml` schema layer until N≥2 fixtures show the cheap intervention plateauing or breaking.

The BLOCKER FN (FN002 polymer texture) was caught by the cheap intervention as G001. The structural argument that motivated the schema-layer proposal in `architecture-v0.3-briefing-semantic-grounding.md` is weakened by this evidence — semantic grounding works at a *prose* layer, no new file type needed yet.

---

_Iter 4 grounded run. Cheap experiment outcome: F1_w 0.24 → 0.98 (predicted, single-rater). v0.3 spec recommendation: scope-down to briefing-prose convention + reference-attached brief. Schema layer (`briefing-semantic-schema-v1.md` draft in working tree) deferred until cheap intervention plateaus._
