# Issue 46 Polished-SVG Clean Dogfood Implementation Plan

**Goal:** Prove the complete polished-SVG route with a deterministic temporary
fixture and record the evidence.

**Architecture:** Reuse existing SVG polish modules. Add one focused test file
instead of changing public APIs.

**Tech Stack:** Python 3.12, pytest, existing figure-agent scripts.

---

### Task 1: Write The Clean Route Test

**Files:**
- Add: `tests/test_svg_polish_clean_dogfood.py`

- [x] Build a temporary fixture with source, briefing, spec, critique, exports,
      style lock, and an SVG element with a stable id.
- [x] Write a fresh recipe.
- [x] Run the executor and assert generated export SVG bytes are unchanged.
- [x] Run delta pack with a fake renderer.
- [x] Run handoff writer.
- [x] Ask `status.infer_stage()` for the real final-artifact state.
- [x] Ask `fig_driver.build_driver_summary(..., mode="polish")` for the final
      route.

Expected first run before the test is finished: failure from missing test code
or missing setup.

### Task 2: Minimal Fixes If Needed

Only change production code if the clean route exposes a real gap. Do not add
new route behavior speculatively.

### Task 3: Milestone Evidence

**Files:**
- Add: `docs/milestones-archive/2026-05-26-polished-svg-clean-dogfood.md`

Record:

- commands run;
- final status/driver observations;
- mutation boundaries;
- review findings.

### Task 4: Verification

Run:

```bash
uv run pytest -q tests/test_svg_polish_clean_dogfood.py tests/test_svg_polish_recipe.py tests/test_svg_polish_executor.py tests/test_svg_polish_delta.py tests/test_svg_polish_handoff.py tests/test_status.py tests/test_fig_driver.py
uv run ruff check scripts/svg_polish_recipe.py scripts/svg_polish_executor.py scripts/svg_polish_delta.py scripts/svg_polish_handoff.py scripts/status.py scripts/fig_driver.py tests/test_svg_polish_clean_dogfood.py
git diff --check
```

Final verification before completion:

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

### Task 5: Review

Run three review passes:

1. Contract correctness: route uses existing modules, status, and driver.
2. Scope containment: no real examples, generated artifacts, accepted, or
   golden state are committed.
3. Integration readiness: clean path covers the gap left by Issue 44E/45.

### Task 6: Commit

Commit only docs and test changes unless a real production gap required a
minimal fix.
