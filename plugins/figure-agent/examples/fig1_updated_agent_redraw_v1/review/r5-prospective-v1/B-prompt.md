You are the sole authoring model in condition B of a prospective comparison.
Do not use tools, inspect files, or ask questions. Work only from the task and
Figure Agent contract below. Use at most 260 source lines and return exactly one
JSON object matching the provided schema. `tex_source` must contain a complete
standalone LuaLaTeX/TikZ document. You get one attempt and no feedback.

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

# Figure Agent contract

- Use `\documentclass[border=6pt]{standalone}` and `\usepackage{polymer-paper-preamble}`.
- Use semantic TikZ objects and named styles; do not define a competing local palette.
- Prefer the paper palette tokens `cBlue`, `cRed`, `cTeal`, `cAmber`, `cBrown`, and `cGray`.
- Maintain a consistent sans-serif hierarchy, restrained strokes, and generous label clearance.
- Do not place opaque label backdrops over curves, arrows, apparatus internals, or sample boundaries.
- Keep panel titles, labels, arrows, paths, and state marks owned by one unambiguous object.
- C is the visual hero; D–F are compact evidence modules rather than decorated instrument drawings.
- Energy increases upward; deeper trap states are lower. Do not draw a quantitative density fit.
- The transient-current plot is qualitative and monotonic under constant voltage.
- The ISPD probe remains visibly noncontact.
- In F, the jig is only mechanical. The voltage source drives the lower electrode and its other terminal returns to ground. The cantilever/sample remains floating. The force arrow points away from the electrode.
- Use explicit semantic source markers around the Panel C trap landscape and Panel F electrical topology:
  `% fig-agent:start object=... panel=... kind=... truth_bearing=true` and matching end markers.
- Machine checks are support only; do not claim publication acceptance.
