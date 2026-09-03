# Fig1 current-candidate handoff — sulfur-rich polymer charge trapping

## Use this first

This is the single working brief for redrawing or refining Fig1. It is a development baseline, not a publication-final claim.

- **Active paper role:** Fig1, overview of structure and charge trapping in sulfur-rich poly(S-r-DIB).
- **Working source:** `fig1_updated_agent_redraw_v1.tex` at the fixture root.
- **Working render:** `build/fig1_updated_agent_redraw_v1.png`.
- **Machine pointer:** `review/current-candidate.json`. If it later disagrees with this document, the pointer wins and this handoff must be refreshed.
- **Authority state:** `promoted_to_canonical_root`; human selection and publication acceptance are pending.

The fixture root was promoted byte-for-byte from `review/failure-first/comparable-v3-repair-c5/repaired.tex`, which is preserved as the promotion origin and must not be edited as the working source. Promotion moved the source only: it grants no acceptance, and passing compile or deterministic checks still does not make this a paper artifact.

Do not edit the historical v5f vault as the working source. It is the visual and narrative reference, not the active paper fixture.

## The one-sentence story

Inverse-vulcanized sulfur-rich poly(S-r-DIB) has composition-dependent localized trap states; transient current and ISPD independently expose their kinetics and distribution, and retained charge produces a mechanically visible Coulomb response in a floating cantilever.

The reader should move from **what the material is** (A), through **how sulfur content is encoded** (B), to **what traps mean physically** (C), then to the three compact evidence/payoff modules (D--F).

## Figure architecture and visual language

- Use the established 2 + 1 + 3 hierarchy: A/B share the top row, C spans the middle row because it must keep real-space and energy-domain views legible, and D/E/F are equal compact modules on the bottom row.
- C is not a semantic or typographic hero. Its extra area is functional; keep title treatment and visual weight commensurate with the other panels.
- Keep the page quiet and journal-like: white background, thin pale-gray panel dividers, restrained labels, and no decorative instrument detail.
- Palette ownership is fixed: amber/brown for sulfur and polymer, blue for shallow traps, red for deep traps and Coulomb response, dark gray for structure/apparatus, light gray for subordinate boundaries.
- Use italic math for physical variables. Do not add unexplained numerical values or fitted parameters. The working print target is height-limited at 166.8 mm wide, with explicit font sizes no smaller than 5 pt.
- At full, 50%, and 33% views, labels must remain in clear lanes rather than touching beams, arrows, plot traces, frames, or apparatus wires.

## Panel contracts

### A — Sulfur-rich poly(S-r-DIB)

Show elemental S8 and 1,3-DIB entering thermally driven inverse vulcanization and yielding a **representative DIB-linked repeat unit** with variable polysulfide rank `S_x`/`S_y`. The drawn S-C(CH3)2-Ar connectivity stands; the name bis(thiocumyl) appears in no manuscript document and must not be used.

- S8 is a reactant, not a decorative icon; the triangle means heat.
- Draw the DIB aromatic ring as aromatic and the product as a representative primary-structure motif.
- Do **not** imply a unique constitutional repeat or a covalent crosslink network.
- `x` and `y` are statistical sulfur rank, not fixed stoichiometric subscripts.

### B — Composition series

Show S60, S75, and S85 as sulfur-weight-percent samples ordered by increasing sulfur content, using representative DIB-linked polysulfide motifs.

- The number of drawn sulfur glyphs is a qualitative ordinal cue only.
- Do **not** make the motif read as an exact molecular chain-length measurement, sulfur atom count, or composition-derived distribution.
- Preserve the increasing-composition ordering and its clear sulfur-content axis.

### C — Localized trap landscape

Use two equal-status subviews: real-space amorphous polymer host at left and an energy diagram at right.

- In real space, show localized shallow (blue) and deep (red) trap sites within an amorphous host. Texture must read as local polymer structure, **not** lamellae, surface topography, a repeated sine wave, or a separate particle phase.
- In energy space, energy increases upward: `E_C`/mobility edge is above the shallow/deep states and `E_V` below them. Deep states are lower than shallow states.
- Show qualitative shallow/deep DOS populations, their correspondence to the real-space sites, thermal escape toward the mobility edge, and the qualitative trap-depth interval `\Delta E_t`.
- Correspondence marks map populations between the two representations; they are not carrier trajectories. The diagram is schematic, not a calibrated DOS fit.

