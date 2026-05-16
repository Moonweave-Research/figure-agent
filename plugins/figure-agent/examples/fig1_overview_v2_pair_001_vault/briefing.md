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

> **Note on "같은 trap" (Q22)**: paper의 실제 trap landscape은 **bimodal Gaussian DOS** (shallow + deep, §13.3 C-R1b). "같은 trap"은 "이 material의 trap landscape" shorthand — 3 modalities (kinetic CvS / ISPD g(E_t)+τ_d / mechanical Δθ)가 동일 bimodal distribution을 다른 domain에서 probe. Multiple trap species 부정 아님. Paper framing은 charge-trap-centered (v9.7, planning/INDEX); bending은 macroscopic probe (NOT showcase).

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
- **Cross-modality quantitative consistency (Q23, planning/session_260427)**: Fig 1은 *narrative convergence* 만 시각화. 정량 cross-check (n from D ↔ deep peak from F ↔ Δx magnitude from G)는 본 paper의 **Fig 3 (CvS n + ISPD g(E_t) + τ_d 3-in-1) + Fig 5 (Δθ(t), t₅₀)** 영역. Pending data action: "Δθ(t) τ_relax ↔ ISPD τ_d 정합 plot" (planning/session_260427 측정 권고, MED priority). Fig 1 reader가 정량 일치 검증을 시도하면 안 됨 (cartoon register).

---

## §3.1 Row 1 reading flow + zoom-out mechanism (eye-trace)

**Eye-flow timeline** (~7s for Row 1, sets context for Row 2):

| Step | Action | Dwell | Trigger |
|---|---|---|---|
| 1 | Eye enters figure from top-left (Panel A) | 1s | reading habit (좌→우, 위→아래); A의 'Sulfur-rich polymer' bold label이 anchor |
| 2 | Scan A: 4 DIB rings + polysulfide segments + S₈ ring (top-right) + inv.vulc. arrow | 1s | chemistry detail; "재료가 뭔지" 식별 |
| 3 | Inter-arrow A → B horizontal trigger | 0.3s | "→" Stealth arrow at y=7.0 = "다음 zoom level" 신호 |
| 4 | Scan B: 4 zigzag chains (S60..S85 samples) + axis 'Sulfur content, wt%' | 1s | "sulfur composition variable, monotonic wt% progression" 인식 |
| 5 | Inter-arrow B → C horizontal trigger | 0.3s | "→" 두 번째 arrow = bulk material로 또 한 번 zoom-out |
| 6 | Panel C HERO dwell (split-half) | **5s** | C-L sheet (real-space) + C-R energy diagram + shallow/deep band + ● markers + dashed leaders + ΔE_t depth |
| 7 | Descend toward Row 2 via caption | 0.5s | "convergent evidence" caption 시작 → §4.1 Row 2 flow 진입 |

Total ~9s for Row 1 (A 1s + B 1s + C 5s + transitions 1.6s + descend 0.5s).

**Zoom-out mechanism — 3-step molecular→bulk progression**:

1. **A: molecular detail** — chemistry-specific (DIB ring + polysulfide + S₈ + isopropenyl methyl pairs). Reader가 "재료 분자 구조" 식별. cAmber!8 wash ellipse가 ring+chain 묶음.
2. **B: sulfur composition sampling** — 4 samples (S60/S70/S75/S85 = 60/70/75/85 wt% S) variation. Same `\zigSChain` macro로 A의 분자 detail이 composition variable로 abstract. Reader가 "황 함량이 다른 4 sample" 인식 (Q1 LOCKED: numbers = wt%, NOT atom count).
3. **C HERO: bulk thin film + energy landscape** — Panel B의 ensemble이 bulk poly(S-r-DIB) thin film (C-L)으로 묶이고, 그 안에 trap states (● markers)가 분포. C-R는 같은 trap을 energy domain에서 다시 보여줌 (split-half binding).

**Cross-panel echo** (A → B → C 연속성):
- A의 `(S)_x` composition label ↔ B의 'Sulfur content, wt%' axis (composition variable 동일 — A는 generic '(S)_x' 표기, B는 specific wt% sampling)
- A/B의 `\zigSChain` chains ↔ C-L의 3 chain hints inside sheet (zoom-out)
- A의 amber tone ↔ B의 cAmber chains ↔ C-L의 cAmber gradient sheet (material identity)

**What reader SHOULD do**:
- Panel A에서 chemistry 정체성만 식별 (S₈ + DIB + polysulfide 단어 인지)
- Panel B에서 "sulfur 함량 variable이 있다" 인지 (S60..S85 = 60..85 wt% S samples); **정량 wt% 값은 무시** (S60..S85 relative ordering만; absolute wt% 비교는 Fig 4 composition sweep 영역)
- Panel C HERO에서 5s dwell — split-half (real-space + energy) **둘 다** 봐야 함
- C-R6 'shallow'/'deep' 라벨이 F의 'Shallow'/'Deep'과 binding될 것을 예고

**What reader should NOT do**:
- Panel A의 specific atom 수 세기 (artistic exaggeration; 실제 polysulfide segment 길이는 cartoon이지 정량 아님)
- Panel B의 drawn chain length 정량 비교 (10/14/18/24 atoms은 artistic correlate of wt% S; 실제 atom count 아님; literal atom count interpretation 금지)
- Panel C-L과 C-R의 ● count 정량 비교 (4 ● vs 4 levels는 representational 일치, 실제 trap 수 아님)
- A → B → C를 "causation" (A가 B를 야기, B가 C를 야기)으로 읽기 — **zoom-out**, not causation

**Reader confusion signals**:
- "A의 polysulfide segment가 짧다?" → cartoon scale; 실제는 길지만 visible compact representation
- "B의 chain 4개는 sample 4종류?" → no, 같은 polymer의 length variation (heterogeneity within single sample)
- "C-L과 C-R의 ●가 다른 trap?" → 같은 trap의 두 representation (real-space vs energy diagram); dashed leaders가 site↔level binding

---

## §4.1 Row 2 reading flow + anti-chain mechanism (eye-trace)

**Eye-flow timeline** (~5s for Row 2 total scan):

| Step | Action | Dwell | Trigger |
|---|---|---|---|
| 1 | Eye descend from Panel C HERO | 0.3s | C 5s dwell이 자연스럽게 Row 2로 내려감 |
| 2 | Catch caption "convergent evidence" | 0.5s | italic gray text + 중앙 위치 = mental gate |
| 3 | Trace 3 spokes from root | 0.7s | radial divergent pattern recognition |
| 4 | Land at one panel (kinetic / ISPD / mechanical) | 1.5s each | reader 선택; 보통 좌→우 시각 습관으로 D 먼저 |
| 5 | Brief visit to remaining panels | 1s each | "확인" — same trap의 다른 측정 |
| 6 | Holistic re-scan | 1s | "3 lines all confirm" gestalt |

**Anti-chain mechanism — 3-fold defense** (briefing §8.7 forbids D→E→F→G linear reading):

1. **Shared origin**: 3 spoke 모두 단일 branchRoot (6.95, 4.85) from C HERO 출발. Reader brain은 "single source emits 3 streams" 패턴으로 인식 (≠ "chain of cause-effect"). →Row2-Root 좌표 명시.
2. **Caption priming**: "convergent evidence — three independent probes" 명시적 의미 gate. Reader가 panel 진입 *전*에 "independent" 단어 인지 → sequential reading 자동 억제. →Row2-Caption.
3. **Color match echo**: Panel C-R2/R3 (shallow blue + deep red band) ↔ Panel F-2/F-3 (shallow + deep Gaussian) ↔ Panel G-4 (q_tr cRed). Color 반복이 "동일 trap이 여기저기 나타남" 시각 echo. → §13.9 Binding-1.

