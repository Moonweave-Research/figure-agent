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
- candidate risk: top_synthesis has moderate-high approximate occupied area (0.67); inspect whether whitespace is sufficient for scanning.
- possible issue: localized_traps has high approximate occupied area (0.76); inspect whether panel density harms first-pass reading.
- evidence: release_module occupied area is 0.19 with text area 0.06; use as layout density evidence, not a pass/fail rule.
- candidate risk: vs_decay_module is unusually sparse by bbox area (0.03); inspect whether the visual weight matches its semantic role.
- candidate risk: ispd_module is unusually sparse by bbox area (0.10); inspect whether the visual weight matches its semantic role.
- candidate risk: probe_module has moderate-high approximate occupied area (0.59); inspect whether whitespace is sufficient for scanning.

### Text / Text Near-Collision
- candidate risk: localized_traps text boxes may compete at 3.1px gap: 'qualitative trap landscape insi...' near 'DOS g(Et)' [box=dos_area].
- candidate risk: probe_module text boxes may compete at 5.0px gap: '+' near 'Maxwell attraction' [box=probe_frame].

### Text / Shape Conflict
- possible issue: localized_traps text '−' is 0.0px from path mark (trap-track) [box=band_area]; inspect label ownership and legibility.
- possible issue: localized_traps text '−' is 0.0px from path mark (dos-lobe-deep) [box=dos_area]; inspect label ownership and legibility.
- possible issue: localized_traps text '−' is 0.0px from path mark (trap-track) [box=band_area]; inspect label ownership and legibility.
- possible issue: localized_traps text '−' is 0.0px from path mark (dos-lobe-deep) [box=dos_area]; inspect label ownership and legibility.
- possible issue: probe_module text '+' is 0.0px from path mark (path) [box=probe_frame]; inspect label ownership and legibility.
- possible issue: probe_module text 'Coulomb F' is 0.0px from path mark (path) [box=probe_frame]; inspect label ownership and legibility.
- possible issue: probe_module text 'Maxwell attraction' is 0.0px from path mark (path) [box=probe_frame]; inspect label ownership and legibility.
- possible issue: probe_module text 'Maxwell attraction' is 0.0px from circle mark (circle) [box=probe_frame]; inspect label ownership and legibility.
- candidate risk: probe_module text 'Coulomb F' is 3.1px from circle mark (circle) [box=probe_frame]; inspect label ownership and legibility.

### Visual Hierarchy
- evidence: hero maximum text size (24.0) exceeds support maximum (18.0); hierarchy appears intentional but still needs visual review.
- evidence: bbox salience proxy: selected primary semantic objects occupy about 0.25 of semantic bbox area; use this as evidence only, not a visual hierarchy failure.

### Reading Order
- evidence: likely panel reading order by top-left position: top_synthesis -> localized_traps -> release_module -> vs_decay_module -> ispd_module -> probe_module.
- candidate risk: 16 text boxes are outside semantic groups ('−', '−', '−', '−', '−', '−', '−', '−'); inspect whether their ownership is visually clear.
- evidence: top_synthesis first text sequence by bbox position: log I -> extract n -> slope -n -> Sulfur-rich net... -> log t -> Heat 160 C.
- evidence: localized_traps first text sequence by bbox position: localized traps -> qualitative tra... -> DOS g(Et) -> shallow -> Et ~ -> 0.5-1.0 eV.
- evidence: release_module first text sequence by bbox position: distributed rel... -> shallow -> deep -> t₁ -> t₂ -> t₃.
- evidence: vs_decay_module first text sequence by bbox position: V_s(t) decay -> V_s(t) -> non-Debye -> t (s).
- evidence: ispd_module first text sequence by bbox position: ISPD-derived g(Et) -> Shallow -> Et -> Deep.
- evidence: probe_module first text sequence by bbox position: Macroscopic probe -> air gap -> + -> Maxwell attraction -> + -> Coulomb F.

### Reference Divergence
- evidence: intentional v21 divergence retained: probe force vector observed: force_target=cantilever, leftward=True, arrow_direction=cantilever_leftward_repulsion; v21 contract expects force_target=cantilever and leftward=True.
- inspect: This report records the known v21 probe-force divergence only; inspect any other reference divergence manually against scaffold, physics, readability, and causal-clarity reasons before treating it as justified.

