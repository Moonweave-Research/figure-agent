# Fig1 Reference-Based Semantic Layout Spec v1

## Target Decision

The visual target is now the supplied LMM reference image:

- `reference/source_variant_aesthetic_ref.png`

The reference is no longer a loose style hint for a 1:2:1:1 L1 strip. It is the authoritative visual layout target for this experiment. The scientific scene model remains semantic-driven, but the visual layout contract must follow the reference composition.

The reference is still not a pixel-tracing target. The renderer must not extract paths from the PNG. It must translate the reference layout into structured visual regions, anchors, object boxes, arrows, and style rules.

## Canvas

- Width: `1595 px`
- Height: `986 px`
- Aspect: match the reference PNG

## Layout

The layout is a center-hero composition with four surrounding support cards.

Required regions:

1. `polymer_origin_card`
   - Position: upper left
   - Bounds: `[22, 30, 455, 394]`
   - Role: support
   - Content: sulfur polymer origin, S8 ring, heat arrow, Sx chain, S60 to S85 composition arrow, three material bullets

2. `electrical_evidence_card`
   - Position: upper right
   - Bounds: `[1076, 30, 497, 394]`
   - Role: support
   - Content: P-E response and current decay side-by-side

3. `deep_trap_hero_card`
   - Position: center
   - Bounds: `[548, 173, 468, 613]`
   - Role: hero
   - Content: LUMO/HOMO band diagram, shallow levels, deep levels, DOS g(Et), Et annotation, deep-trap message callout

4. `interpretation_card`
   - Position: lower left
   - Bounds: `[22, 464, 475, 470]`
   - Role: support
   - Content: trap model flow, current decay, Debye/tau cue, trap DOS inset, convergence callout

5. `macroscopic_probe_card`
   - Position: lower right
   - Bounds: `[1054, 464, 519, 470]`
   - Role: support
   - Content: cantilever probe, trapped charges, electrode, dominant red repulsion force, secondary blue Maxwell attraction cue, charge-trapping-induced repulsion callout

## Flow

Support cards point inward to the center hero:

- upper left -> hero
- upper right -> hero
- lower left -> hero
- lower right -> hero

The flow arrows are visual routing cues, not a left-to-right L1 strip.

## Scientific Semantics

Preserve:

- Sulfur polymer origin from S8 to Sx chain.
- Composition cue S60 to S85.
- Deep traps visually dominate shallow traps.
- Deep DOS lobe visually dominates shallow lobe.
- Electrical evidence includes P-E response and current decay.
- Interpretation links power-law current, Debye/tau, and trap DOS.
- Macroscopic probe shows repulsion as dominant.
- Maxwell attraction is allowed only as a secondary cue in the probe card, because it exists in the reference.

Avoid:

- Generic actuator framing.
- Bidirectional actuation framing.
- A separate force-balance panel.
- Treating the PNG as a traced ground-truth image.

## Machine-Readable Contract

The renderer and verifier must consume:

- `visual_layout.yaml`

This file owns:

- canvas dimensions
- card bounds
- region roles
- region-to-object assignment
- inward flow arrow anchors
- visual rules around hero placement and Maxwell cue treatment

The scene model owns:

- semantic object kinds
- typed payloads
- physics/domain assertions such as trap dominance, DOS dominance, charge sign, and force direction

The renderer must consume both layers:

- domain semantic payloads
- reference visual layout contract

The verifier must check both layers:

- semantic correctness
- reference-layout correctness
