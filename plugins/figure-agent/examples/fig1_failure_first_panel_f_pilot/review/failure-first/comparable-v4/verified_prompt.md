# Bound authoring execution: fig1_failure_first_panel_f_pilot

## Output and attempt boundary
- Resolve every repository path from the repository root.
- Do not change directory before resolving paths.
- Write exactly one new source to [examples/fig1_failure_first_panel_f_pilot/review/failure-first/comparable-v4/verified_generated.tex].
- Do not create an intermediate subdirectory beneath [examples/fig1_failure_first_panel_f_pilot/review/failure-first/comparable-v4].
- Start from the declared blank artifact; perform one attempt only.
- Do not inspect or repair historical generated sources.
- Read repository file content only from [AGENTS.md] and [styles/polymer-paper-preamble.sty] and [/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/slice2-fig3-comparable-runs/plugins/figure-agent/styles/snippets/panel-f-floating-cantilever.tex] and [/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/slice2-fig3-comparable-runs/plugins/figure-agent/styles/snippets/panel-f-floating-cantilever.contract.yaml] and [/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/.worktrees/slice2-fig3-comparable-runs/plugins/figure-agent/styles/snippets/panel-f-floating-cantilever.transfer.yaml]; all other required authoring context is already bound below.

## Mandatory standalone TikZ source requirements
- \documentclass[tikz,border=4pt]{standalone}
- \usepackage{tikz}
- \usepackage{polymer-paper-preamble}

## Style Lock authoring requirements
- Use only the preamble palette tokens cAmber, cBlue, cRed, cTeal, cGray, cLGray, cBrown, cArmAmber, and cAmberSphere, plus TikZ built-in black, white, and gray.
- Keep every explicit line width at or above 0.25pt.
- Do not use local \tiny or \scriptsize font overrides.
- Never use a single backslash as prose punctuation or a line-break substitute; use a space, or a valid double-backslash line break only in a node configured for multiline text.

## Semantic contracts and forbidden implications
- Shared neutral authoring task (verbatim):

# Fig1 scientific authoring task

Create a six-panel scientific overview of sulfur-rich polymer charge trapping.

- Panel A: poly(S-r-DIB) primary microstructure.
- Panel B: sulfur-composition variation using S60, S75, and S85 as representative chains from the S60/S70/S75/S80/S85 series.
- Panel C: localized traps in real-space and energy-space views.
- Panel D: kinetic evidence combining an SMU/MIM apparatus cue with an illustrative current-decay relation.
- Panel E: ISPD evidence combining a corona/probe apparatus cue with surface-potential decay and a derived trap-energy distribution.
- Panel F: trapped-charge Coulomb repulsion of a mechanically held, electrically floating cantilever near a driven electrode.

For Panel F, show one restrained mechanical support, a visible air gap between cantilever and electrode, a compact voltage source driving the electrode, and a source return terminating at ground. The ground belongs to the source circuit, not the sample. Do not add an electrical connector at the mechanical support. The Coulomb-force arrow points away from the driven electrode. Do not infer the support material or conductivity.

