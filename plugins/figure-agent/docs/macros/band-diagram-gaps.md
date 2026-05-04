# BandDiagram Macro API Gaps — Dogfood Findings (2026-05-03)

**Fixture**: `examples/fig3_trapping_concept/` (panel a: trap-free reference, panel b: band diagram with shallow/deep traps)

**Method**: Partial migration of panel (b) raw TikZ → `\BandDiagram[bandEt/.append style={draw=none}]{...}` signature.

**Result**: Compile ✓, collisions 0, visual clash 16 WARN (report-only). Visual model divergence revealed 5 design gaps in macro API.

---

## Gap 1: Visual Model Mismatch — Box vs Line

**Observation**: 
- Panel (a): hand-drawn CB/VB as colored lines (cBlue, cRed, 1.4pt, full-width across panel)
- Panel (b) macro-migrated: CB/VB as filled boxes (cLGray!30, draw=black, 1.55×0.48cm nodes with fixed labels)

**Impact**: Within same figure, two different visual encodings for "same concept" (energy band edges). cTeal rounded frame appears only on panel (b), asymmetrizing layout.

**Design question**: Is macro's box encoding (nodal, fixed label, frame boundary) the intended long-term standard for band diagrams across the manuscript? Or is line encoding (continuous, labeling flexible) preferred for conceptual diagrams?

---

## Gap 2: TrapLevel Extent — Short Dashes vs Full-Width Line

**Observation**:
- Original: trap marks as full-panel-width dashed line (trap electrons confined across entire depth)
- Macro: TrapLevel shallow/deep as short dashes flanking bandbox (trap electrons appear tethered to bandbox right edge only)

**Impact**: Visual metaphor shifts. In macro version, trapped electrons (the 4-point glyphs) appear to "float above" the dashes instead of "living inside" the trap potential well spanning panel width. Conceptual clarity loss.

**Design question**: Should TrapLevel dashes span the energy-axis range (full-width) or be decorative flanking marks?

---

## Gap 3: `$E_t$` Label Suppression — Line Suppressed, Text Persists

**Observation**:
- Attempted: `bandEt/.append style={draw=none}` to remove Et dashed line
- Result: line suppressed ✓, but macro's auto-generated "$E_t$" text node remains, positioned center-right of panel
- Panel already has hand-drawn label: "(escape negligible)" + "$kT \ll E_t$" below panel (b)

**Impact**: Duplicate label "$E_t$" appears orphaned, adding visual noise. No API key to suppress both line + text.

**Needed**: `[no_et]` boolean (or `[bandEt=none]` + auto-suppress text), or conditional text emission rule.

---

## Gap 4: BandBox Label Customization — Hard-Coded "CB"/"VB"

**Observation**:
- Macro: `\BandBox` nodes always render "CB" and "VB" (strings)
- Paper figure: requires "CB / LUMO" and "VB / HOMO" (suffix for spectral interpretation)
- Workaround: external labels (x=4.55 outside frame). Result: visual redundancy.

**Impact**: Caller must add external labels for domain-specific semantics, increasing boilerplate. Macro's fixed labels are appropriate for generic schematics, not domain-specific conceptual figures.

**Needed**: `[box_labels={CB / LUMO, VB / HOMO}]` or similar customization key.

---

## Gap 5: Trap-Free Panel Incompatibility

**Observation**:
- Panel (a): trap-free PDMS (reference case, no trapped charge)
- Macro: unconditional `\BandBox` + mandatory trap dashes (shallow_ys, deep_ys)
- Attempt to apply macro to panel (a): would inject false trap marks into reference panel

**Impact**: Macro design assumes "band diagram = trapping scenario." Trap-free band diagrams (energy-only, no trapping physics) cannot use macro. Mixed raw + macro styling required in same figure.

**Needed**: `[traps=none]` to suppress all trap glyphs/dashes, or new macro variant `\BandDiagramSimple{...}`.

