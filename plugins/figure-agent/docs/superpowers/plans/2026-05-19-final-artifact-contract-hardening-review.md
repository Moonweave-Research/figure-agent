# Final Artifact Contract Hardening Review

**Date:** 2026-05-19
**Scope:** SVG polish final-artifact design after commit `8d37138`

## Review Goal

Repeat critical review until no known in-scope design defect, algorithm gap,
codebase integration gap, or missing-documentation gap remains for the planned
Layer 5.5 final-artifact contract.

This review does not implement Issue 7A-7E. It hardens the plan so future
implementation slices have a narrower failure surface.

## Review Loop

### Loop 1: Source-of-truth and declaration

Finding: polished SVG must not become release-relevant by mere file presence.
The design already uses `spec.yaml.final_artifact` opt-in, but the active
architecture overview did not mention Layer 5.5.

Fix: add planned Layer 5.5 to `docs/architecture-overview.md`.

### Loop 2: Freshness and hash algorithm

Finding: content-hash freshness is the right direction, but implementers need
a deterministic validation order, not only state names.

Fix: add a validation algorithm to the design spec. It starts from `spec.yaml`
opt-in, validates path containment, then recomputes source/export/critique,
polished SVG, and audit hashes.

### Loop 3: Schema boundedness

Finding: `edit_classes` was described as bounded but the allowed values were
not enumerated in the design, leaving room for validator drift.

Fix: enumerate allowed edit classes and require unknown classes to fail in
Issue 7A.

### Loop 4: Codebase integration

Finding: current `/fig_export` and `check_golden_artifacts.py` behavior should
not be changed in the design-only slice. The planned integration point is
status first, accepted gate later.

Fix: keep `/fig_export` generated-only and document that
`final_artifact.kind: generated_export` is equivalent to today's default.

### Loop 5: Product direction

Finding: the quality-kernel goal did not explicitly say that final-artifact
contracts are owned by `figure-agent`, while SVG editing itself is not.

Fix: update `docs/quality-kernel-goal.md` with final-artifact contract
ownership and the explicit non-goal of acting as an SVG editor.

### Loop 6: State machine completeness

Finding: the design had no clear status for a syntactically valid, hash-fresh
polished artifact that declares semantic change or required backport.

Fix: add `BLOCKED` to the final-artifact state machine and require loop and
accepted gates to route that case to semantic backport rather than manifest
repair.

### Loop 7: Source-set freshness completeness

Finding: tracking only `source_tex_hash`, `briefing_hash`, and `spec_hash`
would miss style lock, reference, authoring-context, and theory-guard changes.

Fix: add `base.source_set_hash` to the manifest design and require Issue 7A to
use the repo-relative manifest hash convention from `quality_manifest.py`.

## Residual Risks

- No code exists yet for `svg_polish_manifest.yaml`; Issue 7A must be TDD.
- `final_ready` remains an alias for `release_ready` until Issue 7B or later.
- The plugin still cannot prove semantic preservation from SVG geometry alone;
  it relies on human provenance and backport declarations by design.

No known design-documentation blocker remains after this hardening pass.
