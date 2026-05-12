# Briefing — fig1_overview_v2_pair_001_vault

> **Pilot pair**: `fig1_overview_v2_pair_001` / **Arm**: vault
> **Design snapshot SHA**: `fa7a6d9ff7890a440ca3471995acf8145c47001a996dbd8bf2c428b363d8f7b7`
> **Vault query**: 966e2e89-5c8a-41ea-a11f-658c99c3d037 (approved_only, proposed_records_allowed=false)
> **Vault state**: degraded_mode=true — chroma_v2 absent (text/image/scaffold/style branch indexes all absent)

## 1. Same target, vault-grounded authoring

This arm targets the exact same fig1_overview_v2 design as the no_vault arm —
same 2-row 7-panel layout, same v9.7+α charge-trap-centered framing, same
chemistry-accuracy v2.2 update for Panel A. The difference is that authoring
uses approved tikz-vault references as grammar/style anchors instead of authoring
from design intent alone. Reference source paths are masked (raw_source_path_exposed=false);
only record-level metadata (title, inspiration_role, element_role, domain_tags,
tikz_libraries) informs authoring.

## 2. Vault grammar anchors (selected_reference_ids)

Six records were *used* during this arm's authoring as grammar/style anchors; the
remaining six in `returned_reference_ids` were available but not directly applied.

### Panel A — sulfur polymer chemistry grammar