### D — Transient current

Show a constant-voltage MIM measurement context followed by a qualitative log--log transient-current plot.

- Axes are `\log I` and `\log t`; the condition is `V = V_0`.
- The measured trace is a qualitative power-law decay, `I(t) \sim t^{-n}`, labelled with relaxation-time language rather than trap language.
- Its comparison partner is an idealised single-relaxation (Debye) model reference, drawn with no straight-line regime and named as a model reference, not a measured control. Do not restore the low-`n`/high-`n` two-material contrast, and do not attach fitted numeric exponents, a fit window, measured points, or environment conditions.

### E — ISPD trap distribution

This is a staged measurement-to-derivation story, not a generic Kelvin-probe cartoon.

1. Corona charge the sample with the gridless two-terminal high-voltage setup. Do not add an earth-ground symbol or grid to that charging stage.
2. Manually relocate the same specimen to the non-contact ESVM measurement stage. The transfer is manual; do not depict an automated motion/conveyor system.
3. Ground the conductive backing/substrate only at the measurement stage, and show the ESVM head plus `V_s` meter acquiring `V_s(t)`.
4. Use the `derive` lane to map the surface-potential decay to one continuous qualitative `g(E_t)` distribution with shallower and deeper zones shown by shading only. Draw no `\tau_d` span: a relaxation time has no place on an energy axis. `g(E_t)` and the Panel C energy diagram are the same quantity with the axes swapped and must agree.

### F — Floating-clip bending response

Show a polymer cantilever held by a floating clip and facing a driven electrode across an air gap.

- The cantilever and sample are electrically floating. The clip's own terminal is drawn open; it is not an electrical contact.
- The voltage source drives the electrode and its **source return** is grounded. That ground does not extend to the sample, cantilever, jig, or a second hidden contact.
- The hypothesised trapped charge remains inside the film/cantilever silhouette and carries an explicit hypothesis qualifier.
- The panel asserts the observation only: make the red result arrow point away from the driven electrode and label it as the observed bend, not as a named mechanism. A distinct, subordinate Maxwell-stress baseline can point toward the electrode, but it must not be confused with the result arrow or occupy its label lane.
- The air-gap bracket belongs to the cantilever--electrode separation, and the voltage label belongs to the compact source, not to the ground symbol.
- The source-return topology is preserved but its visual clarity remains a named human-review item. Improve the label/layout only if the distinction between source-return ground and floating sample becomes clearer; never solve it by grounding the cantilever.

## What may and may not change

Free redraw is allowed when it improves scientific legibility, morphology, or print-scale quality. Preserve every panel claim and forbidden reading above. Do not substitute a generic primitive, a literal source block from v5f, or a new scientific claim merely to make the drawing easier.

The current baseline still needs human/master visual judgment. In particular, v5f remains the named visual comparison reference, and passing compile, physics, or collision checks does not establish acceptance.

## Edit and verification routine

Work from the source path above, not from a preserved review child or an old vault. From `plugins/figure-agent`:

```bash
FIGURE_AGENT_STRICT=1 bash scripts/compile.sh \
  examples/fig1_updated_agent_redraw_v1/fig1_updated_agent_redraw_v1.tex
./bin/fig-agent status fig1_updated_agent_redraw_v1 --json
```

After each meaningful edit, inspect the full PNG and A--F crops at 100%, 50%, and 33%; check PDF/vector geometry as well as the raster. Keep the current-candidate pointer and its evidence fresh. If a change needs aesthetic, scientific, or acceptance judgment, stop for the human/master gate rather than recording an inferred accept/reject outcome.

## Source of the handoff

This document consolidates the active candidate pointer, fixture briefing, `spec.yaml`, `semantic_contract.yaml`, `authority.yaml`, and the active paper-figure state. Those machine-readable files remain the enforcement layer; this Markdown is the human/LLM redraw brief and must be updated in the same change whenever the active candidate or a panel contract changes.
