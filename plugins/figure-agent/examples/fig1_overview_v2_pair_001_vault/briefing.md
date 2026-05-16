# Briefing — fig1_overview_v2_pair_001_vault

> **Genre**: Cover / graphical abstract scene via M2 (per-panel cartoon-ize) implementation route.
> **Pilot pair**: `fig1_overview_v2_pair_001` / **Arm**: vault
> **Design snapshot SHA**: `fa7a6d9ff7890a440ca3471995acf8145c47001a996dbd8bf2c428b363d8f7b7`
> **Vault query**: 966e2e89-5c8a-41ea-a11f-658c99c3d037 (approved_only, proposed_records_allowed=false)
> **Vault state**: degraded_mode=true — chroma_v2 absent (text/image/scaffold/style branch indexes all absent)

---

## §1. Figure 정체성 + 30초 viewer impression

**정체성**: Cover-figure / graphical abstract scene. Result-table 또는 plot-grid 인상은 anti-goal. 측정 결과 plot은 *iconic cartoon*으로 압축되고, schematic-illustration이 시각 무게의 다수를 차지.

**30-second message**: *"황 풍부 폴리머에 deep charge trap이 존재하고, 3 lines of evidence가 모두 같은 trap을 가리키며, 거시적 bending으로 발현된다."*

**5-second impression**:
- 처음 눈에 들어오는 것 = Panel C HERO (Row 1 우측, 1.5× 폭, deep red saturation 최강)
- 두 번째 = Row 1 전체가 *연속 scene* (A → B → C 좌→우 흐름)
- 세 번째 = Row 2 = 3 spoke로 발산하는 *evidence radiation* (분리된 plot 4개가 아닌 *1 통합 scene*)

**Anti-goal**:
- 4-panel axis-frame plot grid feel
- "Fig 2/3 in disguise" — 정량 데이터 plot tone
- 결과 나열식 (briefing v2.3까지 .tex의 인상)

---

## §2. Visual story arc (frame-by-frame eye-flow)

| Frame | Element | Dwell | Purpose |
|---|---|---|---|
| 1 | Row 1 좌측 entry (Panel A) | 1s | 재료 식별 |
| 2 | A → B 좌→우 horizontal flow | 1s | 분자 heterogeneity |
| 3 | B → C HERO transition | 1s | trap landscape entry |
| 4 | Panel C dwell | **5s** | hero focal — deep + shallow trap + energy diagram |
| 5 | C → Row 2 vertical transition + caption | 1s | "convergent evidence" semantic gate |
| 6 | Row 2 3-spoke branching | 2s | 3 lines fan-out (kinetic / ISPD / mechanical) |
| 7 | Row 2 holistic scan | 3s | "다 같은 trap 본다" 통합 인상 |

Total ~14s for full read. Panel C dwell = single longest stop.

---

## §3. Plot-vs-schematic balance (Row 2 cover-feel mechanism)

- **Plot panel (D / E / F)**: *iconic cartoon*.
  - Axis frame **제거** (axis arrow + minimal label만)
  - Tick 수치 **없음** (Fig 3 영역 침범 회피)
  - Curve shape 자체가 message
  - Plot이 *icon-sized*: reader가 *plot처럼 분석*하지 않게
- **Schematic panel (A / C / G)**: scene dominant. Detail density 비례적으로 높음.
- **B**: hybrid. Skeletal chains with conceptual axis arrow (axis frame 없음).

**Row 2 cover-binding mechanism (M2 baseline + P-A branching)**:
1. Shared faded polymer matrix background underneath Row 2 4 panel (cAmber!8 tint with subtle chain hint, opacity ~0.15) — 4 panel을 시각적으로 1 scene으로 묶음.
2. No hard panel borders Row 2 — visual continuity.
3. *3-spoke branching arrow from C → {D, E↔F, G}* with modality labels (§4).

P-B (isometric on D/E/F) + P-C (silhouette inset on Row 2 panels)는 **거절** (§9).

---

## §4. Row 2 branching arrow + label semantics

