# BellCurve Macro Style Decoupling — Design Spec

**Date**: 2026-05-02
**Status**: brainstorm-complete, awaiting user review before implementation plan
**Pilot scope**: `\BellCurve` only. Other 7 flagship macros deferred to follow-up plans pending pilot validation.

## Goal

Refactor `polymer-paper-preamble.sty`'s `\BellCurve` macro so the macro provides only **shape geometry** (Bezier control points for the bell lobe). All visual style (color, fill, line width) becomes the **caller's** responsibility, expressed via TikZ-idiomatic option keys.

This pilot establishes the decoupling pattern that will extend to the remaining flagship macros (`\WavyChain`, `\BandDiagram`, `\TrapLevel`, `\LogLogPlot`, `\IsoBlock`, `\GradSlab`, `\IsoConeTip`) in subsequent plans, gated on pilot validation.

## Why

Current macro layer mixes shape and style. `\BellCurve{x1,y1,x2,y2,color,orientation}` hardcodes `fill=<color>!18, stroke=<color>!80!black, line width=0.8pt`. Caller cannot adjust line weight, opacity, or palette mixing without rewriting the macro. Dogfood signal (commit `910c3bc`, fixture `dogfood_power_law_trap_pipeline`) confirmed the shape primitive is the durable value; the embedded style is opinionated overhead. Decoupling restores caller flexibility while keeping the geometry algorithm (Bezier control point ratios) reusable.

The Style Lock layer (`lint_tex.py` palette enforcement) is unaffected: callers must still use palette-bound colors, no raw hex, no `\definecolor`. The lint policy operates at the **callsite**, so moving the style declaration from macro internals to callsites changes nothing about enforcement.

## Empirically validated TikZ pattern

Two TikZ semantic facts established by minimal compile tests during brainstorming (preserved as `/tmp/path_draw_fill_test.tex`, `/tmp/filldraw_test.tex`, `/tmp/separate_test.tex`, `/tmp/path_style_test.tex`):

1. **`\path[draw, fill]` with `fill=none` in scope renders BLACK fill** — TikZ `fill=none` is overridden by the explicit `fill` option key. Likewise `\filldraw` and `\fill` force-activate fill.
2. **`\path[<options>]` activates fill only when the `fill` key is present in the option list** — `\path[draw]` produces outline only because `fill` key is absent. A `tikzset`-defined style key inherits cleanly: `\tikzset{bell/.style={draw=red}}` then `\path[bell] (...)` is outline-only because the style omits `fill`.

**Implication for design**: Conservative defaults must omit the `fill` key entirely (not set it to `none`). The macro body uses `\path[<style key>, #1]` so caller options append after the scope default, which is canonical TikZ idiom.

## Architecture

### Macro definition pattern

```latex
%% Bell-curve shape primitive (style-decoupled).
%% Geometry: bbox (x1,y1)-(x2,y2), orientation in {up, side}.
%% Style: caller passes draw / fill / line width via [optional pgfkeys] or
%% via \tikzset{bell curve/.append style={...}} for figure-wide consistency.
\tikzset{
  bell curve/.style={
    draw=cGray,
    line width=0.5pt,
    % `fill` key intentionally omitted — outline-only default.
  },
}
\newcommand{\BellCurve}[2][]{%
  \BellCurve@parse[#1]#2\relax
}
\makeatletter
\def\BellCurve@parse[#1]#2,#3,#4,#5,#6\relax{%
  \pgfmathsetmacro{\BC@w}{(#4)-(#2)}%
  \pgfmathsetmacro{\BC@h}{(#5)-(#3)}%
  \edef\BC@orient{\zap@space#6 \@empty}%
  \def\BC@up{up}\def\BC@side{side}%
  \ifx\BC@orient\BC@up
    \path[bell curve, #1]
      (#2,#3)
      .. controls (#2+0.207*\BC@w,#3+0.043*\BC@h)
              and (#2+0.264*\BC@w,#3+0.986*\BC@h)
      .. (#2+0.494*\BC@w,#5)
      .. controls (#2+0.724*\BC@w,#5)
              and (#2+0.747*\BC@w,#3+0.058*\BC@h)
      .. (#4,#3) -- cycle;
  \else\ifx\BC@orient\BC@side
    \path[bell curve, #1]
      (#2,#3)
      .. controls (#2+0.043*\BC@w,#3+0.207*\BC@h)
              and (#2+0.986*\BC@w,#3+0.264*\BC@h)
      .. (#4,#3+0.494*\BC@h)
      .. controls (#4,#3+0.724*\BC@h)
              and (#2+0.058*\BC@w,#3+0.747*\BC@h)
      .. (#2,#5) -- cycle;
  \else
    \PackageError{polymer-paper-preamble}{Invalid BellCurve orientation `#6'}{Use up or side.}%
  \fi\fi
}
\makeatother
```

Key changes vs current macro:
- Color positional arg `#5` removed → 5 positional args (4 bbox + 1 orientation), down from 6.
- `\path[draw=#5!80!black, fill=#5!18, line width=0.8pt]` → `\path[bell curve, #1]`. Style now flows from scope key + caller's optional `[#1]`.
- `\begingroup ... \endgroup` removed. Path option scoping is sufficient; no global state to protect.

