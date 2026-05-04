# Briefing - golden_trap_depth_picture

## 1. What does this figure show? (1-2 sentences)

Converged trap-depth interpretation for sulfur-rich polymer charge dynamics.
The figure links experiment, mathematical interpretation, and molecular origin
to a unified trap-depth picture.

## 2. Domain vocabulary (terms, materials, mechanisms)

- Experiment: discharge current, log I, log t, Debye reference.
- Mathematical interpretation: power-law exponent n, Debye tau_d, trap-depth distribution g(E_t).
- Molecular origin: S-rich segments, chemical origin, physical origin, localized traps.
- Energy diagram: CB, VB, E_t, shallow traps, deep traps, g(E_t).

## 3. Composition intent (panel layout, flow direction)

Wide landscape schematic with three left-side narrative rows and one large right-side
converged trap-depth picture. Thin gray horizontal separators divide the rows.
Gray arrows move evidence from the left rows into a teal brace and right-side
energy/distribution diagram.

## 4. Normalize / avoid literal overfit

This is a golden reference reproduction. Do not normalize away labels, row
structure, curve shapes, colors, or sulfur/trap markers.

## 5. Style notes (optional)

White background, manuscript-readable sans-serif labels, thin gray separators
and arrows, blue power-law/electron marks, orange shallow traps, purple deep
traps, and teal convergence title/brace.

## 6. Physics invariants (preserved verbatim in prompt)

- CB is above VB.
- E_t lies between CB and VB.
- Shallow traps appear closer to CB; deep traps appear closer to VB.
- g(E_t) has two lobes: shallow and deep.
- The right-side diagram is the convergence endpoint for experiment,
  mathematical interpretation, and molecular origin.

## 7. Author intent — semantic constraints (for vision critique grounding)

### Must depict
- **Row 3 polymer chain**: three parallel S-rich polymer chains, each with
  monomer-level texture rather than featureless waves. The production fixture
  uses 11 chemfig monomers per chain to preserve layout fit against the
  reference target.
- **Row 2 evidence narrative**: chain of causal arrows (Σ∫ → I(t)∝t^-n → n value → Debye ref → g(E_t)).
  Each step must have an incoming arrow from Row 1 evidence; the chain must flow left→right.
- **Row 3 molecular origin**: sulfur atoms or disulfide bonds must be visually distinct (not just labels).
  "localized traps" label must be physically near the trap markers.
- **Right-side lobes**: shallow lobe peak must be ≈2×–3× taller than deep lobe (visual proportionality).
  Lobe peaks must align with cluster mean from g(E_t) PDF, not arbitrary positions.

### Must avoid
- Featureless waves, plain sine curves, or "gelatinous blob" polymer chains without segment detail.
- Floating arrows not anchored to teal brace or evidence box.
- Energy axis that doesn't span CB→VB range (E_t must be clearly interior).
- Asymmetric continuation markers (if shallow has ellipsis, deep must also; if only deep marked, deep must be visually incomplete).
- Redundant g(E_t) labels (label the distribution once per row, not twice in same plot).

### Semantic assertions (auto-verifiable by critique)
- Trap depth axis (E_t direction) is vertical and monotonic.
- Shallow cluster peaks are closer to CB than deep cluster peaks.
- Both lobes are visible and distinct (not merged or fused).
- Row 1 evidence box title is *outside* the box (not centered within).

### Snippets used (v0.3 L3 library)
- **Row 1 log-log plots** (A2 integrated WIP, 2026-05-04): PGFPlots `loglogaxis` with the `paper loglog` style key declared in `polymer-paper-preamble.sty`. Power-law plot uses log-spaced explicit coordinates of c·t^{-0.7}; Debye reference plot uses log-spaced explicit coordinates of exp(-t/30). No wrapper macro — caller writes raw PGFPlots syntax inside the style key. Convention documented in `styles/snippets/log_plot.snippet.tex` (docs-only, no executable code).
- **Row 3 polymer chains** (A1 integrated WIP): `styles/snippets/polymer_chain.snippet.tex` — chemfig-based.
  3 calls of `\PolymerChain{x}{y}{11}{s_csv}`. The production fixture uses
  11 chemfig monomers; the briefing intent ("monomer-level texture, not
  featureless waves") is satisfied because each monomer is individually
  visible as a backbone vertex with explicit C-C bonds. S branches are
  single -S only (not polysulfide) and hang straight down for non-overlapping geometry;
  density encoding is by branch frequency (sparse=every 3-4 monomers, rich=contiguous
  4-5 monomers inside the dashed highlight box at x=4.20-5.85).