- **Geometry**: Panel C 하단 single arrow가 Row 2 entry transition zone (above D/E/F/G, between rows)에서 3 spoke로 발산.
  - Spoke 1: C → D (kinetic)
  - Spoke 2: C → E ↔ F 묶음 (ISPD, paired)
  - Spoke 3: C → G (mechanical)
- **Spoke labels**: 각 spoke 옆에 modality 단어 (*"kinetic"* / *"ISPD"* / *"mechanical"*) — italic, modest size, cGray.
- **Caption label**: Row 2 위쪽 transition zone에 *"convergent evidence — three independent probes of the same trap"* — italic, cGray, 가운데 정렬. 정확한 좌표 + 폰트 사이즈는 design.md / `.tex` 영역.
- **Semantic discipline**: 화살표는 divergent geometry; "convergent" 의미는 caption + Panel C ↔ F color-matching이 carry. Reader는 2초 안에 *"3 lines → 1 trap"*을 읽어야.
- **Anti-goal**: 화살표가 D→E→F→G 또는 G→F→E→D로 *linear chain*으로 읽히는 것 (causation misleading; §8 physics invariant 8.7).

---

## §5. Hero hierarchy mechanism (시각적, NOT semantic)

| 메커니즘 | Panel C | Row 2 plot (D/E/F) | Row 2 schematic (G) |
|---|---|---|---|
| 면적 | 1.5× width | equal | equal |
| Color saturation | deep-red strong + shallow-blue strong | mid | mid + isometric tone |
| Detail density | maximum (LEFT polymer + RIGHT band + ⊖ markers + leaders + escape arrows) | minimal (axis arrow + 1-2 curve + 1 label) | medium (cantilever + ⊖ + air gap + Coulomb arrow) |
| Position | Row 1 우측 dominant | Row 2 equal | Row 2 equal |

Result: Panel C *시각적 hero*; Row 2는 *evidence radiation*으로 평등 분포. Row 2 내부 hero 위계 없음 (3 lines는 평등).

---

## §6. Per-panel ROLE (NOT current implementation snapshot — see §7)

| Panel | Narrative role | Aesthetic register |
|---|---|---|
| A | 재료 identity — poly(S-r-DIB) primary microstructure | schematic (chemistry) |
| B | 분자 heterogeneity — variable polysulfide chain length | hybrid (skeletal + conceptual axis) |
| C | **HERO #1** — trap landscape (LEFT real-space + RIGHT energy diagram) | schematic dominant (scene) |
| D | Kinetic evidence icon — I(t) ~ t⁻ⁿ shape | iconic cartoon |
| E | ISPD raw V_s decay icon | iconic cartoon |
| F | ISPD-derived g(E_t) bimodal icon | iconic cartoon |
| G | Mechanical evidence scene — Coulomb-driven bending | schematic (isometric scene) |

E ↔ F는 *paired ISPD transformation*으로 묶음 — single spoke from C, paired short-arrow internal.

---

## §7. Current .tex state vs design target — TRANSITIONAL

