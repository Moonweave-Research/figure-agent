# Issue 63D - Basin And Diminishing-Returns Detector

Status: proposed

Depends on: Issue 63C aesthetic metric surfacing

## Problem

The loop can keep returning similar stop reasons, similar bottlenecks, or
similar critique defects across many iterations. That is a sign that the figure
is stuck in a local basin and needs a step-out action: external audit, human art
direction, reference-contract revision, or a broader redesign.

Today the escalation layer maps the current stop reason to a level, but it does
not reason over history. A repeated failure can look like a normal single-step
patch opportunity forever.

## Goal

Teach `/fig_loop` to detect repeated loop basins and route to a step-out action
instead of endlessly recommending the same local polish path.

## Scope

In scope:

- Read recent loop history from existing run records or an explicit compact
  history file.
- Detect repeated classes such as:
  - same critique finding kind across N runs;
  - same aesthetic bottleneck across N runs;
  - same severe metric divergence across N runs;
  - repeated human phrase or route class if represented structurally.
- Add a conservative stop reason such as `basin_detected`.
- Recommend step-out actions:
  - run external second-opinion review;
  - request human art direction;
  - revise reference-learning contract;
  - revise briefing if the reference and intent conflict.
- Keep detection read-only.

Out of scope:

- Guessing fixes automatically.
- Editing source or briefing.
- Using unstructured chat history as the sole source of truth.
- Treating one repeated NIT as a blocker.

## Acceptance

- Repeated bottlenecks route to a basin/step-out state.
- Non-repeated findings preserve current behavior.
- Basin detection includes evidence paths and counted history.
- Human/agent recommendations are concrete and bounded.
- Tests cover repeated, non-repeated, stale-history, and mixed-severity cases.

## Review Questions

1. Does this catch stuck loops without punishing normal iteration?
2. Is the history source reliable and repo-local?
3. Can the user understand why the loop says "step out"?
4. Does the detector avoid hidden state that cannot be reproduced?
