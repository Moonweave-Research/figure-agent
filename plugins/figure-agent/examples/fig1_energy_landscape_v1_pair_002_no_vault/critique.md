---
schema: figure-agent.critique.v1
fixture: fig1_energy_landscape_v1_pair_002_no_vault
generated_at: 2026-05-12T16:25:00+09:00
verdict: revise
panels: []
findings:
  - id: C001
    severity: MAJOR
    category: label_placement
    tex_lines: [129, 131, 133, 136, 138]
    observation: "Panel A bottom-edge legend collapses three labels into one row: the 'localized traps' label (anchored south east at 6.80, 4.70), the legend dots, and the 'shallow' / 'deep' inline labels all sit on or near y=4.70-4.85, producing the collision report IoU=0.291 between 'localized' and 'deep' and IoU≈0.06 between 'S' and 'localized'. In the rendered PNG the three labels overlap visually as a single mushy strip beneath Panel A."
    suggested_fix: "Move 'localized traps' to anchor=north east at (6.80, 8.55), pairing it with the upper-left 'sulfur-rich network' label as a two-token title row. Keep the shallow/deep legend at y=4.85 but move it to anchor=west at x=0.30 (panel left edge) so the bottom strip carries only the legend and the trap-region inline labels are unambiguous."
    status: open
  - id: C002
    severity: MAJOR
    category: hierarchy
    tex_lines: [115, 130]
    observation: "Panel B energy curve does not visually communicate the shallow-vs-deep depth hierarchy required by design.md §'Panel B' ('shallow traps in blue and deep traps in red, ≥3 shallow wells and ≥2 deep wells'). The bezier curve drawn in cGray!75!black uses near-equal well depths (shallow amplitude 0.45, deep amplitude 0.95 ratio ≈ 2.1×) but the rendered amplitudes look closer to 1.4× because the deep wells are drawn with the same line weight (0.85pt) and absent any color-coded well-line. Color is carried only by the blue/red region overlays, not by the curve itself."
    suggested_fix: "Split the single gray bezier into a blue shallow segment (x=7.60-10.45) and a red deep segment (x=10.95-13.55), each drawn with line width 1.0pt and its own color. Increase the deep amplitude from 0.95 to 1.10 so the depth ratio reads ≥2.5×. The current visual contrast does not honor the design rubric."
    status: open
  - id: C003
    severity: MAJOR
    category: label_placement
    tex_lines: [183, 184, 185]
    observation: "Panel C top subplot collides labels 'Debye' and 'slow tail' at the right edge (text_on_path WARN dark=0.049 + WARN dark=0.044 in two stacked rows). In the rendered PNG, 'Debye' anchor=south east at (6.30, 2.90) is the dashed-curve endpoint label and 'slow tail' anchor=north east at (6.30, 3.10) is the power-law label — both sit within ~0.2cm of each other on the right margin, reading as a single illegible cluster."
    suggested_fix: "Move 'slow tail' to anchor=north at the midpoint of the blue power-law line (x≈3.55, y≈3.55) with a short callout line (0.95pt cGray!70). Keep 'Debye' at the dashed-curve endpoint. The annotations carry different roles (one labels the trap-mediated curve, the other labels the Debye reference) and should not stack."
    status: open
  - id: C004
    severity: MINOR
    category: label_placement
    tex_lines: [186, 218]
    observation: "Panel C 'log t' x-axis label appears once at the bottom subplot but is supposed to be the shared x-axis label per design §'Panel C' ('log-time x-axis'). The top subplot's x-axis is unlabeled, which a reader could parse as 'top has no x-axis' rather than 'shared x with bottom'."
    suggested_fix: "Add a faint cGray!50 'log t' label below the top subplot at (3.50, 2.78) or, alternatively, remove the bottom subplot's standalone 'log t' label and place a single shared label at the visual centroid (3.50, 0.20) with a connecting hint."
    status: open
  - id: C005
    severity: MINOR
    category: physics
    tex_lines: [85]
    observation: "Panel A 'retained charge marker' is drawn as a single small red dot at (3.10, 6.50) inside a deep-trap node, but the design brief calls for a clearly identifiable retained-charge symbol distinct from the generic trap dots. As rendered, the retained-charge marker is indistinguishable in color/shape from the surrounding deep traps, defeating the 'retention' callout."
    suggested_fix: "Either enlarge the retained-charge marker to minimum size=3.4mm and add a white minus sign with thicker outline, or change to a filled red diamond shape distinct from the circular trap dots."
    status: open
  - id: C006
    severity: NIT
    category: whitespace
    tex_lines: [56]
    observation: "Panel A polymer chain enters from x=0.30 but the 'e^-' incoming-charge label at the same x range crowds the chain's entry point (the chain bezier starts at y=8.50 and the charge label sits at y=8.85 anchor=south west — only 0.35cm separation)."
    suggested_fix: "Shift the chain entry point down by 0.15cm to (0.30, 8.35) or shift the 'e^-' label to anchor=east at (0.20, 8.85) so the charge arrow tip and chain entry do not visually merge."
    status: open
  - id: C007
    severity: NIT
    category: hierarchy
    tex_lines: [225, 247]
    observation: "Panel D 'fast release' and 'long retention' callouts are styled with labelMute (italic gray-tinted), making them visually equivalent to axis tick labels rather than the diagnostic conclusions of the panel."
    suggested_fix: "Promote 'fast release' and 'long retention' to labelStrong with their respective colors (cBlue!75!black and cRed!75!black), matching the inline 'shallow' / 'deep' label hierarchy in Panel B."
    status: open

---

# Vision Critique — fig1_energy_landscape_v1_pair_002_no_vault

Pilot pair `fig1_energy_landscape_v1_pair_002`, arm = no_vault. Authored only
from the immutable design.md snapshot (SHA 9b4e36033336826a566dfb7dfb95e6ac4...),
no tikz-vault references consulted. The 4-panel 2×2 schematic compiles cleanly
into a single 1-page PDF (≈116 KB) at the requested 178 mm width, with all
physics axes labeled and the shallow/deep color convention honored.

The figure carries the briefing's intent — sulfur-rich polymer network in
Panel A, an energy landscape with shallow and deep wells in Panel B, paired
I(t) and V_s(t) decay curves in Panel C, and a shallow vs deep distribution
comparison in Panel D — but does so with a one-pass, geometry-first idiom
that leaves three label-placement and one hierarchy issue visible in the
build PNG.

**The two MAJOR placement findings are the dominant signal.** Panel A's bottom
edge collapses the 'localized traps' inline label, the shallow/deep legend
dots, and the legend text into a single ~0.2 cm strip, producing the
collision-checker IoU=0.291 (well above the WARN threshold). Panel C's top
subplot overlaps 'Debye' and 'slow tail' at the right margin so the reader
cannot tell which label belongs to which curve. Both are fixable with label
re-anchoring rather than geometry changes.

The MAJOR hierarchy finding (C002) is structural: design.md §Panel B requires
shallow vs deep depth contrast as the panel's visual anchor, but the curve is
drawn in a single shared gray color and the depth amplitude ratio (~2.1×)
reads visually as ~1.4× because the curve carries no color-coded segmentation.
The blue/red region overlays cannot do the work of the curve itself.

**Verdict: revise.** No BLOCKER physics violations; color convention (blue =
shallow, red = deep) is correctly applied throughout. Address C001, C002, C003
before manuscript use; C004-C007 can carry into a second pass.

**Pilot-pair context.** This arm is the design-only baseline of pair_002.
This critique is host-orchestrated (subscription tokens, zero external API)
and is report-only; it does not perform or claim blind A/B evaluation against
the vault arm.
