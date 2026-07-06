# External Questions: fig1_overview_v2_pair_001_vault briefing

Source: `/Users/choemun-yeong/workspace/ResearchOS/[figure-agent]/plugins/figure-agent/examples/fig1_overview_v2_pair_001_vault/briefing.md`
Generated: 2026-05-16T13:02:06+09:00
Inferred adjacent domains: Polymer chemistry, Solid-state / trap physics, Surface science / ISPD method, Electromechanical / cantilever, Kinetics / statistical mechanics
(Override domains specified by user: no)
Total questions: 25 (HIGH: 11, MED: 9, LOW: 5)

> **Note**: This file contains questions only. The agent did NOT answer
> them. Answering is the user's responsibility (consult domain experts
> where needed). Pattern adapted from MARG (arXiv:2401.04259) — the
> questions briefing cannot answer reveal the most valuable gaps.

---

## Domain: Polymer chemistry

### HIGH priority

1. [§6 "재료 identity — poly(S-r-DIB) primary microstructure"]
   1,3-DIB와 S 사이 stoichiometry (mol S : mol DIB) 또는 weight ratio가 briefing 어디에도 명시되지 않음 — Panel A의 4 DIB rings + 3 polysulfide segments는 fixed mole ratio를 의미하는가, 또는 illustrative cartoon만인가? Panel B의 S_n labels (n=60..85)는 1 mol DIB 당 평균 S atom 수의 분포 sampling인가, 또는 다른 정의?

### MEDIUM priority

2. [§13.1 A-2, "linear DIB-polysulfide-DIB links between meta-position vertices"]
   실제 inverse vulcanization으로 합성된 poly(S-r-DIB)는 합성 조건 (S:DIB 비, 반응 온도, 시간)에 따라 broad chain length 분포 + 일부 crosslinking을 보이는 random copolymer로 알려져 있다 — briefing의 "linear, NOT crosslinked" LOCKED는 어느 합성 conditions (paper의 실제 sample)에 정확히 정렬되는가?

3. [§13.1 A-4, "quaternary C(CH₃)₂ junctions...gem-dimethyl from isopropenyl→isopropyl"]
   gem-dimethyl quaternary C가 6 internal DIB-polysulfide sites 모두에 동일 형태로 그려짐 — 실제 합성에서 stereoisomer / diastereomer / partial conversion (잔여 isopropenyl unreacted) 가능성이 briefing에 다뤄지지 않음. 이 단순화가 chemistry-savvy reader에게 어떤 의문을 일으키는가?

### LOW priority

4. [§13.1 A-5, "regular octagon polygon S₈"]
   S₈는 실제로 puckered crown-like 3D conformation (D4d symmetry, dihedral ≈98°)을 가지는데 Panel A에서 2D regular octagon으로 표현됨 — 이 2D 단순화가 figure scope에서 의도된 cartoon convention인지, 또는 reader가 conformation을 "flat ring"으로 오해할 위험은 briefing이 평가하지 않음.

5. [§9 "Panel A topology 위반 금지"]
   1,3-DIB (meta) vs 1,4-DIB (para) 위치 isomer 차이가 briefing에 언급되지 않음 — meta substituent grammar 결정은 paper의 실제 monomer 선택을 따른 것인가, 또는 figure convention 결정인가?

---

## Domain: Solid-state / trap physics

### HIGH priority

6. [§8.1 "Deep traps = lower energy (deeper wells); shallow traps = higher energy"]
   Trap을 어느 carrier (electron 또는 hole)에 대한 것으로 가정하는지 briefing이 명시하지 않음 — Panel C의 ⊖ markers가 electron trap (negative charge trapped) 의미라면, hole trap의 별도 representation이나 paper claim의 carrier polarity는 어디서 확인 가능한가?

7. [§13.3 C-R1, "E_C / mobility edge (dashed) / E_V"]
   Mobility edge concept은 amorphous / disordered semiconductor의 convention (Mott-CFO model) — poly(S-r-DIB)이 어느 disorder regime (fully amorphous, semi-crystalline, dual-phase)인지 briefing이 명시하지 않음. Mobility edge depth (E_C - E_mobility-edge)의 정량 값은 figure scope 밖인가?

