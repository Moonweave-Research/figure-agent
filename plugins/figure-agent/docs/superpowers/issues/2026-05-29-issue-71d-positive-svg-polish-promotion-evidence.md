# Issue 71D - Positive SVG Polish Promotion Evidence

Status: completed

Completion milestone:

- `docs/milestones-archive/2026-05-29-positive-svg-polish-promotion-evidence.md`

Follow-up:

- `docs/superpowers/issues/2026-05-29-issue-73-svg-polish-trigger-semantics.md`

Depends on: Issue 71B and Issue 71C where applicable

Type: HITL/AFK mixed

## Problem

The SVG polish route exists, but prior dogfood mostly proved the negative path:
stale critique or semantic blockers keep fixtures in TikZ/source work. The
plugin still lacks a clean positive real-fixture example showing when
`ready_for_svg_polish` should appear and what evidence makes that safe.

## Goal

Attempt at least one positive SVG polish promotion on a real fixture with fresh
render, critique, adjudication, and loop evidence. If no fixture qualifies,
record a no-go with exact blockers and route the next work accordingly.

## Scope

In scope:

- Select candidates from 71A/71B results.
- Run `/fig_drive --mode polish --dry-run` and inspect `svg_polish_readiness`.
- Run `/fig_loop` if needed to record current polish readiness.
- Build or inspect SVG polish recipe/delta packs only through existing bounded
  tooling.
- Record positive, negative, or blocked route evidence.

Out of scope:

- Editing SVG/vector art.
- Treating SVG polish as semantic repair.
- Forcing `ready_for_svg_polish` by weakening critique gates.
- Accepted/golden/publication mutation.

## Acceptance

- A milestone records candidate selection, freshness state, driver route,
  readiness evidence, and whether the route was useful.
- `ready_for_svg_polish` appears only if human, semantic, crop, aesthetic,
  publication, and freshness blockers are absent.
- If no positive route is possible, the no-go identifies the smallest blocker
  that must be fixed before retrying.
- Relevant SVG polish, driver, loop, and status tests pass.

## Review Questions

1. Is the positive route genuinely evidence-backed, or just absence of obvious
   errors?
2. Does SVG polish remain visual-only rather than semantic repair?
3. Is `semantic_backport_required` still distinct from optical polish?
4. Does this help the user know when to stop TikZ iteration?
