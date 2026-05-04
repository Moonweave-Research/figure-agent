# L3 Snippet Library

v0.3 vendored / curated TikZ snippets for paper-grade scientific figures.
Plan: `docs/architecture-v0.3-snippet-library.md`.

## Catalog

| Snippet | Macro | Status | Source / License |
|---|---|---|---|
| `polymer_chain.snippet.tex` | `\PolymerChain{x}{y}{n_monomers}{s_csv}` | A1 integrated WIP | hand-curated TikZ; snippet code MIT-style |
| `log_plot.snippet.tex` | (no macro — `paper loglog/.style` key in preamble) | A2 integrated WIP, 2026-05-04 | PGFPlots (LPPL 1.3) — TeX Live; style key MIT-style |
| `isometric_exploded.snippet.tex` | (no macro — raw composition) | V1 vendored 2026-05-04 (archived asset port) | own work, MIT-style; sourced from `[tikz-paper-workflow]/test_quality/isometric_exploded_slab.tex` |
| `layered_device_stack.snippet.tex` | (no macro — raw composition) | V2 vendored 2026-05-04 (archived asset port) | own work, MIT-style; sourced from `[tikz-paper-workflow]/test_quality/isometric_layered_device_stack.tex` |
| `process_3column.snippet.tex` | (no macro — raw composition) | V3 vendored 2026-05-05 (archived asset port) | own work, MIT-style; sourced from `[tikz-paper-workflow]/test_quality/fig2_cvs_c3_tradeoff.tex` |
| `molecular_cluster.snippet.tex` | (no macro — raw composition) | V4 vendored 2026-05-05 (Fig 1 panel a port) | own work, MIT-style; sourced from `[tikz-paper-workflow]/test_quality/fig1_hook_panel_a_v1.tex` |
| `band_with_traps.snippet.tex` | (no macro — raw composition) | V5 vendored 2026-05-05 (Fig 1 panel b port) | own work, MIT-style; sourced from `[tikz-paper-workflow]/test_quality/fig1_hook_panel_b_v1.tex` |
| `electret_actuation.snippet.tex` | (no macro — raw composition) | V6 vendored 2026-05-05 (Fig 1 panel c v2 port) | own work, MIT-style; sourced from `[tikz-paper-workflow]/test_quality/fig1_hook_panel_c_v2.tex` |
| `band_diagram.snippet.tex` | `\BandSnippet{...}` | A3 planned (deferred — see compass diagnosis) | hand-curated TikZ |
| `dos_lobes.snippet.tex` | `\DOSLobes{...}` | A4 planned (deferred — see compass diagnosis) | PGFPlots fillbetween |

Adjacent preamble primitive: `\PlotCallout` is not a snippet file, but it is
part of the A2 plot-authoring contract. Use it for plot labels that would
otherwise sit directly on traces, dashed guides, or arrows. Reference:
`docs/macros/plot-callout.md`.

## Usage contract (all snippets)

1. Consumer document loads `polymer-paper-preamble.sty` (which provides
   TikZ, `xstring`, palette colors, PGFPlots styles, and plot callout
   primitives).
2. Consumer `\input`s the snippet file in the preamble (before
   `\begin{document}`).
3. Consumer calls the macro inside any `tikzpicture` scope.
4. Caller may locally override snippet geometry only through documented macro
   arguments or local TikZ scopes; each snippet documents which keys matter.

## Acceptance gate (per `architecture-v0.3-snippet-library.md` §2.4)

A snippet ships only if:

- Compiles standalone with the production preamble + lualatex.
- Style Lock compatible (no clash with palette tokens).
- Parameter-clean: all variations exposed as macro args (no in-snippet
  hardcoded values for things callers will want to tune).
- Attribution + license recorded in this README.
- One smoke fixture in `examples/_snippet_smoke/<name>/` compiles.

## `log_plot.snippet.tex` — A2 (integrated WIP, 2026-05-04)

**Purpose:** PGFPlots-grounded log-log axes for paper-grade scientific
plotting. Replaces hand-rolled `\foreach`-tick + `\draw`-axis idioms that
had no functional meaning (a power-law was just a `\draw` line; a Debye
decay was a Bézier guess).

**No macro.** The snippet defines NO new control sequence. Authoring
convention: callers write raw PGFPlots inside a `loglogaxis` environment
that uses the `paper loglog/.style 2 args={W}{H}` style key declared in
`polymer-paper-preamble.sty`.

