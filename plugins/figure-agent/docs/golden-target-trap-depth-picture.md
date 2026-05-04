# Golden Target 001 - Converged Trap-Depth Picture

**Date**: 2026-04-29
**Status**: first quality-kernel target
**Source**: user-provided PNG in the 2026-04-29 review session

## Goal

Recreate the supplied trap-depth schematic as a publication-ready vector figure.

The first quality-kernel milestone is not to add more prompt orchestration. It
is to prove that `figure-agent` can produce a visually credible vector artifact
from a demanding target figure, then diagnose whether remaining defects come
from source authoring, macro primitives, export quality, or QA weakness.

Target outputs:

- editable vector source: TikZ preferred, SVG acceptable for the first pass;
- PDF export;
- SVG export;
- PNG raster export at manuscript-review resolution.

## Non-Negotiable Acceptance Criteria

The recreated figure must satisfy all of these before it can count as the
golden fixture:

1. **Element completeness**
   - All major visual elements in the target are present.
   - No panel, arrow, axis, label, curve, chain, trap marker, or distribution
     lobe is omitted.

2. **Label correctness**
   - Every text label is readable and semantically attached to the correct
     object.
   - Required labels include `Experiment`, `Mathematical interpretation`,
     `Molecular origin`, `I(t) alpha t^-n`, `slope = -n`, `Discharge (Debye
     reference)`, `Debye exp(-t/tau)`, `tau_d`, `n`, `g(E_t)`, `shallow`,
     `deep`, `localized traps`, `S-rich segments`, `chemical origin`, `physical
     origin`, `converged trap-depth picture`, `Energy`, `CB`, `VB`, and `E_t`.
   - The rendered PDF must pass the required-label floor in
     `scripts/check_golden_artifacts.py`; `.tex` substring checks do not count as
     label verification.

3. **No visible collisions**
   - Text does not overlap other text, axes, curves, icons, or panel borders.
   - Curves and markers do not collide in a way that changes the intended
     meaning.
   - `check_collisions.py` and `check_visual_clash.py` may warn only for known,
     documented false positives.

4. **Visual hierarchy**
   - The right-side converged trap-depth picture is the visual endpoint.
   - The three left-side rows read as experiment, mathematical interpretation,
     and molecular origin.
   - Arrows guide the eye toward the converged trap-depth picture without
     cluttering the figure.

5. **Style consistency**
   - White background.
   - Thin gray separators and arrows.
   - Blue power-law line and electron markers.
   - Orange shallow traps and distribution lobe.
   - Purple deep traps and distribution lobe.
   - Teal title and right-side brace.
   - Font scale is manuscript-readable after double-column fitting.

6. **Export fidelity**
   - PDF, SVG, and PNG preserve layout, fonts, colors, and stroke weights.
   - SVG opens in a browser without missing text or broken paths.
   - PNG has a white background and no transparency-induced black canvas.
   - The accepted fixture must pass `scripts/check_golden_artifacts.py`, including
     the SVG visible-element floor and opaque-white PNG corner check.

7. **Accepted-mode gate**
   - `spec.yaml` must explicitly contain `accepted: true`.
   - `QUALITY_AUDIT.md` must be fresh relative to source and exports.
   - Accepted fixtures must pass:
     `uv run python3 scripts/check_golden_artifacts.py examples/golden_trap_depth_picture --require-accepted --max-collisions 0 --max-visual-clashes 0`.
   - First-pass fixtures may pass the sanity gate while still failing accepted
     mode; that state must not be reported as manuscript-ready.

## Target Layout Inventory

### Canvas

- Wide landscape figure.
- Three horizontal narrative bands on the left two-thirds.
- Large converged picture on the right third.
- Two thin horizontal separator lines divide the three left bands.

### Row 1 - Experiment

Elements:

- Left label/icon stack:
  - small instrument icon with a mini decay curve inside;
  - text label `Experiment`.