- **`manual_seed_cho2024_fig1_s8_polymerization`** (motif, sulfur_polymer_network).
  Title: "Cho 2024 Fig. 1 subpanel: S8 ring-opening and DIB-linked sulfur polymerization grammar".
  Tags: sulfur, polymer, inverse_vulcanization, elemental_sulfur, DIB, S_chain.
  TikZ libraries: arrows.meta, positioning, calc, shapes.geometric, decorations.pathmorphing.
  → Use `shapes.geometric` regular polygon for S₈ ring + `decorations.pathmorphing` snake for
  polysulfide chain (replaces no_vault arm's manual bezier chain).

- **`manual_seed_cho2024_fig1_dynamic_exchange`** (annotation, sulfur_polymer_network).
  Title: "Cho 2024 Fig. 1 subpanel: dynamic polysulfide bond exchange and repair loop".
  → Inform the DIB → polysulfide → DIB bridge motif with explicit bond-exchange-style
  dashed annotation for the S₈ → DIB transformation arrow.

### Panel C — energy landscape + charge trap grammar

- **`manual_seed_natcommun2024_fig1`** (motif).
  Title: "All-polymer dielectric multiboundary architecture with energy diagram,
  homogeneous matrix, and multiscale morphology".
  Tags: energy_diagram, multi_panel, phase_diagram, schematic.
  → Use the energy-diagram grammar to make shallow/deep trap wells visually
  hierarchical (depth-encoded amplitude, not just color).

- **`manual_seed_cho2024_fig7_corona_charge`** (annotation).
  Title: "Cho 2024 Fig. 7 subpanel: corona charging setup and SRP/MXene charge retention grammar".
  Tags: charge_trap, S_chain, network.
  → Direct grammar match for "localized trap" annotation idioms in a sulfur polymer context.

### Cross-figure layout + typography grammar

- **`manual_seed_cho2024_fig2_mxene_percolation`** (layout). Multi-panel composite layout
  grammar for SRP figures. → Anchor the 2-row × 7-panel layout proportions.

- **`manual_seed_cho2024_fig1`** (typography, composite). Title carries paper-typography
  identity for "Sulfur-rich polymer/MXene composite preparation and dynamic bond exchange
  mechanism". → Anchor inline-label typography hierarchy.

### Available but not selected (rationale)

- `manual_seed_cho2024_fig6` + `manual_seed_cho2024_fig6_recycling_loop`: recycling-loop
  grammar — out of scope for fig1 overview narrative.
- `manual_seed_cho2024_fig7` + `manual_seed_cho2024_fig2`: corona-discharge composite +
  MXene percolation composite — relevant but redundant with the selected motif anchors.
- `github_5f38e6be4f18596c_01` + `github_8d009ec75f299a33_01`: MIT-licensed external
  multi-panel network references — useful as layout fallback but not needed once the
  in-paper layout anchor (cho2024_fig2_mxene_percolation) was selected.

## 3. What this figure shows (same as no_vault arm)

논문 전체 논리를 상→하 두 row로 압축. Row 1: Sulfur-rich network → S-chain length 분포 →
localized trap 발생. Row 2: kinetic I(t) → ISPD Vₛ(t)→g(Eₜ) → macroscopic Coulomb probe.
Row 1 → Row 2 vertical bridge arrow labeled "convergent evidence".

스토리: *"황 풍부 폴리머에는 깊은 전하 트랩이 존재 → 다중 측정이 수렴 → 거시적 bending으로 발현."*

## 4. Physics invariants (same as no_vault arm; honored by vault grammar)

- Deep traps = LOWER energy (deeper wells); shallow traps = higher energy.
- Color convention (design.md v2.2 §6 + Q1): **shallow = blue, deep = red.**
- Panel C spatial map (design.md v2.2 §2.3 + Q2): **left = shallow blue, right = deep red.**
  Deep region has 4 wells > shallow's 3 wells, with 1–2 escape-up dashed arrows.
- Panel C must be color-consistent with Panel F (g(Eₜ) bimodal: blue Shallow left, red Deep right).
- Power-law I(t) ~ t⁻ⁿ lies ABOVE Debye reference at long times (non-Debye tail).
- Panel G shows **only** Coulomb repulsion arrow (red, polymer → away from electrode).
  Maxwell attraction arrow is **forbidden** per design.md v2.2 §2.3 정정 사항 row 2.
  Cantilever clip on TOP, polymer hanging down.

## 5. Layout — 2-row, 7-panel

Canvas 14 cm × 9 cm → `\resizebox{178mm}{!}` to NatComm 178 mm wide.
Row 1 (y=5.00..9.00): A (x=0..3.50) | B (x=3.55..6.85) | C HERO (x=6.90..13.95, ~1.5×)
Inter-row gap (y=4.50..5.00): C → Row 2 vertical Stealth arrow + label *"convergent evidence"*.
Row 2 (y=0.10..4.45): D (x=0..4.45) | E (x=4.50..6.95) | F (x=7.00..10.45) | G (x=10.50..13.95).

## 6. Per-panel implementation status (same partial scope as no_vault arm)

- **Panel A** — IMPLEMENTED. 2-DIB benzene rings + polysulfide bridge chain
  (`decorations.pathmorphing` snake per vault motif anchor). S₈ corner inset
  (`shapes.geometric` regular polygon=8). Transformation arrow with dashed
  bond-exchange annotation.
- **Panel C** — IMPLEMENTED (HERO #1). Asymmetric energy landscape:
  left = shallow blue (3 wells, 3 ⊖), right = deep red (4 wells, 4 ⊖, 2 escape-up
  dashed arrows). Color/position obey design.md v2.2 + Panel F consistency.
- **Panel B, D, E, F, G** — scaffold-level (titles + motif outlines only).

Inter-panel arrows (A→B, B→C, D→E, E↔F, F→G): standard horizontal Stealth gray.
C → Row 2: thick vertical Stealth labeled "convergent evidence".

## 7. Author intent recap

This arm tests whether vault-grounded authoring — i.e., explicit awareness of which
records carry the in-paper grammar — surfaces or prevents the categories of error
that the no_vault arm exhibited. The specific corrections from design.md v2.2
§2.3 정정 사항 are applied at author-time here (color swap, Maxwell removal,
clip-up cantilever, hero hierarchy via well-count + saturation), not deferred to
critique. Whether that authoring discipline is *because of* vault references or
*coincident with* them is a question for the blind A/B evaluator, not for this
briefing.
