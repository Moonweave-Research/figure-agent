# Architecture v0.14 — Figure Convergence Contract

**Date**: 2026-07-06
**Status**: initial implementation slice

## Decision

`figure-agent` is a constrained scientific figure convergence system. It is not
a graph plotting library, not a matplotlib wrapper, and not a one-shot image
generator.

The core abstraction is the figure attempt, not the plot. Each attempt records
what the figure is trying to communicate, which hard publication constraints it
must obey, whether semantic correctness is preserved, how scientific-figure
aesthetic quality scores, and why the attempt is accepted, retried, rolled back,
rejected, stopped, or routed to human review.

Normative rule:

```text
Journal compliance is a hard constraint. Scientific aesthetic quality is the
objective. The agent should converge to the most beautiful possible paper figure
that still obeys the journal guide, preserves semantic correctness, and remains
editable.
```

## Relationship To Existing Architecture

This contract does not replace the quality kernel or quality-search loop.

- v0.11 defines the global quality-search loop over editable source, candidate
  rendering, scoring, rollback boundaries, and learning events.
- v0.13 defines reward truth, durable experience, learning wiring,
  self-diagnosis, gate replacement, and exploration ordering.
- v0.14 adds a typed attempt/decision layer so the loop's constraint-first
  reasoning is explicit and testable.

## Contracts

- `figure-agent.figure-attempt.v1`: one rendered or evaluated candidate with
  source/output refs, journal constraint result, semantic result, aesthetic
  score, issues, edit plan, and decision.
- `figure-agent.convergence-decision.v1`: pure controller output selecting
  accept, retry, rollback, human review, reject, or stop.
- `figure-agent.attempt-store-write.v1`: append-only storage receipt for
  attempt rows under `docs/attempts/`.

## Acceptance Ordering

1. Reject if journal constraints fail.
2. Reject if semantic correctness fails.
3. Reject if editable/export output is missing unless policy explicitly allows
   that exception.
4. Among valid attempts, prefer higher scientific aesthetic quality.
5. Roll back when a new attempt is meaningfully worse than the best valid
   previous attempt.
6. Stop when marginal aesthetic improvement falls below threshold or the attempt
   budget is exhausted.

Scores never upgrade hard gates. Aesthetic improvement cannot compensate for a
journal violation, semantic distortion, or loss of editability.

## Initial Scope

The first slice is intentionally pure and deterministic:

- typed validation and canonical hashing;
- pure convergence decision logic;
- append-only attempt storage;
- README identity guard tests;
- deterministic `JournalGuide` hard-constraint adapter;
- deterministic `AestheticObjective` scoring envelope.

It does not call an LLM, run a renderer, fetch journal rules, mutate source, set
accepted/golden/final state, or replace existing experience logs. Missing
external journal rules are represented as explicit defaults or unknowns, never
invented claims.

## Follow-up

Next slices should adapt existing `quality-search --execute` artifacts into
`figure-attempt.v1` and `convergence-decision.v1` using the new hard-constraint
and aesthetic objective adapters.
