# Macro Audit — Phase 1.1 (Roadmap Layer 3-6)

**Date**: 2026-05-01. **Scope**: 3 active `.tex` fixtures.
**Inputs**:

- `examples/fig3_n2_evidence/fig3_n2_evidence.tex` (365 LOC)
- `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex` (196 LOC)
- `examples/fig3_trap_schematic_v97/fig3_trap_schematic_v97.tex` (369 LOC)

Variant authoring artifacts (`*.codex_*.tex`, `*.claude_*.tex`) are excluded; they are LLM scratch and not part of the published baseline.

## Method

1. Grep raw TikZ idioms (`plot[smooth]`, `.. controls`, `foreach .* lab`, `ellipse [x radius`, `rectangle`, axis-arrow draws) per file.
2. Bucket each hit into one of the 8 named candidate macros from the roadmap; raw regex categories overlap (a single `.. controls` Bezier may belong to a panel arc, a bell lobe, or a Debye curve), so attribution by intent is required to avoid double-counting.
3. Two ranking columns: **occurrence count** (uses) and **LOC_saved ≈ count × LOC_per_use**. Step 1.2 implementation order should follow LOC_saved, not raw count — `\PowerLawLine` is trivial 1-LOC and should not displace `\BandDiagram` (~30 LOC/use) on the top-5 list.

## Existing macros (preamble + local)

| Macro | Defined in | Calls | Notes |
|---|---|---|---|
| `\TrapLevel{x}{y}{style}` | `polymer-paper-preamble.sty` | 8 (golden only) | n2 inlines the equivalent draw without the macro; trap_v97 uses a simpler `trapSeg` style without the electron marker. Inconsistency = promotion signal. |
| `\IsoBlock`, `\IsoCharge`, `\GradSlab`, `\IsoConeTip` | preamble | 0 in audit set | Used by other (non-paper) fixtures; out of scope here. |
| `\BandBox{x}{y}{label}` | **local: golden** | 2 calls + 1 def | Same pattern is inlined twice in n2 (CB/VB rectangles, lines 286–295). Empirical promote-to-preamble signal. |
| `\SmallLobe{x}{y}{color}{label}` | **local: golden** | 2 calls + 1 def | Same Bezier lobe is inlined twice in n2 panel 2 (lines 100–120, fill+draw twice). Empirical promote signal. |
| `\WavyChain{...}` | local: golden | 0 calls + 1 def | Defined but never invoked in golden — the chains use raw `plot[smooth] coordinates`. Stale stub. |

The two **already-duplicated-locally** macros (`\BandBox`, `\SmallLobe`) are the highest-confidence promotion candidates: the author needed them, defined them in one fixture, and re-inlined the same pattern in another. They become subprimitives of the larger `\BandDiagram` / `\BellCurve` candidates below.

## Candidate macros — ranked

`LOC/use` is rough (counted by inspecting one representative call site, including helper draws like `fill` + `draw` pairs).

| # | Candidate | Uses | LOC/use | LOC saved | Notes |
|---|---|---|---|---|---|
| 1 | `\BandDiagram{...}` | 3 | ~30 | **~90** | golden right zone, n2 right zone, trap_v97 panel d (mini variant). Largest per-use abstraction. |
| 2 | `\LogLogPlot{x0,y0,w,h, x_decades, y_decades, xlabel, ylabel}` | 4 | ~22 | **~88** | golden ×2 (panel 1 + Debye reference), n2 ×2 (panel 1 + panel 3). trap_v97's panels b/c/d use linear axes without log tick foreach — different macro tier. |
| 3 | `\BellCurve{x1,y1,x2,y2, color, orientation}` where orientation ∈ {up, side} | ~11 | ~5 | **~55** | Already partial as local `\SmallLobe`; orientation arg covers upright (panel-2 lobes) vs sideways (band-diagram g(Et)). Standalone-vs-paired (shallow/deep twin) is handled by repeated calls, not a separate flag. |
| 4 | `\WavyChain{x1,x2,y, style, S_x_list, trap_x_list}` where style ∈ {zigzag, sin} | ~10 | ~5 | **~50** | golden ×3 + n2 ×3 use zigzag-with-S; trap_v97 panel e ×3 uses sin (`0.40*sin(\x*540+phase)`); trap_v97 panel d ×1 is a manual `--` zigzag. The S-marker foreach is the bulk of the LOC. |
| 5 | `\TrapLevel{x}{y}{role}` (extend, do not rename to `\TrapDash`) | ~18 | ~3 inline → 1 via macro | **~36** | golden 8 (already via macro), n2 6 (currently inline), trap_v97 ~4 (no electron variant). See "Naming decision" below. |
| 6 | `\PowerLawLine{x1,y1,x2,y2, color}` | 6 | 1 | ~6 | Trivial — `\draw[color, line width=0.92pt] (x1,y1)--(x2,y2);`. Low ROI; defer or skip. |
| 7 | `\PanelArc{cx,cy,rx,ry,color}` | 3 (+1 dashed motif) | ~2 | ~8 | n2 only. Trivial wrapper around `ellipse [x radius=, y radius=]`. Modest savings but consistent style enforcement is the real win. |
| 8 | `\PanelArrow{from,to,color,dot}` | 3 | ~3 | ~9 | n2 only. Stealth-tipped curve with filled-circle endpoint. Low count, but the inline form is error-prone (separate `\draw` + `\fill` for the dot). |

