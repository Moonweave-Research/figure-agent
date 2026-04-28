# Briefing — fig3_trapping_concept

> **Dogfooding note**: original `_reference_original/fig3_trapping_concept.tex` is in this
> folder as historical context. The dogfooding goal is to regenerate this figure through
> figure-agent (briefing → normalized prompt → external image gen → human/LLM-authored TikZ compile)
> and compare the final vector output against the original. Filling this briefing in your own words (rather
> than copying from the original) is the honest path; otherwise the workflow is just a re-render.

## 1. What does this figure show? (1-2 sentences)

황고분자에서 발생하는 charge trapping 현상의 개념을 독자가 이해하기 좋게 설명하는
4-panel concept figure. 트랩핑 지수가 무엇인지, 어떤 역할인지, 트랩핑 능력이 좋은
조성과 나쁜 조성의 물리적·함수적 차이, 측정 방식까지 한 figure로 보여준다.

**Narrative position**: Fig 2 (mechanism) 패널의 "Capacitive vs Power-law" 시각적 hook을
이어받아, 본 figure에서 **실측 데이터로 확정**하는 역할.

## 2. Domain vocabulary (terms, materials, mechanisms)

- 황고분자 composition sweep: S60, S65, S70, S75, S80, S85
- Charge dynamics: charge trapping, retention, discharge
- Power-law decay: I(t) ∝ t^(-n), trapping index n, raw signal vs RLM MM 통일
- Composition tunability: non-monotonic peak (S70-S75)
- Trap DOS: ISPD (Isothermal Surface Potential Decay), g(E_t), shallow trap, deep trap, 2-peak structure
- Time scale: τ_d discharge time, trap depth로부터의 직접 정량값
- 측정 방식: ISPD 기반 표면전위 감쇠 측정

## 3. Composition intent (panel layout, flow direction)

4-panel storyline (논리 흐름은 left-to-right):

- **(a)** I(t) ∝ t^(-n) per composition: power-law decay 시그니처. raw 측정 + RLM MM 통일 본.
- **(b)** n vs composition: S60-S85 sweep을 한 axis에 두고, **non-monotonic peak가 S70-S75**에서
  나타남 → composition tunability의 1차 증거.
- **(c)** ISPD g(E_t) trap DOS: shallow + deep 2-peak 구조. composition별 대표 곡선 overlay.
- **(d)** τ_d discharge time: trap depth가 retention 시간에 직접 어떻게 매핑되는지 정량 비교.

## 4. Normalize / avoid literal overfit

- 정확한 수치값 (n, τ_d, peak 위치 등) → normalization이 과도한 literal anchoring을 완화
- 셋업 디테일 (ISPD 측정 방식, corona 전압, 시료 두께 등): **노출 OK**
- 핵심 claim 포인트 (composition tunability, non-monotonic peak at S70-S75 등): **노출 OK**
- 도메인 약어 (S60-S85, ISPD, RLM MM, g(E_t), τ_d): **노출 OK**

요약: 수치만 빼면 되고, 셋업·핵심 주장·도메인 vocabulary는 모두 prompt에 포함 가능.

## 5. Style notes (optional)

skip — Nature-tone 4-panel data figure default 적용 (white background, sans-serif,
balanced layout, no extra style override).

---

When this briefing is filled, run `/fig_prompt fig3_trapping_concept` to generate the normalized prompt for external image generation.
