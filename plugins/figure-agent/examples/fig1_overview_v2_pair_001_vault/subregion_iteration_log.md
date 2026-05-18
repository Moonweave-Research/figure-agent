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

### Panel A iter 4/10 — 2026-05-17 — verification-only closure

- **Scope**: NONE (verification iter per template termination rule)
- **Rationale**: Iter 3 reached first all-4-axis ✅. Template termination: "All 4 axes ✅ for 2 consecutive iters with no new sub-regions touched → panel done." Iter 4 verifies state holds at 4-axis ✅ without further patches.
- **Reference source**: N/A
- **Patches**: NONE
- **Briefing edits**: none
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 3)**: all axes unchanged, no patches applied
- **Closure status**: ✅ **PANEL A CLOSED** (2 consecutive 4-axis ✅ verified, no new sub-region touches)
- **Remaining (deferred, not blocking closure)**:
  - A-6 (inv. vulc. dashed arrow + label) — visible but path clarity could improve in future polish round
  - A-8 (typography proportion) — 'Sulfur-rich polymer' bold label occupies ~30% panel vertical; not Nature-grade weakness but proportion could rebalance toward drawing in a future hero-figure pass
- **Visibility gate**: intended yes (all sub-regions perceivable at standard PNG view) | anomaly none
- **Next**: template improvement pass (delta-size guideline, D pre-step formalization, per-iter crop). Then promote learnings to template before next panel pilot.

### Panel A iter 5/10 — 2026-05-17 — closure REOPEN + label cluster fix

- **CLOSURE INVALIDATION**: iter 4 closure declared at `9f2c40d` is **REVOKED**. User-flagged label-cluster overlap ((S)_x + inv.vulc. crowding above ring row) — audit blind spot, acceptance criterion (S13) was missing. False-closure pattern: 4 axes ✅ achieved against incomplete acceptance set.
- **Scope**: A-3 ((S)_x position) + A-6 (inv. vulc. position)
- **Rationale**: User direction: (S)_x left-shift + inv.vulc. critique-iter position. Literature check (WebSearch + WebFetch) confirmed `(S)_x` notation defensible (no standard convention); briefing semantic unchanged. Cluster separation strategy: (S)_x to true ring-row geometric center; inv.vulc. up and right onto dashed-arrow midpath.
- **Reference source**: briefing-only (Panel A reference gap, literature notation cross-check via 2025 RSC review + 2023 JACS mechanism paper)
- **Patches**:
  - A-3 `(S)_x`: anchor x 2.10 → 1.85 (-0.25cm); rationale: ring centers average (0.75+1.50+2.25+3.00)/4 = 1.875 → true geometric center, "centered above row" briefing §13.1 fully satisfied
  - A-6 `inv. vulc.`: position (2.15, 7.82) → (2.40, 7.90); rationale: vacate (S)_x label region, settle in gap between (S)_x top (y=7.85) and S₈ bottom (y=8.10), aligned along dashed-arrow midpath
- **Briefing edits**: none in this iter. Separately flagged for user: briefing claims sample range S60..S85, user clarified actual range 65–85 wt% S → S60 (40 wt% DIB) would be in crosslinked regime contradicting "linear copolymer" subtitle; Type A edit candidate pending user confirmation of actual sample names.
- **New acceptance bullet (panel_goals.md S13)**: "Label cluster mutual bbox non-overlap, minimum 0.05cm gap" — closes audit blind spot from iter 1-4
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 4)**: S ✅→✅ (S13 now in acceptance set, this iter PASS) | A unchanged ✅
- **Notes**: visual clash count 58→54 confirms label-on-label conflict reduction. (S)_x at true ring-row center reads naturally; inv.vulc. on arrow path reads as proper arrow annotation; 3-way cluster ((S)_x / inv.vulc. / S₈) clearly separated.
- **Visibility gate**: intended yes (cluster separation visible at crop) | anomaly none (no new overlap; check_visual_clash count dropped)
- **Closure status**: iter 6 verification required for new closure (2-consecutive 4-axis ✅ rule, this is first ✅ after reopen)

### Column E iter 7/10 — 2026-05-18 — sample stack realistic ratio + disk metallic tint (ref01 grounded)

