# Issue 63 - Reference Learning And Aesthetic Metrics Roadmap

Status: proposed

Depends on: v0.8 release current-truth docs

## Problem

The plugin now has strong deterministic checks for stale state, crop-read
accountability, visual clash evidence, text boundary containment, label-path
proximity, external second-opinion evidence, SVG polish readiness, and
journal-art-direction critique contracts.

The remaining quality gap is different: the plugin can show references to the
host vision model, but the loop still relies on that model to decide whether
the current figure belongs to the same editorial class as the references.
References are already present in fixture specs and critique briefs; the
missing layer is not "show more reference images". The missing layer is a
contract for what may be learned from a reference, plus non-model signals that
can make the loop suspicious when reference-class divergence is large.

Without this roadmap, future work can drift into two unsafe extremes:

- treating a reference image as a copy target and forcing unrelated structure
  into the current figure; or
- continuing to treat reference comparison as advisory prose only, which lets
  old-looking or visually generic figures pass after many polish iterations.

## Goal

Add a bounded reference-learning track that lets the plugin learn editorial
principles from references without copying their content, then surface
non-model aesthetic-class signals and loop-stuck signals in `/fig_loop`.

## Design Principles

- References are not ground-truth drawings for the current figure.
- `briefing.md`, theory guards, fixture semantics, and author intent outrank
  any reference image.
- Reference transfer must be explicit: allowed transfer and forbidden transfer
  are first-class contract fields.
- Numeric metrics must measure aesthetic class, not pixel identity.
- Full-image SSIM or pixel similarity is out of scope because current figures
  are re-implementations, not copies.
- Scores and metrics must not bypass existing human, accepted, golden,
  publication, or SVG-polish gates.
- Severe divergence should make the loop stop and ask for a better action, not
  silently mutate source.

## Child Issues

1. Issue 63A - Reference Learning Contract - implemented on branch
   `codex/issue63-reference-learning-roadmap`
2. Issue 63B - Non-Model Aesthetic Metrics Pack - implemented on branch
   `codex/issue63-reference-learning-roadmap`
3. Issue 63C - Aesthetic Metric Surfacing In Status And Loop - implemented on
   branch `codex/issue63-reference-learning-roadmap`
4. Issue 63D - Basin And Diminishing-Returns Detector - implemented on branch
   `codex/issue63-reference-learning-roadmap`
5. Issue 63E - Unintended-Visible Anomaly Audit

## Order

Run 63A first. Do not implement metrics until the reference-learning contract
prevents copy-target misuse.

Recommended sequence:

1. 63A defines what can and cannot transfer from a reference.
2. 63B emits deterministic local aesthetic metrics.
3. 63C surfaces those metrics in `/fig_status`, `/fig_loop`, and critique
   context without changing release behavior.
4. 63D detects repeated loop basins and routes to step-out review.
5. 63E strengthens crop critique with an explicit anomaly question.

## Acceptance

- The roadmap clearly distinguishes reference learning from reference copying.
- All child issues are independently implementable and testable.
- Numeric metrics are scoped to aesthetic-class divergence, not pixel identity.
- Human/author intent remains the authority for semantics and physics.
- No provider API, network call, hidden auto-patch, accepted/golden mutation, or
  source drawing work is introduced by this roadmap.

## Review Questions

1. Does this prevent references from becoming accidental copy targets?
2. Does it give the loop a non-model signal for old-looking or generic figures?
3. Are semantics, physics, and author intent protected above style references?
4. Can each child issue land as a narrow, reversible slice?