### MEDIUM priority

8. [§13.3 C-R3, "deep trap levels (2 horizontal lines)...broader distribution 암시"]
   2 lines가 discrete 2-level 또는 continuous distribution의 sub-sampling 둘 다로 읽힐 수 있음 — 실제 trap DOS의 functional form (single level, Gaussian, exponential band tail, Urbach)이 paper에서 어느 model에 정렬되어 있는지 briefing에 없음.

9. [§13.3 C-R4, "escape arrow from deep band → mobility edge (Boltzmann thermal release)"]
   Thermal release만 시각화됨 — tunneling (특히 deep trap에서 중요), hopping, field-assisted (Poole-Frenkel) escape 메커니즘은 figure scope 밖인가? 만약 그렇다면 그 가정이 paper text에 명시되어 있는가?

### LOW priority

10. [§8.2 "shallow = blue, deep = red"]
    적록 색맹 (deuteranopia, 인구 6-8%) reader는 cBlue (shallow) vs cRed (deep) 식별이 어려울 수 있음 — color blindness accessibility를 briefing이 고려한 기록이 없음. Color-only가 아닌 shape/size encoding도 함께 쓰는 redundancy 의도는?

---

## Domain: Surface science / ISPD method

### HIGH priority

11. [§13.6 E-2, "β≈0.8, V_0=3.20, V_r=0.55, τ≈0.6"]
    β=0.8이 representative value인지 specific sample value인지 briefing이 구분하지 않음 — ISPD measurement에서 β fitting의 sample-to-sample variation, confidence interval, fitting protocol (least-squares, log-residual)이 paper의 어느 section에 있는가?

12. [§4 "ISPD"]
    ISPD = Iso-thermal Surface Potential Decay 약어가 briefing 본문에서 expanded되지 않음 — figure caption / paper introduction에서 first-use expansion이 어디에서 보장되는가? Outsider reader가 figure 단독으로 "ISPD"를 해석할 수 있는가?

### MEDIUM priority

13. [§13.7 F-3, "deep Gaussian 1.86× shallow height"]
    g(E_t)는 ISPD V_s(t)의 inverse Laplace transform-like derivation으로 추정됨 — 실제 inversion algorithm (Tikhonov regularization, CONTIN, regularized derivative, model fitting)이 briefing 어디에도 없음. Numerical method가 figure scope 밖이면 paper 어느 section?

### LOW priority

14. [§13.6 E-1, "linear t-axis (was log t)"]
    ISPD 분야의 typical convention이 log t인 경우 (multi-decade timescale 포착)와 linear t (single-decade detail) 어느 쪽인지 briefing이 명시하지 않음. Linear t 선택이 cartoon register 의도임은 §13.6 v6.1 comment에 있지만 ISPD-trained reader에게 자명한가?

---

## Domain: Electromechanical / cantilever

### HIGH priority

15. [§13.8 G-3, "polymer cantilever bending LEFT...Coulomb REPULSION (같은 부호 척력)"]
    거시적 bending이 q_tr ⊖ markers와 grounded electrode 사이 Coulomb force로만 표현됨 — bending force와 trap charge q_tr 사이 정량 관계 (Maxwell stress tensor 적분, Lippmann equation, point-charge approximation)는 figure scope 안인가 밖인가? Briefing이 illustrative 의도라 했지만 paper text에서 force equation은 어디?

16. [§8.5 "Maxwell attraction arrow forbidden (design.md v2.2 §2.3)"]
    Maxwell attraction (trapped charge가 grounded electrode에 induce하는 image charge로부터 받는 attractive force) 이 explicitly 금지됨 — 실제로 grounded conductor 옆 charge는 image charge attraction을 반드시 받음. 왜 figure에서 attraction을 제외하는가? Net force가 repulsion-dominant인 specific regime의 가정?

### MEDIUM priority

17. [§13.8 G-7, "air gap 0.575→1.425 cm (2.48×, 31° swing buffer)"]
    Briefing의 air gap dimension이 "visual buffer (31° swing buffer)" 목적이라고 §13.8 G-7에 명시됨 — 실제 measurement geometry (real cantilever length, real air gap in mm/μm range)가 paper text 또는 별도 figure (methods / SI)의 어디에 문서화되어 있는가?

