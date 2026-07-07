# Reference-Gap Analysis — fig1_overview_v3_pair_001_vault

Generated: 2026-06-04. Scope: **measurable style only** (line weight, hue count, type ladder, density/whitespace, panel unification). Content/physics is out of scope per `candidates.md` ("STYLE anchors only").

## Provenance asymmetry — read this before the delta table

The two number columns are **not** measured the same way, and the table is honest about it:

- **fig1 column = EXACT.** The figure is a `standalone` document drawn in real `cm` coordinates with **no global `scale=`** on the tikzpicture (`.tex` lines 29–54). Page width is ~364pt (12.85 cm) + 8pt border. Therefore `line width=Xpt` in the `.tex` **is X pt on the printed page** — no conversion, no estimate. Font sizes are explicit `\fontsize{N}{...}` (4–8 pt). These values are ground truth.
- **Reference column = ESTIMATED.** Reference numbers are eyeballed off full-**page** PDF renders (`reference/_research/cand_*/pages/*.png`) at unknown physical print size and unknown render DPI. A 0.5pt-vs-1.0pt stroke difference is ~0.18 mm — at page-render resolution that is roughly 1 px, i.e. at the measurement floor. **Treat every absolute reference pt as `~approx`.**

Consequence, and the spine of this analysis: **trust the scale-invariant ratios (data : annotation : axis-frame tier), not the absolute reference pt.** Where fig1 and a reference differ by less than reference measurement error, the entry says "within tolerance — no change indicated" rather than manufacturing a delta inside the noise.

## Reference inventory (what was actually found)

- **5 papers**, 42 page-renders total. Not all renders carry figures (several are reference-lists / title pages / body text).
- **Figure-bearing reference pages usable as style anchors: ~30** (Angle A: ~22 figure pages across 3 papers; Angle C: ~8 figure pages across 2 papers).
- **Angle B (multi-panel overview composition) = EMPTY.** 0 PNGs. This is the most relevant angle for fig1's overall 6-panel layout and it has **no reference**. The layout/whitespace rows below therefore rest on general Nature-tier convention, not a matched anchor — flagged inline.

### Strongest anchors (by production tier, descending)

| ID | Paper | Best pages | Why it anchors fig1 |
|---|---|---|---|
| **C1** | Nat Commun 2024, s41467-024-49660-9 | p2 (Fig 1) | **Best single anchor.** Fig 1 mixes an instrument schematic + a workflow/arrow sub-panel + colormap data panels on white — the same heterogeneous-panel problem fig1 solves. Surface-potential domain. |
| **C2** | Nat Commun 2023, s41467-023-42583-x | p2 (Fig 1) | Probe-above-sample schematic geometry (closest spatial analog to the ISPD induction-probe panel e). |
| **A3** | Nat Commun 2020, s41467-020-19434-0 | p6 (Fig 4) | Nature-grade multi-panel **discipline**: 6 sub-panels (a–f), one schematic among data panels, consistent stroke/type across the grid. |
| **A2** | arXiv 2106.15460 (2021) | p2, p3 | Trap-DOS energy-diagram idiom (Gaussian DOS + dashed trap level + capture/emission arrows) — direct analog to panel c band diagram and panel e g(Eₜ). Preprint, not editorial-polished. |
| **A1** | arXiv 1108.2756 (2011) | p25, p28, p34 | Canonical g(E)-vs-energy DOS grammar. Old preprint, Computer-Modern serif + jet colormap — use for *layout idiom only*, not for type or palette. |

## Measurable style of the Nature-tier anchors (C1 / C2 / A3)

- **Line-weight tiers:** ~2 visible tiers. Data/curve + schematic-outline strokes are the heavy tier; axis spines + tick marks are a distinctly lighter tier. Estimated heavy:light ratio ≈ **~2:1**. Panel frames are usually **absent** (panels sit on white, separated by whitespace, not boxed) — C1/A3 do not box individual panels.
- **Hue count (base hues, tints collapsed):** ~**3 chromatic hues** (muted blue + orange/red + green/teal) on white, plus gray/black for structure. Curves stay distinguishable in grayscale (marker shape carries identity, not color alone).
- **Type ladder:** sans-serif throughout; bold lowercase panel letters (a, b, c) upright; compact axis labels with units in parentheses; one clear size step between panel letter and body text. No serif, no oversized titles.
- **Density / whitespace:** generous inter-panel whitespace; panels separated by gutters, not rules; each panel reads as an island. A3 Fig 4 packs 6 panels but keeps per-panel breathing room.
- **Unification of heterogeneous panels:** achieved by **shared stroke tier + shared 3-hue palette + shared type ladder + consistent whitespace rhythm**, NOT by background washes, boxes, or connecting frames.

## DELTA TABLE

`fig1 = exact (.tex)` · `ref = estimated (page render), treat absolute pt as ~approx` · recommendations cross-checked against documented `.tex` rationale.

