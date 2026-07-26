# Sulfur-Polymer Paper — Figure Plan (canonical)

> **Status:** approved narrative plan. `docs/paper_figure_map.yaml` is the
> machine-readable authority for current fixture placement; fixture names in
> this design document are explanatory and cannot override that map.

## Spine (paper's central argument)
**Charge-trapping characterization → mechanism synthesis.** Multiple electrical
measurements are assembled into the complete picture of sulfur-polymer charge trapping
(composition-tunable, S80 optimum), and the trapped charge then drives a cantilever
device (application payoff). NOT a narrow ISPD-only characterization; NOT a pure
device paper.

## Key structural fact: every main figure is a COMPOSITE
Each figure = **[explanatory/mechanism SCHEMATIC] + [DATA GRAPH]**. Figures are NOT
graph-only; a slim, dense, well-explained schematic makes the mechanism legible to
the reader. **figure-agent's job = the SCHEMATIC portion of every figure** (cell
structure, current flow, trapping, why composition matters, the meaning of the fit,
energy landscapes, actuation). The DATA GRAPHS come from the data pipeline
(Origin / Graph Hub). The two are composited into the final figure.

Design constraint for the schematics (user, verbatim intent): "얄쌍하게 오밀조밀하게,
비대하지 않게" — slim, compact, dense, not bloated; explain just enough for human
understanding.

## The 5-figure plan (approach B — mechanism-sequenced)

| Fig | Schematic (figure-agent) | Data graph (pipeline) | One-line role |
|---|---|---|---|
| **Fig1** | concept/structure of the sulfur polymer + the charge-trapping idea (whole-figure schematic) | — | "what this is about" |
| **Fig2** | dielectric / polarization-response mechanism | ε_r vs composition + P–E loops | "tunable dielectric that stores charge" |
| **Fig3** | cell structure → current flows → charge gets trapped → current↓ / resistance↑; meaning of the trap-conduction-law fit; why a given composition traps better | R(t)↑ over time + trap-law fit, composition series, 1 representative reference | "direct evidence: trapping happens during conduction (the bridge)" |
| **Fig4** | trap energy landscape (shallow vs deep states, retention) | ISPD surface-potential decay curves + trap energy distribution N_t(E); S80 optimum | "the traps' energies / depths / lifetimes, quantified" |
| **Fig5 (last)** | actuation charge → OFF/float → reversed drive → reverse bend and slow recovery | qualitative response trace; measured data only when bound | "the trapped charge produces a polarity-dependent mechanical response (payoff)" |

## Figure-grouping rationale (resolves the user's open questions)
- **Resistance → Fig3 (its own figure), NOT Fig2, NOT merged with ISPD.** Three reasons:
  (1) physical-family — ε_r + P–E are polarization/dielectric response (one family → Fig2);
  R(t)↑ is trapping-transport kinetics (different family). (2) narrative-bridge — R(t)↑ is
  the first DIRECT trapping evidence, bridging "is a dielectric" (Fig2) → "quantify the
  traps" (Fig4). (3) weight — resistance carries its own analysis (law fit + composition +
  reference) — too much for a Fig2 panel.
- **P–E loop → Fig2** (paired with ε_r as the dielectric/polarization response).
- **Reference samples → 1 representative in main Fig3; full set → SI.**

## Implications for figure-agent (the tool)
- figure-agent draws the SCHEMATIC sub-content of Fig1–Fig5 (not graph-only Fig1/Fig5 as
  earlier mis-scoped). The Coulomb-well depth-fill lever + bounded-offset primitive already
  built are reusable schematic levers (the well schematic fits Fig2/Fig4 trap-energy content).
- The existing fixtures must be re-scoped to this plan: fig2_trap_design_space (design-space
  schematic) does not map cleanly; its well/energetics sub-parts are reusable, its
  "beyond conventional dielectrics" design-space framing is a broader claim than this paper makes.
- Slice 1 premium levers should be authored against the schematic demands of THESE figures
  (e.g. Fig3 mechanism schematic, Fig4 energy landscape), not a bare primitive.

## Current placement contract

- Fig1 is bound to `fig1_updated_agent_redraw_v1` through its explicit current-candidate pointer.
- Fig2 remains `planned_missing`; this is advisory, not a hidden fixture assignment.
- Fig3 is bound to `fig3_resistance_mechanism`.
- Fig4 is bound to `fig4_trap_energy_diagram`.
- Fig5 is bound to `fig5_cantilever_actuation_artifact_v2`.
- Prior dogfood, vault, and first-trial fixtures remain classified non-main evidence.

Placement changes must update the machine map and exact fixture `paper_binding`
together. Do not add worktree paths, branch names, commit hashes, copied detector
counts, or session next steps to this durable plan.
