# Fig1 Visual Judgment Report v22

This is a report-only visual judgment layer. It surfaces candidate visual risks and review prompts; it does not fail subjective visual issues.

Human visual review remains required before publication-grade approval.

## Scope Boundary

- Report-only: warnings here are not strict gate failures.
- Existing semantic, scaffold, causal, physics, and hash gates remain the hard-fail channels.
- Reference PNG remains layout/style evidence only, not ground truth.
- The v21 leftward cantilever force cue is an intentional reference divergence for physics sanity.

## Category Findings

### Panel Density
- possible issue: polymer_origin_card has high approximate occupied area (0.86); inspect whether panel density harms first-pass reading.
- candidate risk: electrical_evidence_card has moderate-high approximate occupied area (0.63); inspect whether whitespace is sufficient for scanning.
- possible issue: deep_trap_hero_card has high approximate occupied area (0.74); inspect whether panel density harms first-pass reading.
- possible issue: interpretation_card has high approximate occupied area (0.72); inspect whether panel density harms first-pass reading.
- candidate risk: macroscopic_probe_card has moderate-high approximate occupied area (0.67); inspect whether whitespace is sufficient for scanning.

### Text / Text Near-Collision
- possible issue: macroscopic_probe_card text boxes may compete at 0.0px gap: '+' near 'Force on cantilever'.
- candidate risk: polymer_origin_card text boxes may compete at 2.0px gap: 'S-rich segments' near 'S-chain length'.
- candidate risk: polymer_origin_card text boxes may compete at 2.3px gap: 'Sulfur polymer origin' near '(composition tuning)'.
- candidate risk: electrical_evidence_card text boxes may compete at 4.6px gap: 'slope = -n' near 'extract n'.

### Text / Shape Conflict
- candidate risk: deep_trap_hero_card text 'deep' is 2.2px from path mark (path); inspect label ownership and legibility.
- candidate risk: deep_trap_hero_card text 'states' is 2.2px from path mark (path); inspect label ownership and legibility.

### Visual Hierarchy
- evidence: hero maximum text size (24.0) exceeds support maximum (18.0); hierarchy appears intentional but still needs visual review.
- evidence: bbox salience proxy: selected primary semantic objects occupy about 0.25 of semantic bbox area; use this as evidence only, not a visual hierarchy failure.

