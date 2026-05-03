# Briefing - n3_trial_02_actuation_sequence

## 1. What does this figure show? (1-2 sentences)

A three-panel schematic illustrating the voltage-driven actuation cycle of a sulfur-rich polymer strip: charge injection under +V, Coulomb repulsion-dominated bending under -V, and elastic relaxation under open circuit (0 V).

## 2. Domain vocabulary (terms, materials, mechanisms)

Visible text labels only:
- "Charge Injection" (Panel 1 title)
- "Coulomb Repulsion" (Panel 2 title)
- "Relaxation" (Panel 3 title)
- "Contact clip (GND)"
- "S-rich polymer"
- "+V applied" (Panel 1 caption)
- "-V applied" (Panel 2 caption)
- "Open circuit" (Panel 3 caption)
- "floating" (Panels 2 and 3, electrode label)
- "Coulomb > Maxwell" (Panel 2 annotation box)
- "e-" (electron symbol, all three panels)
- "+V" (electrode label, Panel 1)
- "-V" (electrode label, Panel 2)
- "0 V" (Panel 3 caption/label)
- "prev." (Panel 3, dashed ghost position label)

## 3. Composition intent (panel layout, flow direction)

Three equal-width panels arranged left-to-right, separated by thin vertical dividers on a light gray background. Flow is sequential: Panel 1 → Panel 2 → Panel 3.

- Panel 1 (Charge Injection): vertical gold/yellow polymer strip clamped at top (contact clip labeled GND), adjacent to a gray rectangular electrode on the right (+V). Red arrows point rightward from the strip toward the electrode. Electrons (e-) shown as filled circles on the strip.
- Panel 2 (Coulomb Repulsion): strip has bent leftward (away from electrode, which is now labeled -V and "floating"). Teal/green arrows point leftward. Annotation box reads "Coulomb > Maxwell."
- Panel 3 (Relaxation): strip is partially recovering toward its original position. Ghost/dashed outline labeled "prev." indicates prior bent position. Arrow curves from bent back toward upright. Electrode labeled "floating," voltage label "0 V."

## 4. Normalize / avoid literal overfit

- The "S-rich polymer" label is specific to this material system; a prompt should describe the strip generically as a flexible/compliant polymer cantilever clamped at one end, without requiring the exact label to appear.
- "Coulomb > Maxwell" is an interpretive annotation, not a universal label; treat as an optional callout that may be rendered differently.
- Arrow colors (red in Panel 1, teal in Panel 2) encode direction of electrostatic force, not material identity — do not hardcode the palette to these semantics.
- The "prev." ghost outline in Panel 3 communicates memory-of-prior-state; the concept is more important than the exact notation.

## 5. Style notes (optional)

- Panel backgrounds: light blue-gray rounded-rectangle cards.
- Strip material rendered in a warm gold/amber color (consistent across all three panels).
- Electrode rendered as a plain gray rectangle (no decorative features).
- Electron symbols are filled dark circles (no outlines on the symbols themselves).
- Panel titles are bold, black, centered at top of each card.
- Caption text ("+V applied," "-V applied," "Open circuit") appears below each panel in the figure body.
- Overall style is clean schematic illustration, no photorealism, consistent with journal supplementary / main-text figure conventions.

## 6. Physics invariants (preserved verbatim in prompt)

- Strip bends toward the +V electrode in Panel 1 (charge injection phase).
- Strip bends away from the electrode (leftward, away from -V) in Panel 2; annotation explicitly states Coulomb force dominates over Maxwell stress.
- In Panel 3 (open circuit, 0 V), the strip begins returning toward its upright position; a dashed ghost outline marks the previous bent position labeled "prev."
- The top end of the strip is clamped (contact clip, GND) and does not move across all three panels.
- The electrode switches from grounded (+V, Panel 1) to floating (-V, Panel 2) to floating (0 V, Panel 3). [uncertain: whether "floating" in Panel 2 vs Panel 3 has distinct electrical meaning or is the same state with different voltage annotation]
- Electrons (e-) are depicted on the strip surface in all three panels.
