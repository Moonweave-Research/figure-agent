# Reference Audit Table — fig1_overview_v2_pair_001_vault

**Generated**: 2026-05-17
**Purpose**: Per-panel reference curation with 3-axis audit (theoretical / structural / storyline). Each row is one PNG × panel combination. Patch suggestions during element-iteration loop must cite a row from this table and re-validate.

## Audit conventions

- **theoretical**: candidate's physics ↔ briefing §8 LOCKED. PASS = no physics conflict; PARTIAL = adjacent mechanism, geometry transferable but mechanism narrative must come from briefing; FAIL = physics conflict (no content transfer).
- **structural**: candidate's sub-region layout ↔ our panel layout (briefing §13). PASS = directly mappable; PARTIAL = mappable with adaptation; FAIL = layout architecturally different.
- **storyline**: candidate's reading order + intent ↔ briefing §13 reading order. PASS = same narrative flow; PARTIAL = adjacent flow; FAIL = different narrative.
- **usability tag**: full-spectrum / style+structural / structural-only / style-only / discard. Drives in-loop transfer decisions.
- **transferable aspects**: what the iteration loop may mine. **Do-not-transfer** lists what is blocked.

---

## Panel A — Sulfur-rich polymer (molecular identity)

| Candidate | Source | Theoretical | Structural | Storyline | Usability | Transferable | Do-not-transfer |
|---|---|---|---|---|---|---|---|
| `reference/sulfur_polymer_panelA_ref.png` | (anti-reference) | **FAIL** (depicts crosslinked DIB-polysulfide network — briefing §8 / §9 forbid network topology) | FAIL (network ring layout vs our linear chain) | FAIL (network identity narrative vs our linear-copolymer identity) | **anti-reference only** | sulfur color family / DIB hexagon ring glyph / polysulfide bond aesthetic | network topology, multi-ring crosslink, "DIB-linked polysulfide network" caption semantic, gem-dimethyl junction as primary identifier |

**Gap**: no positive Panel A reference. Linear poly(S-r-DIB) primary microstructure is largely a novel-rendering element — Cho 2024 figures show network topology. Design must come from briefing §13.1 + Q1 LOCKED + chemistry convention (regular hexagonal DIB ring + linear polysulfide bridges + S₈ regular octagon inset).

**Recommended next**: figure-research targeted at "skeletal linear copolymer chemistry" / "inverse vulcanization mechanism arrow" published in JACS / Macromolecules / NComm for line-weight + glyph weight reference.

---

## Panel B — Sulfur composition variation

**Gap**: no references gathered. Panel B is a B-1..B-4 scaffold (4 zigzag chains + endpoint sample labels + axis arrow + sample dividers) that could be mined from polymer-composition-sweep figures.

**Recommended next**: figure-research targeted at "polymer composition gradient" / "molecular weight variation scaffold" / "skeletal chain length comparison" in Nature / NComm polymer-chemistry pool.

Design currently from briefing §13.2 + Q1 LOCKED + Cho 2024 typography conventions only.

---

## Panel C — Localized traps (HERO #1)

**Gap**: no panel-level references. Brief authoring contract cites vault grammar anchors (`manual_seed_natcommun2024_fig1` energy_diagram motif, `manual_seed_cho2024_fig7_corona_charge` annotation) but these are vault-metadata-only, no actual PNG. Panel C is the figure HERO + 1.5× width + 5s dwell — **highest-value reference gap**.

**Recommended next**: figure-research targeted at:
- Energy-diagram with Gaussian DOS overlay (Mott-CFO / Bässler disorder representations in amorphous semiconductors)
- Hybrid split-half panels (real-space + energy-space)
- Trap-level annotation with shallow/deep distinction
in Nature Materials / Nature Communications / PRL pool.

Design currently from briefing §13.3 + Q7/Q8/Q9 LOCKED + R14/R15/R20 implementation notes. C-L1 polymer sheet is explicitly TikZ-limited (§12.1 SVG handoff deferred — Inkscape redraw planned).

---

## Column D — Kinetic evidence

Existing pool: 6 PNGs in `reference/row2_apparatus/apparatus1_*` (mid-strength — apparatus-1 is the least-published apparatus type per candidates.md honesty note).