- Required panels:
  - [A] poly(S-r-DIB) primary microstructure
  - [B] Sulfur composition variation — 3 representative chains (S60/S75/S85) of paper's 5-sample range (S60/S70/S75/S80/S85)
  - [C] Localized traps (HERO
  - [D] Column D — Kinetic evidence (SMU+MIM apparatus + I(t)~t^-n result)
  - [E] Column E — ISPD-paired evidence (corona+probe apparatus + V_s decay + g(E_t) derived)
  - [F] Column F — trapped-charge Coulomb repulsion with a grounded voltage-source return and floating cantilever

- Semantic claim [F:required-object:panel_f.mechanical_jig]: The figure includes required object [panel_f.mechanical_jig].
- Semantic claim [F:required-object:panel_f.cantilever]: The figure includes required object [panel_f.cantilever].
- Semantic claim [F:required-object:panel_f.electrode]: The figure includes required object [panel_f.electrode].
- Semantic claim [F:required-object:panel_f.coulomb_force]: The figure includes required object [panel_f.coulomb_force].
- Semantic claim [F:required-object:panel_f.air_gap]: The figure includes required object [panel_f.air_gap].
- Semantic claim [F:required-object:panel_f.trapped_charge_markers]: The figure includes required object [panel_f.trapped_charge_markers].
- Semantic claim [F:required-object:panel_f.applied_voltage_cue]: The figure includes required object [panel_f.applied_voltage_cue].
- Semantic claim [F:required-object:panel_f.voltage_source]: The figure includes required object [panel_f.voltage_source].
- Semantic claim [F:required-object:panel_f.ground_reference]: The figure includes required object [panel_f.ground_reference].
- Locked invariant [F:protected-relation:mechanical_jig_holds_cantilever]: Protected relation holds: [mechanical_jig_holds_cantilever].
- Locked invariant [F:protected-relation:cantilever_separated_from_electrode_by_air_gap]: Protected relation holds: [cantilever_separated_from_electrode_by_air_gap].
- Locked invariant [F:protected-relation:coulomb_force_points_away_from_electrode]: Protected relation holds: [coulomb_force_points_away_from_electrode].
- Locked invariant [F:protected-relation:voltage_source_drives_electrode]: Protected relation holds: [voltage_source_drives_electrode].
- Locked invariant [F:protected-relation:voltage_source_returns_to_ground]: Protected relation holds: [voltage_source_returns_to_ground].
- Locked invariant [F:protected-relation:cantilever_remains_electrically_floating]: Protected relation holds: [cantilever_remains_electrically_floating].
- Locked invariant [F:forbidden-implication:panel_f.grounded_sample]: Forbidden implication is absent: [panel_f.grounded_sample].
- Locked invariant [F:forbidden-implication:panel_f.grounded_cantilever]: Forbidden implication is absent: [panel_f.grounded_cantilever].
- Locked invariant [F:forbidden-implication:panel_f.second_contact]: Forbidden implication is absent: [panel_f.second_contact].
- Locked invariant [F:forbidden-implication:panel_f.electrical_contact_at_jig]: Forbidden implication is absent: [panel_f.electrical_contact_at_jig].
- Machine assertion [panelF-coulomb-repulsion-points-away-from-electrode]: apply TikZ style [panelFCoulombRepulsionArrow] to the single draw/path command that owns this asserted relation.
- Do not imply physics or quantitative relations absent from the declared contracts.

## Curated visual assets
- Curated asset [panel_f_floating_cantilever]: [styles/snippets/panel-f-floating-cantilever.tex]
  - Reuse curated visual asset [panel_f_floating_cantilever] from [styles/snippets/panel-f-floating-cantilever.tex]. Do not redraw its owned geometry.
  - Load it once with [\input{snippets/panel-f-floating-cantilever.tex}].
  - Invoke [panel_f_floating_cantilever] through [\PanelFFloatingCantilever{prefix}{(x,y)}] and adapt only [prefix, origin].
  - Preserve its declared role: floating charge-trapping cantilever opposite a driven electrode.
  - Known pitfall: caller owns panel labels, force arrows, and whole-panel composition
  - Known pitfall: do not connect the floating cantilever to the source-return ground
  - Known pitfall: do not reinterpret the fixed mechanical boundary as an electrical contact
  - Do not transfer: grounded sample or grounded cantilever
  - Do not transfer: bidirectional actuation sequence

## Declared layout directives
- No optional layout contract selected.

## Optional shape-profile directives
- No optional shape profile selected.

## Optional composition-profile directives
- No optional composition profile selected.

## Provenance and publication boundary
- Declared model: gpt-5.5
- feedback_rounds: 0
- manual_repairs: 0
- filesystem_read_isolation: unavailable
- publication_acceptance: not_claimed
