# Sulfur-paper figure authority and handoff

This document preserves the durable scientific and workflow contracts for the
sulfur-polymer paper. It deliberately does not record a local worktree, branch,
commit, source hash, copied detector count, render freshness, or session-specific
next action. Those facts change during development and must be resolved from the
repository at run time.

## Machine source of truth

`docs/paper_figure_map.yaml` owns paper placement. Each active fixture carries
the same exact `paper_id`, `figure_id`, and `role_id` in `spec.yaml`. A fixture
is not a main-paper figure merely because its name or briefing resembles a role.

The current paper bindings are:

| Figure | Role | Fixture authority |
|---|---|---|
| Fig1 | overview, structure, and charge-trapping concept | full-figure candidate `fig1_updated_agent_redraw_v1`; human selection pending |
| Fig2 | transient charge transport and its mechanism context | Panel a schematic candidate `fig2_charge_transport_mechanism`; external 4-panel assembly is the paper artifact |
| Fig3 | frequency-domain dielectric response | fixed main slot; external quantitative full figure |
| Fig4 | ISPD retained-charge decay and trap-energy distribution | fixed main slot; external full figure pending data pipeline |
| Fig5 | cantilever actuation payoff | mechanism schematic candidate `fig5_cantilever_actuation_artifact_v2`; external full figure pending assembly |

Fig1, Fig2, and Fig5 are the three current Figure Agent authoring baselines.
Their active binding records only the declared fixture scope, never automatic
ownership of a full assembled paper figure. A fixture candidate does not imply
human acceptance, a promoted external artifact, or publication readiness.
Earlier figure fixtures and backend experiments remain non-main evidence unless
the machine map explicitly promotes them.

All other real fixtures are explicitly classified in the map as regression,
pilot, reference, superseded, SI, or sandbox evidence. They do not override an
active binding.

To recover live state, run:

```bash
./bin/fig-agent plan-check --strict
./bin/fig-agent status fig1_updated_agent_redraw_v1
./bin/fig-agent status fig5_cantilever_actuation_artifact_v2
```

Read current-candidate pointers and generated evidence directly. Never copy
their hashes, counts, or freshness into this handoff.

## Acceptance boundary

Strict compile, physics grounding, semantic assertions, collision checks, and a
fresh render are machine evidence only. They do not establish human acceptance,
publication acceptance, or a canonical promotion. Fig1's nested candidate must
remain `candidate_only` until a human gate explicitly changes that state.

## Fig1 scientific contract

### Structure and composition

- Panel A shows inverse vulcanization and the paper's polymer chemistry without
  inventing a cross-linked-network claim.
- Panel B is a qualitative composition series. Chain length and sulfur extent
  are explanatory cues, not measured molecular-weight or topology data.
- Chemical notation must preserve conventional aromatic, bond, bracket, and
  inverse-vulcanization heat-symbol grammar.

### Localized traps and electrical evidence

- Shallow and deep states use a consistent energy orientation and categorical
  colour grammar.
- The real-space host is amorphous; texture is explanatory and must not be read
  as lamellae, cells, or measured microstructure.
- The energy view is qualitative. Mobility edge, trap depth, escape, and DOS
  relationships must not acquire undeclared numerical values.
- Transient current uses the qualitative Curie-von Schweidler relationship.
  Rendered slope, exponent notation, and low/high-`n` ordering must agree.

### ISPD apparatus and derivation

- Charging is a gridless, two-terminal high-voltage state. Do not add a grid or
  a protective-ground symbol to the charging stage.
- The specimen is moved manually to the adjacent measurement station. Do not
  depict a motion stage, conveyor, or automatic scan.
- The measurement state uses a grounded conductive substrate.
- Sensing is by an induction-type electrostatic surface voltmeter at the
  SK-family level. It is not a Kelvin probe or KPFM schematic.
- The figure maps measured surface-potential decay `V_s(t)` to a qualitative
  derived trap distribution `g(E_t)`; it does not show a fitted dataset.

