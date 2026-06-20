# Reference Candidates — Consolidated Index

Consolidated: 2026-06-04
Source sub-dirs: cand_a_trap_dos_band / cand_b_overview_composition / cand_c_measurement_polymer

**These are STYLE anchors only.**
Use them to borrow line weight, palette, typography, and panel composition conventions.
Content (physics, axis labels, data, captions) stays entirely from your own science.
Do not pick a winner here — curate by copying pages you want into a `selected/` folder.

Total candidates: 5 papers
- Angle A (trap/DOS/band diagrams): 3 papers, all rendered
- Angle B (overview-composition, multi-panel Fig 1): 0 papers — angle came up empty, no PNGs
- Angle C (measurement schematic / charge decay): 2 papers, all rendered

---

## Angle A — Trap/DOS, Band Diagrams, Energy Schematics

### A1 — arXiv 1108.2756 (2011)

| Field | Value |
|---|---|
| Source | https://arxiv.org/abs/1108.2756 |
| Title | Modeling Space-Charge Limited Currents in Organic Semiconductors: Extracting Trap Density and Mobility |
| Journal / Year | arXiv preprint, August 2011 (pre-2015; no peer-review venue confirmed from renders) |
| Pages rendered | pp 22–35 (figure section only — no title page rendered; only figure pages available) |

**Rendered pages and their content:**

| Page | Relative PNG | Content visible |
|---|---|---|
| 22 | cand_a_trap_dos_band/pages/probe_1108_2756_p-22.png | References list (no figure) |
| 23 | cand_a_trap_dos_band/pages/probe_1108_2756_p-23.png | References list continued |
| 24 | cand_a_trap_dos_band/pages/probe_1108_2756_p-24.png | Fig 1: HOMO/LUMO band diagram (equilibrium + bias), 2-panel (a)(b), minimal black-and-white linework |
| 25 | cand_a_trap_dos_band/pages/probe_1108_2756_p-25.png | Fig 2: trap density g(E) vs energy (eV), log-linear, piecewise exponential fit — single panel |
| 26 | cand_a_trap_dos_band/pages/probe_1108_2756_p-26.png | Fig 3: J(V) log-log multi-curve (T-series, rainbow colormap), measurement vs model |
| 27 | cand_a_trap_dos_band/pages/probe_1108_2756_p-27.png | Fig 4: same J(V) format, exponential DOS, asymmetric contacts |
| 28 | cand_a_trap_dos_band/pages/probe_1108_2756_p-28.png | Fig 5: g(E) comparison — delocalized peak + exponential/Gaussian overlaid, 4-line legend |
| 29 | cand_a_trap_dos_band/pages/probe_1108_2756_p-29.png | Fig 6: J(V) Gaussian DOS + asymmetric contacts |
| 30 | cand_a_trap_dos_band/pages/probe_1108_2756_p-30.png | Fig 7: potential profile vs distance, inset (virtual cathode position vs voltage) |
| 31 | cand_a_trap_dos_band/pages/probe_1108_2756_p-31.png | Fig 8: Fermi-level position vs applied voltage (T-series, rainbow) |
| 32 | cand_a_trap_dos_band/pages/probe_1108_2756_p-32.png | Fig 9: g(E) comparison with error bars — 4-line legend with red squares |
| 33 | cand_a_trap_dos_band/pages/probe_1108_2756_p-33.png | Fig 10: J(V) piecewise exponential DOS |
| 34 | cand_a_trap_dos_band/pages/probe_1108_2756_p-34.png | Fig 11: Gaussian DOS discretization schematic — labeled curve with dashed verticals |
| 35 | cand_a_trap_dos_band/pages/probe_1108_2756_p-35.png | Fig 12: sensitivity curves (5 lines, multi-marker, log-log) |

**Style anchor strengths:**
- Fig 2 / Fig 5 / Fig 9 (pp 25, 28, 32): canonical g(E) vs energy axis layout — delocalized states shown as a tall rectangular block at E=0, trap tail decaying into the gap. Clear axis label format: "Trap density (cm⁻³ eV⁻¹)". This is the canonical visual grammar for trap-DOS schematics.
- Fig 11 (p 34): schematic of Gaussian DOS with dashed-line bin annotations and subscript notation — useful reference for how to annotate energy bins on a g(E) curve without overloading the figure.
- T-series J(V) plots (pp 26–27, 29, 33): rainbow spectrum colormap for temperature series on log-log axes — clean convention, easy to read at a glance.
- Minimal whitespace layout: figures occupy a fixed width, heavy typography uses bold "Figure N:" captions.