**What reader SHOULD do**:
- Spoke 1개 trace → 1개 panel dwell → 다른 spoke 돌아가서 → 다음 panel
- 각 panel의 single-claim 5단어 핵심 ("power-law not Debye" / "raw decay stretched" / "bimodal density" / "macro bending")
- 3 panel 모두 → 같은 trap의 3 측정

**What reader should NOT do**:
- D 끝 → E 시작 → F 시작 → G 시작 (left-to-right linear)
- 정량 수치 추출 (tick 없음으로 차단)
- D의 n 값과 F의 peak ratio를 quantitative하게 연결 (cartoon register; symbolic만)

**Reader confusion signals** (다음 dogfood에서 monitor):
- "왜 G 화살표만 빨간색?" → §8.5 LOCKED 인지 부족; G-6 Coulomb arrow label 분리 필요
- "D의 두 선이 같은 sample이야?" → D-5 'deep-rich' / 'shallow-rich' 라벨이 다른 sample이지 같은 sample 아님 명확화 필요 (briefing §8.8 sample composition)
- "왜 E와 F만 가까이 붙어있어?" → §6 paired ISPD 명시; spoke-ISPD가 vertical인 이유는 E↔F 쌍 결속

---

## §5. Hero hierarchy mechanism (시각적, NOT semantic)

| 메커니즘 | Panel C | Row 2 plot (D/E/F) | Row 2 schematic (G) |
|---|---|---|---|
| 면적 | 1.5× width | equal | equal |
| Color saturation | deep-red strong + shallow-blue strong | mid | mid + isometric tone |
| Detail density | maximum (LEFT polymer + RIGHT band + ● markers + leaders + escape arrows) | minimal (axis arrow + 1-2 curve + 1 label) | medium (cantilever + ● + air gap + Coulomb arrow) |
| Position | Row 1 우측 dominant | Row 2 equal | Row 2 equal |

Result: Panel C *시각적 hero*; Row 2는 *evidence radiation*으로 평등 분포. Row 2 내부 hero 위계 없음 (3 lines는 평등).

---

## §6. Per-panel ROLE (NOT current implementation snapshot — see §7)

| Panel | Narrative role | Aesthetic register |
|---|---|---|
| A | 재료 identity — poly(S-r-DIB) primary microstructure | schematic (chemistry) |
| B | 분자 heterogeneity — variable sulfur composition (S60..S85 wt% samples) | hybrid (skeletal + conceptual axis) |
| C | **HERO #1** — trap landscape (LEFT real-space + RIGHT energy diagram) | schematic dominant (scene) |
| D | Kinetic evidence icon — I(t) ~ t⁻ⁿ shape | iconic cartoon |
| E | ISPD raw V_s decay icon | iconic cartoon |
| F | ISPD-derived g(E_t) bimodal icon | iconic cartoon |
| G | Mechanical evidence scene — Coulomb-driven bending | schematic (isometric scene) |

E ↔ F는 *paired ISPD transformation*으로 묶음 — single spoke from C, paired short-arrow internal.

---

## §7. Current .tex state vs design target — ALIGNED (post-v7, 2026-05-16)

v5/v5.1/v6/v6.1/v7 거치며 briefing 의도와 `.tex`가 정렬됨. 잔여 deferred item만 active.

| Layer | Status | Notes |
|---|---|---|
| Row 1 (A / B / C) | aligned | Panel C 1.5× width + HERO saturation + hybrid split-half ✓ |
| Row 2 layout | aligned (post-v7) | M2 cover-feel ✓; D/E/F/G 모두 3.45cm width-normalized; G 폴리머 압축 (L 2.75→2.15); D/E/F content y ≤ 3.40 |
| Row 2 arrow | aligned | 3-spoke branching from C (kinetic / ISPD / mechanical) + Row2 caption ✓ |
| Panel C LEFT polymer sample | deferred (§12.1) | TikZ R22; Inkscape SVG handoff 별도 작업 |
| Panel G F1 air gap | aligned (v5) | 0.575→1.425cm (2.48×), 31° swing buffer; metallic + chain-hint polish |

Brief = current implementation state. 다음 dogfood에서 새 gap 발견되면 §7 재오픈.

---

## §8. Physics invariants (LOCKED, 기존 v2.3 §4 유지 + branching arrow physics constraint 추가)

