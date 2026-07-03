# Panel Goals — fig1_overview_v5d_redraw_001_vault

**Created**: 2026-05-17
**Source figure**: `fig1_overview_v5d_redraw_001_vault.tex` @ commit `7d41ac2` (post v8.7 + 5-iter critique polish)
**Working PNG**: `build/fig1_overview_v5d_redraw_001_vault.png`

## How to use this file

- Each panel section is the **umbrella goal** for sub-region edits. Any 1-line patch on a sub-region must stay inside the panel's `intent` + not break `forbidden` + advance one `acceptance` bullet.
- **Iteration unit = sub-region**, not panel (per session memory `feedback_subregion_iteration_unit`).
- Per sub-region loop: PNG visibility gate → 1-line patch → recompile → confirm → next. Visibility gate must always pair:
  - "Is the intended element visible / readable at print scale?"
  - "Is anything unintended visible? (rogue stroke, ghost label, overlap)" (memory `feedback_visibility_gate_anomaly_question`)
- Sub-region enumeration is mirrored from `briefing.md §13`. When briefing § updates, mirror here.
- After each sub-region pass, append entry to `subregion_iteration_log.md`.

## 4-axis acceptance scoring (per panel, all must PASS for panel closure)

Acceptance criteria are organized along 4 axes. Element-iteration loop terminates only when all 4 axes are ✅:

| Axis | Definition | Source authority |
|---|---|---|
| **이론 (Theoretical)** | Physics invariants, Forbidden rules, scope locks | briefing §8 LOCKED + §9 Forbidden + Q1..Q19 LOCKED items |
| **구조 (Structural)** | Geometry, coordinates, sub-region alignment, proportion | briefing §13 sub-region specs + bbox |
| **스토리 (Storyline)** | Reading order, intent-in-N-seconds, cross-binding | briefing §13 reading order + §13.9 binding + intent statement |
| **미감 (Aesthetic)** | Nature-grade weight/palette/typography/whitespace, ref-benchmark match | §10 polish constraints + per-panel `reference_image` (spec.yaml) + `reference/audit_table.md` transferable aspects |

Per-iteration scorecard: each axis gets ❌ / ⚠️ / ✅. Loop iteration log records all 4 scores per pass.

## Panels

