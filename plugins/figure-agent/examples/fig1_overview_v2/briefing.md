# Briefing — fig1_overview_v2

> **Reference**: `reference/codex_gen_overview_v1.png` (Codex image-gen, 2026-05-08)
> **Paper framing**: v9.7+α charge-trap-centered (NOT actuation showcase)
> **Layout**: 2-row × 7-panel narrative overview, NatComm 178 mm wide

## 1. What does this figure show?

논문 전체 논리를 상→하 두 row로 압축.
- **Row 1** (재료 → 구조 → 현상): Sulfur-rich network 구성 → S-chain length 분포 → localized trap 발생
- **Row 2** (실험적 증거 수렴): 다중 de-trapping 방출 시퀀스 + I(t) → Vₛ(t) decay → ISPD g(Eₜ) → macroscopic probe

Row 1의 오른쪽 끝(localized traps)에서 수직 화살표로 Row 2로 연결.
스토리: *"황 풍부 폴리머에는 깊은 전하 트랩이 존재 → 다중 측정이 수렴 → 거시적 bending으로 발현."*

## 2. Domain vocabulary

- Sulfur polymer: S₈ ring (octagonal), −Sₓ− chain, S60–S85 wt% label, amorphous network
- Trap levels: shallow trap (high in gap), deep trap (mid-gap, Eₜ ~ 0.5–1.0 eV), g(Eₜ) DOS
- Discharge / de-trapping: I(t) ~ t⁻ⁿ (power-law, non-Debye), Debye reference e⁻ᵗ/τ
- Vₛ(t): surface potential decay (ISPD measurement decay curve)
- g(Eₜ): trap density of states — bimodal (shallow blue + deep red)
- τ_d: mean trap depth timescale (double arrow in g(Eₜ) panel)
- Probe: polymer cantilever strip, electrode, Coulomb repulsion (red), Maxwell attraction (blue), qₜᵣ = trapped charge

## 3. Layout — 2-row, 7-panel structure

Canvas: 178 mm × ~120 mm (2-row stacked; Row 1 ≈ 45% height, Row 2 ≈ 55%).

### Row 1 (top, 3 panels left→right)

**Panel A — Sulfur-rich network** (leftmost, ~25% width)
- Top: S₈ ring (gold octagonal structure, "S" labels on each vertex, "S₈" center label)
- Bottom: 2D polymer network fragment — gold S atoms + gray carbon/crosslink atoms, gray connector lines, showing amorphous topology
- Panel header: "Sulfur-rich network" (above, centered)
- No axes; schematic only

**Panel B — S₆₀–S₈₅ chain length** (center, ~25% width)
- 4–5 horizontal chains of increasing length (stacked vertically, short→long top→bottom)
- Each chain: alternating gold (S) and gray atoms connected by bonds
- Topmost chain: short (S₆₀-like), bottommost: long (S₈₅-like)
- Axis label below: "S-chain length →" (horizontal axis arrow)
- Header: "S₆₀–S₈₅" (above)
- Inter-panel arrow (right-pointing gray) from Panel A → B

**Panel C — Localized traps** (rightmost, ~50% width, visually dominant in row 1)
- Background: polymer network (same S/C atom motif, lighter/faded)
- Superimposed: sinusoidal energy landscape curve (black, above the network)
- Left region (deep traps, blue): 3–4 blue circle electrons (⊖) sitting in potential wells; blue dashed arrows pointing down INTO wells
- Right region (shallow traps, red): 3–4 red circle electrons (⊖) in shallower wells; red dashed arrows pointing down into wells, some pointing upward (escape)
- Header: "localized traps" (above, centered)
- Inter-panel arrow (right-pointing gray) from Panel B → C
- Vertical downward arrow from bottom of Panel C into Row 2 (transition to de-trapping evidence)

### Row 2 (bottom, 4 panels left→right)

**Panel D — Distributed release** (leftmost, ~30% width)
- Top sub-panel: de-trapping sequence snapshots
  - t₁, t₂ (blue labels): electrons in deep potential wells, blue fill
  - t₃, t₄ (red labels): electrons in shallow wells, red fill; some escaping upward
  - "..." between t₂ and t₃
  - Connected by horizontal arrow showing time progression
- Bottom sub-panel: I(t) log-log plot
  - x-axis: t (s), range 10⁻² to 10⁶
  - y-axis: I(t), range ~10⁰ to 10⁻⁸
  - **Red solid line**: I(t) ~ t⁻ⁿ (power-law), annotation "non-Debye tail"
  - **Gray dashed line**: Debye reference ~ e⁻ᵗ/τ
  - Label: "I(t) ~ t⁻ⁿ" with exponent superscript
- Panel header: "distributed release" (above)

**Panel E — Vₛ(t) decay** (center-left, ~15% width)
- Single log-log plot
- x-axis: t (s), range 10⁻¹ to 10⁶
- y-axis: Vₛ (surface potential)
- Data: filled circles following a decay curve (schematic, no real data values)
- Gray gradient background (fading from light to dark from top-left to bottom-right)
- Header: "Vₛ(t) decay" (above)
- Inter-panel arrow (right-pointing) from D → E