### Three call patterns supported simultaneously

```latex
% (1) Default — gray outline, no fill. Caller is lazy; figure shows the lobe shape.
\BellCurve{13.95, 2.05, 15.20, 2.95, side}

% (2) Local override — one call differs from siblings.
\BellCurve[draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt]
          {13.95, 2.05, 15.20, 2.95, side}

% (3) Figure-wide style — Nature Communications-style consistency.
\tikzset{bell curve/.append style={draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt}}
\BellCurve{13.95, 2.05, 15.20, 2.95, side}
\BellCurve{13.95, 0.65, 15.40, 1.85, side}  % inherits the appended style
```

### Migration strategy: bulk

All callsites of the old `\BellCurve{x1,y1,x2,y2,color,orientation}` signature are converted in the same commit as the macro change. No backward-compat shim. Migration preserves the visual output of each call by translating `,color,orientation` into `[draw=color!80!black, fill=color!18, line width=0.8pt]{...,orientation}`.

Affected fixtures (to verify at plan-creation time via `grep -rl 'BellCurve' examples/`):
- `examples/dogfood_power_law_trap_pipeline/dogfood_power_law_trap_pipeline.tex` — 2 calls (Panel 5 shallow + deep lobes)
- `examples/_macro_smoke/_macro_smoke.tex` — 2 calls (BellCurve up + side demonstration)
- Any other fixture surfaced by the grep at plan time

### Lint policy: unchanged

`scripts/lint_tex.py` continues to enforce palette-only colors, no raw hex, no `\definecolor`, no font overrides. The change moves color tokens from the macro body into callsites; the lint scanner already inspects callsites, so coverage is preserved without modification.

### Default style: conservative neutral

`bell curve/.style={draw=cGray, line width=0.5pt}` — outline-only with the palette's neutral gray. Rationale:
- Caller who forgets to specify style still gets a visible result (not invisible, not error).
- Default omits `fill` key entirely (TikZ semantics — see "Empirically validated TikZ pattern" §1), so default rendering is outline-only.
- Caller who wants fill must opt in explicitly via `[fill=...]` or scope-level `\tikzset{bell curve/.append style={fill=...}}`.

This matches TikZ ecosystem norms (`\node`, `\draw`, `\path` all default to neutral if caller omits style).

## Validation

### No-regression criterion: byte-identical PDF content stream

Per advisor recommendation, visual diff (PNG hash + perceptual threshold) is replaced by **content-stream byte equality**. Old `\BellCurve{x1,y1,x2,y2,cAmber,side}` and new `\BellCurve[draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt]{x1,y1,x2,y2,side}` MUST produce PDFs whose drawing instructions are byte-identical (after stripping metadata such as creation timestamps).

Implementation:
- Use `qpdf --qdf --object-streams=disable old.pdf old.qdf` to expand both PDFs.
- Compare content streams (objects of type `/Page` and their `/Contents` streams).
- Tolerance: zero byte difference in content streams. Metadata differences (timestamps, /ID) ignored.

If byte-identical fails, the migration introduced a behavior change. Investigate before merging.

### Tests

Add `tests/test_bell_curve_api.py` with three asserting tests:

1. **Default render** — minimal `.tex` with `\BellCurve{0,0,1,1,side}` compiles, produces PDF with one path object using cGray stroke.
2. **Local override** — `.tex` with `\BellCurve[draw=cAmber, fill=cAmber!18]{0,0,1,1,side}` compiles, produces path with cAmber stroke and fill.
3. **Scope override** — `.tex` with `\tikzset{bell curve/.append style={fill=cAmber!18}}` then `\BellCurve{0,0,1,1,side}` produces path with fill.
4. **Old signature rejected** — `.tex` with `\BellCurve{0,0,1,1,cAmber,side}` (6 positional, old style) MUST fail compile or render incorrectly. Document expected error.

Existing `pytest` suite (currently 219 passed) must remain green after migration.

### Documentation

Add `docs/macros/bell-curve.md`:
- Signature: `\BellCurve[<style keys>]{x1,y1,x2,y2,orientation}`
- Style keys: `draw`, `fill`, `line width` (any TikZ `\path` keys)
- Default style: `\tikzset{bell curve/.style={draw=cGray, line width=0.5pt}}`
- Three call patterns with worked examples
- Lint behavior: palette colors only; non-palette names and raw hex are blocked at compile by `lint_tex.py`
- Migration note for old `[x1,...,color,orientation]` callers

## Paired prerequisite (per advisor)

**Layer 5 export inconsistency must be diagnosed or scheduled with equal priority before promoting any new fixture to golden under this redesign.**

