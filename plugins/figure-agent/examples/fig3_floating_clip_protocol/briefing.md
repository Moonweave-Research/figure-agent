# Briefing — fig3_floating_clip_protocol

> **Genre**: Nature Communications **SI / methods** figure (not main text). Clean
> white background, schematic. A 4-phase process timeline.
> **Diagnostic intent (2026-06-20)**: figure #3, chosen as a DIFFERENT genre from
> fig1/fig2 to test which figure-agent gaps generalize. Mode: SCHEMATIC ONLY —
> the voltage waveform is a qualitative protocol strip (no numbers/ticks).

---

## §1. Topic
Floating-clip 측정 프로토콜을 한 그림으로: 접지 poling으로 전하를 주입·trap →
clip을 끊어(float) 전하를 잠금 → +V/−V drive에서 **극성에 따라 캔틸레버가 반대로
굽는다**(polarity-dependent). 이 bidirectional 굽힘이 inter-electrode에 잠긴
trapped charge의 거시적 probe임을 보인다.

## §2. Domain vocabulary
floating clip, grounded poling, charge injection/trapping, locked charge,
drive electrode, air gap, polymer cantilever, Coulomb force (qE),
Maxwell stress (½ε₀ε'E²), polarity-dependent bending, deflection.

## §3. Composition intent
좌→우 4-phase 시퀀스 (각 column = 한 phase), 상단에 전 phase를 가로지르는 V(t)
파형 strip. 각 column = 측면 단면 apparatus(상단 drive electrode plate + air gap
+ 좌측 clamp/clip + polymer cantilever beam + trapped charge dots).
- P1 Pole: clip→ground, HV 주입 화살표, charge 등장, beam 중립.
- P2 Float: clip→open switch(floating), charge 잠김, beam 중립.
- P3 +V drive: electrode "+", Coulomb force 화살표, beam **굽힘(곡률+tilt tip)**.
- P4 −V drive: electrode "−", force 반전, beam **반대 방향 굽힘**.

## §4. Normalize / avoid literal overfit
- 전압 수치, 시간 축 tick, 정확한 각도/치수 → 금지 (schematic). 파형은 정성적 step만.
- 정확한 7-phase A–G 명칭에 과적합 금지 — 핵심 4 phase(Pole/Float/+/−)만 확실히;
  세부 phase 분할은 protocol.md 확인 후 보강.

## §5. Style notes
polymer-paper preamble. cantilever/polymer = warm(cAmber), electrode/clamp = cGray,
trapped charge = cBlue dots, force/bend arrow = cRed. 178mm landscape, 흰 배경.

## §6. Physics invariants
- **Polarity-dependent**: +V와 −V의 굽힘 방향이 **반대**여야 함 (이게 핵심 novelty —
  polarity-INDEPENDENT(Hirai/Tamura)와 구별). 두 방향이 같으면 그림이 틀린 것.
- clip은 drive 중 **floating(개방)** — 전하가 못 샘. P1만 grounded.
- Coulomb력 qE(극성에 선형, 부호 반전)가 Maxwell(E², 항상 인력)을 지배 → bidirectional.
- **캔틸레버 방향 = 세로 (clip 위, 폴리머 아래로 매달림)** — lab/실험 convention. **가로 금지**
  (AI default-orientation 편향; fig1 Panel F에서도 같은 편향을 수동 교정함). 굽힘은 좌우(측면 전극 쪽).
- 캔틸레버 굽힘은 **처짐 곡률 + tilt된 tip** (rigid 직선봉 금지 — fig1 Panel F 결함 교훈).
- 전하 부호 convention(음전하 trapped, +drive가 위로 인력)은 *작도 선택* — 일관되게만.

## §7. Author intent — semantic constraints (for vision critique grounding)
(a) **Must depict**
- P3와 P4의 캔틸레버가 **명백히 반대 방향**으로 굽을 것 (polarity-dependent의 시각적 핵심).
- clip 상태가 phase마다 식별 가능: P1 ground 기호, P2–P4 open switch(floating).
- 캔틸레버 굽힘은 곡선(처짐)으로, tip이 기울어질 것 — 강체 수평봉 금지.
- 파형 strip이 4 phase(고전압 poling / 0 / +V / −V)를 정성적으로 보일 것.
(b) **Must avoid**
- data-plot tone (전압/시간 수치, 축 tick) — schematic.
- P3/P4를 같은 방향으로 굽히기 (polarity-dependent를 죽임).
- electrode/clamp를 과도하게 gizmo화 — 표준 단면 기호로 깔끔하게.