### Compact cantilever cue

- The specimen/cantilever is floating in the response scene.
- The driven electrode's grounded return belongs to its source circuit, not to
  the floating specimen.
- Maxwell attraction is the polarity-independent baseline; the illustrated
  charge-mediated Coulomb contribution must retain its declared ownership and
  direction.
- Any stronger mechanistic interpretation remains a paper-level human gate.

## Fig2, Fig3, and Fig4 role boundary

- Fig2 owns the transient charge-transport bridge: the MIM context, a
  conventional-versus-sulfur schematic contrast, and the qualitative early/late
  readout windows used by the bound data panels. The schematic does not replace
  those measured panels or prove a microscopic mechanism by itself.
- Fig3 owns the frequency-domain dielectric response as a fixed main-paper
  slot. Its quantitative artifact is authored by the data-plot pipeline, not
  by a Figure Agent schematic fixture. Do not silently
  reuse the earlier resistance-mechanism fixture as the new Fig3 authority.
- Fig4 is fixed as the main-paper ISPD slot and owns retained-charge decay,
  trap energy/depth/lifetime quantification, and the ISPD-derived distribution
  story. Its slot is not conditional on the current data-readiness state. The
  earlier `fig4_trap_energy_diagram`
  diagnostic trial is superseded and is not the current paper authority.
- Until the ISPD conditions and analysis pipeline are validated, Fig4 may show
  only the supported qualitative decay-shape comparison; shallow/deep
  assignment and numerical $E_t$, $g(E_t)$, or $\tau_d$ remain gated.
- A schematic must not turn qualitative state breadth into an undeclared
  numerical exponent, trap density, energy, or composition ranking.

## Fig5 scientific contract

Fig5 tests a polarity-reversal actuation sequence in one persistent apparatus,
not a generic high-voltage charging station and not an ESVM workflow.

1. **Actuation charge:** a nearby driven electrode biases the same cantilever
   across a visible air gap; attraction bends it while the charge state is
   established.
2. **OFF / float:** the source is switched off and the clip ground is opened.
   This electrical boundary is a visible stage, not an arrow caption.
3. **Reversed drive:** the drive polarity reverses and the charge-mediated force
   acts immediately in the opposite bending direction.
4. **Response and recovery:** the qualitative trace passes through the reverse
   excursion and then relaxes slowly toward the Maxwell-dominated direction.

Durable invariants:

- The cantilever, clamp axis, scale, thickness, electrode colour, electrode
  position, and air gap remain consistent across apparatus stages.
- The air gap remains non-contact. A capacitor-like cue does not claim measured
  capacitance.
- Trapped charge remains in the polymer body after source-off; the drawing must
  not imply that charge is stored on a disconnected clip.
- The Coulomb term follows the sign of `q_tr E` and can reverse. Maxwell
  attraction follows `E^2` and cannot explain reverse bending by itself.
- Force arrows share a visual scale when compared. Each arrow touches its
  physical owner and points toward its declared result.
- The response trace is qualitative unless a paper-local dataset is explicitly
  bound. It must still preserve event order, neutral origin, fast reverse
  response, and slower recovery.
- Video frames, measured angles, time constants, and exact plateau durations are
  not inferred from the schematic.

## Historical fixtures

- `fig5_actuation_mechanism` is a regression fixture for an earlier convention.
- `fig3_resistance_mechanism` remains regression evidence for an earlier
  placement, not a current main-figure binding.
- `fig4_trap_energy_diagram` is a superseded diagnostic trial, not the active
  Fig4 paper binding.
- `fig5_cantilever_mechanism_v1` is a superseded first authoring trial.
- `fig3_floating_clip_protocol` is SI/methods evidence with historical boundary
  assumptions.
- Fig1 vault fixtures are reference history, not active paper bindings.

Consult `docs/paper_figure_map.yaml` for the complete classification. If a
fixture changes paper role, update the map, its exact `paper_binding`, and the
resolver-derived tests together.
