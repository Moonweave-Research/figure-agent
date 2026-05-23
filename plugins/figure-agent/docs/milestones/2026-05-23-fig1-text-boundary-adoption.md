# Fig1 Text Boundary Adoption

**Date:** 2026-05-23 KST
**Status:** fixture metadata adopted; compile gate clean

## Scope

This milestone applies the authoring-boundary plugin chain to the active
`fig1_overview_v2_pair_001_vault` fixture. The goal is to make the plugin catch
the concrete class of defects that were previously found only by manual
inspection: text crossing row column rules or sitting inside instrument display
regions.

This pass changes fixture metadata only. It does not edit the TikZ source,
generated build artifacts, export artifacts, accepted state, or golden state.

## Adopted Contract

The fixture now declares `spec.yaml.text_boundary_layout` and matching
`spec.yaml.text_boundary_checks`.

Active checks:

- D/E column rule, scoped to the apparatus/result row body.
- E/F column rule, scoped to the apparatus/result row body.
- Panel E HV display forbidden rectangle.
- Panel E `V_s` meter display forbidden rectangle.
- Panel F PSU display forbidden rectangle.

The row top and bottom horizontal rules were intentionally not adopted in this
first fixture contract. A 7-check trial flagged normal labels near the row
header and bottom annotation band:

- `air` and `gap` near the row bottom boundary.
- `kinetic` near the inter-row branch label band.
- `ISPD` near the row header band.

Those were false-positive risks for the current goal. The final contract keeps
the high-value checks: column-rule crossing and label-internal-display overlap.

## Evidence

Helper output:

```bash
uv run python3 scripts/text_boundary_spec_helper.py \
  examples/fig1_overview_v2_pair_001_vault
```

Result: generated 5 checks matching the committed `text_boundary_checks`.

Closeout:

```bash
uv run python3 scripts/fig_closeout.py \
  fig1_overview_v2_pair_001_vault --json
```

Observed:

- `text_boundary_checks`: `passed`
- `check_count`: 5
- remaining closeout blockers are ordinary fixture workflow state
  (`compile`, `critique`, `adjudication`, `export`, `loop_rerun`), not boundary
  metadata drift.

Compile:

```bash
bash scripts/compile.sh \
  examples/fig1_overview_v2_pair_001_vault/fig1_overview_v2_pair_001_vault.tex
```

Observed:

- compile exited 0
- `build/text_boundary_clash.json` was emitted
- `text_boundary_clash.json.total`: 0
- compiler footer: `OK: no text-boundary clashes found`

## Remaining Limitation

The fixture still does not use a full `row_boxes: contain_text` contract because
the current checker applies containment to all PDF words. That would require a
scoped containment mode before it can be adopted without creating noise from
normal text outside Row 2.

This is not a blocker for the current failure class. Column-rule and forbidden
instrument-rectangle checks are now active for the areas that caused the real
manual-review misses.