| Dimension | Reference standard (estimated) | fig1 current (exact, .tex) | Recommendation |
|---|---|---|---|
| **Line-weight TIER RATIO** (the reliable comparison) | data:axis-frame ≈ **~2:1**, ~2 tiers | narrative 0.9 / annotation 0.7 / axes-spines 0.55 = **~1.6:1**, 3 tiers (.tex 34–37) | **Optional, taste-adjacent:** fig1's data tier is slightly less dominant over its axes than the references. Could nudge narrative→1.0pt **or** axes→0.45pt to reach ~2:1. Low priority — fig1's 3-tier scheme is intentional and documented (lines 34–37). Not a defect. |
| **Axis / spine absolute** | ~0.5–0.8 pt (`~est`, at measurement floor) | 0.55 pt (secondary tier) | **Within tolerance — no change indicated.** Difference is inside reference measurement error. |
| **Data-curve absolute** | ~0.9–1.2 pt (`~est`) | 0.9 pt (panels d/e curves) | **Within tolerance.** Matches reference heavy tier. |
| **Panel FRAME / box** | References do **not** box panels; white + whitespace gutters (C1, A3) | Row-2 columns boxed: cGray!22, **0.30 pt**, rounded 2pt (.tex 991–993) | **Intentional divergence — DO NOT bump.** `.tex` 991–992 documents the frame was deliberately subdued (tone + thinner stroke) after spoke-removal made it prominent. Reference convention is "no frame at all," but if a separator is wanted, current faint hairline is the correct direction. Leave as-is. |
| **Background** | Clean white (C1/A3) | Clean white | **Match.** `.tex` 56–59 documents the 2026-05-22 redirect that removed the cover-scene wash specifically to hit NC main-text white-background convention. Aligned. |
| **Chromatic hue count (base, tints collapsed)** | ~**3** (muted blue/orange/green) | ~**4** (amber-gold, blue, red, teal) — `\definecolor` 89–97; amber family is 4 tints of ONE hue | **Within range, no change.** fig1's blue/red/teal are literally Paul Tol's muted scheme (4477AA / CC6677 / 44AA99) — the same family the NC refs use. Amber is the 4th, carrying polymer identity. 4 vs 3 base hues is not a defect; do **not** read the 9 `\definecolor` lines as 9 hues. |
| **Grayscale-safety** | Curves separable by marker shape, not color alone | Blue/red curves in d use color + position; markers present | Minor: verify panels d/e curves stay separable in grayscale (shape/dash, not hue). Convention-level, not measured here. |
| **Panel-letter type** | Bold, lowercase, upright, ~1 step above body | 8 pt bold upright lowercase (a–f), panelLetter style (.tex 48–53) | **Match.** `.tex` 48–52 documents alignment to Nature "8 pt bold, upright (not italic)" rule. Aligned. |
| **Body / label cap** | Compact sans, units in parens, ≤ panel-letter size | 7 pt cap for non-letter text; 4–7 pt range; sans throughout (.tex 30–47) | **Match.** Capped at 7pt per Nature "max 7pt other text" (.tex 42–45). Type ladder is NC-conformant. No delta. |
| **Typeface** | Sans-serif throughout | sans (`\sffamily` everywhere) | **Match.** (A1's serif is the anti-example — do not borrow A1 type.) |
| **Whitespace / density rhythm** | Generous gutters; panels as islands; no connecting rules | 6 panels, 2 rows; inter-panel arrows + row-bridge arrow (1.6pt, .tex 40–41) carry the narrative | **No measured anchor (Angle B empty).** fig1 is denser than a pure data figure because it is a *concept/overview* figure with deliberate inter-panel narrative arrows — a legitimate Fig-1 genre the references don't cover. Judge against the manuscript's own Fig-1 intent, not against C1/A3 data-figure spacing. No change indicated from available refs. |
| **Heterogeneous-panel unification** | Shared stroke tier + 3-hue palette + type ladder + whitespace (no washes/boxes) | Shared palette + type ladder present; Row-2 uses faint column boxes instead of pure whitespace | fig1 already unifies via palette + type. The one stylistic divergence (faint Row-2 boxes vs reference whitespace-only) is documented-intentional (above). Mechanism is sound. |

## Bottom line

fig1 is **already at or inside Nature-tier convention on every typographic and chromatic dimension that can be measured exactly** (4–8pt sans ladder, 8pt bold upright lowercase letters, 7pt body cap, Paul-Tol muted palette, white background — all documented in the `.tex` as deliberate NC-compliance moves). The only reference-vs-fig1 differences are:

1. **Line-weight tier ratio** ~1.6:1 (fig1) vs ~2:1 (refs) — a real but optional, taste-adjacent nudge, NOT a defect; fig1's 3-tier scheme is documented.
2. **Row-2 column boxes** vs reference whitespace-only separation — documented-intentional, leave alone.
3. **Angle B gap:** no overview-composition reference exists, so the overall 6-panel layout/whitespace has no matched anchor and should be judged against the manuscript's own Fig-1 intent.

No recommended change contradicts a documented `.tex` rationale. Nothing here is a blocking defect.
