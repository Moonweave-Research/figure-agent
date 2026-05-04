---
schema: figure-agent.critique.v1
fixture: golden_trap_depth_picture
generated_at: 2026-05-04T08:57:43Z
iteration: 10 (post polymer schematic redraw)
verdict: revise
grounding:
  - briefing.md §7 Author intent + Snippets used (now lists A1 polymer_chain + A2 log_plot)
  - build/golden_trap_depth_picture.png rendered after PlotCallout adoption and Row 3 polymer redraw
  - reference image (golden_target_001.png) — pre-A1/A2 baseline; build improves on it
  - prior critique iter 8 for deep-dominant DOS and band-edge context
findings:
  - id: C001
    severity: NIT
    category: hierarchy
    tex_lines: [52, 53, 54]
    observation: "Row 1 power-law plot scope shift unchanged at (3.15, 6.15). PGFPlots axis box (3.6 x 2.6 cm) is larger than the prior hand-rolled axis (2.75 x 2.02 cm), so the plot extends ~0.6 cm further right and ~0.4 cm taller than before. Visible as Discharge plot moving slightly right relative to row label column. No collision; falls within row separator headroom."
    suggested_fix: "Optional: shift Row 1 power-law scope from (3.15,6.15) to (2.85,5.95) to recenter visually with label column. Current placement compiles cleanly; cosmetic only."
    status: open
  - id: C004
    severity: MAJOR
    category: visual_gate_policy
    tex_lines: [69, 95, 98, 103]
    observation: "The missing safe-label primitive is now closed by `\\PlotCallout`, and the slope/τ labels in Row 1 dogfood it. The visual-clash checker still reports 38 candidates elsewhere in the figure, so the remaining issue is accepted-artifact policy and source-defect cleanup, not a missing annotation macro."
    suggested_fix: "Do not mark accepted=true. Keep `/fig_compile` report-only for iteration, use `FIGURE_AGENT_STRICT=1` for manuscript/CI checks, and keep `check_golden_artifacts.py --require-accepted` as the golden hard gate until the unresolved visual-clash budget reaches 0."
    status: open
inherited_open:
  - "Reference 'Discharge' label at (0.468, 0.075) — the original placement was *outside* the box on top. PGFPlots `title` puts it *inside* the box at the top. Drift 0.127 reported by /fig_compile is therefore intended — the new placement matches paper-figure convention better than the reference. Not a regression."
closed_findings:
  - "G001 (BLOCKER, polymer chains '지렁이'): CLOSED in iter 5 by A1 polymer_chain.snippet.tex, then refined in iter 10 from raw chemfig-like structure to curated schematic TikZ after visual review."
  - "G004 (MAJOR, log axis tick logic): CLOSED by A2 PGFPlots loglogaxis. Tick labels now standard `10^k` format from PGFPlots default, minor grid auto-rendered, function evaluation real (power-law t^{-0.7} straight line + Debye exp(-t/τ) knee both visible)."
  - "FN001-class (Debye curve geometric inaccuracy in iter 4): CLOSED. Debye plot now uses log-spaced explicit coordinates approximating exp(-t/τ=30); replaces the hand-rolled Bézier that did not match true exponential decay shape."
  - "C002 (NIT, slope label tight): CLOSED in iter 7. Label moved to (axis cs:1.2e0, 8e-4) with white backing; visual clash no longer reports `slope`."
  - "C003 (NIT, tau_d label crowding): PARTIALLY CLOSED in iter 7. Label moved from (30, 3e-4) to (70, 8e-4) with white backing; remaining subscript `d` visual-clash warning is treated as part of C004 policy/gate work."
  - "B1 (MAJOR, Debye inline label clipping): CLOSED after Claude visual review. Label moved from (axis cs:9e1, 2e-1) to the lower-left empty plot region at (axis cs:3e-3, 1e-2) so `exp(-t/τ)` remains inside the plot area and off the curve."
  - "G002 (MAJOR, lobe dominance): CLOSED in iter 8 after author correction. The prior briefing/review text had the ratio backwards; deep lobe, not shallow lobe, is the intended dominant g(E_t) component. Row 2 and the right-side distribution now render deep visibly larger than shallow."
  - "B2-class (right energy-band encoding): CLOSED in iter 8 for this fixture. CB/VB are now line-style band edges with compact labels, not gray filled boxes."
  - "Snippet encapsulation gap (safe plot annotation): CLOSED in iter 9. `\\PlotCallout` was added to `polymer-paper-preamble.sty`, documented in `docs/macros/plot-callout.md`, counted by lint/source inventory, and used for slope + `\\tau_d` labels."
  - "L4.5 label-placement blind spot: CLOSED in iter 9 at rubric level. `docs/critique-evaluation-rubric-v1.md` now requires `label_placement.text_on_line`, `label_placement.label_clipped`, and `label_placement.annotation_crosses_data` checks."
  - "Visual WARN force policy: CLOSED in iter 9 at operating-policy level. `/fig_compile` remains report-only for reviewable builds; `FIGURE_AGENT_STRICT=1` and `check_golden_artifacts.py --require-accepted` are documented as the hard-gate paths."
---

# Vision Critique — golden_trap_depth_picture (iter 10, polymer schematic redraw)

**Verdict: REVISE for release.** A1/A2 integration compiles and improves the
semantic authoring surface, iter 8 closes the previously inverted lobe ratio,
and iter 10 improves the molecular row by replacing the raw chemfig-like chain
with a cleaner schematic TikZ macro. This fixture is still not accepted for
manuscript/release because L6/L8 artifact gates remain open.

