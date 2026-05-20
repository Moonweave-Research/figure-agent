# Fig 1 Caption — fig1_overview_v2_pair_001_vault

> Companion text for the figure file `fig1_overview_v2_pair_001_vault.pdf`.
> v8.6 6-panel structure (A..F) + 2026-05-20 CvS absorption-current framework rewrite reflected.
> Drafted 2026-05-20.

---

## Short caption (≤30 words — table of contents / abstract-figure use)

**Convergent evidence for deep charge trapping in inverse-vulcanized poly(S-r-DIB).** Three independent probes — Curie–von Schweidler kinetics, isothermal surface-potential decay (ISPD), and Coulomb-driven cantilever bending — converge on a bimodal, deep-dominant trap landscape that distinguishes the sulfur polymer from conventional dielectric controls.

---

## Full caption (~250 words — journal body)

**Figure 1 | Convergent evidence that sulfur-rich poly(S-r-DIB) hosts a deep-trap-dominant charge-trapping landscape and that this landscape drives macroscopic actuation.**

**a**, Identity of the parent material: linear poly(S-r-DIB) random copolymer formed by inverse vulcanization of elemental sulfur (S₈ ring, inset) with 1,3-diisopropenylbenzene (DIB); polysulfide segments are joined by DIB rings into a non-crosslinked linear chain.

**b**, Three representative copolymer compositions across the paper's S60–S85 wt% range (S60 / S75 / S85), illustrating the variable polysulfide-to-DIB ratio.

**c**, Conceptual model of the trap landscape (hero panel). *Left:* real-space cross-section of a poly(S-r-DIB) thin film with shallow (blue) and deep (red) charge-trap sites distributed throughout the matrix. *Right:* corresponding bimodal density of trap states *g*(*E*_t) on the energy axis between the vacuum level, mobility edge, valence band *E*_V and conduction band *E*_C; the deep-trap level lies Δ*E*_t below the mobility edge. Color-matched leaders link real-space sites to their energy-axis counterparts.

**d–f**, Three independent measurement modalities convergently probe the same trap landscape.

**d**, *Kinetic.* Absorption transient *I*(*t*) under a constant DC bias applied across a metal–insulator–metal (MIM) stack (source-measure unit, SMU). On a log-log plot of current against time, the sulfur polymer exhibits a steep Curie–von Schweidler power law *I*(*t*) ∝ *t*⁻ⁿ with a **high** *n* (red, paper hero), reflecting continued trap filling that suppresses the current well beyond the initial dielectric polarization. A conventional dielectric control (e.g., polyimide) yields a **low** *n* (blue), indicating negligible trap accumulation. Both responses lie above the single-relaxation Debye exponential (dashed) at long times — the universal non-Debye signature of trap-controlled dielectric response.

**e**, *Spectroscopic.* Iso-thermal surface-potential decay (ISPD) on the same sulfur polymer: a corona discharge (HV⁺) deposits surface charge onto the polymer-on-grounded-substrate stack, and a non-contact vibrating Kelvin probe reads the slow *V*_s(*t*) decay (top sub-panel). Inversion of the stretched-exponential decay yields the bimodal trap energy distribution *g*(*E*_t) (bottom sub-panel), in which the deep Gaussian peak is approximately 1.86× the shallow peak height (separation τ_d).

**f**, *Mechanical.* A poly(S-r-DIB) cantilever clamped opposite a biased planar electrode (*V*_active) accumulates trapped charges *q*_tr on its surface. The resulting Coulomb repulsion (bold red arrow) drives the cantilever away from the electrode, dominating over the baseline Maxwell-stress attraction *F*_Maxwell (gray dashed arrow toward the electrode). Encoding by hue — red for the active Coulomb result, gray for the passive Maxwell baseline — ensures the hierarchy survives red-deficient vision and grayscale print. The macroscopic deflection is the direct mechanical manifestation of the same trap landscape probed in **d** and **e**.