**Panel F — ISPD-derived g(Eₜ)** (center-right, ~20% width)
- Two Gaussian bell curves side by side
  - Left Gaussian: **blue** (shallow traps), smaller amplitude
  - Right Gaussian: **red** (deep traps), taller amplitude
- Open circles on each curve at multiple levels (suggesting discrete trap depths)
- x-axis: Eₜ; x-labels "Shallow" (below blue peak), "Deep" (below red peak)
- y-axis: g(Eₜ)
- **Double-headed red dashed arrow** between the two peaks: labeled "τ_d"
- Header: "ISPD-derived g(Eₜ)" (above)
- Inter-panel arrow (right-pointing) from E → F

**Panel G — Macroscopic probe** (rightmost, ~30% width)
- 3D perspective schematic:
  - Left: gray rectangular electrode block (tall, vertical)
  - Right: bent polymer strip (gold/amber, curved away from electrode)
  - Air gap between electrode and strip, labeled "air gap"
  - Gold spheres on polymer strip face: qₜᵣ labels (trapped charges)
- **Red arrow** (bold, pointing RIGHT, away from electrode): "Coulomb repulsion"
- **Blue arrow** (bold, pointing LEFT, toward electrode): "Maxwell attraction"
- Both arrows visible simultaneously to show competing forces
- Header: "Macroscopic probe" (above)
- Inter-panel arrow (right-pointing) from F → G

## 4. Normalize — what NOT to reproduce literally

- Exact atom count in S₈ ring or chain (± 1–2 atoms fine)
- Exact Eₜ values in g(Eₜ) panel (schematic only, no numbers on axes)
- Exact electrode or strip dimensions
- Number of data-point circles in Vₛ(t) plot (schematic)
- Precise position of each electron in network panels

## 5. Style notes

Based on `polymer-paper` palette and reference visual inspection:
- **Gold/amber** (cAmber ≈ RGB 153,122,30; cAmberSphere ≈ 221,204,119): S atoms, polymer strip, chain atoms
- **cArmAmber** (139,111,62): darker amber for strip body
- **Blue** (cBlue ≈ 68,119,170): shallow trap electrons, Maxwell arrow, blue Gaussian
- **Red** (cRed ≈ 204,102,119): shallow trap escape / deep trap label, Coulomb arrow, red Gaussian, power-law line
- **Gray** (cGray ≈ 70,70,70): network connectors, axes, electrode, Debye dashed line
- **Light gray** (cLGray ≈ 200,200,200): panel backgrounds, separators
- Background: white; no thick panel borders (subtle separator only between rows)
- Typography: 8–9pt labels, 10pt bold panel headers, sans-serif throughout
- Line weight ≥ 0.5pt; arrows ≥ 1pt

## 6. Physics invariants

- Deep traps are LOWER energy (further from LUMO / conduction band) than shallow traps.
  In the potential landscape: deeper wells = blue region.
- Power-law I(t) ~ t⁻ⁿ must lie ABOVE the Debye reference at long times (non-Debye tail).
- g(Eₜ) bimodal: two distinct peaks, not a single distribution.
  Red (deep) peak amplitude ≥ blue (shallow) peak amplitude in the reference.
- Coulomb repulsion arrow direction: AWAY from electrode (not toward it).
- Maxwell attraction arrow direction: TOWARD electrode.
- Both forces coexist; this panel does NOT declare a winner (Fig 5's job).
- qₜᵣ markers are on the polymer strip, not on the electrode.

## 7. Author intent (vision critique grounding)

### Must depict
- Row 1 → Row 2 vertical connector arrow (from Panel C bottom to Row 2)
- Bimodal g(Eₜ): two clearly separate Gaussians with distinct color (blue shallow, red deep)
- I(t) log-log: power-law red line clearly diverges from Debye dashed gray at long t
- Localized trap panel: blue (deep) and red (shallow) regions spatially separated in the network
- Macroscopic probe: both Coulomb (red) and Maxwell (blue) arrows labeled and direction-correct
- Time sequence t₁–t₄ with color coding (t₁,t₂ blue → t₃,t₄ red)

### Must avoid
- Single-peak g(Eₜ) (must be bimodal)
- Power-law line below Debye at long t (physics violation)
- Coulomb arrow pointing toward electrode
- Merging blue/red trap regions in Panel C
- Adding a 4th column in Row 1 or 5th panel in Row 2 (layout is fixed)
- Quantitative data values on any axis (schematic only)

### Semantic assertions (for vision critique)
1. "Row 1 → Row 2 vertical arrow from Panel C present?"
2. "g(Eₜ) shows two distinct peaks, blue left and red right?"
3. "I(t) power-law line lies above Debye reference at t > 10² s?"
4. "Coulomb repulsion arrow points away from electrode?"
5. "t₁/t₂ markers are blue, t₃/t₄ markers are red?"
6. "Macroscopic probe shows both polymer strip (gold) and electrode (gray) with air gap?"
