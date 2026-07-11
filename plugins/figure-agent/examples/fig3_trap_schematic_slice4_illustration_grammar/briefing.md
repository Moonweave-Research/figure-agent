# Briefing — fig3_trap_schematic_slice4_illustration_grammar

> **Slice 4 review derivative.** The historical Slice 3 fixture remains
> immutable. Only Panel e's declared `sulfur_trap_domain` boundary is lowered
> from one neutral scene through paired TikZ and SVG backends. The inherited
> physics invariants remain authoritative; machine validation is not
> publication acceptance.

> Sulfur polymer paper Fig 3 schematic panel set (v9.7 framing — charge-trap-centered).
> All-schematic, multi-panel, fresh authoring. Legacy `fig3_trapping_concept/` superseded.

## 1. What does this figure show? (1-2 sentences)

Sulfur polymer trap-mediated charge dynamics의 측정→해석→화학적·물리적 원인을 multi-panel schematic으로 통합 — 독자에게 Fig 3 정량 데이터(I(t), n, g(E_t), τ_d)의 conceptual scaffold을 제공해, "왜 sulfur polymer에서 trap이 풍부하고 그것이 어떻게 측정·해석되는지"를 한 figure에서 이해하도록 한다.

## 2. Domain vocabulary (terms, materials, mechanisms)

- **Setup (a)**: electrode, polymer film, voltage bias, leakage current, time axis
- **Power-law (b)**: power-law I(t) ∝ t⁻ⁿ, Debye exp(−t/τ), exponential decay, log-log qualitative shape
- **Trap interpretation (c)**: trapping index n, deep trap, shallow trap, no-trap limit (Debye), trap-controlled hopping
- **Chemistry (d)**: sulfur atom (S), S–S bond, electron affinity, electron-trapping site, polymer backbone, sulfur-rich segment
- **Structure (e)**: linear polymer backbone (not cross-linked), sulfur-rich domain along chain, chain entanglement, trap site distribution, amorphous chain packing
- **Convergence (f)**: trap depth distribution, ISPD g(E_t), discharge time τ_d, multi-modal convergence, shallow + deep trap

## 3. Composition intent (panel layout, flow direction)

6-panel schematic, 측정→해석→원인 순 narrative. 좌→우 + 위→아래 흐름.

- **(a) 측정 셋업** — experimental setup schematic (2D side-view): polymer film between electrodes, voltage bias, current meter, time-axis. 측정이 "어떻게" 이루어지는지 직관적으로.
- **(b) 멱함수의 이해** — qualitative I(t) ∝ t^(-n) cartoon vs Debye exp(-t/τ) 대비. log-log axis cartoon (axis tick 없음, 두 곡선 모양만 비교). "왜 power-law가 trap의 시그니처인가" 개념 설명.
- **(c) Trapping index n 해석** — 3-up cartoon comparison: high n (trap-rich, deep) / low n (few/shallow) / no trap (pure Debye). 같은 axis 위에 3개 곡선 모양만 qualitative하게 overlay.
- **(d) 화학적 원인** — sulfur-rich segment, S-S bond, electron affinity 도식. molecular-level view (sulfur 원자 + 인접 결합 + 전자 trapping site 표시).
- **(e) 물리적 원인** — **linear polymer chain** (cross-link 없음) + sulfur-rich segment 분포, trap site density. micro-structure isometric or side view, 사슬 형태 강조 (network/cross-link 그려지지 않음). sulfur cluster 영역에 trap marker 분포.
- **(f) Multi-modal convergence** — n exponent / g(E_t) / τ_d 세 metric의 qualitative shape이 한 화살표 또는 venn-overlap으로 "consistent trap depth distribution" 라벨을 향함. axis tick / 수치 없음, 모양 hint만. Fig 3 데이터의 핵심 논거 ("3 independent metrics converge")를 conceptual hook으로 미리 깔아준다.