Quantitative analysis of the *n* exponent across the full S60–S85 composition series, the bimodal *g*(*E*_t) shape parameters and τ_d, and the time-resolved deflection Δ*x*(*t*)/τ_relax appears in Figs. 3 and 5.

---

## Annotation notes (for journal house-style)

- **ISPD** first-use expanded in caption: "isothermal surface-potential decay (ISPD)".
- **CvS** not abbreviated in caption (full name "Curie–von Schweidler" used twice).
- **DIB** acronym paired with full chemical name "1,3-diisopropenylbenzene" at first use.
- **MIM** first-use expanded: "metal–insulator–metal (MIM) stack".
- **SMU** first-use expanded: "source-measure unit (SMU)".
- "Bimodal trap distribution" wording consistent with paper claim (briefing §1 Q22 LOCKED — "same trap" refers to the bimodal landscape, not a single species).
- "high *n*" / "low *n*" naming (no "deep-rich/shallow-rich" — deprecated 2026-05-20). Math *n* in italic per Nature math convention.
- Color binding §13.9 Binding-1: blue = shallow, red = deep. Used consistently across panels c (real-space + energy diagram), e (Gaussians), f (q_tr markers).

---

## Cross-reference (paper text linkage)

- Mechanism framework / floating-clip Coulomb protocol → Methods §M.x.
- Quantitative *n* exponent values across S60–S85 + control polymers (PI / PDMS / PET) → **Fig 3**.
- Quantitative shallow/deep Gaussian fits + τ_d → **Fig 3**.
- Quantitative Δ*x*(*t*) / τ_relax extraction → **Fig 5**.
- CvS theory framework (Curie 1889 / von Schweidler 1907 / Jonscher 1977) → Introduction + Methods references.
- ISPD method foundations (Li *et al.* 2015, Han *et al.* 2018, Conrad *et al.* 2016 cross-section idiom) → Methods + Discussion.
- Sulfur polymer mechanism contrast with electret / triboelectric / dielectric-elastomer prior art → Discussion §D.x.

---

## Caption ↔ figure consistency audit (2026-05-20)

| Caption claim | Figure element | Verified |
|---|---|---|
| "S60 / S75 / S85" Panel **b** | spec.yaml §13.4 B-2 sample names | ✅ |
| "high *n* (red) / low *n* (blue)" Panel **d** | .tex D-7b sloped labels + cRed!80 / cBlue!55 | ✅ |
| "above the single-relaxation Debye reference at long times" Panel **d** | Debye bezier ends at y=0.45, RED/BLUE end at y=0.55 / y=1.50 — Debye below both | ✅ |
| "deep peak ~1.86× shallow" Panel **e** | briefing §5 Q4 + §13.6 E-8 | ✅ |
| "Coulomb dominates over F_Maxwell" Panel **f** | .tex F-7 cRed!80 0.7pt bold vs F-3 cGray!55 dashed 0.45pt gray (C004 accessibility patch) | ✅ |
| "sulfur polymer" hero attribution **e/f** | briefing §13.6 + §13.7 attribution lines (added 2026-05-20) | ✅ |
| ΔE_t depth scalar Panel **c** | .tex Panel C R3 + briefing §13.3 | ✅ |

No caption ↔ figure inconsistencies detected at this draft level.

## Open items for paper-text iteration

- Sample composition note: paper sweeps S60–S85 in 5 wt%-steps (S60/S70/S75/S80/S85), Panel **b** shows 3 representative; Methods/SI must clarify full set.
- Control polymer choice for Panel **d**: caption uses "polyimide (PI)" as example; user's actual data has PI + PDMS + PET measured. Final caption should pick which control(s) to highlight or use generic "conventional dielectric control".
- Direction of *q*_tr polarity Panel **f**: caption presently does not commit to electron-vs-hole; if Methods commits, caption should match (briefing §8.1 Q6 closure).
- Δ*E*_t in Panel **c**: caption mentions "deep-trap level lies Δ*E*_t below the mobility edge" — Methods §M.x should give the operative definition (Boltzmann release energy, trap depth from CBM, etc.).