---

## Recommendations for v0.3

**Do not fix gaps 1–5 from this single fixture.** (See `/decide` reasoning: premature generalization risk.)

**Next steps** (ordered by pressure):

1. **Gather fixture pressure**: Apply BandDiagram to real paper figures (e.g., fig3_trap_schematic_v97 panel d, if recounted for trap context). Which gaps cause actual migration pain? Priority ranking.

2. **Gap priority triage** (once multi-fixture data exists):
   - Gap 3 (`$E_t$` text suppression): Likely **High** — appears in any trap-free or Et-irrelevant scenario
   - Gap 2 (TrapLevel extent): **Medium-High** — affects visual clarity, but cosmetic
   - Gap 5 (trap-free incompatibility): **High** if reference-panel patterns appear in real figures, else **Low**
   - Gap 4 (box label customization): **Medium** — reduces boilerplate but non-blocking (external labels work)
   - Gap 1 (visual model mismatch): **Design question** — requires stakeholder (user) input; do not decide from single fixture

3. **Sketch specs** (on whiteboard or `docs/macros/band-diagram-v0.3-spec.md`, not code):
   - Gap 3 spec: `[no_et]` boolean, suppress `\BandEt` node definition + line + text
   - Gap 5 spec: `[traps=none]` suppresses trap dashes + labels, or create `\BandDiagramNoTraps` variant
   - Gap 2 spec: parameterize TrapLevel line extent (requires coordinate hint from layer 2.5, deferred)

---

## Appendix: Byte-Identity Implications

Original byte-exact fixture check (L5 export staleness) does not apply here — panel (b) raw → macro is intentional format change, not rebuild staleness. If panel (b) is future golden fixture, the "golden" baseline must be set post-macro (macro version becomes authoritative). Byte-check then detects unintended changes to the macro-emitted output, not user revisions.

**Action**: If panel (b) macro version is adopted for paper, regenerate golden fixture (`/fig_export fig3_trapping_concept --golden`). If rejected, keep raw.

---

## Status update (2026-05-04 EOD): Gap 3 + Gap 5 closed; Gap 1+2+4 remain open

**Closed**:
- **Gap 3** — `\BandDiagram[no_et]` boolean key shipped in `polymer-paper-preamble.sty`. Suppresses both the `bandEt` dashed line and the auto-generated `$E_t$` text node. Backward-compatible (default off).
- **Gap 5** — `\BandDiagram[traps=none]` choice key shipped. Suppresses both `\foreach \BDy in {#8}` (shallow) and `\foreach \BDy in {#9}` (deep) `\TrapLevel` calls. Backward-compatible.

**Verification**:
- `examples/_macro_smoke/_macro_smoke.tex` extended with three new cases: `[no_et]`, `[traps=none]`, `[no_et, traps=none]`. PNG inspection confirms each suppression is exact and additive.
- `golden_trap_depth_picture` recompiles unchanged (no regression — drift = 0.127 same as prior iteration, intentional box-internal title).
- `pytest`: 188/188 pass (no regression).

**Open**:
- **Gap 1** (line vs box visual model) — design question, blocked on stakeholder input. Do not promote from single fixture.
- **Gap 2** (TrapLevel extent — short dashes vs full-width) — requires Layer 2.5 coordinate hint, deferred.
- **Gap 4** (hard-coded "CB"/"VB" — needs `[box_labels=...]` for "CB / LUMO"-style suffixes) — non-blocking (external labels work as workaround).

**`fig3_trapping_concept` migration status**: NOT migrated to `\BandDiagram` macro. Closed Gap 3+5 alone is insufficient — fig3's panel (a)/(b) use line-style CB/VB + "CB / LUMO" suffix labels, which collide with Gap 1 (encoding) + Gap 4 (label hardcoding). Migration deferred until Gap 1+4 promote into scope under multi-fixture pressure.
