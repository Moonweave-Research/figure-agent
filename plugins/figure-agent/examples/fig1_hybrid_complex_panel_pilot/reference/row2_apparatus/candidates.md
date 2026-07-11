# Row 2 Apparatus — Reference Candidates

Search executed: 2026-05-16
Target: 3 measurement-apparatus schematics for Fig 1 Row 2 (D/E/F columns)
- D = transient current I(t) ~ t^-n on polymer thin film
- E = ISPD (corona-charge + Kelvin-probe surface-potential decay)
- F = polymer cantilever electrostatic actuator (Coulomb-driven Δθ)

Pool: 11 papers, 18 page-renders.
All sources are open-access (Nature Communications, Scientific Reports, Polymer Journal).

---

## Apparatus 1 — Transient current / dielectric polarization on polymer thin film

Honesty note: apparatus-1 is intrinsically the least "drawn" of the three —
groups publish I(t) traces but rarely depict the source-meter + electrometer +
sandwich-stack hardware as a single schematic the way ISPD or actuator papers
do. The candidates below are the **best adjacent matches** (polymer dielectric
sandwich stacks, P&F process schematics, breakdown-array layouts) rather than
literal "transient current rig" drawings.

| ID | Source (DOI / journal / year) | Fig | Image | Why candidate | Weakness | Mine these elements |
|---|---|---|---|---|---|---|
| ref01 | [10.1038/s41467-019-09874-8](https://doi.org/10.1038/s41467-019-09874-8) — Shen et al, Nat Commun 2019 | Fig 1 | `apparatus1_ref01_NatComm2019_phasefield_p3-03.png` | 3×3 array of E-field-on / breakdown-state polymer slabs (a–i), then 3×3 energy-density maps (j–r). Clean stacked-electrode geometry, monochrome electrode shading, color-encoded internal field. Demonstrates Nat-Comm convention for "polymer-between-two-electrodes under bias" cross-section. | No measurement-circuit instruments drawn (purely simulated). Field arrows only — no source-meter / electrometer / scope. | Top/bottom electrode shading; stacked-stripe polymer film convention; vertical-arrow E-field annotation; small-multiples grid composition for parameter sweeps |
| ref02 | [10.1038/ncomms5845](https://doi.org/10.1038/ncomms5845) — Mannodi-Kanakkithodi et al, Nat Commun 2014 | Fig 1 | `apparatus1_ref02_NatComm2014_polydielec-2.png`, `-3.png` | 5-step workflow flowchart (combinatorial chemistry → repeat unit → 3D structure → property → synthesis). Each step has a glyph (chemical icon, polymer ribbon, lattice, scatter plot). Useful as a structural/style template for "process-flow" panels rather than the apparatus itself. | Not an apparatus schematic — it's a strategy diagram. Color palette is muted pastel (2014 vintage), worth modernizing. | Stage-numbered process flow layout; mixed icon types within one panel; light-gray rounded-rect step containers |
| ref03 | [10.1038/s41467-019-12391-3](https://doi.org/10.1038/s41467-019-12391-3) — Meng et al, Nat Commun 2019 | Fig 1, Fig 2 | `apparatus1_ref03_NatComm2019_pvdfcap-3.png`, `-4.png` | Fig 1a "Pressed-and-Fold" process schematic (clear arrow→arrow→arrow process sequence), Fig 1b cross-section SEM of layered PVDF stack, Fig 1d the actual D–E ferroelectric hysteresis equipment graph. Fig 2 shows parameter-sweep panels with color-coded conditions. | Equipment side is mostly cartoon hands+rectangle (P&F process), not a real I-t rig. The ferroelectric measurement is mentioned but not pictorially detailed. | The clean P&F process arrows (potential template for "charge → hold → measure" sequence); cross-section SEM-as-photo layout |
| ref04 | [10.1038/s41467-022-33766-z](https://doi.org/10.1038/s41467-022-33766-z) — Wang et al, Nat Commun 2022 | Fig 1 | `apparatus1_ref04_NatComm2022_tribo_p3-03.png` | **Strongest apparatus-1 candidate in pool.** Fig 1a: layered triboelectric series cross-section (PI/Nylon/Glass/PET/PTFE/PVC). Fig 1b: ferro-electric & electrostatic-induction circuit equivalent. Fig 1e: side-by-side "with breakdown" / "without breakdown" measurement-condition schematics with Vmax / Imax / Δgap labels — closest in spirit to a measurement-apparatus drawing. | Triboelectric not pure I(t)-bias; physics is contact-electrification not Curie-von Schweidler. Still adjacent — same MIM-style sandwich. | Equivalent-circuit symbols (∝, switch, Vmax); side-by-side condition compare layout; clean polymer-stack cross-section with material labels |

---

## Apparatus 2 — ISPD (corona-charged surface, Kelvin-probe scan, V_s(t) decay)

This is the **best-represented apparatus type** in the pool — direct matches in
Nat Comm 2024 and 2023.

| ID | Source (DOI / journal / year) | Fig | Image | Why candidate | Weakness | Mine these elements |
|---|---|---|---|---|---|---|
| ref01 | [10.1038/s41467-024-49660-9](https://doi.org/10.1038/s41467-024-49660-9) — He et al, Nat Commun 2024 | Fig 1 | `apparatus2_ref01_NatComm2024_surfacecharge_p2-02.png` | **PRIMARY ISPD candidate.** Fig 1a: 3-D isometric scene of TENG sample with surface-potential / surface-charge mapping, two-color labels, question-mark conceptual gap. Fig 1b: photograph of the actual stepper-motor-driven Kelvin-probe scanner (probe + electrostatic meter + oscilloscope + motion control box). Fig 1c: clean 2-D side-view schematic of Kelvin-probe-over-sample geometry. Fig 1d: math/process inset. Fig 1e–f: result heatmaps. The whole Fig 1 is a textbook example of "concept + apparatus + result" in one row. | Mixed photo + diagram is heavier than a pure schematic. Photo aesthetic may not match a TikZ-clean Row 2. | Probe-above-sample geometry (Fig 1c) — direct steal-able convention; stepper-motor / motion-stage labelling; sample-on-grounded-substrate cross-section; teal-and-coral palette |
| ref02 | [10.1038/s41467-025-61566-8](https://doi.org/10.1038/s41467-025-61566-8) — Beltrami et al, Nat Commun 2025 | Fig 1, Fig 2 | `apparatus2_ref02_NatComm2025_3dprint-03.png`, `-04.png` | Fig 1a: tall isometric polymer-substrate-contact cartoon (extruder + heating coil + substrate + polymer layers, all sketched in one composite illustration with effect labels). Fig 2: matrix of electrostatic-potential heatmaps across print-direction × extruder-temperature, with print-direction sub-icons (diagonal / concentric / vertical). | The Kelvin-probe rig itself is NOT drawn — only the result heatmaps appear. Less direct than ref01 for "show the apparatus." | Multi-variable result grid layout (Fig 2 c–e) is great template for V_s decay vs T condition sweep; isometric labelled-component cartoon (Fig 1a) |
| ref03 | [10.1038/s41467-023-42583-x](https://doi.org/10.1038/s41467-023-42583-x) — Checa et al, Nat Commun 2023 | Fig 1 | `apparatus2_ref03_NatComm2023_sparseKPFM_p3-03.png` | Fig 1a: clean SS-KPFM apparatus schematic — cantilever with tip → sample → XY-scanner → FPGA controller box, with Topo and CPD readout lines clearly labelled. Closest pure-line schematic in pool. | KPFM-AFM (nanoscale) not millimeter-scale ISPD; cantilever-tip is the wrong probe geometry. Hard physics-mismatch if mined literally. | The yellow-on-black FPGA/controller box convention; tip-to-sample geometry as a stand-in for any vibrating-electrode probe; sparse/raster scan-pattern icons |
| ref04 | [10.1038/s41428-022-00725-w](https://doi.org/10.1038/s41428-022-00725-w) — Shinohara et al, Polym J 2022 | Fig 1, Fig 3 | `apparatus2_ref04_PolymJ2022_stretchpi-3.png`, `-4.png` | Stretched π-conjugated polymer electret characterization. Fig 1: polymer chemical structures + stretching test photographs. Fig 3a: schematic + photograph of MEG fabrication (electrode top contact, polymer middle, foil substrate). | More about charge-retention demo than ISPD measurement; small panels. Useful only for cross-section/material-stack reference. | Folded-electret stack convention (Fig 3a inset); how to combine schematic + sample photo at small scale |

---

## Apparatus 3 — Polymer cantilever electrostatic actuator (Δθ from Coulomb force)

Mid-strength pool — `ref01` (NED actuator) is a near-direct match, others are
electret/electrostatic-induction adjacencies.

| ID | Source (DOI / journal / year) | Fig | Image | Why candidate | Weakness | Mine these elements |
|---|---|---|---|---|---|---|
| ref01 | [10.1038/ncomms10078](https://doi.org/10.1038/ncomms10078) — Conrad et al, Nat Commun 2016 | Fig 1, Fig 2 | `apparatus3_ref01_NatComm2016_microactuator-2.png`, `-3.png` | **PRIMARY cantilever candidate.** Fig 1: textbook electrostatic cantilever cross-section — base, two electrodes, spacers, air-gap, top deflecting beam, all line-shaded mono. Fig 1c shows half-cell with explicit geometry parameters annotated (gap d, length L, voltage U). Fig 2: data plot for V-shaped vs Λ-shaped curvature comparison. | MEMS scale, not polymer-cantilever-in-Coulomb-field exactly. No external high-voltage source instrument drawn — only the actuator cell itself. | Cross-section line convention (electrode hatching + insulator stipple); explicit parameter labels (d, L, U); deflection arrow & curvature notation |
| ref02 | [10.1038/s41598-017-07747-y](https://doi.org/10.1038/s41598-017-07747-y) — Wang et al, Sci Rep 2017 | Fig 2, Fig 3 | `apparatus3_ref02_SciRep2017_electretmem-3.png`, `-4.png` | Fig 2: 4-state charge-formation cartoon (charge injection → dipole alignment → induction → compensation) on PTFE/THV/PTFE multilayer — clean stack notation with discrete circular charges. Fig 3: vibration-energy-harvester schematic with electret membrane + electrode + air-gap + ground + rectifier + load — shows full circuit context. | Vibration EH not cantilever bending per se; the moving element is a parallel plate not a bent beam. | The discrete +/− charge symbols on stack interfaces (Fig 2); the air-gap-between-electret-and-electrode convention; how to add a power-supply / rectifier sub-block clearly without crowding |
| ref03 | [10.1038/s41467-024-50520-9](https://doi.org/10.1038/s41467-024-50520-9) — Wang et al, Nat Commun 2024 | Fig 1, Fig 2 | `apparatus3_ref01_NatComm2024_dropletelectret-02.png`, `-03.png` | Fig 1a: vertical cross-section of an electret-charged droplet with electrode-on-droplet polarization arrows. Fig 1b: photograph of the EPD platform. Fig 2: "Attraction between electret and droplet" 6-panel mechanism sequence with positioned-electrode + force-vector arrows, plus Maxwell-stress map in Fig 2E. | Droplet not cantilever beam — physics adjacent (Coulomb attraction) but geometry different. Fig 2E Maxwell-stress map is the most directly useful single panel for "force-on-charged-polymer-body". | Fig 2A 6-panel time-step strip (model for showing actuation sequence); Fig 2E Maxwell-stress color field over geometry; +/− attraction-arrow convention between charged body and electrode |

---

## Pre-filter detail

- Excluded `a1_polyetherimide_arxiv2013.pdf` (arXiv 1304.5536) after download: only 2-page conference abstract, no apparatus schematic of publication quality. Replaced budget with stronger Nature Comm picks.
- Excluded paywalled candidates surfaced in search (Adv Mater / Adv Funct Mater / Macromolecules / Nat Mater) — Nat Commun + Sci Rep + Polym J OA pool is sufficient and preserves the v0 "OA-only" constraint.
- Excluded all results pre-2015 (Mannodi-Kanakkithodi 2014 kept as a single exception because the workflow-template panel is design-language-relevant — strengths apply to layout convention, not aesthetic palette).
- Excluded review papers (composite figs are too cluttered to mine).
- No KPFM-AFM-nanoscale candidate kept as primary (cantilever-tip geometry is wrong for ISPD-mm-scale) — included `ref03` only as a controller-box / sparse-scan visual idiom donor.

## Coverage gaps (be honest)

- **Apparatus 1 is the weakest tier.** The OA Nature-family pool does not contain a clean "constant-voltage source → polymer film → electrometer → oscilloscope" schematic. Closest is Wang 2022 Fig 1e (with/without breakdown side-by-side) — adjacent physics, not exact. If a literal I-t apparatus drawing matters more than visual conventions, the user may want to allow paywalled candidates (Adv Mater, Macromolecules) or older OFET / polymer-MIS literature.
- **No corona-needle illustration found at Nat-Comm aesthetic in OA pool.** The corona-charging step (HV needle / wire above sample) is sparsely visualized — He 2024 Fig 1c shows only the Kelvin-probe side. User may need to draw the corona-needle component from scratch (or composite from corona-discharge engineering papers, lower aesthetic tier).
- **No external position-sensor on cantilever apparatus.** The laser-photodiode / camera readout component for Δθ measurement isn't shown in any of the kept candidates. Likely needs composited from a separate optical-readout reference if it's a load-bearing visual.