**Sizing contract:** `paper loglog={W}{H}` — W/H are the FULL axis box
including tick + axis labels. Data area is approximately `W-1.0cm` by
`H-0.6cm`. To fit a 2.75cm × 2.02cm fixture target, pass `{3.6cm}{2.6cm}`.

**Sampling caveat:** PGFPlots `samples=N` is linear sampling, which
clusters points at the high end of a log axis. For deterministic curve
placement use explicit `coordinates {...}` (log-spaced) over `\addplot
{f(x)}`. Spike G2 documented this confound.

**Smoke fixture:** `examples/_snippet_smoke/log_plot/log_plot_smoke.tex`

**First production consumer:** `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex` Row 1 (power-law + Debye).

## `polymer_chain.snippet.tex` — A1

**Purpose:** Sulfur-rich copolymer chain with monomer-resolved backbone.
Replaces hand-rolled `plot[smooth] coordinates` polymer "worm" curves
that fail the briefing requirement of "monomer-level texture, not
featureless waves" plus "sulfur atoms must be visually distinct (not just
labels)."

**Signature:** `\PolymerChain{anchor_x}{anchor_y}{monomer_count}{s_csv}`

- `anchor_x`, `anchor_y` — TikZ cm coordinates of the chain's leftmost
  backbone vertex.
- `monomer_count` — integer in 4..16. Each monomer step occupies ~0.42 cm
  horizontally; 11 monomers span ~4.2 cm, and 14 monomers span ~5.5 cm.
- `s_csv` — comma-separated 1-based monomer indices that carry a small amber
  sulfur side-group marker. Branches alternate above/below the backbone to
  avoid a comb-like chain. Density encoding:
  - sparse: indices spaced ~4 apart (e.g. `3,7,11`)
  - rich: contiguous indices (e.g. `6,7,8,9`)
  - mixed: combine sparse and rich (e.g. `2,6,7,8,9`)

**Smoke fixture:** `examples/_snippet_smoke/polymer_chain/polymer_chain_smoke.tex`

**First production consumer:** `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex` Row 3.

**Known limitation:** this is a manuscript schematic, not a chemically exact
structural formula. It preserves monomer texture and S-rich density cues while
avoiding full stereochemistry, valence detail, and atom-by-atom chemfig layout.

## `isometric_exploded.snippet.tex` — V1 (vendored 2026-05-04)

**Purpose:** 3D isometric exploded device cross-section — 4-layer slab stack
with leader-line callouts and dashed hidden-edge depth cues. Vendored from
the archived `[tikz-paper-workflow]/test_quality/isometric_exploded_slab.tex`
asset (origin 2026-04-26) under the macro-vs-snippet dichotomy: composition
stays as raw TikZ so the author can add/remove layers, retarget callouts,
and adjust explosion gaps without being forced into a fixed macro shape.

**No macro.** The snippet defines NO new control sequence. `\input` expands
the full `tikzpicture` inline. `\providecommand` exposes color and label
tokens (`\IsoExp{A..D}Color`, `\IsoExp{A..D}Label`, A=bottom..D=top, Roman
letters because TeX macro names may not contain digits) for the common case;
caller can override with `\def` before `\input`, or directly edit a copied
version of the snippet for non-default composition.

**Required preamble primitives** (from `polymer-paper-preamble.sty`):
- `iso basis` tikzset
- `\IsoBlock{w}{d}{h}{color}{hook}` macro (single-block primitive — safe to
  call repeatedly)
- `iso label`, `iso callout`, `iso hidden edge` styles
- palette tokens `cRed`, `cAmber`, `cTeal`, `cBlue`, `cGray`

**14-reference fit:** screenshot 8.27.58 a (3D isometric layered device,
Nature/Sci-grade), screenshot 8.32.10 A (MR array exploded view).

**Smoke fixture:** `examples/_snippet_smoke/isometric_exploded/isometric_exploded_smoke.tex`

**First production consumer:** TBD — vendored as v0.3 dogfood asset; promote
to a real fixture when a manuscript figure naturally uses the 4-layer
exploded composition.

## `layered_device_stack.snippet.tex` — V2 (vendored 2026-05-04)

**Purpose:** 3D isometric collapsed (non-exploded) device stack with a
trapped-charge region inside the dielectric layer. 4 layers
(bottom electrode / dielectric polymer / trapped-charge film /
top electrode), 5 charge dots in the dielectric, alternating-side leader
callouts, single hidden-edge depth cue, and a bold title at upper-left.
Vendored from archived `[tikz-paper-workflow]/test_quality/isometric_layered_device_stack.tex`.

