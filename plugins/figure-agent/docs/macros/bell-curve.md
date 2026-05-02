# `\BellCurve` — bell-lobe shape primitive

**Signature:** `\BellCurve[<style keys>]{x1,y1,x2,y2,orientation}`

Symmetric bell-curve lobe inscribed in the bbox `(x1,y1)–(x2,y2)`. The macro provides only Bezier shape geometry; visual style (color, fill, line width) is the caller's responsibility, expressed via TikZ `\path` option keys.

## Positional arguments

| # | Name        | Notes                                           |
|---|-------------|-------------------------------------------------|
| 1 | `x1`        | bbox lower-left x (TikZ length, in figure units)|
| 2 | `y1`        | bbox lower-left y                               |
| 3 | `x2`        | bbox upper-right x                              |
| 4 | `y2`        | bbox upper-right y                              |
| 5 | `orientation` | `up` (lobe peak at top) or `side` (peak at right) |

## Optional style argument

The leading `[<style keys>]` accepts any TikZ `\path` option (`draw`, `fill`, `line width`, `dash pattern`, `opacity`, …). Keys append after the scope-level `bell curve/.style` defaults, so caller keys override defaults.

## Default style

```latex
\tikzset{
  bell curve/.style={
    draw=cGray,
    line width=0.5pt,
    %% `fill` key intentionally omitted — outline-only by default.
  },
}
```

A caller who omits `[<style keys>]` and never appends to the scope style gets a palette-neutral cGray outline with no fill. This matches TikZ ecosystem norms (`\node`, `\draw`, `\path` all default to neutral when caller omits style).

## Three call patterns

### (1) Default — gray outline, no fill

```latex
\BellCurve{13.95, 2.05, 15.20, 2.95, side}
```

### (2) Local override — one call differs

```latex
\BellCurve[draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt]
          {13.95, 2.05, 15.20, 2.95, side}
```

### (3) Figure-wide style via `\tikzset`

```latex
\tikzset{bell curve/.append style={draw=cAmber!80!black, fill=cAmber!18, line width=0.8pt}}
\BellCurve{13.95, 2.05, 15.20, 2.95, side}
\BellCurve{13.95, 0.65, 15.40, 1.85, side}  % inherits the appended style
```

`/.append style=` adds to the existing style without replacing the cGray default; use `/.style=` to fully replace.

## PDF operator stream note

Each call emits the `bell curve/.style` defaults as a graphics-state prologue (`0.27452 0.27452 0.27452 RG` for cGray, `0.49814 w` for 0.5 pt). When the caller's `[<style keys>]` overrides these (as in patterns (2) and (3)), the prologue is **dead code** — the next `RG`/`w` operator overwrites the state before any draw happens, so the default has no rendering impact. The PDF operator stream nonetheless contains both the defaults and the overrides. This is intrinsic to TikZ's eager pgfkeys evaluation; tests asserting visual equivalence (rasterized output, semantic path inspection) are unaffected, while strict byte-equal content-stream comparisons will see the dead-code prefix.

## Style Lock interaction

`scripts/lint_tex.py` enforces palette-only color tokens at the callsite. The `[<style keys>]` block is scanned the same as any other TikZ option: each `!`-separated color segment must be in the palette (`cAmber`, `cGray`, `cBlue`, …) or a TikZ builtin (`black`, `white`, …). Raw hex values and `\definecolor` are blocked. Numeric mix percentages (`!18`, `!80`) are not color names and are ignored by the scanner.

Mixed expressions like `cBlue!45!cRed!80!black` are accepted because each color-name segment (`cBlue`, `cRed`, `black`) is allowed; the result is left-to-right associative, equal to `((cBlue!45!cRed)!80!black)`.

## Migration note (legacy callers)

The pre-2026-05-02 macro signature was 6-positional with embedded color:

```latex
% OLD — no longer supported, raises \PackageError at compile time:
\BellCurve{x1,y1,x2,y2,COLOR,orientation}
```

Translate to the new signature by moving `COLOR` into the optional argument:

```latex
% NEW — same visual output:
\BellCurve[draw=COLOR!80!black, fill=COLOR!18, line width=0.8pt]{x1,y1,x2,y2,orientation}
```

The new parser treats a 6-positional call as orientation = `COLOR,orientation` (e.g., `cAmber, side`), which matches neither `up` nor `side`, raising `Invalid BellCurve orientation` and halting compile. There is no backward-compat shim by design.
