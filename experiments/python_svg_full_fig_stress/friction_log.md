# Python SVG Full-Figure Stress Friction Log

Format: one row per stress tag from the design spec.

```
tag: SETUP.contract
hours: 0.05
category: setup
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Existing spike helpers copied cleanly; minimal full-canvas SVG parsed.
```

```
tag: LAYOUT.canvas_cards
hours: 0.03
category: layout
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Full-card layout was direct coordinate geometry.
```

```
tag: TL.s8_ring
hours: 0.04
category: drawing
severity: P1
missing-from-stack: chemistry-aware graph layout and atom/bond semantics
scales-to-future-paper-figures-without-new-P0: no
notes: Hand-drawn S8 is readable here, but general chemistry structures would need a real molecule renderer.
```

```
tag: TL.polymer_chain
hours: 0.04
category: drawing
severity: P1
missing-from-stack: chemistry-aware polymer chain renderer
scales-to-future-paper-figures-without-new-P0: no
notes: Manual sulfur chain communicates the story but is not a scalable chemical drawing method.
```

```
tag: TL.composition_swatch
hours: 0.02
category: drawing
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Segmented swatch and arrow were straightforward.
```

```
tag: TL.bullets
hours: 0.02
category: typography
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Simple text primitives were enough.
```

```
tag: CENTER.energy_bands
hours: 0.04
category: drawing
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Energy axis, boxes, and trap levels were direct.
```

```
tag: CENTER.dos_math
hours: 0.08
category: math
severity: P1
missing-from-stack: automatic dvisvgm label layout and collision-aware placement
scales-to-future-paper-figures-without-new-P0: yes
notes: Math quality is strong, but label sizing/placement required manual render inspection.
```

```
tag: CENTER.callout
hours: 0.02
category: typography
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Multi-line callout fit inside card.
```

```
tag: TR.pe_loop
hours: 0.04
category: drawing
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Manual Bezier loop worked for schematic P-E evidence.
```

```
tag: TR.current_decay
hours: 0.05
category: math
severity: P1
missing-from-stack: compact log-axis helper
scales-to-future-paper-figures-without-new-P0: yes
notes: Ticks and labels are manually placed; scalable plot panels need a small helper abstraction.
```

```
tag: BL.model_flow
hours: 0.06
category: math
severity: P1
missing-from-stack: math box auto-fit
scales-to-future-paper-figures-without-new-P0: yes
notes: dvisvgm equations rendered well, but tau/g labels needed manual width tuning.
```

```
tag: BL.current_decay_plot
hours: 0.04
category: drawing
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Mini current plot was easy once the TR pattern existed.
```

```
tag: BL.dos_plot
hours: 0.06
category: drawing
severity: P1
missing-from-stack: reusable compact DOS plot helper
scales-to-future-paper-figures-without-new-P0: yes
notes: Matplotlib lobes are smooth but generated SVG is verbose and needs deterministic cleanup.
```

```
tag: BL.callout
hours: 0.02
category: typography
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Simple rounded callout.
```

```
tag: BR.probe_mechanics
hours: 0.06
category: drawing
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Prior spike pattern scaled into the full figure.
```

```
tag: BR.force_cues
hours: 0.05
category: drawing
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Charges, dashed fields, arrows, and callout worked with existing helpers.
```

```
tag: LAYOUT.inter_panel_arrows
hours: 0.02
category: layout
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Simple arrows were easy; visual balance still needs human polish.
```

```
tag: EXPORT.render_checks
hours: 0.05
category: verification
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: SVG parsed and PNG rendered with rsvg-convert; one visual-defect pass was performed.
```

```
tag: HANDOFF.logs
hours: 0.04
category: documentation
severity: P2
missing-from-stack: none
scales-to-future-paper-figures-without-new-P0: yes
notes: Logs summarize evidence without G2 self-scoring.
```