8.1 Deep traps = **lower energy** (deeper wells); shallow traps = higher energy. **Carrier polarity**: figure는 polarity-neutral filled-dot (●) marker 사용 (v8); ⊖/⊕ 표기는 lit convention상 electron/hole 각각 자동 imply하므로 deferred to paper experimental data. poly(S-r-DIB) charge-trap physics는 published primary source 없음 (Q6 lit-check 2026-05-16; Nicolai 2012 NMat 의 conjugated polymer analog에서는 electron trap dominant). 논문 데이터 확정 시 ●→⊖ (electron) 또는 ⊕ (hole) 또는 둘 다 upgrade 가능.
8.2 Color convention: **shallow = blue, deep = red.** Consistent across Panel C, F, G. **Color-blindness redundancy** (Q10 확인 2026-05-16): color 외 position + size 동시 encoding — shallow는 mobility edge 근처 (높이 위), deep는 멀리 (낮은 위치); F-3 deep Gaussian이 F-2 shallow 대비 1.86× tall. 적록 색맹 (~6-8%) reader도 position + size로 shallow ↔ deep 식별 가능 (triple-encoding). Shape 차이 도입 (e.g., ●/◆)은 scope 밖 — color convention 충분.
8.3 Panel C representation: **hybrid split-half**. LEFT = polymer matrix with mixed-depth ● sites (NOT spatially segregated — same polymer contains both kinds). RIGHT = trap-level energy diagram with E_C / mobility edge / E_V references + shallow + deep horizontal trap-level structures + escape arrows + ΔE_t^d depth annotation. Dashed gray leaders bind LEFT sites to RIGHT energy levels.
8.4 Power-law I(t) ~ t⁻ⁿ lies **above Debye reference** at long times (non-Debye tail). Cannot be below. **Physical basis LOCKED (Q19)**: Curie–von Schweidler (CvS) law (Curie 1889 / von Schweidler 1907), Jonscher universal dielectric response (Jonscher 1977). CvS power-law tail이 Debye exponential보다 long-t에서 항상 위 = 정의적 (non-exponential ≡ slower decay). 본 paper Fig 3에서 CvS n exponent 정량.
8.5 Panel G: **only Coulomb repulsion** arrow (red, polymer → away from electrode). Maxwell attraction arrow **forbidden** (design.md v2.2 §2.3). Cantilever clip on **TOP**, polymer hanging down. **Justification (Q16, planning/session_260427)**: Maxwell attraction (image-charge induced)은 *항상 존재* (Phase C에서 단독 작용 명시) — 그러나 Fig 1 G는 paper의 **novel signature** = polarity-locked Coulomb 척력 (F_clip = Q_clip × E_active simple model)만 표현. Maxwell 화살표 추가 시 narrative novelty 희석. Maxwell + Coulomb 동시 표현은 Fig 5 (mechanism scene) 또는 SI Methods 영역; Fig 1 G는 qualitative illustration of macro probe identity.
8.6 Panel C ↔ Panel F color-consistent (bimodal: blue Shallow / red Deep).
8.7 **Branching arrow physics constraint**: 3 spoke from C **must** match the 3 evidence lines in design.md §3.2 (kinetic / ISPD / mechanical). No new evidence line, no missing line. Spoke 순서 + label은 measurement modality, NOT causation chain — physics는 *3 independent measurements of same trap*, *not* causation chain D→...→G.
8.8 Composition labels (S60 / S70 / S75 / S85 = **sulfur weight-percent sample names**, Q1 LOCKED — NOT chain atom count)은 **Panel B에만** 허용. Row 2 plot panel은 concept-based only ("shallow-rich" / "deep-rich" / "low n" / "high n"). Numbers 60/70/75/85 refer to wt% S per planning/sulfur_sample_selection_policy.md. Drawn chain atom counts (10/14/18/24 in B-1) is artistic correlate only.

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
- **Cross-panel color drift** [LOCKED via §8.2 + §13.9 Binding-1]: Shallow은 cBlue 외 hue 금지, Deep은 cRed 외 hue 금지 (Panel C-R2/R3 / F-2/F-3 / G-4 q_tr 전부). Color drift = binding 깨짐 → reader가 "다른 trap species"로 오독.
- **τ_d 라벨 numeric / unit 부착 금지**: F-4의 $\tau_d$는 *abstract* 시상수 분리 표현이지 literal 시간값 아님. 단위 (ms, μs 등) 또는 숫자 추가 시 cartoon register 위반 + Fig 3 영역 침범.
- **Register mixing 금지**: D/E/F = iconic cartoon register (axis arrow, no ticks, symbolic curves); G = isometric schematic register (scene with concrete physical elements); C = hybrid split (real-space + energy diagram). 같은 row 안에서 register가 섞이면 reader가 "어느 panel을 어떻게 읽어야 할지" 혼란. 신규 panel 추가 시 register 명시 필요.
- **τ_d 화살표 → linear t-axis 직접 연결 금지**: τ_d (energy domain F)와 V_s decay 시상수 (time domain E)는 mathematically related but visually 직접 화살표 금지 — ISPD inter-arrow (E-4)가 derivation 표현 담당.
- **Quantitative cross-panel inference 차단**: D의 n 값 ↔ F peak ratio 정량 연결, G의 Δx 값 ↔ q_tr charge 수치 inference 등은 reader가 *시도하면 안 되는* 추론 (cartoon register; Fig 3에서 다룸).
- **Panel A topology 위반 금지** [LOCKED §6 + §12.3]: poly(S-r-DIB)는 **linear copolymer** (DIB는 bivalent, 결합 가능 위치 2개). Crosslinked network / branched / dendritic 표현 금지. DIB ring을 2개 초과 substituent로 그리거나 polysulfide segment이 3-way junction 형성 금지. A-1/A-2의 4 ring + 3 segment 구조가 **canonical**.
- **Panel A S₈ ring 형태 변형 금지**: regular octagon만 허용 (`shapes.geometric regular polygon sides=8`). Hexagon, decagon, fused-ring 변형은 chemistry 위반. S₈ vertices 8개 = 'S' atom letters 8개, 중앙 'S₈' label = canonical.
- **Panel B chain length monotonicity 위반 금지**: S₆₀ < S₇₀ < S₇₅ < S₈₅ atom count 순서가 위→아래 chain 길이 monotonic increase로 시각화. 순서 뒤바뀜 / 비-monotonic 변형 금지 (chain length variable이 ordering임을 깸).
- **Panel C-L spatial segregation 금지** [LOCKED §8.3]: shallow + deep trap이 polymer matrix 안에서 *공간적으로 분리* 되어 표시되면 안 됨 (e.g., LEFT half = shallow only, RIGHT half = deep only). MIXED distribution이 canonical — shallow ● + deep ●이 동일 matrix에 산재.
- **Panel C dashed leader 형태 변형 금지** [LOCKED §17 dashed semantics]: C-L ● site → C-R trap level binding은 cBlue!55!black / cRed!55!black `densely dashed` 0.28pt **straight** line only. Curved / Stealth-tipped / 색 변형 금지 (semantic = "binding"; arrow=transition, curve=process와 분리 유지).
- **Panel C ΔE_t 수치 부착 금지**: C-R5의 `$\Delta E_t$` annotation은 *symbolic depth scalar*. 단위 (eV) 또는 수치 부착 시 cartoon register 위반 + Fig 3 정량 plot 영역 침범.

---

## §10. Polish constraints (compressed)

10-paper convention checklist (post figure-research 2026-05-15): 16/20 items honored. Full corpus: `~/tmp/figure-refs-top-tier-fig1-overview-polish-20260515-153944/candidates.md`.

Residual items + active markers:
- **#3 Inter-panel gap deviation** [ACTIVE] — Row 1↔Row 2 branching arrow + 3 spoke + caption *intentionally inhabits the gap*. M2 cover-feel goal에 의도된 deviation. Branching 도입은 deviation을 *escalate*하지만 의도된 cost. Current decision; reopen only if cover-feel goal changes.
- **#7 Panel C band borders** [RESOLVED v7] — v7에서 0.80→1.00pt 절충 적용 (convention 2.0pt는 너무 heavy; mechanism tier 1.0pt가 §10 3-tier과 일관). C-R2/C-R3 horizontal trap level lines.
- **#17 Dashed line semantic** [ACTIVE — kept as-is] — 4 meanings (Debye reference / escape transition / inv. vulc. transformation / leaders): 각각 distinct semantic, consolidation 시 정보 손실. Context-based parsing 유지.
- **#18 Panel E markers** [RESOLVED v7] — open(fill=white)→filled(fill=cRed!50). 6 markers Δt=0.30 spacing, low density에 filled가 cleaner read.

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

### §12.1b Scope-out decisions (Q13/14/17/18/21/24/25 auto-resolved 2026-05-16)

External-question 비판 중 non-critical 항목은 host 판단으로 figure scope 밖 처리:

- **Q13 g(E_t) inversion algorithm** (Tikhonov / CONTIN / model fit 중): paper Methods/SI 영역. Figure는 derived 결과 shape만 전달 — algorithm 명시 시 cartoon register 위반.
- **Q14 linear t vs log t convention**: v6.1에서 linear t 확정 (exponential fit이 linear time domain에 적합). ISPD log-t convention과 다르지만 cartoon 의도이며 §13.6 E-1에 이미 명시됨. 추가 fix 없음.
- **Q17 air gap real value vs cartoon dimension**: §13.8 G-7 이미 "31° swing buffer 의도, cartoon dimension" 명시. 실제 measurement geometry는 paper Methods/SI.
- **Q18 ground reference topology** (chamber wall / sample stage / virtual ground): paper Methods 영역. Figure는 grounded symbol만 (universal electrical reference) — topology 명시 시 schematic register 위반.
- **Q21 τ_d magnitude (orders of magnitude)**: §13.7 F-4 이미 "abstract time-constant separation, not literal" 명시. 정량값은 Fig 2/3 영역. F-4의 arrow visual 길이는 cartoon에서 arbitrary.
- **Q24 14s eye-flow cover vs body figure**: §2 visual story arc + §3.1/§4.1 reading flow는 **cover-figure / graphical-abstract** 가정 (single longest dwell Panel C 5s = cover convention). Body figure 모드 시 dwell budget 짧아질 수 있지만 figure 설계는 cover-mode anchor 유지.
- **Q25 §10 #3 inter-panel gap deviation, journal gate risk**: §10 이미 "intended cost for cover-feel goal" 명시. Journal submission 시 referee가 raise하면 cover-feel goal 재평가 단계, current decision은 deviation 유지.

이상 7개는 cartoon-register / scope-out 결정으로 figure 변경 없이 close. 잔여 critical 6개 (Q15/Q16/Q19/Q20/Q22/Q23)는 paper 실험 데이터 또는 §8 LOCKED 룰 챌린지 → user 입력 대기.

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

