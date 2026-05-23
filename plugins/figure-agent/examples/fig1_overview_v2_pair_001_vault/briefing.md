# Briefing — fig1_overview_v2_pair_001_vault

> **Genre**: Nature Communications **main-text Figure 1** — clean white-background convention. NOT a cover / graphical abstract scene. (2026-05-22 redirect: prior cover-scene framing dropped because NC main-text Fig 1 effectively never uses background washes.)
> **Pilot pair**: `fig1_overview_v2_pair_001` / **Arm**: vault
> **Design snapshot SHA**: `fa7a6d9ff7890a440ca3471995acf8145c47001a996dbd8bf2c428b363d8f7b7`
> **Vault query**: 966e2e89-5c8a-41ea-a11f-658c99c3d037 (approved_only, proposed_records_allowed=false)
> **Vault state**: degraded_mode=true — chroma_v2 absent (text/image/scaffold/style branch indexes all absent)

---

## §1. Figure 정체성 + 30초 viewer impression

**정체성**: Nature Communications **main-text Figure 1**. 흰 배경 (no figure-wide wash, no Row wash, no Panel wash, no wavy chain hint background). Result-table 또는 plot-grid 인상은 여전히 anti-goal — 측정 결과 plot은 *iconic cartoon* 압축, schematic-illustration이 시각 무게 다수. 단 cover-scene cohesion cue는 사용 금지: 1 figure = 6 self-contained panel on clean white, panel-letter typography(a/b/c bold 8pt)가 panel 식별의 유일한 cue. Row-binding은 캡션 텍스트와 spoke arrow 기하학으로만 carry. (2026-05-22 redirect.)

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
  - Tick 수치 **없음** (다만 NC Figure 1 데이터 재현성 감각 구현을 위해, 패널 D/E/F 각각에 정량적 숫자 라벨이 배제된 2~3개의 미세 눈금선(Tick marks) 및 곡선 상의 대표 측정 데이터 산포도(Scatter points, 3~4점 수준) 추가는 허용하여 Fig 3의 본격적 정량 플롯 영역 침범을 회피하면서 신뢰성 보강)
  - Curve shape 자체가 message
  - Plot이 *icon-sized*: reader가 *plot처럼 분석*하지 않게
- **Schematic panel (A / C / G)**: scene dominant. Detail density 비례적으로 높음.
- **B**: hybrid. Skeletal chains with conceptual axis arrow (axis frame 없음, 단 S60/S75/S85 정렬에 한해 수치 없는 미세 tick mark 3개 허용 — D/E/F의 "수치 없는 Tick marks" 허용 convention을 Panel B 단일 axis arrow에 일관 적용; tick 높이 ≤0.06cm, line width ≤0.30pt, cGray!60 stroke, 수치 라벨 부착 금지). [briefing relax R1, 2026-05-23]

**Row 2 binding mechanism (NC main-text Fig 1 convention — no background wash)**:
1. ~~Shared faded polymer matrix background underneath Row 2~~ **REMOVED 2026-05-22**: NC main-text Fig 1은 컬러 wash 미사용 관행. Row 2 결속은 spoke arrow geometry + Row 2 caption + panel-letter 위치만으로 carry.
2. No hard panel borders Row 2 — clean white-background visual continuity.
3. *3-spoke branching arrow from C → {D, E↔F, G}* with modality labels (§4). 이 arrow + caption이 Row 2 unity의 유일한 cue.

**M2 baseline downgrade**: cover-scene cohesion cue (faded chain-hint wash, cAmber tint, Row band) 전부 anti-pattern. M2 = "no per-panel border, plain white background, panel-letter typography hierarchy carry the panel boundary".

P-B (isometric on D/E/F) + P-C (silhouette inset on Row 2 panels)는 **거절** (§9). 위 새 M2 baseline에서 P-A (3-spoke branching)만 살아남음.

---

## §3.2 Setup-context icons on Row 2 (v8.4 NEW)

**Problem solved**: Pre-v8.4 Row 2 had register asymmetry — G was a full
isometric mechanical scene (electrode + cantilever + air gap + ground), but
D/E/F were context-less iconic plots. The "convergent evidence — three
**independent** probes" caption (Row2-Caption) was carried entirely by text;
reader had no visual anchor for "3 different apparatus measure same trap."

**Decision**: Add 2 mini setup icons (NOT 3) — Panel D gets a kinetic
measurement icon, E↔F share one ISPD apparatus icon (per §6 paired ISPD;
F is derived from E so they share apparatus). G already shows its full
setup, so no addition.

**Locked constraint set (v8.4):**

- **Size cap**: ≤ 0.5cm × 0.5cm bbox per icon. Hard upper bound. Larger
  defeats §1 anti-goal "Fig 2/3 in disguise."
- **Color**: monochromatic — `cGray!75!black` stroke only, NO fill, NO color.
  Apparatus icons are *referential*, not part of figure-wide color binding.
- **Line weight**: ≤ 0.30pt (reference tier per §10 3-tier line weight ladder).
- **Position**:
  - **D-6** (kinetic icon): inside Panel D bbox, top-right corner near
    `(3.20, 3.30)` (just under axis-tip `\log I`).
  - **E↔F shared (E-5/F-6)**: in the **inter-panel gap** between E and F,
    centered around the existing ISPD inter-arrow location at approximately
    `(7.05, 2.55)`. Sits above the E-4 ISPD inter-arrow label or inline with
    it as a glyph extension.
- **Allowed glyphs** (kept iconic, no realism):
  - Kinetic D-6: 2 horizontal terminal lines + a circle (current-source
    symbol `⊙` or simple constant-current schematic) + thin 1-segment lead
    to a sample slab. NO labels, NO unit, NO ground.
  - ISPD shared: corona-like needle pointing down + thin sample slab + small
    Kelvin probe rectangle hovering above. NO labels.
- **FORBIDDEN**:
  - Apparatus larger than 0.5×0.5cm (would tilt toward Fig 2/3 register).
  - Color fill (would compete with shallow/deep blue/red color binding §13.9).
  - Apparatus labels beyond the existing modality words (kinetic / ISPD /
    mechanical) on the spokes.
  - Quantitative annotation (V values, current values, distances).
  - Light-source gradient on icons (apparatus is purely schematic; gradients
    are reserved for material-identity cues per §9 light-source convention).
- **Reading-flow expectation**: setup icons read at the *peripheral vision*
  level only — reader recognizes "there is an apparatus here" without
  parsing the apparatus details. If reader has to dwell on icon to read it,
  icon is too detailed.

**Anti-violations to monitor in next dogfood:**

- Icon overlapping curve / data marker → re-position to corner.
- Icon read as 5th plot element (curve / marker / label / axis / icon) →
  reduce stroke weight or move further into corner.
- Setup icon implying quantitative measurement (e.g., voltmeter reading
  number) → strip detail.

---

## §3.3 Row 2 size hierarchy verification gate (v8.5 NEW, v8.6 SUPERSEDED by §6 Option α restructure)

**v8.6 status:** The "G is heavier than D/E/F" asymmetry that motivated §3.3 has been
*structurally* dissolved by the v8.6 Option α 3-column restructure (§6). All 3 columns
(D / E / F) now share the same internal pattern: apparatus zone on top + result zone on
bottom. G's old isometric-scene register is no longer an outlier because every column
has an apparatus zone. The §3.3 gate is preserved below as ARCHIVED reference but its
escalation triggers (a/b/c/d) are now empty by design.

**Archived (pre-v8.6) §3.3 verification gate — kept for cross-reference:**

**Problem statement**: §5 Hero hierarchy locks "Row 2 = evidence radiation,
4 panels equal." But G inherits an isometric mechanical scene register (clip
+ polymer + air gap + electrode + ground), which is structurally heavier than
D/E/F's iconic cartoon plots. Pre-v8.4, G was visually dominant Row 2 element
— effectively a "second hero" within Row 2 → §5 violation in practice.

**Decision history**:
- v8.4 attempt: add mini-icons (≤ 0.5cm) to D/E/F per §3.2 to lift the
  *apparatus visual claim* on the iconic-plot side. Outcome: helped but did
  not close the gap — G still felt heavier than D/E/F.