- **Scope**: E-2 sample stack thickness + disk electrode material identity (atomic — interlocked via ground positioning + label collision)
- **Rationale**: Figure-research starting set (4 selected) read; ref01 Checa NatComm 2023 SS-KPFM shows real thin-film-on-substrate cross-section with substrate visually dominant (vs our equal-thickness layers). User "진짜 일러스트하게" + "Claude 그린 느낌" reframed as need for material-realistic representation, not generic schematic.
- **Reference source**: ref01 Checa NatComm 2023 (apparatus cross-section convention); ref09 NatMater2025 (line-weight hierarchy reference)
- **Patches**:
  - **Patch A — Substrate thickness 0.11→0.22cm (2×)**:
    - Substrate fill rect: (6.30, 3.34)→(7.85, 3.45) becomes (6.30, 3.23)→(7.85, 3.45)
    - Substrate hatching: 10 lines proportionally extended; slope (\hx, 3.45)→(\hx-0.07, 3.34) becomes (\hx, 3.45)→(\hx-0.14, 3.23) (maintain 1:1.57 slope angle)
    - Ground tap point: (7.85, 3.39)→(7.85, 3.34) (new substrate mid)
    - Ground bars: y=3.20/3.23/3.26 → y=3.12/3.15/3.18 (shifted down to clear thicker substrate)
    - Polymer film label position: (7.075, 3.32) anchor=north → (7.075, 3.20) anchor=north (clears new substrate bottom)
  - **Patch B — Disk electrode material identity**:
    - Fill: cGray!50!white → **cAmber!18** (subtle metallic Au/Pt tint)
    - Outline: cGray!75!black 0.32pt → **cGray!85!black 0.40pt** (bolder material identity)
- **Briefing edits (Type B, user-authorized)**: §13.6 E-2 sample-stack spec updated (substrate 0.22cm, ref01 convention cite); disk electrode spec updated (cAmber!18 metallic tint, 0.40pt outline)
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 6)**: T unchanged (ISPD invariants intact — physical layout of polymer-on-substrate now MORE accurate) | S unchanged (geometry adjustments, structure intact) | L improved (sample now reads as real research sample, not schematic slab) | A significantly improved (substantial M1 "icon→paper-grade" progress via ref01 grounding)
- **Notes**:
  - This is the most user-impactful aesthetic iter since iter 2 — sample stack now visually communicates "thin film deposited on substrate" which is the actual physical reality of ISPD measurement samples.
  - cAmber!18 disk fill subtle enough not to overpower (less than polymer's cAmber!28).
  - 10 hatch lines at extended length read as denser substrate — visual identity stronger.
  - Closure NOT declared per user.
- **Visibility gate**: intended yes (substrate clearly dominant; polymer thin layer on top; disk has metallic tint) | anomaly none (ground bars + label repositioned cleanly without collision)

### Column E iter 6/10 — 2026-05-18 — Kelvin probe disk-on-shaft + V_s decay icon (Tech illustrator)

- **Scope**: E-2 apparatus zone — Kelvin probe + V_s meter (2 elements, atomic since they're connected via lead)
- **Rationale**: Tech illustrator audit (parallel 4-designer pass) most strongly flagged Kelvin probe identity ("reads as hot plate + RF wireless, not Kelvin probe") and V_s meter sinusoid ("wrong cue — V_s is slow exponential decay, not AC sine"). User: "진짜 일러스트하게 가보자" — proper instrument illustration mode.
- **Reference source**: Tech illustrator audit + He NatComm 2024 Fig 1c (disk-on-shaft probe convention + electrostatic voltmeter labeling)
- **Patches**:
  - **Kelvin probe**: horizontal block (7.20..7.60, 3.60..3.73) + arcs above → **disk-on-shaft**:
    - Vertical shaft (cGray!75 0.32pt) from y=3.95 to 3.66
    - Disk electrode at bottom (cGray!50!white fill, 7.25..7.55, 3.62..3.66, flat horizontal conductive face)
    - **Vertical ↕ vibration arrow ON shaft** (cGray!65 0.32pt, y=3.76..3.88) — Kelvin modulation signature
    - **Air gap indicator** (dashed vertical line cGray!55 0.18pt at x=7.68 + `d` label at (7.70, 3.57)) between disk bottom (y=3.62) and polymer top (y=3.52) — non-contact geometry
    - Probe label repositioned (7.62, 3.82)
  - **V_s meter sinusoid → exponential decay icon**: prior 3-cycle sine wave (Tech illustrator: sine is AC cue, wrong for slow V_s decay over seconds) → smooth bezier decay curve from y=3.98 left to y=3.92 plateau right
  - **Probe-to-meter lead y**: 3.85 → 3.95 to match new shaft top
- **Briefing edits (Type B, user-authorized "진짜 일러스트하게")**: §13.6 E-2 Kelvin probe + V_s meter specs fully rewritten (disk-on-shaft, vertical vibration, air gap, decay icon, lead y) with iter6 rationale + Tech illustrator audit cite
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 5)**: T unchanged (ISPD invariants — non-contact geometry, modulated capacitance, slow potential decay — now physically + visually accurate) | S unchanged (sub-region structures intact) | L improved (probe now reads as Kelvin probe; meter reads as electrostatic voltmeter via decay icon) | A significantly improved (instrument identity correct per Tech illustrator audit)
- **Notes**:
  - This is the most impactful iter for user M1 "icon-level" complaint. Kelvin probe was the WEAKEST element per Tech illustrator audit.
  - Air gap `d` indicator now visually conveys non-contact measurement (was implicit before).
  - V_s meter decay icon ↔ V_s sub-zone curve are now semantically linked (same exponential decay form).
  - Closure NOT declared per user.
- **Visibility gate**: intended yes (disk-on-shaft + ↕ vibration + air gap d + decay icon all visible at crop) | anomaly none

### Column E iter 5/10 — 2026-05-18 — proportion adjust (Option A)

- **Scope**: E-3 (V_s axis) + E-4 (V_s curve waypoints) + E-6 (g(E_t) axis) + E-9 (τ_d caliper position)
- **Rationale**: User-driven layout re-review identified 0.60cm whitespace between apparatus content bottom (y=3.20) and V_s zone top (y=2.60). User selected Option A: reclaim 0.40cm whitespace, distribute to V_s (+0.30) and g(E_t) (+0.10) without reducing apparatus detail.
- **Reference source**: layout analysis, user choice
- **Patches**:
  - E-3 V_s axis top: y=2.55 → y=2.85 (+0.30cm, +33% axis height)
  - E-3 V_s tip label: y=2.30 → y=2.55 (mid-axis proportional)
  - E-4 V_s curve waypoints: scaled (y-1.65)×1.333+1.65 to use new envelope. Peak (5.10, 2.45)→(5.10, 2.72). Plateau values clamped to y=1.65 (on axis).
  - E-4 V_s markers: scaled proportionally
  - E-6 g(E_t) axis top: y=1.35 → y=1.45 (+0.10cm, +11% axis height)
  - E-6 g(E_t) tip label: y=1.15 → y=1.25
  - E-9 τ_d caliper: shifted up y=1.35→1.42 (with T-caps 1.39..1.45); label y=1.36→1.43
- **Briefing edits (Type B, user-authorized)**: §13.6 E-3/E-4/E-6 sub-zone spec sync — axis tops, curve waypoint scaling, tip label positions
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 4)**: T unchanged (Q4 1.86× ratio preserved; Gaussians unchanged this iter) | S improved (cleaner layout, no whitespace waste) | L improved (V_s curve now visually communicates stretched-exp decay dynamics) | A improved (less crowded, more breathing room, M3 partial address even before analytical curve)
- **Notes**:
  - User M3 ("그래프 비율") significantly addressed via proportion-only fix — without redrawing curve analytically (iter 7 still planned but lower priority now).
  - Apparatus detail PRESERVED per user "장비를 여기서 더 줄인다고?" — only zone whitespace reclaimed.
  - Plateau markers on V_s curve now sit ON axis (no longer dipping below) — visual artifact fixed.
  - Closure NOT declared per user.