**No macro.** `\providecommand` exposes color/label tokens
(`\IsoLDS{A..D}Color`, `\IsoLDS{A..D}Label`, `\IsoLDSTitle`). Charge-dot
positions, hidden-edge endpoints, and per-layer thicknesses are intentionally
raw TikZ — the author edits the snippet body directly to add/remove charge
dots, retarget callouts, or change layer count.

**Required preamble primitives** (from `polymer-paper-preamble.sty`):
- `iso basis` tikzset
- `\IsoBlock{w}{d}{h}{color}{hook}` macro
- `iso label`, `iso callout`, `iso hidden edge`, `iso charge` styles
- palette tokens `cAmber`, `cTeal`, `cBlue`, `cGray`

**14-reference fit:** screenshot 8.32.10 A (MR array layered cross-section,
Nature/Sci-grade), screenshot 8.27.58 a (3D isometric layered device).

**Smoke fixture:** `examples/_snippet_smoke/layered_device_stack/layered_device_stack_smoke.tex`

**First production consumer:** TBD — direct fit for sulfur polymer / actuator
device schematics where trapped-charge dynamics are the figure's argument.

## `process_3column.snippet.tex` — V3 (vendored 2026-05-05)

**Purpose:** Three-column process / mechanism comparison schematic. Each
column is a sealed dielectric cell (top/bottom electrodes + tinted polymer
matrix + bottom 3-line caption) with raw inner content (traps, charge
arrows, percolation routes) the author fills inline. Adjacent columns are
joined by left→right connector arrows, bookended by a top title bar and a
bottom summary caption. Vendored from archived
`[tikz-paper-workflow]/test_quality/fig2_cvs_c3_tradeoff.tex`.

**No macro.** `\providecommand` exposes the bookend strings (`\PTriTitle`,
`\PTriSummary`), per-column titles (`\PTri{A..C}Title`), three caption
lines per column (`\PTri{A..C}Cap{Head,Act,Note}`), and per-column accent
colors (`\PTri{A..C}Accent`, A=left ... C=right; Roman letters because TeX
macro names may not contain digits). Per-panel inner geometry — trap dot
positions, charge arrow paths, percolation routes — stays raw TikZ so the
author can replace one panel's inner content with a different mechanism or
extend the strip to 4+ columns by adding scopes and connector arrows.

**Required preamble primitives** (from `polymer-paper-preamble.sty`):
- palette tokens `cAmberSphere`, `cRed`, `cBrown`, `cBlue`, `cTeal`, `cGray`
- standard tikz + xcolor blend syntax (`!N!color`)

**14-reference fit:** screenshot 7.13.45 (CVS strip layout), screenshot
8.41.22 (process flow with mechanism panels).

**Smoke fixture:** `examples/_snippet_smoke/process_3column/process_3column_smoke.tex`

**First production consumer:** TBD — direct fit for "regime A → optimum →
regime C" mechanism explanations (trade-off plots, dose-response, defect
density, percolation thresholds).

## `molecular_cluster.snippet.tex` — V4 (vendored 2026-05-05)

**Purpose:** Sulfur polysulfide network hero panel for a Figure-1-style
hook. S8 ring at top (sc7_v7 idiom: bond lines drawn first, amber spheres
on top, white "S" labels) + reaction arrow with reagent annotations + two
parallel polymer-chain segments (short S_x bridge vs long S_y bridge)
between aromatic crosslinker hexagons + 3-line caption stack at bottom.
Vendored from archived `[tikz-paper-workflow]/test_quality/fig1_hook_panel_a_v1.tex`.

**No macro.** `\providecommand` exposes the title (`\McLTitle`), panel
label (`\McLLabel`), reagent strings (`\McLReagentMain`,
`\McLReagentAdd`), per-bridge labels and ranges (`\McL{Short,Long}{Label,Range}`),
and 3 caption lines (`\McLCap{Head,Mid,Note}`). S8 ring geometry, chain
spacing, hexagon positions, and per-monomer S sphere placements stay raw
TikZ — the author edits in place to vary monomer count, spacing, or
chemistry.

**Required preamble primitives** (from `polymer-paper-preamble.sty`):
- palette tokens `cAmber`, `cAmberSphere`, `cGray`, `cLGray`
- standard tikz with arrows.meta, `regular polygon` shape

