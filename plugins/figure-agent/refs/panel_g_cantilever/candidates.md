# Reference Candidates: cantilever / electret-driven polymer bending schematics (Panel G)

Search executed: 2026-05-15
Pre-filter: ~10 papers excluded (paywall behind WebFetch redirect, off-topic AFM tip geometry, ionic-EAP "bend toward anode" works — different visual idiom)
Final candidates: 7 papers, 11 page renders

User's panel G geometry: clip at top, hanging polymer strip, electrode on right, Coulomb repulsion arrow leftward, q_tr trapped charges, air gap.

Note: candidate ranking weighted toward *visual idiom* (cantilever side-view + gap + electrode), NOT physics-mechanism match. TENG / electret-cantilever / dielectric-elastomer figures dominate because their schematics match Panel G geometry; ionic-EAP works (water-driven polymer strips bending toward anode) excluded because their idiom (no air gap, internal ion-flow arrows inside the strip) does not transfer.

Time-range note: user asked 2020-2026. ref04 (arXiv 2017) and ref05 (arXiv 2011) violate this. Kept anyway because they remain the cleanest **geometric-primitives** references in the literature — the textbook "clamp + beam + gap + electret + electrode" side-view that newer Nat-family papers inherit from. Drop them if you only want recent-style references; the remaining 5 papers (ref01 2024, ref02 2024, ref03 2022, ref06 2020, ref07 2022) still hit the 4-6 target on their own.

Journal-coverage note: user named Adv Mater / Nat Commun / ACS Nano / Adv Funct Mater / Nature Materials. Only ref01 and ref07 hit that list. The others are Nature-family-adjacent (npj Flex Electron, Polymer J, Sci Rep). Cause: OA-only + bending-cantilever side-view + recent date is a rare intersection in flagship journals (ACS/Wiley returned 403 without institutional auth); the TENG/electret literature carries the geometry but lives in a wider journal range.