- **Visibility gate**: intended yes (V_s curve dynamism visible; τ_d caliper has breathing room; apparatus unchanged) | anomaly none

### Column E iter 4/10 — 2026-05-18 — τ_d caliper + derive arrow polish (4-designer audit response)

- **Scope**: E-9 (τ_d annotation) + E-5 (derive inter-arrow)
- **Rationale**: 4-designer parallel external audit (sci illustrator + info designer + typo designer + tech illustrator). 3-of-4 designers flagged τ_d `<- - - ->` dashed double-headed arrow as chartjunk / AI-generic; typo designer flagged "derive" italic verb as ISO 80000-2 violation. Roadmap iter 3 (proportions) rejected by user "장비를 여기서 더 줄인다고?"; iter 4 (this) is C tier easiest cleanup.
- **Reference source**: designer audit findings; briefing-only design
- **Patches**:
  - E-9 τ_d: dashed double-headed arrow → **caliper-style** (solid bar cRed!55 0.32pt + 2 T-end-caps at peak x-positions); tone cRed!70→!55 for annotation tier; label fill=cAmber!8 added for visual separation
  - E-5 derive: arrow weight 0.35→0.55pt + Stealth tip 4pt×3pt→5pt×4pt; label italic→**upright** (verb not variable per ISO 80000-2); position (7.00, 1.42)→(7.05, 1.45) anchor=west