### Reading Order
- evidence: likely panel reading order by top-left position: polymer_origin_card -> electrical_evidence_card -> deep_trap_hero_card -> interpretation_card -> macroscopic_probe_card.
- evidence: polymer_origin_card first text sequence by bbox position: Sulfur polymer ... -> (composition tu... -> S -> S -> S -> Heat 160 C.
- evidence: electrical_evidence_card first text sequence by bbox position: Electrical evid... -> P-E response -> Current decay -> P -> log I -> I(t) ~ t^-n.
- evidence: deep_trap_hero_card first text sequence by bbox position: Converged deep ... -> Deep traps domi... -> DOS g(Et) -> LUMO -> shallow -> shallow.
- evidence: interpretation_card first text sequence by bbox position: Interpretation ... -> I(t) ~ -> Debye -> n -> tau_d -> g(Et).
- evidence: macroscopic_probe_card first text sequence by bbox position: Macroscopic probe -> Cantilever -> (probe) -> + V -> Force on cantil... -> +.

### Reference Divergence
- evidence: intentional v21 divergence retained: probe force vector observed: force_target=cantilever, leftward=True, arrow_direction=cantilever_leftward_repulsion; v21 contract expects force_target=cantilever and leftward=True.
- inspect: This report records the known v21 probe-force divergence only; inspect any other reference divergence manually against scaffold, physics, readability, and causal-clarity reasons before treating it as justified.

### Human Review Prompts
- inspect: Inspect reference divergence: intentional v21 divergence retained: probe force vector observed: force_target=cantilever, leftward=True, arrow_direction=cantilever_leftward_repulsion; v21 contract expects force_target=cantilever and leftward=True.
- inspect: Inspect text / text near-collision: macroscopic_probe_card text boxes may compete at 0.0px gap: '+' near 'Force on cantilever'.
- inspect: Inspect text / shape conflict: deep_trap_hero_card text 'deep' is 2.2px from path mark (path); inspect label ownership and legibility.
- inspect: Inspect visual hierarchy: hero maximum text size (24.0) exceeds support maximum (18.0); hierarchy appears intentional but still needs visual review.
- inspect: Inspect panel density: polymer_origin_card has high approximate occupied area (0.86); inspect whether panel density harms first-pass reading.
- inspect: Inspect reading order: likely panel reading order by top-left position: polymer_origin_card -> electrical_evidence_card -> deep_trap_hero_card -> interpretation_card -> macroscopic_probe_card.
- inspect: Inspect text / text near-collision: polymer_origin_card text boxes may compete at 2.0px gap: 'S-rich segments' near 'S-chain length'.
- inspect: Inspect text / text near-collision: polymer_origin_card text boxes may compete at 2.3px gap: 'Sulfur polymer origin' near '(composition tuning)'.

## Evidence Snapshot

### Panel Bounds And Density

| Panel | Role | Bounds | Occupied | Text | Semantic Objects |
| --- | --- | --- | ---: | ---: | ---: |
| polymer_origin_card | supporting | 22.0,30.0,455.0,394.0 | 0.857 | 0.123 | 1 |
| electrical_evidence_card | supporting | 1076.0,30.0,497.0,394.0 | 0.631 | 0.073 | 3 |
| deep_trap_hero_card | hero | 548.0,173.0,468.0,613.0 | 0.740 | 0.114 | 4 |
| interpretation_card | supporting | 22.0,464.0,475.0,470.0 | 0.716 | 0.099 | 2 |
| macroscopic_probe_card | supporting | 1054.0,464.0,519.0,470.0 | 0.670 | 0.091 | 5 |

### Semantic Object BBoxes

| Semantic id | Kind | Panel | BBox |
| --- | --- | --- | --- |
| layout_flow | LayoutFlow | deep_trap_hero_card | 487.1,153.2,1066.8,724.9 |
| sulfur_polymer_origin | SulfurPolymerOrigin | polymer_origin_card | 47.6,52.0,472.4,413.8 |
| deep_trap_hero | DeepTrapHero | deep_trap_hero_card | 596.0,238.8,968.0,745.0 |
| band_diagram | BandDiagram | deep_trap_hero_card | 566.0,268.5,782.5,666.6 |
| trap_level_set | TrapLevelSet | deep_trap_hero_card | 612.8,375.9,760.4,567.1 |
| dos_lobes | DOSLobes | deep_trap_hero_card | 807.0,303.5,971.0,648.5 |
| evidence_trio | EvidenceTrio | electrical_evidence_card | 1135.5,106.3,1539.5,396.8 |
| pe_hysteresis | PEHysteresisPlot | electrical_evidence_card | 1147.0,168.5,1308.5,325.6 |
| power_law_decay | PowerLawDecayPlot | electrical_evidence_card | 1380.3,164.6,1552.2,346.5 |
| ispd_plot | ISPDPlot | interpretation_card | 373.0,663.5,466.5,829.0 |
| trap_model_flow | TrapModelFlow | interpretation_card | 55.2,540.0,463.0,912.0 |
| macroscopic_probe | MacroscopicProbe | macroscopic_probe_card | 1101.5,573.4,1525.5,897.2 |
| polymer_cantilever | PolymerCantilever | macroscopic_probe_card | 1106.0,543.5,1485.4,831.5 |
| electrode | Electrode | macroscopic_probe_card | 1497.0,608.0,1567.4,878.0 |
| repulsion_arrow | ForceArrow | macroscopic_probe_card | 1193.4,657.6,1360.6,720.0 |
| maxwell_attraction_cue | MaxwellAttractionCue | macroscopic_probe_card | 1314.6,759.0,1433.2,794.8 |

### Text BBox Summary

| Panel | Text boxes | Font range | Role tags |
| --- | ---: | --- | --- |
| polymer_origin_card | 27 | 5.9-18.0 | origin-localized-traps, origin-relation, origin-s-rich-segments, panel-conclusion, panel-title-support |
| electrical_evidence_card | 12 | 9.8-18.0 | decay-extract-n, electrical-conclusion, panel-conclusion, panel-title-support, schematic-label |
| deep_trap_hero_card | 17 | 11.0-24.0 | dos-axis-label, dos-depth-label, dos-label, energy-axis, hero-caption, hero-converged-picture, panel-title-hero |
| interpretation_card | 18 | 7.5-18.0 | interpretation-causal-step, interpretation-conclusion, interpretation-step-debye, interpretation-step-exponent-n, interpretation-step-power-law, interpretation-step-tau-d, interpretation-step-trap-depth-distribution, panel-conclusion, ... |
| macroscopic_probe_card | 13 | 11.2-18.0 | panel-conclusion, panel-title-support, probe-conclusion, probe-force-label |
