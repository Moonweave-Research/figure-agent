# Quality-State Hardening Plan

**Date:** 2026-05-17
**Status:** Historical evidence — non-authoritative.

**Superseded by:** `docs/product-spec.md` and `docs/execution-plan.md`.

**Status at the time:** active issue record and implementation direction

## Direction

Keep `figure-agent` as a paper-figure quality kernel, not a figure-generation
orchestrator. The next durable improvements are stricter state contracts:
explicit references, hashable critique inputs, separated readiness states, and
publication-grade artifact checks.

## Issues

### P1. Implicit reference discovery

`/fig_critique` must not infer a figure-level reference by scanning
`reference/*.png`. Reference grounding is explicit metadata only:
`spec.yaml.reference_image` for figure-level critique, or
`panels[].reference_image` plus `panels[].bbox_pdf_cm` for per-panel critique.

Status: fixed in this slice by routing critique through
`scripts/reference_contract.py`.

### P1. Shared reference contract

Reference failures, participating panel references, and figure-level reference
resolution must be computed by one module rather than separate copies in
`status.py`, `run_export.py`, and `critique_brief.py`.

Status: first slice implemented in `scripts/reference_contract.py`. Further
state-engine work should build on this module rather than re-adding private
reference scanners.

### P2. Hash-based critique freshness

mtime remains useful for cheap local status, but it cannot prove that a
critique was generated from the current prompt/rubric/tool context. Each
future `critique.md` should carry:

- `generator`
- `generator_version`
- `rubric_version`
- `critique_input_hash`

Status: prompt contract asks the host-written critique to include these fields.
`scripts/quality_manifest.py` provides deterministic input hashing, and
`/fig_status` plus `/fig_export` compare the hash when existing critique files
contain complete hash metadata. Legacy critiques without hash metadata keep the
mtime fallback.

### P2. Readiness separation

One boolean cannot represent ordinary workflow closure, golden fixture
acceptance, and release readiness. `/fig_status` now separates:

- `workflow_ready`: render, critique, and export loop is closed.
- `golden_ready`: workflow-ready and `accepted: true`.
- `release_ready`: golden-ready with a content-fresh export state.
- `final_ready`: compatibility alias for `release_ready`.

Status: implemented in `scripts/status.py`.

### P3. TIFF publication quality

The export contract promises 600 dpi TIFF output. The golden-artifact gate must
reject a TIFF that merely opens but carries low-resolution metadata.

Status: implemented as a DPI floor in `scripts/check_golden_artifacts.py`.

## Deferred

- Full hash-based status replacement for every freshness check.
- Schema migration for historical `critique.md` files without hash metadata.
- PDF page-size versus TIFF pixel-dimension fallback for TIFF files missing DPI
  metadata.