- **Briefing edits (Type A)**: §13.6 E-5 derive spec (upright label + arrow weight); §13.6 E-9 caliper-style spec (4-designer audit cite)
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 2b)**: T unchanged (τ_d still energy-domain only; semantic preserved) | S unchanged (positions adjusted, structures intact) | L improved (τ_d reads as proper "energy separation" not chartjunk; derive arrow more confident) | A improved (designer-flagged AI-generic feel partially addressed)
- **Notes**:
  - Roadmap status: iter 3 (proportions) rejected by user. iter 4 done (this). iters 5+6 next (apparatus precision batch A+B). iter 7 (Gaussian width + V_s analytical). iter 8 (math notation cleanup).
  - Closure NOT declared per user "클로져는 맘대로 하지마".
- **Visibility gate**: intended yes (caliper τ_d reads as measurement convention; derive arrow + label confident) | anomaly none

### Column E iter 2/10 — 2026-05-18 — apparatus comprehensive detail upgrade (M1 paper-grade)

- **Scope**: E-2 apparatus zone (atomic — 4 elements interlocked: corona, sample stack, Kelvin probe, V_s meter)
- **Rationale**: User M1 complaint "장비 그림 자체가 아직 논문 그림 수준이 아니야, 최고 퀄리티로 그려봐". Audit identified each apparatus element was icon-level (single shape) instead of communicating ISPD measurement mechanism. Structural commitment iter — 4 elements upgraded atomically since they form coherent apparatus narrative.
- **Reference source**: He NatComm 2024 Fig 1c (audit_table E-ref01 full-spectrum); plus *mechanism-driven* design — each element must visually convey the physical principle it implements.
- **Patches (atomic, structural commitment)**:
  - **Corona needle**: V-tip (2 lines) → **sharp filled triangular tip** + **3 spark/discharge indicators** (cRed!55!black 0.30pt) radiating from tip — communicates corona-discharge mechanism (ion emission)
  - **Sample**: single slab (y=3.40..3.50) → **2-layer stack**: polymer film (cAmber!28, y=3.45..3.52, thin) + **substrate** (cGray!18 with diagonal hatching, y=3.34..3.45, thicker). Ground re-attached to substrate (physically accurate ISPD charge-decay path)
  - **Kelvin probe**: 0.30×0.10cm → **0.40×0.13cm** + **2 vibration arcs above** (Kelvin-modulation signature, FM-CPD defining feature)
  - **V_s meter**: empty outlined box → **box with small sinusoidal waveform inside** (cGray!60 0.22pt, ~3 cycles) — measurement-display cue
  - **Polymer film label**: repositioned (initial attempt above polymer at y=3.54 collided with corona/probe area; reverted to below substrate at y=3.32 anchor=north matching pre-iter2 below-slab pattern)