**Style anchor weaknesses:**
- Pre-2015 preprint (2011): typography is LaTeX default (Computer Modern serif), figure captions use bold-colon format inconsistent with Nature/ACS styles. No panel letters (a)(b)(c) convention.
- MATLAB-generated plots: axis tick density and line styles are software defaults, not publication-polished.
- Palette on multi-curve plots uses MATLAB's jet colormap (blue→red rainbow) which has known perceptual non-uniformity issues and prints poorly in grayscale.
- Only a preprint — no journal editorial polish.
- No measurement schematic, no device stack diagram in the rendered pages.

---

### A2 — arXiv 2106.15460 (2021)

| Field | Value |
|---|---|
| Source | https://arxiv.org/abs/2106.15460 |
| Title | Analytical Model for Gaussian Disorder Traps in Organic Thin-Film Transistors |
| Journal / Year | arXiv preprint, June 2021 (authors: Quanlong Chen et al., affiliations: Chinese institutions visible on p-1) |
| Pages rendered | pp 1–7 |

**Rendered pages and their content:**

| Page | Relative PNG | Content visible |
|---|---|---|
| 1 | cand_a_trap_dos_band/pages/probe_2106_15460_p-1.png | Title, abstract, author affiliations |
| 2 | cand_a_trap_dos_band/pages/probe_2106_15460_p-2.png | Fig 1: side-by-side schematic of HOMO DOS (Gaussian) for HOMO and DLT — filled trap level shown as shaded region below Fermi level; compact two-panel energy diagram |
| 3 | cand_a_trap_dos_band/pages/probe_2106_15460_p-3.png | Figs 2–3: trapping/detrapping process energy diagrams (HOMO Gaussian DOS + DLT DOS panels), with E_ft and E_f_0 levels annotated; arrowed transition schematics |
| 4 | cand_a_trap_dos_band/pages/probe_2106_15460_p-4.png | Fig 4: (a) g(E) vs barrier height, (b) dependence on parameters; small multi-panel inset plots |
| 5 | cand_a_trap_dos_band/pages/probe_2106_15460_p-5.png | Fig 5: parameter tables + comparison plots |
| 6 | cand_a_trap_dos_band/pages/probe_2106_15460_p-6.png | Fig 6: device schematic (OTFT cross-section) + measurement results — schematic linework with device layers labeled |
| 7 | cand_a_trap_dos_band/pages/probe_2106_15460_p-7.png | References |

**Style anchor strengths:**
- Fig 1 (p 2) and Figs 2–3 (p 3): the DOS energy diagram format is the strongest style reference among the Angle A candidates. Shows HOMO Gaussian peak with filled/unfilled regions, trap level E_ft as a horizontal dashed line, and shaded area below. Clean two-column layout. The trap-state annotation idiom (dashed level + labeled arrow) is exactly the visual convention needed for a band-diagram panel.
- Trapping/detrapping arrow schematic (p 3): arrowed transitions between HOMO states and trap states, clear energy axis. Useful reference for how to draw carrier capture/emission arrows without crowding.
- Fig 6 (p 6): OTFT device cross-section with labeled gate/dielectric/semiconductor/drain/source layers — thin-line architecture diagram.
- Typeset as a short preprint: compact layout, moderate whitespace.

**Style anchor weaknesses:**
- Preprint only — no journal editorial polish or Nature-grade figure production.
- Small panel size: individual panels in Figs 2–4 are compact and dense; axis labels use small font relative to figure area — may be difficult to read at publication size without enlargement.
- Palette is limited: mostly black-and-white with blue/red highlights; color use is inconsistent across panels.
- p 4–5 panels (parameter sweeps) are dense with data and hard to parse without domain context.

---

### A3 — Nature Communications 2020 (10.1038/s41467-020-19434-0)

| Field | Value |
|---|---|
| Source | https://doi.org/10.1038/s41467-020-19434-0 |
| Title | Charge-generating mid-gap trap states define the thermodynamic limit of organic photovoltaic devices |
| Journal / Year | Nature Communications, 2020 (OA, CC BY 4.0); authors include Zarrabi, Sandberg, Zeiske, Li, Drew, Riley, Meredith, Armin |
| Pages rendered | pp 1–10 |

**Rendered pages and their content:**

