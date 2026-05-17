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

## Element-Iteration Loop (Nature-grade, 4-axis)

Loop driven by `iteration_prompt_template.md` (2026-05-17). Target: Nature-grade aesthetic + element-by-element quality. 4-axis acceptance: 이론 (T) / 구조 (S) / 스토리 (L) / 미감 (A). 10-iter cap per panel.

### Panel A iter 1/10 — 2026-05-17

- **Scope**: A-1 (4 DIB rings) + A-3 ((S)_x label verification)
- **Rationale**: A-1 is largest visual element + carries chemistry-drawing weight; A-3 just-fixed (C004 commit `34d973a`) needs validation in new iter context
- **Reference source**: briefing-only (Panel A positive-reference gap per audit_table.md); anti-reference (`sulfur_polymer_panelA_ref.png`) confirmed pattern to avoid (crosslinked network, >2 sulfide attachments per ring)
- **Patches**:
  - A-1: aromatic tick weight 0.55→0.65pt (.tex L104-106, applied to all 3 tick lines in `\dibRingAt` macro) — rationale: tick/outline ratio 0.79→0.93, closer to Nature chemistry-paper convention where ring outline and aromatic ticks have comparable weight presence
  - A-3: NO PATCH — verification only (post-C004 placement at x=2.10, y=7.55 confirmed centered above ring row, no overlap with S₈ inset at y=8.45)
- **Briefing edits**: none (briefing §13.1 does not lock aromatic tick width)
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ⚠️
- **Score delta (vs prior iter)**: baseline established for Nature-grade loop on Panel A (no prior iter)
- **Notes**: 0.10pt weight increase is at perceptibility edge in PNG raster; print scale (TIFF 600 DPI) should register more strongly. Panel A still has "schoolbook chemistry" feel overall — single patch on 1 element not transformative. Iter 2-3 candidates: A-2 (polysulfide segments) + A-4 (methyl pairs) to lift A axis to ✅.
- **Visibility gate**: intended yes (aromatic ticks present, hexagonal ring identity preserved) | anomaly none (no rogue stroke, no overlap, no ghost label)
- **Commit**: `a902864`

### Panel A iter 2/10 — 2026-05-17

- **Scope**: A-2 (polysulfide linker bonds — ring↔chain junction stubs) + A-4 (methyl pair stubs in `\methylPair` macro)
- **Rationale**: A-2 linker bonds previously cGray!75 — slight color mismatch with ring outline cGray!85 weakened chain-integrity visual binding. A-4 methyl stubs 0.45pt × 0.08cm — too subtle even for detail-tier role; "completely invisible at PNG" exceeds the "subtle but perceivable" intent of A-4 §13.1 role.
- **Reference source**: briefing-only (Panel A positive-reference gap)
- **Patches**:
  - A-2: 8 linker bond lines (`.tex` L143-150) color cGray!75!black → cGray!85!black (rationale: matches ring outline color exactly for chain-identity visual binding)
  - A-4: `\methylPair` macro lines (`.tex` L128, L130) line width 0.45pt → 0.55pt (rationale: detail tier lifted from "invisible" to "subtle but perceivable", still well below polysulfide 0.9pt = no competition)
- **Briefing edits**: none (briefing §13.1 does not lock linker bond color or methyl stub weight)
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ⚠️
- **Score delta (vs iter 1)**: T unchanged | S unchanged | L unchanged | A unchanged (incremental progress without ⚠️→✅ transition)
- **Notes**: Two consecutive iters with A ⚠️ — Nature-grade for Panel A apparently requires more than weight/color tweaks. Iter 3-5 candidates: A-5 (S₈ inset proportion), A-7 (wash ellipse), A-8 (typography hierarchy). If A still ⚠️ by iter 7, escalation diagnosis (a) TikZ ceiling or (b) need structural change beyond 1-line patches becomes likely.
- **Visibility gate**: intended yes (linker bonds darker matching ring; methyl stubs slightly more present at PNG) | anomaly none (no rogue stroke; color/weight changes preserve 3-tier discipline)

### Panel A iter 3/10 — 2026-05-17 — A+B mode (perceptible deltas)

- **Scope**: A-5 (S₈ atom letter font) + A-7 (wash ellipse tone)
- **Rationale**: After iter 1+2 micro-tweaks (0.10pt) showed sub-pixel changes invisible at typical PNG view resolution (user-flagged "그림 똑같다"), strategy pivoted to **A+B mode**: A = bigger per-patch deltas (≥+30%), B = different sub-region categories (structural/typography vs weight-only). Validates Nature-grade progress requires perceptible jumps.
- **Reference source**: briefing-only (Panel A positive-reference gap); workflow validation iter (D pre-step: per-panel crop generation via `pdftocairo -W 1100 -H 1300` to overcome Read-tool downsample)
- **Patches**:
  - A-5: S₈ atom letter font 4.4pt → 6pt (+36%) — 8 vertex S identities now readable; before, only outer S-S bond labels rendered (.tex L183, `\fontsize{4.4}{5.2}` → `\fontsize{6}{7.2}`)
  - A-7: wash ellipse tone cAmber!08 → cAmber!12 (+50%) — row-binding cue perceivable rather than near-invisible (.tex L95, `\fill[cAmber!08]` → `\fill[cAmber!12]`)
- **Briefing edits**: none (§13.1 A-5 font + A-7 wash tone within polish-range, not locked)
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ⚠️→✅ 🎯
- **Score delta (vs iter 2)**: T unchanged | S unchanged | L unchanged | **A ⚠️→✅ first transition**
- **Notes**: Panel A reached Nature-grade chemistry-paper presence at iter 3 (cumulative: iter 1 aromatic ticks + iter 2 linker color binding + methyl visibility + iter 3 S₈ atom identity + wash binding). Per template termination rule, need 1 more consecutive ✅ iter with no new sub-regions touched for closure. Iter 4 candidate: verification-only OR continued polish on A-6/A-8.
- **Visibility gate**: intended yes (S₈ vertex identities readable, wash visible as row anchor) | anomaly none (no overlap, no rogue stroke; palette/font stay within §10 polish ceiling)
- **Workflow validation**:
  - **D (DPI investigation)**: build PNG was already 600 DPI (4272×2688). Apparent low-res was Read-tool downsample at conversation-display layer. Fix: `pdftocairo -W <px> -H <px>` per-panel crop, smaller file = less downsample → micro-changes visible.
  - **A (delta size)**: ≥+30% changes (font, tone, color hue) PNG-visible at standard resolution; <±0.15pt weight tweaks remain sub-pixel.
  - **B (sub-region category)**: structural / typography / wash hue changes more transformative than weight-only tweaks on the same sub-region. Future iters should mix categories.

- Dashed-line semantics (#17) remain intentionally diverse: Debye reference,
  escape arrow, inverse-vulcanization arrow, and leaders carry different
  meanings. This is low-priority residual risk unless final review finds that
  readers confuse them.
- This file gives one pilot's live iteration evidence only. Cross-fixture
  generalization remains pending.