<!-- AUTHOR NOTE (not for prompt) — contingency on 2026-04-28: v9.7 문서의 ISPD/τ_d Fig 3 잠정 flag 참고. 만약 ISPD/τ_d가 Fig 4로 이동하면 panel (f)는 n exponent 단독 hook (예: composition tunability cartoon)으로 재설계 필요. -->


각 panel 하단에 한 줄 sub-caption. Panel 사이 명시적 화살표는 일반적으로 없음 (narrative는 layout 흐름이 자명).

## 4. Normalize / avoid literal overfit

Image-gen이 절대 literal하게 그리면 안 되는 항목 (band 영역 한정):
- **정확 trap depth value (E_t in eV)** → "deep / shallow level" 상대적 qualitative만
- **Bandgap value (eV)** → 수치 X, CB↔VB 상대 위치만

(나머지 sample code / sulfur wt% / n exponent value / time tick / voltage / sample dimension / trap-electron count / equipment 모델 / domain size / monomer 화학식 등은 사용자 판단에 따라 일반화 불필요 — image-gen이 적절히 해석하도록 둠.)

## 5. Style notes (optional)

Nature schematic 스타일 — 양식을 절대 벗어나지 않음.
- **Layout**: 3×2 grid 우선 (행 1: a-b-c, 행 2: d-e-f). 시각적 균형이 안 맞으면 2×3 또는 다른 적절한 layout으로 fallback.
- **Width**: Nature double-column (~183mm) 권장 — 6 panel을 한 figure에 응집.
- **Background**: white / 패널마다 light-gray rounded rectangle (cLGray!22) 패턴 (`fig3_trapping_concept` 참고).
- **Palette** (polymer-paper-preamble): cBlue=conduction/electron, cRed=valence, cAmber=trap, cGray=axes/labels, cTeal=accent.
- **Font**: sans-serif (Arial via fontspec), Nature scale.
- **Headers**: panel 좌상단 (a)-(f) bold + 한 줄 gray sub-title (예: "(a) measurement setup", "(b) power-law signature" 등).
- **Sub-captions**: 각 panel 하단 한 줄, bold.
- **Axes**: 정량 tick 없음 — qualitative shape만.

## 6. Physics invariants (preserved verbatim in prompt)

1. Polymer is a **linear chain** — no cross-links, no network nodes, no branches connecting separate chains. Sulfur clusters appear as side groups along the chain only.
2. Trap level lies **inside the bandgap** (between CB and VB), drawn as a **short localized line segment** — not a full-width line.
3. **Trapped electrons sit ON the trap level itself** — not floating freely in the bandgap.
4. When the time-current axes are plotted on **double-logarithmic (log-log) scale**: (i) power-law I(t) ∝ t⁻ⁿ appears as a **straight diagonal line** (slope = −n); (ii) Debye exp(−t/τ) appears as a **curved line that bends downward more steeply at later time** (concave-down). This visual contrast IS the trap signature.
5. Panel (c) shows three qualitative curves on the same log-log axes: (i) high-n = **steeper straight line**; (ii) low-n = **gentler straight line**; (iii) no-trap Debye limit = **curved line, not straight**. The distinction is shape (straight vs curved) AND slope, not slope alone.
6. ISPD trap depth distribution g(E_t) has **two lobes** — shallow + deep — not a single peak.
7. The three independent measurements (n exponent, g(E_t), τ_d) **converge on the same trap depth distribution** — multi-modal convergence is the central message of panel (f).
8. The chemical origin of trap formation (panel d) and the physical structural origin (panel e) both point to **the same sulfur-rich regions** along the linear chain — chemistry and physics are consistent, not separate stories.
9. In any panel showing an energy axis: **conduction band (CB) is above valence band (VB)**; trap level sits in mid-gap region between them.

---

When this briefing is filled, author `examples/fig3_trap_schematic_v97/fig3_trap_schematic_v97.tex` directly (cp `styles/tex_template.tex` to start) and run `/fig_compile fig3_trap_schematic_v97`.