Background (from this session, commits `9e1b9f2`, `333248d`, `c808ee2`, `910c3bc`):
- `build/<name>.png` (pdftocairo direct PDF→PNG raster) and `examples/<name>/exports/<name>.png` (PDF→SVG via dvisvgm → PNG via rsvg-convert) produce visually different rasters from the same lualatex PDF.
- For `dogfood_power_law_trap_pipeline`, the macro fix in `910c3bc` removed the mystery cBlue circles from `build/PNG` but they persist in `exports/PNG`.
- SVG inspection confirms the cBlue circle paths are at correct Panel 4 coordinates (x=311, 325, 346 pt). No spurious circles in SVG.
- Implication: rsvg-convert (or dvisvgm SVG generation) is mis-rasterizing SVG paths or applying an incorrect coordinate transform when producing the exports/PNG. PDF and SVG agree; PNG path diverges.

Before any golden fixture promotes new BellCurve callsites:
1. Diagnose the rsvg-convert vs pdftocairo divergence (font glyph difference? viewBox parsing? object cache?).
2. Either fix the export pipeline so all four artifacts (PDF/SVG/TIFF/PNG) round-trip consistently, OR add a Layer 5 contract test that asserts content equivalence (perhaps SSIM ≥ threshold) between `build/<name>.png` and `exports/<name>.png`.

This is **paired**, not deferred. The macro redesign is necessary but insufficient for full kernel quality without Layer 5 consistency.

## Migration notes for composite macros (out of scope, future plans)

When this pilot pattern extends to `\BandDiagram`, `\IsoBlock`, and `\LogLogPlot` (composite macros that draw multiple sub-elements):

- These macros currently use `\begingroup ... \endgroup` with named TikZ coordinates (`isoA` through `isoH` in `\IsoBlock`). TikZ named coordinates are **global**, so `\begin{scope}` does not isolate them. The existing comment in `polymer-paper-preamble.sty` (`Sequential \IsoBlock calls overwrite them (fine). Do not nest \IsoBlock calls inside another's 5th-arg hook -- silent coordinate collisions will result.`) flags this.
- Decoupling style for these macros must preserve the named-coordinate semantics. The `\path[<style key>, #1]` pattern works for primitives like `\BellCurve` but a composite `\BandDiagram` may need per-sub-element style keys (`band frame/.style`, `bandbox/.style`, `trap level/.style`, etc.) so caller can target individual components.
- Empty-iteration macro bug (`\WavyChain` trap_csv issue from commit `910c3bc`) used a per-iteration `\edef + \ifx \WCempty` filter. Composite macros with CSV-style optional lists (e.g., `\BandDiagram` shallow_ys / deep_ys) should adopt the same pattern preemptively.

Each composite macro will get its own design spec following this pattern, after the `\BellCurve` pilot validates the approach.

## Out of scope (separate sprints)

- Other 7 flagship macros (`\WavyChain`, `\BandDiagram`, `\TrapLevel`, `\LogLogPlot`, `\IsoBlock`, `\GradSlab`, `\IsoConeTip`) — own design specs after pilot validation.
- Vision-in-the-loop audit slash command (`/fig_audit_vision`) — addresses single-pass plateau, separate Layer 3 enhancement.
- `\LogLogPlot` relative tick-label scaling — included in `\LogLogPlot`'s eventual decoupling spec.
- Per-iteration empty-filter audit across other CSV-arg macros — bundled with their respective decoupling specs.

## Implementation order (for downstream writing-plans)

1. Confirm current `\BellCurve` callsite count via `grep -rl 'BellCurve' examples/`.
2. Update `styles/polymer-paper-preamble.sty` with the new macro (replace existing definition).
3. Migrate each callsite to new signature, preserving original style via `[draw=color!80!black, fill=color!18, line width=0.8pt]`.
4. Add `tests/test_bell_curve_api.py` (4 assertions per "Tests" §).
5. Verify byte-identical PDF content streams for each migrated fixture (qpdf-based diff).
6. Run full `uv run pytest` — must be 219+ passes, no regressions.
7. Run `uv run ruff check .` — must be clean.
8. Add `docs/macros/bell-curve.md`.
9. Commit as single feature branch with message `refactor(macro): decouple style from BellCurve shape primitive`.
10. PR with REVIEW.md describing pilot validation outcome and the paired Layer 5 prerequisite.

## Self-review

- Placeholder scan: no TBD or TODO. Every section is concrete.
- Internal consistency: macro pattern, three call patterns, and migration translation all use the same `[draw=color!80!black, fill=color!18, line width=0.8pt]` mapping. `lint_tex.py` policy unchanged claim is consistent with callsite-only enforcement.
- Scope check: pilot is one macro, one .sty change, ≤ 5 callsite migrations, one new test file, one new doc. Single implementation plan is appropriate.
- Ambiguity check: empirical TikZ pattern (`\path[<style key>, #1]`) is verified, not speculative. Default `bell curve/.style` omits `fill` key intentionally (validated by `path_style_test.tex` Test A and Test B).
- Paired prerequisite (Layer 5) is explicit, not buried in "out of scope". A reviewer cannot miss it.
