# Briefing — fig1_energy_landscape_v1_pair_002_vault

> **Pilot pair**: `fig1_energy_landscape_v1_pair_002` / **Arm**: vault
> **Design snapshot SHA**: `9b4e36033336826a566dfb7dfb95e6ac4c51851aee423e6696fdd60b0dd89f07`
> **Vault query**: `a5c0a136-f6b3-4d72-940a-54a87dd6a97b` (approved_only, proposed_records_allowed=false)
> **Vault state**: degraded_mode=true — chroma_v2 indexes absent (text/image/scaffold/style branches all `absent`).

## 1. Same target, vault-grounded authoring

This arm targets the exact same focused 4-panel `fig1_energy_landscape_v1`
schematic specified in design.md. Authoring uses approved tikz-vault records
as grammar / style anchors instead of authoring from design intent alone.
All 12 returned records have `source_access=masked`
(`raw_source_path_exposed=false`); only record-level metadata (role,
record_id, role assignment) informs authoring. No raw source files are
opened.

## 2. Vault grammar anchors (selected_reference_ids)

Six of the 12 returned records are *used* during this arm's authoring as
grammar/style anchors. The remaining six are available but not directly
applied (rationale recorded in §"Available but not selected" below).

### Panel A — sulfur polymer network grammar

- **`manual_seed_cho2024_fig1_s8_polymerization`** (motif).
  Sulfur polymer + DIB cross-link motif anchor. → Use the preamble's
  `\WavyChain` macro (zigzag style with S markers) for the two polymer
  chains, replacing the no_vault arm's manual bezier polysulfide chain
  primitives.
- **`manual_seed_cho2024_fig1_dynamic_exchange`** (annotation).
  Dynamic polysulfide bond-exchange grammar. → Use a dashed annotation
  arrow at the retained-charge deep-trap location to evoke the
  exchange/repair-loop idiom and unify trap site with chain dynamics.

### Panel B — energy landscape grammar

- **`manual_seed_patel2019_fig7_recombination_band`** (layout).
  Recombination band-energy hierarchy. → Encode the shallow/deep contrast
  with depth-hierarchical amplitudes (shallow ~0.40, deep ~1.00) and
  explicit band overlays, in addition to the color contrast.
- **`manual_seed_cho2024_fig7_corona_charge`** (annotation).
  Corona-charge / charge-retention annotation grammar. → Use a thicker
  retention arrow with a small filled trap-bound dot (charge-retained
  motif) at the deep-well minimum, instead of the no_vault arm's plain
  Stealth-only arrow.

### Panel D — trap-depth distribution grammar

- **`manual_seed_patel2019_fig4_trap_dos`** (motif).
  Trap density-of-states distribution motif (highest-ranked record in
  this query at ranking_score 0.443). → Use the preamble's `\BellCurve`
  macro for both shallow and deep distributions, giving canonical
  paper-grade lobes rather than the no_vault arm's hand-rolled bezier
  Gaussians.

### Cross-figure layout grammar

- **`manual_seed_cho2024_fig2_mxene_percolation`** (layout).
  Multi-panel composite layout grammar for SRP figures. → Anchor the
  2 × 2 panel grid proportions and figure-wide breathing room.

### Available but not selected (rationale)

- `manual_seed_cho2024_fig6` + `manual_seed_cho2024_fig6_recycling_loop`
  — recycling-loop grammar, out of scope for an energy-landscape figure.
- `manual_seed_cho2024_fig7` — composite redundant with the corona_charge
  annotation anchor already selected.
- `manual_seed_natcommun2024_fig1` — multi-panel composite typography
  redundant with cho2024_fig2_mxene_percolation layout.
- `github_60dad45579bb4d2c_01` (MIT) + `github_16d92f461ca71c30_01` (MIT)
  — external multi-panel references; useful as layout fallback but not
  needed once the in-paper anchor (cho2024_fig2_mxene_percolation) was
  selected.

## 3. Same layout, same physics invariants (design.md verbatim)

- Canvas 14 cm × 9 cm landscape → `\resizebox{178mm}{!}`.
- 2 × 2 grid with A/B/C/D corner labels.
- Panel B (energy landscape) is the visual anchor per design.
- Color map: blue = shallow traps, red = deep traps, gold = sulfur network,
  gray = axes / reference / Debye references.
- Panel C is a split plot with log-time x-axis labeled `time`; top trace
  `I(t) ~ t^{-n}`, bottom trace `V_s(t)`; symbolic axes only — no tick
  values, no measured numerics (figure-agent symbolic-axis policy).
- Panel D shows shallow and deep distributions with a vertical `E_t`
  marker and `fast release` / `long retention` callouts.

## 4. Author intent recap

This arm tests whether vault-grounded grammar surfaces or prevents the
category of issues the no_vault arm exhibits at the same scope. Specific
grammar shifts versus no_vault:

| Panel | no_vault idiom        | vault grammar shift                                  |
| ----- | --------------------- | ---------------------------------------------------- |
| A     | bezier chain          | `\WavyChain` zigzag with S markers + exchange arrow  |
| B     | bezier wells, flat    | depth-hierarchical amplitudes + corona retention arrow |
| C     | shared with no_vault  | label hierarchy from typography grammar              |
| D     | bezier Gaussian lobes | `\BellCurve` macro (paper-grade canonical lobes)     |

Whether the resulting differences are caused by vault grounding or by
independent authoring discipline is the question for an external blind
evaluator, not for this briefing. This run does **not** perform or claim
blind A/B evaluation.
