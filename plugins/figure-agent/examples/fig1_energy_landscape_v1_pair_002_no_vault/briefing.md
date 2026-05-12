# Briefing — fig1_energy_landscape_v1_pair_002_no_vault

> **Pilot pair**: `fig1_energy_landscape_v1_pair_002` / **Arm**: no_vault
> **Design snapshot SHA**: `9b4e36033336826a566dfb7dfb95e6ac4c51851aee423e6696fdd60b0dd89f07`
> **Authoring constraint**: design.md only; no tikz-vault references consulted.

## 1. Target and authoring constraint

This arm targets the focused 4-panel `fig1_energy_landscape_v1` schematic
specified in design.md §"Required Scope". Authoring is from design.md alone —
no tikz-vault query, no record metadata, no grammar/style anchors from a
reference pool. The arm therefore measures what a one-pass author produces
from the design brief without vault grounding.

## 2. Layout

Canvas 14 cm × 9 cm landscape → `\resizebox{178mm}{!}` to NatComm 178 mm.
2 × 2 panel grid, clear A/B/C/D labels, no hero title.

- Panel A — bbox x=0..6.85, y=4.55..9.00
- Panel B — bbox x=7.05..13.95, y=4.55..9.00
- Panel C — bbox x=0..6.85, y=0.10..4.45
- Panel D — bbox x=7.05..13.95, y=0.10..4.45

## 3. Panel A — Sulfur polymer trap network (design §"Panel A")

- Two gold wavy polymer chains (manual bezier, NOT snake decoration).
- Two sparse DIB cross-link nodes drawn as small gray aromatic hexagons.
- 5–7 localized trap sites: small blue wells (shallow) and red wells (deep)
  embedded near the chains. Per design rubric, blue = shallow, red = deep.
- One incoming charge arrow entering the network (top-left).
- One retained charge marker inside a deep trap.
- Inline labels: "sulfur-rich network" (upper-left), "localized traps"
  (lower-right).

## 4. Panel B — Trap energy landscape (design §"Panel B", visual anchor)

- Horizontal position axis labeled `position`.
- Vertical energy axis labeled `energy`.
- Smooth energy curve with multiple wells:
  - 3 shallow wells (blue, amplitude ~0.45)
  - 2 deep wells (red, amplitude ~0.95)
- Dashed escape arrow from one shallow trap (upward exit).
- Thicker / longer retention arrow at one deep trap (pointing down + in).
- Labels: `shallow`, `deep`, `escape`, `retention`.

## 5. Panel C — Decay signatures (design §"Panel C", symbolic axes)

Split plot: top trace = current decay `I(t) ~ t^{-n}`; bottom trace = surface
potential decay `V_s(t)`. Both share a log-time x-axis labeled `time`.

- Top trace: blue power-law line above a faded gray Debye-like reference.
- Bottom trace: red surface-potential decay above a faded gray Debye-like
  reference; trap-mediated slow tail emphasized.
- Inline labels: `slow tail` near the divergence at long time;
  `I(t) ~ t^{-n}` and `V_s(t)` as axis-side titles, kept off the y-axis label.

Axes are schematic: no tick values, no measured numerics — only conceptual
labels per figure-agent symbolic-axis policy.

## 6. Panel D — Trap-depth distribution (design §"Panel D", conceptual)

- Horizontal energy axis labeled `trap depth`.
- Shallow distribution (blue, narrower, peak near smaller depth).
- Deep distribution (red, broader or shifted to greater depth).
- Vertical dashed marker labeled `E_t` between the two peaks.
- Arrow from shallow peak with label `fast release`.
- Arrow from deep peak with label `long retention`.

The two distributions are drawn as filled Gaussian-like bezier lobes;
no precise data — conceptual schematic only.

## 7. Style invariants (design §"Style Constraints")

- Gold (cAmber) for sulfur network, blue (cBlue) for shallow traps, red
  (cRed) for deep traps, gray (cGray) for axes and reference curves.
- Thin axes (line width ≤ 0.55pt) and concise labels.
- No raw TikZ source copied from references — all geometry is author-original.
- Math labels in plain `$...$`; no hero title; no caption text inside figure.

## 8. Author intent recap

The no_vault arm is the design-only baseline of pair_002. Authoring follows
design.md verbatim. Design correctness is held constant; what the pair
measures is the effect of adding vault-grounded grammar/style anchors in the
paired vault arm. Any difference between this arm and the vault arm comes
from grounding awareness, not from a different specification.
