# TikZ Authoring Prompt — fig3_trap_schematic_v97

## 1. Role

You are an expert TikZ author for materials-science schematics. Your task is to
produce a single compilable `.tex` file body that implements the figure described
below. Follow every constraint exactly; do not explain or comment on your choices.

## 2. Hard Constraints

- Preserve §6 Physics Invariants verbatim as logical constraints. Do not
  contradict, weaken, or reorder them.
- Use only palette colors: cAmber, cAmberSphere, cArmAmber, cBlue, cBrown, cGray, cLGray, cRed, cTeal. No `\definecolor`, no font
  overrides, no raw hex (`#RRGGBB`), no non-palette color names (red, blue,
  green, etc.).
- Required scaffolding contract — see §3 for the exact open/close sequences.
  The output must be a complete standalone `.tex` (compile.sh runs `lualatex`
  on the file directly; nothing is wrapped around it).

## 3. Required Scaffolding

Every output must start with:

```latex
\documentclass{standalone}
\usepackage{polymer-paper-preamble}
\begin{document}
\begin{tikzpicture}
```

and end with:

```latex
\end{tikzpicture}
\end{document}
```

## 4. Flagship Macro Guidance

Prefer these macros over raw TikZ primitives for blocks, charges, gradients, and
cone tips. Use them wherever the schematic calls for corresponding elements.

- `\IsoBlock{w}{d}{h}{color}{hook}` — isometric block (W x D x H) at origin; #5 is TikZ code executed inside the iso group.
- `\IsoCharge{x,y,sign}` — half-buried hemisphere charge dot (★★★ v0.2 promotion)
- `\GradSlab{x,y,w,h,c1,c2,axis}` — rectangular slab with x/y color gradient.
- `\IsoConeTip{x,y,direction}` — triangular tip emphasis face.

## 5. Briefing Context

### §1 — What does this figure show?

Sulfur polymer trap-mediated charge dynamics의 측정→해석→화학적·물리적 원인을 multi-panel schematic으로 통합 — 독자에게 Fig 3 정량 데이터(I(t), n, g(E_t), τ_d)의 conceptual scaffold을 제공해, "왜 sulfur polymer에서 trap이 풍부하고 그것이 어떻게 측정·해석되는지"를 한 figure에서 이해하도록 한다.

### §3 — Composition intent

6-panel schematic, 측정→해석→원인 순 narrative. 좌→우 + 위→아래 흐름.

- **(a) 측정 셋업** — experimental setup schematic (2D side-view): polymer film between electrodes, voltage bias, current meter, time-axis. 측정이 "어떻게" 이루어지는지 직관적으로.
- **(b) 멱함수의 이해** — qualitative I(t) ∝ t^(-n) cartoon vs Debye exp(-t/τ) 대비. log-log axis cartoon (axis tick 없음, 두 곡선 모양만 비교). "왜 power-law가 trap의 시그니처인가" 개념 설명.
- **(c) Trapping index n 해석** — 3-up cartoon comparison: high n (trap-rich, deep) / low n (few/shallow) / no trap (pure Debye). 같은 axis 위에 3개 곡선 모양만 qualitative하게 overlay.
- **(d) 화학적 원인** — sulfur-rich segment, S-S bond, electron affinity 도식. molecular-level view (sulfur 원자 + 인접 결합 + 전자 trapping site 표시).
- **(e) 물리적 원인** — **linear polymer chain** (cross-link 없음) + sulfur-rich segment 분포, trap site density. micro-structure isometric or side view, 사슬 형태 강조 (network/cross-link 그려지지 않음). sulfur cluster 영역에 trap marker 분포.
- **(f) Multi-modal convergence** — n exponent / g(E_t) / τ_d 세 metric의 qualitative shape이 한 화살표 또는 venn-overlap으로 "consistent trap depth distribution" 라벨을 향함. axis tick / 수치 없음, 모양 hint만. Fig 3 데이터의 핵심 논거 ("3 independent metrics converge")를 conceptual hook으로 미리 깔아준다.




각 panel 하단에 한 줄 sub-caption. Panel 사이 명시적 화살표는 일반적으로 없음 (narrative는 layout 흐름이 자명).

### §5 — Style notes

