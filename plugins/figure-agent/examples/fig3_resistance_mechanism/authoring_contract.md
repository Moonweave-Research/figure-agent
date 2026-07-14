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
- Keep `rho_60s` orthogonal to `n` in the composite figure's data plot. Do not place it in
  this schematic unless a declared measurement supplies a real scale and visual mapping.
- Show low-sulfur traps as discrete and S80 as continuous broad.
- Draw S60 as a representative discrete state set, never as one narrow smooth peak. The
  number and heights of state marks are illustrative, not measured peak-count evidence.
- Reserve the bottom of panel A as an outcome strip: the causal summary and qualitative
  `I(t)` inset must live together inside the panel, not in the A/B gutter.
- Present S60 on the left and S80 on the right as separate comparison units. Do not overlay
  their curves unless an explicit mixture claim is in the declared science.
- Present panel-A capture, release, and retained states in temporal order. That order must not
  be drawn or described as a net spatial drift through the film.
- Give the current-decay inset visible `$I(t)$` and `$t$` axes, even when it remains qualitative.
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
- Do not use source comments that contradict the briefing's `n`/breadth or `deep` boundaries;
  comments are part of the authoring context consumed by agents.

## Acceptance Gate

For this sprint, retain compile and semantic/geometry evidence and have a reader confirm
within 10 seconds that Fig 3 shows trapping during conduction causing current decay and
resistance increase. A clean machine gate is only a bounded screening result: publication
acceptance requires an explicit human scaffold/review verdict and is never implied by it.
