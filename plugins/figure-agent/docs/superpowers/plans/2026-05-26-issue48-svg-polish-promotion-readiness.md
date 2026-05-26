# Issue 48 SVG Polish Promotion Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only SVG polish readiness summary that explains why a figure can or cannot enter the bounded SVG polish path.

**Architecture:** Reuse the existing editorial route policy in `fig_driver_editorial.py`, write the readiness object from `/fig_loop`, and surface the same object from `/fig_driver --mode polish`. The change is additive and keeps `figure-agent.driver.v1` backward compatible.

**Tech Stack:** Python 3.12, pytest, existing figure-agent scripts and markdown command docs.

---

### Task 1: Editorial Readiness Helper

**Files:**
- Modify: `plugins/figure-agent/scripts/fig_driver_editorial.py`
- Test: `plugins/figure-agent/tests/test_fig_driver_editorial.py`

- [ ] **Step 1: Write failing helper tests**

Add tests for `continue_tikz`, `ready_for_svg_polish`,
`semantic_backport_required`, `needs_human_art_direction`, and malformed
summary input.

- [ ] **Step 2: Run red tests**

Run:

```bash
uv run pytest -q tests/test_fig_driver_editorial.py
```

Expected: fail because `svg_polish_readiness` is not defined.

- [ ] **Step 3: Implement minimal helper**

Add `READINESS_SCHEMA`, `svg_polish_readiness(summary)`, and
`svg_polish_readiness_from_checkpoint(checkpoint)`.

- [ ] **Step 4: Run green tests**

Run:

```bash
uv run pytest -q tests/test_fig_driver_editorial.py
```

Expected: pass.

### Task 2: Loop Output Surfacing

**Files:**
- Modify: `plugins/figure-agent/scripts/fig_loop.py`
- Test: `plugins/figure-agent/tests/test_fig_loop_assessments.py`

- [ ] **Step 1: Write failing loop test**

Add a test that creates a v1.11 critique with
`editorial_art_direction.tikz_vs_svg_polish_trigger.recommended_path:
continue_tikz`, runs the loop summary helper path, and asserts the iteration
contains `svg_polish_readiness.can_start_svg_polish: false`.

- [ ] **Step 2: Run red test**

Run:

```bash
uv run pytest -q tests/test_fig_loop_assessments.py
```

Expected: fail because loop iterations do not include
`svg_polish_readiness`.

- [ ] **Step 3: Implement loop write**

Call `svg_polish_readiness_from_checkpoint()` or equivalent helper after
`editorial_art_direction_summary` is built and include the result in the
iteration JSON.

- [ ] **Step 4: Run green test**

Run:

```bash
uv run pytest -q tests/test_fig_loop_assessments.py
```

Expected: pass.

### Task 3: Driver Top-Level Surfacing

**Files:**
- Modify: `plugins/figure-agent/scripts/fig_driver.py`
- Test: `plugins/figure-agent/tests/test_fig_driver.py`

- [ ] **Step 1: Write failing driver tests**

Add tests that prove `/fig_driver --mode polish` includes top-level
`svg_polish_readiness` for both current checkpoints and legacy checkpoints that
only contain `editorial_art_direction_summary`.

- [ ] **Step 2: Run red tests**

Run:

```bash
uv run pytest -q tests/test_fig_driver.py
```

Expected: fail because top-level readiness is absent.

- [ ] **Step 3: Implement driver surfacing**

Extend `_summary()` with an optional `svg_polish_readiness` field and pass it
from polish-mode branches that include a loop checkpoint. Compute fallback
readiness from the checkpoint if absent.

- [ ] **Step 4: Run green tests**

Run:

```bash
uv run pytest -q tests/test_fig_driver.py
```

Expected: pass.

### Task 4: Command Documentation

**Files:**
- Modify: `plugins/figure-agent/commands/fig_drive.md`
- Modify: `plugins/figure-agent/commands/fig_loop.md`

- [ ] **Step 1: Document readiness output**

Add a short section explaining `svg_polish_readiness` fields and route meanings.

- [ ] **Step 2: Run docs-adjacent tests**

Run:

```bash
uv run pytest -q tests/test_release_contract.py tests/test_fig_driver.py tests/test_fig_loop_assessments.py
```

Expected: pass.

### Task 5: Final Verification and Review

**Files:**
- All touched files.

- [ ] **Step 1: Run focused verification**

```bash
uv run pytest -q tests/test_fig_driver_editorial.py tests/test_fig_driver.py tests/test_fig_loop_assessments.py
```

- [ ] **Step 2: Run full verification**

```bash
uv run pytest -q
uv run ruff check .
git diff --check
claude plugin validate .claude-plugin/plugin.json
claude plugin validate .
claude plugin validate ../../.claude-plugin/marketplace.json
```

- [ ] **Step 3: Critical review**

Review for:

- Does readiness duplicate route policy incorrectly?
- Can readiness imply execution authority?
- Does `ready_for_svg_polish` bypass human/top-tier/crop/aesthetic/semantic blockers?
- Are legacy checkpoints still usable?

- [ ] **Step 4: Commit**

```bash
git add plugins/figure-agent/scripts/fig_driver_editorial.py \
  plugins/figure-agent/scripts/fig_loop.py \
  plugins/figure-agent/scripts/fig_driver.py \
  plugins/figure-agent/tests/test_fig_driver_editorial.py \
  plugins/figure-agent/tests/test_fig_loop_assessments.py \
  plugins/figure-agent/tests/test_fig_driver.py \
  plugins/figure-agent/commands/fig_drive.md \
  plugins/figure-agent/commands/fig_loop.md \
  plugins/figure-agent/docs/superpowers/issues/2026-05-26-issue-48-svg-polish-promotion-readiness.md \
  plugins/figure-agent/docs/superpowers/specs/2026-05-26-issue48-svg-polish-promotion-readiness-design.md \
  plugins/figure-agent/docs/superpowers/plans/2026-05-26-issue48-svg-polish-promotion-readiness.md
git commit -m "Add SVG polish promotion readiness"
```
