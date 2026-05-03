# Briefing - n3_trial_01_trap_depth

## 1. What does this figure show? (1-2 sentences)
The figure presents a three-row narrative that converges an experimental discharge power-law observation, a mathematical interpretation linking exponent to a trap-depth distribution g(E_t), and a molecular origin in a sulfur-rich polymer, into a "unified trap-depth picture" rendered as a band diagram (CB / VB) with shallow-trap and deep-trap populations and their corresponding g(E_t) distributions.

## 2. Domain vocabulary (terms, materials, mechanisms)
- Experiment: "Discharge power-law vs. time (log-log)"
- "Power-law", equation `I = I_0 t^(-n)` (slope = -n)
- "Debye reference", equation `I = I_0 e^(-t/τ)`
- log I vs log t axes
- Mathematical interpretation: "From power-law exponent to trap-depth distribution"
- Variables: `n` (power-law exponent), `τ_d` (time, "time emission line"), `g(E_t)` (trap-depth distribution)
- Equation: `τ_d = τ_0 exp(E_t / k_B T)` [uncertain: subscript reading on k_B]
- g(E_t) vs E_t plots (two-peak distribution sketch)
- Molecular origin: "Sulfur-rich polymer: chemical and physical origin of traps"
- "chemical origin: electron-rich sulfur sites (polarizability, lone pairs)"
- "physical origin: conformational/free-volume heterogeneity"
- Right panel header: "Unified trap-depth picture in a sulfur-rich polymer"
- Band-diagram labels: "CB" (top band), "VB" (bottom band), "Energy" (vertical axis)
- "Shallow traps" (near CB), "Deep traps" (near VB)
- E_t axis labels on g(E_t) side panels
- "Convergence to a unified trap-depth picture" (vertical connector text between left column and right panel)

## 3. Composition intent (panel layout, flow direction)
The figure is a two-column composite. The left column is a vertical stack of three numbered rows (circled 1, 2, 3) flowing top-to-bottom: (1) Experiment — a small log-log plot with a blue power-law line and a dashed Debye reference; (2) Mathematical interpretation — a schematic mapping from exponent n through τ_d to a g(E_t) curve, with the governing exponential equation shown; (3) Molecular origin — a sketched polymer backbone with sulfur sites, plus two captioned sub-bullets distinguishing chemical and physical origins. A vertical green-bordered connector labeled "Convergence to a unified trap-depth picture" bridges the left stack to the right panel. The right panel is a single tall band diagram with CB at top and VB at bottom, two horizontal trap-level groups (shallow near CB, deep near VB) drawn as short tick segments, and on its right side two stacked g(E_t) profiles aligned to the shallow and deep regions respectively. Flow is left-to-right and top-to-bottom: evidence -> theory -> molecular cause -> unified picture.

## 4. Normalize / avoid literal overfit
Preserve the three-row numbered narrative, the convergence connector, and the right-side band diagram with two trap populations and matched g(E_t) side curves; simplify the polymer sketch and the small inset plots to schematic level rather than reproducing exact curve shapes, exact tick counts of trap levels, or precise sulfur-site count.

## 5. Style notes (optional)
- Numbered circles in dark teal/navy on the left margin (1, 2, 3)
- Light teal/cyan rounded rectangles framing each left-column row
- Power-law line in solid blue; Debye reference in dashed gray
- Polymer backbone drawn with yellow sulfur atoms and gray/black bonds
- Right panel: CB block in teal, VB block in purple/violet
- Shallow-trap g(E_t) curve in orange/amber; deep-trap g(E_t) curve in purple
- Trap levels rendered as short horizontal segments (orange near CB, purple near VB)
- Green outlined arrow/box for the central "Convergence" connector
- Sans-serif labels throughout; equations in serif/italic math style

## 6. Physics invariants (preserved verbatim in prompt)
- CB is drawn above VB on the energy axis in the right panel.
- Shallow traps sit just below CB; deep traps sit just above VB.
- Two distinct trap populations are shown, each paired with its own g(E_t) distribution on the right margin.
- Left-column row (1) shows a log-log plot with a power-law line `I = I_0 t^(-n)` and a dashed Debye reference `I = I_0 e^(-t/τ)`.
- Row (2) shows the relation `τ_d = τ_0 exp(E_t / k_B T)` connecting trap depth to emission time.
- Row (3) attributes traps to two origins in a sulfur-rich polymer: chemical (electron-rich sulfur, polarizability, lone pairs) and physical (conformational / free-volume heterogeneity).
- A single "Convergence" connector links the three left rows into the right-panel unified picture.
- Vertical axis of the right panel is labeled "Energy"; horizontal axes of the side curves are labeled E_t.