### LOW priority

18. [§13.8 G-2, "(grounded) label"]
    Grounded electrode의 ground reference (chamber wall, separate ground plate, sample stage, virtual ground)가 briefing에 unspecified — measurement setup의 ground topology가 figure에 의미 있는가?

---

## Domain: Kinetics / statistical mechanics

### HIGH priority

19. [§8.4 "Power-law I(t) ~ t⁻ⁿ lies above Debye reference at long times. Cannot be below."]
    "Cannot be below" LOCKED rule이 어느 physical 제약 (trap detrapping > radiative decay, microscopic reversibility constraint)에 기반하는지 briefing이 명시하지 않음. 일부 trap material에서 short-t에서 power-law가 Debye 위에 있다가 long-t에서 cross-over 하기도 함 — briefing의 figure 가정 regime은?

20. [§13.5 D-2, "deep less-steep slope...smaller n = retention 길다"]
    n value와 trap depth ΔE_t의 quantitative mapping은 어느 model (Tachiya-Hama, Albery-Bartlett, dispersive transport Scher-Montroll)을 따르는가? Sample identity ("deep-rich" vs "shallow-rich")가 합성 변수 (S:DIB ratio, MW)와 어떻게 1:1 정렬되는지 briefing에 없음.

### MEDIUM priority

21. [§13.7 F-4, "τ_d abstract trap time-constant"]
    τ_d arrow의 visual length가 reader's perceived ratio (shallow vs deep release rate) 인지에 영향 줄 수 있음 — briefing의 "abstract" assertion 외에 실제 τ_d magnitude (orders of magnitude difference: 10×, 100×, 10^3×)는 paper 어디에서 정량화되어 있는가?

---

## Meta-questions (cross-domain)

### HIGH priority

22. [§1 "deep charge trap이 존재하고...같은 trap을 가리키며"]
    "Deep charge trap"이 단수 single trap species로 표현됨 — 실제 poly(S-r-DIB)에는 multiple trap species (radical defect, end-group, chemical impurity, conformational trap)가 동시에 존재 가능. Briefing은 "the same trap" 의도적 단일화인지, paper의 실험적 결론 (e.g., dominant trap species가 단일임을 ISPD bimodal로 입증)인지 구분이 없음.

23. [§5 "3 modalities (kinetic / ISPD / mechanical) 평등 분포"]
    "Convergent evidence" claim의 quantitative 일치도 (n value ↔ deep peak fraction ↔ Δx magnitude) 가 어떻게 consistent임을 paper text가 보장하는지 briefing에 없음 — 3 modalities가 같은 trap을 가리킨다는 결론에 대한 cross-check table 또는 unified parameter fit이 paper 어느 section에 있는가?

### MEDIUM priority

24. [§2 "Total ~14s for full read. Panel C dwell = single longest stop"]
    14s eye-flow 가정이 cover figure (잠재 reader의 longer dwell) 대상인지 paper body figure (skim-mode shorter dwell) 대상인지 briefing이 명시하지 않음 — 두 case에서 dwell budget이 다르다면 briefing은 어느 case에 정렬되어 있는가?

25. [§7 "ALIGNED (post-v7)"; §10 "#3 Inter-panel gap deviation [ACTIVE]"]
    Briefing이 self-described "ALIGNED" 상태이지만 §10에 #3 polish residual (inter-panel gap deviation, branching arrow의 intended cost)이 ACTIVE로 남아있음 — 이 deviation이 journal submission gate 또는 referee 단계에서 issue로 fly할지 briefing이 평가하지 않음. Cover-feel goal change 없이 #3가 closed될 path는?

---

## Self-verification log

- Principle check: 25/25 questions describe gaps in briefing, none assert facts about reality.
- Answer-pattern scan ("because"/"due to"/"therefore"/"likely"/etc.): 0 violations after manual rewrites.
- Citation completeness: 25/25 cite specific §/sub-region/quoted snippet.
- Domain coverage matches header (5 inferred + Meta).
- Priority count: HIGH 11 / MED 9 / LOW 5 = 25 total ✓
- No answers attempted, no other agent invoked.
