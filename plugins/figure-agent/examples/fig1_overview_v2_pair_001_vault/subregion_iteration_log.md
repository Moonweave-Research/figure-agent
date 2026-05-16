# Sub-Region Iteration Log: fig1_overview_v2_pair_001_vault

## Scope

This is the live dogfood evidence file for the text-form sub-region loop
described in `docs/subregion-iteration-tool.md`. It records observed patch
units from `briefing.md` section 13 and the current v5-v7 authoring history.

## Active Target Set

| State | Sub-region ID | Evidence | Notes |
|---|---|---|---|
| active target | none | `briefing.md` section 13.9 says all panels are at a stable point after v5/v5.1/v6/v6.1/v7 closure. | Keep the active set empty until a new critique, audit, or human review names a concrete patch target. |
| named but stable | A-1..A-8 | Panel A is stable after the linear topology author decision. | Reopen only if manuscript chemistry contradicts linear poly(S-r-DIB). |
| named but stable | C-L1..C-R6 | Panel C is stable enough for this manual protocol audit; C-L1 remains a deferred SVG-handoff quality debt, not an active patch in this loop. | Do not turn deferred quality debt into an automatic blocker without a fresh review. |
| named but stable | Row2-BG, Row2-BR1, Row2-BR2 | v7 row-2 width normalization and spoke endpoint update are recorded in `briefing.md`. | Reopen if the final review reads the spokes as sequential causation. |
| named but stable | D-1..D-5, E-1..E-4, F-1..F-5, G-1..G-7 | v5-v7 notes record the latest patch cycle. | Reopen individual sub-regions only from concrete visual/theory findings. |

## Iteration Log

| Iteration | Sub-region ID | Problem | Patch Summary | Result | Follow-up |
|---|---|---|---|---|---|
| v5 | G-2, G-7 | Electrode and air gap did not strongly communicate the mechanical setup. | Shifted electrode right by 0.85 cm and widened the air gap from 0.575 cm to 1.425 cm. | Improved separation and Coulomb-probe readability. | Keep Maxwell-attraction transfer forbidden. |
| v5.1 | G-1, G-2, G-3 | Panel G looked too flat and lacked material identity. | Added metallic/polymer gradients, locked upper-left light source, and added low-opacity internal polymer-chain hints. | Improved schematic depth without changing mechanics. | Preserve light-source convention across future gradients. |
| v6 | D-1, E-1, F-1 | Row 2 iconic plots were too tall and plot-like. | Compressed D/E/F axis tops from 4.10 to 3.40 and kept tickless arrow axes. | Moved Row 2 closer to cover-style icon panels. | Do not reintroduce axis frames or ticks. |
| v6 | D-2, D-3 | Kinetic cartoon risked wrong non-Debye reading. | Redrew two separated no-crossing power-law lines and a steeper Debye reference below both long-time tails. | Non-Debye tail invariant became visually explicit. | Recheck after any D width or label patch. |
| v6 | B-1 | Chain rows occupied too much vertical span. | Compressed chain row spacing from 0.75 to 0.60 cm. | Reduced bead-string dominance while keeping four chain lengths. | Keep Panel B composition labels out of Row 2. |
| v6.1 | E-1, E-2 | Panel E axis/curve implied log-time behavior rather than raw linear-time ISPD decay. | Changed x-axis label from log t to t and redrew a linear-time stretched-exponential decay. | Better matches raw surface-potential decay claim. | Reopen only if manuscript wants log-time schematic. |
| v7 | D-1..D-5, E-1..E-4, Row2-BR2 | Row 2 panel widths were uneven and the first spoke endpoint no longer matched the new D geometry. | Shrunk D x-span, widened E, moved the D spoke endpoint and kinetic label, and shifted the E panel letter. | D/E/F/G widths now read more balanced. | Watch for label collisions in final visual review. |
| v7 | G-1, G-2, G-3, G-4, G-6 | Panel G height and polymer length overpowered the row after width normalization. | Scaled polymer y-extent, moved clip/mount/electrode down, shortened electrode, and repositioned charge markers and Coulomb label. | Mechanical scene fits the row while preserving hanging-cantilever logic. | Recheck Coulomb-only direction and air gap label. |
| v7 | C-R2, C-R3 | Trap levels were below the mechanism-tier line-weight convention. | Increased shallow/deep trap level line width from 0.80 pt to 1.00 pt. | Improved mechanism hierarchy. | Preserve C/F shallow-blue and deep-red consistency. |
| v7 | E-3 | Open markers conflicted with the current filled-marker convention. | Changed E markers from white fill to cRed!50 fill. | Improved marker convention consistency. | Verify markers do not overstate measured-data precision. |
| v8.2 | G-6 | Two-line "Coulomb / repulsion" label stack at anchor=east placed both bbox centers across the arrow line at y=1.99 (IoU=0.157, critique C001). | Flipped anchors to south east / north east at y=2.04/1.94 so the arrow now sits BETWEEN the labels. | C001 closed. | None — arrow geometry unchanged; briefing §13.8 G-6 + §13.10 updated to record the v8.2 anchor flip pattern. |
| v8.2 | A-8 | "Sulfur-rich polymer" / "poly(S-r-DIB) linear copolymer" subtitle stack at 0.25 cm gap clipped descender / ascender (IoU=0.055, critique C002). | Dropped subtitle from y=5.55 to y=5.42 to widen the gap to 0.38 cm. | C002 closed. | None. |
| v8.2 | A-8 | "inv. vulc." italic annotation at (2.55, 8.00) bumped the S8 octagon's lower-left vertex S atom (IoU=0.145). | Shifted to (2.15, 7.82) into the gap between chain composition label (top y=7.55) and S8 ring (bottom y=8.10). | S8 vertex collision eliminated; residual IoU=0.068/0.092 vs chain "−(S)x−" composition label is below the 0.1 visual-defect threshold. | None — briefing A-8 did not lock the inv. vulc. coordinate, so this is polish-only. |
| v8.3 | C-R1b | Shallow Gaussian DOS overlay σ=0.06 in `.tex` did not match `briefing.md` §13.3 spec σ=0.085. | Updated denominator in `exp(-(x-μ)²/(2σ²))` form: 0.0072 → 0.01445. | Briefing-grounded spec now matches `.tex`. | Visual: shallow DOS overlay slightly wider, smoother bell — still narrow vs deep (σ=0.18). |
| v8.3 | C-R5 | ΔE_t depth annotation arrow + label rendered cGray!70!black; `briefing.md` §13.3 spec calls for cRed!75 to bind the depth scalar to the deep trap species. | Recolored arrow + label to cRed!75!black per briefing §8.6 / §13.9 Binding-1. | Color binding strengthens TG-CFG-001 deep-red consistency. | None. |
| v8.3 | Row2-Caption | "convergent evidence -- three independent probes ..." used `--` (en-dash) but briefing §13.4 Row2-Caption spec calls for em-dash. | Changed `--` to `---` so the rendered caption shows —. | Em-dash convention restored. | None — typographic fix only. |

## Residual Risk

- Dashed-line semantics (#17) remain intentionally diverse: Debye reference,
  escape arrow, inverse-vulcanization arrow, and leaders carry different
  meanings. This is low-priority residual risk unless final review finds that
  readers confuse them.
- This file gives one pilot's live iteration evidence only. Cross-fixture
  generalization remains pending.
