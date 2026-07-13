# Bound authoring execution: fig3_resistance_mechanism

## Output and attempt boundary
- Before resolving the output path, change directory from the repository root to [plugins/figure-agent].
- Write exactly one new source to [examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v5/treatment_generated.tex].
- Do not create an intermediate subdirectory beneath [examples/fig3_resistance_mechanism/review/failure-first/execution-binding-v5].
- Start from the declared blank artifact; perform one attempt only.
- Do not inspect or repair historical generated sources.
- Read repository file content only from [AGENTS.md] and [styles/polymer-paper-preamble.sty]; all other required authoring context is already bound below.

## Mandatory standalone TikZ source requirements
- \documentclass[tikz,border=4pt]{standalone}
- \usepackage{tikz}
- \usepackage{polymer-paper-preamble}

## Style Lock authoring requirements
- Use only the preamble palette tokens cAmber, cBlue, cRed, cTeal, cGray, cLGray, cBrown, cArmAmber, and cAmberSphere, plus TikZ built-in black, white, and gray.
- Keep every explicit line width at or above 0.25pt.
- Do not use local \tiny or \scriptsize font overrides.

## Semantic contracts and forbidden implications
- Required panels:
  - [A] Cell under applied V — charge carrier (sign-agnostic) undergoes dispersive, repeated trapping; transient current decays (I ∝ t^-n) so resistance rises
  - [B] Trap energy distribution g(E) — discrete (S60, single deep) evolving to continuous broad (S80); n = breadth of the distribution, ρ60s = magnitude
- Binding fixture briefing (verbatim):

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
  multiple-trapping walk(최종 caught); 작은 I-vs-t 감쇠 sparkline + "current decays ⇒ R↑".
- **(b) g(E) evolution**: 에너지 가로축의 trap energy distribution. S60 = discrete 단일 deep
  peak(좁음) → S80 = continuous broad(넓음). `n = breadth`(가로 화살표), `ρ60s = magnitude`
  (세로, 별도). "disorder↑(sulfur↑): discrete → continuous broad" 화살표.

## §3. Binding physics-correctness rules (grounded in 02_Surfur_Polymer docs; DO NOT violate)
1. Measurement = transient current I(t) under applied V, **Curie–von Schweidler power-law
   I(t) ∝ t⁻ⁿ** (n∈(0,2)); I=V/R so I↓ ⇒ R↑. t>~2s = pure trap-mediated absorption current.
2. **n = the BREADTH of the trap energy distribution, NOT trap density.** Magnitude is a
   separate metric ρ60s. (n=density would be WRONG.)
3. **Carrier is sign-agnostic** — dispersive trap-controlled transport in a disordered solid
   (Scher–Montroll for n>1, Jonscher for n≤1). Do NOT commit to electron vs hole; do NOT draw
   a clean band/ballistic-drift picture (no net +→− carrier drift).
4. Traps are a **broad continuous distribution** at high sulfur; **discrete shallow/deep at
   low sulfur**. The discrete→continuous evolution with sulfur IS the mechanism (CvS_Analysis_
   Strategy.md). Do NOT draw 2 fixed discrete levels for all compositions.
5. **Do NOT encode "stronger trapping" as well DEPTH** (depth reads as magnitude, contradicts
   n=breadth). Use breadth + ρ60s only.
6. "S–S radical / sulfur cluster" trap chemistry is **NOT established** — illustrative only,
   never asserted. Unlabeled × marks for trap sites are correct.
7. Use 'trap-energy distribution / landscape', NOT 'trap network' (network asserts spatial
   percolation, a stronger/different claim).

## §4. Provenance
Physics from `~/Google Drive/My Drive/Research/02_Surfur_Polymer/` (저항 측정/docs/protocol_full.md;
docs/si_methods_S0_theoretical_framework.md; Charge trapping 측정/docs/methodology/CvS_Analysis_Strategy.md;
docs/manuscript/framing.md). Schematic hand-authored iter0→iter3 (2026-06-22) after a 5-lens QA
(reader / NC-editor / physics-skeptic / alternative-methods / visual-design → refine, not pivot).

- No fixture semantic contracts are enabled.
- Do not imply physics or quantitative relations absent from the declared contracts.

## Declared layout directives
- Keep text group [applied, trapping, during, conduction] at least 0.015 page-diagonal units clear of text group [V].

## Optional shape-profile directives
- Render [s80] visibly wider in energy than [s60].
- Use one shared outline, fill, and stroke encoding family for [s60, s80].
- Use composition header [increasing sulfur content] without a curve-to-curve causal arrow.
- Do not assert unresolved claims [fixed_peak_count, monotonic_disorder, decay_direction].

## Provenance and publication boundary
- Declared model: gpt-5.5
- feedback_rounds: 0
- manual_repairs: 0
- filesystem_read_isolation: unavailable
- publication_acceptance: not_claimed