### Top 5 for Step 1.2 (by LOC_saved)

1. **`\BandDiagram`** — 90 LOC saved. Highest per-use abstraction. Subsumes `\BandBox` (CB/VB rectangle) as a subprimitive.
2. **`\LogLogPlot`** — 88 LOC saved. Subsumes `\TickLabelsX/Y` foreach blocks.
3. **`\BellCurve`** — 55 LOC saved. Subsumes existing local `\SmallLobe`. Needs orientation arg.
4. **`\WavyChain`** — 50 LOC saved. Subsumes `\SAtom` (sulfur dot + label) foreach idiom.
5. **`\TrapLevel` extension** — 36 LOC saved. Re-export from preamble (already there) and migrate n2 inline copies; add optional `no-electron` variant for trap_v97-style usage.

`\PowerLawLine`, `\PanelArc`, `\PanelArrow` are flagged for **Phase 1.2 second tier** — implement only if Phase 1.4 validation shows authoring still needs them.

## Subprimitives (do not promote to top-level)

These appear inside the top 5 but should not be standalone macros:

- `\TickLabelsX{x0, x1, y, list}` / `\TickLabelsY{x, y0, y1, list}` — inside `\LogLogPlot`. 8 foreach blocks total in audit set.
- `\AxisArrow{x0,y0,x1,y1}` — inside `\LogLogPlot` and `\BandDiagram`. 25 raw axis-arrow draws across files, but their layout is always relative to a parent plot frame, not figure canvas. Independent macro would just hardcode the Stealth dimensions, no real abstraction win.
- `\SAtom{x,y}` — inside `\WavyChain`. 30+ S-marker foreach iterations across files; signature is too thin to be a separate top-level macro.
- `\BandBox{x,y,label}` — already locally defined in golden; promote into `\BandDiagram` as the CB/VB block primitive.

Keeping the candidate set to **8 (5 active + 3 deferred)** protects Step 1.2's scope and prevents preamble bloat.

## Naming decision: `\TrapLevel` vs `\TrapDash`

Roadmap proposes `\TrapDash{x,y,role}` (comma syntax, role-keyed). Current preamble has `\TrapLevel{x}{y}{line-style}` (brace-3-arg, style-keyed). 8 call sites in golden use the existing form.

**Decision: keep `\TrapLevel{x}{y}{role}`; do not rename.** Reasons:

- 8 existing call sites all pass `trapShallow` / `trapDeep` as the third argument — these are already TikZ styles defined in the figure scope. The "role" idea is satisfied if we standardize those style names in the preamble (currently they live in per-figure `tikzpicture` style blocks). No call-site rewrite needed.
- The roadmap's `{role}` slot is sugar for the existing `{line-style}` parameter. Dropping `\TrapDash` from the new-macros list saves a deprecation cycle.
- A `*` variant `\TrapLevel*{x}{y}{role}` (or a 4th boolean arg) handles the trap_v97 "no electron" case.

**Action for Step 1.2**: lift the `trapShallow` / `trapDeep` styles from per-fixture scope into `polymer-paper-preamble.sty`, then migrate n2's inline trap dashes to use `\TrapLevel`. Add a no-electron variant only if trap_v97 dogfooding needs it.

## Patterns observed but out of scope for Phase 1

- **Battery / current-meter symbols** (trap_v97 panel a, lines 86–102) — single occurrence, not abstractable yet. Wait for second instance before macro-izing.
- **Halo fill clusters** (trap_v97 panel e, `\fill[haloFill]`) — 3 instances within one panel; `haloFill` is already a tikz style. Style-only is sufficient.
- **Sin-wave chain (trap_v97 panel e)** — 3 chains with phase-shifted `0.40*sin(\x*540+phase)` plots. Different aesthetic from the golden/n2 zigzag-with-S-atoms style; treat as a `\WavyChain` *style variant*, not a separate macro.

