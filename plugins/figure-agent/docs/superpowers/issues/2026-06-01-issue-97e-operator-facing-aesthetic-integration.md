# Issue 97E - Operator-Facing Aesthetic Integration

Status: proposed

Type: `/fig_driver` UX integration; future loop-improve integration

Parent:

- Issue 97 - Top-Tier Aesthetic Edge-Case Audit Roadmap

## Problem

The plugin has many audit surfaces, but the operator still needs one clear
answer after each loop:

- keep patching in TikZ;
- run host critique;
- adjudicate;
- start SVG polish;
- ask human art direction;
- force golden;
- stop.

Issue 94 improved `/fig_driver` ready-improvement surfacing. A separate
loop-improve orchestrator may later become the long-loop entrypoint, but this
branch should not assume that command exists. New aesthetic edge-case signals
from Issues 97A-D must be surfaced without adding another confusing command.

## Goal

Wire aesthetic anti-patterns, weakest-panel summaries, reference-learning
accountability, and marginal-return summaries into existing driver outputs, and
future loop-improve outputs if that command is merged, as readable bounded
next-action guidance.

## Acceptance

- `/fig_driver` action vocabulary and stop boundaries remain backward
  compatible.
- If a loop-improve command exists in the target branch, it remains a bounded
  orchestrator and does not become a hidden designer.
- Optional aesthetic improvements are explicitly optional.
- Human art-direction cases stop at the human boundary.
- SVG polish cases still require the existing SVG polish readiness gate.
- Release/golden/accepted/publication gates remain authoritative.

## Review Questions

1. Does this make the plugin easier to use, or just more verbose?
2. Can a user understand why the plugin says "complete"?
3. Can the output distinguish "safe to ship" from "still improvable"?
4. Does any output imply hidden auto-design? It must not.
