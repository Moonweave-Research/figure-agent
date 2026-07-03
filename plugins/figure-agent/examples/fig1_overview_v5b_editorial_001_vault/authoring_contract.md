# Authoring Contract: fig1_overview_v5b_editorial_001_vault

## Figure Claim

The figure must read as a cover-style scientific overview: sulfur-rich
poly(S-r-DIB) contains deep and shallow charge traps, three independent probes
point to the same trap model, and trapped charge manifests as macroscopic
Coulomb repulsion. The figure is a schematic argument, not a quantitative data
plot grid.

## Panel Claims

- A: poly(S-r-DIB) is shown as a linear random copolymer primary
  microstructure; bivalent DIB must not read as a 2D covalent network.
- B: S60-S85 chain length variation is shown as delicate schematic chain
  heterogeneity, not a measured sweep plot.
- C: deep and shallow traps coexist in the same polymer matrix, with the right
  energy diagram showing shallow blue and deep red trap levels.
- D: kinetic release is a non-Debye power-law tail; the power-law traces must
  stay above the Debye reference at long times.
- E: surface-potential decay is the raw ISPD signal on a linear time axis.
- F: ISPD inversion yields a bimodal trap distribution with shallow blue and
  deep red peaks.
- G: macroscopic bending is attributed to Coulomb repulsion from trapped
  charge, with the top clip and hanging polymer orientation preserved.

## Theory Invariants

- BLOCKER: Panel A topology is linear poly(S-r-DIB), not a multi-ring
  network. DIB attachment count must remain bivalent.
- BLOCKER: Panel C shallow/deep sites coexist in one polymer matrix; the
  drawing must not imply spatially segregated materials.
- BLOCKER: Shallow traps are blue and deep traps are red across Panels C, F,
  and G.
- BLOCKER: Panel D power-law traces sit above the Debye reference at long
  times.
- BLOCKER: Panel G has only a Coulomb repulsion arrow. Maxwell attraction and
  actuator framing are forbidden.
- BLOCKER: Row 2 is three independent evidence lines from Panel C: kinetic,
  ISPD, and mechanical. It must not read as a D->E->F->G causation chain.
- MAJOR: Panel C remains the primary visual hero; Row 2 evidence panels stay
  balanced rather than creating a second plot-grid hierarchy.
- MAJOR: Composition labels S60/S70/S75/S85 appear only in Panel B.
- MAJOR: Row 2 D/E/F panels stay iconic and tickless, with axis arrows rather
  than full data-plot frames.

## Forbidden Transfers

- Do not transfer the old Panel A network topology from
  `reference/sulfur_polymer_panelA_ref.png`; it is an anti-reference for
  topology after the author decision in `critique.md`.
- Do not transfer Maxwell-attraction semantics, actuator language, or
  bidirectional-device framing from any mechanical reference.
- Do not transfer quantitative plot styling, tick labels, measured values, or
  composition-specific row-2 labels from downstream data figures.
- Do not transfer hard panel borders or equally weighted plot-grid layout from
  the figure-level reference; the target is a continuous cover scene.
- Do not treat vault grammar anchors as content authority when they conflict
  with `design.md` or `briefing.md`.

## Visual Hierarchy

- Primary read path: A -> B -> C, then C branches to D, E/F, and G.
- Hero element: Panel C trap landscape, especially the shallow/deep trap
  energy diagram and mixed trap sites.
- Secondary hero: Panel F deep red trap peak, only as part of the ISPD evidence
  line.
- De-emphasized elements: Row 2 plot axes, Panel B chain enumeration, panel
  letters, and background wash elements.

## Source Limitations

- `coordinate_hints.yaml` is absent, so this authoring pass cannot rely on OCR,
  palette clusters, or structural-region extraction evidence.
- Panels B-G do not declare per-panel `reference_image` fields in `spec.yaml`;
  the figure-level reference is style/layout evidence only.
- `reference/sulfur_polymer_panelA_ref.png` conflicts with the resolved Panel A
  topology and must be used only as an anti-reference for network transfer.
- Existing dirty edits in `briefing.md` and
  `fig1_overview_v5b_editorial_001_vault.tex` are treated as prior authoring work and
  are not overwritten by this contract.

## Acceptance Rubric

- BLOCKER: Reject if any Theory Invariant marked BLOCKER is contradicted by
  the rendered figure, source, critique, or audit.
- BLOCKER: Reject if export proceeds from stale/missing critique evidence
  without an explicit draft override.
- MAJOR: Revise if the figure compiles but reads as a plot grid, loses the
  Panel C hero hierarchy, or fails to trace Row 2 as three independent evidence
  spokes.
- MAJOR: Revise if a patch cannot be traced to the contract, reference pack,
  authoring plan, theory guard, critique, or quality audit.
- MINOR: Polish if only label placement, line weight, or local color balance is
  imperfect and no scientific or publication-compliance condition is affected.