| ID | Source | Page | Image | Why candidate | Potential weakness |
|---|---|---|---|---|---|
| ref01 | [Nat Commun 2024 - Surface charge visualization for triboelectric materials](https://doi.org/10.1038/s41467-024-49660-9) | 2 | pages/ref01_natcomm_49660_p2-02.png | Fig 1b/c: vertical probe + horizontal sample with electrostatic meter; Fig 1c shows clean **probe-electrode + air-gap idiom** very close to user's vertical-electrode geometry. Fig 1b shows oscilloscope + motion-control arrows (dynamism convention by external arrow, not motion blur). | Probe is not bending; only a static separation idiom. No bend-angle data point. Cluttered multi-panel layout. |
| ref02 | [npj Flex Electron 2024 - Strain-dependent charge trapping in IDTBT polymer FETs](https://doi.org/10.1038/s41528-024-00359-3) | 2 | pages/ref02_npjflex_00359_p2-02.png | Fig 1b: **orange IDTBT polymer strip** drawn as flat rectangle on PDMS substrate, with stretching arrows. Excellent example of **uniform-fill strip iconography** (no gradient, no 3D shading). Tip-finish = clean square cut. Mount = absent (free strip) but transferred to a thick PDMS layer (block-cross-hatch idiom shown). Fig 1c-d: optical micrographs of crack initiation under strain — useful as "trapped-charge concentration" visual reference. | No cantilever bending — strip is stretched, not bent. Bend-angle Δx/L = 0. Useful only for strip-fill + substrate clamp idiom. |
| ref03 | [Polym J 2022 - Stretchable π-conjugated polymer electrets for MEGs](https://doi.org/10.1038/s41428-022-00725-w) | 3 | pages/ref03_polyj_00725_p3-3.png | Fig 1b: poled electret film stretched between fixed clamps — **double-clamp bar idiom** with hatched mount blocks at both ends, polymer rendered as thin grey/orange strip. Direct visual vocabulary for "clamped polymer with charge inside". | No bending depicted; stretch-only. |
| ref03 | same | 4 | pages/ref03_polyj_00725_p4-4.png | Fig 3a: **fabricated MEG schematic exploded-view** — electret layer + electrode + insulating layers stacked with labels and dimensioning arrows. Fig 3b: **photographs of actual device folding** — best real-world ground truth for what a deformed polymer-electret-electrode stack actually looks like. | Photo not schematic — has to be visually paraphrased into TikZ vocabulary. |
| ref04 | [arXiv 2017 - Dynamics of capacitive electret-based microcantilever (Mehdi)](https://arxiv.org/abs/1701.08843) | 2 | pages/ref04_arxiv_1701_08843_p2-02.png | Fig 1: **textbook 2D side-view cantilever schematic** — clamp/wall (cross-hatched block) on left, horizontal beam, air gap, electret slab on bottom, electrode beneath. Exact geometric primitives Panel G needs. Beam drawn straight (no bend); tip = square cut. Mount = vertical hatched wall. | Drawn statically (zero bend) — no bend-angle data point. 2D only, no 3D shading. Old typography (Times Roman). Pre-2020 time-range violator. |
| ref04 | same | 3 | pages/ref04_arxiv_1701_08843_p3-03.png | Fig 4: **3D isometric of "future prototype"** — same cantilever now in 3D with shading, on a sample stage. Useful for "more 3D feel" version of the side-view. | Mechanical-engineering CAD aesthetic, not Nature-grade. Pre-2020 time-range violator. |
| ref05 | [arXiv 2011 - Electret-based cantilever energy harvester (Boisseau)](https://arxiv.org/abs/1111.2458) | 1 | pages/ref05_arxiv_1111_2458_p1-1.png | **Fig 1: minimal labelled cantilever model** — clamp on far left, straight horizontal beam labelled "beam/counter-electrode", small green block at tip (proof mass), electret layer + electrode on bottom; y(t) and x(t) motion arrows pointing **vertically** in the gap. Cleanest single-panel reference for the geometry + motion-arrow idiom. | Beam drawn perfectly straight; no curvature exaggeration. Tip = square + tip-mass cuboid, not a free tip. Pre-2020 time-range violator. |
| ref05 | same | 2 | pages/ref05_arxiv_1111_2458_p2-2.png | Fig 3 inset: **electrostatic equivalent circuit overlaid on the cantilever side-view** — useful idiom for combining "physical schematic + charge-flow arrows". | Mostly equations on this page. Pre-2020 time-range violator. |
| ref06 | [Sci Rep 2020 - Soft dielectric composite cantilever harvester (Marsic et al.)](https://doi.org/10.1038/s41598-020-77581-2) | 6 | pages/ref06_scirep_77581_p6-06.png | **HIGHEST VALUE.** Fig 4(B): 3D isometric of triboelectric cantilever in **bent state** — top electrode rendered as a copper tape, soft dielectric (PET) as a dark layer, bottom electrode + seismic mass at tip, drawn with **clear curvature exaggeration ~20-25% Δy/L** (real value would be a few %). Tip = rounded end with a chunky mass block. Mount = grey shaker block with bolts on the left. Fig 5(B): **actual photograph of cantilever in up/down positions** — ground truth for how a real polymer cantilever looks bent. Fig 5(D): companion side-view schematic with curvature + electrode labels Cp1/Cp2/Cs. Demonstrates **3-overlay idiom**: relaxed + up + down states in a single panel. | Only one bent geometry (no motion-trail/multiple-overlay convention). Color palette is utilitarian Sci-Rep, not flagship Adv-Mater polish. Resolution loss from 150 dpi may obscure label details. |
| ref07 | [Nat Commun 2022 - Triboelectric polymer films via rheological forging](https://doi.org/10.1038/s41467-022-31822-2) | 2 | pages/ref07_natcomm_31822_p2-02.png | Fig 1a: **3D illustrative montage** of rheological forging — flat polymer film, roller, charge density arrows. Color palette and 3D shading style is closer to flagship-journal polish (Adv Mater / Nat Mater aesthetic). Useful as a **palette/shading reference**, not a cantilever reference. | No cantilever or bending at all. Use for palette only. |
| ref07 | same | 3 | pages/ref07_natcomm_31822_p3-03.png | Fig 2b: contact/separate cycle diagram + 3D capacitor stack — generic TENG vertical-contact idiom. Air-gap convention reference. | Stack geometry, not cantilever. |

## Per-dimension idiom summary (extracted across the 11 page renders)

### 1. Tip-finish idioms
- **Square cut**: ref02 (stretched strip), ref04 (textbook cantilever), ref05 (Fig 1 beam) — dominant convention for energy-harvester schematics.
- **Square + tip-mass cuboid**: ref05 (small green block at end labelled `m`). Conveys "free oscillating end" without rounding.
- **Square + rounded end / chunky mass**: ref06 Fig 4 — tip terminates in a 3D-shaded mass block.
- **No "tapered" or "pointed" tip observed** in any of the 11 renders. Pointed tips appear only in AFM-probe geometry (excluded as off-topic).

### 2. Bend-angle exaggeration ratios
- ref04, ref05: **0% bend** (perfectly straight beam, motion conveyed only by external arrows in the air gap).
- ref06 Fig 4(B): **~20-25% Δy/L** visually estimated from the rendered isometric view. ref06 Fig 5(B) photograph confirms this exaggeration is achievable in a real bent polymer film, so the schematic is not unrealistic.
- ref03 Fig 3b photograph: shows the polymer-electret stack folded to ~30-40°, demonstrating extreme bend is photographable but rarely drawn schematically at that magnitude.
- **No multi-state overlay (relaxed + bent semi-transparent) observed.** ref06 Fig 5 shows up/down via two **separate panels**, not transparent overlay in one panel.

### 3. Motion / dynamism conventions
- **External straight arrows in the air gap** (ref04 Fig 1, ref05 Fig 1: `y(t) = Y sin(ωt)`) — most common and lowest-cost way to indicate "this oscillates".
- **Curved arc arrows** indicating bend direction: **not observed** in any of the 11 renders. This appears to be a less common convention in electret/TENG figures.
- **Separate "before/after" or "up/down" twin panels**: ref06 Fig 5(B/C) photographs. Twin schematics: ref01 Fig 1e/f (showing charge spot before vs after but for a different physics).
- **Motion-control arrows on the probe holder**: ref01 Fig 1c (vertical down-arrows on the probe stage).
- **Velocity vectors `v` with label**: not observed.

### 4. Texture / 3D feel
- **Flat uniform fill (2D side view)**: ref02 (orange strip), ref04 (cantilever), ref05 (beam) — most common in pedagogy-style schematics.
- **3D isometric with gradient shading**: ref01 Fig 1b (probe in 3D), ref06 Fig 4(B) (cantilever in 3D), ref07 Fig 1a (3D forging device). All use **muted earth-tone palette** (greys, light blues, soft oranges) — none use saturated rainbow palettes.
- **Photograph (real device) embedded next to schematic**: ref03 Fig 3b, ref06 Fig 5. Convention for "this is real, not just a cartoon."
- **Hand-drawn / sketch aesthetic**: not observed. All schematics are vector-rendered.

### 5. Clip / mount geometry
- **Cross-hatched vertical block** (most classic): ref04 Fig 1 (left wall hatched at ~45° lines), ref03 Fig 1b (clamp bars at both ends).
- **Solid grey block labelled "shaker" or "frame"**: ref06 Fig 4(B) (grey block with bolt circles on left), ref05 Fig 1 (clamp implied by sharp vertical edge of beam).
- **Stippled / dotted block**: not observed.
- **Explicit pin/screw symbols** (small circle indicating bolt): ref06 Fig 4(B) — uses **two circles** for shaker mount bolts.
- **PDMS substrate as thick light block**: ref02 Fig 1b — the polymer strip sits on a stripey block representing the elastomer substrate; this is the "soft mount" convention as opposed to "hard clamp".

## Pre-filter detail
- Excluded `s41928-024-01195-z` (Nat Electron 2024 polymer-semiconductor-ceramic cantilever) — paywalled behind Nature redirect, WebFetch could not pre-screen content.
- Excluded ionic-EAP / electroactive-polymer water-driven bending review papers (PMC8399042 et al.) — bend-toward-anode idiom uses internal-ion-flow arrows, no air gap, different visual neighborhood.
- Excluded AFM-probe / Kelvin-probe microscopy papers (Comm Phys 2019 s42005-019-0108-x, ORNL refs) — tip geometry is pointed and microscopic, not macroscopic cantilever.
- Excluded dielectric-elastomer roll/spring-roll actuators (SAGE Soft Robotics 2019 128° bend) — extreme bend angle but tubular geometry, not flat cantilever; visual idiom doesn't transfer.
- Excluded ACS / Wiley publisher PDFs that returned 403 without institutional auth (acsaelm.5c00482 hybrid-mode cantilever-beam TENG, acsami.1c23309 trapezoidal cantilever TENG).
- Excluded older (<2015) papers except for the two arXiv electret-cantilever classics (ref04, ref05) — kept despite age because they are the foundational schematic vocabulary that newer Nat-family papers inherit from. Drop them if you only want recent-style references.

## Files inventory
- candidates.md (this file)
- pages/ref01_natcomm_49660_p2-02.png — probe + sample + electrostatic meter schematic
- pages/ref02_npjflex_00359_p2-02.png — IDTBT polymer strip schematic + crack micrographs
- pages/ref03_polyj_00725_p3-3.png — Fig 1: clamped electret film, double-clamp idiom
- pages/ref03_polyj_00725_p4-4.png — Fig 3: fabricated MEG schematic + folding photo
- pages/ref04_arxiv_1701_08843_p2-02.png — Fig 1: textbook 2D cantilever side-view (HIGHLY RECOMMENDED for primitives)
- pages/ref04_arxiv_1701_08843_p3-03.png — Fig 4: 3D isometric of same device
- pages/ref05_arxiv_1111_2458_p1-1.png — Fig 1: minimal labelled cantilever + electret + electrode (HIGHLY RECOMMENDED)
- pages/ref05_arxiv_1111_2458_p2-2.png — Fig 3: circuit overlay on cantilever
- pages/ref06_scirep_77581_p6-06.png — Fig 4/5: BEST overall for Panel G (3D isometric bent cantilever + real photos + up/down twin panels) (HIGHEST RECOMMENDED)
- pages/ref07_natcomm_31822_p2-02.png — Fig 1: 3D forging illustration (palette reference only)
- pages/ref07_natcomm_31822_p3-03.png — Fig 2: contact-separate stack (air-gap convention)
- selected/ — empty, awaiting user curation
