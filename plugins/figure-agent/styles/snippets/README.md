# L3 Snippet Library

v0.3 vendored / curated TikZ snippets for paper-grade scientific figures.
Plan: `docs/architecture-v0.3-snippet-library.md`.

## Catalog

| Snippet | Macro | Status | Source / License |
|---|---|---|---|
| `polymer_chain.snippet.tex` | `\PolymerChain{x}{y}{n_monomers}{s_csv}` | A1 integrated WIP | chemfig (LPPL 1.3) — TeX Live; snippet code MIT-style |
| `log_plot.snippet.tex` | (no macro — `paper loglog/.style` key in preamble) | A2 integrated WIP, 2026-05-04 | PGFPlots (LPPL 1.3) — TeX Live; style key MIT-style |
| `band_diagram.snippet.tex` | `\BandSnippet{...}` | A3 planned | hand-curated TikZ |
| `dos_lobes.snippet.tex` | `\DOSLobes{...}` | A4 planned | PGFPlots fillbetween |

Adjacent preamble primitive: `\PlotCallout` is not a snippet file, but it is
part of the A2 plot-authoring contract. Use it for plot labels that would
otherwise sit directly on traces, dashed guides, or arrows. Reference:
`docs/macros/plot-callout.md`.

## Usage contract (all snippets)

1. Consumer document loads `polymer-paper-preamble.sty` (which provides
   `chemfig`, `xstring`, palette colors, default `\setchemfig` and
   `\printatom`).
2. Consumer `\input`s the snippet file in the preamble (before
   `\begin{document}`).
3. Consumer calls the macro inside any `tikzpicture` scope.
4. Caller may locally override `\setchemfig{...}` per figure if a
   non-default scale is needed; each snippet documents which keys matter.

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
  atom anchor.
- `monomer_count` — integer in 4..16. With default `atom sep=0.30cm`,
  each monomer occupies ~0.52 cm horizontally; 11 monomers span ~5.2 cm.
- `s_csv` — comma-separated 1-based monomer indices that carry a single
  `-S` branch hanging straight down. Density encoding:
  - sparse: indices spaced ~4 apart (e.g. `3,7,11`)
  - rich: contiguous indices (e.g. `6,7,8,9`)
  - mixed: combine sparse and rich (e.g. `2,6,7,8,9`)

**Smoke fixture:** `examples/_snippet_smoke/polymer_chain/polymer_chain_smoke.tex`

**First production consumer:** `examples/golden_trap_depth_picture/golden_trap_depth_picture.tex` Row 3.

**Known limitation:** chemfig auto-layout positions the leftmost atom
slightly below the requested `anchor_y` because `[:30]` zigzag rises
upward from the anchor. Drift is consistent (~0.1 cm) and predictable;
caller may adjust anchor by `-0.1` if precise centerline alignment with
external elements (labels, arrows) matters.