- v8.5 closure (user directive 2026-05-16: *"G가 메인 피겨가 아니라
  evidence 중 하나이므로 너무 안 크게"*): strip G of decorative elements
  ('undeflected' reference line, Δx dimension, '(grounded)' parenthetical)
  to bring G's visual weight down to D/E/F-equivalent. *No size rescale* —
  G keeps current bbox; only ornament density reduced.

**Locked verification gate (apply at every Row 2 dogfood / critique pass):**

1. **Element count audit**: G should have ≤ 8 distinct visual elements
   post-v8.5: (1) clip block + mount hatch, (2) polymer cantilever + chain
   hints, (3) 3 q_tr markers + leader + label, (4) Coulomb arrow + 2-line
   label, (5) electrode block + hatching + ground symbol + 'electrode' label,
   (6) air gap dimension + label, (7) shared Row2-BG wash, (8) mechanical
   spoke entry. Anything beyond this list reopens the §5 violation risk.
2. **Visual-weight parity check**: when reviewer scans Row 2 in ~3s, no
   panel should "pop out" first. If G consistently catches eye before
   D/E/F, hierarchy gate FAILS → escalate by either (a) further G strip,
   (b) D/E/F mini-icon enlargement to 1.0cm cap, (c) Option D pivot.
3. **Anti-Option-D rule (LOCKED)**: making G bigger or moving G to "hero"
   position is FORBIDDEN. G is one of 3 evidence panels per the paper's
   v9.7 charge-trap-centered framing (NOT actuation showcase). Option D
   pivot reverses paper narrative.
4. **Anti-G-removal rule**: G cannot be deleted — the "macroscopic probe"
   modality is one of the 3 convergent evidence lines (§8.7). Mechanical
   evidence requires *some* physical-setup visualization (other 2 modalities
   are derived plots, but mechanical evidence is inherently a setup +
   observation pair).
5. **Setup-icon escalation gate**: if §3.2 mini-icons read as "noise" rather
   than "apparatus" in human dogfood, escalate icon size cap to 1.0cm but
   keep monochrome + stroke-only constraint to preserve cover-feel.

**Active escalation triggers (reopen this section)**:
- Reviewer feedback: "G feels like the main result"
- Reviewer feedback: "D/E/F icons are illegible / look like data markers"
- Cross-figure check: Fig 5 mechanism schematic redundant with Fig 1 G
  (if so, simplify Fig 1 G further toward "result-only" iconic register)

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
| 4 | Scan B: 3 representative zigzag chains (S60/S75/S85, endpoints + middle) + axis 'Sulfur content, wt%' | 1s | "sulfur composition variable, monotonic wt% progression" 인식 |
| 5 | Inter-arrow B → C horizontal trigger | 0.3s | "→" 두 번째 arrow = bulk material로 또 한 번 zoom-out |
| 6 | Panel C HERO dwell (split-half) | **5s** | C-L sheet (real-space) + C-R energy diagram + shallow/deep band + ● markers + dashed leaders + ΔE_t depth |
| 7 | Descend toward Row 2 via caption | 0.5s | "convergent evidence" caption 시작 → §4.1 Row 2 flow 진입 |

Total ~9s for Row 1 (A 1s + B 1s + C 5s + transitions 1.6s + descend 0.5s).

**Zoom-out mechanism — 3-step molecular→bulk progression**:

1. **A: molecular detail** — chemistry-specific (DIB ring + polysulfide + S₈ + isopropenyl methyl pairs). Reader가 "재료 분자 구조" 식별. cAmber!8 wash ellipse가 ring+chain 묶음.
2. **B: sulfur composition sampling** — concept-figure overview: 3 representative chains shown (S60/S75/S85 = endpoints + middle of the actual 5-sample paper set S60/S70/S75/S80/S85, 60/70/75/80/85 wt% S). Same `\zigSChain` macro로 A의 분자 detail이 composition variable로 abstract. Reader가 "황 함량이 다른 sample이 여럿 존재 + 범위는 S60..S85" 인식 (Q1 LOCKED: numbers = wt%, NOT atom count; full 5-sample dataset belongs to Fig 2~).
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
- "D의 두 선이 같은 sample이야?" → D-5 'high n' (sulfur polymer) / D-6 'low n' (control, e.g., PI) **다른 sample** — paper hero claim 의 cross-sample comparison (§8.4 framework + 실측 데이터 260504_sulfur_rh25 + 260429_PI_control).
- "왜 E와 F만 가까이 붙어있어?" → §6 paired ISPD 명시; spoke-ISPD가 vertical인 이유는 E↔F 쌍 결속

---

## §5. Hero hierarchy mechanism (시각적, NOT semantic) — v8.6 Option α restructure

| 메커니즘 | Panel C | Row 2 Col 1 (kinetic) | Row 2 Col 2 (ISPD-paired) | Row 2 Col 3 (mechanical) |
|---|---|---|---|---|
| 면적 | 1.5× width | equal (~4.5cm) | equal | equal |
| Internal structure (v8.6) | scene dominant | apparatus zone (top) + result zone (bottom) | apparatus zone (top) + V_s + g(E_t) stacked (bottom) | apparatus zone (top, baseline) + result zone (bottom, active) |
| Color saturation | deep-red strong + shallow-blue strong | mid (deep-red + shallow-blue power-law) | mid (cBlue + cRed bimodal) | mid (apparatus mono cGray + result cAmber polymer + bold cRed Coulomb) |
| Detail density | maximum | apparatus icon + 2-line plot | apparatus icon + V_s decay + bimodal Gaussian | apparatus (PSU + neutral fixture + light Maxwell baseline) + result (bent + Coulomb + q_tr) |
| Position | Row 1 우측 dominant | Row 2 left | Row 2 center | Row 2 right |

Result: Panel C *시각적 hero*; Row 2는 *3 columns of evidence*로 평등 분포 — modality count (3) = column count (3). 각 column 내부 "apparatus (위) → result (아래)" 동일 register pattern. **Pre-v8.6 4-panel asymmetry (D/E/F = plot, G = scene) 폐기.**

---

## §6. Per-panel ROLE (v8.6 Option α restructure — Row 2 panel→column re-mapping)

**Row 1 (unchanged):**

| Panel | Narrative role | Aesthetic register |
|---|---|---|
| A | 재료 identity — poly(S-r-DIB) primary microstructure | schematic (chemistry) |
| B | 분자 heterogeneity — variable sulfur composition (S60..S85 wt% samples) | hybrid (skeletal + conceptual axis) |
| C | **HERO #1** — trap landscape (LEFT real-space + RIGHT energy diagram) | schematic dominant (scene) |

**Row 2 (v8.6 RESTRUCTURED — 4 panels → 3 columns; each column has apparatus zone on top + result zone on bottom):**

| Column | ID label | Narrative role | Apparatus zone (top) | Result zone (bottom) |
|---|---|---|---|---|
| 1 | **D** (retained letter for caption continuity) | Kinetic evidence | MIM stack + SMU + ground | I(t)~t⁻ⁿ absorption-current plot (high-n red sulfur + low-n blue control + Debye dashed reference) |
| 2 | **E** (retained letter; ISPD-paired internal split via short arrow) | ISPD-paired evidence | corona needle ▽ + Kelvin probe ▭ + thin-film slab | V_s(t) decay (top sub-zone) + g(E_t) bimodal Gaussian (bottom sub-zone) — stacked within column |
| 3 | **F** (was G; letter renamed to maintain alphabetical Row 2 flow) | Mechanical evidence | Power supply (V_active source) + 2 leads + neutral cantilever fixture + electrode (rest state) + **Maxwell attraction baseline** (light pink, polymer→electrode direction) | Bent cantilever (active state) + 3 q_tr ● markers (deep red) + **Coulomb repulsion** (bold red, electrode-away direction) — Coulomb WINS against Maxwell baseline |

**v8.6 letter re-mapping rationale:** old D/E/F/G (4 panels) → new D/E/F (3 columns). Old E+F (ISPD raw + derived) merge into single column E with internal vertical split. Old G (mechanical scene) → new column F. Caption labels (A..F) form continuous 6-panel alphabet without gap.

E column internal split is *paired ISPD transformation* (V_s raw → g(E_t) derived) — single spoke from C drops into column top, internal short arrow signals raw→derived transformation.

**Pre-v8.6 archived (DO NOT reintroduce without §3.3 escalation gate trigger):**
- 4-panel D/E/F/G horizontal layout
- G as standalone full-scene panel (asymmetric register with D/E/F plots)
- v8.4 mini setup icons (≤0.5cm peripheral) — superseded by proper apparatus zones

---

## §7. Current .tex state vs design target — ALIGNED (post-v8.4 Row 2 setup-icons + Panel B dividers, 2026-05-16)

v5/v5.1/v6/v6.1/v7 → v8.2 (IoU polish) → v8.3 (briefing-grounded audit) → v8.4 (Row 2 register asymmetry closure + Panel B sample boundary) 거치며 briefing 의도와 `.tex`가 정렬됨. 잔여 deferred item만 active.

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
8.4 **CvS absorption-current framework (LOCKED, paper-data-grounded 2026-05-20)**: I(t) ~ t⁻ⁿ measured under **constant DC voltage** (absorption current, Schweidler 1907 original framing — NOT depolarization). Sample 간 n 차이는 **trap accumulation rate**:
- **황고분자 (paper hero, "trap-rich")**: n ≈ 0.85 (S60-S75 range 0.65-0.95) → steep I(t) decay = 유전분극 이후에도 trap이 계속 쌓이며 I 지속 감소 (R 증가).
- **PI control**: n ≈ 0.55-0.60 → less steep = 약한 trap accumulation.
- **PDMS control (예상)**: n ≈ 0-0.2 → nearly flat = trap 거의 없음, 초기 polarization 후 I 평탄.

**n 클수록 trap capability 강함** (within this sample set; corroborated by ISPD g(E_t) bimodal + mechanical bending). **Hero claim**: 황고분자가 기존 절연/유전 폴리머 대비 trap 성능 우월 = 3-line convergent evidence 의 첫째 line.

**Reference curve = Debye exponential** (single-relaxation, Jonscher universal dielectric response framework 1977): I(t) ~ exp(-t/τ). Power-law tail은 항상 Debye보다 long-t 에서 위 = 정의적 (heavy-tail vs exponential).

**실측 데이터 출처**: `/Users/choemun-yeong/workspace/ResearchOS/02_Surfur_Polymer/저항 측정/260504_sulfur_rh25/results/data/selected_samples.csv` (k=19 rolling median + rlm MM-estimator fit, R²>0.99). 본 paper Fig 3에서 CvS n exponent + ISPD trap distribution 정량.

**Reviewer challenge 대비**: (a) trap vs Maxwell-Wagner vs dipolar 분리 → ISPD g(E_t) discrete distribution evidence; (b) Jonscher universality 일반화 challenge → 본 sample set 내 n 차이 정량 강조 + 3-line convergence; (c) fair control → sulfur-poor copolymer 비교 추가 권장.
8.5 Column F (was Panel G — mechanical evidence column post-v8.6): Cantilever clip on **TOP**, polymer hanging down. **v8.6 Maxwell-vs-Coulomb contrast amendment (formerly "Maxwell forbidden" pre-v8.6):**

- **Apparatus zone (top of column, rest state):** Maxwell attraction arrow ALLOWED — depicted as light pink (`cRed!35!white`, dashed, thin 0.40pt) arrow pointing FROM neutral polymer TOWARD electrode. Label: "F_Maxwell (image/induced attraction, baseline)" italic 5.5pt cGray. Polymer is rendered in *pale* tone (cAmber!18..30, opacity 0.6) and *undeflected* (straight, no bend) to signal "neutral, no trapped charges yet." This zone establishes the *attractive baseline* — what would happen if there were NO trapped charges. Power supply + electrode + neutral fixture set up the field, Maxwell attraction is the unavoidable consequence.
- **Result zone (bottom of column, active state):** **only Coulomb repulsion** arrow — bold red `cRed!80!black` solid 0.7pt, electrode-away direction (polymer LEFT). NO Maxwell arrow in this zone (would dilute novelty cue). Polymer rendered in *saturated* tone (cAmber!22→cAmber!42 gradient, current convention) and *bent* (the actual signature). 3 q_tr ● markers (deep red, polarity-same as electrode). Result zone narrates: "trapped charges drive net Coulomb repulsion that WINS against the apparatus-zone Maxwell baseline."

**Maxwell-vs-Coulomb contrast convention (v8.6 LOCKED):** when both forces are shown across zones, Maxwell = light/secondary (cRed!35 dashed thin), Coulomb = bold primary (cRed!80 solid). Color tier signals which force wins. Color asymmetry IS the novelty argument — Coulomb thicker/darker = "Coulomb dominates."

**Justification for amendment (v8.6):** the pre-v8.6 "Maxwell forbidden" rule (design.md v2.2 §2.3, briefing §8.5 pre-v8.6) was intended to keep Fig 1 G simple. But hiding Maxwell makes Coulomb read as "just an arrow" without context — reader cannot tell why Coulomb is novel. The "Coulomb wins AGAINST baseline Maxwell" tension is the paper's actual claim per planning/session_260427_mechanism.md (F_clip = Q_clip × E_active vs F_Maxwell ∝ E²). Apparatus-vs-result zone split (v8.6) is the natural place to show this tension without cluttering the result. Fig 5 still owns the full mechanism (7-phase + Phase D snapshot); Fig 1 Column F now shows the macro-probe identity AND the force-tension at cartoon level.

**Anti-violation rules:**
- Maxwell arrow in result zone (alongside Coulomb) → FORBIDDEN; collapses the contrast.
- Both arrows equal weight → FORBIDDEN; color tier discrimination required.
- Coulomb arrow in apparatus zone → FORBIDDEN; apparatus is the *baseline before trapping*, no Coulomb because no q_tr.
- Quantitative force values (e.g., "F_Coulomb = 12 nN") → FORBIDDEN; Fig 1 is qualitative.
8.6 Panel C ↔ Panel F color-consistent (bimodal: blue Shallow / red Deep).
8.7 **Branching arrow physics constraint**: 3 spoke from C **must** match the 3 evidence lines in design.md §3.2 (kinetic / ISPD / mechanical). No new evidence line, no missing line. Spoke 순서 + label은 measurement modality, NOT causation chain — physics는 *3 independent measurements of same trap*, *not* causation chain D→...→G.
8.8 Composition labels (S60 / S70 / S75 / S80 / S85 = **sulfur weight-percent sample names**, Q1 LOCKED — NOT chain atom count)은 **Panel B에만** 허용. Row 2 plot panel은 concept-based only ("**low n**" / "**high n**" — 2026-05-20 framework rewrite; 이전 "shallow-rich" / "deep-rich" 명명은 depolarization-framework 오인 산물, **DEPRECATED**). Numbers 60/70/75/80/85 refer to wt% S per planning/sulfur_sample_selection_policy.md (5 samples in paper; **Panel B shows 3 representative: S60/S75/S85** = endpoints + middle, concept-figure visual clarity per v8.7 iter1 user-confirmed restructure). Full 5-sample dataset belongs to Fig 2~ (quantitative panels). Drawn chain atom counts (10/18/24 in B-1) is artistic correlate only.

---

## §9. Forbidden (aesthetic side — NEW)

- **Plot grid feel** (4 panel axis-box equally spaced) — anti-goal of M2.
- **Axis frame** on D / E / F (axis arrow + minimal label만 허용).
- **Tick 수치 라벨** on Row 2 plot panel (Fig 3 영역 침범. 단, 수치 라벨이 없는 순수 Tick marks와 소규모 scatter 포인트 추가는 제외).
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
- **Panel B chain length monotonicity 위반 금지**: 표시된 3 representative sample (S₆₀ < S₇₅ < S₈₅) 의 drawn atom count 순서가 위→아래 monotonic increase로 시각화. 순서 뒤바뀜 / 비-monotonic 변형 금지 (chain length variable이 ordering임을 깸). 실제 paper 전체 sample 집합은 5개 (S60/S70/S75/S80/S85) 이며 monotonic 유지; Panel B는 그 중 3개 representative만 표시.
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
  - **Hero-tier micro variance allowance [briefing relax R3, 2026-05-23]**: Panel C (HERO #1) HERO element (polymer film outline, 4 energy level horizontal lines) 에 한해 동일 tier 상한값 +0.05pt 허용 (예: mechanism 1.0pt → 1.05pt, reference 0.4pt → 0.45pt). Same-tier 다른 panel과 시각적 식별 불가능한 수준 — *위계 강화 only, 새 tier 도입 아님*. 다른 panel HERO element에는 확장 금지.
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

## §15. Export-time specs (v8.5 NEW)

Briefing was previously silent on output specs. This section locks
journal-submission-grade parameters so `/fig_export` runs are reproducible
and `accepted: true` claims are verifiable.

**Target journal envelope** (broad: tuneable per actual submission):
- **Width (single-column)**: 89 mm (Nature family) ↔ 88 mm (Science) ↔ 86 mm
  (ACS). Use 89 mm as Fig 1 default — fits all 3 families with ≤1 mm crop.
- **Width (double-column / full-width)**: 178–183 mm. Fig 1 is two-row +
  7-panel composite — **full-width** is canonical. Current `\resizebox{178mm}`
  in `.tex` line 21 matches.
- **Height**: free for cover-style figures; current ~115 mm (514 × 322 pt
  graphic per /fig_export log) ≈ 113 × 178 mm presentation; well within
  full-page (~240 mm available).
- **Font sizes (post-resize at 178 mm)**: panel letters ~9.5 pt, region
  labels ~8.5 pt, axis labels ~7.5 pt, tick labels ~7 pt, mini-icon labels
  ~5.5 pt. Anything < 5 pt at final width = FORBIDDEN (illegibility risk
  in print).

**Raster + vector outputs (all 4 required for submission)**:
- **PDF** (vector master): `/fig_export` default. Embed all fonts as
  Type 1 / OpenType (no Type 3 — Nature explicit reject). `lualatex` with
  the current preamble produces embeddable fonts via `\sffamily` Helvetica
  family.
- **SVG** (web / supplementary): `dvisvgm` from PDF → text remains text
  (NOT outlined paths) so screen readers / search indexing works.
- **TIFF** (raster master for typesetter): 600 DPI minimum at final width.
  Current ~34 MB at 178 mm × 600 DPI = correct envelope (Nature: 300–600
  DPI for line+halftone composites; we sit at upper bound).
- **PNG** (review proof, NOT submission): 600 DPI rasterization for crop
  reviewers; submission-grade outputs are PDF + TIFF.

**FORBIDDEN export practices**:
- Outlined text in SVG (kills accessibility + makes future edits manual)
- Embedded raster inside PDF (Fig 1 is fully vector; raster embeds =
  resolution downgrade)
- Font subsetting that strips italic / bold variants (subscript / equation
  labels lose typography)
- Color profile drift: figure uses RGB; CMYK conversion belongs at
  typesetter stage, not export stage

**Reproducibility gate**: every published figure release commits
- `examples/<name>/exports/<name>.{pdf,svg,tiff,png}` (current convention)
- a short `exports/README.md` recording: build SHA, target journal, target
  width, font embedding mode, color profile. (Currently absent for this
  fixture — add at v0.x submission release.)

---

## §17. Dashed-line semantics consolidation (v8.5 NEW)

Pre-v8.5: §10 #17 marked this as "active, kept as-is — 4 distinct semantics."
Per-panel specs (§13.X) each spelled out the meaning in context, but the
4 semantics were never enumerated in one place. This section consolidates
the convention so a reviewer can cross-check the dashed-line discipline
without grepping the briefing.

**Locked dashed-line semantic table:**

| Semantic | Where | Style | Why dashed (not solid) |
|---|---|---|---|
| **Reference / contrast** | Panel D Debye dashed curve | `dashed, cGray!70!black, 0.65pt` | "What it would be if Debye held" — counterfactual reference. Solid would suggest measured data. |
| **Dynamic / transition** | Panel C-R4 escape arrows (shallow + deep → mobility edge), Panel C-R1 mobility edge horizontal line | `dashed, cBlue!70 / cRed!70, 0.35pt` + `dashed, cGray!?, 0.30pt` for edge | Energetic boundary that carriers *cross* — not a structural feature, a probabilistic transition. |
| **Transformation (reaction)** | Panel A inv. vulc. arrow (S₈ → Ring_c vertex) | `dashed, cAmber!70!black, 0.55pt`, Stealth arrow | Chemical reaction (not a literal bond) — process, not state. |
| **Binding / leader** | Panel C dashed leaders (C-L ● sites ↔ C-R trap levels) | `densely dashed, cBlue!55 / cRed!55, 0.28pt`, NO arrow | "Same trap, two views" semantic binding — not a physical line, conceptual correspondence. |

**Discrimination rules** (so the 4 don't visually collide):
- **Color rule**: gray = reference, color (blue/red) = trap-species binding,
  amber = chemical/material origin. Color tells the reader *which semantic*.
- **Weight rule**: reference ≥ 0.65pt (most visible), transition ~0.35pt,
  transformation ~0.55pt, leader ≤ 0.30pt (most subtle).
- **Arrow tip rule**: transformation + transition use Stealth tips (directed
  process); reference + leader use no arrow tips (no directionality).
- **Density rule**: leader uses `densely dashed` (tighter pattern, reads as
  "this is a thin construction line"); others use plain `dashed`.

**FORBIDDEN dashed-line uses** (would collapse the 4-semantic discipline):
- Dashed arrow with no tip (looks like a broken solid line — semantic noise)
- Mixing colors per dashed semantic (e.g., red dashed for reference would
  collide with deep-trap escape arrow)
- Dashed line as a panel border (solid border or no border, not dashed)
- Dashed line for measurement-data uncertainty bands (use light fill, not
  dashed envelope)

**Future-figure inheritance** (per §18): Fig 2..6 must reuse the same 4
dashed semantics with the same color + weight rules. New dashed meanings
require a §17 amendment.

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

**Reading order**: (1) panel letter 'b' (좌상) → (2) 3 zigzag chains stacked vertically (B-1, S60→S75→S85 위→아래 monotonic progression 인지, representative subset of 5-sample paper set) → (3) S₆₀ / S₇₅ / S₈₅ endpoint labels at chain tails (B-2, composition coord) → (4) bottom axis arrow + 'Sulfur content, wt%' label (B-3, variable composition 명시) → (5) inter-arrow → C HERO 진입.

- **B-1** 3 zigzag skeletal chains, representative subset of full 5-sample paper set (10/18/24 atoms drawn; bond spacing 0.10cm, amplitude 0.08cm, atom r=0.025cm, bond w=0.5pt — R11 delicate). v8.7 iter1 (2026-05-17): restructured 4 → 3 chains for concept-figure clarity; chain y = 7.90 / 7.00 / 6.10 (span 1.80cm, spacing 0.90cm — increased from prior 0.60cm for cleaner breathing room). **Role**: **sulfur composition variation (wt%) visual sampling** (Q1 LOCKED: numbers = wt% S, NOT chain atom count); 3 representative samples (S60/S75/S85 = endpoints + middle) for visual clarity in overview figure; full 5-sample dataset (S60/S70/S75/S80/S85) belongs to Fig 2~ quantitative panels. Zigzag = sff skeletal chemistry convention; shared `\zigSChain` macro = A↔B chain identity binding (§13.9 cross-row). **Note**: drawn atom count (10/18/24) is **artistic correlate** — longer drawn chain = qualitative "more S" 시각화; literal chain atom count 아님 (briefing §3.1 reader DO/DON'T 참조)
- **B-2** sample-name endpoint labels at terminal atoms (S₆₀ / S₇₀ / S₇₅ / S₈₅, cAmber!90 6.5pt; full 4-label set). **Role**: **sample names derived from sulfur wt%** (Q1 LOCKED): S60 = 60 wt% S sample, ..., S85 = 85 wt% S sample (per planning/sulfur_sample_selection_policy.md); subscript form은 sample naming convention (NOT atom count subscript). §8.8 LOCKED — S60..S85 composition labels는 B에만 허용 (Row 2 plot은 concept만); right anchor at terminal atom = chain의 "끝" 시각 정렬
- **B-3** bottom horizontal axis arrow + '**Sulfur content, wt%**' italic label (v8 Q1 fix; was 'Chain length, n'). **Role**: composition variable 명시; arrow = direction (60 wt% → 85 wt%, monotonic 보장); B-2의 sample-name labels (S60..S85)이 이 axis 위에서 wt% progression으로 읽힘
- **B-4** sample boundary divider lines (v8.4 NEW, v8.7 iter1+iter2 updated): 3 chains 사이에 2개의 thin horizontal `cGray!55, line width=0.18pt, densely dotted` divider lines (tone progression: !25→!40 post-C002 → !55 post-iter2 +38% for perceptible print-scale separation), x extent 동일 (3.85..6.30), y at midpoints between adjacent chains (7.45 / 6.55). **Role**: 3개 chain row이 *3개 distinct representative sample* (S60/S75/S85) 임을 시각적으로 명시 — chain bundle 오독 risk 차단. divider는 *separation cue* only (NOT data axis), 따라서 dotted + 얕은 cGray로 inter-sample boundary만 표시. **Forbidden**: solid lines (axis tone 침범), color (sample-identity confusion), width > 0.20pt (mechanism-tier 침범)

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
- **C-L6** thin-film thickness anchor (v8.5 NEW): small ↕ double-headed arrow at LEFT edge of polymer sheet (around x=7.45, spanning y=6.20..7.70 = full sheet height) + inline `'$d \approx 1\,\mu$m'` label (anchor=east, italic 5.5pt cGray!70). **Role**: macroscale anchor — pre-v8.5에 sheet는 "thin film"이라 했지만 두께 감각 없이 abstract rectangle로 읽혔음. 작은 dimension 1개로 reader가 "이건 마이크론 두께 실물 필름이다" 인지. **Locked discipline (per §3.2 setup-context rule philosophy)**: arrow ≤ 0.30pt cGray, label 5.5pt italic, NO units other than μm (절대 nm/Å는 chemistry-scale 모호; mm/cm은 too thick → typological mismatch). Value '≈ 1 μm' = generic poly(S-r-DIB) spin-coat range; 정확한 measured thickness는 Methods/SI. Per briefing §17 dashed semantic 분류 외 (이 dimension은 solid arrow). **Forbidden**: ticks on the dimension, multiple thickness labels (only 1 reference value), arrow span > sheet height (overshoots → reads as "polymer extends beyond what's drawn")

**RIGHT half (energy diagram, x=10.50..13.80):**
- **C-R1** E_C / mobility edge (dashed) / E_V reference horizontal lines + 'Energy' rotated label + vertical axis arrow at x=10.50. **Role**: semiconductor band edge reference; mobility edge (dashed) = "delocalized vs localized" 경계, trap states는 이 아래; E_C / E_V 정량 값 없음 (cartoon register). **Sample regime LOCKED**: poly(S-r-DIB)은 **fully amorphous** (Q7 확인 2026-05-16) → Mott-CFO mobility-edge model 적용이 적절; semi-crystalline / dual-phase 가정 금지
- **C-R1b** Gaussian DOS overlay (Q8 추가, .tex L343-360 R15 기존): shallow Gaussian (cBlue!18 fill opacity 0.55 + cBlue!75!black 0.50pt border, σ=0.085, peak at y=7.49) + deep Gaussian (cRed!18 fill opacity 0.55 + cRed!75!black 0.55pt border, σ=0.18, peak at y=6.05). Energy axis 옆 (x=10.55부터 right로 0.28~0.32cm 너비)에 fill+outline. **Role**: poly(S-r-DIB) amorphous semiconductor의 **continuous Gaussian DOS** 표현 (Mott-CFO + Bässler disorder model); C-R2/R3의 horizontal lines은 이 distribution 안의 representative sample. Shallow 좁은 σ = tight localization; deep 넓은 σ = broader trap-depth distribution. F-2/F-3 Gaussian과 형태 echo (§13.9 Binding-1 강화)
- **C-R2** shallow trap levels (2 horizontal lines at y=7.55/7.35; v7 polish #7: line width 0.80→1.00pt; cBlue!80!black; v8: 1 cBlue ● on each level — carrier-neutral marker). **Role**: shallow trap = mobility edge 근처 좁은 ΔE↓; thermal release easy = fast detrapping; cBlue color = Panel F-2 shallow Gaussian / Panel G implicit과 binding (§13.9 Binding-1); ● polarity-neutral per §8.1; **2 lines = C-R1b Gaussian DOS 안의 sample** (NOT discrete 2-level; F-2 smooth Gaussian과 cross-check 일관)
- **C-R3** deep trap levels (2 horizontal lines at y=6.20/5.85; v7 polish #7: line width 0.80→1.00pt; cRed!80!black; v8: 1 cRed ● on each level — carrier-neutral marker). **Role**: deep trap = mobility edge에서 멀리 (큰 ΔE↓); thermal release hard = slow detrapping = long lifetime; cRed color = F-3 deep Gaussian + G-4 q_tr binding; ● polarity-neutral per §8.1; **2 lines = C-R1b deep Gaussian DOS 안의 continuous distribution sample** (Q8 LOCKED: NOT discrete 2-level; broader σ 인코딩 = wider trap depth spread)
- **C-R4** escape arrows from **BOTH shallow + deep** bands → mobility edge (cBlue!70 + cRed!70 dashed 0.35pt; Boltzmann thermal release). Shallow: short arrow large head (easy escape, y=7.55→7.82). Deep: longer arrow smaller head (hard escape, y=6.20→7.82). **Role**: both shallow + deep traps의 dynamic detrapping 표현 — "no one-sided dominate claim"; dashed = dynamic transition; §17 dashed semantic 중 "transition"; 길이 = activation energy 비례 (longer = harder). **Scope LOCKED (Q9)**: thermal Boltzmann release만 표현 — tunneling / hopping / field-assisted는 cartoon register clutter 우려로 scope 밖. Paper 실험이 위 4 mechanism 중 단일 (가장 basic) 가정에 맞춤; 추가 mechanism 필요 시 SI/Methods 영역
- **C-R5** ΔE_t^d depth annotation (cRed!75 double-headed arrow at x=13.55 spanning E_C → deep band bottom + label). **Role**: trap depth scalar (E_C - deep band 위치) 명시; double-arrow = magnitude (방향 없음); Δ 기호 = "차이" 명확화; reader가 deep의 "왜 retention 길다"를 이 visual로 인지
- **C-R6** 'shallow' / 'deep' band labels (bold 6.5pt sans, anchored east of each band). **Role**: trap species 명명; bold = primary identifier; east anchor = band의 우측 (read 방향 종료점); F-5 'Shallow'/'Deep' base labels과 typography + color binding (§13.9 Binding-1 닫음)

### §13.4 Row 2 cover-binding — 10 sub-regions (v7 split from 3, coord-explicit)

**Background layer (2):**
- **Row2-BG-wash** background tint: `\fill[cAmber!8, rounded corners=2mm] (-0.05, 0.05) rectangle (14.05, 4.55)`. **Role**: 3 columns (D/E/F)을 시각적으로 1 scene으로 결속; no hard column borders (briefing §3 cover-binding mechanism #1). Pre-v8.6 4-panel bind language updated to 3-column.
- **Row2-BG-chains** 3 wavy chain hints (cAmber!22, line width 0.30pt, plot[smooth]) crossing horizontally at y ≈ 1.20 / 2.50 / 3.80 spanning x=0.10..13.90. **Role**: row 2 "floor" 의 polymer material identity — Panel C-L thin film chain hints과 visual binding (zoom-out: micro chain → macro bulk → measurement scene)

**Branching root + caption (2):**
- **Row2-Caption** 'convergent evidence — three independent probes of the same trap' (font: sffamily italic 6.5pt, text=cGray!75!black, anchor=south align=center) at (7.00, 4.92). **Role**: 의미 gate — divergent 화살표 geometry를 convergent semantic으로 invert; reader 2초 안에 "3 lines → 1 trap" 인식
- **Row2-Root** branchRoot coordinate (6.95, 4.85) — Panel C 하단 (x 6.95 = Panel C left edge + 0.05 inset) + inter-row gap (y 4.55 wash top to 5.00 Panel C bottom) 안에 위치. **Role**: 3 spoke의 공통 출발점; "동일 trap의 3 measurement modality" 시각적 anchor

**3 spokes (3) — v8.6 endpoints updated to 3-column layout:**
- **Row2-Spoke-Kinetic** (6.95, 4.85) → (2.28, 4.30) v8.6 (was (1.73, 4.30) v7). Style: Stealth 6pt×4pt arrow tip, cGray!65!black, line width=0.9pt. **Role**: C → Column D (kinetic) narrative spoke; endpoint (2.28, 4.30) = new Column 1 bbox center top.
- **Row2-Spoke-ISPD** (6.95, 4.85) → (6.975, 4.30). Endpoint shifted from (6.95, 4.32) → (6.975, 4.30) to align with new Column E bbox center top. Same style. **Role**: C → Column E (paired ISPD) spoke; vertical, lands at column-top → reader sees V_s + g(E_t) as one column.
- **Row2-Spoke-Mechanical** (6.95, 4.85) → (11.70, 4.30) v8.6 (was (12.20, 4.30) v7). Same style. **Role**: C → Column F (mechanical) narrative spoke; endpoint (11.70, 4.30) = new Column 3 bbox center top.

**3 modality labels (3) — v8.6 positions updated to 3-column centers:**
- **Row2-Label-Kinetic** 'kinetic' (font: sffamily italic 6pt, text=cGray!75!black, anchor=south, fill=cAmber!8, inner sep=1pt) at (4.55, 4.55) v8.6 (was (4.34, 4.55) v7). **Role**: kinetic spoke modality 명명; new position is midway between C and Column D top.
- **Row2-Label-ISPD** 'ISPD' same style at (6.975, 4.50). **Role**: ISPD paired spoke 명명; Column E modality.
- **Row2-Label-Mechanical** 'mechanical' same style at (9.40, 4.55) v8.6 (was (9.55, 4.55) v7). **Role**: mechanical spoke modality 명명; new position is midway between C and Column F top.

**Anti-chain mechanism note**: 3 spoke가 발산형 geometry이지만 reader가 convergent로 invert하는 메커니즘 = (a) shared origin (C HERO, 단일 source); (b) caption "convergent evidence" semantic 명시; (c) Panel C ↔ Panel F color match (shallow blue + deep red), 동일 trap 시각 echo. §8.7 forbids linear chain (D→E→F→G); 이 3중 메커니즘이 그 forbidden 강제.

### §13.5 Column D — Kinetic evidence (v8.6 restructure, 7 sub-regions)

**Column bbox**: x=0.05..4.50, y=0.10..4.45. Internal split: apparatus zone y=2.80..4.25 + mini-gap y=2.65..2.80 + result zone y=0.20..2.60.

**Reading order (2026-05-20 framework rewrite)**: (1) kinetic spoke 진입 (column top, x≈2.28) → (2) **D-2 MIM stack apparatus** (SMU + polymer film + ground) "constant V 인가 + I 측정" → (3) **D-4 equation label** `I(t)~t⁻ⁿ` (mental model) → (4) **D-5 high-n red curve** (sulfur polymer, **steeper**, n ≈ 0.85, ends lower right) "trap 계속 쌓임 → I 지속 감소" → (5) **D-6 low-n blue curve** (control polymer, **less steep**, n ≈ 0.55, ends upper right) "trap 거의 없어 I 평탄" → (6) **D-3 Debye dashed reference** (single-relaxation exponential, 둘 다보다 long-t 에서 아래) → (7) D-7 curve ID labels (high n / low n).

- **D-1** column-frame: implicit bbox boundary (no visible stroke, just coordinate anchor). 3-spoke endpoint lands at column top center `(2.28, 4.25)`. **Role**: column-level layout anchor; replaces pre-v8.6 individual Panel D bbox.
- **D-2** apparatus zone — kinetic-measurement scene at column-top, generic-instrument SYNTHESIS per v8.7 (no direct OA reference for transient I-t rig — Wang Nat Commun 2022 Fig 1e equivalent-circuit framing partial-mined). Layout: SMU box (LEFT) + MIM sample stack (CENTER) + ground symbol (BOTTOM). Mono cGray!75!black 0.30pt stroke. Width ~3.5cm × height ~1.30cm.
  - **SMU box**: rectangle at `(0.55, 3.10)`..`(1.55, 3.95)` with `V` symbol upper-left + `A` symbol lower-left (dual-function source-meter unit). cGray!75!black 0.30pt outline.
  - **MIM sample stack** at column-center `(2.50, 3.50)`: top electrode (hatched gray rectangle 1.20cm × 0.08cm at y=3.85) + polymer film (cAmber!28 filled rectangle 1.20cm × 0.30cm at y=3.50..3.80) + bottom electrode (hatched gray rectangle 1.20cm × 0.08cm at y=3.42).
  - **2 leads**: SMU top lead → top electrode (cGray!75 0.28pt); SMU bottom lead → bottom electrode.
  - **Ground symbol** at bottom electrode (3-bar standard).
  - **Role**: apparatus zone hero — visualizes "transient I-t = SMU drives V across MIM stack, measures I(t)" with standard EE convention. Replaces v8.6 simple `current-source ⊙ + slab` per user 2026-05-17 directive (Nature Comm publication grade).
- **D-3** result-zone axis arrows Stealth-tipped (cGray!65 0.40pt). Origin shifted from pre-v8.6 (0.55, 0.45) to fit new column bbox; new origin `(0.45, 0.40)`. Tip labels `\log I` (rotated at y=2.55) / `\log t` (at x ~4.20, y=0.30). **Role**: log-log frame compresses power-law to straight lines; tick-less = cartoon register preserved.
- **D-4** main equation label `$I(t)\sim t^{-n}$` at column-result top, around `(0.55, 2.70)`, labelStrong. **Role**: mental-model anchor; reader reads curves as "I~t^-n family with different n values."
- **D-5** **high-n** power-law line (cRed!80 0.80pt, **sulfur polymer paper hero**) from `(0.65, 2.30)` to `(3.85, 0.55)`. **Steep** slope (visual n ≈ 0.55; conceptual n ≈ 0.85 from real data — cartoon-compressed for figure scale). Physical meaning: constant V 인가 후 trap이 지속적으로 채워지며 I 가파르게 감소 → "trap-rich" / strong trap capability. *2026-05-20 framework rewrite: 이전 "deep-rich less-steep (0.65,2.40)→(3.85,1.10)" 매핑은 잘못된 depolarization framework 가정 결과; absorption-current 해석에서는 high n = steeper.*
- **D-6** **low-n** power-law line (cBlue!80 0.80pt, **control polymer**, e.g., PI) from `(0.65, 2.30)` to `(3.85, 1.50)`. **Less steep** (visual n ≈ 0.25; conceptual n ≈ 0.55-0.60 PI / ≈ 0-0.2 PDMS). Physical meaning: trap 거의 없어 초기 polarization 후 I 평탄. *2026-05-20: 이전 "shallow-rich steeper" 매핑 폐기.*
- **Both curves start at same y_0 = 2.30** (initial dielectric polarization current 동일 order — cartoon simplification; 실제 측정에서는 sample geometry 의해 다소 다름).
- **D-7a** Debye dashed reference (cGray!85!black 0.75pt, bezier) ending at `(2.55, 0.56)`. **Ends below both power-law tails** per §8.4 (heavy-tail vs single-relaxation exponential). Label `Debye` (labelMute, cGray!65!black) at `(2.60, 0.55)` anchor=west, INSIDE plot, just above x-axis (iter 52d + iter 53 lift). No leader (color-match + adjacency = unambiguous identifier).
- **D-7b** curve-ID labels (**high-n / low-n naming, 2026-05-20**): sloped path-attached convention — 'high n' (cRed!75!black) along D-5 red curve `above=3pt`; 'low n' (cBlue!75!black) along D-6 blue curve `above=4pt`. **No fill** (Nature cardinal sin guard — never break primary data strokes). 이전 'deep-rich/shallow-rich' 명명은 framework 오인 산물 — 폐기.

### §13.6 Column E — ISPD-paired evidence (v8.6 restructure, 10 sub-regions)

**Cross-panel narrative attribution (2026-05-20 framework rewrite)**: Panel E shows **the sulfur polymer's** internal trap landscape — Panel D (D-5/D-6) establishes 황고분자 > control via cross-sample high-n vs low-n comparison; Panel E then drills into the sulfur sample's bimodal g(E_t) DOS (deep-trap-dominant, 1.86× shallow); Panel F shows the macroscopic mechanical consequence on the same sulfur cantilever. Reading sequence: D = comparison establishes hero → E = hero's trap landscape → F = hero's mechanical manifestation. Control polymer g(E_t) is NOT drawn (would clutter; Panel D already established 황 vs control).

**Column bbox**: x=4.65..9.30, y=0.10..4.45. Internal split: apparatus zone y=2.80..4.25 + V_s sub-zone y=1.50..2.60 + g(E_t) sub-zone y=0.20..1.40 + mini-gap y=2.65..2.80.

**Reading order**: (1) ISPD spoke 진입 (column top, x≈6.975) → (2) **E-2 apparatus icon** (corona ▽ + Kelvin probe ▭ + thin-film slab) "비접촉 표면 전위 측정" → (3) E-3 V_s sub-zone axis + **E-4 V_s decay curve** (raw measurement) → (4) **E-5 internal raw→derived inter-arrow** "이제 derive 함" → (5) E-6 g(E_t) sub-zone axis + **E-7 shallow Gaussian** (좌, 파랑, 낮음) → (6) **E-8 deep Gaussian** (우, 빨강, 1.86× 높음, "deep dominant") → (7) **E-9 τ_d annotation** → (8) E-10 Shallow/Deep base labels.

- **E-1** column-frame: bbox anchor at top center `(6.975, 4.25)`. 3-spoke 2nd endpoint lands here.
- **E-2** apparatus zone — ISPD-apparatus scene at column-top, **He et al Nat Commun 2024 Fig 1c adaptation** per v8.7 (direct reference match). Layout: corona needle (LEFT, charging step) + sample slab on grounded base (CENTER) + Kelvin probe with support (RIGHT, V_s readout) + small instrument box (FAR-RIGHT, "V_s meter"). Mono cGray!75!black 0.30pt stroke. Width ~3.7cm × height ~1.30cm.
  - **Corona needle** at LEFT around `(5.10, 3.50)`: thin vertical needle (cGray!75 0.30pt) hanging down to point at sample top, with small lightning-bolt or "C" label nearby; needle base around `(5.10, 3.95)` apex at `(5.10, 3.65)`. Optional `+` polarity cue near apex.
  - **Sample stack (2-layer, v8.7 Column-E iter2 + iter7 upgrades)** at CENTER: polymer film (cAmber!28 fill + cAmber!70!black 0.30pt outline) at top y=3.45..3.52 (0.07cm thin film, x=6.30..7.85) + **substrate** (cGray!18 fill + cGray!75 0.30pt outline + diagonal hatching cGray!55 0.14pt at 10 lines/0.14×0.22cm slope, material-identification cue) at bottom y=**3.23..3.45 (0.22cm thick, iter7 doubled from 0.11)**. **Realistic thin-film-on-substrate ratio per ref01 Checa NatComm 2023 SS-KPFM convention** — substrate visually dominant vs thin film, as in actual research samples. Substrate represents the conductive base required for ISPD charge-decay path. Ground attaches to substrate (not polymer) at right edge y=3.34 — physically accurate. Ground bars repositioned to y=3.12..3.18 (was 3.20..3.26) to clear thicker substrate.
  - **Corona needle (v8.7 Column-E iter2 upgrade)** at LEFT around `(6.55, 3.95→3.62)`: thin vertical needle (cGray!85 0.55pt) with support ball at top + **sharp filled triangular tip** (downward point) at (6.55, 3.55) + **3 short spark/discharge indicators** (cRed!55!black 0.30pt, radiating SW/S/SE from tip) — "ion emission" cue communicating corona-discharge mechanism. `+` polarity at (6.32, 3.75); 'Corona' italic 5pt label above needle.
  - **Kelvin probe (v8.7 Column-E iter6 disk-on-shaft + iter E12 user-flagged redesign 2026-05-20)**: vertical shaft (cGray gradient) at x=7.36..7.44, y=3.87..**4.05** (length 0.18cm, was 0.08cm stub — extended for proper Kelvin-probe-vs-disk aspect ratio 1:2.2 vs prior 1:5) + disk electrode at bottom (cGray metallic gradient, x=7.20..7.60, y=3.80..3.87) + **TikZ `<->` double-arrow vibration cue** LEFT of shaft at x=7.32, y=3.90..4.03 (replaces prior \updownarrow unicode glyph that floated x=7.62 disconnected from probe). Vibration arrow indicates FM-CPD vertical oscillation modulation. Cable from new shaft top (7.40, 4.05) to V_s meter port. Label `Probe` italic 5pt at (7.62, 3.82). **Air-gap "d" annotation removed iter E12** — non-contact geometry self-conveyed by probe-hover; quantitative gap value belongs in Methods/SI, not cartoon Fig 1.
  - **V_s meter box (v8.7 Column-E iter6 update)** at FAR-RIGHT `(8.20, 3.65)`..`(9.00, 4.05)`: rectangle with **small exponential-decay icon inside top** (cGray!60 0.28pt smooth bezier from y=3.98 left to y=3.92 right plateau) — replaces prior iter2 sinusoidal cue (Tech illustrator audit: sine was WRONG cue, V_s is slow exponential decay over seconds, not AC signal). Decay icon communicates "this instrument reads slow potential decay" semantically correct. `$V_s$ meter` italic 5pt label in lower portion. Lead from probe shaft top to meter LEFT side (cGray!75 0.22pt) at y=3.95 (updated iter6).
  - **Role**: apparatus zone hero — shared by raw V_s + derived g(E_t) per §6 paired ISPD. He 2024 Fig 1c idiom transfer plus iter2 paper-grade detail upgrade: each element now communicates *measurement mechanism* (discharge / charge-decay path / vibration modulation / signal display), not just iconic shape.
- **E-3** V_s sub-zone axis arrows Stealth-tipped (cGray!65 0.40pt). Origin `(4.95, 1.65)`. Vertical axis top `(4.95, 2.85)` post v8.7 Column-E iter5 (was 2.55, +0.30cm) — axis height 0.90→1.20cm reclaiming whitespace from apparatus-V_s gap. Tip labels `$V_s(t)$` rotated at (4.83, 2.55) (was 2.30, mid-axis) + `$t$` at (8.50, 1.55).
- **E-4** V_s stretched-exp decay curve (cRed!70 0.70pt, smooth bezier 9 waypoints). β≈0.8 shape preserved; cartoon illustrative values per Q11. v8.7 Column-E iter5: waypoints scaled (y-1.65)*1.333+1.65 to use new envelope; peak at (5.10, 2.72) was 2.45. Markers shifted accordingly.
- **E-5** internal ISPD raw→derived inter-arrow (Stealth tip 5pt×4pt, 0.55pt cGray!75) — vertical downward arrow at column-center (6.95) from V_s sub-zone (y=1.55) to g(E_t) sub-zone (y=1.28). Label 'derive' **upright** 6pt cGray!75 fill=cAmber!8 at (7.05, 1.45) — verb describing transformation (ISO 80000-2: upright for non-variable text). v8.7 Column-E iter1+2 history: 'ISPD' (redundant with column-top label) → 'derive'. iter 4 (2026-05-18): weight 0.35→0.55pt + larger Stealth tip + italic→upright per designer audit.
- **E-6** g(E_t) sub-zone axis arrows Stealth-tipped (cGray!65 0.40pt). Origin `(4.95, 0.40)`. Vertical axis top `(4.95, 1.45)` post v8.7 Column-E iter5 (was 1.35, +0.10cm) — more headroom for τ_d caliper above Gaussians. Tip labels `$g(E_t)$` rotated at (4.83, 1.25) (was 1.15) + `$E_t$` right.
- **E-7** shallow Gaussian (cBlue!85 border + cBlue!35 fill, 0.70pt). σ≈0.085 per §13.3 (v8.3 spec). Peak position LEFT side of g(E_t) sub-zone. v8.7 Column-E iter1 (2026-05-18): fill !25 → !35 (+40% saturation).
- **E-8** deep Gaussian (cRed!85 border + cRed!35 fill, 0.70pt). σ≈0.18, peak 1.86× shallow height per §5 Q4. Peak position RIGHT side of g(E_t) sub-zone. v8.7 Column-E iter1 (2026-05-18): peak y 1.30 → 1.24 to bring ratio from over-shoot 2.0× to 1.87× ≈ Q4 spec; fill !25 → !35 (+40% saturation).
- **E-9** τ_d annotation — energy-domain interval between Gaussian peaks. v8.7 Column-E iter4 (2026-05-18): redesigned from dashed double-headed arrow (`<- - - ->`, designer-flagged as chartjunk + AI-generic per 4-designer parallel audit) to **caliper-style**: solid horizontal bar (cRed!55!black 0.32pt) at y=1.35 spanning shallow-peak-x (5.70) to deep-peak-x (6.80) + 2 vertical T-end-caps at peak x-positions (y=1.32..1.38) — scientific "distance between two points" convention. Label `$\tau_d$` cRed!55!black 6pt fill=cAmber!8 at (6.25, 1.36) anchor=south. Tone cRed!70→!55 for proper annotation-tier hierarchy.
- **E-10** 'Shallow' / 'Deep' base labels at Gaussian feet (cBlue!75 / cRed!75 italic). Closes color binding per §13.9 Binding-1.

### §13.7 Column F — Mechanical evidence (v8.6 restructure, supersedes Panel G; 8 sub-regions)

**Cross-panel narrative attribution (2026-05-20 framework rewrite)**: Panel F shows **the sulfur polymer cantilever's** macroscopic response — third leg of the convergent-evidence triad (after D = kinetic CvS sample comparison establishing hero, E = hero's bimodal trap DOS). The bent cantilever, q_tr charge markers, and Coulomb-dominant arrow all depict the sulfur polymer (paper hero) under bias; control polymer mechanical response is NOT drawn (paper claim is "황고분자가 큰 bending", control would be flat/small — not the visual story). The Maxwell-vs-Coulomb force contrast within Panel F is intra-sample (same sulfur cantilever, two competing force terms).

**Column bbox**: x=9.45..13.95, y=0.10..4.45. Internal split: apparatus zone y=2.80..4.25 + mini-gap y=2.65..2.80 + result zone y=0.20..2.60.

**Reading order**: (1) mechanical spoke 진입 (column top, x≈11.70) → (2) **F-2 apparatus zone** — PSU box + leads to electrode + neutral cantilever fixture + **F-3 Maxwell attraction baseline** (light pink, polymer→electrode, "baseline before charges") → (3) reader 시선 아래로 → (4) **F-4 result clip** (TOP, same fixture geometry) → (5) **F-5 bent cantilever** (left, AWAY from electrode — bend signature) → (6) **F-6 3 q_tr ● markers** (cRed deep — color binding to C/E) + `$q_{tr}$` label → (7) **F-7 Coulomb repulsion arrow** (bold cRed!80 0.7pt, polymer→away from electrode) + 2-line label "Coulomb / repulsion" — **Coulomb WINS against apparatus-zone Maxwell baseline** → (8) **F-8 result-zone electrode + air gap** dimension cue.

- **F-1** column-frame: bbox anchor at top center `(11.70, 4.25)`. 3-spoke 3rd endpoint lands here.
- **F-2** apparatus zone — mechanical-fixture scene at column-top, **Conrad et al Nat Commun 2016 Fig 1b cross-section idiom adaptation** per v8.7 (direct reference match for cantilever cross-section + electrode hatching). Layout: PSU box (LEFT) + 2 leads + neutral cantilever fixture (CENTER-RIGHT) with Conrad-style mount-spacer stipple, hatched electrode, air-gap label, neutral pale polymer. Mono cGray!75!black 0.30pt stroke. Width ~4.0cm × height ~1.30cm.
  - **PSU box** at LEFT `(9.85, 3.45)`..`(10.40, 4.00)`: rectangle with `V` label + tiny pulse trace on display (3-segment square wave indicating pulsed-bias protocol).
  - **2 leads from PSU** (v8.6 routing preserved — both leads avoid crossing the neutral polymer): lead 1 (top, to clip-mount) routes ABOVE fixture via y=4.30; lead 2 (bottom, to electrode) routes BELOW PSU via y=2.80 with `−` polarity indicator near electrode connection.
  - **Mount + spacers**: small rectangular clip block at `(12.25, 4.10)`..`(12.65, 4.20)` with Conrad-style stipple/hatch pattern (3-4 small triangles or stippled cluster) at clip top indicating fixed mount.
  - **Neutral polymer cantilever**: straight vertical rectangle `(12.40, 4.10)`..`(12.50, 2.90)`, color `cAmber!18` opacity 0.6 (pale = "no trapped charges yet, before measurement"). Optional internal chain hint at very low opacity.
  - **Electrode (apparatus, RIGHT side)**: vertical rectangle `(13.30, 2.90)`..`(13.50, 4.05)` with **cross-hatched fill** per Conrad 2016 convention (cGray!50 cross-hatch pattern at 45° + 135°, line spacing 0.04cm) — distinguishes apparatus-zone electrode from result-zone electrode (which uses metallic gradient + single-direction hatch).
  - **Air gap label**: tiny `air gap` italic 5pt cGray!65 inline label between polymer and electrode at `(12.95, 3.10)` with optional `↔` dimension cue at smaller scale.
  - **Role**: apparatus zone hero — establishes the *setup at rest* with PSU + cantilever fixture (Conrad cross-section style) + applied bias. v8.6 baseline replaced with publication-grade cross-section idiom per user 2026-05-17 directive.
- **F-3** Maxwell attraction baseline arrow (cRed!35!white dashed, 0.35pt, Stealth tip length 3pt, polymer→electrode direction inside apparatus-zone neutral fixture) + 'F_Maxwell' label italic 5.5pt cGray!70 + parenthetical 'image/induced attraction (baseline)' below. **Role**: baseline attractive force present *regardless of charges* (Maxwell stress / dielectric polarization). Light pink + dashed signals "weaker / baseline / not the winner." Per §8.5 v8.6 amendment: Maxwell ALLOWED in apparatus zone, FORBIDDEN in result zone.
- **F-4** result-zone clip + mount: clip rectangle `(11.55, 2.45)` rectangle `(11.90, 2.55)` cGray gradient + stub down + mount hatch above. **Role**: 'fixed support' icon at result-zone top.
- **F-5** result-zone polymer cantilever (bent LEFT, AWAY from electrode = Coulomb REPULSION per §8.5): root `(11.625, 2.45)`, tip `(11.20, 0.85)`, bend shape ~0.35cm Δx; cAmber!22→cAmber!42 gradient per §9; outline cAmber!80!black 0.55pt rounded 0.3mm. Internal: 2 thin chain hints (cAmber!65!black 0.25pt opacity 0.38). Compressed from pre-v8.6 L=2.15cm to L≈1.60cm to fit result-zone bbox.
- **F-6** 3 q_tr ● markers (cRed!75!black fill, cRed!85!black border, ~1.4mm diameter, 0.40pt outline) at positions tracking the bent cantilever interior. Plus q_tr leader from polymer right edge to fill=white label `$q_{tr}$` italic 6.5pt cRed!70 to the RIGHT of polymer.
- **F-7** Coulomb repulsion arrow (cRed!80!black Stealth-tipped, line width 0.7pt) from polymer tip area to LEFT (away from electrode) + 2-line label stack `Coulomb` (bfseries 7pt) + `repulsion` (mute 6.5pt) cRed!75!black, anchored to keep arrow line BETWEEN labels (v8.2 SE/NE anchor pattern carried over). **Role**: G's hero claim — force vector + bold red text. Maxwell-vs-Coulomb contrast: this arrow is bold/solid (cRed!80 0.7pt) vs apparatus-zone Maxwell (light pink dashed 0.35pt). Color tier asymmetry = Coulomb WINS.
- **F-8** result-zone electrode + air gap: electrode RIGHT vertical block `(13.55, 0.30)` rectangle `(13.80, 2.50)` cGray metallic gradient + hatching 4-5 lines + 3-bar ground at base + 'electrode' label above. Air-gap dimension arrow `(11.55, 0.50)` ↔ `(13.55, 0.50)` cGray 0.32pt + 'air gap' inline label cAmber!8 fill. **Role**: completes the macro-probe scene; clearance + reference potential. **Removed from pre-v8.6 G-7**: undeflected dashed line + Δx dimension + (grounded) parenthetical — already dropped in v8.5 G simplification, NOT reintroduced.

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
- **Endpoints (2026-05-20 framework rewrite)**: D-5 ('high n' = sulfur polymer) ↔ E의 Deep Gaussian dominant (1.86× taller than Shallow) ↔ F의 bent cantilever Coulomb dominance. **세 modality 모두 황고분자 trap-rich evidence**.
- **Mechanism**: D의 steeper 'high n' line (large n) ↔ E의 deep-trap-heavy bimodal g(E_t) ↔ F의 큰 cantilever bending. 세 panel 모두 "황고분자 trap capability 강함" 으로 convergent. Control polymer 비교: D의 'low n' (flat) ↔ E의 shallow-only DOS (if measured) ↔ F의 작은 bending.
- **Anti-confusion**: 두 panel이 다른 domain (time-power vs energy-density)이지만 same sample → 같은 trap 분포가 D의 n과 F의 peak height 둘 다 결정

**Row 1 internal bindings (A → B → C 좌→우 zoom-progression):**
- **A ↔ B chain identity** [shared macro]: 동일 `\zigSChain` macro — A에서 polysulfide 분자 detail 보여주고 B에서 chain length 변화 sampling (n=60..85). Reader가 같은 chain의 "다른 길이" 인식.
- **A-3 (S)_x ↔ B variable n** [composition tag]: A의 `(S)_x` label에서 'x' = B의 'n' (chain monomer 수); A는 generic chemistry, B는 specific length quantization.
- **A/B ↔ C-L material identity** [amber tone]: cAmber!8 wash (A) + cAmber chains (B) + cAmber gradient sheet (C-L) — 동일 hue family가 "분자 (A) → length variation (B) → bulk thin film (C-L)" zoom-out 흐름 시각화.
- **A → B → C HERO eye-flow** [3-zoom narrative]: A "재료 식별" 1s → B "분자 heterogeneity" 1s → C "trap landscape" 5s dwell (§2 visual story arc). 좌→우 horizontal progression = "분자 단위 → bulk 단위 → trap 단위" mental zoom.
- **B-3 'Sulfur content, wt%' axis ↔ C-L sheet** [discrete→continuous]: B의 discrete 3 representative chains이 C-L의 continuous bulk sheet으로 압축 (ensemble→bulk averaging mental model; bulk thin film이 5-sample composition range 전체의 representative).
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
| D ↔ E ↔ F | trap-capability convergence | sulfur high-n CvS ↔ deep-trap-dominant g(E_t) ↔ Coulomb-dominant bending | §8.4 + §8.7 (anti-chain) |
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

**Total sub-regions (v8.6 restructure)**: 58 (A:8 + B:4 + C:12 [+C-L6 v8.5 thickness anchor] + Row2:10 + Column D:7 + Column E:10 + Column F:8 - 1 [pre-v8.6 redundancy collapse]). Pre-v8.6 totals: 57 (4-panel: D:6 + E:5 + F:5 [shared] + G:7 = 22). Post-v8.6 Row2 column totals: 7+10+8 = 25 (+3 from sub-region split into apparatus zone elements).

**Active iteration target (v8.6, 2026-05-16):**
- Compile + visual review of 3-column Row 2 in progress
- Potential refinement: apparatus zone glyph readability, spoke endpoint visual alignment, V_s ↔ g(E_t) internal arrow polish, Maxwell-vs-Coulomb color tier discrimination check

**Recently iterated (v5–v8.6, 2026-05-15..16):**
- v8.6 (Row 2 Option α restructure — 4 panels → 3 columns with apparatus + result zones):
  - §6 RESTRUCTURED panel-role table: D/E/F/G (4 panels) → Column D/E/F (3 columns, each apparatus+result)
  - §8.5 AMENDED Maxwell rule: ALLOWED in Column F apparatus zone (baseline cue), FORBIDDEN in result zone (Coulomb-only novelty preserved). Maxwell-vs-Coulomb color tier convention LOCKED.
  - §3.3 ARCHIVED size-hierarchy gate (asymmetry dissolved structurally by 3-column restructure)
  - §13.4 spoke endpoints + modality label positions updated to 3-column centers (2.28, 6.975, 11.70)
  - §13.5-§13.7 REWRITTEN: 21 sub-regions (pre-v8.6 D:6 + E:5 + F:5 + G:7) → 25 sub-regions (Column D:7 + Column E:10 + Column F:8). Apparatus zone sub-regions added (D-2 kinetic icon full-scale, E-2 ISPD icon full-scale, F-2 PSU + neutral fixture, F-3 Maxwell baseline).
  - v8.4 mini-icons SUPERSEDED — full-scale apparatus zones replace ≤0.5cm peripheral icons.
  - Total sub-regions 57 → 58 (Column-F apparatus zone splits PSU/Maxwell into 2 sub-regions; redundancy collapse via column-frame unification).
- v8.5 (Row 2 hierarchy rebalance + briefing 4 new sections):
  - §3.3 NEW Row 2 size hierarchy verification gate (now archived by v8.6 §6 restructure)
  - §15 NEW Export-time specs
  - §17 NEW Dashed-line semantics consolidation
  - §18 NEW Cross-figure consistency
  - C-L6 NEW thickness anchor + Panel G simplification (undeflected / Δx / "(grounded)" removed)
- v8.4 (Row 2 register asymmetry attempt with mini-icons — SUPERSEDED by v8.6):
- v8.4 (Row 2 register asymmetry closure + Panel B sample-boundary clarity):
  - §3.2 NEW Setup-context rule (≤ 0.5cm mini-icons, mono cGray, ≤ 0.30pt, peripheral-vision read)
  - D-6 NEW kinetic-measurement setup icon (current source + sample slab) at (3.05, 3.30)
  - E-5 / F-6 NEW shared ISPD-apparatus icon (corona needle + sample + Kelvin probe) at (7.05, 2.55) — single icon binds E↔F per §6 paired ISPD
  - B-4 sample boundary divider lines (post-v8.7 iter1: 2 dotted cGray!40 between 3 representative chains)
  - Total sub-regions 53 → 56
- v8.3 (briefing-grounded audit closure):
  - Gap #1 C-R1b shallow Gaussian σ 0.06 → 0.085 (briefing §13.3 spec)
  - Gap #2 C-R5 ΔE_t arrow + label color cGray!70!black → cRed!75!black (binds depth scalar to deep trap species per §8.6 / §13.9 Binding-1)
  - Gap #4 Row2-Caption em-dash: `--` → `---` (rendered – → —)
- v8.2 polish (IoU collision closure):
  - Panel A subtitle 'poly(S-r-DIB) linear copolymer' y 5.55 → 5.42 (descender/ascender clip)
  - Panel A 'inv. vulc.' (2.55, 8.00) → (2.15, 7.82) (S8 vertex bump)
  - Panel G G-6 Coulomb / repulsion anchor flip + y 2.09/1.91 → 2.04/1.94 (see §13.8 G-6)
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
- #17 dashed-line semantics (Debye D-3 + escape C-R4 + inv.vulc. A-6 + leaders): **CLOSED v8.5** — consolidated into briefing §17 with locked semantic table + discrimination rules + forbidden-use list.

---

## §18. Cross-figure consistency (paper-wide anchors, v8.5 NEW)

Fig 1 is the paper's **identity figure** (cover + graphical-abstract role).
Its conventions establish the visual grammar that Fig 2..6 must inherit.
Without an explicit inheritance clause, sister-figure authors silently
diverge → reader sees "different paper" across panels → narrative coherence
breaks.

**Locked paper-wide anchors set by Fig 1** (Fig 2..6 SHALL conform):

1. **Color binding** (§8.6 / §13.9 Binding-1, v8.3 strengthened):
   - Shallow trap species → `cBlue` family (border `cBlue!85!black`, fill
     `cBlue!18..25`, accent `cBlue!75..80!black`).
   - Deep trap species → `cRed` family (border `cRed!85!black`, fill
     `cRed!18..25`, accent `cRed!75..80!black`).
   - Trapped-charge marker (`q_tr`, `q_clip`) → cRed family (Binding-2 per
     §13.9 inherits to Fig 5).
   - Polymer / material identity → `cAmber` family (A/B/C-L sheet/G strip).
   - Gray / neutral references (axis, dimension, secondary annotation) →
     `cGray!55..75!black`.
   - **Forbidden**: re-using cBlue for non-shallow or cRed for non-deep
     semantic (e.g., Fig 5 mechanism schematic uses cRed for Coulomb arrow
     — OK because force *causes* deep trap response; cRed for Maxwell
     attraction would violate).

2. **Typography hierarchy** (§10):
   - panel-letter `\bfseries 9.5pt` (`labelStrong` family + `panelLetter` style)
   - region-label `\bfseries 8.5pt`
   - axis-label `\itshape 7.5pt`
   - tick-label / sub-annotation `\itshape 7pt` or smaller
   - mini-icon / setup `\itshape 5.5pt`
   - **Forbidden**: serif fonts anywhere; Times / Computer Modern in math
     (use `\sffamily` consistently). Variable symbols italic, units upright,
     subscript labels (sample names) upright.

3. **Line-weight tiers** (§10 3-tier):
   - Mechanism / hero (trap level lines, force arrows, primary curves):
     1.0–1.5pt
   - Curve / measurement: 0.6–0.8pt
   - Reference / leader / annotation: 0.2–0.4pt
   - **Forbidden**: line weights > 1.5pt (cover-feel grain too coarse) or
     < 0.18pt (print loss).

4. **Arrow tip style** (§10): one tip style throughout the paper = `Stealth`
   (sized per element: 4pt for inter-panel, 6–8pt for primary force/spoke).
   - **Forbidden**: latex-tip, harpoon, triangle — mixing tip styles makes
     "different arrows = different processes" cue noisy.

5. **Dashed-line semantics** (§17): 4 locked semantics (reference / dynamic
   transition / chemical transformation / binding leader) with color, weight,
   and density discrimination rules. Sister figures may use only these 4;
   new dashed meanings require §17 amendment AND amendment must be
   echoed in Fig 1 (so the figure's grammar shifts together).

6. **Gradient + light source** (§9 LOCKED): upper-left light source for all
   gradient fills (`top color=lighter, bottom color=darker` or `left color=
   lighter, right color=darker`). Panel C-L4 anchors the convention.

7. **Setup-icon discipline** (§3.2): ≤ 0.5cm bbox per icon, monochrome
   cGray!75!black stroke only, ≤ 0.30pt line, peripheral-vision read.
   Sister figures showing measurement context must follow same size cap.

8. **Composition labels** (§8.8): sample names S60/S70/S75/S80/S85 (5 samples in paper) only in
   composition-variable panels (Fig 1 Panel B + Fig 4 composition sweep);
   forbidden on result panels (Fig 1 Row 2 + Fig 2/3 plots = concept labels
   like "high n" / "low n" only — 2026-05-20 rewrite from deprecated "deep-rich" / "shallow-rich").

**Inheritance protocol**:
- Each new figure's briefing must include a `§-cross-figure-check` section
  enumerating which §18 anchors apply + any explicit exceptions with
  justification.
- Cross-figure violations are caught at QUALITY_AUDIT stage (new theory
  guard TG-CFG-002: "Color / typography / line-weight conventions match
  Fig 1 anchor or have documented exception").

**Out of scope of §18** (paper-author decision, not figure-agent's):
- Equation rendering (Methods / Discussion text)
- Citation typography
- Caption formatting style (handled by §14 caption template — DEFERRED
  pending separate add)
- Provenance / AI-image policy statement (handled by §16 — DEFERRED
  pending separate add)
