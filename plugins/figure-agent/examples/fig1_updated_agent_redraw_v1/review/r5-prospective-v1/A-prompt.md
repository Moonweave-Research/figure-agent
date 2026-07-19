You are the sole authoring model in condition A of a prospective comparison.
Do not use tools, inspect files, or ask questions. Work only from the task below.
Use at most 260 source lines and return exactly one JSON object matching the
provided schema. `tex_source` must contain a complete standalone LuaLaTeX/TikZ
document. You get one attempt and no feedback.

# Neutral scientific task — Fig1 six-panel overview

Create one editable TikZ scientific schematic for a sulfur-rich polymer paper.
The figure has six panels arranged as two rows of three:

- A: polymer repeat-unit concept, including the sulfur-rich segment and DIB crosslinker.
- B: qualitative sulfur-composition series; do not imply measured numerical spacing.
- C: the visual hero, showing coexisting shallow and deep localized trap states with energy increasing upward.
- D: qualitative transient current decay under constant applied voltage; no measured ticks or fitted numerical values.
- E: noncontact ISPD surface-potential measurement and a qualitative trap-distribution interpretation.
- F: a mechanical jig holds a floating cantilever above a driven electrode. The voltage source returns to ground, while neither the sample nor cantilever is grounded. Show Coulomb repulsion away from the electrode.

Keep all scientific relationships legible at paper scale. Use no external images,
no measured data, and no claims of quantitative accuracy. Return a complete
standalone `.tex` source and nothing else.