Nature schematic 스타일 — 양식을 절대 벗어나지 않음.
- **Layout**: 3×2 grid 우선 (행 1: a-b-c, 행 2: d-e-f). 시각적 균형이 안 맞으면 2×3 또는 다른 적절한 layout으로 fallback.
- **Width**: Nature double-column (~183mm) 권장 — 6 panel을 한 figure에 응집.
- **Background**: white / 패널마다 light-gray rounded rectangle (cLGray!22) 패턴 (`fig3_trapping_concept` 참고).
- **Palette** (polymer-paper-preamble): cBlue=conduction/electron, cRed=valence, cAmber=trap, cGray=axes/labels, cTeal=accent.
- **Font**: sans-serif (Arial via fontspec), Nature scale.
- **Headers**: panel 좌상단 (a)-(f) bold + 한 줄 gray sub-title (예: "(a) measurement setup", "(b) power-law signature" 등).
- **Sub-captions**: 각 panel 하단 한 줄, bold.
- **Axes**: 정량 tick 없음 — qualitative shape만.

### §6 — Physics invariants (hard constraints)

1. Polymer is a **linear chain** — no cross-links, no network nodes, no branches connecting separate chains. Sulfur clusters appear as side groups along the chain only.
2. Trap level lies **inside the bandgap** (between CB and VB), drawn as a **short localized line segment** — not a full-width line.
3. **Trapped electrons sit ON the trap level itself** — not floating freely in the bandgap.
4. When the time-current axes are plotted on **double-logarithmic (log-log) scale**: (i) power-law I(t) ∝ t⁻ⁿ appears as a **straight diagonal line** (slope = −n); (ii) Debye exp(−t/τ) appears as a **curved line that bends downward more steeply at later time** (concave-down). This visual contrast IS the trap signature.
5. Panel (c) shows three qualitative curves on the same log-log axes: (i) high-n = **steeper straight line**; (ii) low-n = **gentler straight line**; (iii) no-trap Debye limit = **curved line, not straight**. The distinction is shape (straight vs curved) AND slope, not slope alone.
6. ISPD trap depth distribution g(E_t) has **two lobes** — shallow + deep — not a single peak.
7. The three independent measurements (n exponent, g(E_t), τ_d) **converge on the same trap depth distribution** — multi-modal convergence is the central message of panel (f).
8. The chemical origin of trap formation (panel d) and the physical structural origin (panel e) both point to **the same sulfur-rich regions** along the linear chain — chemistry and physics are consistent, not separate stories.
9. In any panel showing an energy axis: **conduction band (CB) is above valence band (VB)**; trap level sits in mid-gap region between them.

## 6. Spec Context

### Panels

- (a) 측정 셋업
- (b) 멱함수 (power-law) 의 이해
- (c) Trapping index n 해석
- (d) 화학적 원인
- (e) 물리적 원인
- (f) Multi-modal convergence (n / g(E_t) / τ_d → consistent trap depth)

### Selected preview

codex_v01.png

### Selection notes (preview-grounded authoring guide)

The notes below refine §3 composition intent with preview-specific element
placement, palette use, and corrections. Priority order: §6 invariants >
§3 composition intent > selection notes. When selection notes conflict
with §6, honor §6 and ignore the conflicting note. Selection notes may
add visual detail consistent with §6 but cannot introduce new invariants.

Codex app (codex_v01) chosen as primary baseline (2026-04-28 2-candidate
compare with chatgpt_web_v01). Codex was preferred for 2D line-art
consistency that carries invariant #8 visually — panels (d) and (e)
share the same visual motif — and for a palette closer to Nature
schematic convention.

Visual motifs to preserve:
  - green wavy polymer backbone shared between panels (d) and (e)
  - yellow S-circle marking sulfur sites along the chain
  - amber trap halo on sulfur cluster regions
  - shared sulfur-halo motif across (d)+(e) so invariant #8 (chem ↔ phys point to same sulfur regions) reads visually

Preview errors to fix in TikZ:
  - panel (c) no-trap Debye curve is drawn nearly straight in both previews — must be concave-down to honor invariant #5
  - both previews under-visualize invariant #8 — TikZ must add an explicit shared sulfur-halo marker across (d)+(e)

Labels to lift (from chatgpt_web_v01, kept as enrichment reference):
  - (a) explicit "voltage-bias" / "current-meter" labels
  - (b) "trap-controlled hopping" inset cartoon labeling
  - (c) "trap-rich" / "shallow or fewer traps" verbal labels
  - (f) numbered-metric panel labeling

Style overrides:
  - polymer-paper-preamble.sty Style Lock wins: Paul Tol Muted palette + Arial override both previews' palettes during .tex authoring

## 7. Output Contract

- Output a single `.tex` file body. No prose, no markdown fences, no commentary.
- The file must compile with `lualatex` against `polymer-paper-preamble.sty`
  without errors.
- Every color reference must be from the palette list in §2.
- Every element that corresponds to a flagship macro must use that macro.

