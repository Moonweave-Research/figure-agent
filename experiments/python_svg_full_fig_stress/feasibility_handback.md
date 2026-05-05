# Python SVG Full-Figure Stress Feasibility Handback

## Artifacts

- `full_figure.svg`
- `full_figure.png`
- `src/full_figure.py`
- `src/stack/drawsvg_helpers.py`
- `src/stack/dvisvgm_math.py`
- `friction_log.md`
- `defect_log.md`
- `time_log.md`
- `comparison_full.md`

## Evidence

- Full multi-panel figure generated from Python.
- SVG XML parsed successfully during every implementation step.
- PNG rendered with `rsvg-convert`.
- One visual defect loop was completed after image inspection.
- Forbidden stack components were not used in source code.

## Feasibility Statement

Under the locked stack, Python SVG is feasible for complex two-dimensional scientific overview figures with schematic panels, plot-like lobes, arrows, callouts, and LaTeX-grade math labels.

It is not yet proven as a Nature Communications final-art pipeline. The current output is a strong stress artifact, not final publication polish. The remaining gap is not basic rendering; it is scalable chemistry drawing, layout automation, collision-aware typography, reusable plot grammars, and human visual refinement.

## Stack Limits Observed

- Chemistry-like structures can be hand-drawn for a specific figure, but arbitrary chemistry needs a dedicated renderer outside the locked stack.
- dvisvgm math is high quality but lacks automatic box metrics for layout decisions.
- Matplotlib SVG embedding works but produces verbose SVG, requiring cleanup for deterministic source artifacts.
- Full-figure layout remains coordinate-driven and benefits from direct visual iteration.

## Practical Conclusion

Python-only is viable for many 2D schematic-heavy paper figures.

For a real Nature Communications workflow, the honest target is likely hybrid unless chemistry panels are excluded or a chemistry-rendering dependency is explicitly allowed.
