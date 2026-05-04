---
schema: figure-agent.critique.v1
fixture: n3_trial_01_trap_depth
generated_at: 2026-05-04T06:29:07Z
verdict: ready
context: catalog-stability signal (NOT v0.3.0 ship-gate measurement — see docs/architecture-v0.3-snippet-library.md §5 addendum)
findings:
  - id: C001
    severity: MINOR
    category: hierarchy
    tex_lines: [86, 87, 88, 89, 90, 91, 96]
    observation: "Row 2 chain shows symbols only (n, τ_d, g(E_t)) without the reference image's sub-labels ('power-law exponent' / 'time emission line' / 'trap-depth distribution'). The governing equation is present but the chain reads as bare math without semantic anchoring. Briefing §2 names these roles verbatim."
    suggested_fix: "Add small italic gray sub-label nodes under each chain symbol at fontsize 4.6/5.6, anchored north, e.g. \\node[font=...] at (1.30, 4.60) {power-law exponent};. Use mathNode-derived style. Verify no collision with arrowFlow lines (offset y by ≥0.30)."
    status: open
  - id: C002
    severity: MINOR
    category: hierarchy
    tex_lines: [98, 99]
    observation: "Reference shows a small inline two-peak g(E_t) curve sketch under the chain label, providing visual hint that the math symbol resolves to a distribution shape. Build removed this in iter 1 (WARN-driven cleanup, comment lines 98-99). Loss is minor — equation + symbol carry the message — but the reference's pedagogical link from chain-symbol to right-panel side curves is weaker."
    suggested_fix: "Optional: re-introduce a 1.0×0.5 cm two-peak sketch at (5.40, 4.20)–(6.40, 4.70) using two BellCurve calls in side orientation, low contrast. Only if Row 2 has visual room without colliding with the chain (currently tight). Leave as-is if collision risk is high."
    status: open
  - id: C003
    severity: MINOR
    category: hierarchy
    tex_lines: [110, 111, 112, 113]
    observation: "Row 3 polymer backbone is a single zigzag chain with 5 S markers + 2 trap dots. Reference shows a denser stacked-chain motif suggesting polymer-network character. Briefing §4 explicitly allows 'simplify the polymer sketch ... rather than reproducing exact ... sulfur-site count', so author intent is honored, but visual weight in Row 3 is thinner than the other two rows."
    suggested_fix: "Optional: add a second zigzag chain at y=2.05 (offset above the current y=1.55 chain) with sparse S sites, matching golden_trap_depth_picture's multi-chain Row 3 pattern. Or increase WCamp to 0.20 for thicker single-chain visual."
    status: open
  - id: C004
    severity: NIT
    category: label_placement
    tex_lines: [148, 149, 150, 151, 152, 153]
    observation: "Convergence connector arrow tip (length=4.5pt, line 156-157) is visually small relative to the connector box's vertical mass. Reference connector arrow is more prominent."
    suggested_fix: "Increase Stealth length to 6pt, width to 4.5pt at line 156. Cosmetic only."
    status: open
  - id: C005
    severity: NIT
    category: style
    tex_lines: [172, 173, 174, 175, 176]
    observation: "BandDiagram trap dashes render correctly per macro spec (shallow at y=7.0/7.3/7.0, deep at 3.4/3.05). Reference shows electron occupancy dots (small filled circles) sitting ON the trap dashes to indicate trapped charge populations. BandDiagram macro does not emit these by default; briefing §6 invariants do not mandate them."
    suggested_fix: "Optional post-call \\node[electron] markers at (10.5, 7.30), (11.0, 7.00), (11.5, 6.70) for shallow and (10.8, 3.40), (11.4, 3.05) for deep. Define electron style in tikzpicture options block. Defer until briefing explicitly requests trap occupancy or until a dedicated [traps_filled] macro option exists."
    status: open
---

# Vision Critique — n3_trial_01_trap_depth

**Overall verdict: ready.** Zero BLOCKER, zero MAJOR. All physics invariants from briefing §6 are honored: CB above VB; shallow traps below CB and deep traps above VB; two trap populations paired with two g(E_t) side curves; power-law + Debye reference equations both visible in Row 1; governing relation `τ_d = τ_0 exp(E_t/k_B T)` present in Row 2; chemical + physical origin captions in Row 3; vertical Convergence connector links the three rows into the right panel with a labeled "Energy" axis. The five findings below are MINOR/NIT cosmetic deltas vs the reference image; none violate author intent as expressed in `briefing.md`.

This run is a **catalog-stability signal** for the snippet library, not a v0.3.0 ship-gate measurement. The fixture exercises four library macros (`\LogLogPlot`, `\WavyChain`, `\BandDiagram`, `\BellCurve`) in a different briefing context than `golden_trap_depth_picture`, with no compile or palette-lock violations, which is genuine evidence that the catalog generalizes across briefings. It does **not** test the v0.3 net-new deliverables `\PolymerChain` (chemfig wrapper) or `paper loglog/.style` (PGFPlots key); those remain validated only on golden, awaiting a real paper figure that pulls them in. See `docs/architecture-v0.3-snippet-library.md` §5 addendum.

## Per-finding discussion

**C001 (hierarchy / MINOR)** — Row 2 chain compresses three named concepts (`power-law exponent`, `time emission line`, `trap-depth distribution`) into bare symbols. The author's iter-2 comment (lines 82–84) cites collision pressure as the reason; this is a legitimate trade-off. If Row 2 vertical space allows a second pass, sub-labels would restore the semantic bridge from Row 1's empirical observation to Row 3's molecular cause. Skip if collision returns.

**C002 (hierarchy / MINOR)** — The inline two-peak sketch in the reference functions as a "preview" of the right-panel side curves. Removing it (iter 1) tightened the row but cost a pedagogical hand-off. Re-introducing is conditional on collision-free placement and may not be worth the layout cost.

**C003 (hierarchy / MINOR)** — Row 3 polymer chain is sparse relative to the other two rows' visual density. The author's choice to use a single `\WavyChain` is consistent with briefing §4's allowance for schematic simplification. A second stacked chain or a thicker amplitude would balance the row's weight without compromising the schematic intent.

**C004 (label_placement / NIT)** — Connector arrow tip is small. Pure cosmetic.

**C005 (style / NIT)** — Trap-level electron occupancy is shown in the reference but not in the build. Briefing §6 doesn't require it; this finding is logged for future macro work (potential `\BandDiagram[traps_filled=...]` option) rather than a current edit.

## Macro coverage signal

The fixture compiled cleanly with the current library. Specific evidence:

- `\LogLogPlot` (line 42): bbox-based log-log axes with explicit tick lists worked at this scale (3.4–6.9 × 7.85–10.25 cm); slope-line and dashed exponential overlay both render correctly above the axes.
- `\WavyChain` (line 111): zigzag style with five S sites + two trap markers parses correctly under the comma-split tail args fix.
- `\BandDiagram` (line 172): default form (no `[no_et]` / no `[traps=none]`) renders frame + CB/VB boxes + Energy axis + Et dashed line + three shallow / two deep TrapLevel dashes. The Gap 3+5 boolean keys added this session were not exercised here, by design — default-path regression check.
- `\BellCurve` (lines 203, 217): two side-oriented amber and violet bell curves render symmetrically and align vertically with the band-diagram trap regions.

No Style Lock violation, no BLOCKER collisions; 26 visual-clash WARNs (report-only) match expected density for this composition.
