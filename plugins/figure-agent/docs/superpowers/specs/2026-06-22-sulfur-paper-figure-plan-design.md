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

## The 5-figure plan (mechanism-sequenced; Fig2/Fig3 numbering superseded by the current layout)

| Fig | Schematic (figure-agent) | Data graph (pipeline) | One-line role |
|---|---|---|---|
| **Fig1** | concept/structure of the sulfur polymer + the charge-trapping idea (whole-figure schematic) | — | "what this is about" |
| **Fig2** | MIM context → parallel conventional-versus-sulfur comparison → qualitative two-window transient readout | $I(t)$ + two-segment fit, composition-dependent $n$, and late-time deviation | "charge transport differs in the sulfur-rich copolymer" |
| **Fig3** | frequency-domain dielectric-response mechanism | dielectric-frequency response data | "frequency-domain dielectric response" |
| **Fig4** | trap energy landscape (shallow vs deep states, retention) | ISPD surface-potential decay curves + trap energy distribution N_t(E); S80 optimum | "the traps' energies / depths / lifetimes, quantified" |
| **Fig5 (last)** | actuation charge → OFF/float → reversed drive → reverse bend and slow recovery | qualitative response trace; measured data only when bound | "the trapped charge produces a polarity-dependent mechanical response (payoff)" |

## Figure-grouping rationale (current layout)
- The current layout places the transient transport panels in **Fig2**: the
  two-window $I(t)$ reading, composition dependence, and late-time departure
  make one coherent transport story. Its schematic is therefore a narrow
  comparison/context strip, not an invented quantitative plot.
- **Fig3** now carries the frequency-domain dielectric response. This supersedes
  the earlier dielectric-Fig2 / resistance-Fig3 numbering in this document.
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
- Fig2 is bound to `fig2_charge_transport_mechanism` as an active candidate;
  this is a workflow binding, not human or publication acceptance.
- Fig3 remains `planned_missing` for the frequency-domain dielectric-response figure.
- Fig4 is bound to `fig4_trap_energy_diagram`.
- Fig5 is bound to `fig5_cantilever_actuation_artifact_v2`.
- Prior dogfood, vault, and first-trial fixtures remain classified non-main evidence.

Placement changes must update the machine map and exact fixture `paper_binding`
together. Do not add worktree paths, branch names, commit hashes, copied detector
counts, or session next steps to this durable plan.
