---
schema: figure-agent.critique.v1
fixture: golden_trap_depth_picture
generated_at: 2026-05-04T07:51:36Z
iteration: 7 (post v0.3 review-blocker fixes)
verdict: revise
grounding:
  - briefing.md §7 Author intent + Snippets used (now lists A1 polymer_chain + A2 log_plot)
  - reference image (golden_target_001.png) — pre-A1/A2 baseline; build improves on it
  - prior critique iter 5 (post-A1) for inherited findings
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
    observation: "Row 1 inline labels and evidence arrows require manual placement. The branch moved the Debye outgoing arrow to the plot right edge and moved slope/Debye/tau_d labels onto white-backed positions, but the visual-clash checker still reports 35 candidates elsewhere in the figure. This proves the remaining gate is an artifact policy/visual-QA gate, not a TeX compile gate."
    suggested_fix: "Do not mark accepted=true. For a later branch, add a callout/safe-label pattern and decide whether accepted fixtures should run visual clash strict by default."
    status: open
inherited_open:
  - "G002 (MAJOR, lobe height ratio): pre-existing from N=1; not addressed by A1/A2; targets A4 (dos_lobes via PGFPlots fillbetween). Claude visual review on 2026-05-04 confirmed this is a briefing §7 must-depict miss, not a cosmetic nit."
  - "Reference 'Discharge' label at (0.468, 0.075) — the original placement was *outside* the box on top. PGFPlots `title` puts it *inside* the box at the top. Drift 0.127 reported by /fig_compile is therefore intended — the new placement matches paper-figure convention better than the reference. Not a regression."
closed_findings:
  - "G001 (BLOCKER, polymer chains '지렁이'): CLOSED in iter 5 by A1 polymer_chain.snippet.tex."
  - "G004 (MAJOR, log axis tick logic): CLOSED by A2 PGFPlots loglogaxis. Tick labels now standard `10^k` format from PGFPlots default, minor grid auto-rendered, function evaluation real (power-law t^{-0.7} straight line + Debye exp(-t/τ) knee both visible)."
  - "FN001-class (Debye curve geometric inaccuracy in iter 4): CLOSED. Debye plot now uses log-spaced explicit coordinates approximating exp(-t/τ=30); replaces the hand-rolled Bézier that did not match true exponential decay shape."
  - "C002 (NIT, slope label tight): CLOSED in iter 7. Label moved to (axis cs:1.2e0, 8e-4) with white backing; visual clash no longer reports `slope`."
  - "C003 (NIT, tau_d label crowding): PARTIALLY CLOSED in iter 7. Label moved from (30, 3e-4) to (70, 8e-4) with white backing; remaining subscript `d` visual-clash warning is treated as part of C004 policy/gate work."
  - "B1 (MAJOR, Debye inline label clipping): CLOSED after Claude visual review. Label moved from (axis cs:9e1, 2e-1) to the lower-left empty plot region at (axis cs:3e-3, 1e-2) so `exp(-t/τ)` remains inside the plot area and off the curve."
---

# Vision Critique — golden_trap_depth_picture (iter 7, v0.3 A1 + A2)

**Verdict: REVISE for release.** A1/A2 integration compiles and improves the
semantic authoring surface, but this fixture is still not accepted for
manuscript/release because L6/L8 artifact gates remain open.

A2 PGFPlots `log_plot` integration into Row 1 closes G004 (MAJOR) and
FN001-class (Debye curve shape). The branch also fixes the immediate
scale-only-axis side effects found during review: the Debye outgoing arrow now
starts at the plot right edge instead of inside the restored axis area, and the
Row 1 inline labels are moved off the plotted curves with white backing.

Comparing the current build to `reference/golden_target_001.png`:

- **Reference Row 1 (pre-A2 state)**: tick labels positioned by hand `\foreach`
  loops, axes drawn as raw `\draw` lines, power-law as a single straight
  `\draw[cBlue] (0.18,2.25) -- (2.62,0.48)` with no actual functional meaning,
  Debye as a `\draw .. controls` Bézier that does not match true exp(-t/τ).
- **Current build (v0.3 A2)**: PGFPlots `loglogaxis` with `paper loglog`
  style key. Power-law is explicit log-spaced coordinates of c·t^{-0.7}
  (slope -0.7 visible across full 6-decade x range, 5-decade y range). Debye
  is log-spaced coordinates of exp(-t/30) showing the canonical plateau →
  knee → drop-off shape. Minor grids and `10^k` tick labels rendered by
  PGFPlots default behavior.

Why this matters:

- **Function evaluation grounding** (the real A2 motivation, not G004
  tick crowding): downstream critique iterations can now ask "is the curve
  the right *shape*?" instead of "is the line approximately diagonal?".
  A2 closes the gap that made the reference image's Debye curve
  geometrically wrong (Bézier handle artifact).
- **Style Lock unified**: both Row 1 plots and Row 3 polymer chains now
  share preamble-level style declarations (`paper loglog` for axes,
  `\printatom` + `\setchemfig` for monomers). A future plot or chain edit
  cannot drift visually without explicitly overriding the style.

## Per-finding discussion

**C001 — Row 1 plot box larger than prior hand-rolled axis (NIT).**
PGFPlots `paper loglog={3.6cm}{2.6cm}` includes tick labels and axis labels
inside the bounding box, so the *data area* is ~2.5 × 2.0 cm while the *box
extent* is 3.6 × 2.6. Old hand-rolled axes used 2.75 × 2.02 for the data
area only. Net visual change: Row 1 plots extend further right and slightly
upward into row 1 headroom. Row 1/2 separator at y=5.65 still has clearance.

**C002 — slope label tight against reference L (NIT, closed).** Label moved
from `(axis cs:1.5e0, 1.7e-3)` to `(axis cs:1.2e0, 8e-4)` with a small white
backing. `check_visual_clash.py` no longer reports `slope`.

**C003 — tau_d label crowded near bottom axis (NIT, partially closed).**
Label moved from `(axis cs:30, 3e-4)` to `(axis cs:70, 8e-4)` with white
backing. The remaining `d` warning is not enough to mark the figure accepted;
it is tracked under C004 with the broader strict visual gate.

**C004 — visual gate policy still open (MAJOR).** `check_visual_clash.py` still
reports 35 candidates after the Row 1 fix. Some are expected false positives
from legitimate labels on filled icons or chemical glyphs, but accepted-mode
golden artifacts must not treat that ambiguity as a pass. The correct next
engineering work is a safe callout/label pattern plus an accepted-fixture
strictness policy, not another compile-only macro tweak.

## What this critique does NOT address

- **G002 (MAJOR, lobe height ratio)**: still inherited; A4 target. Claude
  visual review confirmed the shallow/deep lobe ratio is a real briefing §7
  must-depict miss, not a cosmetic nit.
- **C004 (MAJOR, strict visual gate policy)**: still open; this fixture remains
  `accepted: false`.
- Discharge title drift 0.127 (vs reference): intended — title moved from
  outside-top to inside-top via PGFPlots `title` key, which is the
  paper-figure convention. Reference image was the inferior spec here.

## Next gate

A1 polymer_chain + A2 log_plot: integrated as WIP. This branch should close the
repo contract/test/documentation blockers first. A follow-up branch should
handle C004: safe plot callouts, visual-clash strictness policy for accepted
fixtures, and critique-rubric language for text-on-line findings.
