# Briefing — fig2_trap_design_space

> **Genre**: Nature Communications **main-text Figure 2** — clean white background, schematic.
> **Decision (2026-06-20)**: Option 1 discovery-forward. Fig 2 leads with the
> composition-tunable charge-trap discovery (not the universal-dielectric baseline).
> ISPD spectroscopy → Fig 3, mechanism synthesis → Fig 4 (re-deal). Baseline
> dielectric/ferroelectric controls → SI.
> **Mode**: SCHEMATIC ONLY. Data plots (P-E, CvS, ISPD) are produced by the data
> pipeline (Origin / Graph Hub). figure-agent draws the *picture*; any graph here
> is an idealized, number-free "schematic 같은 그래프" evidence icon.

---

## §1. Topic
황고분자(poly(S-r-DIB), S60–S85)가 기존 유전체(PI/PDMS/PET)가 닿지 못하는
charge-trap 설계공간을, **조성으로 튜닝하며** 연다는 것을 한 그림으로 보여준다.
독자가 보는 첫 번째 figure-of-data-substance이며 논문의 중심 발견(L2)을 착지시킨다.

## §2. Domain vocabulary
charge trap, deep/shallow trap, Coulomb trap, S–S homolytic cleavage, sulfur radical,
low dielectric constant (ε), trap-distribution breadth (CvS exponent n),
charge retention / resistivity (ρ), power-law transient current I(t)~t^-n,
Debye reference, conventional dielectrics (PI, PDMS, PET), composition tuning.

## §3. Composition intent
좌→우 3-zone schematic.
- **Panel a (left column)** — "Origin of deep traps": S–S backbone zigzag with a
  homolytic-cleavage radical (= deep Coulomb trap); below it a Coulomb-well
  comparison (sulfur = wide + deep, low ε; conventional = shallow + narrow, high ε).
- **Panel b (center-right, HERO)** — "Composition-tunable trap design space":
  2D conceptual map. x = trap-distribution breadth & density (n, ρ), y = charge
  retention. Conventional dielectrics clustered low-left (shallow, leaky);
  sulfur S60→S85 traces an arc up-right into a shaded "beyond conventional" region;
  composition arrow = tuning knob.
- **Panel c (bottom strip)** — "Kinetic charge-trapping signature (schematic)":
  two idealized number-free icons — I(t)~t^-n (sulfur persistent / high n vs
  conventional steep / low n, Debye dashed) and n vs sulfur content (rise→plateau
  above a conventional band).

## §4. Normalize / avoid literal overfit
- 정확 n/ρ 수치, sample code, 축 tick 값, 막대 높이 → 절대 그리지 말 것 (schematic 전용).
- Panel b의 sulfur 궤적은 정확한 (n,ρ) 좌표가 아니라 "황은 canonical 클러스터에서
  멀리 떨어진 고-trap 영역을 점유하고 조성이 그 안에서 움직인다"는 **정성적 메시지**.
  단조 직선으로 그려 데이터를 호도하지 말 것 (실제 n은 S70~80 고원, S85 하강).
- PI는 trap-rich(저-n 아님) — conventional 클러스터에 두되 "얕고 새는" 일반화 라벨로.

## §5. Style notes
polymer-paper preamble. 황 = warm(cAmber/cRed), conventional = cool(cBlue),
axes/labels = cGray. 178mm 2-col landscape, 흰 배경, panel-letter a/b/c bold 8pt.

## §6. Physics invariants
- deep trap의 기원은 **S–S 라디칼 + 낮은 ε(넓은 Coulomb 우물)** — 이 인과를 보존.
- 황은 conventional 유전체를 **초월**(설계공간에서 분리된 영역) — 두 클러스터가
  겹치면 안 됨.
- I(t)∝t^-n에서 황은 n이 커 log-log 기울기가 더 **가파름**(conventional은 low-n으로
  완만), Debye는 지수 reference. n(분포 형태)과 ρ(크기)는 **독립 2-metric** —
  Panel b x=n / y=ρ, Panel c 좌=I(t) 기울기(n) / 우=ρ. 기울기·크기 순서를 뒤집지 말 것.
- Fig 1과 중복 금지: Fig 1은 "3 probe가 같은 trap으로 수렴". Fig 2는 "튜닝성 +
  canonical 초월". 에너지 다이어그램/수렴 모티프 재탕 금지.

## §7. Author intent — semantic constraints (for vision critique grounding)
(a) **Must depict**
- S–S 백본의 **homolytic cleavage 라디칼**이 monomer-level로 식별될 것 (generic 점 아님).
- Panel b에서 **두 개의 분리된 군집**(conventional 저-좌, sulfur 고-우) + 그 사이를
  잇는 조성 화살표가 명확할 것. "beyond conventional" 영역이 시각적으로 구분될 것.
- Panel c의 두 아이콘은 **축 tick 수치 없이** 곡선 형태만으로 메시지를 전달.
(b) **Must avoid**
- data-plot tone (tick 숫자, error bar, 정확한 축 눈금) 추가 금지 — schematic.
- sulfur 궤적을 깔끔한 단조 상승 직선으로 "정리" 금지 (실제는 고원+하강; 정성 arc 유지).
- Fig 1의 bimodal g(E_t) 에너지 다이어그램을 다시 그리지 말 것 (Fig 3 소관).
