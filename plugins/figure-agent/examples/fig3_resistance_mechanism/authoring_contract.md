# Authoring Contract — fig3_resistance_mechanism

## Role

Produce a three-column, Nature Communications-style explanatory schematic: **(a) trapping
mechanism → (b) qualitative transient-current response → (c) composition-dependent
trap-energy landscape**. It explains the interpretation of the experimental transient-current
data; it must not impersonate that data.

## Must Preserve

- Panel A uses vertical `energy, E`, sign-agnostic carrier glyphs, and temporal capture → release
  → representative slow-release occupancy. Every path endpoint attaches to a named carrier or trap anchor.
- Panel B is the only `I(t)` graph. It has visible `current, I(t)` and `time, t` axes, no ticks or
  values, and the explicit qualifier `qualitative CvS decay (not measured data)`.
- Panel B expresses only `I(t) ∝ t⁻ⁿ`, `trapping → I↓`, and `I=V/R → R↑`; it does not imply a
  fitted exponent, a composition comparison, or an experimentally sampled trace.
- Panel C uses the same vertical energy orientation as A. S60 is a representative set of discrete
  horizontal energy states; S80 is a continuous broad energy support. They are separate units.
- A broader support cue is qualitative and must not equate geometric width directly with `n` or read
  as a fitted density-of-states envelope.
- Encode S80 as a dense, irregular field of horizontal state marks over a broader vertical span; do
  not use a symmetric silhouette, closed contour, or hard-edged interior container to stand for it.
- Place the Panel A terminal-state annotation as unboxed text in deliberate whitespace. A knockout
  label is only a last resort after a verified background conflict, never a default detector workaround.
- When a leader is necessary to disambiguate a semantic annotation, name the leader target coordinate
  and the label node, place that node at the named coordinate, and declare the relation in
  `named_endpoint_assertions.required_node_bindings`. Do not add a leader merely as decoration.
- Keep the schematic slim, dense, and readable at a main-figure scale.

## Must Not Infer

- No measured data, numeric ticks, fitted values, time window, carrier polarity, trap chemistry,
  spatial trap network, fixed peak count, or stronger-trapping-as-well-depth claim.
- Do not use spectrum/bar-chart/Fourier-style sticks with a horizontal `g(E)` axis; this fixture
  needs an energy-landscape grammar, not a density-of-states plot.
- Do not place an `I(t)` micrograph in Panel A or create an orphan plot in an inter-panel gutter.

## Acceptance Gate

Machine checks may screen source, geometry, and label relations. They do not establish scientific
or publication acceptance: a human must explicitly review the causal reading and finish quality.
