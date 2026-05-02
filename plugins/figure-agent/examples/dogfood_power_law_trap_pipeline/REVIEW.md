# Dogfood Review — dogfood_power_law_trap_pipeline

**Date**: 2026-05-02
**Branch**: main
**Reference**: `reference/dogfood_concept.png` (LLM-generated 5-panel ISPD pipeline schematic)
**Purpose**: First post-augmentation (commit `c808ee2`) dogfood of the semantic-first authoring workflow on a fresh, complex fixture intentionally separated from existing trap-domain fixtures.

## Workflow validation

### Semantic-first 4-step authoring (prompts §5b contract)

All four steps fired as specified in the augmented prompt:

1. **Look at reference PNG first**: 5 panels decomposed into discrete semantic units (log-log plot, math symbols, polymer chains, band diagram, distribution lobes) before touching any coordinate.
2. **Macro mapping**: every panel mapped to existing `polymer-paper-preamble` macros — `\LogLogPlot`, `\WavyChain`, `\BandBox`/`bandFrame` (decomposed for full Conduction Band / Valence Band labels), `\TrapLevel` with `trapShallow`/`trapDeep` styles, `\BellCurve` with `side` orientation. Zero raw SVG path output, zero auto-traced clouds.
3. **Coordinate hints used for placement only**: OCR-derived panel title positions (px → cm via 1833 px / 16 cm = 115 px/cm) used to anchor panel x-ranges. `coordinate_hints.yaml` was evidence, not source.
4. **Semantic TikZ**: macro-driven, no path dumps. `lint_tex.py` BLOCKER passed on first compile.

Briefing-only fallback was not exercised (this fixture has a reference image).

## Iteration cost

| Iter | Wall time | Lines changed | Compile gates | Visual issues remaining |
|---|---|---|---|---|
| 1 — scaffold + first .tex | ~10 min | 200 (initial) | 5/5 PASS, 28 clash report | 4 (ylabel typo, Panel 1 font, "deep ⋯", Panel 3 callout) |
| 2 — 4 fixes | ~3 min | 8 lines | 5/5 PASS, 29 clash | 2 fixed + 1 new (Panel 2 overlap) + 1 mystery |
| 3 — callout x correction | ~2 min | 4 lines | 5/5 PASS, 32 clash | 1 fixed + mystery |
| 4 — mystery debug | ~10 min | 5 macro fix attempts + per-iteration filter | 5/5 PASS | **mystery resolved** |
| **Total** | **~25 min** | **~220 lines** | All gates green | publication-ready (1 macro-design backlog) |

## Macro bug discovered + fix

### Symptom
Three large hollow cBlue circles persistently rendered in Panel 1 plot region across iterations 1–3. Visible in both PDF and rasterized PNG (not a viewer artifact).

### Root cause isolation (binary search)
- Commenting `\LogLogPlot` → circles persist (not LogLogPlot)
- Commenting `\TrapLevel` calls → circles persist (not TrapLevel coordinate leak)
- Commenting all `\WavyChain` calls → **circles disappear** (\WavyChain is the source)

### Mechanism
`\WavyChainDraw#1,#2,#3,#4,#5,#6\relax` matches the macro arg with `#6 = " {}"` (space + empty group). The original code:

```latex
\edef\WCTlist{\zap@space#6 \@empty}%
\ifx\WCTlist\WCempty\else
  \foreach \WCtx in {#6} { ... circle node at (\WCtx, ...) ... }
\fi
```

`\zap@space` does not normalize bare empty groups to true empty, so the `\ifx` comparison falls into `\else`. `\foreach` then runs one iteration with `\WCtx` bound to an empty token. The coordinate `(\WCtx, #3+\WCamp+0.10)` parses as `(0, #3+0.27)`, emitting a stray cBlue circle at chain-row x=0 (Panel 1 region). The y values (3.12, 2.12, 1.12) match the three observed mystery-circle positions.

### Failed fix attempts (documented for future reference)
1. `\detokenize{#6}` outer check → `{}` becomes char tokens `"{"` + `"}"`, never empty
2. Two-`\detokenize` reference comparison → leading-space mismatch
3. `etoolbox \ifblank{#6}` → leading space + group still not normalized to blank

### Working fix (per-iteration filter)
Move the empty check inside the `\foreach` body, where `\WCtx` is a single bound token regardless of outer arg shape:

```latex
\foreach \WCtx in {#6} {%
  \edef\WCtxcheck{\WCtx}%
  \ifx\WCtxcheck\WCempty\else
    \node[circle, ...] at (\WCtx,...) {};
  \fi
}%
```

### Regression verification
- `_macro_smoke` (other `\WavyChain` user, also passes `{}` for trap_csv on the sin row) compiles cleanly: "WavyChain sin (no markers)" row shows zero spurious circles, "WavyChain zigzag w/ S+trap" row still draws normal trap markers from non-empty trap_csv.
- Full pytest suite: 219 passed, ruff clean.
- Other fixtures using `polymer-paper-preamble.sty` are unaffected because the change only adds a per-iteration empty filter; non-empty `\WCtx` paths through unchanged.

## Visual quality assessment

| Panel | State | Notes |
|---|---|---|
| 1 Experimental trace | Acceptable | tick label font biased large vs plot bbox — `\LogLogPlot` macro limitation (absolute font size, no relative scaling) |
| 2 Mathematical interpretation | Clean | Debye inset readable at scale=0.55 |
| 3 Chemical / physical origin | Clean | callouts confined to Panel 3 x-range after iter 3 |
| 4 Trap-depth inference | Clean | full Conduction Band / Valence Band labels fit in 2.50 cm bandbox at 6 pt |
| 5 Trap distribution (ISPD) | Cleanest panel | shallow lobe slightly smaller per §6 invariant |
| Inter-panel arrows | Clean | gray straight 1→2→3→4, teal curved 4→5 (3-arrow CB/mid/VB → shallow/mid/deep) |

## Deferred to v0.2 backlog

- `\LogLogPlot` lacks a relative tick-label scaling option; tick text reads disproportionately large when bbox is small. Fix candidate: optional 8th arg `tickScale` or auto-scale by bbox area.
- `\WavyChain` and `\BandDiagram` argument signatures could benefit from optional/keyword parameters to avoid the empty-group dance entirely (e.g., LaTeX3 `xparse` or pgfkeys-style options).
- Per-iteration empty filter pattern should be audited across other macros that take CSV-style optional lists (likely `\BandDiagram` shallow_ys / deep_ys — currently passed via brace-wrap in the same way).

## Dogfood signal summary

- **Workflow contract works**: semantic-first 4-step ordering produced a coherent first-pass figure with all macros correctly mapped and no path dumps. The augmented prompt §5b (commit `333248d` + `c808ee2`) delivered its promise on a fresh complex fixture.
- **Quality kernel detected real macro bug**: figure-agent's gates passed all five layers (lint, lualatex, collision/clash, drift skip, plugin validate), but visual review surfaced a flagship macro defect that had likely lived in `polymer-paper-preamble.sty` undetected. The dogfood loop — author → compile → look → diagnose — is the kernel's actual ROI.
- **Iteration cost characterization**: ~25 min from blank fixture to publication-ready, including a 10-min macro-debug detour. Reviewer-round patches are O(1-line edits), confirming the macro-driven authoring style preserves patch surface.
- **Plateau confirmed**: tick-label font and callout placement decisions both required render-time vision feedback the LLM cannot self-supply. v0.2 macro improvements + future vision-in-the-loop tooling remain the path to single-pass results.
