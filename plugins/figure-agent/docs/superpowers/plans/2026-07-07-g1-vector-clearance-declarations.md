# G1 Vector Clearance Declarations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship G1 only: declaration-gated vector-to-vector clearance checks with fail-loud selectors and no declaration-free topology inference.

**Architecture:** Add a dedicated `vector_clearance` detector that reads `vector_clearance_checks` from `spec.yaml`, extracts typed literal TikZ vector elements from source geometry, resolves author selectors with P5 zero/multi-match loud failures, and reports declared relation violations. Promotion wiring reads only non-conservative declared violations; curve/circle envelope checks remain non-auto-promotable.

**Tech Stack:** Python stdlib geometry, existing `yaml`/`pdfplumber` dependency set, existing `compile.sh`, `promotion_wiring`, and `quality_defect_ledger`.

---

### Task 1: Detector Schema And P5 Selector Tests

**Files:**
- Create: `plugins/figure-agent/scripts/vector_clearance.py`
- Create: `plugins/figure-agent/tests/test_vector_clearance.py`

- [ ] Write RED tests for absent `vector_clearance_checks`, malformed schema, source-line selector zero-match, and matched-text selector multi-match.
- [ ] Run `uv run pytest tests/test_vector_clearance.py -q`; expected failures are missing module/functions.
- [ ] Implement `parse_vector_clearance_checks()`, `extract_vector_elements()`, and selector resolution with `selector_missing` / `selector_ambiguous` issues.
- [ ] Re-run `uv run pytest tests/test_vector_clearance.py -q`; expected pass.

### Task 2: Declared Geometry Relations

**Files:**
- Modify: `plugins/figure-agent/scripts/vector_clearance.py`
- Modify: `plugins/figure-agent/tests/test_vector_clearance.py`

- [ ] Add RED tests for `must_not_cross`, `must_touch`, and `min_clearance_cm` on declared literal line elements.
- [ ] Add RED tests that circle/curve envelope participants mark the issue `non_auto_promotable: true`.
- [ ] Implement conservative geometry distances/intersections for line/rect/circle/curve bbox envelopes.
- [ ] Re-run vector tests.

### Task 3: Build And Promotion Wiring

**Files:**
- Modify: `plugins/figure-agent/scripts/compile.sh`
- Modify: `plugins/figure-agent/scripts/promotion_wiring.py`
- Modify: `plugins/figure-agent/tests/test_g4_promotion_wiring.py`

- [ ] Add RED tests that `vector_clearance.json` missing/corrupt/wrong-schema fails loud when loaded directly.
- [ ] Add RED tests that an auto-tier vector clearance violation reaches the quality ledger with `source_detector: vector_clearance` and `promoted_by: auto`.
- [ ] Add RED tests that conservative curve/circle issues are not auto-promoted.
- [ ] Implement `VECTOR_CLEARANCE_SCHEMA`, loader validation, `_auto_promoted_vector_clearance_defects()`, and compile step.
- [ ] Re-run vector and promotion tests.

### Task 4: Fixture Smoke And PR

**Files:**
- Modify only if needed: `plugins/figure-agent/examples/fig1_overview_v5f_art_direction_001_vault/spec.yaml`

- [ ] Do not add broad corpus declarations. Add at most a tiny declared smoke only if an existing deterministic G1 benchmark target can be bound without guessing visual intent.
- [ ] Run `./bin/fig-agent compile fig1_overview_v5f_art_direction_001_vault` and inspect `build/vector_clearance.json`.
- [ ] Run `./bin/fig-agent quality-map fig1_overview_v5f_art_direction_001_vault --json` and confirm no declaration-free vector findings appear.
- [ ] Run targeted tests, ruff, and full suite.
- [ ] Commit with one-line message and open a stacked PR over `g3-shape-coordinate-parsing`.

## Scope Review

- G1 only; G2 vector alignment, named-coordinate resolution, exact Bézier flattening, and unattended path-through-marker detection are excluded.
- No LLM gate, no topology inference, no universal declaration-free vector rules.
- Conservative curve/circle envelope results are detectable but not auto-promoted.