**Reading order**: (1) panel letter 'A' (좌상) → (2) 'Sulfur-rich polymer' bold label (lower-left, A-8 1st-tier identity) → (3) 4 DIB rings horizontal row (A-1, 좌→우 chain progression) → (4) polysulfide segments between rings (A-2, "linear copolymer" 확인) → (5) (S)_x composition label above (A-3, variable repeat tag) → (6) S₈ inset top-right (A-5, "before transformation") → (7) inv.vulc. dashed arrow S₈→Ring_c (A-6, "transformation" 화살표) → (8) methyl pair stubs at junctions (A-4, chemistry detail; 놓쳐도 OK) → (9) inter-arrow → B 진입.

- **A-1** 4 DIB benzene rings (high-low staggered horizontal row; ring R=0.26cm; 3 internal aromatic ticks each). **Role**: polymer "backbone" 시각 anchor; 4 rings = 충분 ensemble + **linear** topology (NOT crosslinked network) 명시; staggered row = visual interest, NOT branching
- **A-2** 3 internal polysulfide segments (linear DIB-polysulfide-DIB links between meta-position vertices, 120° apart; bivalent DIB chemistry constraint). **Role**: "S-r" (random sulfide repeat) 부분 시각화; 4 rings 사이 3 segments = linear copolymer (not crosslinked, 화학적 정확성)
- **A-3** `(S)_x` parenthesis composition label (single floating, centered above row; ref01 Zheng 2024 NComm idiom). **Role**: 'x' = variable repeat count (Panel B의 n=60-85과 binding); centered floating = "전체 chain의 composition tag"; reader가 A와 B를 mentally 연결
- **A-4** `\methylPair` quaternary C(CH₃)₂ junctions (6 internal DIB-polysulfide sites; gem-dimethyl from isopropenyl→isopropyl). **Role**: gem-dimethyl quaternary C from isopropenyl→isopropyl (DIB의 정확한 chemistry); 작은 stub = detail, narrative weight 낮음 (놓쳐도 OK)
- **A-5** S₈ ring inset (regular octagon polygon + 8 vertex 'S' atom letters + bold 'S₈' center label, top-right corner). **Role**: pre-polymerization S₈ source 분자; A의 "inverse vulcanization" 출처; top-right 위치 = "before transformation" 공간적 cue (좌→우 시간/반응 흐름)
- **A-6** dashed inverse-vulcanization arrow (S₈ → Ring_c 60° vertex). **Role**: S₈ ring → DIB chain transformation 명시; dashed = chemical reaction (literal bond 아님); §17 dashed semantic 중 "transformation"; specific vertex termination = "어느 원자에서 시작" 의미 부여
- **A-7** `cAmber!08` background wash ellipse (1.55×0.65cm hugging the row). **Role**: A의 narrative focus 묶음 (rings + chains); horizontal hugging = 좌-우 chain progression 강조; cAmber!08 = bulk polymer tone reference (C-L sheet과 같은 hue family)
- **A-8** inline labels ('Sulfur-rich polymer' bold + 'poly(S-r-DIB) linear copolymer' subtitle + 'inv. vulc.' italic). **Role**: 3-tier typography hierarchy — Strong bold (panel identity) + Mute italic (sub-identity) + small italic (annotation); subtitle의 "linear" 단어가 §8 invariant 강제

### §13.2 Panel B — 3 sub-regions

**Reading order**: (1) panel letter 'B' (좌상) → (2) 4 zigzag chains stacked vertically (B-1, n=60→85 위→아래 monotonic progression 인지) → (3) S₆₀ / S₇₀ / S₇₅ / S₈₅ endpoint labels at chain tails (B-2, composition coord) → (4) bottom axis arrow + 'Chain length, n' label (B-3, variable n 명시) → (5) inter-arrow → C HERO 진입.

