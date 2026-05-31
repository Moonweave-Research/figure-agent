# Issue 91 TikZ/SVG Semantic Near-Miss Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden figure-agent so LLM-authored TikZ and SVG polish cannot pass through undeclared near-miss geometry, stale SVG delta pixels, or ungrounded crop observations.

**Architecture:** Implement five conservative vertical slices. First bind SVG delta review pixels to hashes and renderer provenance. Then add a deterministic SVG semantic diff report. Then add TikZ undeclared-geometry and near-miss candidate reporting. Then strengthen host-vision crop and delta evidence grounding. Finally prove the contracts on regression fixtures and dogfood evidence. Each slice must remain additive and preserve legacy critique compatibility.

**Tech Stack:** Python, pytest, lualatex/poppler outputs, JSON/YAML manifests, existing figure-agent scripts under `plugins/figure-agent/scripts`.

---

## File Structure

- `plugins/figure-agent/scripts/svg_polish_delta.py`
  - Owns SVG delta pack rendering, manifest validation, and delta staleness.
- `plugins/figure-agent/scripts/svg_semantic_diff.py`
  - New focused checker for generated-vs-polished SVG semantic inventory.
- `plugins/figure-agent/scripts/svg_polish_manifest.py`
  - Consumes semantic diff state when computing final artifact status.
- `plugins/figure-agent/scripts/check_undeclared_geometry.py`
  - New focused checker for undeclared TikZ/render geometry risks.
- `plugins/figure-agent/scripts/compile.sh`
  - Calls the undeclared-geometry checker after existing text/path checks.
- `plugins/figure-agent/scripts/critique_brief.py`
  - Emits undeclared geometry and strengthened crop/delta instructions.
- `plugins/figure-agent/scripts/critique_schema_validator.py`
  - Adds current-schema structural requirements for grounded crop/delta entries.
- `plugins/figure-agent/scripts/critique_lint.py`
  - Enforces report accounting and rejects generic crop/delta observations.
- `plugins/figure-agent/scripts/fig_loop.py`
  - Surfaces uncertain or ungrounded evidence as a blocker.
- `plugins/figure-agent/scripts/fig_driver.py`
  - Keeps polish/release routes blocked when semantic diff or evidence grounding is unresolved.
- Tests:
  - `plugins/figure-agent/tests/test_svg_polish_delta.py`
  - `plugins/figure-agent/tests/test_svg_semantic_diff.py`
  - `plugins/figure-agent/tests/test_svg_polish_manifest.py`
  - `plugins/figure-agent/tests/test_undeclared_geometry.py`
  - `plugins/figure-agent/tests/test_critique_lint.py`
  - `plugins/figure-agent/tests/test_critique_schema_validator.py`
  - `plugins/figure-agent/tests/test_fig_loop.py`
  - `plugins/figure-agent/tests/test_fig_driver.py`

## Task 1: SVG Delta Artifact Hashes

- [x] Write failing tests in `plugins/figure-agent/tests/test_svg_polish_delta.py` for stale detection when `before.png`, `after.png`, or `diff.png` content changes.
- [x] Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_svg_polish_delta.py -k delta_artifact_hash
```

Expected: fail because current manifest does not hash delta PNG files.

- [x] Update `svg_polish_delta.py` so manifest payload includes:

```yaml
artifact_hashes:
  before_png_hash: sha256:<hash>
  after_png_hash: sha256:<hash>
  diff_png_hash: sha256:<hash>
renderer:
  script_hash: sha256:<scripts/svg_to_png.sh hash>
  executable: <renderer name>
  version: <version or unknown>
