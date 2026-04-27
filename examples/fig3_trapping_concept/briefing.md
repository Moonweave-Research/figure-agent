# Briefing — fig3_trapping_concept

> **Dogfooding note**: original `_reference_original/fig3_trapping_concept.tex` is in this
> folder as a benchmark. The dogfooding goal is to regenerate this figure end-to-end through
> figure-agent (briefing → prompt → external image gen → vector reconstruct) and compare
> the new vector output against the original. Filling this briefing in your own words (rather
> than copying from the original) is the honest path; otherwise the workflow is just a re-render.

## 1. What does this figure show? (1-2 sentences)

<!-- TODO: 사용자가 채움. 예: "PDMS와 sulfur polymer의 band diagram을 나란히 비교해
     deep trap이 charge retention의 핵심임을 시각화한다." -->

## 2. Domain vocabulary (terms, materials, mechanisms)

<!-- TODO: 사용자가 채움. 예시 항목:
     - Materials: PDMS, sulfur polymer
     - Band structure: LUMO, HOMO, conduction band (CB), valence band (VB), bandgap
     - Trap physics: shallow trap, deep trap (E_t), trapped electrons, thermal escape (kT << E_t)
     - Charge dynamics: injection, capture, recombination, retention
-->

## 3. Composition intent (panel layout, flow direction)

<!-- TODO: 사용자가 채움. 예시 골격:
     - Two-panel side-by-side: (a) PDMS / (b) Sulfur Polymer
     - Vertical E-axis on the left of each panel
     - Same y-coordinate scale across both panels (CB top, VB bottom, mid-gap = trap region)
     - (a): one mobile electron + one fast recombination arrow
     - (b): trap level lines (shallow + deep), trapped electrons at trap levels,
            injection arrow capturing into deep trap, weak thermal escape arrow with kT<<E_t label
     - Bottom one-line caption per panel summarizing the mechanism
-->

## 4. What MUST NOT appear (sensitive numbers, geometry, conditions)

<!-- TODO: 사용자가 채움. 예시:
     - Numerical trap depth values (E_t in eV)
     - Specific corona discharge voltages
     - Sample dimensions
     - wt% sulfur composition
-->

## 5. Style notes (optional)

<!-- TODO: optional. 예: Nature schematic, white/light-gray panel backgrounds,
     blue=conduction/electron, red=valence, amber=deep trap, gray=axis/recombination -->

---

When this briefing is filled, run `/fig_prompt` to generate the redacted prompt for external image generation.
