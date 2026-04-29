# Briefing — smoke_trap_demo

## 1. What does this figure show? (1-2 sentences)

단일 polymer slab에서 charge trapping 메커니즘의 직관적 schematic — injection된 carrier가 deep trap level에 capture되어 retention이 길어지는 과정을 1-panel band-diagram cartoon으로 보여준다.

## 2. Domain vocabulary (terms, materials, mechanisms)

- Band structure: conduction band (CB), valence band (VB), bandgap
- Trap physics: deep trap level (E_t), trapped electron
- Charge dynamics: injection, capture (vertical capture arrow)
- Material context: generic polymer dielectric (재료명 일반화)

## 3. Composition intent (panel layout, flow direction)

1-panel band-diagram cartoon (smoke test 최소 구성).

**Layout**: vertical E-axis 좌측 (위→아래는 high→low energy), 가로 방향으로 band level들 평행 배치.

**Element 배치 (energy-ordered, top→bottom)**:
- CB (conduction band): 수평 청색 선, 상단
- Deep trap level E_t: 짧은 amber 수평 선분, mid-gap 영역 (CB와 VB 사이, 둘 다와 명확히 분리)
- VB (valence band): 수평 적색 선, 하단
- Trapped electron: E_t 선분 위에 점 2-3개 박혀있음 (level-localized 상태)

**Arrows**:
- Injection arrow: 좌측 외곽 → CB level로 진입 (화살표 head가 CB 선에 정확히 닿음)
- Capture arrow: CB → E_t 수직 하강 (electron이 phonon emission으로 deep trap에 떨어지는 의미)

**Caption (panel 하단)**: "long retention via deep trap"

**Flow**: 좌→우 (injection 시작) + 위→아래 (capture 흐름).

**Physics constraints (보존)**:
- E_t는 반드시 bandgap 내부 (CB 아래, VB 위)
- Trapped electron은 E_t level 자체에 위치 (자유 상태로 gap에 떠있지 않음)
- Trap level은 짧은 선분 (localized state) — 전체 가로폭의 line 아님
- Injection은 CB로 들어가고, Capture는 CB→trap (반대 방향 아님)

## 4. Normalize / avoid literal overfit

Image-gen이 과하게 literal하게 따라가면 안 되는 항목 (정규화 audit에 포함):
- Exact trap depth value (E_t 수치, eV 단위) → generalize as "mid-gap"
- Specific polymer material name (PDMS, sulfur polymer 등) → keep as "generic polymer dielectric"
- Sample dimensions / thickness → omit entirely (not central to trapping mechanism)
- Exact trapped electron count (정확 4개, 5개 강요 X) → qualitative "2-3개 points"
- Injection energy / voltage numbers → omit (mechanism-only, not measured)
- Bandgap value (eV) → omit (illustrative-only, not real material)

## 5. Style notes (optional)

Nature schematic minimal style — follow polymer-paper-preamble.sty. No additional style preference.

---

When this briefing is filled, run `/fig_prompt smoke_trap_demo` to generate the normalized prompt for external image generation.