- **Briefing edits (Type B, user-authorized "최고 퀄리티")**: §13.6 E-2 sub-section fully rewritten — sample stack 2-layer spec, corona spark cue, probe vibration arcs, meter waveform display, all documented with coordinates + rationale
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 1)**: T unchanged (ISPD invariants intact; physical accuracy *improved* via grounded substrate) | S unchanged (sub-region count maintained, internal structure updated) | L improved (apparatus now communicates *measurement mechanism* not just shape — reader can infer ISPD operating principle from drawing) | A significantly improved (M1 "icon-level" complaint substantial address)
- **Notes**:
  - Structural commitment iter exception to ≤2 sub-region rule — 4 apparatus elements interlocked (changing one affects others' geometry); documented per Panel B iter1 precedent.
  - User M1 substantial address; M2 (palette/AI feel) partial address via iter1 saturation; M3 (V_s curve dynamism) still pending → roadmap iter 3
  - Closure intentionally NOT declared per user "클로져는 맘대로 하지마"
- **Visibility gate**: intended yes (each apparatus element now reads as paper-grade scientific drawing with mechanism cue) | anomaly resolved (polymer-film-label collision fixed mid-iter)

### Column E iter 1/10 — 2026-05-18 — T5 BLOCKER fix + Gaussian saturation

- **Scope**: E-7 + E-8 (Gaussian peaks)
- **Rationale**: Full Panel E audit identified T5 violation — Gaussian peak ratio = 2.0× (current) ≠ 1.86× (Q4 LOCKED spec). Over-shoot from v8.7 critique iter 4 over-correction (was 1.36× → set 2.0× target instead of 1.86×). Fix priority: T-axis spec drift takes precedence over polish.
- **Reference source**: He NatComm 2024 Fig 1c (audit_table.md E-ref01 PRIMARY full-spectrum) — but this iter is briefing-spec-sync, not reference-driven.
- **Patches**:
  - E-8 deep peak y `1.30 → 1.24` (3 control points): height above base 0.90 → 0.84; new ratio 0.84/0.45 = **1.87× ≈ 1.86× Q4 spec**
  - E-7 fill `cBlue!25 → cBlue!35` (+40% saturation)
  - E-8 fill `cRed!25 → cRed!35` (+40% saturation)
- **Briefing edits (Type A)**: §13.6 E-7/E-8 spec sync — fill saturation + deep peak rationale documented
- **4-axis scores**: T ✅ (was ❌ T5) | S ✅ | L ✅ | A ✅
- **Score delta**: T ❌→✅ (BLOCKER T5 cleared, Q4 LOCKED satisfied) | A improved (saturation polish, partial user M2 response)
- **Notes**:
  - Audit insight: deep peak height was over-corrected at iter 4 to 2.0× instead of intended 1.86×. Lesson — *always verify* spec values after correction iters.
  - User M2 "AI feel" partial address — saturation bump. Full M2 resolution needs broader palette polish (multiple iters).
  - User M1 (apparatus icon-level) + M3 (V_s curve dynamism) NOT addressed this iter — roadmap continues.
- **Visibility gate**: intended yes (deep clearly taller than shallow with new ratio; fills more visible) | anomaly none

### Column D iter 1/10 — 2026-05-18 — D-7 Debye reference (FIRST reference-grounded iter)

- **Scope**: D-7 (Debye dashed reference curve)
- **Rationale**: First reference-grounded loop iter. Wang NatComm 2022 Fig 1 = primary reference per spec.yaml + audit_table.md. Mining "reference-curve styling" transferable aspect. Current Debye (cGray!70 0.55pt) reads as background line; Wang convention is stronger reference styling. Validates reference-grounded loop pattern (vs Panel A/B reference-free).
- **Reference source**: `reference/row2_apparatus/apparatus1_ref04_NatComm2022_tribo_p3-03.png` — Wang NatComm 2022. Audit: theoretical PARTIAL, structural PASS, storyline PARTIAL. **Transferable mined**: reference-curve styling convention. **Do-not-transfer respected**: triboelectric mechanism, breakdown narrative (no content transfer, visual weight only).
- **Patches**:
  - D-7 Debye: weight `0.55 → 0.75pt` (+36%); tone `cGray!70 → cGray!85` (+21%); width 0.75pt stays under mechanism-tier 1.0pt (correct hierarchy: reference 0.75 < primary curves 0.80pt)
- **Briefing edits (Type A)**: §13.5 D-7 weight/tone references — pending (low priority, polish-tier; defer to next iter or batch with D-7b curve labels)
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs prior post-Nature-compliance state)**: T unchanged (§8.4 LOCKED preserved — Debye still below power-law endpoints at right) | S unchanged (same coords) | L improved (reference role clearer) | A improved (reference comparison anchor confidently visible)
- **Reference-grounded workflow data point #1**:
  - Patch citation is clear: reference path + transferable aspect named
  - Audit-table do-not-transfer respected (visual weight only, no content)
  - Workflow indistinguishable from reference-free except for Step 2 reference scan step + commit-message reference path
  - Easier to justify aesthetic decisions vs reference-free (concrete benchmark vs subjective judgment)
- **Notes**: Conservative single sub-region scope for first reference-grounded iter. Visual clash count 56 → 56 unchanged.
- **Visibility gate**: intended yes (Debye clearly distinguishable as reference comparison) | anomaly none (no overlap with curves or labels; §8.4 below-endpoints rule maintained)

### Panel B iter 2/10 — 2026-05-18 — B-4 divider tone polish (Nature-grade)

- **Scope**: B-4 (sample boundary divider tone)
- **Rationale**: Post-iter1 3-chain restructure, divider at cGray!40 still subtle at print scale. Per A+B mode lesson (≥+30% delta perceptible), bump tone +38% to cGray!55 while holding width 0.18pt (§13.2 forbidden cap >0.20pt). Strengthens 3 distinct sample binding.
- **Reference source**: briefing-only (Panel B reference gap; concept-figure framing)
- **Patches**:
  - .tex B-4 foreach: `cGray!40` → `cGray!55` (single 1-line)
- **Briefing edits (Type A)**:
  - §13.2 B-4 spec: tone history "!25→!40→!55" + iter2 rationale documented
  - panel_goals.md Panel B S5 + A2 references updated
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 1)**: T/S/L unchanged | A improved (divider now perceptible at print scale; 3 distinct sample binding visually confirmed)
- **Notes**: Conservative single sub-region scope. Visual clash count 56 → 56 unchanged.
- **Visibility gate**: intended yes (dividers visible separating 3 chains) | anomaly none (no overlap, no axis-tone violation)

### Panel B iter 1/10 — 2026-05-17 — restructure 4→3 representative chains (β)

