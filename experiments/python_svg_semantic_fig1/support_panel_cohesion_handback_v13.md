# v13 Support-Panel Cohesion Handback

## Scope

`v13_support_panel_cohesion` continues the v12 panel audit without changing the semantic scene object model. It is a renderer/composition pass over existing `SulfurPolymerOrigin`, `MacroscopicProbe`, `PolymerCantilever`, `Electrode`, `ForceArrow`, and `MaxwellAttractionCue` payloads.

## RED Checks Added First

The v13 verifier blocks the support-panel issues that remained visually awkward after v12:

- Origin panel must render a compact `origin-relation` cue instead of relying on checklist density.
- Origin panel may not expose more than two `origin-bullet` labels.
- Probe panel must render a normalized one-line `probe-force-label`.
- Probe panel may not keep the old boxed `#fff8f7` footer callout.
- Probe cantilever may not use `url(#softInsetShadow)` inset-shadow effects.

Initial RED output:

```text
v13 support-panel cohesion checks failed:
- origin panel missing compact composition relation cue
- probe panel missing normalized one-line force label
- probe panel still uses a boxed footer callout
- probe cantilever still uses heavy inset shadow effects
```

## Rendering Changes

- Replaced the origin checklist with a compact relation chain: `S fraction -> S-S sequence -> deep traps`.
- Reduced the origin ramp arrow and label scale so the S60-to-S85 cue no longer dominates the card edge.
- Flattened probe clamp/electrode fills and removed the inset shadow from the cantilever fixture.
- Replaced the probe boxed footer with a rule-separated conclusion cue.
- Normalized the repulsion-force label to one line and softened the secondary Maxwell cue.

## Remaining Direction

v13 still does not make the figure final. It moves the two most awkward support panels closer to the same schematic language as the hero, but the next useful pass is a global figure-level pass:

- unify arrow opacity/weight across support-to-hero and local mechanism arrows;
- normalize support panel title placement and caption density;
- decide whether the probe should stay semi-device-like or be flattened further into a pure schematic.

## Verification

The v13 output should be regenerated with `render_fig1_l1.py`, checked with `verify_fig1_semantics.py`, parsed as XML, compiled with `py_compile`, converted through `rsvg-convert`, and visually reviewed as `fig1_reference_semantic.png`.