**14-reference fit:** screenshot 5.34.12 (polysulfide network monomer chain),
screenshot 6.21.50 (S8 ring + bridge length comparison).

**Smoke fixture:** `examples/_snippet_smoke/molecular_cluster/molecular_cluster_smoke.tex`

**First production consumer:** TBD — direct fit for sulfur polymer paper
hook panel (Figure 1, panel a).

## `band_with_traps.snippet.tex` — V5 (vendored 2026-05-05)

**Purpose:** Charge trapping physics dual-panel for a Figure-1-style hook.
Band diagram (LUMO/HOMO + shallow + deep trap level rows with electrons
drawn as filled circles on selected sites) on the left, density-of-states
sub-panel (band-edge fills + narrow Gaussian DOS at E_S + broader Gaussian
at E_D) on the right. Dashed LUMO/HOMO horizontal guidelines bridge the
gap between the two sub-panels at matched energies. Vendored from archived
`[tikz-paper-workflow]/test_quality/fig1_hook_panel_b_v1.tex`.

**No macro.** `\providecommand` exposes the title (`\BwTTitle`), panel
label (`\BwTLabel`), band-edge labels (`\BwT{Lumo,Homo}Label`), trap-depth
labels (`\BwTShallow`, `\BwTDeep`), DOS species labels (`\BwT{Shallow,Deep}DOS`,
`\BwTGofE`, `\BwTEnergyLabel`), and 3 caption lines
(`\BwTCap{Head,Mid,Note}`). Trap-state tick positions, electron occupation
sites, and Gaussian DOS shape parameters stay raw TikZ — the author edits
to tune trap density, occupancy, or DOS width.

**Required preamble primitives** (from `polymer-paper-preamble.sty`):
- palette tokens `cBlue`, `cRed`, `cGray`
- standard tikz with arrows.meta, `plot smooth`

**14-reference fit:** screenshot 6.42.18 (band + DOS dual-panel),
screenshot 7.11.50 (trap-level diagram with electron occupancy).

**Smoke fixture:** `examples/_snippet_smoke/band_with_traps/band_with_traps_smoke.tex`

**First production consumer:** TBD — direct fit for sulfur polymer paper
hook panel (Figure 1, panel b). NOTE: the deferred A3 `band_diagram.snippet.tex`
will become a thinner primitive (band edges + traps only, no DOS sub-panel)
once that work resumes; this V5 vendor is the full hero composition.

## `electret_actuation.snippet.tex` — V6 (vendored 2026-05-05)

**Purpose:** Bidirectional Coulomb actuation panel for a Figure-1-style
hook. Two side-by-side sub-panels (Step 1: blue cantilever bending right
toward +V vertical electrode plate; Step 2: red cantilever bending left
away from -V plate) with: clamped-from-top wall hatching, GND vs floating
clamp annotation, amber electret coating + inner colored beam, seven
trapped negative charges along each beam, bending-angle θ_+ / θ_- arcs,
leftward E-field arrows, horizontal force arrow, electret callout, 3-line
caption. Vendored from archived `[tikz-paper-workflow]/test_quality/fig1_hook_panel_c_v2.tex`
(geometry-fixed v2: vertical electrode parallel to cantilever).

**No macro.** `\providecommand` exposes the title (`\EActTitle`), panel
label (`\EActLabel`), voltage strings (`\EAct{Pos,Neg}V`), per-step bottom
labels (`\EActStep{One,Two}`), electret callout text (`\EActElectretLbl`),
clamp annotations (`\EActGndLabel`, `\EActFloatLabel`), field-vector
label (`\EActFieldLabel`), and 3 caption lines (`\EActCap{Head,Mid,Note}`).
Cantilever spline control points, charge positions, E-field arrow y-coords,
electrode rectangle bounds, and bending-arc parameters stay raw TikZ —
the author edits to retune deflection, charge density, or sub-panel
separation.

**Required preamble primitives** (from `polymer-paper-preamble.sty`):
- palette tokens `cAmber`, `cBlue`, `cRed`, `cTeal`, `cGray`
- standard tikz with arrows.meta, dashed pattern

**14-reference fit:** screenshot 7.42.05 (cantilever sequence two-step
actuation), screenshot 8.18.33 (electret actuator schematic).

**Smoke fixture:** `examples/_snippet_smoke/electret_actuation/electret_actuation_smoke.tex`

**First production consumer:** TBD — direct fit for sulfur polymer paper
hook panel (Figure 1, panel c).
