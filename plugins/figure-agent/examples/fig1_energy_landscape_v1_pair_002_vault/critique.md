---
schema: figure-agent.critique.v1
fixture: fig1_energy_landscape_v1_pair_002_vault
generated_at: 2026-05-12T16:35:00+09:00
verdict: revise
panels: []
findings:
  - id: C001
    severity: MAJOR
    category: label_placement
    tex_lines: [114, 118]
    observation: "Panel C top subplot still overlaps 'Debye' and 'slow tail' labels at the right edge of the I(t) plot (text_on_path WARN dark=0.045 + WARN dark=0.059). The two labels sit within ~0.2 cm of each other at x≈6.30 — 'Debye' anchored south east at the dashed curve endpoint and 'slow tail' anchored north east at the blue power-law endpoint — reading as a single cluster. The same issue carries over from the no_vault arm because Panel C did not receive a vault grammar shift."
    suggested_fix: "Move 'slow tail' to a mid-curve callout near (3.55, 3.55) using a short cGray!70 leader and anchor=south. The blue power-law curve has clear vertical space at that x range. Keep 'Debye' at the endpoint."
    status: open
  - id: C002
    severity: MINOR
    category: label_placement
    tex_lines: [56, 58, 60]
    observation: "Panel A shows two tiny 'S' atom fragments at the extreme left edge of the figure (around x≈-0.05, y≈4.20-4.40) — visible in the rendered PNG as ghost letters near the left margin. These appear to be a \\WavyChain side-effect from the brace-wrapped S_csv parsing emitting a stray atom node outside the intended chain range when the chain endpoint x1=0.30 sits right next to the figure background's rounded-corner edge at x=-0.10."
    suggested_fix: "Trim the chain start to x1=0.40 instead of 0.30 to give the leading S marker clearance from the figure-wide background rectangle. Alternatively, move the chain S_csv items to start at x≥0.5 so no S glyph is drawn on the figure-frame boundary."
    status: open
  - id: C003
    severity: MINOR
    category: label_placement
    tex_lines: [101]
    observation: "Panel A 'localized traps' inline label at (6.80, 8.55) anchor=north east occupies the same y row as 'sulfur-rich network' (anchor=north west at 0.10, 8.55) but with different style tiers (italic gray vs strong amber). Both fit, but the vertical alignment to the same baseline reads as a two-column title — which is fine if intended, but the briefing positioned 'localized traps' in the lower region of the panel."
    suggested_fix: "Move 'localized traps' to anchor=north at (3.45, 4.95) — centered above the legend strip — so the upper labels read 'sulfur-rich network' alone and the trap callout sits with its legend dots."
    status: open
  - id: C004
    severity: MINOR
    category: hierarchy
    tex_lines: [231, 240]
    observation: "Panel D 'fast release' (cBlue!75!black) and 'long retention' (cRed!75!black) callouts use labelMute font tier, equating them visually with axis-tick labels rather than panel conclusions."
    suggested_fix: "Promote both to labelStrong with the same color choices. The color carries the shallow/deep mapping; the strong tier carries 'this is the panel's takeaway, not an axis annotation'."
    status: open
  - id: C005
    severity: NIT
    category: whitespace
    tex_lines: [83, 89]
    observation: "Panel A 'exchange' annotation (dashed amber arrow with label) sits between the upper and lower polymer chains, intended to evoke the cho2024_fig1_dynamic_exchange vault motif. Currently the arrow loops between two trap dots at y≈6.65 and y≈6.05 — visually reads, but the 'exchange' label at (3.75, 6.42) sits very close to the chain at y=5.45 and the second DIB ring at y=6.05."
    suggested_fix: "Raise the 'exchange' label y to 6.60 with anchor=south, putting the text above the arrow midpoint instead of beside it. This gives the dashed arrow visual breathing room from the lower chain."
    status: open
  - id: C006
    severity: NIT
    category: physics
    tex_lines: [83]
    observation: "Panel A retained-charge marker at (2.95, 6.80) is the same circular style as the deep-trap dots, so the retained-charge 'inside a deep trap' annotation is implied only by the dashed 'exchange' arrow termination."
    suggested_fix: "Add a small white minus sign on top of the retained-charge dot, or use a distinct filled-diamond shape to differentiate retained-charge from a generic deep trap."
    status: open

---

# Vision Critique — fig1_energy_landscape_v1_pair_002_vault

Pilot pair `fig1_energy_landscape_v1_pair_002`, arm = vault. Authored from the
same immutable design.md (SHA 9b4e36033336826a566dfb7dfb95e6ac4...) plus
approved-only vault metadata as grammar/style anchors (query
a5c0a136-f6b3-4d72-940a-54a87dd6a97b, source_access=masked,
raw_source_path_exposed=false, degraded_mode=true preserved). The 4-panel 2×2
schematic compiles cleanly into a single 1-page PDF (≈117 KB) at the requested
178 mm width.

Three grammar shifts are visible in the rendered PNG versus the no_vault arm:

1. **Panel A** uses `\WavyChain` zigzag for two parallel polymer chains
   instead of the no_vault arm's single bezier weave. The S markers are
   distributed across both chains, giving the network a clear 'two
   cross-linked chains' reading rather than one curved scribble. A dashed
   'exchange' annotation arrow ties a retained-charge deep trap to the lower
   DIB ring — the cho2024_fig1_dynamic_exchange motif anchor.

2. **Panel B** carries the depth hierarchy on the curve itself: shallow
   region drawn in cBlue!85!black at amplitude 0.40, deep region drawn in
   cRed!85!black at amplitude 1.00 (depth ratio ≈ 2.5×). The retention
   annotation includes a small filled red charge dot at the deep-well
   minimum — the cho2024_fig7_corona_charge anchor — so the arrow now reads
   as 'charge bound in well' rather than a plain Stealth.

3. **Panel D** uses the preamble's `\BellCurve` macro (vault motif:
   patel2019_fig4_trap_dos) for both shallow and deep distributions. The
   resulting lobes have the canonical paper-grade Gaussian silhouette and a
   visibly larger depth/breadth contrast than the no_vault arm's hand-rolled
   bezier lobes.

The compile-side QA signal also shifted: zero IoU collisions (vs three in the
no_vault arm) and 22 visual clash candidates (vs 30). Both are report-only,
but they corroborate the grammar improvements.

Remaining findings are mostly carryover from Panel C (which did not receive a
vault grammar shift, only typography hierarchy) and a small \\WavyChain
side-effect at the figure left margin (C002). The 'exchange' annotation and
retained-charge differentiation in Panel A could go further (C005-C006).

**Verdict: revise.** No BLOCKER physics violations; color convention applied
correctly throughout. Address C001 (the Panel C label overlap shared with the
no_vault arm) and C002 (the \\WavyChain margin glyphs) before manuscript use;
C003-C006 can carry into a second pass.

**Pilot-pair context.** This arm is the vault-grounded arm of pair_002. The
critique is host-orchestrated (subscription tokens, zero external API) and is
report-only. Whether the visible quality differences versus the no_vault arm
are caused by vault grounding or by independent authoring discipline is a
question for an external blind evaluator, not for this critique. This run
does **not** perform or claim blind A/B evaluation.
