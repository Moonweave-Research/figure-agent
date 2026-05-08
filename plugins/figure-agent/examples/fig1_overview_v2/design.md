# Fig 1 Overview Design — fig1_overview_v2

**Version**: v2.1 (2026-05-08, Q&A 인터뷰 + 어드바이저 final review 반영)
**Status**: Locked. 남은 implementation detail (arrow weights, plot tick density, qtr marker count, atom 정확한 배치)은 first compile 후 visual judgment로 결정.

**v2.1 변경 (어드바이저 final review):**
- Issue 1: Panel D 라벨을 *concept-based* (shallow-rich/deep-rich)로 정정 — composition 라벨 (S60/S85) 금지 명시. Fig 3 영역 침범 회피.
- Issue 2: Panel B 중간 chain 라벨 *"..." 제거* — enumeration 톤 회피.
- Issue 3: Framing 표현 *"3 lines of evidence (kinetic, ISPD, mechanical)"* 로 통일.
**Source-of-truth precedence**: 본 문서 > reference image. Reference는 layout/style anchor only.
**Plan reference**:
- `02_Surfur_Polymer/docs/figure_set/planning/detailed_figure_composition.md` (v9.7)
- `02_Surfur_Polymer/docs/figure_set/designs/fig1_overview_design_260505.md` (4-bit semantic carryover)
- `reference/codex_gen_overview_v1.png` (layout + visual style anchor only)

---

## 1. Figure-level intent

### 1.1 30-second message

> *"기존 sulfur-rich polymer에서 deep charge trap을 발견했고, 다중 독립 측정이 같은 trap 모델로 수렴하며, Coulomb 척력으로 거시적 발현된다."*

### 1.2 Argumentative spine

```
재료 정의 (이미 알려진 sulfur polymer)
   ↓ (구조: 한 시료 안에 다양한 길이의 S-chain 분포)
Deep charge trap이 *발생*하는 무대
   ↓ (3 lines of evidence — kinetic, ISPD, mechanical — 같은 trap으로 수렴)
   ├── Kinetic line (I(t) ~ t⁻ⁿ, time domain)
   ├── ISPD line (Vₛ(t) raw → g(Eₜ) derived, paired transformation)
   └── Mechanical line (Coulomb 척력 = trapped charge 직접 증거)
```

### 1.3 Framing 원칙 (v9.7)

- **Subject = charge trap phenomenon. Bending = macroscopic probe (NOT showcase).**
- 키워드 회피: electret, bidirectional, actuation, device (응용 톤)
- 톤: "macroscopic probe" / "polarity-dependent bending" / "trap dynamics manifest"
- 본 figure는 L1 (현상 발견의 무대) + L3 (probe) hook. L2 tunability는 제목 + Fig 3+4가 짊어짐.
- **Soft tunability OK** — 시료 함량 라벨 (S60, S85)은 cover에 나옴. Hard sweep curve / 함량별 색 그라데이션은 X.

---

## 2. Layout + Visual flow

### 2.1 Layout (locked)

