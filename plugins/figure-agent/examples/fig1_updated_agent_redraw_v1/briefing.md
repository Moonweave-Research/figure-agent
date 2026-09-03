# Fig1 updated-agent redraw v1

> **Current handoff (2026-07-26):** the maintained render is the explicit
> nested candidate `review/failure-first/comparable-v3-repair-c5/repaired.tex`.
> It is a development baseline (`candidate_only`), not publication-final.
> The single redraw brief is `FIG1_CURRENT_CANDIDATE_HANDOFF.md`; reproducibility and
> next-figure instructions live in `docs/current-sulfur-paper-figure-state.md`.

This is an additive full-figure candidate, not a modification of the historical
v5f source. It must explain one narrative: sulfur-rich poly(S-r-DIB) has a
composition-dependent trap landscape, probed independently by transient
current and ISPD, with a mechanically visible bending response.

`authority.yaml` pins the historical visual/narrative baseline and the
human-reviewed Panel F physics correction. The candidate is deliberately
independent source: it may reuse explicitly selected catalog assets with bound
hashes and contracts, but never historical candidate source blocks or an
unreviewed electrical interpretation. The first render is a structural baseline,
not an aesthetic replacement for v5f; human review must judge whether its visual
language actually improves on the reference.

Panel C integrates the real-space and energy-domain trap views, but it is not a
privileged visual hero. Give it only the additional area needed to keep both
representations legible at the common reduction used for all panels. Panels
D--F are compact evidence modules: retain scientific relations, suppress
instrument decoration, and keep labels outside the depicted apparatus. The
publication target is Nature Communications. In Panel F, the voltage-source
return is grounded; the sample and cantilever remain electrically floating, and
the clip's own terminal is drawn open.

## §6. Physics invariants

- Panel C preserves a shared energy orientation: energy increases upward and
  deeper localized states sit lower than shallower ones. The population is one
  continuous distribution; shallower and deeper are shading-only zones of that
  single curve, and no shallow-to-deep ratio is drawn.
- Panel D preserves a constant-voltage transient-current comparison between the
  measured power law \(I(t)\sim t^{-n}\) and an idealised single-relaxation
  (Debye) model reference. The Debye trace has no straight-line regime and
  falls away from the power law; it is a model reference, not a measured
  control, and the curve carries relaxation-time language, not trap language.
- Panel E preserves the manual ISPD sequence: gridless two-terminal corona
  charging with no control grid, manual sample transfer, grounded measurement
  substrate, non-contact induction-type ESVM acquisition (never a Kelvin
  probe), and derivation of \(g(E_t)\). No relaxation-time span is drawn on
  the \(g(E_t)\) energy axis, and \(g(E_t)\) is the same single continuous
  distribution as Panel C with the axes swapped.
- Panel F preserves the floating topology: the grounded voltage-source return
  belongs to the driven-electrode circuit, not to the sample or cantilever, and
  the clip terminal is open. The panel asserts only the observation, that the
  floating cantilever bends away from the driven electrode; the polarity-
  dependent force is hypothesised, labelled \(q_{tr}\) (hyp.), and named only
  in the caption.

## Physics invariants

- Panel C energy increases upward; the mobility edge is above the thermal-escape
  annotation and deeper wells are lower in the energy landscape.
- Panel F the observed bend is away from the driven electrode; the grounded
  source return does not ground the sample or cantilever.

Machine checks support inspection only. A named human review is required before
any development-baseline or publication claim.
