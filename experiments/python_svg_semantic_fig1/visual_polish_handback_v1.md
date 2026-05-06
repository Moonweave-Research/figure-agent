# Fig1 Semantic Visual Polish Handback v1

## Verdict

The important lesson from the first preview was that semantic payloads alone did not reproduce the desired figure. The renderer needed a structured visual contract for the reference layout, not only scientific object kinds.

This pass therefore treats the supplied reference as the authoritative visual layout target and encodes it in `visual_layout.yaml`. The result is closer in composition: center hero, four surrounding support cards, inward arrows, two-plot electrical evidence, interpretation card, and probe card with dominant repulsion plus secondary Maxwell cue.

## Fixed Since The L1 Preview

- Replaced the 1780 x 1000 horizontal L1 strip with the 1595 x 986 reference canvas.
- Replaced 1:2:1:1 columns with five explicit reference regions.
- Promoted card bounds, object assignment, and support-to-hero arrows into data.
- Moved ISPD into the interpretation card, matching the reference structure.
- Made P-E red and current decay blue from payload colors.
- Added a secondary `MaxwellAttractionCue` object instead of forbidding the reference cue.
- Updated verification to check the reference layout contract, not the old L1 ratio.

## Still Visually Weak

- The renderer follows region layout, but internal micro-composition is still less fluent than the LMM reference.
- Plot ticks, axis balance, and label kerning remain schematic.
- The cantilever and polymer curvature are functional but not yet manuscript-polished.
- The hero card has the right semantic hierarchy, but the LUMO/HOMO/DOS spacing needs another manual pass.

## Next Visual Pass

The next pass should not add more semantic kinds first. It should tune anchors and local geometry inside each card:

- Hero local layout anchors.
- Plot thumbnail templates.
- Probe beam curve and charge placement.
- Text collision checks.
- Print-scale typography.

No PNG tracing was used; the reference was converted into a structured layout contract.
