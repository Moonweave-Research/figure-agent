# Fig1 Energy Landscape v1 Design Brief

## Figure Target

`fig1_energy_landscape_v1`

## Purpose

Create a focused manuscript-style schematic that explains why sulfur-rich DIB
polymer networks show persistent surface potential and slow current decay.

This pilot intentionally narrows the task compared with
`fig1_overview_v2_pair_001`. It should test whether Reference Intelligence v2
helps the figure-agent choose better grammar for energy landscapes, transient
decay plots, and trap-depth distributions.

## Required Scope

Author the same 4-panel figure for both arms.

Canvas:

- landscape page
- 2 x 2 panel grid
- clear panel labels A-D
- compact journal style
- no hero title
- no explanatory paragraphs inside the figure

Panel layout:

- A: sulfur-rich polymer network with localized trap sites
- B: trap energy landscape
- C: current transient and surface-potential decay
- D: trap-depth distribution comparison

## Panel A: Sulfur Polymer Trap Network

Goal: show the material scene.

Required content:

- sulfur-rich polymer network drawn as wavy gold chains
- sparse aromatic DIB cross-link nodes in gray/dark slate
- 5-7 localized trap sites as small blue or red wells/dots embedded near chains
- one incoming charge arrow entering the network
- one retained charge marker inside the network
- short label: `sulfur-rich network`
- short label: `localized traps`

Do not draw a generic hydrocarbon blob. The network must visually read as
polymer chains plus cross-link nodes.

## Panel B: Trap Energy Landscape

Goal: show shallow and deep trap states as an energy landscape.

Required content:

- horizontal reaction-coordinate axis labeled `position`
- vertical axis labeled `energy`
- smooth energy curve with several wells
- shallow traps in blue and deep traps in red
- at least 3 shallow wells and 2 deep wells
- dashed escape arrow from a shallow trap
- thicker or longer retention arrow at a deep trap
- labels: `shallow`, `deep`, `escape`, `retention`

Design preference:

- the energy landscape should be the visual anchor of the figure
- avoid overcrowded math
- use consistent color mapping with Panel D

## Panel C: Decay Signatures

Goal: connect traps to measurable time-domain signatures.

Required content:

- two small aligned plots or one split plot
- log-time x-axis labeled `time`
- top trace: current decay labeled `I(t) ~ t^{-n}`
- bottom trace or paired trace: surface potential decay labeled `V_s(t)`
- Debye-like fast reference curve in gray
- trap-mediated slow tail in blue/red
- short label: `slow tail`

The curves should be clearly separated from axis labels. Avoid placing the
power-law equation on top of the y-axis label.

## Panel D: Trap-Depth Distribution

Goal: summarize shallow vs deep trap populations.

Required content:

- energy axis labeled `trap depth`
- two distributions:
  - shallow distribution in blue, narrower and lower depth
  - deep distribution in red, broader or shifted deeper
- vertical marker for `E_t`
- arrow from shallow distribution toward faster decay
- arrow from deep distribution toward longer retention
- compact labels: `fast release`, `long retention`

The panel should read as a conceptual distribution, not a precise data plot.

## Style Constraints

- Use restrained paper colors: gold for sulfur network, blue for shallow traps,
  red for deep traps, gray for neutral axes/reference curves.
- Use thin axes and concise labels.
- Keep math labels legible.
- Prefer smooth curves and clean callouts over dense decoration.
- No raw TikZ source copying from references.
- If references are available, use them only as grammar/style anchors.

## Evaluation Rubric

Blind evaluator should compare candidates on:

- scientific_fidelity: network, energy landscape, decay signatures, and trap
  distributions are physically coherent and match this brief
- layout_quality: 2 x 2 grid is balanced and readable
- typography_labeling: math labels and axes are clear and not collided
- visual_polish: curves, arrows, colors, and spacing look publication-ready
- reference_use_without_copying: candidate synthesizes grammar rather than
  reproducing any single reference

## Non-Goals

- No full device stack.
- No Maxwell stress panel.
- No seven-panel overview.
- No quantitative fitting.
- No claim that the figure validates a physical model.
