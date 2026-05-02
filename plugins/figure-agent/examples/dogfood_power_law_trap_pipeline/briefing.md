# briefing — dogfood_power_law_trap_pipeline

## 1. Topic

Conceptual schematic linking Isothermal Surface Potential Decay (ISPD) power-law analysis to trap-depth distribution inference in sulfur-containing polymers. The figure depicts the methodological pipeline from experimental I(t) decay through mathematical interpretation, chemical/physical origin of carriers, energy-level inference, and final trap density of states g(E_t).

## 2. Domain vocabulary

- 황고분자 (sulfur-containing polymer); S-rich segments vs isolated S atoms
- ISPD (Isothermal Surface Potential Decay)
- shallow trap / deep trap
- Conduction Band / Valence Band (약자 X — full words required throughout)
- power-law decay; decay time τ_d; Debye relaxation exp(-t/τ)
- trap density of states g(E_t)

## 3. Composition intent

5-panel left-to-right conceptual flow, each panel separated by a horizontal arrow marking a methodological transition:

1. Panel 1 — **Experimental trace**: log-log plot of I(t) ∝ t^(-n) with slope-n triangle annotation; single straight line on log-log axes (axes are symbolic representation of "wide time/intensity range", not measured data points).
2. Panel 2 — **Mathematical interpretation**: three extracted quantities (n, τ_d, g(E_t)) listed vertically with arrows leading right; a small Debye exp(-t/τ) inset associated with τ_d.
3. Panel 3 — **Chemical / physical origin**: three zigzag polymer chain rows; sulfur (S) atoms shown as small amber markers above the chain. Middle row highlights "S-rich segments" with a dashed bracket and two callout arrows pointing to "chemical origin" (left) and "physical origin" (right).
4. Panel 4 — **Trap-depth inference**: band diagram with Conduction Band block on top and Valence Band block on bottom; shallow trap levels (amber) below the Conduction Band, deep trap levels (purple) above the Valence Band; electron markers (blue dots) on a subset of trap levels; vertical Energy axis on the left.
5. Panel 5 — **Trap distribution (ISPD)**: g(E_t) profile with two side-oriented bell lobes stacked vertically — shallow lobe (amber) on top with slightly smaller amplitude, deep lobe (purple) on bottom. Horizontal axis labeled g(E_t).

Inter-panel connections: straight gray arrows between Panels 1→2→3→4. From Panel 4 to Panel 5, three teal curved arrows map (Conduction Band → shallow lobe), (between bands → between lobes), (Valence Band → deep lobe).

## 4. Normalize / avoid literal overfit

skip

## 5. Style notes

Nature Communications premium figure aesthetic. Palette and font sizes auto-bound via `polymer-paper-preamble` Style Lock conventions; no overrides. Trust the preamble's stroke weights and tick label scale — match the visual register of a methods-pipeline display figure.

## 6. Physics invariants

- I(t) ∝ t^(-n) form is canonical; do not substitute exponential or stretched-exponential.
- 5-panel left-to-right ordering is fixed; panels cannot be reordered.
- Conduction Band sits above Valence Band; energy axis points upward in Panel 4.
- shallow trap binds to amber palette; deep trap binds to purple (cBlue!45!cRed); Panel 4 and Panel 5 must use consistent color binding for shallow vs deep.
- Panel 4 trap levels and Panel 5 distribution lobes correspond 1:1: shallow levels → shallow lobe, deep levels → deep lobe; the teal curved arrows make this mapping explicit.
- S-rich (clustered) segments represent chemical origin; isolated S atoms represent physical origin (Panel 3 callouts).
- Panel 5 shallow lobe has slightly smaller amplitude/integral than deep lobe (asymmetric, not equal-height).
- Inter-panel arrow direction (left → right) conveys the methodological inference flow and is fixed.
