# `\BandDiagram` Macro Reference

**Signature**: `\BandDiagram[<style keys>]{x1,y1,x2,y2,cb_y,vb_y,et_x,shallow_ys,deep_ys}`

Positional CSV args (brace-wrapped at call site, commas inside):
- `x1,y1,x2,y2` — bounding box (rectangle frame corners).
- `cb_y` — y-coordinate of the conduction band (CB) `BandBox`.
- `vb_y` — y-coordinate of the valence band (VB) `BandBox`.
- `et_x` — x-coordinate of the dashed Et reference line.
- `shallow_ys` — list of y-values for shallow trap dashes (use `{}` for none).
- `deep_ys` — list of y-values for deep trap dashes (use `{}` for none).

Optional pgfkeys arg (`[#1]`):
- TikZ `\path` keys applied via the `band diagram` outer style key after the figure-wide defaults.
- Use `.append style` form to patch a single sub-style for this call only:
  `\BandDiagram[bandFrame/.append style={draw=cAmber, line width=0.8pt}]{...}`.

## Sub-style keys

The macro draws into 5 named sub-styles defined in `polymer-paper-preamble.sty`. Defaults preserve the figure-agent palette and convention; callers override via `.append style` on any of these keys (either at scope head or per call):

| Key | Default | Role |
|---|---|---|
| `bandFrame` | `cTeal, line width=1.2pt, rounded corners=4pt` | rectangle around the diagram (decoration) |
| `bandbox` | `draw=black, line width=0.45pt, fill=cLGray!30, ...` | CB / VB filled blocks (geometry + decoration) |
| `bandAxis` | `Stealth tip, cGray, line width=0.42pt` | vertical Energy axis arrow (geometry) |
| `bandEt` | `cGray!45, dashed, line width=0.38pt` | Et reference dashed line (semantic encoding — Et is by convention dashed) |
| `trapShallow` | `cAmber, line width=0.72pt` | shallow trap dash (semantic encoding — color = depth class) |
| `trapDeep` | `cBlue!45!cRed, line width=0.72pt` | deep trap dash (semantic encoding — color = depth class) |

## Style-responsibility carving rule

Three categories of style live in this macro:
1. **Geometric parameters** — positions, dimensions, arrow tip lengths, rounded-corner radii. Part of the shape; lives in macro.
2. **Semantic encoding** — `bandEt` dashed (Et = reference convention), `trapShallow`/`trapDeep` color hue (shallow vs deep classification). Smart default in macro; caller may override.
3. **Decoration** — frame color, fill opacity, non-semantic line widths. Belongs to caller; macro provides default as convenience.

Caller is free to override any (1)/(2)/(3) value; the defaults exist to make uncustomized calls produce a meaningfully encoded figure.

## Three usage patterns

### Default
```latex
\BandDiagram{6,0,11,5, 4, 1, 9, {3.5,3.2,2.9}, {1.8,1.5}}
```
No optional arg → renders with all sub-style defaults.

### Per-call override
```latex
\BandDiagram[bandFrame/.append style={draw=cAmber, line width=0.8pt}]
            {6,0,11,5, 4, 1, 9, {3.5,3.2,2.9}, {1.8,1.5}}
```
Caller patches `bandFrame` for this call only; subsequent `\BandDiagram` calls revert to the figure-wide default.

### Figure-wide tikzset
```latex
\tikzset{bandFrame/.append style={draw=cAmber}}
\BandDiagram{6,0,11,5, 4, 1, 9, {3.5,3.2,2.9}, {1.8,1.5}}
\BandDiagram{0,0,5,5, 4, 1, 3, {3.0}, {1.5}}
```
All `\BandDiagram` calls in this scope inherit the appended style. (Pre-pilot caller pattern; still supported unchanged.)

## Migration note

Existing 1-arg callsites (`\BandDiagram{...}`) compile unchanged under the new `[2][]` signature — the missing `[#1]` defaults to empty, and the wrapping scope's `\tikzset{}` becomes a no-op. No migration is required.

## Not supported in this pilot

- Direct sub-key syntax `\BandDiagram[bandFrame={...}, bandAxis={...}]` (β fan-out pattern). The macro does not parse `[#1]` into per-sub-element keys; only `.append style` and similar pgfkeys idioms work. (`bandFrame={...}` will fail compile because `bandFrame` is a `.style` key, not a value-accepting key.)
- Nesting `\BandDiagram` inside another macro's hook arg in a way that crosses `\begingroup`/`\endgroup` boundaries. `\BD@opts` is grouped per-call; sequential calls are safe.

If a future fixture needs the β fan-out pattern, that is a separate spec — not a backwards-incompatible change to this pilot's interface.