- Main power-law log-log plot:
  - x-axis label `log t`;
  - y-axis label `log I`;
  - blue straight descending line;
  - blue dashed vertical helper line;
  - text `I(t) alpha t^-n`;
  - text `slope = -n`.
- Debye reference plot in a rounded rectangle:
  - title `Discharge (Debye reference)`;
  - gray concave-down curve;
  - x-axis label `log t`;
  - y-axis label `log I`;
  - text `Debye exp(-t/tau)`;
  - gray dashed vertical helper line;
  - label `tau_d`.
- Gray arrow leading toward the right-side convergence brace.

### Row 2 - Mathematical Interpretation

Elements:

- Left label/icon stack:
  - small square equation icon;
  - text label `Mathematical interpretation`.
- Formula chain:
  - `I(t) alpha t^-n`;
  - arrow to `n`;
  - `Debye exp(-t/tau)` over downward arrow to `tau_d`;
  - arrow to `g(E_t)`;
  - shallow/deep two-lobe mini distribution with orange and purple lobes;
  - arrow toward the right-side convergence brace.

### Row 3 - Molecular Origin

Elements:

- Left label/icon stack:
  - small curled polymer-chain icon with sulfur markers;
  - text label `Molecular origin`.
- Three long gray wavy polymer chains.
- Orange sulfur markers and `S` labels along the chains.
- Dashed rounded highlight around an S-rich chain segment.
- Orange label `S-rich segments`.
- Gray annotation arrow and label:
  - `chemical origin`;
  - `(electronegativity, polarizability of S)`.
- Dashed rounded box labeled `localized traps` containing:
  - orange shallow trap levels with blue electron dots;
  - purple deep trap levels with blue electron dots;
  - ellipsis marks.
- Gray annotation arrow and label:
  - `physical origin`;
  - `(local potential fluctuations)`.
- Gray arrows connecting molecular origin and localized traps toward the final
  converged picture.

### Right-Side Converged Picture

Elements:

- Teal vertical brace grouping the incoming evidence.
- Teal title `converged trap-depth picture`.
- Energy-level diagram:
  - vertical `Energy` axis;
  - line-style `CB` band edge at top with compact label;
  - line-style `VB` band edge at bottom with compact label;
  - orange shallow localized trap levels with blue electron dots near CB;
  - purple deep localized trap levels with blue electron dots near VB;
  - dashed vertical divider near the distribution plot;
  - label `E_t` near the divider.
- Trap-depth distribution plot:
  - vertical axis with arrow;
  - horizontal axis with arrow;
  - label `g(E_t)` above and on x-axis;
  - orange shallow lobe at higher energy;
  - larger purple deep lobe at lower energy;
  - labels `shallow` and `deep`.

## Defect Classification Required

Every failed attempt must classify visible defects into one of these buckets:

- **Source defect**: manual/LLM-authored TikZ/SVG places or draws something
  incorrectly.
- **Macro defect**: the style/macro library lacks the primitive needed to draw
  the target cleanly.
- **Export defect**: PDF/SVG/PNG conversion changes the visual result.
- **QA defect**: a visible issue exists but the checkers do not report it.

Classification rule of thumb:

- Keep a defect in **source** when it is a one-off coordinate, label, or drawing
  error in this single figure.
- Escalate to **macro** only when the same semantically identical primitive
  appears at least three times or will clearly recur across future schematic
  figures.
- Use **export** only when the PDF is visually correct and SVG/TIFF/PNG
  conversion changes it.
- Use **QA** only when a visible defect survives the current automated gates and
  would be worth catching again.

## First Implementation Strategy

Start with a controlled vector reconstruction, not a blind prompt-generation
loop.

Recommended first pass:

1. Build a single editable TikZ source for this target.
2. Use stable coordinate grids and named scopes for each row and the right-side
   convergence diagram.
3. Render PDF and PNG.
4. Export SVG.
5. Run collision and visual-clash checks.
6. Compare visually against the target and write a defect table.
7. Only then decide whether to improve source layout, add macros, alter export,
   or strengthen QA.

The pass/fail bar is manuscript credibility, not merely successful compilation.