- **2-row × 7-panel** 구조
- Canvas: 178 mm wide (NatComm 2-col) × ~120 mm tall
- **Row 1 (top)**: Panel A | B | **C (HERO #1, 폭 1.5×)** — 재료 → 구조 → trap 발생
- **Row 2 (bottom)**: Panel D | E ↔ F | G — 측정 evidence (3 lines)
- **Row 1 → Row 2**: Panel C 하단에서 Row 2 상단으로 vertical arrow + 라벨 *"convergent evidence"*

### 2.2 Visual flow principle (locked)

핵심: **유기적 스토리, NOT 7개 분리된 박스.**

| 원칙 | 구현 |
|------|------|
| **No hard panel borders** | 패널 박스/배경 fill X. Row separator 선/배경톤 X. |
| **Row separator 처리** | Row 1↔Row 2 사이는 *vertical arrow + 라벨*만으로 분기 표시. 가로선 X, 배경 톤 차이 X. |
| **Element continuity** | 7 panel 전체 동일 팔레트, 동일 line weight, 동일 atom size scale |
| **Inter-panel arrow** | Hybrid — Row 1↔Row 2 수직만 라벨 (*"convergent evidence"*), 좌우 panel 사이 화살표는 clean (라벨 X) |
| **Reading flow** | 좌→우, 상→하 자연 흐름 |
| **헤더 처리** | Inline 라벨만 (panel 안의 시각 요소 옆에 작은 라벨). Panel 위 별도 헤더 X. 알파벳 마커 (a, b, c) X — caption 매핑은 후속 figure 작업에서. |

### 2.3 Reference 정정 사항 (필수)

| 결함 | 정정 |
|------|------|
| **Panel G cantilever 방향** | reference는 클립이 아래 → 실제 setup은 *클립이 위, 캔틸레버 hanging down*. 정정 |
| **Panel G Maxwell 화살표** | reference는 Coulomb + Maxwell 양쪽 — design intent는 Coulomb 단일. **Maxwell 제거** |
| **Panel C 색상 매핑** | reference는 좌=blue 깊은 well / 우=red 얕은 well — Q1 color convention과 충돌. **좌=shallow blue (얕은 well) / 우=deep red (깊은 well)으로 뒤집기** |
| **Hero 위계 부재** | reference는 7-panel 평등 분포 — Panel C 폭 1.5× + Panel F deep peak 1.8× shallow로 hero 회복 |
| **Panel B 함량별 색 그라데이션** | reference는 chain별 색 차이 가능 — *모든 chain 동일 gold*로 통일 (함량별 색 차이 거의 없는 실제 시료에 정합) |

---

## 3. Narrative mapping

### 3.1 4-bit (design v260505) → 7-panel

| 4-bit | 7-panel | 의미 운반 |
|---|---|---|
| **① Material** | A (network) + B (S-chain 분포) | 재료 + 분자 heterogeneity |
| **② Trap site (HERO #1)** | C (localized traps) | trap이 *발생*하는 자리 |
| **③④ Convergent evidence (3 lines)** | D (kinetic) + E↔F (ISPD) + G (mechanical) | 3 lines of evidence 수렴 |

### 3.2 Evidence framing — 3 lines of evidence

- **Panel D — Kinetic line** (time domain): I(t) ~ t⁻ⁿ
- **Panel E ↔ F — ISPD line** (paired transformation): Vₛ(t) raw → g(Eₜ) derived
- **Panel G — Mechanical line** (macroscopic): Coulomb 척력 = trapped charge 직접 증거

→ P-E hysteresis는 본문 Fig 2 (universal dielectric)의 일. Cover에서 빠짐.
→ ISPD line은 *paired E↔F transformation*으로 구현되지만 framing 상 *one line of evidence*.

---

## 4. Per-panel design

### Panel A — Sulfur-rich network (sparse identifier)

- **Semantic claim**: *"이 paper의 시료는 inverse vulcanization으로 만든 sulfur-rich polymer다."*
- **Role**: 재료 식별. 시각 무게는 가벼움 (HERO #1인 Panel C에 시각 무게 양보).
- **Design (Split 2 — sparse identifier)**:
  - **Network**: ~12 atoms (8 S gold + 4 C gray), 불규칙 cross-linked topology, manual TikZ 배치 (spring layout 사용 X)
  - **S₈ ring inset**: 우상단 corner, 작게 (Panel A 면적의 ~20%). chemfig `*8(-S-...-)`.
  - **Inline 라벨**: 네트워크 옆 *"polymer network"*, S₈ 옆 *"S₈"*
- **Forbidden**:
  - 24+ atoms (rich network — Panel C와 redundant, hero 위계 invert)
  - S₈을 panel 중앙에 두기 (Q11 결정대로 corner inset)
  - 결정 격자 패턴 (amorphous decoration)
- **Render approach**:
  - S₈ → `chemfig` `*8(-S-S-S-S-S-S-S-S-)` with `atom style` (gold fill)
  - Network → manual TikZ nodes
- **Connection out**: 우측 화살표 (clean, 라벨 X) → Panel B

### Panel B — S₆₀–S₈₅ chain length (soft tunability)

- **Semantic claim**: *"우리는 S60–S85 범위에서 시료를 따로 제작했다."*
- **Role**: ① Material의 sub-element. 시료 함량 범위 노출 (soft tunability).
- **Design**:
  - **4개 horizontal chain** (subitizing 한계 ≤4 → counting effort 0)
  - 위→아래로 짧음 → 긺 (S% ↑ → 평균 chain 길이 ↑)
  - 각 chain: gold S 원자 + gray cross-link 원자 + bond. **모든 chain 동일 gold** (함량별 색 그라데이션 X)
  - **Inline 라벨**: top chain 옆 *"S₆₀"*, bottom chain 옆 *"S₈₅"*, **중간 두 chain 라벨 X** (4개 chain 자체가 *범위* 운반, "..." enumeration 신호 회피)
  - 하단 axis arrow + *"S-chain length →"* 라벨
- **Forbidden**:
  - 함량별 sweep curve / 색 그라데이션
  - 5개 이상 chain (enumeration 톤, Fig 3 redundancy)
  - 정량 plot
- **Render approach**: manual TikZ chains (간단한 chain 패턴)
- **Connection out**: 우측 화살표 (clean) → Panel C

### Panel C — Localized traps (HERO #1)

- **Semantic claim**: *"이 network 안에서 *deep + shallow* trap이 발생한다. Deep trap이 *우세*다."*
- **Role**: ② Hero. trap 발생 자리 + visual focal point.
- **Design (Split 2 — rich integrated network + trap)**:
  - **Background**: polymer network 24–30 atoms (Panel A의 sparse identifier보다 풍부), 불규칙 amorphous topology, faded/lighter (network detail 뒤로)
  - **Foreground**: Asymmetric potential energy landscape — 좌→우로 진폭 증가 (좌측 얕은 wave, 우측 깊은 wave)
  - **좌측 region (shallow, blue)**: 3 well + 3 blue ⊖ electron
  - **우측 region (deep, red)**: 4 well + 4 red ⊖ electron + **1–2 escape arrow up (dashed)** — Panel D의 *distributed release* narrative 시사
  - **Hero 강조 수단**: well 깊이 좌→우 증가 + 개수 비대칭 (3 vs 4) + electron 개수 비대칭 + red saturation (deep) > blue (shallow) + escape arrow
  - **Inline 라벨**: *"shallow"* (좌), *"deep"* (우), *"localized traps"* (panel 안 어딘가)
  - **폭**: Row 1 안에서 1.5× (A, B 대비)
- **Forbidden**:
  - Sinusoidal symmetric landscape (deep > shallow asymmetry 메시지 약화)
  - shallow ≥ deep 개수 (hero 실패)
  - Eₜ 정확 수치 라벨 (정량은 Fig 3)
- **Render approach**:
  - Background network → manual TikZ
  - Energy landscape → `\draw plot` 또는 manual bezier
  - Wells/electrons → TikZ nodes
- **Connection out**: 하단 vertical arrow → Row 2 + 라벨 *"convergent evidence"* (figure 전체 row-transition signal, line weight 강하게)

### Panel D — Kinetic evidence (I(t) ~ t⁻ⁿ)

- **Semantic claim**: *"Trap된 charge의 release는 power-law I(t) ~ t⁻ⁿ — non-Debye, distributed timescales."*
- **Role**: ③ Evidence #1, time domain.
- **Design — Multi-slope iconic plot (밀도감 있는 hybrid):**
  - **2개 I(t) 곡선** (single 아닌 multiple — n 의미 운반):
    - 위쪽 (가파른 slope, blue 계열): *shallow-rich* 케이스 — larger n → faster decay → 짧은 tail
    - 아래쪽 (완만한 slope, red 계열): *deep-rich* 케이스 — smaller n → 긴 non-Debye tail
  - **Gray dashed Debye reference** (e⁻ᵗ/τ): 두 곡선 모두 Debye 대비 *"평탄한 power-law tail"* 시각 대비
  - **메인 라벨**: *"I(t) ~ t⁻ⁿ"* (수식 자체가 메시지)
  - **Side 라벨 (concept-based, NOT composition-specific)**:
    - 위쪽 곡선: *"shallow-rich"* 또는 *"low n"* (또는 *"n ↑ → closer to Debye"*)
    - 아래쪽 곡선: *"deep-rich"* 또는 *"high n"* (또는 *"n ↓ → more non-Debye"*)
    - **금지 라벨**: *"S₆₀"*, *"S₈₅"*, 또는 다른 composition specific 식별자 — Fig 3(a)(b)의 정량 결과 (n vs composition) 영역 침범
  - **Axis**: 미니멀 — *"log t"*, *"log I"* 화살표만. tick 수치 X (또는 매우 옅은 회색 보조)
  - **non-Debye tail 영역**: 두 곡선이 Debye보다 위로 vouching하는 long-time 영역에 옅은 highlight + *"non-Debye"* 라벨
  - **부가 요소 OK**: 곡선 끝에 작은 trap icon 또는 시간 hint 등 (밀도감 있게 복합)
- **Forbidden**:
  - 정확한 axis 수치 (실측 데이터 톤 — Fig 3와 redundancy)
  - 단일 곡선 (n 의미 운반력 약화)
  - 곡선이 Debye 아래 (물리 violation)
  - **Composition-specific 라벨** (S60/S85 등) — Fig 3 영역 침범
- **Render approach**:
  - `pgfplots` `paper loglog/.style` (preamble의 매크로 사용 가능)
  - 부가 schematic은 raw TikZ overlay

### Panel E ↔ F — ISPD evidence (paired transformation)

**핵심**: Vₛ(t)와 g(Eₜ)는 *독립 측정 아님*. Vₛ(t) → 수학적 inversion → g(Eₜ) 의 *같은 측정 변환*. 두 panel을 *paired*로 시각화.

#### Panel E — Vₛ(t) decay (ISPD raw)

- **Semantic claim**: *"표면 전위가 시간에 따라 감소 — trap된 charge가 누출되는 raw 신호."*
- **Design**:
  - 단일 plot (Vₛ vs t, log-log)
  - Open circles data points (schematic)
  - Inline 라벨: *"Vₛ(t)"* (axis), *"surface potential decay"* (panel 안)
  - Plot frame style: Panel F와 *동일* (color-linked, 같은 axis style/font/line weight)

#### Panel F — g(Eₜ) (ISPD-derived DOS, HERO #2)

- **Semantic claim**: *"Trap DOS는 *bimodal* — shallow + deep. Deep peak이 우세 (1.8× shallow)."*
- **Design**:
  - 좌 Gaussian (blue, shallow) + 우 Gaussian (red, deep)
  - **Deep peak height = shallow × 1.8** (강한 비대칭, hero 위계 보강)
  - τ_d 양방향 화살표 두 peak 사이 (선택적, 이상적이면 포함)
  - x label: *"Shallow"* (좌), *"Deep"* (우), y label: *"g(Eₜ)"*
  - 폭: 평등 (Row 2 trio 응집 유지)
  - Plot frame style: Panel E와 *동일*

#### Paired visual treatment (E ↔ F)

- **두 panel 사이 짧은 arrow** + 라벨 (예: *"ISPD"* 또는 *"→ g(Eₜ)"*) — 의존성 시각 인정
- **같은 plot frame** (axis style, font, line weight)
- **색 연계** — Panel E의 데이터가 어떤 trap에서 오는지 시사하기 위해 plot 내 annotation 또는 색조에 blue/red hint 가능
- **Forbidden**:
  - E를 F의 단순 precursor로 강등 (E 자체의 *raw observation* identity 보존)
  - 두 panel이 시각적으로 *동떨어진* 별도 plot으로 보이기

### Panel G — Mechanical evidence (Coulomb 척력)

- **Semantic claim**: *"Trap dynamics는 polarity-dependent transient bending으로 발현. Coulomb 척력 = trapped charge 직접 증거."*
- **Role**: ③ Evidence #3, mechanical (macroscopic) domain.
- **Design**:
  - **Isometric 3D 시점** (살짝 입체감, 평면 2D 또는 풀 perspective 아님)
  - **Hanging cantilever** — 클립이 *위*에 있고 polymer strip이 hanging down (reference 정정)
  - **Polymer strip** (gold, bent away from electrode)
  - **Electrode** (gray block, vertical)
  - **qₜᵣ markers** (trapped charge 표시, polymer strip 안쪽)
  - **Coulomb 척력 화살표** — red, polymer에서 electrode 반대 방향. 단일 (Maxwell 제거)
  - **air gap 라벨** — strip과 electrode 사이 gap 표시
  - **Inline 라벨**: *"Coulomb repulsion"*, *"qₜᵣ"*, *"air gap"*
  - **클립 표시**: 위쪽 작은 직사각형으로 hanging 시각화
  - **바닥 받침대 생략** (cantilever가 hang하는 구도면 불필요)
- **Forbidden**:
  - **Maxwell attraction 화살표**
  - 클립이 아래
  - "Bidirectional Actuation" / "Actuator" tone label
- **Render approach**: manual TikZ (3D-like isometric)

---

## 5. Inter-panel connection

| 연결 | 화살표 / 스타일 | 라벨 |
|---|---|---|
| A → B | 우측 horizontal Stealth, gray, line weight standard | (clean, 라벨 X) |
| B → C | 우측 horizontal Stealth, gray | (clean) |
| **C → Row 2** | **하단 vertical Stealth, gray, line weight 강하게** | **"convergent evidence"** (8–9pt) |
| D → E | 우측 horizontal Stealth, gray | (clean) |
| **E ↔ F** | **두 panel 사이 짧은 arrow** | **"ISPD"** 또는 **"→ g(Eₜ)"** (변환 인정) |
| F → G | 우측 horizontal Stealth, gray | (clean) |

---

## 6. Style Lock + palette

- **Style source**: `polymer-paper-preamble.sty`
- **팔레트**:
  - cAmber / cAmberSphere / cArmAmber: S 원자, polymer strip
  - cBlue: shallow trap region, shallow Gaussian, electron (shallow), shallow-dominant I(t) 곡선, Maxwell (제거됨)
  - cRed: deep trap region, deep Gaussian, deep electron, deep-dominant I(t) 곡선, Coulomb arrow
  - cGray / cLGray: connector atoms, axes, electrode, Debye reference, inter-panel arrow
- **Typography**: NatComm sans (Helvetica/Arial). Inline 라벨 7–8pt, 강조 라벨 8–9pt
- **Line weight**: ≥ 0.5pt, 강조 선 0.8–1.0pt
- **Background**: 패널 fill 제거 (white). Row separator X.

---

## 7. 패키지/매크로 사용 정책

| 도구 | 용도 |
|---|---|
| `chemfig` | Panel A S₈ ring (atom style로 gold fill), Panel B chain |
| `pgfplots` (`paper loglog/.style`) | Panel D I(t), E Vₛ(t), F g(Eₜ) |
| **`graphdrawing` (`spring layout`) — 사용 X** | 좌표 통제 불가 입증됨 |
| Raw TikZ | Panel A network 배치, Panel C trap landscape, Panel G probe |
| `polymer-paper-preamble` 매크로 | 우선순위 낮음 — 패키지 직접 사용이 투명 |

---

## 8. Success criteria

1. 독자가 Fig 1만 보고 30초 안에 *"sulfur polymer의 deep charge trap → 다중 측정 수렴 → Coulomb 척력 발현"* 파악
2. 7-panel이 *분리된 박스* 가 아니라 *연속 스토리*로 읽힘 (시각 흐름 검증)
3. Panel C trap region의 *deep > shallow* 비대칭이 명확 (well 깊이 + 개수 + saturation)
4. Panel F g(Eₜ) deep peak = shallow × 1.8
5. Panel G에 Coulomb 단일 화살표만 (Maxwell 제거 확인)
6. Panel G cantilever 클립이 위 (정정 확인)
7. Panel C 색상 매핑 (좌=shallow blue / 우=deep red, reference 정정 확인)
8. Panel E ↔ F가 *paired ISPD transformation*으로 읽힘 (의존성 시각 인정)
9. Style Lock 통과, NatComm 178mm × ~120mm
10. v9.7 framing 키워드 위배 X (electret/actuator/device tone 없음)

---

## 9. Reference 역할 재정의

- **Reference는 style/composition anchor만**:
  - 색상 톤 (gold sulfur, blue/red trap)
  - 원자 크기 비율, line weight 분위기
  - 7-panel 공간 분할 비율 (대략적)
- **Reference는 content authority가 아님**:
  - 클립 방향 (정정 대상)
  - Maxwell 화살표 (제거 대상)
  - Hero 위계 (회복 대상)
  - Panel C 색상 매핑 (정정 대상)
  - 함량별 색 그라데이션 (제거 대상)
- **충돌 시 본 design.md 우선**.

---

## 10. Implementation order (locked)

1. **design.md v2 잠금** ✓ (2026-05-08)
2. **fig1_overview_v2.tex 전면 재작성** (현재 Panel A draft는 Split 2 결정에 따라 sparse identifier로 재작성)
3. **Panel C (HERO #1) 먼저** — 메시지 가장 무거움. 24–30 atoms + asymmetric landscape + 3 shallow well + 4 deep well + escape arrow
4. **Panel F (HERO #2)** → Panel E ↔ F paired
5. **Panel D (kinetic)** — multi-slope plot
6. **Panel A, B** (재료) → Panel G (probe)
7. **Inter-panel 연결자 통합** → 시각 흐름 검증
8. `/fig_compile` → first compile 후 *남은 detail* (arrow weights, plot tick density, qtr marker 개수, atom 정확한 배치) visual judgment로 결정
9. `/fig_critique` (host vision review) → 수정 루프
10. `/fig_export` (PDF/SVG/TIFF/PNG)

---

## 11. 남은 detail (compile-iterate territory — 미리 잠그지 않음)

- Inter-panel arrow line weight, length, gap
- Plot tick density / 수치 표기 정도
- Panel G qₜᵣ marker 개수
- Panel A 정확한 atom 좌표 배치
- Panel C 정확한 atom 배치 + landscape 곡선 진폭 비율
- Panel B chain 정확한 길이 비율
- Panel F τ_d 화살표 포함 여부

→ first compile + 시각 판단으로 잡음. design.md 미리 잠그지 않음.

---

## 12. Q&A 결정 기록 (2026-05-08)

| Q | 결정 | 근거 |
|---|---|---|
| Q1 색상 | Blue=Shallow / Red=Deep | planning 문서 + Panel F (g(Eₜ)) reference 라벨 정합 |
| Q2 Panel C 배치 | 좌=shallow blue, 우=deep red, hero 강조는 well 깊이+개수+saturation+electron 개수 | Panel F와 좌우 매핑 일관 + reading flow |
| Q3 Hero 면적 | Panel C만 1.5× (Row 1 dominant), Panel F 평등 | trio 응집 유지 + Hero 위계 회복 |
| Q4 deep peak 비율 | shallow × 1.8 | 강한 비대칭, hero 위계 보강 |
| Q5 Panel B | Soft tunability OK, 모든 chain 동일 gold (함량별 색 변화 X) | 시료 색 차이 거의 없음 (사용자 정정) |
| Q6 헤더 | Inline 라벨만, 알파벳 마커 X | 유기적 연속 원칙 |
| Q7 화살표 | Hybrid — Row 1↔Row 2 수직만 라벨 | clean default + narrative 분기점만 명시 |
| Q8 수직 화살표 라벨 | "convergent evidence" | 3 line evidence 수렴 의미 |
| Q9 landscape | Asymmetric (좌→우 진폭 증가) | deep > shallow 메시지를 곡선으로 직접 |
| Q10 well/electron | Shallow 3+3 / Deep 4+4 + 1–2 escape arrow | 균형 + 동적 의미 |
| Q11 Panel A 배치 | Network 메인 + S₈ 우상단 작은 inset | "S₈이 building block" hint |
| Q12 Panel G | Isometric 3D, 클립 위, air gap 라벨 표시, 받침대 생략 | hanging cantilever 정합 |
| Q13 Panel D | Multi-slope iconic plot (2 곡선 + Debye + non-Debye 라벨), 라벨은 **concept-based** (shallow-rich/deep-rich, low n/high n) — composition 라벨 X | data가 아니라 concept 운반 + Fig 3 영역 회피 (어드바이저 final review 정정) |
| Q14 Panel E framing | 3 lines of evidence (E ↔ F paired ISPD line) | 구조 정직 (어드바이저 지적) |
| Q15 E ↔ F 처리 | Paired transformation, short arrow + "ISPD" 라벨 | 의존성 시각 인정 |
| Q16 Panel B chain | 4개 (subitizing 한계), **"..." 제거** — 양 끝 라벨 (S60, S85)만, 중간 둘 라벨 X | counting effort 0 + enumeration 톤 회피 (어드바이저 final review 정정) |
| Q17 Panel A 밀도 | sparse identifier ~12 atoms (Split 2) | Hero 위계 (C가 무거워야) |
| Q18 Row separator | 화살표만 (선/배경 X) | 유기적 연속 원칙 |