이 brief는 **design target**. 현재 .tex는 *전 단계 — divergence는 의도된 transitional state*. Row 2 redesign은 별도 task (#35).

| Layer | Current .tex | Brief target | Gap |
|---|---|---|---|
| Row 1 (A / B / C) | mostly aligned (Panel C 1.5×, color, hero saturation) | aligned | same; 잔여 polish (§12.1 Panel C LEFT SVG handoff) |
| Row 2 layout | 4-panel axis-framed plot boxes | M2: axis frame 제거, shared faded polymer background, no panel borders | **divergent — redesign needed** |
| Row 2 arrow | single vertical Stealth + "convergent evidence" label | 3-spoke branching from C + spoke modality labels + Row 2 caption | **divergent — redesign needed** |
| Panel C LEFT polymer sample | TikZ R22 (rectangular sheet, medium-limit hit) | Inkscape SVG handoff | parallel deferred (§12.1) |

Brief가 future state 기록. `.tex`가 따라잡기 전까지 두 source는 의도적으로 divergent.

---

## §8. Physics invariants (LOCKED, 기존 v2.3 §4 유지 + branching arrow physics constraint 추가)

8.1 Deep traps = **lower energy** (deeper wells); shallow traps = higher energy.
8.2 Color convention: **shallow = blue, deep = red.** Consistent across Panel C, F, G.
8.3 Panel C representation: **hybrid split-half**. LEFT = polymer matrix with mixed-depth ⊖ sites (NOT spatially segregated — same polymer contains both kinds). RIGHT = trap-level energy diagram with E_C / mobility edge / E_V references + shallow + deep horizontal trap-level structures + escape arrows + ΔE_t^d depth annotation. Dashed gray leaders bind LEFT sites to RIGHT energy levels.
8.4 Power-law I(t) ~ t⁻ⁿ lies **above Debye reference** at long times (non-Debye tail). Cannot be below.
8.5 Panel G: **only Coulomb repulsion** arrow (red, polymer → away from electrode). Maxwell attraction arrow **forbidden** (design.md v2.2 §2.3). Cantilever clip on **TOP**, polymer hanging down.
8.6 Panel C ↔ Panel F color-consistent (bimodal: blue Shallow / red Deep).
8.7 **Branching arrow physics constraint**: 3 spoke from C **must** match the 3 evidence lines in design.md §3.2 (kinetic / ISPD / mechanical). No new evidence line, no missing line. Spoke 순서 + label은 measurement modality, NOT causation chain — physics는 *3 independent measurements of same trap*, *not* causation chain D→...→G.
8.8 Composition labels (S60 / S70 / S75 / S85)은 **Panel B에만** 허용. Row 2 plot panel은 concept-based only ("shallow-rich" / "deep-rich" / "low n" / "high n").

---

## §9. Forbidden (aesthetic side — NEW)

- **Plot grid feel** (4 panel axis-box equally spaced) — anti-goal of M2.
- **Axis frame** on D / E / F (axis arrow + minimal label만 허용).
- **Tick 수치 라벨** on Row 2 plot panel (Fig 3 영역 침범).
- **Composition-specific labels** (S60 / S85 등) on Row 2 plot panel.
- **Hard panel border** on Row 2 (M2 cover overlay).
- **More than 7 hues** total.
- **Drop shadow / gradient fill / texture / bevel** (gradient=data 예외만; M2 polymer background opacity는 단색 tint, gradient 아님).
- **Material-identity volume cue 예외**: 폴리머 schematic body 내부의 *explicit polymer-chain hint*는 texture 금지의 예외. cAmber-tone, **≤0.40 opacity, ≤0.40pt line width, ≤3 chains per region**. Semantic = polymer chain identity (Panel C LEFT thin film 기존 convention), NOT aesthetic decoration. 적용: Panel C LEFT 기존, Panel G cantilever (v5/F1 추가).
- **Light-source convention (figure-wide LOCKED)**: upper-left. 모든 gradient는 `top color=lighter, bottom color=darker` 또는 `left color=lighter, right color=darker`. Panel C LEFT (L278) = 기준 anchor; Panel G clip / polymer / electrode 동일 방향 유지.
- **Curved or dashed leader lines** (semantic violation — leaders = thin black straight 0.3-0.5pt).
- **P-A linear chain arrow** (D→E→F→G 또는 역) — causation chain implies, physics-misleading.
- **P-B isometric on D/E/F** — log-axis perspective skew, reader perception risk.
- **P-C silhouette inset on Row 2 panels** — Panel C와 redundant, noise.

---

## §10. Polish constraints (compressed)

10-paper convention checklist (post figure-research 2026-05-15): 16/20 items honored. Full corpus: `~/tmp/figure-refs-top-tier-fig1-overview-polish-20260515-153944/candidates.md`.

Residual items + active markers:
- **#3 Inter-panel gap deviation** — Row 1↔Row 2 branching arrow + 3 spoke + caption *intentionally inhabits the gap*. M2 cover-feel goal에 의도된 deviation. Branching 도입은 deviation을 *escalate*하지만 의도된 cost. Current decision; reopen only if cover-feel goal changes.
- **#7 Panel C band borders** 0.45-0.50pt vs convention 2.0pt — Row 2 redesign 시 함께 결정.
- **#17 Dashed line semantic** — currently 4 meanings (Debye / escape / inv. vulc. / leader). Consider consolidating to "reference / hypothetical" only at Row 2 redesign.
- **#18 Panel E open markers** vs convention filled — Row 2 redesign 시 axis frame 제거와 함께 결정.

Style discipline (full list at corpus):
- 3-tier line weight (mechanism 1.0–1.5pt / curve 0.8pt / reference 0.4pt)
- ≤7 hues, fills ~30% saturation / strokes ~90%
- Variables italic, units upright
- Sans-serif throughout (Helvetica/Arial family)
- One arrow tip style (Stealth)
- Hierarchy: panel-letter ~9.5pt > region-label ~8.5pt > axis-label ~7.5pt > tick-label ~7pt

---

## §11. Reference roles

- Reference image = **style anchor only** (line weight, palette, font family, layout proportion).
- design.md > reference (content authority — 충돌 시 design.md 우선).
- Vault references (§12.3) = grammar/style anchor only.

---

## §12. Deferred placeholders + Author intent

### §12.1 Deferred (Row 1, parallel to Row 2 redesign)

- **Panel C LEFT polymer-sample SVG handoff** — TikZ R22 (rectangular sheet)이 medium-limit hit ("PPT 수준"). Inkscape에서 sample drawing 별도 작업 후 `\includegraphics`로 integrate. Row 1 scope, Row 2 redesign과 parallel/independent.

### §12.2 Author intent (vault A/B test)

이 arm은 vault-grounded authoring (approved tikz-vault references as grammar/style anchors)이 no_vault arm의 error category를 surface or prevent하는지 test. 6 vault records used; remaining 6 returned but unused (rationale at §12.3 below).

### §12.3 Vault grammar anchors (selected_reference_ids)

**Panel A — sulfur polymer chemistry grammar:**
- `manual_seed_cho2024_fig1_s8_polymerization` (motif): S₈ ring-opening + DIB-linked polymerization grammar. TikZ libraries: arrows.meta, positioning, calc, shapes.geometric, decorations.pathmorphing. → `shapes.geometric` regular polygon for S₈ ring + linear DIB-polysulfide-DIB primary-microstructure grammar.
- `manual_seed_cho2024_fig1_dynamic_exchange` (annotation): dynamic polysulfide bond exchange grammar. → S₈ → DIB inverse-vulcanization transformation arrow. Do **not** reinterpret this as a 2D crosslinked network; Panel A is locked to linear poly(S-r-DIB) primary microstructure.

**Panel C — energy landscape + trap grammar:**
- `manual_seed_natcommun2024_fig1` (motif): energy-diagram + homogeneous matrix grammar. Tags: energy_diagram, multi_panel, phase_diagram, schematic. → shallow/deep trap visual hierarchy via depth-encoded amplitude (not just color).
- `manual_seed_cho2024_fig7_corona_charge` (annotation): corona charging + SRP/MXene charge retention grammar. → "localized trap" annotation idioms in sulfur polymer context.

**Cross-figure layout + typography:**
- `manual_seed_cho2024_fig2_mxene_percolation` (layout): multi-panel composite layout for SRP figures. → 2-row × 7-panel proportions.
- `manual_seed_cho2024_fig1` (typography, composite): inline-label typography hierarchy.

**Available but not selected (rationale):**
- `manual_seed_cho2024_fig6` + `manual_seed_cho2024_fig6_recycling_loop`: recycling-loop — out of scope for fig1 overview narrative.
- `manual_seed_cho2024_fig7` + `manual_seed_cho2024_fig2`: corona-discharge + MXene percolation composites — relevant but redundant with selected motif anchors.
- `github_5f38e6be4f18596c_01` + `github_8d009ec75f299a33_01`: MIT-licensed external multi-panel network references — rejected for Panel A because the chemistry decision is linear poly(S-r-DIB) primary microstructure.

---

## §13. Sub-region enumeration (iteration unit / dogfood design input)

**Frame**: per `docs/subregion-iteration-tool.md` §7 decision gate ("tool shape must come from observed iteration"), this enumeration lives in `briefing.md` as *text-form design input*, NOT in `spec.yaml` schema (subregions[] field does not exist yet). Each sub-region is an *iteration unit* — the smallest patch granularity for `feedback_element_iteration_workflow.md` 1-line-patch cycles.

**ID format**: `Panel-RegionLetter[+Index]` (e.g., `C-L1` = Panel C LEFT sub-region 1; `D-3` = Panel D sub-region 3).

### §13.1 Panel A — 8 sub-regions

- **A-1** 4 DIB benzene rings (high-low staggered horizontal row; ring R=0.26cm; 3 internal aromatic ticks each)
- **A-2** 3 internal polysulfide segments (linear DIB-polysulfide-DIB links between meta-position vertices, 120° apart; bivalent DIB chemistry constraint)
- **A-3** `(S)_x` parenthesis composition label (single floating, centered above row; ref01 Zheng 2024 NComm idiom)
- **A-4** `\methylPair` quaternary C(CH₃)₂ junctions (6 internal DIB-polysulfide sites; gem-dimethyl from isopropenyl→isopropyl)
- **A-5** S₈ ring inset (regular octagon polygon + 8 vertex 'S' atom letters + bold 'S₈' center label, top-right corner)
- **A-6** dashed inverse-vulcanization arrow (S₈ → Ring_c 60° vertex)
- **A-7** `cAmber!08` background wash ellipse (1.55×0.65cm hugging the row)
- **A-8** inline labels ('Sulfur-rich polymer' bold + 'poly(S-r-DIB) linear copolymer' subtitle + 'inv. vulc.' italic)

### §13.2 Panel B — 3 sub-regions

- **B-1** 4 zigzag skeletal chains (10/14/18/24 atoms; bond spacing 0.10cm, amplitude 0.08cm, atom r=0.025cm, bond w=0.5pt — R11 delicate)
- **B-2** S_n endpoint labels at terminal atoms (S₆₀ / S₇₀ / S₇₅ / S₈₅, cAmber!90 6.5pt; full 4-label set, design.md Q16 inconsistency flagged)
- **B-3** bottom horizontal axis arrow + 'Chain length, n' italic label

### §13.3 Panel C — 11 sub-regions

**LEFT half (real-space polymer, x=7.55..9.85):**
- **C-L1** rectangular polymer sheet (R22; 2.30×1.50cm; top→bottom amber gradient `cAmber!10` to `cAmber!38`) — medium-limit hit, SVG handoff deferred (§12.1)
- **C-L2** 3 wavy chain hints inside sheet (varied opacity 0.85/1.0/0.85; varied line weight 0.50/0.55/0.50pt)
- **C-L3** embedded ⊖ trap sites (3 sites mixed: ~1 shallow cBlue + ~2 deep cRed; coordinates at chain peaks/junctions)
- **C-L4** top-edge white highlight (opacity 0.55) + right-edge cAmber shadow (opacity 0.45) — depth cues
- **C-L5** 'poly(S-r-DIB) thin film' subtitle below sheet (italic 5.5pt cGray!70)

**RIGHT half (energy diagram, x=10.50..13.80):**
- **C-R1** E_C / mobility edge (dashed) / E_V reference horizontal lines + 'Energy' rotated label + vertical axis arrow at x=10.50
- **C-R2** shallow trap band (cBlue!75 border + cBlue!18 fill rounded rectangle, narrow y=7.38..7.60, contains 1 cBlue ⊖)
- **C-R3** deep trap band (cRed!75 border + cRed!18 fill rounded rectangle, taller y=5.75..6.30, contains 2 cRed ⊖)
- **C-R4** escape arrow from deep band → mobility edge (cRed!70 dashed 0.35pt; Boltzmann thermal release)
- **C-R5** ΔE_t^d depth annotation (cRed!75 double-headed arrow at x=13.55 spanning E_C → deep band bottom + label)
- **C-R6** 'shallow' / 'deep' band labels (bold 6.5pt sans, anchored east of each band)

### §13.4 Row 2 cover-binding — 3 sub-regions

- **Row2-BG** shared faded polymer matrix background (cAmber!8 rounded rectangle 14×4.55cm + 3 wavy cAmber!22 chain hints crossing horizontally) — §3 cover-binding mechanism #1
- **Row2-BR1** branching root + caption 'convergent evidence — three independent probes of the same trap' (italic 6.5pt cGray!75 above root at (7.00, 4.92))
- **Row2-BR2** 3 spokes from root to D/E↔F/G entry + modality labels ('kinetic' / 'ISPD' / 'mechanical' mid-spoke, italic 6pt)

### §13.5 Panel D — 5 sub-regions (iconic kinetic cartoon)

- **D-1** axis arrows Stealth-tipped (vertical log I + horizontal log t, cGray!65 0.50pt) + tip-end labels '$\log I$' / '$\log t$' — M2 no-frame
- **D-2** 2 power-law straight slopes (shallow-rich cBlue!80 + deep-rich cRed!80, 0.90pt)
- **D-3** Debye dashed reference curve (cGray!70 0.65pt, smooth bezier) + thin straight leader + 'Debye' label with white fill
- **D-4** main equation label '$I(t)\sim t^{-n}$' (top-left, labelStrong)
- **D-5** curve identification labels ('shallow-rich' cBlue!75 + 'deep-rich' cRed!75)

### §13.6 Panel E — 4 sub-regions (iconic ISPD-raw cartoon)

- **E-1** axis arrows Stealth-tipped + tip labels ('$V_s(t)$' rotated 90 + '$\log t$') — M2 no-frame
- **E-2** stretched-exponential decay curve (cRed!70 smooth, 0.80pt)
- **E-3** 6 open ISPD markers (circle, white fill, cRed!70 border, 1.4mm — open marker convention #18 candidate)
- **E-4** paired ISPD inter-arrow → F + 'ISPD' label (E↔F paired transformation per briefing §6)

### §13.7 Panel F — 5 sub-regions (iconic g(E_t) cartoon)

- **F-1** axis arrows Stealth-tipped + tip labels ('$g(E_t)$' top + '$E_t$' right) — M2 no-frame
- **F-2** shallow Gaussian (cBlue!85 border + cBlue!25 fill, smaller, x=7.45..8.95)
- **F-3** deep Gaussian (cRed!85 border + cRed!25 fill, taller 1.8× per Q4, x=8.95..10.15)
- **F-4** τ_d double-headed dashed arrow between peaks (cRed!70) + '$\tau_d$' label
- **F-5** 'Shallow' / 'Deep' base labels (cBlue!75 / cRed!75)

### §13.8 Panel G — 7 sub-regions (isometric mechanical scene)

- **G-1** clip rectangle (top, cGray!50 fill, 0.45×0.15cm) + thin stub
- **G-2** electrode block (left vertical, cGray!50!black fill, 0.35×3.30cm) + 'electrode' label below
- **G-3** polymer strip (hanging from clip, cAmber!30 fill + cAmber!75 outline 0.70pt, curved away from electrode = Coulomb repulsion manifestation)
- **G-4** 3 q_tr markers (cRed!75 circle ⊖ symbol, 1.6mm, inside polymer strip)
- **G-5** q_tr leader line + '$q_{tr}$' label (white fill, cRed!70)
- **G-6** Coulomb repulsion arrow (cRed!80 Stealth 0.7pt, polymer → away from electrode) + 'Coulomb / repulsion' label
- **G-7** 'air gap' label between strip and electrode

### §13.9 Totals + active iteration map

**Total sub-regions**: 46 (A:8 + B:3 + C:11 + Row2:3 + D:5 + E:4 + F:5 + G:7).

**Active iteration target** (current dogfood focus — Row 2 redesign 1차 compile):
- Row2-BG, Row2-BR1, Row2-BR2 (newly authored — visual review needed)
- D-1, E-1, F-1 (axis-frame → arrow conversion — visual review needed)
- C-L1, C-L2, C-L4 (Panel C LEFT R22 — medium-limit hit, SVG handoff deferred §12.1)

**Stable / minimum iteration**:
- Panel A 전체, Panel B 전체, Panel G 전체, Panel C RIGHT 전체

**Known iteration-debt items** (from polish checklist §10):
- C-R2/C-R3 band borders 0.45pt vs convention 2.0pt (#7)
- E-3 open markers vs convention filled (#18)
- D-3 dashed reference + C-R4 escape + A-6 inv.vulc. + leader lines = 4 dashed-line semantics (#17 consolidation)
