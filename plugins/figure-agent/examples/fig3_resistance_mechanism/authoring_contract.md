# Authoring Contract — fig3_resistance_mechanism

## Role

This fixture is the schematic half of the paper's Fig 3 composite. It explains why
transient-current resistance data are direct evidence of charge trapping during
conduction, bridging Fig 2 dielectric response to Fig 4 trap-energy quantification.

## Must Preserve

- Read left to right: applied bias cell -> dispersive trapping walk -> I(t) decay / R increase -> trap-energy distribution broadening.
- Keep the carrier sign-agnostic. Do not imply electron-only or hole-only transport.
- Encode Curie-von Schweidler behavior as qualitative decay, not a measured data plot.
- Keep `n` as the fitted Curie-von Schweidler exponent. The schematic may show
  trap-distribution breadth, but must not equate geometric width directly with `n`
  without a declared model or calibration.
- Keep `rho_60s` orthogonal to `n` as a magnitude cue.
- Show low-sulfur traps as discrete and S80 as continuous broad.
- Name the panel-A vertical axis `energy, E`; never leave bare `E` beside applied-voltage
  terminals where it can be read as an electric field.
- Bind every capture/release path endpoint to a named carrier or trap-state anchor. Do not
  tune path and state coordinates independently.
- Keep the schematic slim, compact, and dense, not bloated.

## Must Not Infer

- Do not add unverified trap chemistry such as S-S radicals or sulfur clusters.
- Do not add quantitative tick values or measured curve parameters.
- Do not convert this schematic into the data-graph half of Fig 3.
- Do not encode stronger trapping as well depth.
- Do not label a distribution `deep` unless the panel declares its transport-energy reference.
- Do not infer the direction or magnitude of a breadth-to-`n` relation from the
  schematic alone.
- Do not use “trap network”; the intended phrase is trap-energy distribution or landscape.

## Acceptance Gate

The fixture is acceptable for this sprint when compile succeeds, the current C001
label/curve overlap is removed, and a reader can state within 10 seconds that Fig 3
shows trapping during conduction causing current decay and resistance increase.