## Verification (post-audit, 2026-05-01)

### V1 — Measured LOC/use; ranking flips

Block-level `wc -l` on representative call sites:

| Candidate | Site | Block LOC | Replaceable LOC | Note |
|---|---|---|---|---|
| `\LogLogPlot` | golden panel 1 | 22 | 21 | Pure log-log block; entire region collapses to one macro call. |
| `\LogLogPlot` | golden Debye reference | 25 | 16 | Block also contains rounded border + Debye curve + caption (non-LogLogPlot). |
| `\LogLogPlot` | n2 panel 1 | 26 | 25 | Pure. |
| `\LogLogPlot` | n2 panel 3 | 20 | 19 | Pure. |
| **LogLogPlot total** |  |  | **~81** |  |
| `\BandDiagram` | golden right zone | 33 | ~22 | Skeleton + trap dashes; gaussians stay as separate `\BellCurve` calls. |
| `\BandDiagram` | n2 right zone | 42 | ~24 | Same. CB/VB rectangles + Et axis + 2 foreach trap blocks. |
| `\BandDiagram` | trap_v97 panel d | 21 | ~10 | Different style (line bands, single trap, no g(Et)); needs variant or stays inline. |
| **BandDiagram total** |  |  | **~46–56** |  |

**Ranking flip**: `\LogLogPlot` (~81 LOC saved) > `\BandDiagram` (~46–56 LOC saved). The eyeballed table above had them at 88 vs 90 — measurement re-orders them. Step 1.2 should implement `\LogLogPlot` first.

### V2 — Trap style lift (preamble promotion of `trapShallow` / `trapDeep`)

Cross-fixture audit of `.style` definitions:

- **golden**: defines `trapShallow={cAmber, line width=0.72pt}`, `trapDeep={cBlue!45!cRed, line width=0.72pt}`, `electron={circle, fill=cBlue!45, draw=cBlue!75!black, minimum size=1.35mm, line width=0.34pt}` (lines 18–20).
- **n2**: does **not** define `trapShallow` / `trapDeep` / `electron` styles. Trap dashes are inlined as `\draw[cAmber, line width=0.72pt] ...` (line 311) and `\draw[cBlue!45!cRed, line width=0.72pt] ...` (line 319). Colors and widths are **exact match** to golden's style def — promotion is a true no-op for line geometry.
- **trap_v97**: defines `electron`, `trapLine` (dashed, line-width-only), `trapSeg` (solid amber). **No name collision** with `trapShallow` / `trapDeep`. Different semantics; no migration target.

**Caveat — electron node geometry drift** (not flagged in audit body):

- golden `\TrapLevel` macro hardcodes electron geometry: `fill=cBlue!45, draw=cBlue!75!black, minimum size=1.35mm, line width=0.34pt`.
- n2 inline electrons: `fill=cBlue!50, draw=cBlue!80!black, minimum size=1.4mm, line width=0.35pt`. Slightly different fill saturation and 0.05 mm larger size.
- trap_v97 electrons: `minimum size=2.4mm` (panel a), `1.8mm` (panel e). Markedly larger.

Migrating n2 inline trap dashes to `\TrapLevel` is **not a pixel-perfect no-op** — electrons will re-render with golden geometry. Visually near-identical but should be called out as a Style Lock normalisation, not silent. trap_v97 cannot adopt `\TrapLevel` without an electron-size parameter or a `*`-variant; defer until Phase 2 dogfooding signals a need.

**Decision for Step 1.2**:

- Lift `trapShallow` and `trapDeep` to preamble — safe, no collision, exact color/width match.
- Migrate n2 inline trap blocks to `\TrapLevel`, accepting electron-geometry homogenisation onto golden's spec. Run drift gate post-migration to confirm 12/12 maintained.
- Do **not** migrate trap_v97 in Step 1.2; revisit if Phase 2 needs it.

## Cross-references

- Roadmap source: `docs/roadmap-layer3-6.md` Phase 1.1.
- Active preamble: `styles/polymer-paper-preamble.sty`.
- Layer 2.5 plateau commit: `e611f1e`.
- Step 1.2 entry: implement top-5 macros in preamble; register via `_RE_FLAGSHIP_NEWCOMMAND` extraction in `scripts/llm_author_prompt.py`. **Implementation order**: `\LogLogPlot` → `\BandDiagram` → `\BellCurve` → `\WavyChain` → `\TrapLevel` extension (per V1 ranking).