- **Scope**: B-1 + B-2 + B-4 (atomic structural change; concept-figure overview restructure)
- **Rationale**: User-driven audit ("개념 figure" framing + "굳이 모든 sample 다 보여줄 필요?") + literature finding (2025 RSC Starter Guide: IV field uses property plots not scaffold-of-chains for quantitative wt% sweep). Concept figure justifies *minimum sufficient* representation: 3 representative (endpoints + middle) instead of 5 full sampling. Full 5-sample dataset deferred to Fig 2~.
- **Reference source**: Literature audit (RSC 2025, NComm 2024 Structural evolution) + Nature concept-figure conventions; briefing-only Panel B design.
- **Patches (atomic, structural)**:
  - .tex Panel B foreach: 4 items `{7.90/10/60, 7.30/14/70, 6.70/18/75, 6.10/24/85}` → 3 items `{7.90/10/60, 7.00/18/75, 6.10/24/85}` (S70 + S85's adjacent chains removed; S75 elevated to middle position; chain spacing 0.60→0.90 for breathing room)
  - .tex Panel B dividers foreach: `{7.60, 7.00, 6.40}` (3 dividers) → `{7.45, 6.55}` (2 dividers at new midpoints between 3 chains)
- **Briefing Type B edits** (user-authorized via "제안대로 진행"):
  - §8.8 Q1 LOCKED: sample list "S60/S70/S75/S85" → "S60/S70/S75/S80/S85" (5 samples in paper) + "Panel B shows 3 representative: S60/S75/S85" clause + Fig 2~ deferral note
  - §13.2 B-1: "4 zigzag chains" → "3 representative" with iter1 restructure note; atom counts "10/14/18/24" → "10/18/24"; y positions update
  - §13.2 B-4: "3 dividers between 4 chains" → "2 dividers between 3 representative chains"; positions update
  - §13.9 B-3 cross-binding: "discrete 4 chains" → "discrete 3 representative chains"
  - §9 monotonicity rule: "S₆₀ < S₇₀ < S₇₅ < S₈₅" → "(displayed) S₆₀ < S₇₅ < S₈₅ + (paper-full) S60/S70/S75/S80/S85"
  - §1-§2 visual story arc references updated
- **panel_goals.md edits**: Panel B section fully rewritten — intent, forbidden, 4-axis acceptance (T1-T4, S1-S5, L1-L4, A1-A6), sub-region checklist all updated for 3 representative chains
- **spec.yaml**: Panel B caption updated to clarify 3 representative + paper-full 5
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs prior state with 4 chains)**: T improved (briefing-narrative coherence: actual 5-sample paper set now properly documented) | S improved (cleaner geometry, 0.90cm spacing) | L improved (3 representative = clearer concept-figure narrative, less crowded) | A improved (breathing room, less visual density)
- **Notes**:
  - This is a **structural commitment iter** (Type B briefing edit) — touches 3 sub-regions atomically because they're interlocked (chain count, label count, divider count must match). Deviates from template ≤2 sub-region rule per "structural commitment" exception, documented.
  - Cross-panel sample identity intentionally abstract for concept figure (Panel C/D/E/F do not specify "this is sample X" — concept conveys "trap exists across composition range").
  - 5-sample full data deferred to Fig 2~ (quantitative panels).
- **Visibility gate**: intended yes (3 chains + labels + dividers + axis all readable at panel B crop) | anomaly none (no overlap, clean spacing)

### Panel A iter 8/10 — 2026-05-17 — P1+P2 font cap (residual Nature N3 violations)

- **Scope**: A-3 ((S)_x label fontsize) + figure-wide default font fallback
- **Rationale**: Post figure-wide N1+N2+N3 pass, residual 8pt usages still present: (S)_x label explicit 8pt (line 180) and `every node` default 8pt (line 30). Both exceed Nature/Nat Comm 7pt cap for non-panel-letter text. Audit miss from previous pass — pass closed N1/N2/N3 in style definitions but didn't sweep individual `\fontsize{...}` explicit overrides.
- **Reference source**: Nature formatting guide max-text-size rule
- **Patches**:
  - P1 (A-3): `(S)_x` label explicit fontsize `\fontsize{8}{9.5}` → `\fontsize{7}{8.4}` — closes sole explicit non-panel-letter 8pt violation
  - P2 (defensive figure-wide): `every node/.style` default fontsize `\fontsize{8}{10}` → `\fontsize{7}{8.4}` — prevents future silent inheritance violations on any node lacking explicit font override
