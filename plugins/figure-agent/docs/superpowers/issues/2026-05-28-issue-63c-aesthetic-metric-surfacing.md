# Issue 63C - Aesthetic Metric Surfacing In Status And Loop

Status: proposed

Depends on: Issue 63B non-model aesthetic metrics pack

## Problem

A metrics file is not useful if it stays hidden in `build/`. The loop needs to
surface metric freshness, severe divergence, and the next recommended action in
the same places users and agents already check: `/fig_status`, `/fig_loop`, and
the critique brief.

At the same time, metric surfacing must not become a release shortcut or a
false authority over physics, author intent, accepted state, or human gates.

## Goal

Make aesthetic metrics visible and actionable without letting them silently
unlock or mutate anything.

## Scope

In scope:

- Add status notes for missing, stale, invalid, and severe-divergence metric
  states when the fixture opts in.
- Add a compact `/fig_loop` summary such as
  `reference_aesthetic_metrics_summary`.
- Route severe divergence to an action-required or human-review path depending
  on the configured threshold profile.
- Include metric summary in the critique brief so the host LLM must explain or
  link any severe divergence.
- Preserve existing export, release, accepted, golden, SVG-polish, and
  publication gates.

Out of scope:

- Changing the underlying metrics.
- Making all metrics blocking by default.
- Replacing journal-grade assessment.
- Auto-patching source.

## Acceptance

- `/fig_status` surfaces opted-in metric states.
- `/fig_loop` records metric state in iteration JSON and stdout summary.
- Severe divergence cannot silently pass as "all clear".
- Missing opt-in preserves current behavior.
- Stale metrics cannot make a current critique look fresh.
- Tests cover pass, warn, severe, missing, stale, invalid, and no-opt-in cases.

## Review Questions

1. Is surfacing visible enough that users do not miss severe divergence?
2. Are existing hard gates preserved?
3. Is the route conservative while thresholds are still being calibrated?
4. Does the summary explain what to do next rather than just reporting a number?