### Human Review Prompts
- inspect: Inspect reference divergence: intentional v21 divergence retained: probe force vector observed: force_target=cantilever, leftward=True, arrow_direction=cantilever_leftward_repulsion; v21 contract expects force_target=cantilever and leftward=True.
- inspect: Inspect text / text near-collision: localized_traps text boxes may compete at 3.1px gap: 'qualitative trap landscape insi...' near 'DOS g(Et)' [box=dos_area].
- inspect: Inspect text / shape conflict: localized_traps text '−' is 0.0px from path mark (trap-track) [box=band_area]; inspect label ownership and legibility.
- inspect: Inspect visual hierarchy: hero maximum text size (24.0) exceeds support maximum (18.0); hierarchy appears intentional but still needs visual review.
- inspect: Inspect panel density: top_synthesis has moderate-high approximate occupied area (0.67); inspect whether whitespace is sufficient for scanning.
- inspect: Inspect reading order: likely panel reading order by top-left position: top_synthesis -> localized_traps -> release_module -> vs_decay_module -> ispd_module -> probe_module.
- inspect: Inspect text / text near-collision: probe_module text boxes may compete at 5.0px gap: '+' near 'Maxwell attraction' [box=probe_frame].
- inspect: Inspect text / shape conflict: localized_traps text '−' is 0.0px from path mark (dos-lobe-deep) [box=dos_area]; inspect label ownership and legibility.

## Evidence Snapshot

### Panel Bounds And Density

| Panel | Role | Bounds | Occupied | Text | Semantic Objects |
| --- | --- | --- | ---: | ---: | ---: |
| top_synthesis | supporting | 22.0,30.0,900.0,410.0 | 0.667 | 0.044 | 1 |
| localized_traps | hero | 940.0,30.0,633.0,410.0 | 0.760 | 0.094 | 4 |
| release_module | supporting | 22.0,488.0,380.0,470.0 | 0.192 | 0.057 | 2 |
| vs_decay_module | supporting | 414.0,488.0,240.0,470.0 | 0.033 | 0.033 | 0 |
| ispd_module | supporting | 666.0,488.0,520.0,470.0 | 0.096 | 0.017 | 1 |
| probe_module | supporting | 1198.0,488.0,375.0,470.0 | 0.592 | 0.085 | 5 |

### Semantic Object BBoxes

| Semantic id | Kind | Panel | Sub-region | BBox |
| --- | --- | --- | --- | --- |
| layout_flow | LayoutFlow | ispd_module | - | 211.5,232.0,1198.5,728.0 |
| sulfur_polymer_origin | SulfurPolymerOrigin | top_synthesis | composition_ramp | 56.3,120.2,860.7,419.8 |
| deep_trap_hero | DeepTrapHero | localized_traps | dos_area | 988.0,95.8,1522.0,435.5 |
| band_diagram | BandDiagram | localized_traps | band_area | 946.0,119.5,1182.5,366.5 |
| trap_level_set | TrapLevelSet | localized_traps | band_area | 1054.9,179.6,1151.9,302.7 |
| dos_lobes | DOSLobes | localized_traps | dos_area | 1254.0,114.5,1440.0,367.5 |
| power_law_decay | PowerLawDecayPlot | release_module | decay_inset | 63.4,729.6,275.4,830.1 |
| ispd_plot | ISPDPlot | ispd_module | ispd_plot | 872.0,633.5,969.5,835.0 |
| trap_model_flow | TrapModelFlow | release_module | release_callout | 54.7,916.6,369.3,942.5 |
| macroscopic_probe | MacroscopicProbe | probe_module | probe_callout | 1235.5,909.5,1535.5,965.0 |
| polymer_cantilever | PolymerCantilever | probe_module | probe_frame | 1284.0,576.0,1482.3,896.0 |
| electrode | Electrode | probe_module | probe_frame | 1468.8,600.0,1561.2,858.6 |
| repulsion_arrow | ForceArrow | probe_module | probe_frame | 1231.5,699.7,1317.6,747.0 |
| maxwell_attraction_cue | MaxwellAttractionCue | probe_module | probe_frame | 1317.5,642.5,1420.5,676.6 |

### Text BBox Summary

| Panel | Text boxes | Font range | Role tags |
| --- | ---: | --- | --- |
| top_synthesis | 16 | 11.2-18.0 | origin-localized-traps, origin-relation, origin-s-rich-segments, panel-conclusion, panel-title-support |
| localized_traps | 18 | 8.4-24.0 | dos-axis-label, dos-depth-label, dos-label, hero-caption, hero-converged-picture, panel-title-hero |
| release_module | 8 | 9.0-18.0 | interpretation-causal-strip, interpretation-conclusion, interpretation-step-debye, interpretation-step-exponent-n, interpretation-step-power-law, interpretation-step-tau-d, interpretation-step-trap-depth-distribution, panel-conclusion, ... |
| vs_decay_module | 4 | 9.0-18.0 | panel-title-support |
| ispd_module | 4 | 7.5-18.0 | panel-title-support, schematic-dos-depth-label, schematic-label |
| probe_module | 12 | 9.5-18.0 | panel-conclusion, panel-title-support, probe-conclusion, probe-force-label |