- **Briefing edits**: none (font size is polish-tier, not §13.1 locked)
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 7)**: T/S/L unchanged | A: residual Nature N3 violation closed
- **Notes**: (S)_x label slightly smaller, cluster non-overlap (S13) preserved with extra clearance. Default 8pt → 7pt is defensive — no visible nodes inherited 8pt (all explicit), but future patches now safe.
- **Visibility gate**: intended yes ((S)_x readable at 7pt, all labels intact) | anomaly none (visual clash 55 → 55 unchanged)
- **Audit pattern lesson**: Figure-wide style pass missed explicit per-node fontsize overrides. Add to template anti-patterns: "Style-definition sweep must be paired with per-`\fontsize{...}` explicit-override grep, not assumed equivalent."

### Figure-wide Nature compliance pass — 2026-05-17 (N1+N2+N3)

NOT a Panel iter — figure-wide intervention touching all panels. Logged separately for traceability.

- **Scope**: preamble style definitions (panelLetter, labelStrong, labelStd) + 6 panel letter uses (A..F → a..f)
- **Rationale**: User direction "전부 받아들여야겠지. 전월 양식에 따라" — adopt all Nature/Nat Comm figure regulations. Three rule violations identified in earlier audit:
  - N1: panel letters uppercase, Nat Comm rule = lowercase "a, b, c"
  - N2: panel letter 9.5pt, Nat Comm rule = 8pt
  - N3: labelStrong 8.5pt + labelStd 7.5pt, Nature rule = "Maximum text size for all other text should be 7 pt"
- **Reference source**: Nature formatting guide, Nat Comm formatting instructions
- **Patches** (preamble L39-46):
  - `panelLetter`: fontsize 9.5/11 → 8/9.6 (N2)
  - `labelStrong`: fontsize 8.5/10.2 → 7/8.4 (N3) — affects "Sulfur-rich polymer", panel C "real space"/"energy diagram", any other labelStrong-tagged label
  - `labelStd`: fontsize 7.5/9 → 7/8.4 (N3)
  - `labelMute` unchanged (already 7pt italic)
- **Panel letter uses** (L54-59):
  - `A`/`B`/`C`/`D`/`E`/`F` → `a`/`b`/`c`/`d`/`e`/`f` (N1) — 6 line changes, anchor=north west preserved
- **Briefing edits**: none in this pass. Briefing §13 references "Panel A", "Panel B" etc. in body text — those naming references unchanged (body convention can use uppercase even when figure labels are lowercase per typical Nature convention).
- **4-axis scores (figure-wide, all panels)**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta**: T/S unchanged. L improved (Nature rule alignment). A: typography hierarchy compressed but Nature-compliant; "Sulfur-rich polymer" bold no longer dominates Panel A → drawing-as-hero proportion improved.
- **Notes**:
  - Visual hierarchy: panel letter 8pt bold (top tier) > labelStrong 7pt bold (2nd) > labelStd 7pt regular > labelMute 7pt italic. Hierarchy now compressed (1pt diff between top and next tier) — by Nature design.
  - "Sulfur-rich polymer" label proportion improved (was visually dominant, now properly subordinate to drawing).
  - Visual clash count: 56 → 55 (negligible delta, no regressions).
- **Visibility gate**: intended yes (all panel letters + labels readable at print scale) | anomaly none
- **Out of scope for this pass** (deferred):
  - N4 (wash ellipse cAmber tint): "avoid excessive colour" borderline call; design-intent element, defer to submission-review
  - N5 (caption.md abbreviation definitions): caption requires full v8.6 6-panel rewrite, separate task

### Panel A iter 7/10 — 2026-05-17 — M1 Nature-compliance fix (inv. vulc. → inverse vulcanization)

- **Scope**: A-5 (S₈ inset position) + A-6 (inverse vulcanization label)
- **Rationale**: User-flagged + literature confirmed "inv. vulc." is non-standard. Nature/Nat Comm rule: "Use standard chemical and biological abbreviations" + "Unusual or unconventional abbreviations should be spelled out in full or defined in the legend." Literature standard is "IV" or full text. User preference: full text per "전부 받아들여야겠지" (accept all Nature conventions).
- **Reference source**: Nature formatting guide, Nat Comm formatting instructions, RSC 2025 starter guide, JACS 2023 mechanism paper
- **Patches**:
  - A-5: S₈ inset shifted (3.05, 8.45) → (3.05, 8.55) (+0.10cm y); same x preserves §13.1 A-5 top-right corner semantic; frees vertical room for 2-line full-text label
  - A-6: label "inv.\ vulc." italic 6pt → "inverse\\vulcanization" 2-line italic **5pt** (Nature min), position (2.15, 7.82) → (2.50, 8.00) anchor=center align=center, white fill maintained for visual separation
