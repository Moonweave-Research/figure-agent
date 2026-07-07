# Authoring Plan: fig1_overview_v4_pair_001_vault

## Inputs Read

- `briefing.md`
- `design.md`
- `spec.yaml`
- `critique.md`
- `authoring_contract.md`
- `reference/reference_pack.md`
- `reference/codex_gen_overview_v1.png`
- `reference/sulfur_polymer_panelA_ref.png`
- `coordinate_hints.yaml`: absent; no OCR, palette-cluster, or structural-hint
  evidence is available for this pass.

## Panel Strategy

- A: Preserve the current linear poly(S-r-DIB) topology. Use DIB ring and
  polysulfide-link motifs only as bivalent linear-chain chemistry. Key risk:
  accidental network transfer from the anti-reference.
- B: Keep four delicate schematic S-chain rows and Panel-B-only composition
  labels. Key risk: making chain length look like a measured quantitative
  sweep.
- C: Preserve the split real-space/energy-diagram hero. Use mixed trap markers
  in one polymer matrix and color-matched shallow/deep trap levels. Key risk:
  implying spatial segregation or mismatching C/F colors.
- Row2-BG/BR1/BR2: Preserve the shared background and three evidence spokes
  from C to D, E/F, and G. Key risk: reading as a D->E->F->G causation chain.
- D: Keep tickless axis arrows, separated power-law traces, and Debye reference
  below the long-time tails. Key risk: non-Debye physics inversion.
- E: Keep the raw ISPD decay as a linear-time schematic with filled red
  markers. Key risk: reverting to log-time or overclaiming quantitative data.
- F: Keep the bimodal shallow/deep g(Et) cartoon with red deep dominance and
  blue shallow lobe. Key risk: color or depth mismatch with Panel C.
- G: Keep top clip, hanging polymer, right electrode, trapped-charge markers,
  and a single Coulomb repulsion arrow. Key risk: Maxwell-attraction transfer
  or actuator framing.

## Theory Decisions

- Panel A linear topology is locked by `authoring_contract.md` and resolved
  `critique.md`; `reference/sulfur_polymer_panelA_ref.png` is an
  anti-reference for topology.
- Panel C and Panel F color semantics are locked by `briefing.md` physics
  invariant 8.2 and the contract.
- Row 2 evidence is independent and three-spoke, not sequential causation, per
  `briefing.md` sections 4 and 8.7.
- Panel G Coulomb-only mechanics are locked by `design.md` section 2.3 and
  `briefing.md` invariant 8.5.
- Publication readiness requires provenance/publication compliance review; a
  successful compile/export is not sufficient for `accepted: true`.

## Patch Order

1. Row2-BR2: verify the C-to-D/E/F/G spoke geometry and modality labels still
   read as three independent evidence lines after v7 width normalization.
2. D-2/D-3: verify power-law tails remain above the Debye reference at long
   times and the labels do not collide.
3. C-R2/C-R3/F-2/F-3: verify shallow/deep color and trap-depth consistency
   across Panels C and F.
4. G-2/G-3/G-6: verify the compressed hanging-polymer scene preserves
   Coulomb-only mechanics and electrode/polymer separation.
5. A-1/A-2/A-4/A-8: verify the linear topology remains readable and no network
   semantics leak back in.
6. Publication/provenance sweep: verify reference roles, anti-reference
   boundaries, critique freshness, and audit decision before export acceptance.

## Human Checkpoints

- Confirm whether the current linear poly(S-r-DIB) claim remains valid against
  manuscript chemistry before any Panel A topology edit.
- Confirm target-journal AI/image policy before any `submission-safe` or
  `accepted: true` claim.
- Confirm whether dashed-line semantic diversity (#17) is acceptable as an
  intentional residual risk or should be consolidated in a later patch.
- Confirm any theory BLOCKER that cannot be decided from `briefing.md`,
  `design.md`, `critique.md`, and rendered/source evidence.