- **B-1** 4 zigzag skeletal chains (10/14/18/24 atoms drawn; bond spacing 0.10cm, amplitude 0.08cm, atom r=0.025cm, bond w=0.5pt — R11 delicate). v6: chain row spacing compressed 0.75→0.60 (span 2.25→1.80; chain y = 7.90/7.30/6.70/6.10, center y=7.00). **Role**: **sulfur composition variation (wt%) visual sampling** (Q1 LOCKED: numbers = wt% S, NOT chain atom count); 4 samples (S60..S85) = sufficient monotonic progression; zigzag = sff skeletal chemistry convention; shared `\zigSChain` macro = A↔B chain identity binding (§13.9 cross-row). **Note**: drawn atom count (10/14/18/24)은 **artistic correlate** — longer drawn chain = qualitative "more S" 시각화; literal chain atom count 아님 (briefing §3.1 reader DO/DON'T 참조)
- **B-2** sample-name endpoint labels at terminal atoms (S₆₀ / S₇₀ / S₇₅ / S₈₅, cAmber!90 6.5pt; full 4-label set). **Role**: **sample names derived from sulfur wt%** (Q1 LOCKED): S60 = 60 wt% S sample, ..., S85 = 85 wt% S sample (per planning/sulfur_sample_selection_policy.md); subscript form은 sample naming convention (NOT atom count subscript). §8.8 LOCKED — S60..S85 composition labels는 B에만 허용 (Row 2 plot은 concept만); right anchor at terminal atom = chain의 "끝" 시각 정렬
- **B-3** bottom horizontal axis arrow + '**Sulfur content, wt%**' italic label (v8 Q1 fix; was 'Chain length, n'). **Role**: composition variable 명시; arrow = direction (60 wt% → 85 wt%, monotonic 보장); B-2의 sample-name labels (S60..S85)이 이 axis 위에서 wt% progression으로 읽힘

### §13.3 Panel C — 11 sub-regions (HERO #1, 5s dwell)

**Reading order** (split-half: LEFT real-space → RIGHT energy diagram; 5s total):
1. Panel letter 'C' (좌상) → 'localized traps' italic subtitle 위
2. **LEFT half first** (x=7.55..9.85): rectangular sheet (C-L1, amber gradient bulk film) → 3 chain hints inside (C-L2, polymer body identity) → 4 ● markers mixed shallow/deep (C-L3, trap distribution; **NOT segregated**)
3. 'poly(S-r-DIB) thin film' subtitle (C-L5, material identity)
4. Eye crosses to **RIGHT half** (x=10.50..13.80): Energy rotated axis label + E_C / mobility edge / E_V refs (C-R1)
5. shallow trap levels (C-R2, blue, near mobility edge) → 'shallow' label (C-R6 top)
6. deep trap levels (C-R3, red, much lower) → 'deep' label (C-R6 bottom)
7. ΔE_t^d annotation (C-R5, depth scalar 인지)
8. escape arrow from deep (C-R4, thermal release dynamic)
9. **Dashed leaders** binding LEFT ● sites ↔ RIGHT trap levels (visual "same trap, two views")
10. Eye descend toward Row 2 caption ("convergent evidence" 진입).

**LEFT half (real-space polymer, x=7.55..9.85):**
- **C-L1** rectangular polymer sheet (R22; 2.30×1.50cm; top→bottom amber gradient `cAmber!10` to `cAmber!38`) — medium-limit hit, SVG handoff deferred (§12.1). **Role**: bulk poly(S-r-DIB) thin film = Panel A/B 분자 chain의 macroscopic 형태 (zoom-out: 분자→bulk); amber gradient = figure-wide upper-left 광원 anchor (§9 LOCKED — 다른 panel gradient의 reference)
- **C-L2** 3 wavy chain hints inside sheet (varied opacity 0.85/1.0/0.85; varied line weight 0.50/0.55/0.50pt). **Role**: 폴리머 내부 chains 시각화 (Panel A/B individual chains의 bulk 포함 형태); varied opacity/weight = 깊이 perception (front-back layering); G-3 internal chain hints와 binding (poly material identity)
- **C-L3** embedded ● trap sites (v8: 2 shallow cBlue + 2 deep cRed filled dots; coordinates siteS1/S2/D1/D2 at chain peaks/junctions). **Role**: trap이 polymer 내부에 *공간 분포* 명시 — NOT spatially segregated (briefing §8.3 LOCKED); shallow + deep mixed in same matrix; chain junction에 위치 = chain defect 시각화. v8 carrier-neutral marker (was ●); §8.1 carrier-polarity note 참조
- **C-L4** top-edge white highlight (opacity 0.55) + right-edge cAmber shadow (opacity 0.45) — depth cues. **Role**: figure-wide light source anchor — upper-LEFT (briefing §9 LOCKED); 다른 panel(Panel G clip/polymer/electrode) gradient는 이 anchor와 방향 일치 필수
- **C-L5** 'poly(S-r-DIB) thin film' subtitle below sheet (italic 5.5pt cGray!70). **Role**: bulk material 정체성 명시 (chemistry 명명); A-8 'Sulfur-rich polymer' label과 binding (분자→bulk identity 동일)

**RIGHT half (energy diagram, x=10.50..13.80):**
- **C-R1** E_C / mobility edge (dashed) / E_V reference horizontal lines + 'Energy' rotated label + vertical axis arrow at x=10.50. **Role**: semiconductor band edge reference; mobility edge (dashed) = "delocalized vs localized" 경계, trap states는 이 아래; E_C / E_V 정량 값 없음 (cartoon register). **Sample regime LOCKED**: poly(S-r-DIB)은 **fully amorphous** (Q7 확인 2026-05-16) → Mott-CFO mobility-edge model 적용이 적절; semi-crystalline / dual-phase 가정 금지
- **C-R1b** Gaussian DOS overlay (Q8 추가, .tex L343-360 R15 기존): shallow Gaussian (cBlue!18 fill opacity 0.55 + cBlue!75!black 0.50pt border, σ=0.085, peak at y=7.49) + deep Gaussian (cRed!18 fill opacity 0.55 + cRed!75!black 0.55pt border, σ=0.18, peak at y=6.05). Energy axis 옆 (x=10.55부터 right로 0.28~0.32cm 너비)에 fill+outline. **Role**: poly(S-r-DIB) amorphous semiconductor의 **continuous Gaussian DOS** 표현 (Mott-CFO + Bässler disorder model); C-R2/R3의 horizontal lines은 이 distribution 안의 representative sample. Shallow 좁은 σ = tight localization; deep 넓은 σ = broader trap-depth distribution. F-2/F-3 Gaussian과 형태 echo (§13.9 Binding-1 강화)
- **C-R2** shallow trap levels (2 horizontal lines at y=7.55/7.35; v7 polish #7: line width 0.80→1.00pt; cBlue!80!black; v8: 1 cBlue ● on each level — carrier-neutral marker). **Role**: shallow trap = mobility edge 근처 좁은 ΔE↓; thermal release easy = fast detrapping; cBlue color = Panel F-2 shallow Gaussian / Panel G implicit과 binding (§13.9 Binding-1); ● polarity-neutral per §8.1; **2 lines = C-R1b Gaussian DOS 안의 sample** (NOT discrete 2-level; F-2 smooth Gaussian과 cross-check 일관)
- **C-R3** deep trap levels (2 horizontal lines at y=6.20/5.85; v7 polish #7: line width 0.80→1.00pt; cRed!80!black; v8: 1 cRed ● on each level — carrier-neutral marker). **Role**: deep trap = mobility edge에서 멀리 (큰 ΔE↓); thermal release hard = slow detrapping = long lifetime; cRed color = F-3 deep Gaussian + G-4 q_tr binding; ● polarity-neutral per §8.1; **2 lines = C-R1b deep Gaussian DOS 안의 continuous distribution sample** (Q8 LOCKED: NOT discrete 2-level; broader σ 인코딩 = wider trap depth spread)
- **C-R4** escape arrow from deep band → mobility edge (cRed!70 dashed 0.35pt; Boltzmann thermal release). **Role**: deep trap의 dynamic detrapping 표현 (정적 level 아닌 process); dashed = dynamic transition; §17 dashed semantic 중 "transition"; 길이 = activation energy 비례 (longer = harder). **Scope LOCKED (Q9)**: thermal Boltzmann release만 표현 — tunneling / hopping / field-assisted는 cartoon register clutter 우려로 scope 밖. Paper 실험이 위 4 mechanism 중 단일 (가장 basic) 가정에 맞춤; 추가 mechanism 필요 시 SI/Methods 영역
- **C-R5** ΔE_t^d depth annotation (cRed!75 double-headed arrow at x=13.55 spanning E_C → deep band bottom + label). **Role**: trap depth scalar (E_C - deep band 위치) 명시; double-arrow = magnitude (방향 없음); Δ 기호 = "차이" 명확화; reader가 deep의 "왜 retention 길다"를 이 visual로 인지
- **C-R6** 'shallow' / 'deep' band labels (bold 6.5pt sans, anchored east of each band). **Role**: trap species 명명; bold = primary identifier; east anchor = band의 우측 (read 방향 종료점); F-5 'Shallow'/'Deep' base labels과 typography + color binding (§13.9 Binding-1 닫음)

### §13.4 Row 2 cover-binding — 10 sub-regions (v7 split from 3, coord-explicit)

**Background layer (2):**
- **Row2-BG-wash** background tint: `\fill[cAmber!8, rounded corners=2mm] (-0.05, 0.05) rectangle (14.05, 4.55)`. **Role**: 4 panel (D/E/F/G)을 시각적으로 1 scene으로 결속; no hard panel borders (briefing §3 cover-binding mechanism #1)
- **Row2-BG-chains** 3 wavy chain hints (cAmber!22, line width 0.30pt, plot[smooth]) crossing horizontally at y ≈ 1.20 / 2.50 / 3.80 spanning x=0.10..13.90. **Role**: row 2 "floor" 의 polymer material identity — Panel C-L thin film chain hints과 visual binding (zoom-out: micro chain → macro bulk → measurement scene)

**Branching root + caption (2):**
- **Row2-Caption** 'convergent evidence — three independent probes of the same trap' (font: sffamily italic 6.5pt, text=cGray!75!black, anchor=south align=center) at (7.00, 4.92). **Role**: 의미 gate — divergent 화살표 geometry를 convergent semantic으로 invert; reader 2초 안에 "3 lines → 1 trap" 인식
- **Row2-Root** branchRoot coordinate (6.95, 4.85) — Panel C 하단 (x 6.95 = Panel C left edge + 0.05 inset) + inter-row gap (y 4.55 wash top to 5.00 Panel C bottom) 안에 위치. **Role**: 3 spoke의 공통 출발점; "동일 trap의 3 measurement modality" 시각적 anchor

**3 spokes (3):**
- **Row2-Spoke-Kinetic** (6.95, 4.85) → (1.73, 4.30) v7 (was 2.20). Style: Stealth 6pt×4pt arrow tip, cGray!65!black, line width=0.9pt. **Role**: C → D narrative spoke (kinetic modality); endpoint (1.73, 4.30) = Panel D 신 bbox 중심 위쪽
- **Row2-Spoke-ISPD** (6.95, 4.85) → (6.95, 4.32). Same style. **Role**: C → E↔F (paired ISPD) spoke; vertical (수직), E↔F 사이 boundary로 종료 → 두 panel 하나로 묶음
- **Row2-Spoke-Mechanical** (6.95, 4.85) → (12.20, 4.30). Same style. **Role**: C → G narrative spoke (mechanical modality); endpoint = Panel G 중심 위쪽

**3 modality labels (3):**
- **Row2-Label-Kinetic** 'kinetic' (font: sffamily italic 6pt, text=cGray!75!black, anchor=south, fill=cAmber!8, inner sep=1pt) at (4.34, 4.55) v7 (was 4.50). **Role**: kinetic spoke modality 명명; cAmber!8 fill로 BG-chains line 위에 punch (가독성 확보)
- **Row2-Label-ISPD** 'ISPD' same style at (6.95, 4.50). **Role**: ISPD paired spoke 명명; 두 panel(E+F) 공유 modality 명시
- **Row2-Label-Mechanical** 'mechanical' same style at (9.55, 4.55). **Role**: mechanical spoke modality 명명; G의 macro register와 connect

**Anti-chain mechanism note**: 3 spoke가 발산형 geometry이지만 reader가 convergent로 invert하는 메커니즘 = (a) shared origin (C HERO, 단일 source); (b) caption "convergent evidence" semantic 명시; (c) Panel C ↔ Panel F color match (shallow blue + deep red), 동일 trap 시각 echo. §8.7 forbids linear chain (D→E→F→G); 이 3중 메커니즘이 그 forbidden 강제.

### §13.5 Panel D — 5 sub-regions (iconic kinetic cartoon)

**Reading order**: (1) kinetic spoke 진입 (1.73, 4.30) → (2) equation $I(t)\sim t^{-n}$ 라벨 (mental model 주입) → (3) deep-rich 빨간 선 (위, less-steep) → (4) shallow-rich 파란 선 (아래, steeper) → (5) Debye dashed 우하단 (둘 다보다 아래 = non-Debye 증명) → (6) axis tip labels 확인 종료.

- **D-1** axis arrows Stealth-tipped (cGray!65 0.50pt) — v6: axis-top 4.10→3.40; v7: x-axis end 4.10→3.40 (width-normalized 4.45→3.45); tip labels '$\log I$' (y=3.20) / '$\log t$' (x=3.28). **Role**: log-log frame은 power-law를 직선으로 압축; tick 없이 arrow만 = M2 cartoon register (reader가 plot 분석 모드 진입 안 함)
- **D-2** 2 power-law straight slopes (v6: 0.80pt; v7 x-shrunk 0.803 anchored at axis origin 0.55) — deep-rich cRed!80 (0.67,3.30)→(3.28,1.55) above, shallow-rich cBlue!80 (0.67,2.80)→(3.28,0.55) below; diverge, NO crossing. **Role**: less-steep red = smaller n = deep trap = 느린 release = retention 길다; 두 라인 색 = C-R2/R3 shallow/deep band과 binding (trap population 종속 kinetics). **n ↔ trap depth model (Q20, planning/session_260427)**: Jonscher / Dissado-Hill universal dielectric response framework (Jonscher 1977 / Dissado-Hill 1984). Composition (S60..S85 = wt% S, Q1 LOCKED)이 trap density 변조 → n 직접 영향. 본 paper Fig 3에 **CvS n exponent**로 정량.
- **D-3** Debye dashed reference curve (v6+v7: cGray!70 0.65pt, steep bezier (0.77,3.35) ctrl→ (2.12,0.55); ends clearly below both power-law tails per §8.4) + thin straight leader (2.08,0.60)→(2.28,0.75) + 'Debye' label white fill. **Role**: "non-Debye tail" 주장의 시각적 anchor — 비교 기준 없으면 power-law 단독으로는 의미 없음. Debye exponential이 long-t에서 빠르게 떨어지고 power-law는 그 위에 있다는 visual proof
- **D-4** main equation label '$I(t)\sim t^{-n}$' (v7: (0.67,3.55) labelStrong, above axis top). **Role**: panel 진입 즉시 mental model 주입 — reader가 두 선을 "I(t)~t^-n 라는 가족 중 다른 n 값" 으로 읽음
- **D-5** curve identification labels (v7: 'deep-rich' cRed!75 (2.12,2.55) anchor=south + 'shallow-rich' cBlue!75 (2.52,1.45) anchor=south). **Role**: 각 곡선의 sample 정체 명시 — "sample이 어떤 trap 조성이면 어떤 곡선이 나오는지" 인과 binding

### §13.6 Panel E — 4 sub-regions (iconic ISPD-raw cartoon)

**Reading order**: (1) ISPD spoke 진입 (6.95, 4.32) — paired E↔F 묶음 인지 → (2) $V_s(t)$ y-label (좌상 회전) "raw measurement" 신호 → (3) 곡선 top-left (V₀ ≈ 3.20) → (4) 6 filled markers 따라 내려가기 (steep initial drop) → (5) 곡선 long tail (V_r ≈ 0.55 asymptote) → (6) $t$ x-axis 라벨 (linear t, NOT log) → (7) ISPD inter-arrow 우측으로 → F panel.

- **E-1** axis arrows Stealth-tipped (v6: axis-top 3.40; v7: axis origin 4.85→3.85, bbox 4.50..6.95→3.50..6.95 widened); tip labels '$V_s(t)$' rotated at (3.59,3.20) + '$t$' (v6.1: linear t-axis) at (6.57,0.35). **Role**: linear-t (not log) = stretched-exp fitting의 실제 좌표계; cartoon register는 D와 동일
- **E-2** linear-t stretched-exponential decay curve (cRed!70 0.80pt, 11 waypoints; β≈0.8, V_0=3.20, V_r=0.55, τ≈0.6). v7: x scaled 1.513 anchored at 3.85 → waypoints (3.96,3.20)→(6.73,0.79). **Role**: raw V_s 시간 도메인 measurement; concave-up shape = trap-mediated long tail (β<1); F의 g(E_t)는 이 곡선의 inverse-Laplace 같은 derived 산물. **Parameter values LOCKED arbitrary (Q11 확인)**: β=0.8 / V_0=3.20 / V_r=0.55 / τ≈0.6는 **cartoon illustrative values** (paper 실제 측정값 아님); 정량 fitting result는 Fig 2/3 또는 SI 영역. shape는 stretched-exp identity 유지, 수치는 figure scope 밖.
- **E-3** 6 ISPD markers (v7 polish #18: fill=cRed!50 — filled convention, was open). v7 marker x's scaled: (4.15,2.54)(4.61,1.79)(5.06,1.37)(5.51,1.11)(5.97,0.95)(6.42,0.84). **Role**: "data point" convention — 곡선은 fit, marker는 실제 측정; 6개 = 충분 density without crowding
- **E-4** paired ISPD inter-arrow → F + 'ISPD' label (E↔F paired transformation per briefing §6). **Role**: 두 panel을 single spoke (ISPD)로 묶어 reader에게 "같은 measurement 종류" 신호 — V_s raw → g(E_t) derived 변환의 시각적 명명. **Abbreviation expansion responsibility (Q12)**: figure 자체에는 "ISPD" 약어만 (다른 modality 'kinetic' / 'mechanical'은 일상어이므로 ISPD만 약어 status). **figure caption first-use에서 "ISPD (Iso-thermal Surface Potential Decay) measurement" 한 번 expansion 필수** — cover figure / standalone exposure 대비. paper introduction이 별도로 expansion 다뤄도 figure caption 책임 분리 권장 (asymmetric treatment 정당화: familiarity asymmetry).

### §13.7 Panel F — 5 sub-regions (iconic g(E_t) cartoon)

**Reading order**: (1) E의 ISPD inter-arrow에서 도착 (left entry) → (2) $g(E_t)$ y-label (좌상 north-west, "density of states" 신호) → (3) shallow Gaussian (좌, 파랑, 낮음) → (4) deep Gaussian (우, 빨강, 1.86× 높음 = "deep dominant") → (5) τ_d dashed 화살표 between peaks (시상수 분리) → (6) base 라벨 'Shallow' / 'Deep' (color confirmation; C-R2/R3 ↔ F-2/F-3 ↔ G-4 binding 닫음) → (7) $E_t$ x-axis 라벨.

- **F-1** axis arrows Stealth-tipped (v6: axis-top 4.10→3.40); tip labels '$g(E_t)$' top-left at (7.25,3.30) anchor=north west + '$E_t$' right at (10.35,0.50). **Role**: energy domain (E_t) + 상태 density (g) — D의 시간 domain과 dual; bimodal 형상이 즉시 "2 trap species" 신호
- **F-2** shallow Gaussian (cBlue!85 border + cBlue!25 fill, v6: peak y=1.50, x=7.45..8.95, 0.80pt). **Role**: narrow σ = 좁은 trap depth 분포 (얕은 trap이 비교적 균질); 낮은 peak height = 적은 state density
- **F-3** deep Gaussian (cRed!85 border + cRed!25 fill, v6: peak y=2.40 = 1.86× shallow height per §5 Q4, x=8.95..10.15, 0.80pt). **Role**: taller (1.86×) = "deep dominant" density 인코딩; wider σ = 깊은 trap이 broader spread; F의 hero element
- **F-4** τ_d double-headed dashed arrow between peaks (v6: y=2.55, was 3.55; cRed!70 0.55pt) + '$\tau_d$' label at (8.90,2.60). **Role**: 두 peak 사이 time-constant 분리의 abstract 표현; dashed = literal 거리 아님 (E_t 축 자체가 시상수 ↔ trap depth 관계의 derived); reader가 "shallow 빠른 release, deep 느린 release" 로 읽음
- **F-5** 'Shallow' / 'Deep' base labels (cBlue!75 / cRed!75). **Role**: figure-wide color convention 묶음 — Shallow=cBlue / Deep=cRed가 C-R2/R3 band ↔ F Gaussian ↔ G ● 셋 모두 흐름 (§8.6)

### §13.8 Panel G — 7 sub-regions (isometric mechanical scene)

**Reading order**: (1) mechanical spoke 진입 (12.20, 4.30) → (2) mount hatch + clip block (위 고정 지지) → (3) cantilever 매달려 내려옴 (amber gradient, polymer identity) → (4) 3 q_tr ● 빨간 markers (charge entity; C/F deep red과 binding) → (5) $q_{tr}$ label (우상, white fill로 강조) → (6) 폴리머가 LEFT로 휜 시각 인지 → (7) "Coulomb / repulsion" 빨간 화살표 + 라벨 (force vector — G의 hero claim) → (8) undeflected dashed (reference 기준) → (9) Δx 치수 (실제 displacement) → (10) air gap 치수 + 라벨 (clearance, 31° swing buffer 시각화) → (11) electrode (우, 금속 gradient) → (12) ground 심볼 + '(grounded)' 라벨 (reference potential 종료).

- **G-1** clip rectangle (top, 11.90..12.35; v7 y-shifted: 4.00..4.15→3.40..3.55; v5.1 gradient cGray!38!white→cGray!55!white per §9) + stub down to polymer + mount hatch at y=3.70 (was 4.30). **Role**: 'fixed support' 보편 기호; briefing §8.5 LOCKED — clip TOP, polymer 매달림 down
- **G-2** electrode block (**RIGHT** vertical, F1 shifted: 13.55..13.80; v7 height: 0.80..3.40 (was 0.80..3.80, height 3.00→2.60); v5 metallic gradient + left highlight opacity 0.50) + hatching 6 lines (v7 reduced from 7) to x=13.95 + 3-bar ground at x_center=13.675 + 'electrode' label (13.675,3.45) (v7 y 3.85→3.45). **Role**: Coulomb 척력의 target; grounded = reference potential (mutual induction 배제, 순수 Coulomb); metallic gradient = material identity (polymer organic vs metal inorganic)
- **G-3** polymer strip (v7: y-scaled 0.78 anchored at tip y=1.25 → L 2.75→2.15, root (12.25,3.40)/(12.00,3.40), tip (11.65,1.25)/(11.40,1.25); bezier ctrls (12.25/12.00, 2.62) and (12.05/11.80, 1.84); v5.1 gradient cAmber!22→cAmber!42 per §9; outline cAmber!80!black 0.70pt rounded 0.3mm) curved away from electrode; v5.1 internal: 2 chain hints (cAmber!65!black 0.30pt opacity 0.38; v7 y-scaled to (12.075/12.175, 3.33..1.31)). **Role**: bend LEFT = Coulomb REPULSION (같은 부호 척력) per §8.5; chain hints = poly material identity (Panel C-L thin film과 visual binding); cantilever 형태 = micro→macro 다리. **Quantitative model (Q15, planning/session_260427)**: F_clip = Q_clip × E_active (floating-clip protocol, Phase A grounded poling으로 Q_clip lock); Fig 1 G는 qualitative — 정량 model은 paper Fig 5 + SI Methods S0 (Coulomb-Maxwell framework)
- **G-4** 3 q_tr markers (v7 y-scaled: (12.10,2.93)/(11.95,2.23)/(11.75,1.52)). v8: $\ominus$ → ● filled red dot (carrier-neutral; q_tr label이 charge semantic 담당). **Role**: ensemble representation — 3 = "sufficient to illustrate"; 절대 count 아님; cRed = C/F deep red과 color-bind (deep trap이 macro bending 야기); ● polarity-neutral per §8.1
- **G-5** q_tr leader (12.22,2.93)→(12.35,2.93) + '$q_{tr}$' label white fill cRed!70. **Role**: trapped charge entity 명명; white fill = wash 위에서 가독성 확보 (다른 cAmber!8 punch와 달리 white로 강조)
- **G-6** Coulomb repulsion arrow (cRed!80 Stealth 0.7pt; v7 y 2.20→1.99: (11.95,1.99)→(11.10,1.99)) + 'Coulomb' (11.10,2.09)/'repulsion' (11.10,1.91) 2-line stacked. **Role**: G 가장 강한 visual claim — force vector + bold red text가 panel narrative ("거시적 발현")의 anchor; briefing §8.5 LOCKED: Maxwell attraction 화살표 금지, Coulomb-only
- **G-7** air gap dimension (F1: 0.575→1.425cm, ↔ arrow 12.125→13.55 at y=0.85, unchanged in v7) + 'air gap' inline label (12.84,0.85) anchor=center fill=cAmber!8; 'undeflected' dashed line (v7: 12.125,3.40→12.125,1.20) + label (12.15,2.30) (v7: y 2.70→2.30); Δx dim (11.525,1.10)→(12.125,1.10) unchanged. **Role**: 3개 dimension이 macro 기하 communicating — air gap (clearance, 31° swing buffer 의도) / Δx (실제 displacement) / undeflected (reference 기준선). Three-dimension idiom이 cantilever physics를 quantitative-feeling 없이 cartoon-grade로 전달

### §13.9 Cross-panel bindings (semantic + visual echo mechanisms)

Sub-region들이 panel 단위 enumeration이지만 figure narrative는 panel↔panel binding이 carry. 4가지 명시 binding:

**Binding-1 Color (Shallow=cBlue / Deep=cRed)** [LOCKED §8.6]
- **Endpoints**: C-R2 (shallow band lines) + C-R3 (deep band lines) ↔ F-2 (shallow Gaussian) + F-3 (deep Gaussian) ↔ G-4/G-5 (q_tr cRed markers, "deep dominant" implication)
- **Mechanism**: 동일 hue가 4 panel(C, D, F, G)에 흘러 reader가 "같은 trap species"로 식별
- **Forbidden**: §9 color drift — Shallow→cBlue 외 hue, Deep→cRed 외 hue 금지

**Binding-2 Charge entity (● marker)** [implicit]
- **Endpoints**: C-L3 (polymer matrix ● sites) ↔ C-R2/R3 (energy-level ●) ↔ G-4 (q_tr 3 markers inside polymer)
- **Mechanism**: 동일 ● glyph + cRed/cBlue 두 representation (real-space + energy diagram + macro probe)
- **Reader inference**: "Panel C 안에서 본 trap을 G에서 macro scale로 다시 본다"

**Binding-3 E↔F derivation (ISPD pair)** [explicit via inter-arrow]
- **Endpoints**: E-2 (V_s(t) raw, time domain) → ISPD inter-arrow (E-4) → F-2/F-3 (g(E_t) derived, energy domain)
- **Mechanism**: 단일 spoke from C (ISPD modality)가 두 panel 묶음; 수학 mental model = inverse-Laplace transform (V_s decay → trap density)
- **Visual cue**: ISPD label이 E와 F 사이 (x=7.00, y=2.35); spoke 자체도 E↔F boundary (x=6.95)로 끝남

**Binding-4 D↔F kinetic↔density coupling** [implicit, label-driven]
- **Endpoints**: D-5 ('deep-rich' / 'shallow-rich' curve labels) ↔ F-3/F-2 (deep Gaussian dominant / shallow Gaussian smaller)
- **Mechanism**: D의 less-steep 'deep-rich' line (smaller n) ↔ F의 taller 'Deep' Gaussian (higher density). 두 panel 모두 "deep trap dominant" 동일 sample 합의
- **Anti-confusion**: 두 panel이 다른 domain (time-power vs energy-density)이지만 same sample → 같은 trap 분포가 D의 n과 F의 peak height 둘 다 결정

**Row 1 internal bindings (A → B → C 좌→우 zoom-progression):**
- **A ↔ B chain identity** [shared macro]: 동일 `\zigSChain` macro — A에서 polysulfide 분자 detail 보여주고 B에서 chain length 변화 sampling (n=60..85). Reader가 같은 chain의 "다른 길이" 인식.
- **A-3 (S)_x ↔ B variable n** [composition tag]: A의 `(S)_x` label에서 'x' = B의 'n' (chain monomer 수); A는 generic chemistry, B는 specific length quantization.
- **A/B ↔ C-L material identity** [amber tone]: cAmber!8 wash (A) + cAmber chains (B) + cAmber gradient sheet (C-L) — 동일 hue family가 "분자 (A) → length variation (B) → bulk thin film (C-L)" zoom-out 흐름 시각화.
- **A → B → C HERO eye-flow** [3-zoom narrative]: A "재료 식별" 1s → B "분자 heterogeneity" 1s → C "trap landscape" 5s dwell (§2 visual story arc). 좌→우 horizontal progression = "분자 단위 → bulk 단위 → trap 단위" mental zoom.
- **B-3 'Chain length, n' axis ↔ C-L sheet** [discrete→continuous]: B의 discrete 4 chains이 C-L의 continuous bulk sheet으로 압축 (ensemble→bulk averaging mental model).
- **C-L ↔ C-R within Panel C** [split-half binding]: C-L의 4 ● sites와 C-R의 4 trap levels이 동일 trap 분포를 2 representation (real-space + energy diagram); §8.3 LOCKED — dashed leaders가 site↔level 직접 binding (visual proof: "같은 trap이 두 그림에 나타남").

**Cross-row bindings (Row 1 → Row 2):**
- **C-L ↔ G-3 chain hint** [poly identity gloss]: poly chains inside polymer body — C-L sheet의 3 chain hints이 G cantilever 안 2 chain hints로 echo. 같은 material identity convention (briefing §9 material-identity exception).
- **C-L3 ● sites ↔ G-4 q_tr markers** [charge entity]: C-L 내부 ● trap sites + C-R level ● + G의 q_tr ● = 동일 charge entity의 3 visualization. cRed marker가 모두 흐름 (§13.9 Binding-2).
- **C HERO ↔ Row 2 all** [narrative root]: 3 spokes from C는 Row 2 root; Row 2의 D/E/F/G 모두 "C에서 본 trap의 3 measurement 증거". §4.1 anti-chain mechanism의 3-fold defense 핵심.
- **C-R6 'shallow'/'deep' labels ↔ F-5 'Shallow'/'Deep'** [explicit binding]: 동일 단어 (only case different) + 동일 color → reader가 "C에서 본 trap species가 F에서 다시 나타남" 즉시 인식.

**Binding 검증 chart** (다음 dogfood/critique에 reference):

| Pair | Type | Mechanism | LOCKED |
|---|---|---|---|
| **Row 2 internal** | | | |
| C ↔ F | color | shallow blue / deep red | §8.6 |
| C ↔ G | charge | ● markers cRed | §8.5 + §8.6 |
| E ↔ F | derivation | ISPD inter-arrow | §6 |
| D ↔ F | kinetic-density | deep-rich ↔ deep peak | §8.7 (anti-chain) |
| **Row 1 internal** | | | |
| A ↔ B | chain identity | shared zigSChain macro | §13.2 B-1 |
| A-3 ↔ B | composition tag | (S)_x generic ↔ wt% specific (S60..S85) | §8.8 + Q1 |
| A/B → C-L | material zoom-out | cAmber tone + chain | §8.2 |
| A → B → C HERO | eye-flow | 좌→우 1s + 1s + 5s | §2 visual story arc |
| B-3 ↔ C-L | discrete→bulk | n axis → continuous sheet | implicit |
| C-L ↔ C-R | split-half | 4 ● sites + 4 levels | §8.3 + dashed leaders |
| **Row 1 → Row 2** | | | |
| C-L ↔ G-3 | chain hint | poly identity | §9 material-identity 예외 |
| C-L3/C-R ↔ G-4 | charge entity | ● markers cRed | §8.5 + §13.9 Binding-2 |
| C-R6 ↔ F-5 | explicit label | 'shallow'/'deep' twin | §8.6 + Binding-1 |
| C HERO → Row 2 | narrative root | 3 spoke source | §3 + §4.1 |

### §13.10 Totals + active iteration map

**Total sub-regions**: 53 (A:8 + B:3 + C:11 + Row2:10 [v7 split, was 3] + D:5 + E:4 + F:5 + G:7).

**Active iteration target** (post-v7, 2026-05-16):
- (none — all panels at stable point after v5/v5.1/v6/v6.1/v7 closure)

**Recently iterated (v5–v7, 2026-05-15..16)**:
- v5/v5.1 (Panel G F1 polish): electrode shift +0.85cm, air gap 0.575→1.425cm, metallic + polymer gradients, light-source upper-left LOCKED, polymer internal chain hints (Gemini #2/#3/#4 adjudication)
- v6 (D/E/F drawing quality): D lines separated no-cross + Debye redrawn, E S-shape, F peaks lowered, D/E/F axis-top 4.10→3.40, B chain spacing 0.75→0.60
- v6.1 (Panel E linear-t): x-axis log t→t + linear-t stretched-exp curve
- v7 (Row 2 width normalization + Panel G compression):
  - D bbox 0..4.45→0..3.45 (x-shrink 0.803); E bbox 4.50..6.95→3.50..6.95 (axis origin 4.85→3.85, x-widen 1.513); F/G x unchanged → all 3.45cm wide
  - G polymer y-scale 0.78 anchored at tip; L 2.75→2.15; clip + mount + electrode shifted/shortened to match
  - Spoke endpoint to D (2.20→1.73), 'kinetic' label (4.50→4.34), Panel E letter (4.55→3.55)
  - Polish #7: C-R2/C-R3 trap line 0.80→1.00pt
  - Polish #18: E markers fill=white→cRed!50 (filled convention)

**Stable / minimum iteration**:
- Panel A 전체, Panel C 전체 (C-R borders 1.00pt now per §10 mechanism tier), Row2 cover-binding

**Known iteration-debt items** (remaining):
- #17 dashed-line semantics (Debye D-3 + escape C-R4 + inv.vulc. A-6 + leaders): kept as-is — distinct semantics, consolidation would lose information
