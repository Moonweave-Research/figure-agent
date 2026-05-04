# Briefing — fig3_trapping_concept (RESET — schematic intent)

> **Reset note (2026-04-28)**: 첫 시도는 4-panel data figure로 어긋남
> (figure-agent scope 밖). figure-agent는 schematic 전용. 사용자 4-panel
> storyline은 figure-agent v0.1 범위 밖이며, data plot이 필요하면
> Graph_making_hub 영역에서 별도로 다룸.

## 1. What does this figure show? (1-2 sentences)

황고분자 charge trapping의 메커니즘과 fundamental 개념을 독자가 이해하기 좋게
설명하는 schematic. 본 연구의 차별점은 **trap-based retention 메커니즘**이
일반 dielectric의 polarization-based 응답과 본질적으로 다르다는 점.

## 2. Domain vocabulary (terms, materials, mechanisms)

- Band structure: conduction band (CB), valence band (VB), bandgap, LUMO, HOMO
- Trap physics: shallow trap, deep trap, trap level (E_t), trapped electrons,
  injection, capture, thermal escape, kT ≪ E_t
- Mechanism contrast: trap-based retention vs polarization-based response
- Materials: PDMS (low-trap dielectric — polarization 응답이 dominant),
  Sulfur Polymer (deep-trap dielectric — trap이 charge retention의 핵심)
- Charge dynamics: charge injection, retention, recombination

## 3. Composition intent (panel layout, flow direction)

2-panel side-by-side schematic, 두 메커니즘을 직접 대비:

- (a) **PDMS — polarization mechanism**:
  vertical E-axis (좌측), clean bandgap (CB top blue line, VB bottom red line),
  no trap level. Mobile electron 1개 + 빠른 recombination 화살표.
  Optional: dipole/charge displacement 표현 (polarization 응답을 시각화).
  → "fast V(t) loss" 의미.

- (b) **Sulfur Polymer — trap mechanism**:
  vertical E-axis (좌측), CB/VB 동일 위치, **mid-gap에 deep trap level (E_t)**,
  바로 위에 shallow trap level. Deep trap에 trapped electrons (4개 점),
  shallow trap에 trapped electrons (2개 점). Injection 화살표가 CB로 들어와
  deep trap으로 capture (수직 화살표). Weak thermal escape 화살표 + 라벨
  "kT ≪ E_t (escape negligible)".
  → "long retention" 의미.

각 panel 하단에 한 줄 캡션 ("fast V(t) loss" / "long retention"),
panel 사이 화살표/구분 없음 — 두 메커니즘 자체가 대비.

## 4. Normalize / avoid literal overfit

- 정확한 trap depth 수치 (E_t 값)
- corona discharge voltage
- 시료 dimensions (두께, 면적)
- wt% sulfur composition 정확값

(이번 schematic은 정량값을 거의 안 씀. normalization default도 충분.)

## 5. Style notes (optional)

Nature schematic 스타일 — minimal, white/light-gray panel backgrounds,
sans-serif, balanced composition. blue=conduction/electron, red=valence,
amber=deep trap, gray=axis/recombination/escape (원본 sty 매크로 결).

## 6. Physics invariants

- Panel (a): PDMS has clean CB/VB bandgap and no trap level.
- Panel (b): sulfur polymer has deep trap level E_t inside the bandgap, below CB and above VB.
- Injection arrow enters CB before capture.
- Capture direction is CB to deep trap, not the reverse.
- Trapped electrons sit on trap levels, not floating freely in the gap.
- Thermal escape is weak/negligible relative to deep-trap retention.

## 7. Author Intent (vision critique grounding)

### Must depict
- **Panel (a) electrons** — round dots or circles (not zigzag or featureless), ideally 1-2 circled electrons mobile in CB region before fast recombination arrow.
- **Panel (b) trap levels** — two distinct discrete lines (shallow 상단, deep 하단) in the mid-gap region; NOT continuous states. Visually separate from CB/VB band edges.
- **Trapped electron cluster on deep trap** — ≥4 electron dots sitting directly on the deep trap line (or clustered ~0.1cm above it), indicating capture. NOT floating in the gap.
- **Thermal escape arrow on deep trap** — small, weak upward arrow from deep trap toward CB (or labeled "kT ≪ E_t"), indicating *suppressed* escape. If arrow is present, must be ≪ injection arrow in size.
- **Panel contrast** — (a) should be visually simpler (clean bands, fast recombination, fewer components); (b) more complex (two trap levels, cluster of electrons, retention physics). Spatial/visual density difference should be perceptible.

### Must avoid
- **Trap levels as energy curves** — E_t must be a line (discrete level), not Gaussian/smooth distribution.
- **Floating electrons in gap** — all trapped electrons must be clearly anchored to trap levels, not drifting between CB and VB.
- **Equal-sized arrows** — injection and thermal-escape arrows must differ visually (injection dominant, escape tiny/suppressed).
- **Unlabeled trap levels** — shallow/deep distinction must be visually or textually clear (label or relative position).
- **Polarization representation overlapping with charge dynamics** — if (a) includes dipole/polarization, keep it distinct from electron motion (use separate region or color).

### Semantic assertions (for vision critique)
1. "Can you identify which electrons are trapped vs. mobile in panel (b)?" → must be visually distinct (color or position).
2. "The trap levels in panel (b) appear as discrete states, not a continuum." → verify as line features, not gradients.
3. "Thermal escape from deep trap is suppressed (small arrow, labeled kT ≪ E_t)." → if arrow exists, size & label confirm suppression intent.
4. "Panel (a) and (b) are visually contrastable as 'polarization-only' vs 'trap-retention' mechanisms." → composition density, component count should differ.

---

When this briefing is filled, author `examples/fig3_trapping_concept/fig3_trapping_concept.tex` directly (cp `styles/tex_template.tex` to start) and run `/fig_compile fig3_trapping_concept`.
