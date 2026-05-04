# `\PlotCallout` Macro Reference

**Signature:** `\PlotCallout[<node style>]{target coord}{label coord}{text}`

Draws a short leader arrow from a white-backed label to a plotted feature. Use it
when an inline plot annotation would otherwise sit on top of a data trace, axis
line, threshold line, or reference marker.

## Arguments

- `target coord` — TikZ coordinate the annotation points to. Plain coordinates
  like `(1,2)` and pgfplots coordinates like `(axis cs:1e0, 8e-4)` are both valid.
- `label coord` — TikZ coordinate where the label node is placed.
- `text` — label content.
- Optional `[<node style>]` — appended to the label node. Typical values:
  `text=cBlue`, `anchor=north west`, `align=left`.

## Defaults

| Style key | Default | Purpose |
|---|---|---|
| `plotCalloutLine` | `cGray!70`, `0.34pt`, stealth arrow | semantic leader from label to feature |
| `plotCalloutLabel` | white fill, small sans font, `inner sep=0.65pt` | readable label backing |

## Example

```tex
\PlotCallout[text=cBlue, anchor=north west]
  {(axis cs:1e0, 1.6e-3)}{(axis cs:1.2e0, 8e-4)}{slope = $-n$}
```

## Scope

This macro is an annotation-safety primitive. It does not solve automatic label
placement; authors still choose the target and label coordinates. Its role is to
make the safe pattern explicit and reusable instead of hand-writing a bare
`\node at (...)` directly over plot data.