| Page | Relative PNG | Content visible |
|---|---|---|
| 1 | cand_a_trap_dos_band/pages/probe_s41467_020_19434_0_p-01.png | Title page with Nature Comms header, abstract |
| 2 | cand_a_trap_dos_band/pages/probe_s41467_020_19434_0_p-02.png | Body text (no figure) |
| 3 | cand_a_trap_dos_band/pages/probe_s41467_020_19434_0_p-03.png | Fig 1: Voc vs illumination plots (EQEpv spectra, VOC-series) — multi-panel data plots, clean Nature axis style |
| 4 | cand_a_trap_dos_band/pages/probe_s41467_020_19434_0_p-04.png | Fig 2: EQEpv spectra + Voc curves with model overlaid — high-quality line plots, consistent palette |
| 5 | cand_a_trap_dos_band/pages/probe_s41467_020_19434_0_p-05.png | Fig 3: sub-gap Voc-illumination analysis + inset EQEpv spectrum — 4-panel publication layout |
| 6 | cand_a_trap_dos_band/pages/probe_s41467_020_19434_0_p-06.png | Fig 4: two-diode model circuit diagram + J(V) multi-panel — 6 sub-panels (a)–(f), ideal diode/trap diode circuit schematic |
| 7 | cand_a_trap_dos_band/pages/probe_s41467_020_19434_0_p-07.png | Fig 5: sub-gap EQEpv spectra for multiple cells |
| 8 | cand_a_trap_dos_band/pages/probe_s41467_020_19434_0_p-08.png | Fig 6: trap-state specific detectivity + mid-gap detection — 3-panel |
| 9 | cand_a_trap_dos_band/pages/probe_s41467_020_19434_0_p-09.png | Fig 7: illumination-dependent Voc per cell — large multi-panel |
| 10 | cand_a_trap_dos_band/pages/probe_s41467_020_19434_0_p-10.png | References |

**Style anchor strengths:**
- Nature Communications production quality: the strongest typographic and visual production standard in Angle A. Panel letters (a)(b)(c) in bold, tight sans-serif axis labels, consistent line weights across panels, clean white backgrounds.
- Fig 4 (p 6): two-diode equivalent circuit schematic is a reference-quality circuit diagram embedded in a multi-panel figure — shows how to integrate a schematic panel with data panels in the same figure grid at Nature style.
- Multi-panel layout discipline (Figs 3, 5, 6, 7, 9): consistent panel sizing, shared axes, minimal redundant decoration. The 6-panel Fig 4 in particular demonstrates how to pack multiple related datasets into one cohesive figure without clutter.
- Color palette: muted blue, orange, green accents on white — Nature Comms standard. Prints well in grayscale (curves distinguished by marker shape not just color).
- Axis label typography: unit notation in parentheses (cm⁻², eV), compact font, no redundant "axis title" framing.

**Style anchor weaknesses:**
- OPV / photovoltaic domain context — band-gap trap physics in solar cell context rather than polymer dielectric. No surface-potential or charge-decay schematics.
- No energy band diagram or g(E) schematic in the rendered pages — the figures are primarily measurement data plots, not energy-level diagrams. For trap-DOS schematic style, A2 is a stronger reference.
- Dense panel packing (Fig 4 has 6 panels): the individual panels are small; if the user's figure has fewer panels, this layout may not translate directly.

---

## Angle B — Multi-panel Overview Figure Composition

**No candidates.** The `cand_b_overview_composition/` sub-dir contains only a stub `candidates.md` with an empty table and no rendered PNGs. The search was conducted but yielded no papers meeting the filter criteria (OA + ≥4 of 5 target panel types in Fig 1). This angle is a gap.

If Angle B coverage is needed, suggested re-search terms:
- "polymer dielectric overview figure nature communications 2022 2023 2024"
- "organic semiconductor device schematic overview multi-panel figure arXiv"

---

## Angle C — Measurement Schematic / Surface Potential / Charge Decay

### C1 — Nature Communications 2024 (10.1038/s41467-024-49660-9)

| Field | Value |
|---|---|
| Source | https://doi.org/10.1038/s41467-024-49660-9 |
| Journal / Year | Nature Communications 2024, PMC OA (CC BY 4.0) |
| Pages rendered | pp 2–7 |

**Rendered pages and their content:**

| Page | Relative PNG | Content visible |
|---|---|---|
| 2 | cand_c_measurement_polymer/pages/ref01_s41467-024-49660-9_p2-02.png | Fig 1: full instrument schematic (TENG scanning platform, corona-probe, surface-potential scanning) + iterative regularization workflow panels — 4-panel layout on white background |
| 3 | cand_c_measurement_polymer/pages/ref01_s41467-024-49660-9_p3-03.png | Fig 2 / body text: surface charge distribution panels, colormap grids |
| 4 | cand_c_measurement_polymer/pages/ref01_s41467-024-49660-9_p4-04.png | Fig 3: corona discharge electrode schematic (three-electrode) + charge map results |
| 5 | cand_c_measurement_polymer/pages/ref01_s41467-024-49660-9_p5-05.png | Fig 4: charge density distribution plots |
| 6 | cand_c_measurement_polymer/pages/ref01_s41467-024-49660-9_p6-06.png | Fig 5: ISPD (isothermal surface potential decay) multi-curve plots |
| 7 | cand_c_measurement_polymer/pages/ref01_s41467-024-49660-9_p7-07.png | Supplementary / conclusions section |

