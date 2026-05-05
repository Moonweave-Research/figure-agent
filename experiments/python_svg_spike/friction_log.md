# Python SVG Spike Friction Log

Format follows spec section 8. Exactly one row is recorded for each frozen sub-region tag.

```
sub-region: A.cantilever_beam
hours: 0.015
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Bezier stroke/ribbon was direct; width profile is manually tuned but not blocking.
```

```
sub-region: A.clamp
hours: 0.012
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Hatching was manual line geometry inside a block; acceptable for this schematic scale.
```

```
sub-region: A.charges
hours: 0.007
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Reusable circle-minus marker covered the charge glyphs cleanly.
```

```
sub-region: A.electrode
hours: 0.011
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Plate, hatching, highlights, and +V label were straightforward drawsvg primitives.
```

```
sub-region: A.repulsion_arrow
hours: 0.011
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Filled arrowhead helper gave direct control over force emphasis.
```

```
sub-region: A.maxwell_arrow
hours: 0.009
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Same arrow helper scaled down cleanly for secondary force encoding.
```

```
sub-region: A.field_lines
hours: 0.010
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Curved dashed paths were simple; manual control points remain the tuning surface.
```

```
sub-region: A.probe_icon
hours: 0.013
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Icon is simplified but built from local primitives without stack friction.
```

```
sub-region: A.callout
hours: 0.020
category: typography
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Segmented emphasis required one spacing refinement after PNG render.
```

```
sub-region: B.title
hours: 0.008
category: typography
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Text and rounded card were direct drawsvg primitives.
```

```
sub-region: B.energy_axis
hours: 0.008
category: layout
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Arrow and rotated Energy label were straightforward.
```

```
sub-region: B.LUMO_box
hours: 0.006
category: layout
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Label box used ordinary rounded rectangle and text.
```

```
sub-region: B.HOMO_box
hours: 0.006
category: layout
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Same pattern as LUMO box.
```

```
sub-region: B.shallow_lines
hours: 0.009
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Horizontal state lines and label were direct primitives.
```

```
sub-region: B.deep_lines
hours: 0.009
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Dense red line stack was direct and stable.
```

```
sub-region: B.DOS_shallow
hours: 0.021
category: drawing
severity: P1
missing-from-stack: matplotlib SVG nesting cleanup for DOCTYPE/root handling
scales-to-remaining-panels-without-new-P0: yes
notes: Matplotlib SVG needed helper cleanup before embedding; once fixed, output parsed and reused.
```

```
sub-region: B.DOS_deep
hours: 0.013
category: drawing
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Reused the matplotlib lobe path after the shallow-lobe cleanup.
```

```
sub-region: B.Et_annotation
hours: 0.020
category: math
severity: P1
missing-from-stack: automatic math-label box placement
scales-to-remaining-panels-without-new-P0: yes
notes: dvisvgm math was high quality, but bracket/text placement required manual render tuning.
```

```
sub-region: B.math_labels
hours: 0.023
category: math
severity: P1
missing-from-stack: automatic dvisvgm baseline and scale metrics
scales-to-remaining-panels-without-new-P0: yes
notes: Labels rendered cleanly as paths; visual scale needed manual width iteration.
```

```
sub-region: B.callout
hours: 0.010
category: typography
severity: P2
missing-from-stack: none
scales-to-remaining-panels-without-new-P0: yes
notes: Italic multi-line callout fit after direct line breaking.
```
