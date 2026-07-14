# Briefing — fig3_resistance_mechanism

> **Genre**: Nature Communications main-text figure — clean white, schematic. This is the
> **explanatory SCHEMATIC half** of a composite Fig 3; the real transient-current data
> (I(t)∝t⁻ⁿ curves, composition series) come from the data pipeline (Origin / Graph Hub)
> and are composited beside this schematic. figure-agent draws ONLY the schematic.
> **Role (2026-06-22 figure plan)**: Fig 3 = the "trapping during conduction" mechanism —
> the narrative bridge from "the material is a tunable dielectric" (Fig 2: ε_r + P–E) to
> "the traps' energies/lifetimes, quantified" (Fig 4: ISPD decay + trap spectra).
> **Design constraint (user, verbatim)**: 얄쌍하게 오밀조밀하게, 비대하지 않게 — slim, compact,
> dense; explain just enough for human understanding.

## §1. Topic
저항 측정(전류를 흘려 transient current로 charge trapping을 분석)의 메커니즘을 한 그림으로:
셀에 전압을 인가 → 전하 캐리어가 무질서한 황고분자 막을 dispersive하게 통과하며 trap에
반복적으로 잡힘 → 전류가 시간에 따라 감쇠(흡수전류) → 저항 증가. 그리고 이 trap 분포가
황 함량에 따라 **discrete(저황, shallow+deep)에서 continuous broad(S80)로 진화**한다.

## §2. Sub-regions (2 dense blocks)
- **(a) cell + transport + decay**: 전극/sulfur film/전극 + 인가 V; carrier의 tortuous
  representative trapping-state sequence(최종 retained); 작은 I-vs-t 감쇠 sparkline + "current decays ⇒ R↑".
  세로축은 전기장이 아닌 **energy, E**이며, carrier-path의 모든 끝점은 실제 trap/carrier glyph에
  결속해야 한다. 좌→우 배치는 시간 순서만 나타내며 net spatial drift를 뜻하지 않는다.
- **(b) g(E) evolution**: 에너지 가로축의 trap energy distribution. S60 = discrete
  localized trap state set → S80 = continuous broad(넓음). `distribution breadth`(가로 범위)를
  보이며, `ρ60s`는 이 explanatory schematic이 아니라 companion transient-current data plot에서
  보고한다. S60과 S80은 겹친 성분처럼 그리지 말고 좌→우 비교 단위로 분리한다.

## §3. Physics invariants (grounded in 02_Surfur_Polymer docs; DO NOT violate)
1. Measurement = transient current I(t) under applied V, **Curie–von Schweidler power-law
   I(t) ∝ t⁻ⁿ** (n∈(0,2)); I=V/R so I↓ ⇒ R↑. t>~2s = pure trap-mediated absorption current.
2. **n is the fitted CvS power-law exponent.** Distribution breadth is the schematic
   mechanism cue; `ρ60s` belongs to the companion data plot. A direct width-to-`n`
   mapping is model/calibration dependent; do not assert it from geometry alone.
3. **Carrier is sign-agnostic** — dispersive trap-controlled transport in a disordered solid
   (Scher–Montroll for n>1, Jonscher for n≤1). Do NOT commit to electron vs hole; do NOT draw
   a clean band/ballistic-drift picture (no net +→− carrier drift).
4. Traps are a **broad continuous distribution** at high sulfur; **discrete shallow/deep at
   low sulfur**. The discrete→continuous evolution with sulfur IS the mechanism (CvS_Analysis_
   Strategy.md). Do NOT draw 2 fixed discrete levels for all compositions.
5. **Do NOT encode "stronger trapping" as well DEPTH** (depth reads as magnitude, contradicts
   width-to-n mapping). With no declared transport-energy reference in panel B, do not label a
   peak "deep". Use distribution breadth + ρ60s as distinct schematic cues.
6. "S–S radical / sulfur cluster" trap chemistry is **NOT established** — illustrative only,
   never asserted. Unlabeled × marks for trap sites are correct.
7. Use 'trap-energy distribution / landscape', NOT 'trap network' (network asserts spatial
   percolation, a stronger/different claim).

## §4. Provenance
Physics from `~/Google Drive/My Drive/Research/02_Surfur_Polymer/` (저항 측정/docs/protocol_full.md;
docs/si_methods_S0_theoretical_framework.md; Charge trapping 측정/docs/methodology/CvS_Analysis_Strategy.md;
docs/manuscript/framing.md). Schematic hand-authored iter0→iter3 (2026-06-22) after a 5-lens QA
(reader / NC-editor / physics-skeptic / alternative-methods / visual-design → refine, not pivot).