**Style anchor strengths:**
- Fig 1 (p 2): the instrument schematic panel shows a surface-potential scanning platform with labeled components (probe, sample stage, motion controller, oscilloscope) — this is the closest available analog to a measurement-setup schematic for surface-potential work. Clean white background, clear label lines, consistent stroke weight.
- Fig 1 also includes a multi-step workflow diagram with arrows connecting schematic stages — useful reference for how to embed a process-flow sub-panel adjacent to an instrument diagram.
- Blue/orange accent palette on white: consistent across all panels, prints in grayscale via distinct gray levels.
- Nature Comms production: tight axis labels, bold panel letters, consistent figure sizing.
- Fig 5 (p 6): ISPD decay curves with multiple samples — multi-curve log-time or linear-time plot format.

**Style anchor weaknesses:**
- TENG (triboelectric nanogenerator) application context: the instrument scans a horizontally-moving TENG, not a stationary polymer film with induction probe above. The probe geometry is lateral (horizontal scan), whereas the user's Keyence SK ESVM setup is a stationary induction probe above a sample. The schematic's spatial orientation may not directly translate.
- Saturated color accents in workflow panels (teal/orange) are stronger than typical materials-science palette — may need toning down.
- Corona schematic (p 4) shows three-electrode configuration as a plan-view diagram, not a cross-section. If the user's setup uses a different electrode geometry, the content diverges.

---

### C2 — Nature Communications 2023 (10.1038/s41467-023-42583-x)

| Field | Value |
|---|---|
| Source | https://doi.org/10.1038/s41467-023-42583-x |
| Journal / Year | Nature Communications 2023, PMC OA (CC BY 4.0) |
| Pages rendered | pp 2–6 |

**Rendered pages and their content:**

| Page | Relative PNG | Content visible |
|---|---|---|
| 2 | cand_c_measurement_polymer/pages/ref02_s41467-023-42583-x_p2-02.png | Introduction text + Fig 1: KPFM system schematic with scanning tip trajectory above sample — probe-above-sample geometry, labeled components |
| 3 | cand_c_measurement_polymer/pages/ref02_s41467-023-42583-x_p3-03.png | Fig 2/3: LAO/STO device cross-section schematic + charge relaxation temporal profiles — two-panel layout |
| 4 | cand_c_measurement_polymer/pages/ref02_s41467-023-42583-x_p4-04.png | Fig 3 continued: decay profiles at multiple temperatures, Arrhenius analysis panel |
| 5 | cand_c_measurement_polymer/pages/ref02_s41467-023-42583-x_p5-05.png | Fig 4: spatial mapping panels + decay fits |
| 6 | cand_c_measurement_polymer/pages/ref02_s41467-023-42583-x_p6-06.png | Fig 5: further temporal analysis + discussion panels |

**Style anchor strengths:**
- Fig 1 (p 2): KPFM probe-above-sample geometry schematic — tip illustrated above the sample surface with trajectory arc, labeled with measurement parameters. This is the closest spatial match to an induction-probe-above-sample setup (closer than C1's horizontal scan). Strong anchor for drawing the probe geometry in a measurement schematic panel.
- Charge relaxation temporal decay plots (pp 3–4): multi-temperature curves on linear or log-time axes, clean curve labeling with temperature as parameter. Directly relevant to surface-potential decay visualization.
- Arrhenius analysis panel (p 4): 1/T vs ln(rate) scatter plot with linear fit — reference for how to present activation-energy extraction.
- Compact 5-panel structure: demonstrates tight but readable multi-panel layout at Nature scale.
- Grayscale + single accent color palette: prints perfectly in grayscale.

**Style anchor weaknesses:**
- KPFM nanoscale technique: the probe tip in the schematic is an AFM cantilever (nanoscale), not a macroscopic induction voltmeter. The schematic scale and probe illustration style will need adaptation for a macroscopic instrument.
- Oxide device (LAO/STO) context: no polymer, no corona charging. Content diverges significantly from user's system.
- No corona discharge or charging-setup diagram in any of the rendered pages.

---

## Summary

| Angle | Papers | PNGs | Status |
|---|---|---|---|
| A — trap/DOS/band diagrams | 3 | 31 pages | Rendered; annotations above |
| B — overview-composition (multi-panel Fig 1) | 0 | 0 | **Empty — no candidates found** |
| C — measurement schematic / charge decay | 2 | 11 pages | Rendered; annotations above |
| **Total** | **5** | **42 pages** | |

**Note on A1 (arXiv 1108.2756):** This is a 2011 preprint, predating the 2015 cutoff the other angles applied. It is included here because the upstream research session rendered it, and its g(E) vs energy figures (pp 25, 28, 32) and DOS schematic (p 34) remain useful style references for the canonical trap-DOS plot format. The user should weigh the age and preprint status against the visual utility.

**Angle B gap:** No multi-panel overview-composition references were found. If this angle matters for drawing the overall figure layout, a new search pass is needed.
