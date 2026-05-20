# Auto Adjudication Policy Dogfood

**Date:** 2026-05-20 KST
**Fixture:** `fig1_overview_v2_pair_001_vault`
**Status:** pass

## Commands

- `uv run python3 scripts/critique_adjudication.py scaffold fig1_overview_v2_pair_001_vault --force --policy conservative-v1`
- `uv run python3 scripts/fig_loop.py fig1_overview_v2_pair_001_vault --goal 'auto adjudication policy dogfood' --json`
- `uv run python3 scripts/fig_driver.py fig1_overview_v2_pair_001_vault --mode review --goal 'auto adjudication policy dogfood' --dry-run`

## Result

- `P001`: dismiss
- `P002`: dismiss
- `P003`: dismiss
- `C001`: defer
- `C002`: needs_human
- `/fig_loop final_stop_reason`: human_gate_required
- `/fig_loop recommended_next_action`: human review required for C002
- `/fig_driver action`: human_gate_stop
- `/fig_driver stop_boundary`: human_gate_required

## Fixes Found During Dogfood

- Initial policy over-protected `mechanism`, `topology`, and `Theory Guard`
  words even when they appeared as preserved-rationale text inside accepted
  style simplifications. The policy now protects unresolved changes/conflicts
  and violations instead of the bare terms.
- Initial policy evaluated accepted simplification before thumbnail defer, so
  C001 was incorrectly dismissed. The policy now defers non-gateable thumbnail
  polish before considering accepted-simplification dismissal.

## Judgment

The policy reduced routine human adjudication while preserving the fundamental
human gate. The loop still stops for target-journal art direction, but no
longer asks the human to adjudicate accepted iconic-abstraction confirmations.