| Candidate | Source | Theoretical | Structural | Storyline | Usability | Transferable | Do-not-transfer |
|---|---|---|---|---|---|---|---|
| `apparatus1_ref01_NatComm2019_phasefield_p3-03.png` | Shen NatComm 2019 | **PARTIAL** (simulated breakdown, polymer + electrode field — physics adjacent to MIM bias) | **PASS** (clean MIM-style sandwich + bias arrow convention) | PARTIAL (small-multiples grid not log-log) | **style + structural** | top/bottom electrode shading; stacked-stripe polymer; vertical-arrow E-field annotation | breakdown mechanism, simulated-field color encoding, small-multiples grid composition |
| `apparatus1_ref02_NatComm2014_polydielec-2.png`, `-3.png` | Mannodi-Kanakkithodi NatComm 2014 | **FAIL** (combinatorial workflow, not measurement) | FAIL (process-flow flowchart) | FAIL (strategy diagram) | **discard** | (palette is dated pastel; not recommended) | — |
| `apparatus1_ref03_NatComm2019_pvdfcap-3.png`, `-4.png` | Meng NatComm 2019 | PARTIAL (ferroelectric not non-Debye dielectric) | PARTIAL (P&F process not MIM stack) | FAIL (process flow not measurement) | **structural-only** | cross-section SEM-as-photo layout; P&F process arrow convention | ferroelectric content, P&F mechanism semantic |
| `apparatus1_ref04_NatComm2022_tribo_p3-03.png` | Wang NatComm 2022 | PARTIAL (triboelectric not Curie-von Schweidler; same MIM sandwich family) | **PASS** (layered cross-section + side-by-side condition compare, mirrors our apparatus+result split) | PARTIAL (contact-electrification narrative not transient I-t) | **PRIMARY for D** (style + structural; HANDOFF-adopted) | equivalent-circuit symbols (∝, switch, Vmax); side-by-side condition compare layout; clean polymer-stack cross-section with material labels | triboelectric mechanism, contact-electrification physics, breakdown vs no-breakdown narrative |

**Adopted (per HANDOFF v8.7)**: ref04 as kinetic apparatus anchor (Wang 2022) — equivalent-circuit framing partial-mined as generic SMU+MIM synthesis.

---

## Column E — ISPD-paired evidence

Existing pool: 6 PNGs in `reference/row2_apparatus/apparatus2_*` (best-represented apparatus type — direct Nat Comm matches).

| Candidate | Source | Theoretical | Structural | Storyline | Usability | Transferable | Do-not-transfer |
|---|---|---|---|---|---|---|---|
| `apparatus2_ref01_NatComm2024_surfacecharge_p2-02.png` | He NatComm 2024 | **PASS** (KPFM/Kelvin-probe geometry matches our ISPD exactly) | **PASS** (concept + apparatus + result in one row, mirrors our apparatus+result split) | **PASS** (characterize material then derive) | **PRIMARY for E, full-spectrum** (HANDOFF-adopted) | probe-above-sample geometry (Fig 1c direct steal); stepper-motor / motion-stage labeling; sample-on-grounded-substrate cross-section; teal-and-coral palette; concept-apparatus-result row layout | photo-aesthetic mixing (Fig 1b photograph), TENG-specific labels |
| `apparatus2_ref02_NatComm2025_3dprint-03.png`, `-04.png` | Beltrami NatComm 2025 | FAIL (3D printing scope, not ISPD) | PARTIAL (multi-variable result grid layout) | FAIL (print-direction sweep, not trap distribution) | **structural-only** | multi-variable result grid (Fig 2 c–e) template for V_s decay vs T condition sweep; isometric labelled-component cartoon | 3D-printing content, extruder geometry, print-direction icons |
| `apparatus2_ref03_NatComm2023_sparseKPFM_p3-03.png` | Checa NatComm 2023 | FAIL (AFM-KPFM nanoscale, wrong probe geometry — cantilever tip not Kelvin) | **PASS** (clean SS-KPFM apparatus schematic — tip→sample→XY-scanner→FPGA box) | PARTIAL (scan pattern not decay measurement) | **style-only** | yellow-on-black FPGA/controller box convention; sparse/raster scan-pattern icons | cantilever-tip-as-probe (geometry mismatch), nanoscale labels |
| `apparatus2_ref04_PolymJ2022_stretchpi-3.png`, `-4.png` | Shinohara PolymJ 2022 | PARTIAL (electret characterization, different material) | PARTIAL (schematic + photo combination at small scale) | PARTIAL (charge-retention demo not ISPD) | **structural-only** | folded-electret stack convention (Fig 3a inset); schematic+photo at small scale | stretched-π material identity, MEG fabrication semantic |

**Adopted (per HANDOFF v8.7)**: ref01 as ISPD apparatus anchor (He 2024 Fig 1c) — direct match for probe/sample/meter layout.

---

## Column F — Mechanical evidence