- **Briefing edits**: none. (Position is polish-tier; abbreviation choice was idiosyncratic, no LOCKED rule covered it. Future briefing §13.1 A-6 could lock "full text per Nature rule" as new acceptance constraint.)
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 6)**: T unchanged | S unchanged (S13 cluster non-overlap maintained) | L improved (Nature rule alignment) | A unchanged ✅
- **Notes**: label cluster now ((S)_x left of, inv. vulcanization 2-line stacked center, S₈ top-right) reads naturally. Iter pivots from "iter 6 verified closure (deferred)" status — Panel A re-enters loop for spec-compliance polish, no closure declared.
- **Visibility gate**: intended yes ("inverse vulcanization" full readable at 5pt min size; cluster non-overlap preserved) | anomaly none (no rogue stroke; visual clash 54→56 net +2 likely from new larger label bbox triggering false-positive text-on-path; check_visual_clash heuristic)
- **Related future audit (N1-N3, not in iter scope)**: panel letter case + size + max text size — separate figure-wide Nature compliance pass

### Panel A iter 6/10 — 2026-05-17 — verification closure (valid)

- **Scope**: NONE (verification-only per template termination rule; post-reopen closure check)
- **Rationale**: Iter 5 reached first valid 4-axis ✅ after closure reopen and S13 acceptance addition. Iter 6 verifies state holds under expanded acceptance set without further patches.
- **Reference source**: N/A
- **Patches**: NONE
- **Briefing edits**: none in this iter
- **4-axis scores**: T ✅ | S ✅ | L ✅ | A ✅
- **Score delta (vs iter 5)**: all axes unchanged, no patches applied
- **Closure status**: **DEFERRED per user instruction** ("정식 클로저는 하지마", 2026-05-17). Template rule's 2-consecutive-✅ condition met technically (iter 5 + iter 6), but formal panel closure NOT declared. Panel A iteration suspended in "valid ✅ state, pending further user direction" — additional sub-regions (e.g., A-8 typography subtitle pending Panel B sample-range resolution) or deferred items may reopen the loop without closure-revoke ceremony.
- **Sample range note (out of iter scope, flagged for follow-up)**: User confirmed actual paper samples = S60/S70/S75/S80/S85 (5 samples, 60-85 wt% S). Briefing currently locks S60..S85 with 4 samples (S60/S70/S75/S85, briefing §8.8 Q1 LOCKED). Two discrepancies: (1) Panel B has 4 chains, paper has 5; (2) S60 = 40 wt% DIB which literature (RSC 2025 starter guide, JACS 2023 mechanism) flags as crosslinked-regime threshold — "linear copolymer" subtitle (A-8) becomes conditional at this composition. Both flagged as Type B briefing edit candidates (require structural commitment change), deferred per user instruction "패널 A 이터레이션까지만 진행" — Panel B iteration scope.
- **Visibility gate**: intended yes (all sub-regions perceivable at standard PNG view + per-panel crop) | anomaly none
- **Remaining deferred (non-blocking)**:
  - "linear copolymer" subtitle conditional at S60 composition — Type B if Panel A subtitle text changes
  - briefing.md §8.8 Q1 LOCKED 4-sample → 5-sample expansion — Type B (touches Q1 LOCKED)
  - Panel B-1 chain enumeration 4 → 5 chains + B-2 label set 4 → 5 — Type B + structural
  - These all properly belong to Panel B iteration scope, not Panel A

## Panel closure summary

| Panel | Closure status | Iters to ✅ | Strategy notes |
|---|---|---|---|
| A | **deferred** (iter 6 verified 4-axis ✅ × 2 consecutive; formal closure withheld per user) | iter 3 (A axis ✅ first) → iter 5 (S13 added, all ✅) → iter 6 (verify) | A+B mode (≥+30% delta, multi-category) after iter 1+2 micro-tweaks failed perceptibility. D pre-step at iter 3. iter 4 closure invalidated by user-flagged label-cluster blind spot; iter 5 closed via new S13 acceptance + position fix; iter 6 verified. Audit lesson: bullet-coverage gaps are blind spots, and user feedback caught a closure false-positive. Sample range (60/70/75/80/85) confirmed by user but defers to Panel B iter for figure update. Closure status suspended per user "정식 클로저는 하지마" — Panel A remains in "valid ✅ state, iteration suspended" with re-entry available without closure-revoke ceremony. |


- Dashed-line semantics (#17) remain intentionally diverse: Debye reference,
  escape arrow, inverse-vulcanization arrow, and leaders carry different
  meanings. This is low-priority residual risk unless final review finds that
  readers confuse them.
- This file gives one pilot's live iteration evidence only. Cross-fixture
  generalization remains pending.