A2 PGFPlots `log_plot` integration into Row 1 closes G004 (MAJOR) and
FN001-class (Debye curve shape). Iter 9 also fixes the macro/system gap behind
the Row 1 label collisions: slope and `\tau_d` now use `\PlotCallout`, a
white-backed leader-label primitive, instead of bare inline nodes placed
directly on the plotted geometry.

Comparing the current build to `reference/golden_target_001.png`:

- **Reference Row 1 (pre-A2 state)**: tick labels positioned by hand `\foreach`
  loops, axes drawn as raw `\draw` lines, power-law as a single straight
  `\draw[cBlue] (0.18,2.25) -- (2.62,0.48)` with no actual functional meaning,
  Debye as a `\draw .. controls` Bézier that does not match true exp(-t/τ).
- **Current build (v0.3 A2 + PlotCallout)**: PGFPlots `loglogaxis` with
  `paper loglog` style key. Power-law is explicit log-spaced coordinates of
  c·t^{-0.7}
  (slope -0.7 visible across full 6-decade x range, 5-decade y range). Debye
  is log-spaced coordinates of exp(-t/30) showing the canonical plateau →
  knee → drop-off shape. Minor grids and `10^k` tick labels rendered by
  PGFPlots default behavior. Inline explanatory labels with known line-contact
  risk use `\PlotCallout`.

Why this matters:

- **Function evaluation grounding** (the real A2 motivation, not G004
  tick crowding): downstream critique iterations can now ask "is the curve
  the right *shape*?" instead of "is the line approximately diagonal?".
  A2 closes the gap that made the reference image's Debye curve
  geometrically wrong (Bézier handle artifact).
- **Style Lock unified**: Row 1 plots, plot callouts, and Row 3 polymer chains
  now share preamble/snippet-level style declarations (`paper loglog` for axes,
  `plotCallout*` styles for annotation leaders, and `\PolymerChain` for
  monomer-resolved S-rich chains). A future plot or chain edit cannot drift
  visually without explicitly overriding the style.

## Per-finding discussion

**C001 — Row 1 plot box larger than prior hand-rolled axis (NIT).**
PGFPlots `paper loglog={3.6cm}{2.6cm}` includes tick labels and axis labels
inside the bounding box, so the *data area* is ~2.5 × 2.0 cm while the *box
extent* is 3.6 × 2.6. Old hand-rolled axes used 2.75 × 2.02 for the data
area only. Net visual change: Row 1 plots extend further right and slightly
upward into row 1 headroom. Row 1/2 separator at y=5.65 still has clearance.

**C002 — slope label tight against reference L (NIT, closed).** Label moved
from a bare node to `\PlotCallout[text=cBlue, anchor=north west]`, pointing at
the slope reference corner from `(axis cs:1.2e0, 8e-4)`. The label is no longer
drawn as free-floating text on the dashed guide.

**C003 — tau_d label crowded near bottom axis (NIT, closed for Row 1).**
Label moved from a bare node to `\PlotCallout[text=cGray, anchor=south west]`,
pointing at the dashed `\tau_d` marker from `(axis cs:7e1, 8e-4)`. The
remaining `d` warning is part of the global visual-clash candidate pool, not a
visible label-on-line defect after manual PNG review.

**C004 — accepted visual gate still open (MAJOR).** `check_visual_clash.py`
still reports 38 candidates after the Row 1 PlotCallout fix and Row 3 redraw.
Some are expected
false positives from legitimate labels on filled icons or compact S markers, but
accepted-mode golden artifacts must not treat that ambiguity as a pass. The
engineering surface is now explicit: `/fig_compile` emits reviewable artifacts,
`FIGURE_AGENT_STRICT=1` gives a strict compile loop, and
`check_golden_artifacts.py --require-accepted` is the ship gate.

**G002 — lobe dominance semantics (MAJOR, closed in iter 8).** The earlier
briefing text said the shallow lobe should be 2×–3× taller than deep. That was
the wrong source-of-truth. The corrected intent is deep-dominant: shallow traps
remain closer to CB, deep traps remain closer to VB, but the lower-energy deep
component carries the larger g(E_t) lobe. The fixture now encodes that in both
Row 2 and the right-side distribution.

**B2-class — right band encoding (closed for fixture).** The previous right-side
CB/VB rendering read as gray boxes rather than band edges. Iter 8 replaces those
with line-style CB/VB band edges and compact labels while preserving the vertical
Energy axis and interior E_t divider. This fixture intentionally uses the
lower-level `\BandBox`, `\TrapLevel`, and `\BellCurve` primitives instead of
forcing the current `\BandDiagram` composite, because that composite still has
known model gaps for this exact right-panel layout.

## What this critique does NOT address

- **C004 (MAJOR, accepted visual gate)**: still open; this fixture remains
  `accepted: false`.
- Discharge title drift 0.127 (vs reference): intended — title moved from
  outside-top to inside-top via PGFPlots `title` key, which is the
  paper-figure convention. Reference image was the inferior spec here.

## Next gate

A1 polymer_chain + A2 log_plot + `\PlotCallout`: integrated and rendered. This
branch should land the macro/test/documentation hardening plus the Row 3
schematic redraw. A follow-up visual polish pass should reduce the remaining 13
unresolved visual-clash source defects before `accepted: true` is even
considered.