Existing pool: 6 PNGs in `reference/row2_apparatus/apparatus3_*` (mid-strength — ref01 near-direct, others electret adjacencies).

| Candidate | Source | Theoretical | Structural | Storyline | Usability | Transferable | Do-not-transfer |
|---|---|---|---|---|---|---|---|
| `apparatus3_ref01_NatComm2016_microactuator-2.png`, `-3.png` | Conrad NatComm 2016 | PARTIAL (MEMS electrostatic actuator, close mechanism — Coulomb force on dielectric) | **PASS** (textbook cross-section — base + 2 electrodes + spacers + air-gap + top deflecting beam, line-shaded mono; Fig 1c half-cell with explicit d/L/U geometry) | PARTIAL (V-shaped vs Λ-shaped curvature comparison; adjacent to our before/after) | **PRIMARY for F, structural anchor** (HANDOFF-adopted) | cross-section line convention (electrode hatching 45°+135° + insulator stipple); explicit parameter labels (d, L, U); deflection arrow + curvature notation | MEMS scale labels, no-external-source convention (HV source not drawn) |
| `apparatus3_ref02_SciRep2017_electretmem-3.png`, `-4.png` | Wang SciRep 2017 | PARTIAL (vibration EH, parallel-plate moving element, not cantilever bending) | **PASS** (4-state charge-formation cartoon, discrete +/− symbols on stack interfaces; full-circuit context with electret + electrode + air-gap + ground + rectifier + load) | PARTIAL (multi-state injection→alignment→induction→compensation sequence) | **style + structural** | discrete +/− charge symbols on stack interfaces; air-gap-between-electret-and-electrode convention; power-supply / rectifier sub-block layout | vibration-EH narrative, parallel-plate moving element, energy-harvester scope |
| `apparatus3_ref03_NatComm2024_dropletelectret-02.png`, `-03.png` | Wang NatComm 2024 | PARTIAL (droplet not cantilever, but Coulomb attraction adjacent + Maxwell-stress map directly relevant) | **PASS** (Fig 2 6-panel mechanism sequence — apparatus + result-step strip; Fig 2E Maxwell-stress color field over geometry) | **PASS** (attraction sequence between charged body and electrode mirrors our Coulomb narrative; Maxwell-vs-Coulomb tension is exactly the physics question Column F asks) | **SECONDARY for F, full-spectrum** | Fig 2A 6-panel time-step strip (template for apparatus→result sequence); Fig 2E Maxwell-stress color field over geometry; +/− attraction-arrow convention between charged body and electrode | droplet-specific geometry, EPD platform photo (Fig 1b) |

**Adopted (per HANDOFF v8.7)**: ref01 as Column F primary structural reference (Conrad 2016 Fig 1b cross-section idiom). ref03 not yet mined — recommended for v8.8+ Maxwell-stress visualization upgrade if F's color tier needs reinforcement.

---

## Figure-level

| Candidate | Source | Theoretical | Structural | Storyline | Usability | Transferable | Do-not-transfer |
|---|---|---|---|---|---|---|---|
| `reference/codex_gen_overview_v1.png` | codex-generated reference | (N/A — figure-level style anchor only) | (N/A) | (N/A) | **style + layout + label_hierarchy** | palette restraint; 2-row proportion; text scale; cover-scene density | hard plot-grid equality; content authority; Panel G Maxwell semantics (pre-v8.6 anti); quantitative data-plot implication |

---

## Gap summary + next steps

| Panel | Positive refs | Status |
|---|---|---|
| A | 0 (only anti-ref) | **GAP** — figure-research recommended for linear chemistry skeletal grammar |
| B | 0 | **GAP** — figure-research recommended for polymer composition gradient scaffolds |
| C | 0 | **GAP — highest priority** (HERO panel) — figure-research recommended for energy-diagram + Gaussian DOS overlay grammar |
| D | 4 (1 primary + 3 partial) | ADEQUATE |
| E | 4 (1 primary + 3 partial) | ADEQUATE |
| F | 3 (1 primary + 1 secondary + 1 partial) | ADEQUATE |

**Loop readiness**: Row 2 (D/E/F) ready to enter element-iteration loop with reference-grounded patches. Row 1 (A/B/C) iteration must initially run *reference-free* (briefing-only) until figure-research gap is closed — accept higher drift risk per `feedback_perception_spec_rejected` memory until then.

**Recommendation**: Pilot loop on Panel A first (smallest sub-region count = 8, novel rendering acceptable without positive ref). Use Panel A pilot to validate the 10-iter / 4-axis termination structure. Then trigger figure-research for B/C in parallel with Row 2 iteration.