- [Panel A — Sulfur-rich polymer (molecular identity)](#panel-a) — 8 sub-regions ✏️ goal drafted
- [Panel B — Sulfur composition variation](#panel-b) — 3+1 sub-regions ✏️ goal drafted
- [Panel C — Localized traps (HERO #1)](#panel-c) — 11 sub-regions (6 left / 5 right) ✏️ goal drafted
- [Row 2 cover-binding](#row-2-cover-binding) — 10 sub-regions ✏️ goal drafted
- [Column D — Kinetic evidence](#column-d) — 7 sub-regions ✏️ goal drafted
- [Column E — ISPD-paired evidence](#column-e) — 10 sub-regions ✏️ goal drafted
- [Column F — Mechanical evidence](#column-f) — 8 sub-regions ✏️ goal drafted

Total: **57 sub-regions** across 6 panels + 1 cover-binding band.

---

<a id="panel-a"></a>
## Panel A — Sulfur-rich polymer (molecular identity) — 8 sub-regions

**Intent** (2s reader): "이건 sulfur-rich **linear** copolymer (poly(S-r-DIB)) 이고, S₈에서 inverse-vulcanization으로 만들어졌다." 4 DIB ring + 3 polysulfide segment + (S)_x composition tag + S₈ inset + inv.vulc. dashed arrow가 합쳐서 한 문장으로 읽혀야 함.

**Forbidden**
- Crosslinked network topology — 4 rings 사이에 segment가 *추가로* 가지치는 모양 (briefing §8 reader DON'T LOCKED)
- 3D / branching / dendritic 인상
- Methyl pair가 primary identifier로 읽힘 (A-4는 detail tier, 놓쳐도 OK)
- A-8 'linear copolymer' subtitle 누락 (§8 invariant 강제 매개)
- cAmber bulk identity 외 hue 사용 (다른 panel과 material binding 깨짐)

**Acceptance criteria** (4-axis)

*이론 (Theoretical)*
- T1. Linear topology preserved (4 rings + 3 polysulfide segments only, no branching, no 3-way junctions) — §8 LOCKED + §9 P-A
- T2. S₈ ring is regular octagon (8 vertices + 8 S letters + center S_8 label) — §9 forbidden variants
- T3. DIB attachment is bivalent (each ring 2 polysulfide attachments at meta positions, not >2) — §8 LOCKED chemistry
- T4. gem-dimethyl methyl pair stubs at 6 quaternary C sites (isopropenyl→isopropyl product) — §13.1 A-4

*구조 (Structural)*
- S1. 4 DIB rings horizontal staggered row, R=0.26cm, ring centers at (0.75/1.50/2.25/3.00, 7.10/6.55/7.10/6.55) — §13.1 A-1
- S2. 3 polysulfide segments connect ring-to-ring at 120°-apart meta vertices — §13.1 A-2
- S3. `(S)_x` composition label position (post-C004 fix: x=2.10, y=7.55, anchor=south) — §13.1 A-3
- S4. S₈ inset at (3.05, 8.45), 7mm regular polygon, 8 atom letters at 0/45/90/.../315° vertices — §13.1 A-5
- S5. dashed inv.vulc. arrow connects S₈ vertex → Ring_c (60° vertex) — §13.1 A-6
- S6. cAmber!08 wash ellipse 1.55×0.65cm centered (1.85, 6.83) hugs ring row — §13.1 A-7
- **S13 (added v8.7 iter 5)**: Label cluster ((S)_x + inv.vulc. + S₈ inset) mutual bbox overlap absent — minimum 0.05cm gap between any two label bounding boxes. Rationale: iter 4 false-closure revealed audit blind spot — original acceptance didn't enforce label-on-label non-overlap. v8.7 iter 5 fix: (S)_x x=2.10→1.85 + inv.vulc. (2.15, 7.82)→(2.40, 7.90).

*스토리 (Storyline)*
- L1. 2-second intent: "sulfur-rich linear copolymer (poly(S-r-DIB)) + S₈ inv.vulc. origin" reads as a single sentence
- L2. Reading order honored: panel letter A → 'Sulfur-rich polymer' bold (lower-left) → 4 DIB ring row → polysulfide segments → (S)_x label → S₈ inset (top-right) → inv.vulc. dashed arrow → methyl stubs (detail tier) → inter-arrow to B
- L3. 3-tier typography hierarchy clearly distinguishable: 'Sulfur-rich polymer' bold (primary) + 'poly(S-r-DIB) linear copolymer' italic (sub) + 'inv. vulc.' italic (annotation) — §13.1 A-8
- L4. Methyl stubs read as detail (놓쳐도 OK), not primary identifier
- L5. cAmber identity binds to B/C polymer chain hints (cross-panel material continuity §13.9)

*미감 (Aesthetic)*
- A1. Line weight 3-tier strictly applied: DIB ring stroke 0.70pt (annotation) / polysulfide bond 0.50pt (R11 delicate) / methyl stub 0.55pt
- A2. Color palette: cAmber family only (cAmber!85!black strokes, cAmber!08 wash, cAmberSphere!40 S₈ fill) — §10 ≤7 hue
- A3. (S)_x label and ring row 사이 vertical whitespace 충분 — label feels floating, not crowding
- A4. S₈ inset and ring row right edge 사이 horizontal whitespace 적당 — no compression
- A5. Methyl stubs proportion subtle relative to rings — domain reader sees as gem-dimethyl, generalist reader skips harmlessly
- A6. inv.vulc. dashed arrow rendering: clean straight bezier, equal dash spacing, no hand-drawn variation
- A7. Reference benchmark: **no positive reference available for Panel A** (audit_table.md gap). Aesthetic axis evaluated against §10 alone + Nature chemistry-paper convention judgement until figure-research closes gap.

**Known issues / open**
- 핸드오프 §5 polish list에 Panel A 직접 항목 없음 (post-v8.7 critique 결과 C004 fixed: (S)_x label x 1.90→2.10)
- A-7 wash ellipse 크기/위치가 reading-order step (2)인 'Sulfur-rich polymer' label과 시각적으로 충돌하는지 미검증
- A-6 dashed arrow의 vertex termination이 ring 어느 위치에서 끝나는지 — "어느 원자에서 transformation 시작"이라는 의미가 잡히는지 확인 필요
- Positive reference gap (audit_table.md) — Nature-grade aesthetic 평가에 reference benchmark 부재; A-7 reference judgement subjective

**Sub-region checklist** (mirror of §13.1)
- [ ] **A-1** 4 DIB benzene rings (staggered row, R=0.26cm)
- [ ] **A-2** 3 internal polysulfide segments (linear DIB–S–DIB)
- [ ] **A-3** `(S)_x` composition label (floating center above row)
- [ ] **A-4** methyl pair stubs (6 sites, detail tier)
- [ ] **A-5** S₈ ring inset (top-right, 8 S vertex)
- [ ] **A-6** dashed inv.vulc. arrow (S₈ → ring vertex)
- [ ] **A-7** cAmber!08 background wash ellipse
- [ ] **A-8** 3-tier label stack ('Sulfur-rich polymer' bold / 'poly(S-r-DIB) linear copolymer' italic / 'inv. vulc.' italic)

---

<a id="panel-b"></a>
## Panel B — Sulfur composition variation — 3+1 sub-regions (post-iter1 restructure)

**Intent** (2s reader): "polymer 조성이 변화하는 sample이 *여럿* 있고, sulfur 함량이 monotonically 증가한다 (S60→S85 wt% range)." Concept-figure overview: 3 representative chains (S60/S75/S85 = endpoints + middle) of the actual 5-sample paper set (S60/S70/S75/S80/S85) + endpoint labels + axis arrow가 wt% variable의 ordered sampling으로 읽힘. Drawn-atom 개수는 artistic correlate.

**Forbidden**
- 3 chain이 하나의 chain bundle처럼 묶여 읽힘 — sample distinctness 깨짐 (B-4 divider가 막아야 함)
- S₆₀/S₇₅/S₈₅ 라벨이 *chain atom 개수*로 읽힘 (Q1 LOCKED = wt% sample name)
- chain 길이가 wt% 순서와 다르게 표현 (S₆₀ < S₇₅ < S₈₅ 순서 깨짐, §9 P-A monotonicity)
- S60..S85 라벨이 Row 2 plot panel에도 등장 (§8.8 — Panel B에만 허용; Row 2는 'shallow-rich'/'deep-rich' concept만)
- chain hue가 cAmber family 외 (Panel A material binding 깨짐)
- B-4 divider가 solid / colored / > 0.20pt (§13.2 forbidden — axis-tone 침범 / mechanism-tier 침범)
- Panel B에 full 5-sample data 표시 (quantitative figures area; overview는 concept만)

**Acceptance criteria** (4-axis)

*이론 (Theoretical)*
- T1. S60/S75/S85 (paper set의 representative subset) are wt% sulfur sample names, NOT chain atom counts (Q1 LOCKED, briefing §8.8) — full paper set S60/S70/S75/S80/S85
- T2. Composition labels appear only in Panel B; forbidden in Row 2 plot panels — §8.8
- T3. Chain length monotonicity: S60 < S75 < S85 enforced top-to-bottom — §9 forbidden non-monotonic
- T4. Concept figure scope: 3 representative chains only (full 5-sample dataset belongs to Fig 2~ quantitative panels)

*구조 (Structural)*
- S1. 3 zigzag skeletal chains stacked, chain row spacing 0.90cm (iter1 expanded from 0.60cm), centers at y=7.90/7.00/6.10 — §13.2 B-1
- S2. Drawn atom counts 10/18/24 (artistic correlate, not literal) — §13.2 B-1
- S3. Endpoint labels S₆₀/S₇₅/S₈₅ at terminal atoms (cAmber!90 6.5pt subscript) — §13.2 B-2
- S4. Bottom axis arrow + 'Sulfur content, wt%' italic label at (5.20, 5.62) — §13.2 B-3
- S5. B-4 sample boundary dividers at y=7.45 / 6.55 (2 dividers between 3 chains), x extent 3.85..6.30 — §13.2 B-4 (post-C002 + iter1 + iter2: cGray!55, +38% from !40 for perceptible print-scale)

*스토리 (Storyline)*
- L1. 2-second intent: "여러 sample (S60..S85 wt% range) 중 representative 3개 — sulfur content monotonically increases"
- L2. Reading order: panel letter b → 3 chains 위→아래 (S60→S85 monotonic recognition) → endpoint labels at chain tails → bottom axis arrow + 'Sulfur content, wt%' label → inter-arrow to C
- L3. 3 chain bundle ≠ 3 distinct samples — B-4 dividers prevent bundle misread
- L4. cAmber chain identity binds to A material continuity (\zigSChain shared macro) — §13.9

*미감 (Aesthetic)*
- A1. Zigzag bond width 0.50pt R11 delicate (NOT mechanism-tier) — §13.2 B-1
- A2. B-4 divider: cGray!55 (post-iter2, was !40), 0.18pt, densely dotted — separator only, NOT data-axis weight (§13.2 forbidden cap >0.20pt)
- A3. Chain row vertical rhythm: 0.90cm spacing (iter1 expanded) — breathing room generous; clean Nature-grade composition
- A4. Sample labels (S₆₀/S₇₅/S₈₅) subscript hierarchy clean — cAmber!90 reads as "darker than chain" without competing with chain identity
- A5. Axis arrow Stealth-tipped (length 4pt, width 3pt) cGray!60!black 0.55pt — annotation tier
- A6. Reference benchmark: concept figure (literature audit 2026-05-17: field uses property plots / sample photos for quantitative; schematic scaffold acceptable for overview/cover); no positive panel-B-specific reference

**Known issues / open**
- post-v8.7 iter1: 4→3 representative restructure SHIPPED. Cross-panel sample identity to Panel C/D/E/F intentionally abstract (concept figure does not specify which sample → measurement)
- B-1 drawn atom count (10/18/24) literal misread risk — caption.md disclaimer (v8.6 caption rewrite pending) to clarify artistic-correlate
- Positive reference gap: concept figure framing reduces priority

**Sub-region checklist** (mirror of §13.2, iter1 update)
- [ ] **B-1** 3 representative zigzag skeletal chains (S60/S75/S85, drawn-atom artistic correlate)
- [ ] **B-2** sample-name endpoint labels (S₆₀/S₇₅/S₈₅, wt% per Q1 LOCKED, representative subset)
- [ ] **B-3** bottom axis arrow + 'Sulfur content, wt%' label
- [ ] **B-4** sample boundary divider lines (2 between 3 chains, cGray!40 0.18pt dotted)

---

<a id="panel-c"></a>
## Panel C — Localized traps (HERO #1, 5s dwell) — 11 sub-regions

**Intent** (5s dwell, HERO): "poly(S-r-DIB) thin film 안에 shallow + deep trap이 *공간적으로 섞여* 분포한다. 이를 energy diagram으로 보면 mobility edge 아래 Gaussian DOS — shallow는 좁고 가까이 (easy escape), deep는 넓고 멀리 (long lifetime). 동일 trap의 real-space + energy-space *two views*가 dashed leader로 묶인다." Panel C는 figure의 시각적 hero (1.5× width + maximum detail density).

**Forbidden**
- C-L에서 shallow ●만 LEFT half, deep ●만 RIGHT half 같은 spatial segregation (§8.3 LOCKED — MIXED canonical)
- C-L3 ●가 cBlue/cRed 외 색 (§8.6 / §13.9 Binding-1 깨짐)
- dashed leader가 curved / Stealth-tipped / 색 변형 (§9 dashed semantic — straight 0.28pt densely dashed only)
- C-R5 ΔE_t에 단위 (eV) 또는 수치 부착 (§9 — symbolic depth scalar only; Fig 3 정량 영역 침범)
- C-R4 escape arrow에 tunneling / hopping / field-assisted 표현 추가 (Q9 LOCKED — thermal Boltzmann release only)
- semi-crystalline / dual-phase 가정 표현 (Q7 LOCKED — fully amorphous, Mott-CFO mobility-edge model)
- C-L1 amber gradient 방향이 upper-LEFT light anchor 외 (§9 figure-wide LOCKED — 다른 panel gradient의 reference)
- C-L6 thickness anchor가 μm 외 단위 (nm/Å chemistry-scale 모호, mm/cm typological mismatch); 두께 라벨 2개 이상; arrow span > sheet height
- shallow + deep band line width이 3-tier (mechanism 1.0pt) 외 (§10 — convention 2.0pt heavy 거부됨)

**Acceptance criteria** (4-axis)

*이론 (Theoretical)*
- T1. shallow ● + deep ● MIXED in same polymer matrix (NOT spatially segregated) — §8.3 LOCKED
- T2. Shallow = cBlue, Deep = cRed across LEFT ● + RIGHT trap levels + Gaussians + leaders — §8.2 + §8.6 + Binding-1
- T3. Mobility-edge model (Mott-CFO) applied; sample is fully amorphous (NOT semi-crystalline / dual-phase) — Q7 LOCKED
- T4. Escape arrows = thermal Boltzmann release ONLY (no tunneling / hopping / field-assisted) — Q9 LOCKED scope
- T5. C-R1b Gaussian DOS represents continuous distribution (Mott-CFO + Bässler disorder); C-R2/R3 horizontal lines are representative samples of this distribution (NOT discrete 2-level) — Q8 LOCKED
- T6. ΔE_t^d annotation is symbolic depth scalar (no eV unit, no numeric value) — §9 cartoon register
- T7. C-L6 thickness in μm only (not nm/Å chemistry-scale or mm/cm typological mismatch) — §13.3 C-L6

*구조 (Structural)*
- S1. LEFT polymer sheet at (7.55..9.85, 6.20..7.70), 2.30×1.50cm, amber gradient top→bottom cAmber!10→cAmber!38 — §13.3 C-L1
- S2. 4 ● trap sites in LEFT at siteS1/S2/D1/D2 coordinates (chain peaks/junctions) — §13.3 C-L3
- S3. C-L6 thickness arrow at x≈7.45, span y=6.20..7.70 = full sheet height + 'd ≈ 1 μm' label anchor=east italic 5.5pt — §13.3 C-L6
- S4. Energy axis vertical at x=10.50 spanning y=5.20..8.45 with tick marks — §13.3 C-R1
- S5. Gaussian DOS overlay at x=10.55, shallow peak y=7.49 σ=0.085, deep peak y=6.05 σ=0.18 (post-C001 fix: horizontal scale 0.45/0.55, opacity 0.70) — §13.3 C-R1b
- S6. C-R2 shallow trap lines at y=7.55/7.35 (2 lines + 1 ● each); C-R3 deep at y=6.20/5.85 — §13.3
- S7. dashed leaders 4줄 connect siteS1→y=7.55, siteS2→y=7.35, siteD1→y=6.20, siteD2→y=5.85, color cBlue!55!black / cRed!55!black, 0.28pt — §13.3 + §17
- S8. C-R4 escape arrows shallow (11.10, 7.55)→(11.10, 7.82) + deep (11.10, 6.20)→(11.10, 7.82), post-C005 fix: shallow 0.50pt / deep 0.35pt weight asymmetry — §13.3
- S9. C-R5 ΔE_t double-arrow at x=13.55, y=8.27..5.83 (E_C → deep band bottom), cRed!75!black 0.40pt — §13.3
- S10. C-R6 band labels 'shallow'/'deep' east-anchor bold 6.5pt sans — §13.3

*스토리 (Storyline)*
- L1. 5-second dwell (HERO): LEFT real-space → RIGHT energy-diagram → dashed leaders bind "same trap, two views" → reader infers "shallow easy escape / deep slow lifetime"
- L2. Reading order: panel letter C → 'localized traps' italic subtitle → LEFT half (sheet → chain hints → ● markers → 'thin film' subtitle) → eye crosses to RIGHT half (Energy axis → shallow band + 'shallow' label → deep band + 'deep' label → ΔE_t annotation → escape arrows → dashed leaders bind) → descend to Row 2 caption
- L3. Light anchor upper-LEFT (C-L4 highlight + shadow) — Column F polymer gradient references this — §9 figure-wide LOCKED
- L4. C-L5 'poly(S-r-DIB) thin film' subtitle binds to A-8 'Sulfur-rich polymer' (chemistry → bulk continuity) — §13.9
- L5. C-R6 typography binds to F-5 'Shallow'/'Deep' base labels (cross-panel trap-species naming) — §13.9 Binding-1

*미감 (Aesthetic)*
- A1. Line weight 3-tier: trap level lines 1.00pt (mechanism, post-v7 polish); Gaussian outline 0.50/0.55pt (annotation); axis 0.45pt; ticks 0.35pt; dashed leader 0.28pt — §10 + §13.3 R15
- A2. Color palette tight: cBlue/cRed for trap species; cAmber for polymer; cGray for axis. Shallow cBlue!75!black / Deep cRed!75!black for outlines, !18 fills, !55!black for leaders — §10 ≤7 hue
- A3. Gaussian fill opacity 0.70 (post-C001 fix) reads as distribution shape, not slivers
- A4. Whitespace: LEFT sheet (x=7.55..9.85) and RIGHT axis (x=10.50) gap 0.65cm — leader crossing space adequate
- A5. Dashed pattern semantic 일관: leaders + mobility edge + escape arrows + ΔE annotation 각각 distinct semantic (no consolidation) — §17
- A6. Polymer sheet medium quality: TikZ R22 reaches "PPT-level" not Nature-grade — §12.1 SVG handoff deferred (Inkscape redraw planned)
- A7. Reference benchmark: **no positive reference for Panel C** (audit_table.md HIGHEST-PRIORITY gap). Aesthetic judgment subjective until figure-research closes — N=1 dogfood (Panel A loop) precedes Panel C deep iteration to validate workflow

**Known issues / open**
- C-L1 polymer sheet TikZ R22 medium-limit hit ("PPT 수준") — §12.1 SVG handoff deferred, Inkscape 별도 작업 예정
- C-R1b Gaussian DOS overlay 위치 정렬 (post-C001 fix) PNG 검증 통과 (deep red clearly visible, shallow blue lighter)
- C-L3 ●가 chain peak/junction과 정확히 정렬되는지 미검증 (siteS1/S2/D1/D2 coordinate)
- Positive reference gap — Panel C HERO이므로 figure-research highest priority (energy-diagram + Gaussian DOS + hybrid split-half 주제)
- C-R4 escape arrow asymmetry (post-C005 fix) — shallow 0.50pt vs deep 0.35pt PNG에서 인지됨

**Sub-region checklist** (mirror of §13.3)

LEFT half (real-space polymer, x=7.55..9.85):
- [ ] **C-L1** amber gradient polymer sheet (2.30×1.50cm)
- [ ] **C-L2** 3 wavy chain hints inside sheet (varied opacity)
- [ ] **C-L3** embedded ● trap sites (2 shallow cBlue + 2 deep cRed, mixed NOT segregated)
- [ ] **C-L4** top-edge white highlight + right-edge cAmber shadow (upper-LEFT light anchor)
- [ ] **C-L5** 'poly(S-r-DIB) thin film' subtitle
- [ ] **C-L6** thin-film thickness anchor (↕ arrow + 'd ≈ 1 μm' label, v8.5 NEW)

RIGHT half (energy diagram, x=10.50..13.80):
- [ ] **C-R1** E_C / mobility-edge dashed / E_V refs + 'Energy' rotated label
- [ ] **C-R1b** Gaussian DOS overlay (shallow cBlue σ=0.085 / deep cRed σ=0.18, Q8 LOCKED)
- [ ] **C-R2** shallow trap levels (2 cBlue lines + ●, 1.00pt)
- [ ] **C-R3** deep trap levels (2 cRed lines + ●, 1.00pt)
- [ ] **C-R4** escape arrows (shallow short / deep long, dashed, Boltzmann scope LOCKED Q9)
- [ ] **C-R5** ΔE_t^d depth annotation (cRed double-arrow at x=13.55)
- [ ] **C-R6** 'shallow' / 'deep' band labels (bold 6.5pt sans, east anchor)

---

<a id="row-2-cover-binding"></a>
## Row 2 cover-binding — 10 sub-regions

**Intent** (2s reader): "3 independent measurement modality (kinetic / ISPD / mechanical)가 *같은 trap*을 다른 각도로 본다 — convergent evidence." Panel C HERO에서 3 spoke이 동시 fan-out + Row2 caption이 convergent semantic 명시 + 3 modality label이 각 column 묶음. **Reading은 D→E→F linear chain이 아니라 C에서 3방향 동시 분기.**

**Forbidden**
- 3 spoke을 D→E→F arrow로 표현하여 *causation chain* 인상 (§8.7 LOCKED — 3 independent measurements of same trap; §9 P-A linear chain arrow 금지)
- Row 2에 hard panel border (§9 — M2 cover-feel goal 깨짐)
- Row2 caption에 "shows", "leads to", "causes" 등 causation 언어 (convergent evidence 깨짐)
- 3 spoke 외 추가 또는 누락 (§8.7 — 3 evidence line ↔ 3 spoke 정확 매칭, design.md §3.2와 일치)
- modality label이 spoke과 다른 column center로 정렬 (kinetic/ISPD/mechanical 매핑 깨짐)
- 3 spoke의 style 불일치 (Stealth tip / cGray!65 / 0.9pt 통일 필수)
- Row2 background에 chain hint 외 polymer-texture decoration (§9 — material-identity volume cue 예외 외 texture 금지)

**Acceptance criteria** (4-axis)

*이론 (Theoretical)*
- T1. 3 spokes = 3 INDEPENDENT measurements of same trap (NOT causation chain D→E→F) — §8.7 LOCKED
- T2. Modality count 3 = column count 3, exact match with design.md §3.2 evidence lines (kinetic / ISPD / mechanical) — §8.7
- T3. Caption uses convergent language ("convergent evidence", "three independent probes"), NOT causation ("shows", "leads to", "causes") — §8.7 + §9 P-A
- T4. Anti-chain mechanism preserved via (a) shared root + (b) caption + (c) Panel C ↔ Panel F color echo — §13.4 anti-chain note

*구조 (Structural)*
- S1. 3 spokes from single root (6.95, 4.85) → endpoints (2.28, 4.30) / (6.975, 4.30) / (11.70, 4.30) — §13.4
- S2. Caption at (7.00, 4.92) south-anchored, italic 6.5pt cGray!75!black — §13.4 Row2-Caption
- S3. Modality labels: 'kinetic' (4.55, 4.55) / 'ISPD' (6.975, 4.50) / 'mechanical' (9.40, 4.55), italic 6pt sans cGray!75 fill=cAmber!8 — §13.4
- S4. cAmber!8 background wash (-0.05, 0.05) rectangle (14.05, 4.55), rounded corners 2mm — §13.4 Row2-BG-wash
- S5. 3 wavy chain hints at y≈1.20/2.50/3.80, cAmber!22 0.30pt smooth — §13.4 Row2-BG-chains
- S6. Spoke style uniform: Stealth tip 6pt×4pt, cGray!65!black, 0.9pt — §13.4
- S7. branchRoot (6.95, 4.85) inside inter-row gap (y 4.55..5.00) below Panel C bottom — §13.4 Row2-Root
- S8. ISPD spoke endpoint (6.975, 4.30) aligns to Column E column-frame top center — §13.4

*스토리 (Storyline)*
- L1. 2-second intent: "3 independent modalities (kinetic / ISPD / mechanical) measure the same trap → convergent evidence"
- L2. Reading order: Panel C bottom → caption "convergent evidence" → 3 spokes (eye perceives fan-out as simultaneous, NOT D-then-E-then-F sequence) → modality labels read as 3 parallel categories → enter Row 2 columns
- L3. Reader inversion: divergent geometry → convergent semantic. Caption + anti-chain mechanism trigger this within 2 seconds
- L4. Row2-BG-chains visual binding: Panel C-L thin film chain hints (micro) → Row 2 floor chain hints (macro) — §13.9 cross-row material continuity

*미감 (Aesthetic)*
- A1. Wash hue: cAmber!8 (Row 2) vs cAmber!08 (Panel A) — practically identical, figure-wide cAmber family integrity preserved — §10
- A2. No hard panel border on Row 2 (M2 cover-feel goal) — §9 forbidden
- A3. Spoke 3-tier weight: 0.9pt narrative tier — heavier than reference lines (0.4pt) but lighter than mechanism (1.0pt+). One arrow tip style (Stealth) figure-wide — §10
- A4. Modality label typography: italic 6pt sans, fill=cAmber!8 inner sep 1pt — labels float above wash without crowding spokes
- A5. Whitespace: inter-row gap (4.55..5.00) = 0.45cm hosts caption + branchRoot without compression
- A6. cAmber wash saturation low enough not to compete with column content — wash is "scene-binding", content is "data" hierarchy preserved
- A7. Reference benchmark: figure-level reference `codex_gen_overview_v1.png` for 2-row cover-scene density and palette restraint

**Known issues / open**
- Row2 caption "three independent probes" 표현이 5초 미만 dwell에서도 convergent로 invert되는지 미검증
- 3 spoke divergent geometry → convergent semantic invert가 (c) Panel C ↔ Panel F color match로 강화되는데, 이 visual echo가 PNG에서 실제로 강하게 작동하는지 미검증
- wash 경계가 column boundary와 시각적으로 충돌하지 않는지 미검증
- branchRoot가 inter-row gap에 있어 캡션 + spoke이 *intentional cover deviation* (§10 #3 ACTIVE) — submission journal에서 referee가 raise할 시 reopen

**Sub-region checklist** (mirror of §13.4)

Background layer (2):
- [ ] **Row2-BG-wash** cAmber!8 rounded rectangle (3 columns into 1 scene)
- [ ] **Row2-BG-chains** 3 wavy chain hints (y ≈ 1.20 / 2.50 / 3.80)

Branching root + caption (2):
- [ ] **Row2-Caption** 'convergent evidence — three independent probes of the same trap'
- [ ] **Row2-Root** branchRoot coord (6.95, 4.85) below Panel C

3 spokes (3):
- [ ] **Row2-Spoke-Kinetic** → (2.28, 4.30) Column D center
- [ ] **Row2-Spoke-ISPD** → (6.975, 4.30) Column E center
- [ ] **Row2-Spoke-Mechanical** → (11.70, 4.30) Column F center

3 modality labels (3):
- [ ] **Row2-Label-Kinetic** 'kinetic' at (4.55, 4.55)
- [ ] **Row2-Label-ISPD** 'ISPD' at (6.975, 4.50)
- [ ] **Row2-Label-Mechanical** 'mechanical' at (9.40, 4.55)

---

<a id="column-d"></a>
## Column D — Kinetic evidence — 7 sub-regions

**Intent** (2s reader, post-spoke): "transient I-t 측정 (SMU drive V across MIM stack, measure I(t))에서 I(t) ~ t⁻ⁿ power-law decay가 Debye exponential보다 long-t에서 *위로* 떨어진다 (non-Debye, CvS law). deep-rich (less-steep, smaller n) vs shallow-rich (steeper, larger n) 두 sample의 n 값이 다르다." apparatus zone (위) + log-log result zone (아래)로 register split, mini-gap이 두 zone 분리.

**Forbidden**
- power-law 곡선이 Debye dashed reference *아래로* 떨어짐 (§8.4 LOCKED — CvS는 long-t에서 항상 Debye 위; 정의적)
- D-3 axis arrow에 tick numeric label (§9 — Fig 3 정량 plot 영역 침범; cartoon register)
- D-5/D-6 curve에 S60..S85 specific sample label (§8.8 — Row 2 plot은 concept-based 'deep-rich'/'shallow-rich' only)
- D-2 apparatus zone과 D-3..D-7 result zone이 같은 register (§9 register mixing 금지 — apparatus = scene, result = log-log curve)
- deep curve가 cRed 외 hue, shallow curve가 cBlue 외 hue (§9 cross-panel color drift — Binding-1 깨짐)
- D-5/D-6 두 curve의 n 값을 *정량* 비교 또는 D ↔ F 정량 cross-panel inference 유도 (§9 quantitative cross-panel inference 차단)
- D-7 Debye가 power-law curve 끝점보다 위 (§8.4 위반)
- D-4 equation에 정량 n 값 부착 (§9 — abstract symbolic only)

**Acceptance criteria** (4-axis)

*이론 (Theoretical)*
- T1. Power-law curves (D-5/D-6) sit ABOVE Debye dashed reference at long t (Curie-von Schweidler / Jonscher universal dielectric response) — §8.4 LOCKED
- T2. NO tick numeric labels on axes (cartoon register; Fig 3 quantitative scope only) — §9 forbidden
- T3. NO composition-specific labels (S60..S85) on D-5/D-6 curves; concept-based 'deep-rich'/'shallow-rich' only — §8.8
- T4. Deep cRed / shallow cBlue color binding to Panel C/E (Binding-1) — §8.6
- T5. NO quantitative n value, no Δn cross-panel inference invitation — §9 cartoon register

*구조 (Structural)*
- S1. apparatus zone y=2.80..4.25: SMU box (0.55..1.55, 3.10..3.95) + V/A symbols + SMU italic label — §13.5 D-2 (post-C007 fix: readout indicator deleted)
- S2. MIM sample stack centered (2.50, 3.50): top hatched electrode 1.80×0.10cm + cAmber!28 polymer film 1.80×0.45cm + bottom hatched electrode — §13.5 D-2
- S3. 2 leads SMU→electrodes route outside polymer-film boundary — §13.5
- S4. Ground symbol 3-bar at bottom electrode RIGHT side (3.50..3.73, 3.21..3.35) — §13.5
- S5. mini-gap y=2.65..2.80 between zones — §13.5
- S6. result-zone axis origin (0.45, 0.40), Stealth tips at \log I (rotated) + \log t — §13.5 D-3
- S7. D-4 equation `$I(t) \sim t^{-n}$` at (0.55, 2.70) labelStrong — §13.5
- S8. D-5 deep-rich (cRed!80 0.80pt) at (0.55, 2.45)→(3.20, 1.05) — less-steep, smaller n — §13.5
- S9. D-6 shallow-rich (cBlue!80 0.80pt) at (0.55, 1.95)→(3.20, 0.45) — steeper, larger n — §13.5
- S10. D-7 Debye dashed (cGray!70 0.55pt bezier) below both curves' endpoints — §13.5
- S11. 'MIM stack' label at (0.10, 4.20) anchor=north west, italic 5pt cGray!65 — post-C012 fix
- S12. Spoke endpoint (2.28, 4.25) lands column-frame top center — §13.5

*스토리 (Storyline)*
- L1. 2-second intent: "transient I-t measurement on MIM stack → power-law I~t^-n decay above Debye exponential; deep-rich less-steep, shallow-rich steeper"
- L2. Reading order: kinetic spoke enters → D-2 apparatus icon "SMU drives V, measures I(t)" → D-4 equation mental-model anchor → D-5 deep-rich curve (위, less-steep) → D-6 shallow-rich curve (아래, steeper) → D-7 Debye dashed below (non-Debye proof) → curve-ID labels
- L3. Apparatus zone (top) and result zone (bottom) register split — apparatus = scene, result = log-log curve. Same column = "this measurement on this apparatus" — §6 LOCKED
- L4. Binding-4 to F: 'deep-rich' D-5 ↔ F deep Gaussian dominant (cross-panel kinetic↔density coupling, label-driven) — §13.9

*미감 (Aesthetic)*
- A1. Line weight 3-tier: power-law curves 0.80pt (curve tier between mechanism and annotation); axis 0.40pt; SMU/MIM/leads 0.30pt; Debye 0.55pt — §10
- A2. cBlue/cRed palette tier 0.80pt 80% saturation for primary curves; cGray for apparatus (mono frame) — §10
- A3. PSU pulse trace replaced by V_active label semantic (no analogous element in D, but D's SMU readout deleted post-C007 for clean look)
- A4. MIM stack hatching density: 18 hatches across 1.80cm = 0.10cm spacing — readable at print without noise (post-C012 'MIM stack' label clarifies architecture)
- A5. Whitespace: mini-gap 0.15cm between apparatus + result zones — clean separation
- A6. Reference benchmark (Wang NatComm 2022 Fig 1, audit_table.md D-ref04): equivalent-circuit symbols transferable; layered cross-section style. Do-not-transfer: triboelectric mechanism.

**Known issues / open**
- 핸드오프 §5: Column D MIM hatching이 300dpi raster에서 noisy 보일 수 있음 — print scale 검증 필요
- D-2 apparatus zone의 2 leads가 polymer film과 시각적으로 충돌하는지 미검증 (lead 경로가 MIM stack 외부로 우회하는지)
- ground symbol과 bottom electrode 정렬 미검증
- D-4 equation label이 D-5 curve start point (0.55, 2.45)와 너무 가까운지 (overlap risk) 미검증
- C007 SMU readout deleted (post-Tier 2); C012 'MIM stack' label added (post-Tier 2)

**Sub-region checklist** (mirror of §13.5)

Column bbox: x=0.05..4.50, y=0.10..4.45.
- [ ] **D-1** column-frame (implicit bbox anchor, no visible stroke)
- [ ] **D-2** apparatus zone (SMU box + 2 leads + MIM stack + ground, v8.7 generic synthesis)
- [ ] **D-3** result-zone axis arrows (Stealth, cGray!65 0.40pt)
- [ ] **D-4** main equation label `I(t) ~ t^-n` at (0.55, 2.70)
- [ ] **D-5** deep-rich power-law line (cRed!80 0.80pt, less-steep, smaller n)
- [ ] **D-6** shallow-rich power-law line (cBlue!80 0.80pt, steeper, larger n)
- [ ] **D-7** Debye dashed reference + curve-ID labels ('deep-rich' / 'shallow-rich')

---

<a id="column-e"></a>
## Column E — ISPD-paired evidence — 10 sub-regions

**Intent** (2s reader, post-spoke): "corona charging으로 sample 표면을 charge → Kelvin probe로 V_s(t) decay (stretched-exp, β≈0.8) 측정 → inverse-Laplace류 derivation으로 g(E_t) bimodal Gaussian 얻음. shallow (좁은 σ, LEFT) + deep (넓은 σ, RIGHT, peak 1.86× tall) → deep dominant." Single ISPD spoke이 column에 떨어져서 raw V_s + derived g(E_t) 두 sub-zone이 *paired view*로 stacked.

**Forbidden**
- V_s decay 곡선과 g(E_t) Gaussian이 *같은 axis*에 plot됨 (§13.6 — 두 sub-zone으로 stacked separation 필수: V_s y=1.50..2.60 / g(E_t) y=0.20..1.40)
- g(E_t) inversion algorithm (Tikhonov / CONTIN / model fit) 시각화 (Q13 scope-out — Methods/SI 영역; cartoon register 위반)
- E-9 τ_d 화살표에 단위 (ms / μs) 또는 수치 (§9 — abstract symbolic only; F-4 τ_d와 동일 rule)
- shallow Gaussian이 cBlue 외 hue, deep이 cRed 외 hue (§8.6 / Binding-1 깨짐)
- deep peak이 shallow와 *같거나 더 낮음* (Q4 LOCKED — 1.86× ratio = "deep dominant" narrative core)
- τ_d 화살표가 V_s decay sub-zone의 t-axis와 *직접* 연결 (§9 — ISPD inter-arrow E-5가 derivation 표현 담당; energy ↔ time domain 직접 binding 금지)
- V_s sub-zone axis에 log-t convention 적용 (Q14 — linear t LOCKED, exponential fit 적합)
- corona/Kelvin probe/meter idiom이 He 2024 Fig 1c style anchor에서 *content* 변형 (style anchor만 채택, content는 design.md)
- E-4 V_s 곡선에 numeric V_s value 또는 time scale 부착 (cartoon illustrative, Q11)

**Acceptance criteria** (4-axis)

*이론 (Theoretical)*
- T1. V_s decay and g(E_t) Gaussians on SEPARATE sub-zones (NOT same axis) — §13.6
- T2. NO inversion algorithm (Tikhonov / CONTIN / model fit) visualized — Q13 scope-out (Methods/SI only)
- T3. τ_d arrow has NO unit (ms/μs) or numeric value — §9 abstract symbolic only
- T4. Shallow cBlue / Deep cRed binding to C/F (Binding-1) — §8.6
- T5. Deep peak height = 1.86× shallow peak (deep dominant narrative) — Q4 LOCKED
- T6. τ_d arrow restricted to energy domain (no t-axis direct connection) — §9 forbidden
- T7. V_s sub-zone uses linear-t (NOT log-t convention) — Q14 LOCKED (exp fit suited to linear time)
- T8. V_s curve values cartoon illustrative (no numeric V_s or time scale) — Q11

*구조 (Structural)*
- S1. apparatus zone y=2.80..4.25: corona needle x=5.10 + sample slab (6.30..7.85, 3.40..3.50) cAmber!28 + Kelvin probe (7.25..7.55, 3.62..3.72) + V_s meter (8.20..8.95, 3.70..4.00) — §13.6 E-2
- S2. corona '+' polarity at (6.32, 3.75); 'Corona' italic 5pt at (6.55, 4.02); 'Probe' label at (7.58, 3.67); 'V_s meter' label at (8.575, 3.85); 'polymer film' label at (7.075, 3.32) — §13.6
- S3. probe support stem (7.40, 3.72→3.85) + lead probe→meter (7.40, 3.85)→(8.20, 3.85) — §13.6
- S4. V_s sub-zone y=1.50..2.60, axis origin (4.95, 1.65), V_s(t) rotated + t labels — §13.6 E-3
- S5. V_s curve cRed!70 0.70pt smooth bezier 7-9 waypoints β≈0.8 — §13.6 E-4
- S6. E-5 inter-arrow + 'derive' label (post-v8.7 iter 2 replacement of 'ISPD'); briefing §13.6 spec stale
- S7. g(E_t) sub-zone y=0.20..1.40, axis origin (4.95, 0.40), g(E_t) + E_t labels — §13.6 E-6
- S8. E-7 shallow Gaussian: cBlue!85 border + cBlue!25 fill 0.70pt σ≈0.085, LEFT peak — §13.6
- S9. E-8 deep Gaussian: cRed!85 border + cRed!25 fill 0.70pt σ≈0.18, RIGHT peak, height 1.86× shallow — §13.6 + Q4
- S10. E-9 τ_d double-headed dashed arrow (cRed!70 0.45pt) between Gaussian peaks (energy domain only) — §13.6
- S11. E-10 'Shallow'/'Deep' base labels (cBlue!75/cRed!75 italic) at Gaussian feet — Binding-1 close
- S12. Spoke endpoint (6.975, 4.30) lands column-frame top center — single spoke binds raw+derived paired view — §13.6

*스토리 (Storyline)*
- L1. 2-second intent: "corona charges sample → Kelvin probe reads V_s(t) decay → derive g(E_t) bimodal Gaussian with deep dominant (1.86×)"
- L2. Reading order: ISPD spoke enters → E-2 apparatus (corona + probe + meter) "비접촉 표면 전위 측정" → E-3/4 V_s decay raw → E-5 inter-arrow "derive" → E-6/7/8 g(E_t) Gaussians (shallow LEFT lower / deep RIGHT taller) → E-9 τ_d → E-10 base labels
- L3. Paired ISPD view: single C spoke → raw + derived sub-zones stacked vertically (mathematical inverse-Laplace mental model) — §6 + §13.9 Binding-3
- L4. Cross-panel: V_s decay (time domain) and g(E_t) (energy domain) are mathematically related, but visually connected ONLY via inter-arrow — §9 forbidden τ_d direct t-axis connection

*미감 (Aesthetic)*
- A1. Line weight 3-tier: Gaussian outline 0.70pt (curve tier); apparatus elements 0.30pt (annotation); inter-arrow 0.35pt; axes 0.40pt — §10
- A2. Color palette: cBlue/cRed for trap species (Binding-1); cGray for apparatus (mono frame); cAmber!28 sample slab (material identity) — §10 ≤7 hue
- A3. Apparatus zone density: He 2024 Fig 1c idiom transferred — components compact but identifiable, no crowding
- A4. V_s meter readout indicator deleted (post-C008) — cleaner apparatus zone, label carries function
- A5. Whitespace: V_s sub-zone and g(E_t) sub-zone vertical separation (mini-gap 2.65..2.80) — clean stacking; inter-arrow occupies separation logic
- A6. Reference benchmark (He NatComm 2024 Fig 1c, audit_table.md E-ref01): full-spectrum match. Probe-above-sample geometry, motion-stage labeling, sample-on-grounded-substrate cross-section. Style transfer comprehensive.

**Known issues / open**
- shallow vs deep peak ratio 1.86× — iter 4에서 1.26×→2.0× 수정; PNG에서 deep > shallow 확인됨, 정확한 1.86× ratio 측정 미실행
- corona needle '+' polarity cue가 sample slab top과 정렬되는지 미검증
- Kelvin probe support stem이 meter box까지 lead로 연결 visible 한지 미검증
- C008 V_s meter readout deleted (post-Tier 2)
- 'derive' label과 briefing §13.6 E-5의 'ISPD' label 명세 불일치 — briefing Type A edit (LLM autonomous) 후보로 표시됨

**Sub-region checklist** (mirror of §13.6)

Column bbox: x=4.65..9.30, y=0.10..4.45.
- [ ] **E-1** column-frame (bbox anchor at top center (6.975, 4.25))
- [ ] **E-2** apparatus zone (corona needle + sample slab + Kelvin probe + V_s meter, He 2024 Fig 1c adaptation)
- [ ] **E-3** V_s sub-zone axis (Stealth, V_s(t) / t labels)
- [ ] **E-4** V_s stretched-exp decay curve (cRed!70 0.70pt, β≈0.8 cartoon)
- [ ] **E-5** internal raw→derived inter-arrow + 'ISPD' label
- [ ] **E-6** g(E_t) sub-zone axis (g(E_t) / E_t labels)
- [ ] **E-7** shallow Gaussian (cBlue!85 σ≈0.085)
- [ ] **E-8** deep Gaussian (cRed!85 σ≈0.18, peak 1.86× shallow per Q4)
- [ ] **E-9** τ_d double-headed dashed arrow between peaks
- [ ] **E-10** 'Shallow' / 'Deep' base labels (cBlue!75 / cRed!75 italic)

---

<a id="column-f"></a>
## Column F — Mechanical evidence — 8 sub-regions

**Intent** (2s reader, post-spoke): "PSU drives V across electrode + neutral cantilever fixture (rest state) → image/induced Maxwell attraction이 baseline으로 약하게 (light pink dashed). trapping 후 q_tr 도입 → polymer가 electrode AWAY (LEFT)로 bend, Coulomb repulsion 화살표가 bold cRed solid로 *Maxwell baseline을 이김*." **Clip FIXED / polymer MOVES** narrative + apparatus vs result zone에서 Maxwell-vs-Coulomb color tier 대비가 paper의 novelty argument.

**Forbidden** (§8.5 v8.6 amendment + §9)
- Maxwell arrow가 *result zone*에 등장 (§8.5 — apparatus only; collapse the contrast)
- Coulomb arrow가 *apparatus zone*에 등장 (§8.5 — q_tr 없으므로 Coulomb 없음)
- Maxwell과 Coulomb arrow가 same color/weight (§8.5 — color tier discrimination required: Maxwell 가볍게/세컨더리, Coulomb 굵게/프라이머리)
- 정량 force 값 부착 (e.g., "F_Coulomb = 12 nN") (§8.5 — qualitative cartoon)
- clip이 apparatus와 result zone에서 *다른 x 위치* (clip FIXED narrative 깨짐 — x-aligned 필수)
- polymer가 electrode RIGHT (toward)으로 bend (§8.5 — Coulomb REPULSION = away/LEFT)
- q_tr ●가 cRed 외 hue (Binding-1 깨짐, C/E의 deep cRed와 trap-species 일관성 깨짐)
- electrode hatching이 apparatus (cross-hatched 45°+135° per Conrad)와 result (metallic gradient + single-direction)에서 *구별 불가* (apparatus = Conrad idiom signal, result = active state distinction)
- isometric perspective skew on F (§9 P-B — orthographic only)
- light-source convention upper-LEFT 외 방향 (§9 figure-wide LOCKED — C-L4 anchor와 일치)
- apparatus polymer 안에 chain hint > 0.40 opacity 또는 > 3 chains (§9 — material-identity volume cue 예외 한도)

**Acceptance criteria** (4-axis)

*이론 (Theoretical)*
- T1. Maxwell ALLOWED in apparatus zone (baseline cue); FORBIDDEN in result zone — §8.5 v8.6 amendment
- T2. Coulomb arrow appears ONLY in result zone (apparatus has no q_tr) — §8.5
- T3. Color tier mandatory: Maxwell light (cRed!35 dashed thin) << Coulomb bold (cRed!80 solid thick) — §8.5 anti-violation
- T4. NO quantitative force values (no "F=12nN") — §8.5 qualitative cartoon
- T5. Polymer bends LEFT (AWAY from electrode) = Coulomb REPULSION, NOT attraction — §8.5
- T6. q_tr cRed binding to C/E deep-trap red (Binding-1) — §8.6
- T7. NO isometric perspective on F (orthographic only) — §9 P-B
- T8. Light source convention upper-LEFT consistent with C-L4 anchor — §9 figure-wide LOCKED
- T9. Apparatus polymer chain hint ≤0.40 opacity, ≤0.40pt, ≤3 chains — §9 material-volume cue cap

*구조 (Structural)*
- S1. apparatus zone y=2.80..4.25: PSU box (9.85..10.40, 3.45..4.00) + V_active label + pulse trace (post-C003 v2 fix: 0.60pt) + 2 leads (top y=4.30, bottom y=2.80) — §13.7 F-2
- S2. clip-mount block (12.25..12.65, 4.10..4.20) + 4-triangle stipple above — §13.7
- S3. neutral polymer cantilever (12.40..12.50, 2.90..4.10), pale cAmber!18 opacity 0.75 (post-C006 fix), straight upright — §13.7
- S4. apparatus electrode (13.30..13.50, 2.90..4.05) cross-hatched 45°+135° cGray!50, line spacing 0.04cm (Conrad 2016 idiom) — §13.7
- S5. 'air gap' inline italic 5pt cGray!65 at (12.95, 3.10) — §13.7
- S6. F-3 Maxwell arrow (cRed!55!black dashed 0.45pt, polymer→electrode, apparatus zone) + 'F_Maxwell (baseline)' label anchor=north at (12.90, 3.45) (post-C009 fix) — §13.7
- S7. result zone y=0.20..2.60: result clip (11.55..11.90, 2.45..2.55) x-aligned with apparatus clip — §13.7 F-4
- S8. F-5 bent polymer root (11.625, 2.45) → tip (11.20, 0.85), bend ~0.35cm Δx LEFT; cAmber!22→!42 gradient saturated; outline cAmber!80!black 0.55pt rounded 0.3mm — §13.7
- S9. F-6 3 q_tr ● (cRed!75!black fill / cRed!85!black border, 1.4mm diameter, 0.40pt outline) inside bent polymer + 'q_tr' italic 6.5pt cRed!70 fill=white label — §13.7
- S10. F-7 Coulomb arrow (cRed!80!black Stealth solid 0.7pt) polymer tip → LEFT + 2-line label 'Coulomb' bfseries 7pt / 'repulsion' mute 6.5pt cRed!75!black SE/NE anchor (line between labels) — §13.7
- S11. F-8 air-gap dimension arrow (11.55, 0.50)↔(13.55, 0.50) cGray 0.32pt + 'air gap' fill=cAmber!8 + result electrode (13.55..13.80, 0.30..2.50) cGray metallic gradient + 'electrode' label — §13.7
- S12. Spoke endpoint (11.70, 4.30) lands column-frame top center — §13.7

*스토리 (Storyline)*
- L1. 2-second intent: "PSU drives V across rest-state fixture → Maxwell baseline attraction (light pink). After trapping, q_tr drives Coulomb REPULSION (bold red) that wins against Maxwell baseline."
- L2. Reading order: mechanical spoke enters → F-2 apparatus (PSU + clip + neutral polymer + electrode + Maxwell baseline) → F-3 Maxwell arrow (light, secondary) → eye descends → F-4 result clip (same x as apparatus, FIXED) → F-5 bent polymer (LEFT, polymer MOVES narrative) → F-6 q_tr cRed markers → F-7 Coulomb arrow (bold red, primary) + 2-line label → F-8 air gap dimension + electrode
- L3. Maxwell-vs-Coulomb tension = paper novelty argument: weight + color asymmetry encodes "Coulomb wins"
- L4. Clip FIXED / polymer MOVES: apparatus + result clip x-aligned ⇒ reader perceives temporal evolution of same setup (NOT two different fixtures)
- L5. Apparatus electrode (cross-hatched, "rest setup") vs result electrode (metallic gradient, "active state") differentiation distinguishes the two zones while preserving same physical object identity

*미감 (Aesthetic)*
- A1. Line weight 3-tier: Coulomb 0.70pt (mechanism); Maxwell 0.45pt (annotation); cantilever outline 0.55pt; apparatus elements 0.30pt; air-gap dimension 0.32pt — §10 + §8.5
- A2. Color palette: cAmber polymer (rest pale opacity 0.75 / active saturated gradient) + cRed for forces and q_tr + cGray for apparatus mono — §10 ≤7 hue
- A3. Color tier asymmetry CARRIES the narrative argument (not just a visual choice) — cRed!35 dashed vs cRed!80 solid encodes "wins"
- A4. F_Maxwell label moved below arrow (post-C009 fix) — apparatus-electrode gap clean
- A5. Result polymer bend curvature: 0.35cm Δx over 1.60cm length — currently rigid-looking, Nature-grade would have smoother parabolic bend (deferred)
- A6. PSU pulse trace marginal at print scale even at 0.60pt (post-C003 v2) — accept as semantic-via-label OR widen PSU box later
- A7. apparatus electrode (cross-hatched) and result electrode (metallic gradient) — two stylizations of same component invite reader confusion; clarification candidate
- A8. Reference benchmark (Conrad NatComm 2016 Fig 1, audit_table.md F-ref01): cross-section line convention adopted. Secondary Wang NatComm 2024 dropletelectret Fig 2E (Maxwell-stress color field) deferred — could reinforce Maxwell baseline visualization if F's color tier needs upgrade.

**Known issues / open**
- 핸드오프 §5: PSU pulse trace marginal even after C003 v2 fix (0.60pt) — accept via V_active label semantic OR widen PSU box (next iteration)
- 핸드오프 §5: 'F_Maxwell (baseline)' label crowding resolved post-C009 (anchor south→north)
- TG-G-002 (Maxwell-vs-Coulomb color/weight discrimination) PASS at desktop view; print-scale verification pending
- F-2 lead routing (top via y=4.30 + bottom via y=2.80)이 polymer를 *완전히* 피하는지 PNG 미검증
- F-5 cantilever bend가 0.35cm Δx로 reader가 perceivable 한 변형으로 보이는지 미검증; Nature-grade에서는 smoother parabolic curvature 권장 (deferred)
- apparatus electrode (cross-hatched) vs result electrode (metallic gradient) 두 stylization이 같은 figure에서 *동일 component*로 인지되는지 (or 다른 object로 오독되는지) 미검증
- C006 apparatus polymer opacity 0.6→0.75 (post-Tier 2) — slight improvement but 0.10cm thin rect inherently limited

**Sub-region checklist** (mirror of §13.7)

Column bbox: x=9.45..13.95, y=0.10..4.45.
- [ ] **F-1** column-frame (bbox anchor (11.70, 4.25))
- [ ] **F-2** apparatus zone (PSU + 2 leads + clip-mount + neutral polymer + cross-hatched electrode + air gap label, Conrad 2016 Fig 1b adaptation)
- [ ] **F-3** Maxwell attraction baseline arrow (cRed!35!white dashed 0.35pt, apparatus zone only per §8.5 amendment)
- [ ] **F-4** result-zone clip + mount (FIXED, x-aligned with apparatus clip)
- [ ] **F-5** bent polymer cantilever (LEFT, away from electrode — Coulomb repulsion)
- [ ] **F-6** 3 q_tr ● markers (cRed!75 deep, color binding to C/E) + label
- [ ] **F-7** Coulomb repulsion arrow (cRed!80 bold 0.7pt) + 2-line 'Coulomb / repulsion' label
- [ ] **F-8** result-zone electrode + air gap dimension

---

## Cross-panel bindings to honor during iteration (§13.9)

- **B1 Color**: Shallow=cBlue / Deep=cRed across C ↔ E ↔ F. Any patch on those colors must preserve binding.
- **B2 ● marker**: same glyph in C-L3 (matrix) + C-R2/R3 (energy levels) + F-6 (q_tr). Don't substitute shape per panel.
- **B3 E↔F derivation**: V_s decay (E-4) → ISPD inter-arrow (E-5) → g(E_t) Gaussians (E-7/E-8). Don't break the visual chain.
- **B4 D↔F kinetic↔density**: 'deep-rich' (D-5) ↔ deep Gaussian dominant (E-8) ↔ q_tr cRed (F-6). Same trap species story.

## Theory guards in flight

- **TG-G-001..ROW2-001**: prior guards, status in `theory_guard.md`
- **TG-G-002** (v8.6 NEW): Maxwell vs Coulomb color/weight discrimination — pending verification post-v8.7 critique