```

- [x] Update manifest validation and `svg_polish_delta_is_stale()` to compare the new hashes.
- [x] Run targeted tests and `ruff` for touched files.

Issue 91A verification:

- `uv run pytest -q tests/test_svg_polish_delta.py tests/test_critique_lint.py tests/test_critique_brief.py tests/test_fig_driver.py tests/test_svg_polish_clean_dogfood.py`
  - Result: 246 passed.
- `uv run ruff check scripts/svg_polish_delta.py tests/test_svg_polish_delta.py tests/test_critique_lint.py tests/test_fig_driver.py`
  - Result: All checks passed.
- `git diff --check`
  - Result: clean.

## Task 2: SVG Semantic Diff Report

- [x] Write tests in `plugins/figure-agent/tests/test_svg_semantic_diff.py` for:
  - visual-only pass;
  - missing text label;
  - changed viewBox;
  - unsupported external raster image;
  - group transform risk;
  - marker/path inventory change.
- [x] Implement `scripts/svg_semantic_diff.py` with a small XML inventory:
  - text inventory;
  - id/class inventory;
  - frame attributes;
  - unsupported feature inventory;
  - path/marker counts;
  - transform risk inventory.
- [x] Integrate the report into `svg_polish_manifest.py` or `fig_driver.py` so blocking states cannot become final-artifact FRESH silently.
- [x] Run targeted tests and `ruff`.

Issue 91B verification:

- `uv run pytest -q tests/test_svg_semantic_diff.py tests/test_svg_polish_manifest.py tests/test_status.py tests/test_fig_driver.py tests/test_fig_loop.py`
  - Result: 343 passed.
- `uv run ruff check scripts/svg_semantic_diff.py scripts/svg_polish_manifest.py scripts/status_next_policy.py tests/test_svg_semantic_diff.py tests/test_status.py`
  - Result: All checks passed.

## Task 3: TikZ Undeclared Geometry And Near-Miss Report

- [x] Write tests in `plugins/figure-agent/tests/test_undeclared_geometry.py` for empty report, undeclared rect, undeclared column rule, declared suppression, near-miss distance, and deterministic ids.
- [x] Implement `scripts/check_undeclared_geometry.py`.
- [x] Update `scripts/compile.sh` to write `build/undeclared_geometry.json`.
- [x] Update `critique_brief.py` to include non-empty report contents.
- [x] Update `critique_lint.py` to require accounting for non-empty report candidates.
- [x] Run targeted tests and `ruff`.

Issue 91C verification:

- `uv run pytest -q tests/test_undeclared_geometry.py tests/test_critique_brief.py tests/test_critique_lint.py`
  - Result: 173 passed.
- `uv run ruff check scripts/check_undeclared_geometry.py scripts/critique_brief.py scripts/critique_lint.py tests/test_undeclared_geometry.py tests/test_critique_brief.py tests/test_critique_lint.py`
  - Result: All checks passed.
- `bash -n scripts/compile.sh`
  - Result: clean.

## Task 4: Crop And Delta Observation Grounding

- [x] Write tests in `test_critique_schema_validator.py` and `test_critique_lint.py` for missing `observed_objects`, generic `local_relationship`, missing candidate refs, and legacy compatibility.
- [x] Update current-schema validator to require grounded crop and delta observation fields only for the new schema version.
- [x] Update lint to reject generic object/relationship prose and wrong/missing candidate refs.
- [x] Confirm `fig_loop.py` surfaces unresolved grounding failures through the existing `critique_lint_blocked` status blocker.
- [x] Run targeted tests and `ruff`.

Issue 91D verification:

- `uv run pytest -q tests/test_critique_schema_validator.py tests/test_critique_lint.py tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_status.py tests/test_fig_loop.py`
  - Result: 499 passed.
- `uv run ruff check scripts/critique_schema_validator.py scripts/critique_schema_vocab.py scripts/quality_manifest.py scripts/critique_brief.py scripts/critique_lint.py tests/test_critique_schema_validator.py tests/test_quality_manifest.py tests/test_critique_brief.py tests/test_critique_lint.py`
  - Result: All checks passed.
- `git diff --check`
  - Result: clean.

## Task 5: Regression Fixture And Dogfood Evidence

- [x] Add synthetic tests or fixtures for SVG delta artifact drift, text
      identity loss, group-transform overreach, undeclared TikZ boundary,
      near-miss geometry, and generic crop evidence.
- [x] Record the commands and observed results in a milestone document under
      `plugins/figure-agent/docs/milestones/`.
- [x] Confirm no accepted, golden, export, publication, or real paper figure
      source was mutated.

Issue 91E verification:

- `uv run pytest -q tests/test_svg_polish_delta.py tests/test_svg_semantic_diff.py tests/test_undeclared_geometry.py tests/test_critique_schema_validator.py tests/test_critique_lint.py`
  - Result: 216 passed.

## Task 6: Whole-Slice Verification

- [x] Run:

```bash
uv run pytest -q plugins/figure-agent/tests/test_svg_polish_delta.py plugins/figure-agent/tests/test_svg_semantic_diff.py plugins/figure-agent/tests/test_svg_polish_manifest.py plugins/figure-agent/tests/test_undeclared_geometry.py plugins/figure-agent/tests/test_critique_lint.py plugins/figure-agent/tests/test_critique_schema_validator.py plugins/figure-agent/tests/test_fig_loop.py plugins/figure-agent/tests/test_fig_driver.py
```

- [ ] Run:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

Whole-slice verification:

- `uv run pytest -q tests/test_svg_polish_delta.py tests/test_svg_semantic_diff.py tests/test_svg_polish_manifest.py tests/test_undeclared_geometry.py tests/test_critique_lint.py tests/test_critique_schema_validator.py tests/test_fig_loop.py tests/test_fig_driver.py tests/test_status.py tests/test_critique_brief.py tests/test_quality_manifest.py tests/test_status_next_policy.py tests/test_svg_polish_clean_dogfood.py tests/test_golden_artifact_checks.py`
  - Result: 710 passed.
- `uv run pytest -q`
  - Result: 1529 passed, 1 skipped, 1 xfailed.
- `uv run ruff check .`
  - Result: All checks passed.
- `git diff --check`
  - Result: clean.
- `claude plugin validate .claude-plugin/plugin.json`
  - Result: passed.
- `claude plugin validate .`
  - Result: passed.
- `claude plugin validate ../../.claude-plugin/marketplace.json`
  - Result: passed.

## Review Requirements

After each task, run three clean reviews:

1. Contract and freshness correctness.
2. Backward compatibility and false-positive containment.
3. Operator workflow and release/polish safety.

Do not proceed to the next task until all three reviews are clean or the issue
doc is updated to record a deliberate deferred risk.
