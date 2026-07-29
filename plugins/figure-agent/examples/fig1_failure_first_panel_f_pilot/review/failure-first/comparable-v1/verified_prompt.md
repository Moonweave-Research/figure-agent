# Bound authoring execution: fig1_failure_first_panel_f_pilot

## Output and attempt boundary
- Resolve every repository path from the repository root.
- Do not change directory before resolving paths.
- Write exactly one new source to [examples/fig1_failure_first_panel_f_pilot/review/failure-first/comparable-v1/verified_generated.tex].
- Do not create an intermediate subdirectory beneath [examples/fig1_failure_first_panel_f_pilot/review/failure-first/comparable-v1].
- Start from the declared blank artifact; perform one attempt only.
- Do not inspect or repair historical generated sources.
- Read repository file content only from [AGENTS.md] and [styles/polymer-paper-preamble.sty]; all other required authoring context is already bound below.

## Mandatory standalone TikZ source requirements
- \documentclass[tikz,border=4pt]{standalone}
- \usepackage{tikz}
- \usepackage{polymer-paper-preamble}

## Style Lock authoring requirements
- Use only the preamble palette tokens cAmber, cBlue, cRed, cTeal, cGray, cLGray, cBrown, cArmAmber, and cAmberSphere, plus TikZ built-in black, white, and gray.
- Keep every explicit line width at or above 0.25pt.
- Do not use local \tiny or \scriptsize font overrides.

## Semantic contracts and forbidden implications
- Required panels:
  - [A] poly(S-r-DIB) primary microstructure
  - [B] Sulfur composition variation — 3 representative chains (S60/S75/S85) of paper's 5-sample range (S60/S70/S75/S80/S85)
  - [C] Localized traps (HERO
  - [D] Column D — Kinetic evidence (SMU+MIM apparatus + I(t)~t^-n result)
  - [E] Column E — ISPD-paired evidence (corona+probe apparatus + V_s decay + g(E_t) derived)
  - [F] Column F — trapped-charge Coulomb repulsion with a grounded voltage-source return and floating cantilever
- Binding fixture briefing (verbatim):

# Fig1 failure-first Panel F pilot

## §1. Intent

Test whether Figure Agent can turn a reviewed complex-panel defect into exact,
multiscale evidence and one bounded repair without pretending that machine
checks establish publication quality.

## §3. Correctness rules

- Panel F must show one understated fixed mechanical boundary holding the
  cantilever: a restrained support rail, short structural stem, and shallow jaw.
- Panel F must show a compact voltage source driving the right electrode.
- The source return must terminate at ground; the ground belongs to the source
  circuit, not to the sample.
- The sample and cantilever must remain electrically floating, with no
  electrical connector at the mechanical jig.
- The holder's material and conductivity are not established by the reference;
  leave them electrically unmodeled rather than declaring an insulating or
  conducting clip.
- A compact source symbol is sufficient; a detailed instrument display is not required.
- The historical v5f source must remain unchanged.

## §6. Physics invariants

- The cantilever must remain separated from the right electrode by an air gap.
- The Coulomb-force arrow must point away from the right electrode.
- Correcting the source/ground topology must not alter charge, cantilever,
  electrode, air-gap, or force relations.

## §7. Review constraints

- Raw, verified, and repaired states must use the same model/input/budget
  contracts.
- Review must include whole, panel, object/relation, and zoom evidence.
- A named human must supply scientific and visual verdicts separately.
- Machine gates must not claim publication acceptance.

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
- Do not imply physics or quantitative relations absent from the declared contracts.

## Curated visual assets
- No curated visual assets selected.

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
