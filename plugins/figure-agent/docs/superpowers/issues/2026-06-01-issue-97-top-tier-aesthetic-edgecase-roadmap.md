# Issue 97 - Top-Tier Aesthetic Edge-Case Audit Roadmap

Status: implemented for Issues 97A-E

Type: aesthetic audit hardening, guided improvement, operator UX

Design:
`docs/superpowers/specs/2026-06-01-top-tier-aesthetic-edgecase-audit-roadmap.md`

## Problem

The plugin is strong at catching objective and contract-level failures, but
top-tier figure quality still has softer edge cases that the host LLM may miss
or describe vaguely:

- generic template look;
- childish or cartoonish shape language;
- weak eye path;
- low-authority typography;
- unconvincing handcrafted finish;
- weakest-panel mismatch;
- reference over-copying or under-learning;
- marginal polish loops with no stop signal.

These failures are not always hard blockers. Many are optional polish or human
art-direction decisions. The plugin needs to make them inspectable without
pretending it can automatically certify Nature/Science visual quality.

## Goal

Turn top-tier aesthetic edge cases into structured, lintable, route-aware audit
contracts that can feed `/fig_driver`, and the loop-improve orchestrator if it
is merged, as optional or human-gated next actions.

## Child Issues

1. Issue 97A - Aesthetic Anti-Pattern Checklist
2. Issue 97B - Weakest-Panel Coherence Summary
3. Issue 97C - Reference Learning Accountability
4. Issue 97D - Marginal-Return Stop Signal
5. Issue 97E - Operator-Facing Integration

## Non-Goals

- No hidden auto-editing.
- No release gating based only on taste scores.
- No accepted/golden/export/publication mutation.
- No reference pixel-copying or topology-copying.
- No SVG polish requirement for fixtures that do not need SVG polish.
- No external provider dependency.

## Acceptance

- Each child issue has a narrow, testable scope.
- Existing deterministic gates remain authoritative.
- Human art direction remains explicit when the decision is subjective.
- Optional improvements never hide blockers.
- Existing driver/runner boundaries remain explicit; any future loop-improve
  integration must remain a bounded orchestrator, not a hidden designer.

## Implemented Slices

- 97A: brief checklist plus v1.17 `aesthetic_antipattern_audit` schema
  validation for grounded critiques.
- 97B: v1.17 `weakest_panel_coherence` schema validation for grounded
  critiques.
- 97C: v1.17 `reference_learning_accountability` schema validation for
  grounded critiques.
- 97D: marginal-return summary added to `ready_improvement_summary`.
- 97E: `/fig_driver.next_action_summary` surfaces ready-improvement and
  marginal-return state.

## Review Checklist

1. Does this roadmap solve a real operator gap observed in dogfood?
2. Does it avoid making aesthetics falsely objective?
3. Does it preserve human/author authority over taste and target-journal fit?
4. Is the implementation order incremental and reversible?
